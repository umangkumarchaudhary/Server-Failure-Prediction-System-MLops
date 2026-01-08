"""
AI Maintenance Copilot Agent Package.

Provides:
- MaintenanceCopilot: Core agent with observe-reason-act loop
- LLM providers: OpenAI, Ollama, Mock
- Ticket providers: Jira, ServiceNow, Webhook
- Notification providers: Slack, Teams, Email
- Event monitor: Bridge between ML pipeline and agent
- CopilotService: High-level FastAPI integration
"""
from ml.agent.copilot import (
    MaintenanceCopilot,
    Event,
    EventType,
    Action,
    ActionType,
    Priority,
    Incident,
    AgentMemory,
)
from ml.agent.llm_provider import (
    LLMProvider,
    OpenAIProvider,
    OllamaProvider,
    MockLLMProvider,
    create_llm_provider,
)
from ml.agent.ticket_provider import (
    TicketProvider,
    JiraProvider,
    ServiceNowProvider,
    WebhookProvider,
    MockTicketProvider,
    create_ticket_provider,
)
from ml.agent.notification_provider import (
    NotificationProvider,
    MultiChannelNotifier,
    MockNotificationProvider,
    create_notification_provider,
)
from ml.agent.event_monitor import (
    EventMonitor,
    CopilotService,
)

__all__ = [
    # Core
    "MaintenanceCopilot",
    "Event",
    "EventType",
    "Action",
    "ActionType",
    "Priority",
    "Incident",
    "AgentMemory",
    # LLM
    "LLMProvider",
    "OpenAIProvider",
    "OllamaProvider",
    "MockLLMProvider",
    "create_llm_provider",
    # Tickets
    "TicketProvider",
    "JiraProvider",
    "ServiceNowProvider",
    "WebhookProvider",
    "MockTicketProvider",
    "create_ticket_provider",
    # Notifications
    "NotificationProvider",
    "MultiChannelNotifier",
    "MockNotificationProvider",
    "create_notification_provider",
    # Service
    "EventMonitor",
    "CopilotService",
]
