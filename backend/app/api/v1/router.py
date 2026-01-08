"""
API Router aggregating all v1 endpoints.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, assets, ingest, predictions, alerts, dashboard, ml, copilot, notifications

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["Data Ingestion"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(ml.router, prefix="/ml", tags=["Machine Learning"])
api_router.include_router(copilot.router, prefix="/copilot", tags=["AI Copilot"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])


