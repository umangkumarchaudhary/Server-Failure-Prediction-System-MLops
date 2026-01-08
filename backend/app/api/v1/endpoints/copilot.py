"""
Copilot API Endpoints - AI Assistant Interface.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import asyncio

from app.models import User
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


# ============ Schemas ============

class ChatRequest(BaseModel):
    """Chat message request."""
    message: str
    asset_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat message response."""
    response: str
    suggestions: Optional[List[str]] = None
    timestamp: str


class SuggestionsResponse(BaseModel):
    """AI suggestions response."""
    asset_id: str
    suggestions: List[dict]
    recent_event_count: int
    similar_incident_count: int


class IncidentDraft(BaseModel):
    """AI-generated incident draft."""
    title: str
    description: str
    root_cause: str
    suggested_actions: List[str]
    priority: str


# ============ Service Instance ============

_copilot_service = None

def get_copilot_service():
    """Get or create copilot service instance."""
    global _copilot_service
    
    if _copilot_service is None:
        from ml.agent import CopilotService
        _copilot_service = CopilotService.get_instance(
            llm_provider_type="mock",  # Use "openai" in production
            ticket_provider_type="mock",
        )
    
    return _copilot_service


# ============ Endpoints ============

@router.post("/chat", response_model=ChatResponse)
async def chat_with_copilot(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Chat with the AI maintenance copilot.
    
    The copilot can answer questions about:
    - Asset health and anomalies
    - Maintenance recommendations
    - Historical incidents
    - Best practices
    """
    service = get_copilot_service()
    
    response = await service.chat(
        message=request.message,
        tenant_id=str(current_user.tenant_id),
        asset_id=request.asset_id,
    )
    
    return ChatResponse(
        response=response,
        suggestions=None,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/suggestions/{asset_id}", response_model=SuggestionsResponse)
async def get_suggestions(
    asset_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get AI-generated suggestions for an asset.
    
    Returns proactive maintenance recommendations based on
    recent events, predictions, and historical patterns.
    """
    service = get_copilot_service()
    
    result = await service.get_suggestions(
        tenant_id=str(current_user.tenant_id),
        asset_id=asset_id,
    )
    
    return SuggestionsResponse(**result)


@router.post("/draft-incident/{asset_id}", response_model=IncidentDraft)
async def draft_incident(
    asset_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Generate an AI-drafted incident description for an asset.
    
    Uses recent anomalies, predictions, and historical context
    to create a comprehensive incident report.
    """
    service = get_copilot_service()
    tenant_id = str(current_user.tenant_id)
    
    # Get recent events
    recent_events = service.copilot.memory.get_recent_events(
        tenant_id=tenant_id,
        asset_id=asset_id,
        hours=24,
    )
    
    if not recent_events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recent events found for this asset",
        )
    
    # Use most recent event
    latest_event = recent_events[-1]
    similar = service.copilot.memory.get_similar_incidents(tenant_id, asset_id)
    
    # Generate incident
    incident = await service.llm.generate_incident(latest_event, similar)
    
    # Determine priority
    priority = "medium"
    if latest_event.severity == "critical":
        priority = "critical"
    elif latest_event.severity == "warning":
        priority = "high"
    
    return IncidentDraft(
        title=incident.get("title", f"Incident on {asset_id}"),
        description=incident.get("description", ""),
        root_cause=incident.get("root_cause", ""),
        suggested_actions=incident.get("actions", []),
        priority=priority,
    )


@router.get("/activity/{asset_id}")
async def get_agent_activity(
    asset_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get recent AI agent activity for an asset.
    
    Shows what actions the copilot has taken, including
    incidents created, tickets filed, and notifications sent.
    """
    service = get_copilot_service()
    tenant_id = str(current_user.tenant_id)
    
    # Get from agent memory
    actions = [
        {
            "id": a.id,
            "type": a.type.value,
            "description": a.description,
            "priority": a.priority.value,
            "executed": a.executed,
            "created_at": a.created_at.isoformat(),
            "result": a.result,
        }
        for a in service.copilot.memory.action_history
        if a.asset_id == asset_id
    ][-20:]  # Last 20
    
    events = [
        {
            "id": e.id,
            "type": e.type.value,
            "severity": e.severity,
            "timestamp": e.timestamp.isoformat(),
            "processed": e.processed,
        }
        for e in service.copilot.memory.events
        if e.asset_id == asset_id
    ][-20:]
    
    return {
        "asset_id": asset_id,
        "actions": actions,
        "events": events,
    }


@router.post("/escalate/{asset_id}")
async def escalate_to_human(
    asset_id: str,
    reason: str,
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger escalation for an asset.
    
    Notifies management and creates high-priority ticket.
    """
    service = get_copilot_service()
    
    from ml.agent.copilot import Action, ActionType, Priority
    
    action = Action(
        id=f"manual_escalate_{datetime.utcnow().timestamp()}",
        type=ActionType.ESCALATE,
        priority=Priority.CRITICAL,
        tenant_id=str(current_user.tenant_id),
        asset_id=asset_id,
        description=f"Manual escalation: {reason}",
        details={
            "requested_by": current_user.email,
            "reason": reason,
        },
    )
    
    result = await service.copilot.act(action)
    
    return {
        "status": "escalated",
        "action_id": action.id,
        "result": result,
    }
