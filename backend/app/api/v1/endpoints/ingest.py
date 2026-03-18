"""
Data ingestion endpoints: metrics, logs, CSV upload.
"""
from typing import List, Optional, Set, Tuple
from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import csv
import io

from app.core import get_db, hash_api_key
from app.models import Tenant, Asset, ChangeEvent, Metric, Log
from app.schemas import (
    ChangesIngestRequest,
    IngestResponse,
    LogsIngestRequest,
    MetricsIngestRequest,
    TelemetryIngestRequest,
)
from app.services import (
    get_risk_alert_service,
    get_telemetry_adapter,
    get_telemetry_normalizer,
)

router = APIRouter()


def _derive_change_metric(change_type: str, severity: str) -> Optional[Tuple[str, float]]:
    """Map a structured change event into a canonical risk-engine metric."""
    normalized_type = change_type.strip().lower().replace(" ", "_")
    metric_map = {
        "deploy": "deploy_change_score",
        "package": "package_change_score",
        "runtime": "runtime_change_score",
        "config": "config_change_score",
        "feature_flag": "config_change_score",
        "schema": "config_change_score",
    }
    metric_name = metric_map.get(normalized_type)
    if metric_name is None:
        return None

    severity_scores = {
        "info": 0.5,
        "low": 0.7,
        "medium": 1.0,
        "warning": 1.4,
        "high": 1.6,
        "critical": 2.0,
    }
    return metric_name, severity_scores.get(severity.strip().lower(), 1.0)


async def _sync_risk_alerts_for_assets(
    db: AsyncSession,
    tenant_id: str,
    asset_ids: Set[str],
    refresh_all: bool = False,
) -> Optional[dict]:
    """Refresh automated pre-failure alerts for the touched assets."""
    if not asset_ids and not refresh_all:
        return None

    await db.flush()
    return await get_risk_alert_service().sync_for_assets(
        db,
        tenant_id=tenant_id,
        asset_ids=None if refresh_all else sorted(asset_ids),
    )


async def get_tenant_by_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db)
) -> Tenant:
    """Authenticate tenant via API key."""
    api_key_hash = hash_api_key(x_api_key)
    
    result = await db.execute(
        select(Tenant).where(Tenant.api_key_hash == api_key_hash)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return tenant


@router.post("/metrics", response_model=IngestResponse)
async def ingest_metrics(
    request: MetricsIngestRequest,
    tenant: Tenant = Depends(get_tenant_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest batch of metric data points.
    Authenticate with X-API-Key header.
    """
    accepted = 0
    rejected = 0
    touched_asset_ids: Set[str] = set()
    normalizer = get_telemetry_normalizer()
    
    # Get valid asset IDs for this tenant
    result = await db.execute(
        select(Asset.id).where(Asset.tenant_id == tenant.id)
    )
    valid_asset_ids = set(row[0] for row in result.fetchall())
    
    for point in request.data:
        if point.asset_id not in valid_asset_ids:
            rejected += 1
            continue
        
        metric = Metric(
            tenant_id=tenant.id,
            asset_id=point.asset_id,
            timestamp=point.timestamp,
            metric_name=normalizer.normalize_metric_name(point.metric_name),
            metric_value=point.metric_value,
        )
        db.add(metric)
        accepted += 1
        touched_asset_ids.add(point.asset_id)

    await _sync_risk_alerts_for_assets(db, tenant.id, touched_asset_ids)
    
    return IngestResponse(
        accepted=accepted,
        rejected=rejected,
        message=f"Ingested {accepted} metrics, rejected {rejected}"
    )


@router.post("/telemetry", response_model=IngestResponse)
async def ingest_telemetry(
    request: TelemetryIngestRequest,
    tenant: Tenant = Depends(get_tenant_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest collector-style telemetry envelopes for host, app, DB, and runtime packs.
    Authenticate with X-API-Key header.
    """
    accepted = 0
    rejected = 0
    touched_asset_ids: Set[str] = set()
    adapter = get_telemetry_adapter()

    result = await db.execute(
        select(Asset.id).where(Asset.tenant_id == tenant.id)
    )
    valid_asset_ids = set(str(row[0]) for row in result.fetchall())

    for envelope in request.data:
        if envelope.asset_id not in valid_asset_ids:
            rejected += max(1, len(envelope.metrics) + len(envelope.samples))
            continue

        metric_points = adapter.expand_envelope(
            asset_id=envelope.asset_id,
            timestamp=envelope.timestamp,
            adapter_type=envelope.adapter_type,
            metrics=envelope.metrics,
            samples=[sample.model_dump() for sample in envelope.samples],
            source=envelope.source,
            tags=envelope.tags,
        )

        if not metric_points:
            rejected += 1
            continue

        for point in metric_points:
            db.add(
                Metric(
                    tenant_id=tenant.id,
                    asset_id=point["asset_id"],
                    timestamp=point["timestamp"],
                    metric_name=point["metric_name"],
                    metric_value=point["metric_value"],
                )
            )
            accepted += 1
            touched_asset_ids.add(point["asset_id"])

    await _sync_risk_alerts_for_assets(db, tenant.id, touched_asset_ids)

    return IngestResponse(
        accepted=accepted,
        rejected=rejected,
        message=f"Ingested {accepted} telemetry samples, rejected {rejected}",
    )


@router.post("/logs", response_model=IngestResponse)
async def ingest_logs(
    request: LogsIngestRequest,
    tenant: Tenant = Depends(get_tenant_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest batch of log entries.
    Authenticate with X-API-Key header.
    """
    accepted = 0
    rejected = 0
    
    # Get valid asset IDs
    result = await db.execute(
        select(Asset.id).where(Asset.tenant_id == tenant.id)
    )
    valid_asset_ids = set(row[0] for row in result.fetchall())
    
    for point in request.data:
        if point.asset_id not in valid_asset_ids:
            rejected += 1
            continue
        
        log = Log(
            tenant_id=tenant.id,
            asset_id=point.asset_id,
            timestamp=point.timestamp,
            raw_text=point.raw_text,
            parsed_json=point.parsed_json,
        )
        db.add(log)
        accepted += 1
    
    return IngestResponse(
        accepted=accepted,
        rejected=rejected,
        message=f"Ingested {accepted} logs, rejected {rejected}"
    )


@router.post("/changes", response_model=IngestResponse)
async def ingest_changes(
    request: ChangesIngestRequest,
    tenant: Tenant = Depends(get_tenant_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest deploy, package, runtime, or config change events.
    Authenticate with X-API-Key header.
    """
    accepted = 0
    rejected = 0
    touched_asset_ids: Set[str] = set()
    refresh_all_assets = False
    normalizer = get_telemetry_normalizer()

    result = await db.execute(
        select(Asset.id).where(Asset.tenant_id == tenant.id)
    )
    valid_asset_ids = set(str(row[0]) for row in result.fetchall())

    for point in request.data:
        if point.asset_id and point.asset_id not in valid_asset_ids:
            rejected += 1
            continue

        change_event = ChangeEvent(
            tenant_id=tenant.id,
            asset_id=point.asset_id,
            timestamp=point.timestamp,
            change_type=point.change_type.strip().lower().replace(" ", "_"),
            title=point.title,
            summary=point.summary,
            source=point.source,
            severity=point.severity,
            version=point.version,
            extra_data=point.metadata,
        )
        db.add(change_event)
        accepted += 1

        derived_metric = _derive_change_metric(point.change_type, point.severity)
        if point.asset_id:
            touched_asset_ids.add(point.asset_id)
            if derived_metric is not None:
                metric_name, metric_value = derived_metric
                db.add(
                    Metric(
                        tenant_id=tenant.id,
                        asset_id=point.asset_id,
                        timestamp=point.timestamp,
                        metric_name=normalizer.normalize_metric_name(metric_name),
                        metric_value=metric_value,
                    )
                )
        else:
            refresh_all_assets = True

    await _sync_risk_alerts_for_assets(
        db,
        tenant.id,
        touched_asset_ids,
        refresh_all=refresh_all_assets,
    )

    return IngestResponse(
        accepted=accepted,
        rejected=rejected,
        message=f"Ingested {accepted} change events, rejected {rejected}"
    )


@router.post("/csv", response_model=IngestResponse)
async def ingest_csv(
    file: UploadFile = File(...),
    asset_id: Optional[str] = None,
    tenant: Tenant = Depends(get_tenant_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload CSV file with metrics.
    Expected columns: timestamp, metric_name, metric_value
    Optionally include asset_id column, or pass as query param.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV"
        )
    
    # Read file
    contents = await file.read()
    decoded = contents.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))
    
    # Validate required columns
    required = {'timestamp', 'metric_name', 'metric_value'}
    if not required.issubset(set(reader.fieldnames or [])):
        if 'asset_id' not in (reader.fieldnames or []) and not asset_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV must have columns: {required} and either asset_id column or query param"
            )
    
    # Get valid asset IDs
    result = await db.execute(
        select(Asset.id).where(Asset.tenant_id == tenant.id)
    )
    valid_asset_ids = set(row[0] for row in result.fetchall())
    
    accepted = 0
    rejected = 0
    touched_asset_ids: Set[str] = set()
    normalizer = get_telemetry_normalizer()
    
    for row in reader:
        row_asset_id = row.get('asset_id', asset_id)
        
        if not row_asset_id or row_asset_id not in valid_asset_ids:
            rejected += 1
            continue
        
        try:
            from datetime import datetime
            timestamp = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
            value = float(row['metric_value'])
            
            metric = Metric(
                tenant_id=tenant.id,
                asset_id=row_asset_id,
                timestamp=timestamp,
                metric_name=normalizer.normalize_metric_name(row['metric_name']),
                metric_value=value,
            )
            db.add(metric)
            accepted += 1
            touched_asset_ids.add(row_asset_id)
        except (ValueError, KeyError):
            rejected += 1

    await _sync_risk_alerts_for_assets(db, tenant.id, touched_asset_ids)
    
    return IngestResponse(
        accepted=accepted,
        rejected=rejected,
        message=f"Processed CSV: {accepted} accepted, {rejected} rejected"
    )
