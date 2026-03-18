"""Backend Services Package."""
from app.services.email_service import EmailService, create_email_provider
from app.services.webhook_service import (
    WebhookService,
    WebhookConfig,
    WebhookEventType,
    get_webhook_service,
    get_webhook_manager,
)
from app.services.notification_orchestrator import (
    NotificationOrchestrator,
    get_notification_orchestrator,
    configure_notifications,
)
from app.services.change_intelligence import ChangeIntelligenceService, get_change_intelligence
from app.services.telemetry_normalizer import TelemetryNormalizer, get_telemetry_normalizer
from app.services.telemetry_adapter import TelemetryAdapterService, get_telemetry_adapter
from app.services.risk_engine import RiskEngine, get_risk_engine
from app.services.risk_alert_service import (
    RISK_ALERT_SOURCE,
    RiskAlertService,
    get_risk_alert_service,
)
from app.services.automation_scheduler import (
    AutomationSchedulerService,
    get_automation_scheduler,
)

__all__ = [
    "EmailService",
    "create_email_provider",
    "WebhookService",
    "WebhookConfig",
    "WebhookEventType",
    "get_webhook_service",
    "get_webhook_manager",
    "NotificationOrchestrator",
    "get_notification_orchestrator",
    "configure_notifications",
    "ChangeIntelligenceService",
    "get_change_intelligence",
    "TelemetryNormalizer",
    "get_telemetry_normalizer",
    "TelemetryAdapterService",
    "get_telemetry_adapter",
    "RiskEngine",
    "get_risk_engine",
    "RISK_ALERT_SOURCE",
    "RiskAlertService",
    "get_risk_alert_service",
    "AutomationSchedulerService",
    "get_automation_scheduler",
]
