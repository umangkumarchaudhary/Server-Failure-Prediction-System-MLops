"""
Prediction endpoints: get predictions, explanations.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core import get_db
from app.models import Prediction, Asset, User
from app.schemas import PredictionResponse, ExplanationResponse
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


@router.get("/asset/{asset_id}", response_model=List[PredictionResponse])
async def get_asset_predictions(
    asset_id: str,
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get predictions for a specific asset."""
    # Verify asset belongs to tenant
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.tenant_id == current_user.tenant_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # Get predictions
    result = await db.execute(
        select(Prediction)
        .where(Prediction.asset_id == asset_id)
        .order_by(Prediction.timestamp.desc())
        .limit(limit)
    )
    predictions = result.scalars().all()
    
    return predictions


@router.get("/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(
    prediction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific prediction."""
    result = await db.execute(
        select(Prediction).where(
            Prediction.id == prediction_id,
            Prediction.tenant_id == current_user.tenant_id
        )
    )
    prediction = result.scalar_one_or_none()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )
    
    return prediction


@router.get("/{prediction_id}/explain", response_model=ExplanationResponse)
async def get_prediction_explanation(
    prediction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get XAI explanation for a prediction.
    Includes SHAP feature contributions, similar incidents, and correlated logs.
    """
    result = await db.execute(
        select(Prediction).where(
            Prediction.id == prediction_id,
            Prediction.tenant_id == current_user.tenant_id
        )
    )
    prediction = result.scalar_one_or_none()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )
    
    # Extract explanation from stored JSON or compute on-the-fly
    explanation_data = prediction.explanation_json or {}
    
    return ExplanationResponse(
        prediction_id=prediction_id,
        top_features=explanation_data.get("top_features", []),
        similar_incidents=explanation_data.get("similar_incidents", []),
        correlated_logs=explanation_data.get("correlated_logs", []),
    )
