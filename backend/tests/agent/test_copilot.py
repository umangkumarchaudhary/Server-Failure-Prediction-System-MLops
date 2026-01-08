"""
Unit Tests for AI Copilot Agent Decision Logic.
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ml.agent.copilot import (
    MaintenanceCopilot,
    Event,
    EventType,
    Action,
    ActionType,
    Priority,
    AgentMemory,
)


class TestAgentMemory:
    """Tests for AgentMemory class."""
    
    @pytest.mark.unit
    @pytest.mark.agent
    def test_add_event(self, sample_tenant_id, sample_asset_id):
        """Test adding events to memory."""
        memory = AgentMemory()
        
        event = Event(
            id="test_event_1",
            type=EventType.ANOMALY_DETECTED,
            tenant_id=str(sample_tenant_id),
            asset_id=str(sample_asset_id),
            timestamp=datetime.utcnow(),
            data={"anomaly_score": 0.8},
            severity="warning",
        )
        
        memory.add_event(event)
        
        assert len(memory.events) == 1
        assert memory.events[0].id == "test_event_1"
    
    @pytest.mark.unit
    @pytest.mark.agent
    def test_get_recent_events(self, sample_tenant_id, sample_asset_id):
        """Test retrieving recent events."""
        memory = AgentMemory()
        
        # Add events
        for i in range(5):
            event = Event(
                id=f"event_{i}",
                type=EventType.ANOMALY_DETECTED,
                tenant_id=str(sample_tenant_id),
                asset_id=str(sample_asset_id),
                timestamp=datetime.utcnow(),
                data={},
            )
            memory.add_event(event)
        
        recent = memory.get_recent_events(str(sample_tenant_id), hours=1)
        
        assert len(recent) == 5
    
    @pytest.mark.unit
    @pytest.mark.agent
    def test_get_events_filtered_by_asset(self, sample_tenant_id):
        """Test filtering events by asset."""
        memory = AgentMemory()
        
        asset_1 = "asset_1"
        asset_2 = "asset_2"
        
        # Add events for different assets
        for asset in [asset_1, asset_1, asset_2]:
            event = Event(
                id=f"event_{asset}_{datetime.utcnow().timestamp()}",
                type=EventType.ANOMALY_DETECTED,
                tenant_id=str(sample_tenant_id),
                asset_id=asset,
                timestamp=datetime.utcnow(),
                data={},
            )
            memory.add_event(event)
        
        recent_1 = memory.get_recent_events(str(sample_tenant_id), asset_id=asset_1)
        recent_2 = memory.get_recent_events(str(sample_tenant_id), asset_id=asset_2)
        
        assert len(recent_1) == 2
        assert len(recent_2) == 1
    
    @pytest.mark.unit
    @pytest.mark.agent
    def test_memory_limit(self):
        """Test memory enforces max events limit."""
        memory = AgentMemory(max_events=10)
        
        for i in range(20):
            event = Event(
                id=f"event_{i}",
                type=EventType.ANOMALY_DETECTED,
                tenant_id="tenant_1",
                asset_id="asset_1",
                timestamp=datetime.utcnow(),
                data={},
            )
            memory.add_event(event)
        
        assert len(memory.events) == 10


class TestMaintenanceCopilot:
    """Tests for MaintenanceCopilot decision logic."""
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_observe_anomaly(
        self,
        mock_llm_provider,
        mock_ticket_provider,
        mock_notification_provider,
        sample_tenant_id,
        sample_asset_id,
    ):
        """Test observing anomaly events."""
        copilot = MaintenanceCopilot(
            llm_provider=mock_llm_provider,
            ticket_provider=mock_ticket_provider,
            notification_provider=mock_notification_provider,
        )
        
        await copilot.observe_anomaly(
            tenant_id=str(sample_tenant_id),
            asset_id=str(sample_asset_id),
            anomaly_score=0.85,
            risk_level="critical",
            explanation={"top_features": []},
        )
        
        # Event should be queued
        assert not copilot.event_queue.empty()
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_reason_high_anomaly_creates_incident(
        self,
        mock_llm_provider,
        mock_ticket_provider,
        mock_notification_provider,
        sample_tenant_id,
        sample_asset_id,
    ):
        """Test that high anomaly triggers incident creation."""
        copilot = MaintenanceCopilot(
            llm_provider=mock_llm_provider,
            ticket_provider=mock_ticket_provider,
            notification_provider=mock_notification_provider,
        )
        copilot.anomaly_threshold = 0.7
        
        event = Event(
            id="test_anomaly",
            type=EventType.ANOMALY_DETECTED,
            tenant_id=str(sample_tenant_id),
            asset_id=str(sample_asset_id),
            timestamp=datetime.utcnow(),
            severity="critical",
            data={
                "anomaly_score": 0.9,
                "risk_level": "critical",
            },
        )
        
        actions = await copilot.reason(event)
        
        # Should have incident, notification, and ticket actions
        action_types = [a.type for a in actions]
        assert ActionType.CREATE_INCIDENT in action_types
        assert ActionType.SEND_NOTIFICATION in action_types
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_reason_critical_rul_creates_maintenance(
        self,
        mock_llm_provider,
        mock_ticket_provider,
        mock_notification_provider,
        sample_tenant_id,
        sample_asset_id,
    ):
        """Test that critical RUL triggers maintenance scheduling."""
        copilot = MaintenanceCopilot(
            llm_provider=mock_llm_provider,
            ticket_provider=mock_ticket_provider,
            notification_provider=mock_notification_provider,
        )
        copilot.rul_critical_hours = 24
        
        event = Event(
            id="test_rul",
            type=EventType.RUL_CRITICAL,
            tenant_id=str(sample_tenant_id),
            asset_id=str(sample_asset_id),
            timestamp=datetime.utcnow(),
            severity="critical",
            data={"rul_hours": 12},
        )
        
        actions = await copilot.reason(event)
        
        action_types = [a.type for a in actions]
        assert ActionType.SCHEDULE_MAINTENANCE in action_types
        assert ActionType.CREATE_TICKET in action_types
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_reason_drift_suggests_retrain(
        self,
        mock_llm_provider,
        mock_ticket_provider,
        mock_notification_provider,
        sample_tenant_id,
        sample_asset_id,
    ):
        """Test that drift detection suggests retraining."""
        copilot = MaintenanceCopilot(
            llm_provider=mock_llm_provider,
            ticket_provider=mock_ticket_provider,
            notification_provider=mock_notification_provider,
        )
        
        event = Event(
            id="test_drift",
            type=EventType.DRIFT_DETECTED,
            tenant_id=str(sample_tenant_id),
            asset_id=str(sample_asset_id),
            timestamp=datetime.utcnow(),
            severity="warning",
            data={
                "drift_score": 0.6,
                "drifted_features": ["temperature", "vibration"],
            },
        )
        
        actions = await copilot.reason(event)
        
        action_types = [a.type for a in actions]
        assert ActionType.SUGGEST_ACTION in action_types
        
        # Check retrain suggestion
        suggest_action = next(a for a in actions if a.type == ActionType.SUGGEST_ACTION)
        assert "retrain" in suggest_action.details.get("action", "").lower()
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_act_creates_incident(
        self,
        mock_llm_provider,
        mock_ticket_provider,
        mock_notification_provider,
        sample_tenant_id,
        sample_asset_id,
    ):
        """Test incident creation action."""
        copilot = MaintenanceCopilot(
            llm_provider=mock_llm_provider,
            ticket_provider=mock_ticket_provider,
            notification_provider=mock_notification_provider,
        )
        
        action = Action(
            id="test_action",
            type=ActionType.CREATE_INCIDENT,
            priority=Priority.HIGH,
            tenant_id=str(sample_tenant_id),
            asset_id=str(sample_asset_id),
            description="Test incident",
            details={
                "full_description": "Full test description",
                "root_cause": "Test root cause",
                "suggested_actions": ["Action 1"],
            },
        )
        
        result = await copilot.act(action)
        
        assert result["status"] == "success"
        assert "incident_id" in result
        assert action.executed == True
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_act_creates_ticket(
        self,
        mock_llm_provider,
        mock_ticket_provider,
        mock_notification_provider,
        sample_tenant_id,
        sample_asset_id,
    ):
        """Test ticket creation action."""
        copilot = MaintenanceCopilot(
            llm_provider=mock_llm_provider,
            ticket_provider=mock_ticket_provider,
            notification_provider=mock_notification_provider,
        )
        
        action = Action(
            id="test_ticket_action",
            type=ActionType.CREATE_TICKET,
            priority=Priority.HIGH,
            tenant_id=str(sample_tenant_id),
            asset_id=str(sample_asset_id),
            description="Test ticket",
            details={
                "system": "jira",
                "project": "MAINT",
            },
        )
        
        result = await copilot.act(action)
        
        assert result["status"] == "success"
        assert "ticket_id" in result
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_escalation_on_multiple_critical_events(
        self,
        mock_llm_provider,
        mock_ticket_provider,
        mock_notification_provider,
        sample_tenant_id,
        sample_asset_id,
    ):
        """Test escalation triggers on multiple critical events."""
        copilot = MaintenanceCopilot(
            llm_provider=mock_llm_provider,
            ticket_provider=mock_ticket_provider,
            notification_provider=mock_notification_provider,
        )
        copilot.escalation_threshold = 3
        
        # Add multiple critical events
        for i in range(4):
            event = Event(
                id=f"critical_{i}",
                type=EventType.ANOMALY_DETECTED,
                tenant_id=str(sample_tenant_id),
                asset_id=str(sample_asset_id),
                timestamp=datetime.utcnow(),
                severity="critical",
                data={"anomaly_score": 0.95},
            )
            copilot.memory.add_event(event)
        
        # New event should trigger escalation
        new_event = Event(
            id="trigger_event",
            type=EventType.ANOMALY_DETECTED,
            tenant_id=str(sample_tenant_id),
            asset_id=str(sample_asset_id),
            timestamp=datetime.utcnow(),
            severity="critical",
            data={"anomaly_score": 0.9, "risk_level": "critical"},
        )
        
        actions = await copilot.reason(new_event)
        
        action_types = [a.type for a in actions]
        assert ActionType.ESCALATE in action_types
