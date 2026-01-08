"""
Ticket Providers - Integration with ticketing systems.

Supports:
- Jira
- ServiceNow
- Generic webhook
"""
import os
from datetime import datetime
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class TicketProvider(ABC):
    """Abstract base for ticket providers."""
    
    @abstractmethod
    async def create_ticket(
        self,
        system: str,
        title: str,
        description: str,
        priority: str,
        project: str,
        issue_type: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a ticket."""
        pass
    
    @abstractmethod
    async def update_ticket(
        self,
        ticket_id: str,
        **updates,
    ) -> Dict[str, Any]:
        """Update a ticket."""
        pass
    
    @abstractmethod
    async def get_ticket(
        self,
        ticket_id: str,
    ) -> Dict[str, Any]:
        """Get ticket details."""
        pass


class JiraProvider(TicketProvider):
    """Jira Cloud integration."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
    ):
        if not HAS_HTTPX:
            raise ImportError("httpx package not installed")
        
        self.base_url = base_url or os.getenv("JIRA_BASE_URL", "https://your-domain.atlassian.net")
        self.email = email or os.getenv("JIRA_EMAIL")
        self.api_token = api_token or os.getenv("JIRA_API_TOKEN")
        
        self.client = httpx.AsyncClient(
            base_url=f"{self.base_url}/rest/api/3",
            auth=(self.email, self.api_token) if self.email and self.api_token else None,
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )
    
    async def create_ticket(
        self,
        system: str,
        title: str,
        description: str,
        priority: str,
        project: str,
        issue_type: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create Jira issue."""
        # Map priority
        priority_map = {
            "low": "Low",
            "medium": "Medium",
            "high": "High",
            "critical": "Highest",
        }
        
        payload = {
            "fields": {
                "project": {"key": project},
                "summary": title,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}]
                        }
                    ]
                },
                "issuetype": {"name": issue_type},
                "priority": {"name": priority_map.get(priority, "Medium")},
            }
        }
        
        # Add custom fields if provided
        if "custom_fields" in kwargs:
            payload["fields"].update(kwargs["custom_fields"])
        
        try:
            response = await self.client.post("/issue", json=payload)
            response.raise_for_status()
            data = response.json()
            
            return {
                "status": "success",
                "ticket_id": data["key"],
                "url": f"{self.base_url}/browse/{data['key']}",
                "system": "jira",
            }
        except Exception as e:
            logger.error(f"Failed to create Jira ticket: {e}")
            return {"status": "error", "error": str(e)}
    
    async def update_ticket(
        self,
        ticket_id: str,
        **updates,
    ) -> Dict[str, Any]:
        """Update Jira issue."""
        payload = {"fields": updates}
        
        try:
            response = await self.client.put(f"/issue/{ticket_id}", json=payload)
            response.raise_for_status()
            return {"status": "success", "ticket_id": ticket_id}
        except Exception as e:
            logger.error(f"Failed to update Jira ticket: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_ticket(
        self,
        ticket_id: str,
    ) -> Dict[str, Any]:
        """Get Jira issue."""
        try:
            response = await self.client.get(f"/issue/{ticket_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get Jira ticket: {e}")
            return {"status": "error", "error": str(e)}


class ServiceNowProvider(TicketProvider):
    """ServiceNow integration."""
    
    def __init__(
        self,
        instance: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        if not HAS_HTTPX:
            raise ImportError("httpx package not installed")
        
        self.instance = instance or os.getenv("SERVICENOW_INSTANCE")
        self.username = username or os.getenv("SERVICENOW_USERNAME")
        self.password = password or os.getenv("SERVICENOW_PASSWORD")
        
        self.client = httpx.AsyncClient(
            base_url=f"https://{self.instance}.service-now.com/api/now",
            auth=(self.username, self.password) if self.username and self.password else None,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30.0,
        )
    
    async def create_ticket(
        self,
        system: str,
        title: str,
        description: str,
        priority: str,
        project: str,
        issue_type: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create ServiceNow incident."""
        # Map priority (ServiceNow uses 1-5, 1 being highest)
        priority_map = {
            "critical": "1",
            "high": "2",
            "medium": "3",
            "low": "4",
        }
        
        # Map issue type to table
        table = "incident" if issue_type.lower() == "incident" else "sc_request"
        
        payload = {
            "short_description": title,
            "description": description,
            "priority": priority_map.get(priority, "3"),
            "category": project,
        }
        
        if "assignment_group" in kwargs:
            payload["assignment_group"] = kwargs["assignment_group"]
        
        try:
            response = await self.client.post(f"/table/{table}", json=payload)
            response.raise_for_status()
            data = response.json()
            
            ticket_number = data["result"]["number"]
            return {
                "status": "success",
                "ticket_id": ticket_number,
                "sys_id": data["result"]["sys_id"],
                "url": f"https://{self.instance}.service-now.com/{table}.do?sysparm_query=number={ticket_number}",
                "system": "servicenow",
            }
        except Exception as e:
            logger.error(f"Failed to create ServiceNow ticket: {e}")
            return {"status": "error", "error": str(e)}
    
    async def update_ticket(
        self,
        ticket_id: str,
        **updates,
    ) -> Dict[str, Any]:
        """Update ServiceNow incident."""
        try:
            response = await self.client.patch(
                f"/table/incident/{ticket_id}",
                json=updates
            )
            response.raise_for_status()
            return {"status": "success", "ticket_id": ticket_id}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_ticket(
        self,
        ticket_id: str,
    ) -> Dict[str, Any]:
        """Get ServiceNow incident."""
        try:
            response = await self.client.get(f"/table/incident/{ticket_id}")
            response.raise_for_status()
            return response.json()["result"]
        except Exception as e:
            return {"status": "error", "error": str(e)}


class WebhookProvider(TicketProvider):
    """Generic webhook provider for custom integrations."""
    
    def __init__(
        self,
        webhook_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        if not HAS_HTTPX:
            raise ImportError("httpx package not installed")
        
        self.webhook_url = webhook_url or os.getenv("TICKET_WEBHOOK_URL")
        self.headers = headers or {}
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def create_ticket(
        self,
        system: str,
        title: str,
        description: str,
        priority: str,
        project: str,
        issue_type: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Send ticket creation webhook."""
        payload = {
            "action": "create",
            "timestamp": datetime.utcnow().isoformat(),
            "ticket": {
                "title": title,
                "description": description,
                "priority": priority,
                "project": project,
                "type": issue_type,
                **kwargs,
            },
        }
        
        try:
            response = await self.client.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
            
            data = response.json() if response.content else {}
            return {
                "status": "success",
                "ticket_id": data.get("id", f"WH-{datetime.utcnow().timestamp()}"),
                "system": "webhook",
            }
        except Exception as e:
            logger.error(f"Webhook failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def update_ticket(
        self,
        ticket_id: str,
        **updates,
    ) -> Dict[str, Any]:
        """Send ticket update webhook."""
        payload = {
            "action": "update",
            "ticket_id": ticket_id,
            "updates": updates,
        }
        
        try:
            response = await self.client.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
            )
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_ticket(
        self,
        ticket_id: str,
    ) -> Dict[str, Any]:
        """Not supported for webhooks."""
        return {"status": "error", "error": "Get not supported for webhooks"}


class MockTicketProvider(TicketProvider):
    """Mock provider for testing."""
    
    def __init__(self):
        self.tickets: Dict[str, Dict] = {}
        self.counter = 0
    
    async def create_ticket(
        self,
        system: str,
        title: str,
        description: str,
        priority: str,
        project: str,
        issue_type: str,
        **kwargs,
    ) -> Dict[str, Any]:
        self.counter += 1
        ticket_id = f"MOCK-{self.counter}"
        
        self.tickets[ticket_id] = {
            "id": ticket_id,
            "title": title,
            "description": description,
            "priority": priority,
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        logger.info(f"Mock ticket created: {ticket_id}")
        
        return {
            "status": "success",
            "ticket_id": ticket_id,
            "url": f"https://mock.tickets.local/{ticket_id}",
            "system": "mock",
        }
    
    async def update_ticket(
        self,
        ticket_id: str,
        **updates,
    ) -> Dict[str, Any]:
        if ticket_id in self.tickets:
            self.tickets[ticket_id].update(updates)
            return {"status": "success"}
        return {"status": "error", "error": "Ticket not found"}
    
    async def get_ticket(
        self,
        ticket_id: str,
    ) -> Dict[str, Any]:
        return self.tickets.get(ticket_id, {"status": "error", "error": "Not found"})


def create_ticket_provider(
    provider_type: str = "mock",
    **kwargs,
) -> TicketProvider:
    """Factory to create ticket provider."""
    if provider_type == "jira":
        return JiraProvider(**kwargs)
    elif provider_type == "servicenow":
        return ServiceNowProvider(**kwargs)
    elif provider_type == "webhook":
        return WebhookProvider(**kwargs)
    else:
        return MockTicketProvider()
