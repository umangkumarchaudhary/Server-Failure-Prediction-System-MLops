"""
Event Monitor - Observes ML pipeline and feeds events to agent.

Connects:
- Anomaly detection results
- Drift detection results
- RUL predictions
- Log analysis results
"""
import asyncio
from datetime import datetime
from typing import Dict, Optional, Any, Callable
import logging

from ml.agent.copilot import MaintenanceCopilot, EventType

logger = logging.getLogger(__name__)


class EventMonitor:
    """
    Monitors ML pipeline outputs and feeds events to the AI copilot.
    
    Acts as the bridge between:
    - InferencePipeline → Copilot (anomalies, RUL)
    - DriftDetector → Copilot (drift events)
    - LogAnalyzer → Copilot (log patterns)
    """
    
    def __init__(
        self,
        copilot: MaintenanceCopilot,
        anomaly_threshold: float = 0.7,
        rul_warning_hours: float = 48.0,
        drift_threshold: float = 0.5,
    ):
        self.copilot = copilot
        self.anomaly_threshold = anomaly_threshold
        self.rul_warning_hours = rul_warning_hours
        self.drift_threshold = drift_threshold
        
        self.is_running = False
        self._event_handlers: Dict[str, Callable] = {}
    
    async def on_prediction(
        self,
        tenant_id: str,
        asset_id: str,
        prediction_type: str,
        result: Dict[str, Any],
    ):
        """
        Handle a prediction result from the inference pipeline.
        
        Args:
            tenant_id: Tenant ID
            asset_id: Asset ID
            prediction_type: Type of prediction (anomaly, rul)
            result: Prediction result
        """
        if prediction_type == "anomaly":
            score = result.get("anomaly_score", 0)
            risk = result.get("risk_level", "normal")
            
            if score >= self.anomaly_threshold or risk in ["warning", "critical"]:
                await self.copilot.observe_anomaly(
                    tenant_id=tenant_id,
                    asset_id=asset_id,
                    anomaly_score=score,
                    risk_level=risk,
                    explanation=result.get("explanation"),
                )
        
        elif prediction_type == "rul":
            rul = result.get("rul_estimate", 999)
            
            if rul <= self.rul_warning_hours:
                await self.copilot.observe_rul(
                    tenant_id=tenant_id,
                    asset_id=asset_id,
                    rul_hours=rul,
                    confidence=result.get("confidence"),
                )
    
    async def on_drift_detected(
        self,
        tenant_id: str,
        asset_id: str,
        drift_result: Dict[str, Any],
    ):
        """
        Handle drift detection result.
        
        Args:
            tenant_id: Tenant ID
            asset_id: Asset ID
            drift_result: Drift detection result
        """
        drift_score = drift_result.get("overall_drift_score", 0)
        drifted = drift_result.get("drifted_features", [])
        
        if drift_score >= self.drift_threshold or len(drifted) >= 2:
            await self.copilot.observe_drift(
                tenant_id=tenant_id,
                asset_id=asset_id,
                drift_score=drift_score,
                drifted_features=[f["feature"] for f in drifted] if isinstance(drifted[0], dict) else drifted,
            )
    
    async def on_log_pattern(
        self,
        tenant_id: str,
        asset_id: str,
        pattern: Dict[str, Any],
    ):
        """
        Handle significant log pattern detection.
        
        Args:
            tenant_id: Tenant ID
            asset_id: Asset ID
            pattern: Detected log pattern
        """
        from ml.agent.copilot import Event
        
        event = Event(
            id=f"log_{datetime.utcnow().timestamp()}",
            type=EventType.LOG_PATTERN_DETECTED,
            tenant_id=tenant_id,
            asset_id=asset_id,
            timestamp=datetime.utcnow(),
            severity="warning",
            data=pattern,
        )
        
        await self.copilot.observe(event)
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register custom event handler."""
        self._event_handlers[event_type] = handler
    
    async def start(self):
        """Start the event monitor."""
        self.is_running = True
        logger.info("Event monitor started")
        
        # Start copilot processing loop
        asyncio.create_task(self.copilot.run())
    
    def stop(self):
        """Stop the event monitor."""
        self.is_running = False
        self.copilot.stop()
        logger.info("Event monitor stopped")


class CopilotService:
    """
    High-level service that manages the AI copilot lifecycle.
    
    Use this in your FastAPI application.
    """
    
    _instance: Optional["CopilotService"] = None
    
    def __init__(
        self,
        llm_provider_type: str = "mock",
        ticket_provider_type: str = "mock",
        **kwargs,
    ):
        from ml.agent.llm_provider import create_llm_provider
        from ml.agent.ticket_provider import create_ticket_provider
        from ml.agent.notification_provider import create_notification_provider
        
        # Create providers
        self.llm = create_llm_provider(llm_provider_type, **kwargs.get("llm_config", {}))
        self.tickets = create_ticket_provider(ticket_provider_type, **kwargs.get("ticket_config", {}))
        self.notifications = create_notification_provider(
            kwargs.get("notification_provider_type", "mock"),
            **kwargs.get("notification_config", {}),
        )
        
        # Create copilot
        self.copilot = MaintenanceCopilot(
            llm_provider=self.llm,
            ticket_provider=self.tickets,
            notification_provider=self.notifications,
        )
        
        # Create monitor
        self.monitor = EventMonitor(self.copilot)
    
    @classmethod
    def get_instance(cls, **kwargs) -> "CopilotService":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance
    
    async def start(self):
        """Start the copilot service."""
        await self.monitor.start()
    
    def stop(self):
        """Stop the copilot service."""
        self.monitor.stop()
    
    async def chat(
        self,
        message: str,
        tenant_id: str,
        asset_id: Optional[str] = None,
    ) -> str:
        """
        Chat with the AI copilot.
        
        Args:
            message: User message
            tenant_id: Tenant ID
            asset_id: Optional asset context
        
        Returns:
            Copilot response
        """
        context = {"tenant_id": tenant_id}
        
        if asset_id:
            context["asset_id"] = asset_id
            context["asset_context"] = self.copilot.memory.get_asset_context(asset_id)
            
            # Get recent events for context
            recent = self.copilot.memory.get_recent_events(tenant_id, asset_id, hours=24)
            context["recent_events"] = [
                {"type": e.type.value, "severity": e.severity, "time": e.timestamp.isoformat()}
                for e in recent[-5:]
            ]
        
        return await self.llm.chat(message, context)
    
    async def get_suggestions(
        self,
        tenant_id: str,
        asset_id: str,
    ) -> Dict[str, Any]:
        """
        Get AI suggestions for an asset.
        
        Args:
            tenant_id: Tenant ID
            asset_id: Asset ID
        
        Returns:
            Suggestions based on recent events
        """
        recent_events = self.copilot.memory.get_recent_events(
            tenant_id=tenant_id,
            asset_id=asset_id,
            hours=24,
        )
        
        similar_incidents = self.copilot.memory.get_similar_incidents(
            tenant_id=tenant_id,
            asset_id=asset_id,
        )
        
        # Find recent suggestions in action history
        suggestions = [
            {
                "action": a.details.get("action", ""),
                "recommendation": a.details.get("recommendation", ""),
                "priority": a.priority.value,
            }
            for a in self.copilot.memory.action_history[-10:]
            if a.asset_id == asset_id and a.type.value == "suggest_action"
        ]
        
        return {
            "asset_id": asset_id,
            "suggestions": suggestions,
            "recent_event_count": len(recent_events),
            "similar_incident_count": len(similar_incidents),
        }
