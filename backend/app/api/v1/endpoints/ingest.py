"""
Data ingestion endpoints: metrics, logs, CSV upload.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import csv
import io

from app.core import get_db, hash_api_key
from app.models import Tenant, Asset, Metric, Log
from app.schemas import MetricsIngestRequest, LogsIngestRequest, IngestResponse

router = APIRouter()


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
            metric_name=point.metric_name,
            metric_value=point.metric_value,
        )
        db.add(metric)
        accepted += 1
    
    return IngestResponse(
        accepted=accepted,
        rejected=rejected,
        message=f"Ingested {accepted} metrics, rejected {rejected}"
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


@router.post("/csv", response_model=IngestResponse)
async def ingest_csv(
    file: UploadFile = File(...),
    asset_id: str = None,
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
                metric_name=row['metric_name'],
                metric_value=value,
            )
            db.add(metric)
            accepted += 1
        except (ValueError, KeyError):
            rejected += 1
    
    return IngestResponse(
        accepted=accepted,
        rejected=rejected,
        message=f"Processed CSV: {accepted} accepted, {rejected} rejected"
    )
