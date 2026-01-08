"""
Notification Provider - Multi-channel notification delivery.

Supports:
- Email (SMTP/SendGrid)
- Slack
- Microsoft Teams
- Webhooks
"""
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import logging
import json

logger = logging.getLogger(__name__)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class NotificationProvider(ABC):
    """Abstract base for notification delivery."""
    
    @abstractmethod
    async def send(
        self,
        channels: List[str],
        message: str,
        priority: str,
        tenant_id: str,
        recipients: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Send notification to specified channels."""
        pass


class MultiChannelNotifier(NotificationProvider):
    """
    Multi-channel notification orchestrator.
    
    Routes notifications to appropriate providers based on channel.
    """
    
    def __init__(
        self,
        slack_webhook: Optional[str] = None,
        teams_webhook: Optional[str] = None,
        email_config: Optional[Dict] = None,
    ):
        self.slack_webhook = slack_webhook or os.getenv("SLACK_WEBHOOK_URL")
        self.teams_webhook = teams_webhook or os.getenv("TEAMS_WEBHOOK_URL")
        self.email_config = email_config or {}
        
        if HAS_HTTPX:
            self.client = httpx.AsyncClient(timeout=30.0)
        else:
            self.client = None
    
    async def send(
        self,
        channels: List[str],
        message: str,
        priority: str,
        tenant_id: str,
        recipients: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Send notification to all specified channels."""
        results = {}
        
        for channel in channels:
            if channel == "slack":
                results["slack"] = await self._send_slack(message, priority, **kwargs)
            elif channel == "teams":
                results["teams"] = await self._send_teams(message, priority, **kwargs)
            elif channel == "email":
                results["email"] = await self._send_email(message, priority, recipients, **kwargs)
            elif channel == "sms":
                results["sms"] = {"status": "skipped", "message": "SMS not configured"}
        
        return {
            "status": "sent",
            "channels": results,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def _send_slack(
        self,
        message: str,
        priority: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Send to Slack."""
        if not self.slack_webhook or not self.client:
            return {"status": "skipped", "reason": "Not configured"}
        
        # Color based on priority
        color_map = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745",
        }
        
        payload = {
            "attachments": [
                {
                    "color": color_map.get(priority, "#6c757d"),
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"🔔 PredictrAI Alert ({priority.upper()})",
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": message,
                            }
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        try:
            response = await self.client.post(self.slack_webhook, json=payload)
            response.raise_for_status()
            return {"status": "sent"}
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _send_teams(
        self,
        message: str,
        priority: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Send to Microsoft Teams."""
        if not self.teams_webhook or not self.client:
            return {"status": "skipped", "reason": "Not configured"}
        
        # Adaptive card format
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7" if priority != "critical" else "DC3545",
            "summary": f"PredictrAI Alert - {priority}",
            "sections": [
                {
                    "activityTitle": f"🔔 PredictrAI Alert ({priority.upper()})",
                    "text": message,
                    "facts": [
                        {
                            "name": "Priority",
                            "value": priority.upper()
                        },
                        {
                            "name": "Time",
                            "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                        }
                    ],
                }
            ],
        }
        
        try:
            response = await self.client.post(self.teams_webhook, json=payload)
            response.raise_for_status()
            return {"status": "sent"}
        except Exception as e:
            logger.error(f"Teams notification failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _send_email(
        self,
        message: str,
        priority: str,
        recipients: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Send email notification."""
        # In production, use SendGrid, SES, or SMTP
        logger.info(f"Email notification queued: {message[:100]}...")
        
        return {
            "status": "queued",
            "recipients": recipients or ["admin@example.com"],
            "message": "Email queued for delivery",
        }


class SlackNotifier:
    """Direct Slack integration with interactive elements."""
    
    def __init__(self, webhook_url: Optional[str] = None, bot_token: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        
        if HAS_HTTPX:
            self.client = httpx.AsyncClient(timeout=30.0)
        else:
            self.client = None
    
    async def send_alert(
        self,
        channel: str,
        title: str,
        message: str,
        priority: str,
        asset_id: str,
        actions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send rich alert with action buttons."""
        if not self.client:
            return {"status": "error", "error": "httpx not available"}
        
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🚨 {title}"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Asset:*\n{asset_id}"},
                    {"type": "mrkdwn", "text": f"*Priority:*\n{priority.upper()}"},
                ]
            },
        ]
        
        # Add action buttons
        if actions:
            button_elements = []
            for i, action in enumerate(actions[:3]):  # Max 3 buttons
                button_elements.append({
                    "type": "button",
                    "text": {"type": "plain_text", "text": action[:20]},
                    "action_id": f"action_{i}",
                    "value": action,
                })
            
            blocks.append({
                "type": "actions",
                "elements": button_elements,
            })
        
        payload = {"channel": channel, "blocks": blocks}
        
        if self.bot_token:
            headers = {"Authorization": f"Bearer {self.bot_token}"}
            response = await self.client.post(
                "https://slack.com/api/chat.postMessage",
                json=payload,
                headers=headers,
            )
        elif self.webhook_url:
            response = await self.client.post(self.webhook_url, json=payload)
        else:
            return {"status": "error", "error": "No Slack credentials configured"}
        
        return {"status": "sent" if response.is_success else "error"}


class MockNotificationProvider(NotificationProvider):
    """Mock provider for testing."""
    
    def __init__(self):
        self.notifications: List[Dict] = []
    
    async def send(
        self,
        channels: List[str],
        message: str,
        priority: str,
        tenant_id: str,
        recipients: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        notification = {
            "channels": channels,
            "message": message,
            "priority": priority,
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.notifications.append(notification)
        logger.info(f"Mock notification: {message[:50]}...")
        
        return {"status": "sent", "mock": True}


def create_notification_provider(
    provider_type: str = "mock",
    **kwargs,
) -> NotificationProvider:
    """Factory to create notification provider."""
    if provider_type == "multi":
        return MultiChannelNotifier(**kwargs)
    else:
        return MockNotificationProvider()
