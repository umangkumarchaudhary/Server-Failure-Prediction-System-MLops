"""
Alert management endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core import get_db
from app.models import Alert, Asset, User
from app.schemas import AlertResponse, AlertUpdate
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: str = Query(None, alias="status"),
    severity: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List alerts for the current tenant."""
    query = select(Alert).where(Alert.tenant_id == current_user.tenant_id)
    
    if status_filter:
        query = query.where(Alert.status == status_filter)
    if severity:
        query = query.where(Alert.severity == severity)
    
    query = query.order_by(Alert.triggered_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    # Enrich with asset names
    response = []
    for alert in alerts:
        asset_result = await db.execute(select(Asset.name).where(Asset.id == alert.asset_id))
        asset_name = asset_result.scalar_one_or_none()
        
        response.append(AlertResponse(
            id=alert.id,
            asset_id=alert.asset_id,
            asset_name=asset_name,
            triggered_at=alert.triggered_at,
            severity=alert.severity,
            message=alert.message,
            agent_suggestion=alert.agent_suggestion,
            status=alert.status,
        ))
    
    return response


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific alert."""
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.tenant_id == current_user.tenant_id
        )
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Get asset name
    asset_result = await db.execute(select(Asset.name).where(Asset.id == alert.asset_id))
    asset_name = asset_result.scalar_one_or_none()
    
    return AlertResponse(
        id=alert.id,
        asset_id=alert.asset_id,
        asset_name=asset_name,
        triggered_at=alert.triggered_at,
        severity=alert.severity,
        message=alert.message,
        agent_suggestion=alert.agent_suggestion,
        status=alert.status,
    )


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    update: AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update alert status (acknowledge, resolve)."""
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.tenant_id == current_user.tenant_id
        )
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    alert.status = update.status
    await db.flush()
    await db.refresh(alert)
    
    # Get asset name
    asset_result = await db.execute(select(Asset.name).where(Asset.id == alert.asset_id))
    asset_name = asset_result.scalar_one_or_none()
    
    return AlertResponse(
        id=alert.id,
        asset_id=alert.asset_id,
        asset_name=asset_name,
        triggered_at=alert.triggered_at,
        severity=alert.severity,
        message=alert.message,
        agent_suggestion=alert.agent_suggestion,
        status=alert.status,
    )
