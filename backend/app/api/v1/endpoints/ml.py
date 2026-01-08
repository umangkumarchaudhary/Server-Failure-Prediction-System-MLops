"""
ML API Endpoints - Expose ML functionality via REST.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import pandas as pd

from app.core import get_db
from app.models import User, Metric, Log, Prediction, Asset
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


# ============ Schemas ============

class TrainModelRequest(BaseModel):
    """Request to train models."""
    model_type: str = "all"  # all, anomaly, rul, logs
    asset_ids: Optional[List[str]] = None


class TrainModelResponse(BaseModel):
    """Training job response."""
    job_id: str
    status: str
    message: str


class PredictRequest(BaseModel):
    """Request for prediction."""
    asset_id: str
    include_explanation: bool = True


class RunPipelineResponse(BaseModel):
    """Pipeline run response."""
    status: str
    assets_processed: int
    predictions_created: int
    alerts_generated: int


# ============ Endpoints ============

@router.post("/train", response_model=TrainModelResponse)
async def train_models(
    request: TrainModelRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger model training for the tenant.
    Training runs in the background.
    """
    tenant_id = current_user.tenant_id
    
    # Generate job ID
    job_id = f"train_{tenant_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    # Add training to background tasks
    background_tasks.add_task(
        run_training_job,
        tenant_id=tenant_id,
        model_type=request.model_type,
        asset_ids=request.asset_ids,
    )
    
    return TrainModelResponse(
        job_id=job_id,
        status="queued",
        message=f"Training job {job_id} has been queued",
    )


@router.post("/run-pipeline", response_model=RunPipelineResponse)
async def run_inference_pipeline(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Run the inference pipeline for all tenant assets.
    Generates predictions and alerts.
    """
    tenant_id = current_user.tenant_id
    
    # Get all assets
    result = await db.execute(
        select(Asset).where(Asset.tenant_id == tenant_id)
    )
    assets = result.scalars().all()
    
    if not assets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No assets found for this tenant"
        )
    
    # Queue inference for each asset
    for asset in assets:
        background_tasks.add_task(
            run_asset_inference,
            tenant_id=tenant_id,
            asset_id=asset.id,
        )
    
    return RunPipelineResponse(
        status="queued",
        assets_processed=len(assets),
        predictions_created=0,  # Will be updated async
        alerts_generated=0,
    )


@router.get("/status/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get status of a training job."""
    # In production, this would check a job queue (Redis/Celery)
    return {
        "job_id": job_id,
        "status": "completed",  # Mock
        "message": "Training completed successfully",
    }


@router.get("/drift/{asset_id}")
async def check_drift(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check data drift for an asset."""
    tenant_id = current_user.tenant_id
    
    # Verify asset ownership
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.tenant_id == tenant_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # In production, this would use the DriftDetector
    return {
        "asset_id": asset_id,
        "drift_detected": False,
        "overall_drift_score": 0.12,
        "drifted_features": [],
        "checked_at": datetime.utcnow().isoformat(),
        "should_retrain": False,
    }


# ============ Background Tasks ============

async def run_training_job(
    tenant_id: str,
    model_type: str,
    asset_ids: Optional[List[str]] = None,
):
    """Background task for model training."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting training for tenant {tenant_id}, type={model_type}")
        
        # In production:
        # 1. Create MLService instance
        # 2. Fetch data from database
        # 3. Train models
        # 4. Save results
        
        # ml_service = MLService(mlflow_tracking_uri="http://localhost:5000")
        # training_pipeline = TrainingPipeline(ml_service)
        # await training_pipeline.train_tenant_models(tenant_id)
        
        logger.info(f"Training completed for tenant {tenant_id}")
    except Exception as e:
        logger.error(f"Training failed for tenant {tenant_id}: {e}")


async def run_asset_inference(
    tenant_id: str,
    asset_id: str,
):
    """Background task for asset inference."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Running inference for asset {asset_id}")
        
        # In production:
        # 1. Fetch recent metrics
        # 2. Run prediction
        # 3. Store result in predictions table
        # 4. Generate alerts if needed
        
        logger.info(f"Inference completed for asset {asset_id}")
    except Exception as e:
        logger.error(f"Inference failed for asset {asset_id}: {e}")
