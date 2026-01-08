"""
Asset management endpoints: CRUD operations.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core import get_db
from app.models import Asset, User
from app.schemas import AssetCreate, AssetUpdate, AssetResponse
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


@router.get("", response_model=List[AssetResponse])
async def list_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    type: str = Query(None, description="Filter by asset type"),
    risk_level: str = Query(None, description="Filter by risk level"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all assets for the current tenant."""
    query = select(Asset).where(Asset.tenant_id == current_user.tenant_id)
    
    if type:
        query = query.where(Asset.type == type)
    if risk_level:
        query = query.where(Asset.risk_level == risk_level)
    
    query = query.order_by(Asset.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    assets = result.scalars().all()
    
    return assets


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset_in: AssetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new asset."""
    asset = Asset(
        tenant_id=current_user.tenant_id,
        name=asset_in.name,
        type=asset_in.type,
        tags=asset_in.tags,
        location=asset_in.location,
        metadata=asset_in.metadata,
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)
    
    return asset


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific asset by ID."""
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.tenant_id == current_user.tenant_id
        )
    )
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    return asset


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: str,
    asset_in: AssetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an asset."""
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.tenant_id == current_user.tenant_id
        )
    )
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # Update fields
    update_data = asset_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)
    
    await db.flush()
    await db.refresh(asset)
    
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an asset."""
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.tenant_id == current_user.tenant_id
        )
    )
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    await db.delete(asset)
