"""
Notification Orchestrator - Unified notification delivery.

Coordinates:
- Email
- Slack/Teams
- Webhooks
- SMS (future)
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import asyncio

from app.services.email_service import EmailService, create_email_provider
from app.services.webhook_service import WebhookService, WebhookEventType, get_webhook_service

logger = logging.getLogger(__name__)


class NotificationOrchestrator:
    """
    Unified notification delivery system.
    
    Routes notifications to appropriate channels based on:
    - Alert priority
    - User preferences
    - Tenant configuration
    """
    
    def __init__(
        self,
        email_service: Optional[EmailService] = None,
        webhook_service: Optional[WebhookService] = None,
    ):
        self.email = email_service
        self.webhooks = webhook_service or get_webhook_service()
        
        # Channel priority mapping
        self.priority_channels = {
            "critical": ["email", "slack", "webhook", "sms"],
            "high": ["email", "slack", "webhook"],
            "medium": ["email", "webhook"],
            "low": ["webhook"],
        }
    
    async def notify_alert(
        self,
        tenant_id: str,
        alert: Dict[str, Any],
        recipients: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send notifications for an alert.
        
        Args:
            tenant_id: Tenant ID
            alert: Alert data
            recipients: Email recipients
        
        Returns:
            Delivery results per channel
        """
        priority = alert.get("severity", "medium")
        channels = self.priority_channels.get(priority, ["webhook"])
        
        results = {}
        tasks = []
        
        # Email
        if "email" in channels and self.email and recipients:
            tasks.append(self._send_email_alert(recipients, alert, priority))
        
        # Webhook
        if "webhook" in channels:
            tasks.append(self._send_webhook(
                tenant_id,
                WebhookEventType.ALERT_CREATED,
                alert,
            ))
        
        # Execute all
        if tasks:
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(completed):
                if isinstance(result, Exception):
                    results[f"task_{i}"] = {"status": "error", "error": str(result)}
                else:
                    results.update(result)
        
        return results
    
    async def notify_incident(
        self,
        tenant_id: str,
        incident: Dict[str, Any],
        recipients: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send notifications for an incident."""
        results = {}
        
        # Always send incident webhooks
        webhook_result = await self._send_webhook(
            tenant_id,
            WebhookEventType.INCIDENT_CREATED,
            incident,
        )
        results.update(webhook_result)
        
        # Email for all incidents
        if self.email and recipients:
            email_result = await self.email.send_incident(
                recipients=recipients,
                incident_id=incident.get("id", "UNKNOWN"),
                title=incident.get("title", "Incident"),
                description=incident.get("description", ""),
                severity=incident.get("severity", "medium"),
                suggested_actions=incident.get("suggested_actions", []),
            )
            results["email"] = email_result
        
        return results
    
    async def notify_anomaly(
        self,
        tenant_id: str,
        asset_id: str,
        anomaly_data: Dict[str, Any],
        recipients: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send notifications for anomaly detection."""
        score = anomaly_data.get("anomaly_score", 0)
        risk = anomaly_data.get("risk_level", "normal")
        
        # Only notify for significant anomalies
        if score < 0.5 and risk == "normal":
            return {"status": "skipped", "reason": "Below threshold"}
        
        return await self._send_webhook(
            tenant_id,
            WebhookEventType.ANOMALY_DETECTED,
            {
                "asset_id": asset_id,
                **anomaly_data,
            },
        )
    
    async def notify_drift(
        self,
        tenant_id: str,
        drift_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send notifications for drift detection."""
        return await self._send_webhook(
            tenant_id,
            WebhookEventType.DRIFT_DETECTED,
            drift_data,
        )
    
    async def _send_email_alert(
        self,
        recipients: List[str],
        alert: Dict,
        priority: str,
    ) -> Dict[str, Any]:
        """Send email for alert."""
        if not self.email:
            return {"email": {"status": "skipped", "reason": "Not configured"}}
        
        result = await self.email.send_alert(
            recipients=recipients,
            alert_type=alert.get("type", "Alert"),
            asset_name=alert.get("asset_name", "Unknown Asset"),
            message=alert.get("message", ""),
            priority=priority,
            details=alert.get("details"),
        )
        
        return {"email": result}
    
    async def _send_webhook(
        self,
        tenant_id: str,
        event_type: WebhookEventType,
        payload: Dict,
    ) -> Dict[str, Any]:
        """Send webhook notification."""
        results = await self.webhooks.trigger(
            event_type=event_type,
            tenant_id=tenant_id,
            payload=payload,
        )
        
        return {"webhook": results}


# Singleton
_orchestrator: Optional[NotificationOrchestrator] = None


def get_notification_orchestrator() -> NotificationOrchestrator:
    """Get notification orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = NotificationOrchestrator()
    return _orchestrator


def configure_notifications(
    email_provider_type: str = "smtp",
    email_config: Optional[Dict] = None,
    default_recipients: Optional[List[str]] = None,
) -> NotificationOrchestrator:
    """Configure notification services."""
    global _orchestrator
    
    email_service = None
    if email_config:
        provider = create_email_provider(email_provider_type, **email_config)
        email_service = EmailService(provider, default_recipients)
    
    _orchestrator = NotificationOrchestrator(
        email_service=email_service,
        webhook_service=get_webhook_service(),
    )
    
    return _orchestrator
