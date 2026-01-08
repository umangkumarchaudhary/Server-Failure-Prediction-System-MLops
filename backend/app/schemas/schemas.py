"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field


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
    tags: List[str] = []
    location: Optional[str] = None
    metadata: dict = {}


class AssetUpdate(BaseModel):
    """Schema for updating an asset."""
    name: Optional[str] = None
    type: Optional[str] = None
    tags: Optional[List[str]] = None
    location: Optional[str] = None
    metadata: Optional[dict] = None


class AssetResponse(BaseModel):
    """Asset response with health info."""
    id: str
    name: str
    type: str
    tags: List[str]
    location: Optional[str]
    metadata: dict
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
    status: str

    class Config:
        from_attributes = True


class AlertUpdate(BaseModel):
    """Update alert status."""
    status: str = Field(..., pattern="^(active|acknowledged|resolved)$")


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
