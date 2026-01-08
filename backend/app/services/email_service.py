"""
Email Provider - Production email delivery service.

Supports:
- SendGrid
- AWS SES
- SMTP
"""
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

logger = logging.getLogger(__name__)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class EmailProvider(ABC):
    """Abstract base for email providers."""
    
    @abstractmethod
    async def send(
        self,
        to: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        priority: str = "medium",
        **kwargs,
    ) -> Dict[str, Any]:
        """Send an email."""
        pass


class SendGridProvider(EmailProvider):
    """SendGrid email provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: str = "PredictrAI",
    ):
        if not HAS_HTTPX:
            raise ImportError("httpx package not installed")
        
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        self.from_email = from_email or os.getenv("SENDGRID_FROM_EMAIL", "alerts@predictr.ai")
        self.from_name = from_name
        
        self.client = httpx.AsyncClient(
            base_url="https://api.sendgrid.com/v3",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
    
    async def send(
        self,
        to: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        priority: str = "medium",
        **kwargs,
    ) -> Dict[str, Any]:
        """Send via SendGrid."""
        personalizations = [{"to": [{"email": addr} for addr in to]}]
        
        content = [{"type": "text/plain", "value": body}]
        if html_body:
            content.append({"type": "text/html", "value": html_body})
        
        payload = {
            "personalizations": personalizations,
            "from": {"email": self.from_email, "name": self.from_name},
            "subject": subject,
            "content": content,
        }
        
        # Add categories for tracking
        if "category" in kwargs:
            payload["categories"] = [kwargs["category"]]
        
        try:
            response = await self.client.post("/mail/send", json=payload)
            
            if response.status_code in [200, 201, 202]:
                return {
                    "status": "sent",
                    "provider": "sendgrid",
                    "message_id": response.headers.get("X-Message-Id"),
                }
            else:
                logger.error(f"SendGrid error: {response.text}")
                return {"status": "error", "error": response.text}
        except Exception as e:
            logger.error(f"SendGrid send failed: {e}")
            return {"status": "error", "error": str(e)}


class AmazonSESProvider(EmailProvider):
    """AWS SES email provider."""
    
    def __init__(
        self,
        region: Optional[str] = None,
        from_email: Optional[str] = None,
    ):
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.from_email = from_email or os.getenv("SES_FROM_EMAIL", "alerts@predictr.ai")
        
        try:
            import boto3
            self.client = boto3.client("ses", region_name=self.region)
            self.available = True
        except ImportError:
            logger.warning("boto3 not installed, SES provider unavailable")
            self.client = None
            self.available = False
    
    async def send(
        self,
        to: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        priority: str = "medium",
        **kwargs,
    ) -> Dict[str, Any]:
        """Send via AWS SES."""
        if not self.available:
            return {"status": "error", "error": "boto3 not installed"}
        
        try:
            message = {
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body}},
            }
            
            if html_body:
                message["Body"]["Html"] = {"Data": html_body}
            
            response = self.client.send_email(
                Source=self.from_email,
                Destination={"ToAddresses": to},
                Message=message,
            )
            
            return {
                "status": "sent",
                "provider": "ses",
                "message_id": response["MessageId"],
            }
        except Exception as e:
            logger.error(f"SES send failed: {e}")
            return {"status": "error", "error": str(e)}


class SMTPProvider(EmailProvider):
    """SMTP email provider for self-hosted email."""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        from_email: Optional[str] = None,
        use_tls: bool = True,
    ):
        self.host = host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", str(port)))
        self.username = username or os.getenv("SMTP_USERNAME")
        self.password = password or os.getenv("SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("SMTP_FROM_EMAIL", self.username)
        self.use_tls = use_tls
    
    async def send(
        self,
        to: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        priority: str = "medium",
        **kwargs,
    ) -> Dict[str, Any]:
        """Send via SMTP."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = ", ".join(to)
            
            # Priority headers
            if priority == "critical":
                msg["X-Priority"] = "1"
                msg["X-MSMail-Priority"] = "High"
            elif priority == "high":
                msg["X-Priority"] = "2"
            
            msg.attach(MIMEText(body, "plain"))
            if html_body:
                msg.attach(MIMEText(html_body, "html"))
            
            # Send
            context = ssl.create_default_context()
            
            if self.use_tls:
                with smtplib.SMTP(self.host, self.port) as server:
                    server.starttls(context=context)
                    if self.username and self.password:
                        server.login(self.username, self.password)
                    server.sendmail(self.from_email, to, msg.as_string())
            else:
                with smtplib.SMTP_SSL(self.host, self.port, context=context) as server:
                    if self.username and self.password:
                        server.login(self.username, self.password)
                    server.sendmail(self.from_email, to, msg.as_string())
            
            return {
                "status": "sent",
                "provider": "smtp",
                "recipients": to,
            }
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return {"status": "error", "error": str(e)}


class EmailService:
    """
    High-level email service for PredictrAI.
    
    Handles:
    - Template rendering
    - Priority-based routing
    - Rate limiting
    """
    
    def __init__(
        self,
        provider: EmailProvider,
        default_recipients: Optional[List[str]] = None,
    ):
        self.provider = provider
        self.default_recipients = default_recipients or []
    
    async def send_alert(
        self,
        recipients: List[str],
        alert_type: str,
        asset_name: str,
        message: str,
        priority: str = "medium",
        details: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Send an alert email with template."""
        subject = self._get_subject(alert_type, priority, asset_name)
        body = self._render_text_body(alert_type, asset_name, message, details)
        html_body = self._render_html_body(alert_type, asset_name, message, priority, details)
        
        return await self.provider.send(
            to=recipients or self.default_recipients,
            subject=subject,
            body=body,
            html_body=html_body,
            priority=priority,
            category="predictr-alert",
        )
    
    async def send_incident(
        self,
        recipients: List[str],
        incident_id: str,
        title: str,
        description: str,
        severity: str,
        suggested_actions: List[str],
    ) -> Dict[str, Any]:
        """Send incident notification."""
        subject = f"[{severity.upper()}] Incident {incident_id}: {title}"
        
        body = f"""
PredictrAI Incident Report

Incident ID: {incident_id}
Severity: {severity.upper()}

{title}

{description}

Suggested Actions:
{chr(10).join(f'  - {action}' for action in suggested_actions)}

---
View in PredictrAI Dashboard: https://app.predictr.ai/incidents/{incident_id}
"""
        
        html_body = self._render_incident_html(
            incident_id, title, description, severity, suggested_actions
        )
        
        priority = "critical" if severity == "critical" else "high"
        
        return await self.provider.send(
            to=recipients,
            subject=subject,
            body=body,
            html_body=html_body,
            priority=priority,
            category="predictr-incident",
        )
    
    async def send_digest(
        self,
        recipients: List[str],
        tenant_name: str,
        stats: Dict[str, Any],
        top_alerts: List[Dict],
    ) -> Dict[str, Any]:
        """Send daily digest email."""
        subject = f"PredictrAI Daily Digest - {tenant_name}"
        
        body = f"""
Daily Digest for {tenant_name}
{datetime.utcnow().strftime('%Y-%m-%d')}

Summary:
- Total Assets: {stats.get('total_assets', 0)}
- Healthy: {stats.get('healthy', 0)}
- Warning: {stats.get('warning', 0)}
- Critical: {stats.get('critical', 0)}
- Active Alerts: {stats.get('active_alerts', 0)}

Top Alerts:
{chr(10).join(f"  - {a.get('message', 'N/A')}" for a in top_alerts[:5])}

View full report: https://app.predictr.ai/dashboard
"""
        
        return await self.provider.send(
            to=recipients,
            subject=subject,
            body=body,
            priority="low",
            category="predictr-digest",
        )
    
    def _get_subject(self, alert_type: str, priority: str, asset_name: str) -> str:
        """Generate email subject."""
        prefix = "🚨" if priority == "critical" else "⚠️" if priority == "high" else "ℹ️"
        return f"{prefix} PredictrAI Alert: {alert_type} on {asset_name}"
    
    def _render_text_body(
        self,
        alert_type: str,
        asset_name: str,
        message: str,
        details: Optional[Dict],
    ) -> str:
        """Render plain text email body."""
        body = f"""
PredictrAI Alert Notification

Alert Type: {alert_type}
Asset: {asset_name}
Time: {datetime.utcnow().isoformat()}

{message}
"""
        if details:
            body += "\nDetails:\n"
            for key, value in details.items():
                body += f"  - {key}: {value}\n"
        
        body += "\n---\nView in dashboard: https://app.predictr.ai/alerts"
        return body
    
    def _render_html_body(
        self,
        alert_type: str,
        asset_name: str,
        message: str,
        priority: str,
        details: Optional[Dict],
    ) -> str:
        """Render HTML email body."""
        color = "#dc3545" if priority == "critical" else "#fd7e14" if priority == "high" else "#0d6efd"
        
        details_html = ""
        if details:
            details_html = "<ul style='margin: 0; padding-left: 20px;'>"
            for key, value in details.items():
                details_html += f"<li><strong>{key}:</strong> {value}</li>"
            details_html += "</ul>"
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <div style="background: {color}; padding: 20px; text-align: center;">
            <h1 style="margin: 0; color: white; font-size: 24px;">PredictrAI Alert</h1>
        </div>
        <div style="padding: 30px;">
            <p style="margin: 0 0 10px; color: #666; font-size: 14px;">{alert_type}</p>
            <h2 style="margin: 0 0 20px; color: #333;">{asset_name}</h2>
            <p style="margin: 0 0 20px; color: #333; line-height: 1.6;">{message}</p>
            {f'<div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 20px;">{details_html}</div>' if details_html else ''}
            <a href="https://app.predictr.ai/alerts" style="display: inline-block; background: {color}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 500;">View in Dashboard</a>
        </div>
        <div style="background: #f8f9fa; padding: 15px; text-align: center; color: #666; font-size: 12px;">
            <p style="margin: 0;">PredictrAI - Universal Predictive Maintenance</p>
        </div>
    </div>
</body>
</html>
"""
    
    def _render_incident_html(
        self,
        incident_id: str,
        title: str,
        description: str,
        severity: str,
        actions: List[str],
    ) -> str:
        """Render incident HTML email."""
        color = "#dc3545" if severity == "critical" else "#fd7e14" if severity == "high" else "#ffc107"
        
        actions_html = "".join(f"<li style='margin-bottom: 8px;'>{a}</li>" for a in actions)
        
        return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden;">
        <div style="background: {color}; padding: 20px;">
            <span style="color: white; font-size: 12px; text-transform: uppercase;">Incident {incident_id}</span>
            <h1 style="margin: 10px 0 0; color: white; font-size: 20px;">{title}</h1>
        </div>
        <div style="padding: 30px;">
            <p style="color: #333; line-height: 1.6;">{description}</p>
            <h3 style="margin: 20px 0 10px; color: #333;">Suggested Actions</h3>
            <ul style="color: #555; line-height: 1.6;">{actions_html}</ul>
            <a href="https://app.predictr.ai/incidents/{incident_id}" style="display: inline-block; background: #0d6efd; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px;">View Incident</a>
        </div>
    </div>
</body>
</html>
"""


def create_email_provider(
    provider_type: str = "smtp",
    **kwargs,
) -> EmailProvider:
    """Factory to create email provider."""
    if provider_type == "sendgrid":
        return SendGridProvider(**kwargs)
    elif provider_type == "ses":
        return AmazonSESProvider(**kwargs)
    else:
        return SMTPProvider(**kwargs)
