"""
ML Guard API endpoints for drift detection and ML health summaries.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.core import get_db, settings
from app.models import Asset, ChangeEvent, Metric, Prediction, User
from app.schemas import (
    AutomationRunResponse,
    AutomationStatusResponse,
    AssetRiskDetailResponse,
    ChangeEventResponse,
    ChangeFeedResponse,
    DriftSummaryResponse,
    MLHealthOverviewResponse,
    MLHealthSummaryResponse,
    MLModelHealthResponse,
    RiskAlertSyncRequest,
    RiskAlertSyncResponse,
    RiskOverviewResponse,
    TelemetryCatalogResponse,
    TelemetryAdapterCatalogResponse,
    TelemetryAdapterDefinitionResponse,
    TelemetrySignalResponse,
)
from app.services import (
    get_automation_scheduler,
    get_change_intelligence,
    get_risk_alert_service,
    get_telemetry_adapter,
    get_risk_engine,
    get_telemetry_normalizer,
)
from ml.guard.drift import DriftMonitor

router = APIRouter()


class DriftRequest(BaseModel):
    """Payload for ad hoc drift checks."""

    current_data: List[Dict[str, Any]]
    reference_data: Optional[List[Dict[str, Any]]] = None


_dataset_monitor: Optional[DriftMonitor] = None
_prediction_monitors: Dict[str, DriftMonitor] = {}


def get_default_reference_data() -> pd.DataFrame:
    """
    Generate a default dataset baseline for ad hoc drift checks.
    """
    np.random.seed(42)
    n_samples = 1000

    return pd.DataFrame(
        {
            "temperature": np.random.normal(65, 10, n_samples),
            "vibration": np.random.normal(0.5, 0.1, n_samples),
            "pressure": np.random.normal(100, 15, n_samples),
            "rpm": np.random.normal(1500, 100, n_samples),
            "current": np.random.normal(10, 2, n_samples),
        }
    )


def get_default_prediction_reference_data(target_column: str = "prediction") -> pd.DataFrame:
    """
    Generate a default prediction baseline for ad hoc prediction drift checks.
    """
    np.random.seed(42)
    return pd.DataFrame(
        {
            target_column: np.clip(np.random.beta(2.5, 8.0, 1000), 0.0, 1.0),
        }
    )


def get_dataset_monitor(custom_reference_data: Optional[List[Dict[str, Any]]] = None) -> DriftMonitor:
    """Return a dataset drift monitor backed by either custom or cached reference data."""
    global _dataset_monitor

    if custom_reference_data:
        return DriftMonitor(reference_data=pd.DataFrame(custom_reference_data))

    if _dataset_monitor is None:
        _dataset_monitor = DriftMonitor(reference_data=get_default_reference_data())

    return _dataset_monitor


def get_prediction_monitor(
    target_column: str = "prediction",
    custom_reference_data: Optional[List[Dict[str, Any]]] = None,
) -> DriftMonitor:
    """Return a prediction drift monitor with a baseline that includes the target column."""
    if custom_reference_data:
        return DriftMonitor(reference_data=pd.DataFrame(custom_reference_data))

    if target_column not in _prediction_monitors:
        _prediction_monitors[target_column] = DriftMonitor(
            reference_data=get_default_prediction_reference_data(target_column)
        )

    return _prediction_monitors[target_column]


def _format_float(value: Optional[float], digits: int = 2, suffix: str = "") -> str:
    """Format a float for dashboard display."""
    if value is None or pd.isna(value):
        return "No data"
    return f"{value:.{digits}f}{suffix}"


def _to_iso(timestamp: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO string when present."""
    if timestamp is None:
        return None
    return timestamp.isoformat()


def _resolve_model_status(last_activity: Optional[datetime], healthy_data: bool = True) -> str:
    """Map last activity to a coarse model lifecycle state."""
    if last_activity is None:
        return "learning"
    if not healthy_data:
        return "monitoring"
    if last_activity >= datetime.utcnow() - timedelta(hours=48):
        return "production"
    return "monitoring"


def _build_metric_frame(metric_rows: List[Any]) -> pd.DataFrame:
    """Pivot tall metric rows into a wide feature matrix per asset/timestamp."""
    if not metric_rows:
        return pd.DataFrame()

    normalizer = get_telemetry_normalizer()
    records = [
        {
            "asset_id": str(row.asset_id),
            "timestamp": row.timestamp,
            "metric_name": normalizer.normalize_metric_name(row.metric_name),
            "metric_value": row.metric_value,
        }
        for row in metric_rows
    ]
    frame = pd.DataFrame(records)
    if frame.empty:
        return frame

    pivoted = (
        frame.pivot_table(
            index=["asset_id", "timestamp"],
            columns="metric_name",
            values="metric_value",
            aggfunc="mean",
        )
        .reset_index()
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    pivoted.columns.name = None
    return pivoted


def _build_prediction_frame(prediction_rows: List[Any]) -> pd.DataFrame:
    """Create a prediction feature matrix for drift checks."""
    if not prediction_rows:
        return pd.DataFrame()

    frame = pd.DataFrame(
        [
            {
                "asset_id": str(row.asset_id),
                "timestamp": row.timestamp,
                "anomaly_score": row.anomaly_score,
                "rul_estimate": row.rul_estimate,
            }
            for row in prediction_rows
        ]
    )
    if frame.empty:
        return frame

    return frame.sort_values("timestamp").reset_index(drop=True)


def _split_windows(frame: pd.DataFrame, max_rows: int = 240, min_window: int = 12):
    """Split a time-ordered frame into reference and current numeric windows."""
    if frame.empty:
        return None, None

    working = frame.copy()
    if "timestamp" in working.columns:
        working = working.sort_values("timestamp")

    working = working.tail(max_rows).reset_index(drop=True)
    numeric_cols = [col for col in working.select_dtypes(include=np.number).columns.tolist() if col != "timestamp"]
    if not numeric_cols:
        return None, None

    numeric_frame = working[numeric_cols].dropna(how="all")
    if len(numeric_frame) < min_window * 2:
        return None, None

    current_window_size = max(min_window, min(48, len(numeric_frame) // 3))
    if len(numeric_frame) - current_window_size < min_window:
        current_window_size = len(numeric_frame) // 2

    reference_frame = numeric_frame.iloc[:-current_window_size]
    current_frame = numeric_frame.iloc[-current_window_size:]

    if len(reference_frame) < min_window or len(current_frame) < min_window:
        return None, None

    return reference_frame, current_frame


def _summarize_drift(kind: str, frame: pd.DataFrame, insufficient_message: str) -> DriftSummaryResponse:
    """Run a drift check over rolling historical windows and normalize the response shape."""
    reference_frame, current_frame = _split_windows(frame)
    if reference_frame is None or current_frame is None:
        return DriftSummaryResponse(
            kind=kind,
            status="insufficient_data",
            drift_detected=False,
            message=insufficient_message,
        )

    report = DriftMonitor(reference_data=reference_frame).detect_drift(current_frame)
    if report.get("error"):
        return DriftSummaryResponse(
            kind=kind,
            status="insufficient_data",
            drift_detected=False,
            sample_size=len(current_frame),
            message=report["error"],
        )

    summary = report.get("summary", {})
    drifted_features = list(report.get("drifted_columns", {}).keys())
    drift_detected = bool(report.get("drift_detected"))
    status = "drift_detected" if drift_detected else "healthy"

    if drift_detected:
        message = (
            f"Detected drift in {len(drifted_features)} of {summary.get('total_columns', 0)} "
            f"{'prediction signals' if kind == 'prediction' else 'input features'}."
        )
    else:
        message = (
            "Latest window looks stable against the tenant's recent baseline."
        )

    return DriftSummaryResponse(
        kind=kind,
        status=status,
        drift_detected=drift_detected,
        drifted_features=drifted_features,
        drifted_count=summary.get("drifted_count", 0),
        total_columns=summary.get("total_columns", 0),
        share_of_drifted_columns=summary.get("share_of_drifted_columns", 0.0),
        sample_size=len(current_frame),
        message=message,
    )


def _build_model_cards(
    total_assets: int,
    metric_rows: List[Any],
    prediction_rows: List[Any],
    data_drift: DriftSummaryResponse,
    prediction_drift: DriftSummaryResponse,
) -> List[MLModelHealthResponse]:
    """Build truthful ML capability cards from live tenant data."""
    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)

    metric_assets = {str(row.asset_id) for row in metric_rows}
    prediction_assets = {str(row.asset_id) for row in prediction_rows}

    anomaly_rows = [row for row in prediction_rows if row.anomaly_score is not None]
    anomaly_recent = [row for row in anomaly_rows if row.timestamp and row.timestamp >= day_ago]
    anomaly_last_activity = max((row.timestamp for row in anomaly_rows), default=None)
    anomaly_avg_score = (
        float(np.mean([row.anomaly_score for row in anomaly_rows[:25]]))
        if anomaly_rows
        else None
    )
    anomaly_prediction_drift = "anomaly_score" in prediction_drift.drifted_features
    anomaly_drifted_features = (
        ["anomaly_score"] if anomaly_prediction_drift else data_drift.drifted_features[:3]
    )
    anomaly_status = _resolve_model_status(
        anomaly_last_activity,
        healthy_data=data_drift.status != "insufficient_data",
    )
    anomaly_summary = (
        "Scoring live prediction streams and comparing them against recent healthy behavior."
        if anomaly_rows
        else "Waiting for anomaly predictions before a stable baseline can be established."
    )

    rul_rows = [row for row in prediction_rows if row.rul_estimate is not None]
    rul_recent = [row for row in rul_rows if row.timestamp and row.timestamp >= day_ago]
    rul_last_activity = max((row.timestamp for row in rul_rows), default=None)
    rul_median = (
        float(np.median([row.rul_estimate for row in rul_rows[:25]]))
        if rul_rows
        else None
    )
    rul_prediction_drift = "rul_estimate" in prediction_drift.drifted_features
    rul_drifted_features = ["rul_estimate"] if rul_prediction_drift else data_drift.drifted_features[:3]
    rul_status = _resolve_model_status(
        rul_last_activity,
        healthy_data=prediction_drift.status != "insufficient_data",
    )
    rul_summary = (
        "Tracking remaining useful life signals from recent predictions."
        if rul_rows
        else "Waiting for RUL predictions before health and stability can be assessed."
    )

    drift_last_activity = max(
        [row.timestamp for row in metric_rows if row.timestamp] + [row.timestamp for row in prediction_rows if row.timestamp],
        default=None,
    )
    drift_status = (
        "learning"
        if data_drift.status == "insufficient_data" and prediction_drift.status == "insufficient_data"
        else "production"
    )
    drift_features = list(
        dict.fromkeys(data_drift.drifted_features + prediction_drift.drifted_features)
    )[:5]
    drift_summary = (
        "Watching both telemetry inputs and model outputs for drift."
        if drift_status != "learning"
        else "Need more metrics or prediction history before drift monitoring becomes reliable."
    )
    drift_primary_value = (
        "Waiting"
        if data_drift.status == "insufficient_data"
        else f"{data_drift.share_of_drifted_columns * 100:.0f}%"
    )

    return [
        MLModelHealthResponse(
            key="anomaly_detector",
            name="Anomaly Detector",
            category="Prediction",
            status=anomaly_status,
            last_activity_at=_to_iso(anomaly_last_activity),
            assets_covered=len({str(row.asset_id) for row in anomaly_rows}),
            activity_24h=len(anomaly_recent),
            primary_metric_label="Avg anomaly score",
            primary_metric_value=_format_float(anomaly_avg_score),
            summary=anomaly_summary,
            drift_detected=anomaly_prediction_drift or data_drift.drift_detected,
            drifted_features=anomaly_drifted_features,
        ),
        MLModelHealthResponse(
            key="rul_forecaster",
            name="RUL Forecaster",
            category="Prediction",
            status=rul_status,
            last_activity_at=_to_iso(rul_last_activity),
            assets_covered=len({str(row.asset_id) for row in rul_rows}),
            activity_24h=len(rul_recent),
            primary_metric_label="Median RUL",
            primary_metric_value=_format_float(rul_median, 1, "h"),
            summary=rul_summary,
            drift_detected=rul_prediction_drift or data_drift.drift_detected,
            drifted_features=rul_drifted_features,
        ),
        MLModelHealthResponse(
            key="drift_monitor",
            name="Drift Monitor",
            category="Guardrail",
            status=drift_status,
            last_activity_at=_to_iso(drift_last_activity),
            assets_covered=len(metric_assets | prediction_assets) or total_assets,
            activity_24h=len([row for row in metric_rows if row.timestamp and row.timestamp >= day_ago]),
            primary_metric_label="Input drift share",
            primary_metric_value=drift_primary_value,
            summary=drift_summary,
            drift_detected=data_drift.drift_detected or prediction_drift.drift_detected,
            drifted_features=drift_features,
        ),
    ]


@router.get("/summary", response_model=MLHealthSummaryResponse)
async def get_ml_health_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Build a tenant-aware ML health summary from live metrics and predictions.
    """
    tenant_id = current_user.tenant_id

    total_assets_result = await db.execute(
        select(func.count(Asset.id)).where(Asset.tenant_id == tenant_id)
    )
    total_assets = int(total_assets_result.scalar() or 0)

    metric_rows_result = await db.execute(
        select(Metric.asset_id, Metric.timestamp, Metric.metric_name, Metric.metric_value)
        .where(Metric.tenant_id == tenant_id)
        .order_by(Metric.timestamp.desc())
        .limit(5000)
    )
    metric_rows = metric_rows_result.all()

    prediction_rows_result = await db.execute(
        select(
            Prediction.asset_id,
            Prediction.timestamp,
            Prediction.anomaly_score,
            Prediction.rul_estimate,
        )
        .where(Prediction.tenant_id == tenant_id)
        .order_by(Prediction.timestamp.desc())
        .limit(1000)
    )
    prediction_rows = prediction_rows_result.all()

    metric_frame = _build_metric_frame(metric_rows)
    prediction_frame = _build_prediction_frame(prediction_rows)

    data_drift = _summarize_drift(
        "data",
        metric_frame,
        "Need more recent metric windows before input drift can be assessed.",
    )
    prediction_drift = _summarize_drift(
        "prediction",
        prediction_frame,
        "Need more prediction history before output drift can be assessed.",
    )

    models = _build_model_cards(
        total_assets=total_assets,
        metric_rows=metric_rows,
        prediction_rows=prediction_rows,
        data_drift=data_drift,
        prediction_drift=prediction_drift,
    )

    assets_covered = len(
        {
            *[str(row.asset_id) for row in metric_rows],
            *[str(row.asset_id) for row in prediction_rows],
        }
    )
    production_models = len([model for model in models if model.status == "production"])
    drift_detected_models = len([model for model in models if model.drift_detected])

    return MLHealthSummaryResponse(
        overview=MLHealthOverviewResponse(
            active_models=len(models),
            production_models=production_models,
            drift_detected_models=drift_detected_models,
            assets_covered=assets_covered,
            last_updated_at=datetime.utcnow().isoformat(),
        ),
        models=models,
        data_drift=data_drift,
        prediction_drift=prediction_drift,
        mlflow_tracking_uri=settings.MLFLOW_TRACKING_URI,
    )


async def _fetch_metric_rows(
    db: AsyncSession,
    tenant_id: str,
    hours: int,
    asset_id: Optional[str] = None,
    limit: int = 12000,
) -> List[Dict[str, Any]]:
    """Fetch recent metric telemetry for risk analysis."""
    since = datetime.utcnow() - timedelta(hours=hours)
    query = (
        select(Metric.asset_id, Metric.timestamp, Metric.metric_name, Metric.metric_value)
        .where(Metric.tenant_id == tenant_id, Metric.timestamp >= since)
        .order_by(Metric.timestamp.desc())
        .limit(limit)
    )
    if asset_id:
        query = query.where(Metric.asset_id == asset_id)

    result = await db.execute(query)
    return [
        {
            "asset_id": str(row.asset_id),
            "timestamp": row.timestamp,
            "metric_name": row.metric_name,
            "metric_value": row.metric_value,
        }
        for row in result.all()
    ]


@router.get("/signals", response_model=TelemetryCatalogResponse)
async def get_supported_telemetry_signals(
    current_user: User = Depends(get_current_user),
):
    """
    List the telemetry signals and aliases that feed the pre-failure risk engine.
    """
    del current_user
    normalizer = get_telemetry_normalizer()
    return TelemetryCatalogResponse(
        generated_at=datetime.utcnow().isoformat(),
        signals=[
            TelemetrySignalResponse.model_validate(signal)
            for signal in normalizer.supported_signals()
        ],
    )


@router.get("/adapters", response_model=TelemetryAdapterCatalogResponse)
async def get_supported_telemetry_adapters(
    current_user: User = Depends(get_current_user),
):
    """
    List supported collector packs and sample payloads for telemetry onboarding.
    """
    del current_user
    adapter = get_telemetry_adapter()
    return TelemetryAdapterCatalogResponse(
        generated_at=datetime.utcnow().isoformat(),
        endpoint="/api/v1/ingest/telemetry",
        adapters=[
            TelemetryAdapterDefinitionResponse.model_validate(item)
            for item in adapter.supported_adapters()
        ],
    )


async def _fetch_prediction_rows(
    db: AsyncSession,
    tenant_id: str,
    hours: int,
    asset_id: Optional[str] = None,
    limit: int = 2000,
) -> List[Dict[str, Any]]:
    """Fetch recent predictions for risk analysis."""
    since = datetime.utcnow() - timedelta(hours=hours)
    query = (
        select(
            Prediction.asset_id,
            Prediction.timestamp,
            Prediction.anomaly_score,
            Prediction.rul_estimate,
        )
        .where(Prediction.tenant_id == tenant_id, Prediction.timestamp >= since)
        .order_by(Prediction.timestamp.desc())
        .limit(limit)
    )
    if asset_id:
        query = query.where(Prediction.asset_id == asset_id)

    result = await db.execute(query)
    return [
        {
            "asset_id": str(row.asset_id),
            "timestamp": row.timestamp,
            "anomaly_score": row.anomaly_score,
            "rul_estimate": row.rul_estimate,
        }
        for row in result.all()
    ]


async def _fetch_change_rows(
    db: AsyncSession,
    tenant_id: str,
    hours: int,
    asset_id: Optional[str] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    """Fetch recent structured change events for correlation and feed views."""
    since = datetime.utcnow() - timedelta(hours=hours)
    query = (
        select(ChangeEvent.id, ChangeEvent.asset_id, ChangeEvent.timestamp, ChangeEvent.change_type, ChangeEvent.title,
               ChangeEvent.summary, ChangeEvent.source, ChangeEvent.severity, ChangeEvent.version, ChangeEvent.extra_data)
        .where(ChangeEvent.tenant_id == tenant_id, ChangeEvent.timestamp >= since)
        .order_by(ChangeEvent.timestamp.desc())
        .limit(limit)
    )
    if asset_id:
        query = query.where(
            or_(
                ChangeEvent.asset_id == asset_id,
                ChangeEvent.asset_id.is_(None),
            )
        )

    result = await db.execute(query)
    return [
        {
            "id": row.id,
            "asset_id": str(row.asset_id) if row.asset_id else None,
            "timestamp": row.timestamp,
            "change_type": row.change_type,
            "title": row.title,
            "summary": row.summary,
            "source": row.source,
            "severity": row.severity,
            "version": row.version,
            "extra_data": row.extra_data or {},
        }
        for row in result.all()
    ]


@router.get("/risks", response_model=RiskOverviewResponse)
async def get_risk_overview(
    limit: int = Query(5, ge=1, le=25),
    hours: int = Query(72, ge=6, le=168),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Build a tenant-wide early warning overview from recent telemetry and prediction history.
    """
    tenant_id = current_user.tenant_id
    assets_result = await db.execute(
        select(Asset.id, Asset.name, Asset.type).where(Asset.tenant_id == tenant_id)
    )
    assets = [
        {"id": str(row.id), "name": row.name, "type": row.type}
        for row in assets_result.all()
    ]
    if not assets:
        return RiskOverviewResponse(
            generated_at=datetime.utcnow().isoformat(),
            monitored_assets=0,
            critical_assets=0,
            warning_assets=0,
            normal_assets=0,
            average_risk_score=0.0,
            highest_risk_score=0,
            summary="No assets are registered yet, so there is nothing to assess.",
        )

    metric_rows = await _fetch_metric_rows(db, tenant_id, hours, limit=12000)
    prediction_rows = await _fetch_prediction_rows(db, tenant_id, hours, limit=3000)
    change_rows = await _fetch_change_rows(db, tenant_id, hours, limit=300)

    risk_engine = get_risk_engine()
    overview = risk_engine.assess_fleet(assets, metric_rows, prediction_rows, limit=limit)

    asset_name_lookup = {asset["id"]: asset["name"] for asset in assets}
    change_intelligence = get_change_intelligence()
    changes_by_asset: Dict[str, List[Dict[str, Any]]] = {}
    global_changes = [change for change in change_rows if change["asset_id"] is None]
    for change in change_rows:
        if change["asset_id"] is None:
            continue
        changes_by_asset.setdefault(str(change["asset_id"]), []).append(change)

    enriched_assets = [
        change_intelligence.enrich_asset_assessment(
            asset,
            [*changes_by_asset.get(asset["asset_id"], []), *global_changes],
            asset_name_lookup=asset_name_lookup,
        )
        for asset in overview["assets"]
    ]
    overview["assets"] = enriched_assets
    overview["recent_changes"] = change_intelligence.summarize_recent_changes(
        change_rows,
        asset_name_lookup=asset_name_lookup,
        limit=5,
    )
    overview["change_correlated_assets"] = change_intelligence.count_change_correlated_assets(enriched_assets)
    return overview


@router.get("/risks/{asset_id}", response_model=AssetRiskDetailResponse)
async def get_asset_risk_detail(
    asset_id: str,
    hours: int = Query(72, ge=6, le=168),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Build a detailed pre-failure assessment for a single asset.
    """
    tenant_id = current_user.tenant_id
    asset_result = await db.execute(
        select(Asset.id, Asset.name, Asset.type).where(
            Asset.id == asset_id,
            Asset.tenant_id == tenant_id,
        )
    )
    asset = asset_result.one_or_none()
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    metric_rows = await _fetch_metric_rows(db, tenant_id, hours, asset_id=asset_id, limit=2000)
    prediction_rows = await _fetch_prediction_rows(db, tenant_id, hours, asset_id=asset_id, limit=500)
    change_rows = await _fetch_change_rows(db, tenant_id, hours, asset_id=asset_id, limit=50)

    risk_engine = get_risk_engine()
    assessment = risk_engine.assess_asset(
        asset_id=str(asset.id),
        asset_name=asset.name,
        asset_type=asset.type,
        metric_points=metric_rows,
        prediction_points=prediction_rows,
    )
    return get_change_intelligence().enrich_asset_assessment(
        assessment,
        change_rows,
        asset_name_lookup={str(asset.id): asset.name},
    )


@router.get("/changes", response_model=ChangeFeedResponse)
async def get_recent_changes(
    limit: int = Query(20, ge=1, le=100),
    hours: int = Query(72, ge=6, le=168),
    asset_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the latest deploy, runtime, package, and config changes for the tenant.
    """
    change_rows = await _fetch_change_rows(
        db,
        current_user.tenant_id,
        hours=hours,
        asset_id=asset_id,
        limit=limit,
    )
    asset_name_lookup: Dict[str, str] = {}
    asset_ids = sorted({str(change["asset_id"]) for change in change_rows if change["asset_id"]})
    if asset_ids:
        assets_result = await db.execute(
            select(Asset.id, Asset.name).where(
                Asset.tenant_id == current_user.tenant_id,
                Asset.id.in_(asset_ids),
            )
        )
        asset_name_lookup = {str(row.id): row.name for row in assets_result.all()}

    change_intelligence = get_change_intelligence()
    return ChangeFeedResponse(
        generated_at=datetime.utcnow().isoformat(),
        total_changes=len(change_rows),
        changes=[
            ChangeEventResponse.model_validate(change)
            for change in change_intelligence.summarize_recent_changes(
                change_rows,
                asset_name_lookup=asset_name_lookup,
                limit=limit,
            )
        ],
    )


@router.post("/risks/sync-alerts", response_model=RiskAlertSyncResponse)
async def sync_risk_alerts(
    request: RiskAlertSyncRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Force a synchronization of automated pre-failure alerts for review or backfill.
    """
    result = await get_risk_alert_service().sync_for_assets(
        db,
        tenant_id=current_user.tenant_id,
        asset_ids=request.asset_ids or None,
        hours=request.hours,
    )
    return RiskAlertSyncResponse.model_validate(result)


@router.get("/automation", response_model=AutomationStatusResponse)
async def get_automation_status(
    current_user: User = Depends(get_current_user),
):
    """
    Show scheduler health for recurring risk sync and drift monitoring jobs.
    """
    del current_user
    return AutomationStatusResponse.model_validate(
        get_automation_scheduler().status()
    )


@router.post("/automation/run", response_model=AutomationRunResponse)
async def run_automation_job(
    job_key: str = Query("all", pattern="^(risk_sync|drift_monitor|all)$"),
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger one or all background automation jobs for review or recovery.
    """
    del current_user
    try:
        result = await get_automation_scheduler().run_now(job_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AutomationRunResponse.model_validate(result)


@router.post("/dataset")
async def check_dataset_drift(request: DriftRequest):
    """
    Check for data drift in a provided dataset using either custom or default reference data.
    """
    try:
        monitor = get_dataset_monitor(request.reference_data)
        return monitor.detect_drift(request.current_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/prediction")
async def check_prediction_drift(request: DriftRequest, target_column: str = "prediction"):
    """
    Check for prediction drift using either custom or default reference data.
    """
    try:
        monitor = get_prediction_monitor(target_column, request.reference_data)
        current_frame = pd.DataFrame(request.current_data)
        return monitor.detect_prediction_drift(current_frame, target_column)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
