"""
Notifications API - Webhook and email configuration endpoints.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.models import User
from app.api.v1.endpoints.auth import get_current_user
from app.services.webhook_service import (
    WebhookConfig,
    get_webhook_manager,
    get_webhook_service,
)

router = APIRouter()


# ============ Schemas ============

class WebhookCreate(BaseModel):
    """Create webhook request."""
    url: str
    secret: Optional[str] = None
    events: Optional[List[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://api.example.com/webhooks/predictr",
                "secret": "your-secret-key",
                "events": ["alert.created", "incident.created"]
            }
        }


class WebhookResponse(BaseModel):
    """Webhook configuration response."""
    id: str
    url: str
    events: List[str]
    active: bool
    created_at: str


class WebhookDeliveryResponse(BaseModel):
    """Webhook delivery record."""
    id: str
    webhook_id: str
    event_type: str
    status: str
    attempts: int
    response_code: Optional[int]
    created_at: str


class TestWebhookRequest(BaseModel):
    """Test webhook request."""
    url: str


class NotificationSettingsUpdate(BaseModel):
    """Update notification settings."""
    email_enabled: bool = True
    slack_enabled: bool = False
    slack_webhook_url: Optional[str] = None
    email_recipients: Optional[List[str]] = None
    alert_threshold: str = "high"  # low, medium, high, critical


# ============ Endpoints ============

@router.get("/webhooks", response_model=List[WebhookResponse])
async def list_webhooks(
    current_user: User = Depends(get_current_user),
):
    """List all webhooks for the tenant."""
    manager = get_webhook_manager()
    webhooks = manager.get_tenant_webhooks(str(current_user.tenant_id))
    
    return [
        WebhookResponse(
            id=w.id,
            url=w.url,
            events=w.events,
            active=w.active,
            created_at=datetime.utcnow().isoformat(),
        )
        for w in webhooks
    ]


@router.post("/webhooks", response_model=WebhookResponse)
async def create_webhook(
    request: WebhookCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new webhook endpoint."""
    manager = get_webhook_manager()
    
    config = manager.add_webhook(
        tenant_id=str(current_user.tenant_id),
        url=request.url,
        secret=request.secret,
        events=request.events,
    )
    
    return WebhookResponse(
        id=config.id,
        url=config.url,
        events=config.events,
        active=config.active,
        created_at=datetime.utcnow().isoformat(),
    )


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a webhook endpoint."""
    manager = get_webhook_manager()
    manager.remove_webhook(str(current_user.tenant_id), webhook_id)
    
    return {"status": "deleted", "id": webhook_id}


@router.post("/webhooks/test")
async def test_webhook(
    request: TestWebhookRequest,
    current_user: User = Depends(get_current_user),
):
    """Send a test event to a webhook URL."""
    from app.services.webhook_service import WebhookEventType
    
    service = get_webhook_service()
    
    # Create temporary webhook
    test_config = WebhookConfig(
        id="test_webhook",
        url=request.url,
        active=True,
    )
    
    # Try to deliver
    try:
        service.register_webhook(test_config)
        
        results = await service.trigger(
            event_type=WebhookEventType.ALERT_CREATED,
            tenant_id=str(current_user.tenant_id),
            payload={
                "test": True,
                "message": "This is a test webhook from PredictrAI",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        
        service.unregister_webhook("test_webhook")
        
        return {
            "status": "sent",
            "results": results,
        }
    except Exception as e:
        service.unregister_webhook("test_webhook")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook test failed: {str(e)}"
        )


@router.get("/webhooks/{webhook_id}/deliveries", response_model=List[WebhookDeliveryResponse])
async def get_webhook_deliveries(
    webhook_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get delivery history for a webhook."""
    service = get_webhook_service()
    deliveries = service.get_deliveries(webhook_id=webhook_id, limit=50)
    
    return [
        WebhookDeliveryResponse(
            id=d.id,
            webhook_id=d.webhook_id,
            event_type=d.event_type,
            status=d.status,
            attempts=d.attempts,
            response_code=d.response_code,
            created_at=d.created_at.isoformat(),
        )
        for d in deliveries
    ]


@router.get("/events")
async def list_available_events(
    current_user: User = Depends(get_current_user),
):
    """List all available webhook event types."""
    from app.services.webhook_service import WebhookEventType
    
    return {
        "events": [
            {
                "name": e.value,
                "description": _get_event_description(e),
            }
            for e in WebhookEventType
        ]
    }


def _get_event_description(event_type) -> str:
    """Get human-readable description for event type."""
    descriptions = {
        "anomaly.detected": "Triggered when an anomaly is detected on an asset",
        "alert.created": "Triggered when a new alert is created",
        "alert.resolved": "Triggered when an alert is resolved",
        "incident.created": "Triggered when a new incident is created",
        "incident.updated": "Triggered when an incident is updated",
        "asset.critical": "Triggered when an asset enters critical state",
        "drift.detected": "Triggered when data or model drift is detected",
        "maintenance.due": "Triggered when maintenance is due based on RUL prediction",
        "model.trained": "Triggered when a model completes training",
    }
    return descriptions.get(event_type.value, "No description available")
