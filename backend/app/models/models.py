"""
SQLAlchemy models for multi-tenant data.
"""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import String, Text, Float, Integer, ForeignKey, DateTime, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Tenant(Base):
    """Tenant (company/organization) model."""
    __tablename__ = "tenants"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="starter")
    api_key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    assets: Mapped[List["Asset"]] = relationship("Asset", back_populates="tenant", cascade="all, delete-orphan")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """User model with tenant association."""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="user")  # admin, user
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")


class Asset(Base):
    """Asset model - generic entity for any type of equipment/system."""
    __tablename__ = "assets"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)  # machine, server, turbine, vehicle
    tags: Mapped[dict] = mapped_column(JSON, default=list)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    health_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100
    risk_level: Mapped[str] = mapped_column(String(20), default="normal")  # normal, warning, critical
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="assets")
    metrics: Mapped[List["Metric"]] = relationship("Metric", back_populates="asset", cascade="all, delete-orphan")
    logs: Mapped[List["Log"]] = relationship("Log", back_populates="asset", cascade="all, delete-orphan")
    predictions: Mapped[List["Prediction"]] = relationship("Prediction", back_populates="asset", cascade="all, delete-orphan")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="asset", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_assets_tenant", "tenant_id"),
    )


class Metric(Base):
    """Time-series metric data point."""
    __tablename__ = "metrics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"))
    asset_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("assets.id", ondelete="CASCADE"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="metrics")
    
    __table_args__ = (
        Index("idx_metrics_asset_time", "asset_id", "timestamp"),
        Index("idx_metrics_tenant", "tenant_id"),
    )


class Log(Base):
    """Log entry for an asset."""
    __tablename__ = "logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"))
    asset_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("assets.id", ondelete="CASCADE"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    cluster_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="logs")
    
    __table_args__ = (
        Index("idx_logs_asset_time", "asset_id", "timestamp"),
    )


class Prediction(Base):
    """ML prediction result for an asset."""
    __tablename__ = "predictions"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"))
    asset_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("assets.id", ondelete="CASCADE"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    anomaly_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-1
    risk_level: Mapped[str] = mapped_column(String(20), default="normal")
    rul_estimate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # hours/cycles
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    explanation_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # SHAP values, similar cases
    
    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="predictions")
    
    __table_args__ = (
        Index("idx_predictions_asset_time", "asset_id", "timestamp"),
    )


class Alert(Base):
    """Alert triggered by anomaly or threshold."""
    __tablename__ = "alerts"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"))
    asset_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("assets.id", ondelete="CASCADE"))
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # info, warning, critical
    message: Mapped[str] = mapped_column(Text, nullable=False)
    agent_suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # AI copilot suggestion
    channel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # email, slack, webhook
    ticket_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, acknowledged, resolved
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="alerts")
    asset: Mapped["Asset"] = relationship("Asset", back_populates="alerts")
    
    __table_args__ = (
        Index("idx_alerts_tenant_status", "tenant_id", "status"),
    )


class Incident(Base):
    """Historical incident for learning and similar case matching."""
    __tablename__ = "incidents"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"))
    asset_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("assets.id", ondelete="CASCADE"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Operator feedback
    embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # For similarity search
