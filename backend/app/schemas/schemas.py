"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Optional, List, Any, Literal
from pydantic import AliasChoices, BaseModel, EmailStr, Field


# ============ Auth Schemas ============

class TenantCreate(BaseModel):
    """Schema for tenant registration."""
    name: str = Field(..., min_length=2, max_length=255)


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None


class SignupRequest(BaseModel):
    """Combined tenant + user signup."""
    tenant_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None


class SignupResponse(BaseModel):
    """Signup response with API key."""
    tenant_id: str
    user_id: str
    email: str
    api_key: str  # Only shown once!
    message: str = "Signup successful. Save your API key - it won't be shown again."


class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User info response."""
    id: str
    email: str
    name: Optional[str]
    role: str
    tenant_id: str
    tenant_name: str


# ============ Asset Schemas ============

class AssetCreate(BaseModel):
    """Schema for creating an asset."""
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1, max_length=100)  # machine, server, turbine, vehicle
    tags: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    metadata: dict = Field(default_factory=dict, validation_alias=AliasChoices("metadata", "extra_data"))


class AssetUpdate(BaseModel):
    """Schema for updating an asset."""
    name: Optional[str] = None
    type: Optional[str] = None
    tags: Optional[List[str]] = None
    location: Optional[str] = None
    metadata: Optional[dict] = Field(
        default=None,
        validation_alias=AliasChoices("metadata", "extra_data"),
    )


class AssetResponse(BaseModel):
    """Asset response with health info."""
    id: str
    name: str
    type: str
    tags: List[str]
    location: Optional[str]
    metadata: dict = Field(validation_alias=AliasChoices("extra_data", "metadata"))
    health_score: Optional[float]
    risk_level: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Ingestion Schemas ============

class MetricDataPoint(BaseModel):
    """Single metric data point for ingestion."""
    asset_id: str
    timestamp: datetime
    metric_name: str
    metric_value: float


class MetricsIngestRequest(BaseModel):
    """Batch metrics ingestion."""
    data: List[MetricDataPoint]


class LogDataPoint(BaseModel):
    """Single log entry for ingestion."""
    asset_id: str
    timestamp: datetime
    raw_text: str
    parsed_json: Optional[dict] = None


class LogsIngestRequest(BaseModel):
    """Batch logs ingestion."""
    data: List[LogDataPoint]


class ChangeEventDataPoint(BaseModel):
    """Single deploy, package, runtime, or config change event."""

    asset_id: Optional[str] = None
    timestamp: datetime
    change_type: str = Field(..., min_length=2, max_length=50)
    title: str = Field(..., min_length=3, max_length=255)
    summary: Optional[str] = None
    source: Optional[str] = None
    severity: str = Field(default="medium", pattern="^(info|low|medium|high|warning|critical)$")
    version: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class ChangesIngestRequest(BaseModel):
    """Batch change-event ingestion."""

    data: List[ChangeEventDataPoint]


class TelemetrySample(BaseModel):
    """A single telemetry metric sample from an adapter or collector."""

    name: str = Field(..., min_length=1, max_length=255)
    value: float
    unit: Optional[str] = None


class TelemetryEnvelope(BaseModel):
    """A batchable telemetry envelope from a real-world collector or agent."""

    asset_id: str
    timestamp: datetime
    adapter_type: Literal["host", "application", "database", "runtime", "custom"]
    source: Optional[str] = None
    metrics: dict[str, float] = Field(default_factory=dict)
    samples: List[TelemetrySample] = Field(default_factory=list)
    tags: dict[str, str] = Field(default_factory=dict)


class TelemetryIngestRequest(BaseModel):
    """Adapter-friendly telemetry ingestion payload."""

    data: List[TelemetryEnvelope]


class IngestResponse(BaseModel):
    """Ingestion response."""
    accepted: int
    rejected: int
    message: str


# ============ Prediction Schemas ============

class PredictionResponse(BaseModel):
    """Prediction result."""
    id: str
    asset_id: str
    timestamp: datetime
    anomaly_score: Optional[float]
    risk_level: str
    rul_estimate: Optional[float]
    model_version: Optional[str]
    explanation_json: Optional[dict] = None

    class Config:
        from_attributes = True


class ExplanationResponse(BaseModel):
    """XAI explanation for a prediction."""
    prediction_id: str
    top_features: List[dict]  # [{name, value, contribution}]
    similar_incidents: List[dict]  # [{id, description, similarity}]
    correlated_logs: List[dict]  # [{cluster_id, sample_text, count}]


# ============ Alert Schemas ============

class AlertResponse(BaseModel):
    """Alert response."""
    id: str
    asset_id: str
    asset_name: Optional[str] = None
    triggered_at: datetime
    severity: str
    message: str
    agent_suggestion: Optional[str]
    source: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class AlertUpdate(BaseModel):
    """Update alert status."""
    status: str = Field(..., pattern="^(active|acknowledged|resolved)$")


class ChangeEventResponse(BaseModel):
    """Recorded change event for dashboard and correlation views."""

    id: int
    asset_id: Optional[str] = None
    asset_name: Optional[str] = None
    timestamp: str
    change_type: str
    title: str
    summary: Optional[str] = None
    source: Optional[str] = None
    severity: str
    version: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    correlation_score: float = 0.0


class ChangeFeedResponse(BaseModel):
    """Recent change intelligence feed."""

    generated_at: str
    total_changes: int
    changes: List[ChangeEventResponse] = Field(default_factory=list)


# ============ Dashboard Schemas ============

class DashboardStats(BaseModel):
    """Overview dashboard statistics."""
    total_assets: int
    healthy_assets: int
    warning_assets: int
    critical_assets: int
    active_alerts: int
    anomalies_24h: int


class AssetHealthTrend(BaseModel):
    """Asset health over time."""
    timestamp: datetime
    health_score: float
    anomaly_count: int


# ============ ML Health Schemas ============

class DriftSummaryResponse(BaseModel):
    """Shared drift summary payload for dashboard use."""
    kind: Literal["data", "prediction"]
    status: Literal["healthy", "drift_detected", "insufficient_data"]
    drift_detected: bool
    drifted_features: List[str] = Field(default_factory=list)
    drifted_count: int = 0
    total_columns: int = 0
    share_of_drifted_columns: float = 0.0
    sample_size: int = 0
    message: str


class MLModelHealthResponse(BaseModel):
    """High-level health card for a model capability."""
    key: str
    name: str
    category: str
    status: Literal["production", "monitoring", "learning"]
    last_activity_at: Optional[str] = None
    assets_covered: int = 0
    activity_24h: int = 0
    primary_metric_label: str
    primary_metric_value: str
    summary: str
    drift_detected: bool = False
    drifted_features: List[str] = Field(default_factory=list)


class MLHealthOverviewResponse(BaseModel):
    """Top-level summary cards for the ML health dashboard."""
    active_models: int
    production_models: int
    drift_detected_models: int
    assets_covered: int
    last_updated_at: str


class MLHealthSummaryResponse(BaseModel):
    """API response for the ML health dashboard."""
    overview: MLHealthOverviewResponse
    models: List[MLModelHealthResponse]
    data_drift: DriftSummaryResponse
    prediction_drift: DriftSummaryResponse
    mlflow_tracking_uri: Optional[str] = None


# ============ Risk Schemas ============

class RiskIndicatorResponse(BaseModel):
    """Single risk signal that contributes to an asset warning."""

    signal_key: str
    label: str
    category: str
    severity: Literal["elevated", "critical"]
    metric_name: str
    latest_value: float
    threshold: float
    trend: Literal["stable", "rising", "falling", "spiking"]
    contribution: float
    reason: str


class AssetRiskSummaryResponse(BaseModel):
    """Compact risk summary for dashboard lists."""

    asset_id: str
    asset_name: str
    asset_type: str
    risk_score: int
    risk_level: Literal["normal", "warning", "critical"]
    confidence: float
    forecast_window: str
    summary: str
    last_metric_at: Optional[str] = None
    last_prediction_at: Optional[str] = None
    top_signals: List[str] = Field(default_factory=list)
    likely_causes: List[str] = Field(default_factory=list)
    change_correlation_score: float = 0.0


class AssetRiskDetailResponse(AssetRiskSummaryResponse):
    """Detailed risk assessment for a single asset."""

    recommended_actions: List[str] = Field(default_factory=list)
    indicators: List[RiskIndicatorResponse] = Field(default_factory=list)
    recent_changes: List[ChangeEventResponse] = Field(default_factory=list)


class RiskSignalFrequencyResponse(BaseModel):
    """Counts of the most common risky signals across the fleet."""

    signal_key: str
    label: str
    count: int


class RiskOverviewResponse(BaseModel):
    """Tenant-level early warning overview."""

    generated_at: str
    monitored_assets: int
    critical_assets: int
    warning_assets: int
    normal_assets: int
    average_risk_score: float
    highest_risk_score: int
    summary: str
    change_correlated_assets: int = 0
    assets: List[AssetRiskSummaryResponse] = Field(default_factory=list)
    top_signals: List[RiskSignalFrequencyResponse] = Field(default_factory=list)
    recent_changes: List[ChangeEventResponse] = Field(default_factory=list)


class TelemetrySignalResponse(BaseModel):
    """Canonical telemetry signal exposed for ingestion guidance."""

    signal_key: str
    label: str
    category: str
    aliases: List[str] = Field(default_factory=list)


class TelemetryCatalogResponse(BaseModel):
    """Telemetry onboarding catalog for the risk engine."""

    generated_at: str
    signals: List[TelemetrySignalResponse] = Field(default_factory=list)


class TelemetryAdapterDefinitionResponse(BaseModel):
    """Supported telemetry adapter or collector pack."""

    adapter_type: str
    label: str
    description: str
    recommended_metrics: List[str] = Field(default_factory=list)
    sample_payload: dict[str, Any] = Field(default_factory=dict)


class TelemetryAdapterCatalogResponse(BaseModel):
    """Adapter-friendly onboarding catalog for telemetry integration."""

    generated_at: str
    endpoint: str
    adapters: List[TelemetryAdapterDefinitionResponse] = Field(default_factory=list)


class RiskAlertSyncRequest(BaseModel):
    """Manual request to sync automated risk alerts."""

    asset_ids: List[str] = Field(default_factory=list)
    hours: int = Field(default=72, ge=6, le=168)


class RiskAlertSyncResponse(BaseModel):
    """Result of an automated risk alert synchronization."""

    generated_at: str
    processed_assets: int
    assets_with_telemetry: int
    warning_assets: int
    critical_assets: int
    alerts_created: int
    alerts_updated: int
    alerts_resolved: int
    message: str


class AutomationJobStatusResponse(BaseModel):
    """Runtime status for a scheduled automation job."""

    job_key: str
    label: str
    interval_seconds: int
    last_status: Literal["idle", "running", "success", "error", "disabled", "degraded"]
    last_started_at: Optional[str] = None
    last_finished_at: Optional[str] = None
    last_duration_ms: Optional[int] = None
    last_error: Optional[str] = None
    last_summary: dict = Field(default_factory=dict)
    total_runs: int = 0
    success_runs: int = 0
    failure_runs: int = 0
    is_running: bool = False


class AutomationStatusResponse(BaseModel):
    """Overall scheduler status for background automation."""

    enabled: bool
    started_at: Optional[str] = None
    running_jobs: int = 0
    jobs: List[AutomationJobStatusResponse] = Field(default_factory=list)


class AutomationRunResponse(BaseModel):
    """Result of manually triggering one or more automation jobs."""

    triggered_at: str
    job_key: str
    status: Literal["completed", "completed_with_errors"]
    jobs: List[AutomationJobStatusResponse] = Field(default_factory=list)
