"""
AI Maintenance Copilot - Core Agent Implementation

Autonomous agent that:
1. Observes: Monitors anomalies, drift, and system events
2. Reasons: Analyzes context and determines appropriate actions
3. Acts: Generates incidents, suggestions, and creates tickets
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events the agent monitors."""
    ANOMALY_DETECTED = "anomaly_detected"
    DRIFT_DETECTED = "drift_detected"
    RUL_CRITICAL = "rul_critical"
    ALERT_TRIGGERED = "alert_triggered"
    MAINTENANCE_DUE = "maintenance_due"
    LOG_PATTERN_DETECTED = "log_pattern_detected"


class ActionType(Enum):
    """Types of actions the agent can take."""
    CREATE_INCIDENT = "create_incident"
    SUGGEST_ACTION = "suggest_action"
    CREATE_TICKET = "create_ticket"
    SEND_NOTIFICATION = "send_notification"
    SCHEDULE_MAINTENANCE = "schedule_maintenance"
    ESCALATE = "escalate"


class Priority(Enum):
    """Priority levels for incidents."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Event:
    """Represents an observed event."""
    id: str
    type: EventType
    tenant_id: str
    asset_id: str
    timestamp: datetime
    data: Dict[str, Any]
    severity: str = "info"
    processed: bool = False


@dataclass
class Action:
    """Represents an action to be taken."""
    id: str
    type: ActionType
    priority: Priority
    tenant_id: str
    asset_id: str
    description: str
    details: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    executed: bool = False
    result: Optional[Dict[str, Any]] = None


@dataclass
class Incident:
    """Represents a maintenance incident."""
    id: str
    tenant_id: str
    asset_id: str
    title: str
    description: str
    severity: Priority
    root_cause_analysis: str
    suggested_actions: List[str]
    created_at: datetime
    related_events: List[str]
    status: str = "open"
    ticket_id: Optional[str] = None


class AgentMemory:
    """
    Agent's memory for context retention.
    
    Stores:
    - Recent events
    - Historical incidents
    - Asset context
    """
    
    def __init__(self, max_events: int = 1000):
        self.max_events = max_events
        self.events: List[Event] = []
        self.incidents: Dict[str, Incident] = {}
        self.asset_context: Dict[str, Dict] = {}
        self.action_history: List[Action] = []
    
    def add_event(self, event: Event):
        """Add event to memory."""
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
    
    def get_recent_events(
        self,
        tenant_id: str,
        asset_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        hours: int = 24,
    ) -> List[Event]:
        """Get recent events matching criteria."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            e for e in self.events
            if e.tenant_id == tenant_id
            and e.timestamp >= cutoff
            and (asset_id is None or e.asset_id == asset_id)
            and (event_type is None or e.type == event_type)
        ]
    
    def add_incident(self, incident: Incident):
        """Add incident to memory."""
        self.incidents[incident.id] = incident
    
    def get_similar_incidents(
        self,
        tenant_id: str,
        asset_id: str,
        limit: int = 5,
    ) -> List[Incident]:
        """Get similar historical incidents."""
        return [
            inc for inc in self.incidents.values()
            if inc.tenant_id == tenant_id
            and inc.asset_id == asset_id
        ][:limit]
    
    def update_asset_context(self, asset_id: str, context: Dict):
        """Update context for an asset."""
        if asset_id not in self.asset_context:
            self.asset_context[asset_id] = {}
        self.asset_context[asset_id].update(context)
    
    def get_asset_context(self, asset_id: str) -> Dict:
        """Get context for an asset."""
        return self.asset_context.get(asset_id, {})


class MaintenanceCopilot:
    """
    AI Maintenance Copilot Agent.
    
    Implements the Observe → Reason → Act loop for
    autonomous predictive maintenance operations.
    """
    
    def __init__(
        self,
        llm_provider: Optional["LLMProvider"] = None,
        ticket_provider: Optional["TicketProvider"] = None,
        notification_provider: Optional["NotificationProvider"] = None,
    ):
        self.memory = AgentMemory()
        self.llm = llm_provider
        self.tickets = ticket_provider
        self.notifications = notification_provider
        
        self.is_running = False
        self.event_queue: asyncio.Queue = asyncio.Queue()
        
        # Thresholds
        self.anomaly_threshold = 0.7
        self.rul_critical_hours = 24
        self.escalation_threshold = 3  # events within window
    
    # ==================== OBSERVE ====================
    
    async def observe(self, event: Event):
        """
        Observe and queue an event for processing.
        
        Args:
            event: The event to observe
        """
        logger.info(f"Observed event: {event.type.value} for asset {event.asset_id}")
        
        # Add to memory
        self.memory.add_event(event)
        
        # Queue for processing
        await self.event_queue.put(event)
    
    async def observe_anomaly(
        self,
        tenant_id: str,
        asset_id: str,
        anomaly_score: float,
        risk_level: str,
        explanation: Optional[Dict] = None,
    ):
        """Observe an anomaly detection result."""
        event = Event(
            id=f"anomaly_{datetime.utcnow().timestamp()}",
            type=EventType.ANOMALY_DETECTED,
            tenant_id=tenant_id,
            asset_id=asset_id,
            timestamp=datetime.utcnow(),
            severity=risk_level,
            data={
                "anomaly_score": anomaly_score,
                "risk_level": risk_level,
                "explanation": explanation or {},
            },
        )
        await self.observe(event)
    
    async def observe_drift(
        self,
        tenant_id: str,
        asset_id: str,
        drift_score: float,
        drifted_features: List[str],
    ):
        """Observe a drift detection result."""
        event = Event(
            id=f"drift_{datetime.utcnow().timestamp()}",
            type=EventType.DRIFT_DETECTED,
            tenant_id=tenant_id,
            asset_id=asset_id,
            timestamp=datetime.utcnow(),
            severity="warning",
            data={
                "drift_score": drift_score,
                "drifted_features": drifted_features,
            },
        )
        await self.observe(event)
    
    async def observe_rul(
        self,
        tenant_id: str,
        asset_id: str,
        rul_hours: float,
        confidence: Optional[float] = None,
    ):
        """Observe a RUL prediction."""
        severity = "critical" if rul_hours < 10 else "warning" if rul_hours < 50 else "info"
        
        event = Event(
            id=f"rul_{datetime.utcnow().timestamp()}",
            type=EventType.RUL_CRITICAL if rul_hours < self.rul_critical_hours else EventType.MAINTENANCE_DUE,
            tenant_id=tenant_id,
            asset_id=asset_id,
            timestamp=datetime.utcnow(),
            severity=severity,
            data={
                "rul_hours": rul_hours,
                "confidence": confidence,
            },
        )
        await self.observe(event)
    
    # ==================== REASON ====================
    
    async def reason(self, event: Event) -> List[Action]:
        """
        Reason about an event and determine actions.
        
        Uses:
        - Rule-based logic for immediate responses
        - LLM for complex reasoning (if available)
        - Historical context from memory
        
        Args:
            event: The event to reason about
        
        Returns:
            List of actions to take
        """
        actions = []
        
        # Get context
        recent_events = self.memory.get_recent_events(
            tenant_id=event.tenant_id,
            asset_id=event.asset_id,
            hours=24,
        )
        similar_incidents = self.memory.get_similar_incidents(
            tenant_id=event.tenant_id,
            asset_id=event.asset_id,
        )
        asset_context = self.memory.get_asset_context(event.asset_id)
        
        # Determine priority
        priority = self._determine_priority(event, recent_events)
        
        # Rule-based reasoning
        if event.type == EventType.ANOMALY_DETECTED:
            actions.extend(await self._reason_anomaly(event, priority, similar_incidents))
        
        elif event.type == EventType.DRIFT_DETECTED:
            actions.extend(await self._reason_drift(event, priority))
        
        elif event.type == EventType.RUL_CRITICAL:
            actions.extend(await self._reason_critical_rul(event, priority))
        
        elif event.type == EventType.MAINTENANCE_DUE:
            actions.extend(await self._reason_maintenance(event, priority))
        
        # Check for escalation
        if self._should_escalate(recent_events):
            actions.append(Action(
                id=f"escalate_{datetime.utcnow().timestamp()}",
                type=ActionType.ESCALATE,
                priority=Priority.CRITICAL,
                tenant_id=event.tenant_id,
                asset_id=event.asset_id,
                description="Multiple critical events detected - escalating to management",
                details={"event_count": len(recent_events)},
            ))
        
        return actions
    
    async def _reason_anomaly(
        self,
        event: Event,
        priority: Priority,
        similar_incidents: List[Incident],
    ) -> List[Action]:
        """Reason about anomaly detection."""
        actions = []
        score = event.data.get("anomaly_score", 0)
        risk = event.data.get("risk_level", "normal")
        explanation = event.data.get("explanation", {})
        
        if score >= self.anomaly_threshold or risk in ["warning", "critical"]:
            # Generate incident description
            incident_desc = await self._generate_incident_description(event, similar_incidents)
            
            # Create incident action
            actions.append(Action(
                id=f"incident_{datetime.utcnow().timestamp()}",
                type=ActionType.CREATE_INCIDENT,
                priority=priority,
                tenant_id=event.tenant_id,
                asset_id=event.asset_id,
                description=incident_desc["title"],
                details={
                    "full_description": incident_desc["description"],
                    "root_cause": incident_desc["root_cause"],
                    "suggested_actions": incident_desc["actions"],
                    "top_features": explanation.get("top_features", []),
                },
            ))
            
            # Add notification
            actions.append(Action(
                id=f"notify_{datetime.utcnow().timestamp()}",
                type=ActionType.SEND_NOTIFICATION,
                priority=priority,
                tenant_id=event.tenant_id,
                asset_id=event.asset_id,
                description=f"Anomaly detected: {incident_desc['title']}",
                details={"channels": ["email", "slack"]},
            ))
            
            # Create ticket for critical
            if priority in [Priority.HIGH, Priority.CRITICAL]:
                actions.append(Action(
                    id=f"ticket_{datetime.utcnow().timestamp()}",
                    type=ActionType.CREATE_TICKET,
                    priority=priority,
                    tenant_id=event.tenant_id,
                    asset_id=event.asset_id,
                    description=incident_desc["title"],
                    details={
                        "system": "jira",  # or servicenow
                        "project": "MAINT",
                        "issue_type": "Incident",
                        "description": incident_desc["description"],
                    },
                ))
        
        return actions
    
    async def _reason_drift(
        self,
        event: Event,
        priority: Priority,
    ) -> List[Action]:
        """Reason about data drift."""
        actions = []
        
        drift_score = event.data.get("drift_score", 0)
        features = event.data.get("drifted_features", [])
        
        # Suggest model retraining
        actions.append(Action(
            id=f"suggest_{datetime.utcnow().timestamp()}",
            type=ActionType.SUGGEST_ACTION,
            priority=priority,
            tenant_id=event.tenant_id,
            asset_id=event.asset_id,
            description="Data drift detected - consider model retraining",
            details={
                "action": "retrain_model",
                "drift_score": drift_score,
                "affected_features": features,
                "recommendation": f"Feature distributions have shifted for: {', '.join(features[:5])}. "
                                  "Consider retraining the anomaly detection model.",
            },
        ))
        
        return actions
    
    async def _reason_critical_rul(
        self,
        event: Event,
        priority: Priority,
    ) -> List[Action]:
        """Reason about critical RUL."""
        actions = []
        
        rul_hours = event.data.get("rul_hours", 0)
        
        # Generate maintenance recommendation
        rec = await self._generate_maintenance_recommendation(event)
        
        actions.append(Action(
            id=f"incident_{datetime.utcnow().timestamp()}",
            type=ActionType.CREATE_INCIDENT,
            priority=Priority.CRITICAL,
            tenant_id=event.tenant_id,
            asset_id=event.asset_id,
            description=f"Critical: Only {rul_hours:.0f} hours of useful life remaining",
            details={
                "rul_hours": rul_hours,
                "recommendation": rec,
                "urgency": "immediate",
            },
        ))
        
        actions.append(Action(
            id=f"schedule_{datetime.utcnow().timestamp()}",
            type=ActionType.SCHEDULE_MAINTENANCE,
            priority=Priority.CRITICAL,
            tenant_id=event.tenant_id,
            asset_id=event.asset_id,
            description="Schedule immediate maintenance",
            details={
                "type": "preventive",
                "deadline_hours": min(rul_hours * 0.8, 24),
            },
        ))
        
        actions.append(Action(
            id=f"ticket_{datetime.utcnow().timestamp()}",
            type=ActionType.CREATE_TICKET,
            priority=Priority.CRITICAL,
            tenant_id=event.tenant_id,
            asset_id=event.asset_id,
            description=f"URGENT: Asset requires immediate maintenance (RUL: {rul_hours:.0f}h)",
            details={
                "system": "jira",
                "issue_type": "Incident",
                "priority": "Highest",
            },
        ))
        
        return actions
    
    async def _reason_maintenance(
        self,
        event: Event,
        priority: Priority,
    ) -> List[Action]:
        """Reason about maintenance due."""
        actions = []
        
        rul_hours = event.data.get("rul_hours", 100)
        
        actions.append(Action(
            id=f"suggest_{datetime.utcnow().timestamp()}",
            type=ActionType.SUGGEST_ACTION,
            priority=priority,
            tenant_id=event.tenant_id,
            asset_id=event.asset_id,
            description=f"Maintenance recommended within {rul_hours:.0f} hours",
            details={
                "action": "schedule_maintenance",
                "rul_hours": rul_hours,
                "recommendation": f"Based on RUL prediction, plan maintenance within the next {rul_hours:.0f} hours.",
            },
        ))
        
        return actions
    
    def _determine_priority(
        self,
        event: Event,
        recent_events: List[Event],
    ) -> Priority:
        """Determine priority based on event and context."""
        # Base priority from severity
        if event.severity == "critical":
            base = Priority.CRITICAL
        elif event.severity == "warning":
            base = Priority.HIGH
        else:
            base = Priority.MEDIUM
        
        # Escalate if many recent events
        critical_count = sum(1 for e in recent_events if e.severity == "critical")
        if critical_count >= 3:
            return Priority.CRITICAL
        
        return base
    
    def _should_escalate(self, recent_events: List[Event]) -> bool:
        """Check if situation requires escalation."""
        critical_events = [e for e in recent_events if e.severity == "critical"]
        return len(critical_events) >= self.escalation_threshold
    
    async def _generate_incident_description(
        self,
        event: Event,
        similar_incidents: List[Incident],
    ) -> Dict[str, Any]:
        """Generate incident description using LLM or templates."""
        explanation = event.data.get("explanation", {})
        top_features = explanation.get("top_features", [])
        
        # Use LLM if available
        if self.llm:
            return await self.llm.generate_incident(event, similar_incidents)
        
        # Template-based fallback
        feature_desc = ""
        if top_features:
            feature_desc = "Contributing factors: " + ", ".join(
                f"{f['feature']} ({f.get('contribution', 0):.2f})"
                for f in top_features[:3]
            )
        
        return {
            "title": f"Anomaly detected on asset {event.asset_id}",
            "description": (
                f"An anomaly was detected with score {event.data.get('anomaly_score', 0):.2f}.\n\n"
                f"Risk Level: {event.data.get('risk_level', 'unknown').upper()}\n"
                f"Time: {event.timestamp.isoformat()}\n\n"
                f"{feature_desc}\n\n"
                f"Please investigate and take appropriate action."
            ),
            "root_cause": (
                f"Analysis indicates the primary contributing factors are: "
                f"{', '.join(f['feature'] for f in top_features[:3]) if top_features else 'undetermined'}."
            ),
            "actions": [
                "Review recent operational changes",
                "Check sensor calibration status",
                "Compare with historical baseline",
                "Inspect physical components if accessible",
            ],
        }
    
    async def _generate_maintenance_recommendation(
        self,
        event: Event,
    ) -> str:
        """Generate maintenance recommendation."""
        if self.llm:
            return await self.llm.generate_recommendation(event)
        
        rul = event.data.get("rul_hours", 0)
        return (
            f"Based on current predictions, this asset has approximately {rul:.0f} hours "
            f"of remaining useful life. Recommend scheduling preventive maintenance within "
            f"the next {min(rul * 0.5, 24):.0f} hours to avoid unplanned downtime."
        )
    
    # ==================== ACT ====================
    
    async def act(self, action: Action) -> Dict[str, Any]:
        """
        Execute an action.
        
        Args:
            action: The action to execute
        
        Returns:
            Execution result
        """
        logger.info(f"Executing action: {action.type.value} for asset {action.asset_id}")
        
        result = {"status": "success", "action_id": action.id}
        
        try:
            if action.type == ActionType.CREATE_INCIDENT:
                result = await self._create_incident(action)
            
            elif action.type == ActionType.CREATE_TICKET:
                result = await self._create_ticket(action)
            
            elif action.type == ActionType.SEND_NOTIFICATION:
                result = await self._send_notification(action)
            
            elif action.type == ActionType.SUGGEST_ACTION:
                result = await self._record_suggestion(action)
            
            elif action.type == ActionType.SCHEDULE_MAINTENANCE:
                result = await self._schedule_maintenance(action)
            
            elif action.type == ActionType.ESCALATE:
                result = await self._escalate(action)
            
            action.executed = True
            action.result = result
            self.memory.action_history.append(action)
            
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            result = {"status": "error", "error": str(e)}
            action.result = result
        
        return result
    
    async def _create_incident(self, action: Action) -> Dict[str, Any]:
        """Create an incident record."""
        incident = Incident(
            id=f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            tenant_id=action.tenant_id,
            asset_id=action.asset_id,
            title=action.description,
            description=action.details.get("full_description", ""),
            severity=action.priority,
            root_cause_analysis=action.details.get("root_cause", ""),
            suggested_actions=action.details.get("suggested_actions", []),
            created_at=datetime.utcnow(),
            related_events=[],
        )
        
        self.memory.add_incident(incident)
        
        return {
            "status": "success",
            "incident_id": incident.id,
            "incident": {
                "id": incident.id,
                "title": incident.title,
                "severity": incident.severity.value,
            },
        }
    
    async def _create_ticket(self, action: Action) -> Dict[str, Any]:
        """Create a ticket in external system."""
        if self.tickets:
            return await self.tickets.create_ticket(
                system=action.details.get("system", "jira"),
                title=action.description,
                description=action.details.get("description", ""),
                priority=action.priority.value,
                project=action.details.get("project", "MAINT"),
                issue_type=action.details.get("issue_type", "Task"),
            )
        
        # Mock response
        ticket_id = f"MAINT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        return {
            "status": "success",
            "ticket_id": ticket_id,
            "system": action.details.get("system", "jira"),
            "url": f"https://jira.example.com/browse/{ticket_id}",
        }
    
    async def _send_notification(self, action: Action) -> Dict[str, Any]:
        """Send notification."""
        if self.notifications:
            return await self.notifications.send(
                channels=action.details.get("channels", ["email"]),
                message=action.description,
                priority=action.priority.value,
                tenant_id=action.tenant_id,
            )
        
        return {
            "status": "success",
            "channels": action.details.get("channels", []),
            "message": "Notification queued",
        }
    
    async def _record_suggestion(self, action: Action) -> Dict[str, Any]:
        """Record a suggestion."""
        return {
            "status": "success",
            "suggestion": {
                "id": action.id,
                "action": action.details.get("action", ""),
                "recommendation": action.details.get("recommendation", ""),
            },
        }
    
    async def _schedule_maintenance(self, action: Action) -> Dict[str, Any]:
        """Schedule maintenance."""
        deadline = datetime.utcnow() + timedelta(
            hours=action.details.get("deadline_hours", 24)
        )
        
        return {
            "status": "success",
            "maintenance": {
                "asset_id": action.asset_id,
                "type": action.details.get("type", "preventive"),
                "deadline": deadline.isoformat(),
            },
        }
    
    async def _escalate(self, action: Action) -> Dict[str, Any]:
        """Escalate to management."""
        if self.notifications:
            await self.notifications.send(
                channels=["email", "sms"],
                message=f"ESCALATION: {action.description}",
                priority="critical",
                tenant_id=action.tenant_id,
                recipients=["management"],
            )
        
        return {
            "status": "escalated",
            "description": action.description,
        }
    
    # ==================== MAIN LOOP ====================
    
    async def run(self):
        """Run the agent's main processing loop."""
        self.is_running = True
        logger.info("AI Maintenance Copilot started")
        
        while self.is_running:
            try:
                # Wait for event
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )
                
                # Process event
                await self.process_event(event)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in agent loop: {e}")
    
    async def process_event(self, event: Event):
        """Process a single event through observe-reason-act."""
        # Already observed, now reason
        actions = await self.reason(event)
        
        # Execute actions
        for action in actions:
            await self.act(action)
        
        event.processed = True
    
    def stop(self):
        """Stop the agent."""
        self.is_running = False
        logger.info("AI Maintenance Copilot stopped")
