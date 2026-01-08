"""
Webhook Service - Outbound webhook delivery.

Supports:
- Generic webhooks
- Signed payloads (HMAC)
- Retry logic
- Async delivery
"""
import os
import hmac
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class WebhookEventType(Enum):
    """Types of webhook events."""
    ANOMALY_DETECTED = "anomaly.detected"
    ALERT_CREATED = "alert.created"
    ALERT_RESOLVED = "alert.resolved"
    INCIDENT_CREATED = "incident.created"
    INCIDENT_UPDATED = "incident.updated"
    ASSET_CRITICAL = "asset.critical"
    DRIFT_DETECTED = "drift.detected"
    MAINTENANCE_DUE = "maintenance.due"
    MODEL_TRAINED = "model.trained"


@dataclass
class WebhookConfig:
    """Webhook endpoint configuration."""
    id: str
    url: str
    secret: Optional[str] = None
    events: List[str] = field(default_factory=list)  # Empty = all events
    active: bool = True
    headers: Dict[str, str] = field(default_factory=dict)
    retry_count: int = 3
    retry_delay: int = 5  # seconds


@dataclass
class WebhookDelivery:
    """Record of a webhook delivery attempt."""
    id: str
    webhook_id: str
    event_type: str
    payload: Dict
    status: str  # pending, success, failed
    attempts: int = 0
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None


class WebhookService:
    """
    Production webhook delivery service.
    
    Features:
    - HMAC signature verification
    - Automatic retries with backoff
    - Event filtering per endpoint
    - Async delivery queue
    """
    
    def __init__(self):
        if not HAS_HTTPX:
            logger.warning("httpx not installed, webhooks will be mocked")
        
        self.webhooks: Dict[str, WebhookConfig] = {}
        self.deliveries: List[WebhookDelivery] = []
        self.client = httpx.AsyncClient(timeout=30.0) if HAS_HTTPX else None
    
    def register_webhook(self, config: WebhookConfig):
        """Register a webhook endpoint."""
        self.webhooks[config.id] = config
        logger.info(f"Registered webhook: {config.id} -> {config.url}")
    
    def unregister_webhook(self, webhook_id: str):
        """Unregister a webhook endpoint."""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            logger.info(f"Unregistered webhook: {webhook_id}")
    
    async def trigger(
        self,
        event_type: WebhookEventType,
        tenant_id: str,
        payload: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Trigger webhooks for an event.
        
        Args:
            event_type: Type of event
            tenant_id: Tenant ID
            payload: Event payload
        
        Returns:
            List of delivery results
        """
        event_name = event_type.value
        results = []
        
        # Build full payload
        full_payload = {
            "event": event_name,
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": tenant_id,
            "data": payload,
        }
        
        # Find matching webhooks
        for webhook in self.webhooks.values():
            if not webhook.active:
                continue
            
            # Check event filter
            if webhook.events and event_name not in webhook.events:
                continue
            
            # Deliver
            result = await self._deliver(webhook, full_payload)
            results.append(result)
        
        return results
    
    async def _deliver(
        self,
        webhook: WebhookConfig,
        payload: Dict,
    ) -> Dict[str, Any]:
        """Deliver payload to webhook with retries."""
        delivery = WebhookDelivery(
            id=f"del_{datetime.utcnow().timestamp()}",
            webhook_id=webhook.id,
            event_type=payload["event"],
            payload=payload,
            status="pending",
        )
        
        if not self.client:
            delivery.status = "mocked"
            self.deliveries.append(delivery)
            return {"status": "mocked", "delivery_id": delivery.id}
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "PredictrAI-Webhook/1.0",
            "X-Webhook-ID": webhook.id,
            "X-Event-Type": payload["event"],
            **webhook.headers,
        }
        
        # Sign payload if secret configured
        if webhook.secret:
            signature = self._sign_payload(payload, webhook.secret)
            headers["X-Signature-256"] = f"sha256={signature}"
        
        # Attempt delivery with retries
        for attempt in range(webhook.retry_count):
            delivery.attempts = attempt + 1
            
            try:
                response = await self.client.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                )
                
                delivery.response_code = response.status_code
                delivery.response_body = response.text[:500]  # Truncate
                
                if response.is_success:
                    delivery.status = "success"
                    delivery.delivered_at = datetime.utcnow()
                    break
                elif response.status_code >= 500:
                    # Retry on server errors
                    logger.warning(f"Webhook {webhook.id} returned {response.status_code}, retrying...")
                    await asyncio.sleep(webhook.retry_delay * (attempt + 1))
                else:
                    # Don't retry on client errors
                    delivery.status = "failed"
                    break
                    
            except Exception as e:
                logger.error(f"Webhook delivery failed: {e}")
                delivery.status = "failed"
                delivery.response_body = str(e)
                
                if attempt < webhook.retry_count - 1:
                    await asyncio.sleep(webhook.retry_delay * (attempt + 1))
        
        if delivery.status == "pending":
            delivery.status = "failed"
        
        self.deliveries.append(delivery)
        
        return {
            "status": delivery.status,
            "delivery_id": delivery.id,
            "attempts": delivery.attempts,
            "response_code": delivery.response_code,
        }
    
    def _sign_payload(self, payload: Dict, secret: str) -> str:
        """Generate HMAC signature for payload."""
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        signature = hmac.new(
            secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return signature
    
    @staticmethod
    def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
        """Verify incoming webhook signature."""
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)
    
    def get_deliveries(
        self,
        webhook_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[WebhookDelivery]:
        """Get delivery history."""
        results = self.deliveries
        
        if webhook_id:
            results = [d for d in results if d.webhook_id == webhook_id]
        if status:
            results = [d for d in results if d.status == status]
        
        return results[-limit:]


class WebhookManager:
    """
    Tenant-aware webhook management.
    
    Stores webhook configurations per tenant.
    """
    
    def __init__(self, service: WebhookService):
        self.service = service
        self.tenant_webhooks: Dict[str, List[str]] = {}  # tenant_id -> webhook_ids
    
    def add_webhook(
        self,
        tenant_id: str,
        url: str,
        secret: Optional[str] = None,
        events: Optional[List[str]] = None,
    ) -> WebhookConfig:
        """Add webhook for a tenant."""
        config = WebhookConfig(
            id=f"wh_{tenant_id}_{datetime.utcnow().timestamp()}",
            url=url,
            secret=secret,
            events=events or [],
        )
        
        self.service.register_webhook(config)
        
        if tenant_id not in self.tenant_webhooks:
            self.tenant_webhooks[tenant_id] = []
        self.tenant_webhooks[tenant_id].append(config.id)
        
        return config
    
    def remove_webhook(self, tenant_id: str, webhook_id: str):
        """Remove webhook for a tenant."""
        if tenant_id in self.tenant_webhooks:
            if webhook_id in self.tenant_webhooks[tenant_id]:
                self.tenant_webhooks[tenant_id].remove(webhook_id)
                self.service.unregister_webhook(webhook_id)
    
    def get_tenant_webhooks(self, tenant_id: str) -> List[WebhookConfig]:
        """Get all webhooks for a tenant."""
        webhook_ids = self.tenant_webhooks.get(tenant_id, [])
        return [self.service.webhooks[wid] for wid in webhook_ids if wid in self.service.webhooks]


# Singleton instances
_webhook_service: Optional[WebhookService] = None
_webhook_manager: Optional[WebhookManager] = None


def get_webhook_service() -> WebhookService:
    """Get webhook service singleton."""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service


def get_webhook_manager() -> WebhookManager:
    """Get webhook manager singleton."""
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = WebhookManager(get_webhook_service())
    return _webhook_manager
