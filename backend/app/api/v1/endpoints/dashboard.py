"""
Dashboard endpoints: stats, trends.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core import get_db
from app.models import Asset, Alert, Prediction, User
from app.schemas import DashboardStats
from app.api.v1.endpoints.auth import get_current_user
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get overview dashboard statistics."""
    tenant_id = current_user.tenant_id
    
    # Total assets
    result = await db.execute(
        select(func.count(Asset.id)).where(Asset.tenant_id == tenant_id)
    )
    total_assets = result.scalar() or 0
    
    # Assets by risk level
    result = await db.execute(
        select(Asset.risk_level, func.count(Asset.id))
        .where(Asset.tenant_id == tenant_id)
        .group_by(Asset.risk_level)
    )
    risk_counts = {row[0]: row[1] for row in result.fetchall()}
    
    healthy_assets = risk_counts.get("normal", 0)
    warning_assets = risk_counts.get("warning", 0)
    critical_assets = risk_counts.get("critical", 0)
    
    # Active alerts
    result = await db.execute(
        select(func.count(Alert.id))
        .where(Alert.tenant_id == tenant_id, Alert.status == "active")
    )
    active_alerts = result.scalar() or 0
    
    # Anomalies in last 24h
    yesterday = datetime.utcnow() - timedelta(hours=24)
    result = await db.execute(
        select(func.count(Prediction.id))
        .where(
            Prediction.tenant_id == tenant_id,
            Prediction.timestamp >= yesterday,
            Prediction.anomaly_score > 0.7  # High anomaly threshold
        )
    )
    anomalies_24h = result.scalar() or 0
    
    return DashboardStats(
        total_assets=total_assets,
        healthy_assets=healthy_assets,
        warning_assets=warning_assets,
        critical_assets=critical_assets,
        active_alerts=active_alerts,
        anomalies_24h=anomalies_24h,
    )
