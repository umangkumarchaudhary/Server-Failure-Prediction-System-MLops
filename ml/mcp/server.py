"""
SensorMind MCP (Model Context Protocol) Server

This module implements an MCP server that allows AI assistants like Claude
to interact with SensorMind's predictive maintenance capabilities.

MCP enables AI to:
- Query asset health and predictions
- Get anomaly detection results
- Chat with the AI Copilot
- Create alerts and incidents
"""

import json
import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import httpx


@dataclass
class MCPTool:
    """Definition of an MCP tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    

@dataclass
class MCPResource:
    """Definition of an MCP resource."""
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"


class SensorMindMCPServer:
    """
    MCP Server for SensorMind Predictive Maintenance Platform.
    
    This server exposes SensorMind's capabilities to AI assistants,
    allowing them to query assets, predictions, and interact with
    the AI Copilot.
    
    Usage:
        server = SensorMindMCPServer(
            api_url="https://your-api.onrender.com",
            api_key="your-api-key"
        )
        
        # List available tools
        tools = server.list_tools()
        
        # Call a tool
        result = await server.call_tool("get_asset_health", {"asset_id": "pump-001"})
    """
    
    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        jwt_token: Optional[str] = None,
    ):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.jwt_token = jwt_token
        self._client = httpx.AsyncClient(timeout=30.0)
        
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
        
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        headers = {"Content-Type": "application/json"}
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers
    
    # =========================================================================
    # MCP Protocol Methods
    # =========================================================================
    
    def list_tools(self) -> List[MCPTool]:
        """
        List all available MCP tools.
        
        Returns:
            List of tool definitions with names, descriptions, and input schemas.
        """
        return [
            MCPTool(
                name="get_all_assets",
                description="Get a list of all monitored assets with their current health status",
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of assets to return",
                            "default": 50
                        },
                        "risk_level": {
                            "type": "string",
                            "enum": ["normal", "warning", "critical"],
                            "description": "Filter by risk level"
                        }
                    }
                }
            ),
            MCPTool(
                name="get_asset_health",
                description="Get detailed health information for a specific asset including anomaly score, RUL, and risk level",
                input_schema={
                    "type": "object",
                    "properties": {
                        "asset_id": {
                            "type": "string",
                            "description": "The unique identifier of the asset"
                        }
                    },
                    "required": ["asset_id"]
                }
            ),
            MCPTool(
                name="get_predictions",
                description="Get ML predictions (anomaly scores, RUL estimates) for an asset",
                input_schema={
                    "type": "object",
                    "properties": {
                        "asset_id": {
                            "type": "string",
                            "description": "The asset to get predictions for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of recent predictions to return",
                            "default": 10
                        }
                    },
                    "required": ["asset_id"]
                }
            ),
            MCPTool(
                name="get_prediction_explanation",
                description="Get SHAP-based explanation for why a prediction was made (XAI)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "prediction_id": {
                            "type": "string",
                            "description": "The prediction to explain"
                        }
                    },
                    "required": ["prediction_id"]
                }
            ),
            MCPTool(
                name="get_alerts",
                description="Get active alerts across all assets or for a specific asset",
                input_schema={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["active", "acknowledged", "resolved"],
                            "description": "Filter by alert status"
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["info", "warning", "critical"],
                            "description": "Filter by severity"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 20
                        }
                    }
                }
            ),
            MCPTool(
                name="get_dashboard_stats",
                description="Get overall platform statistics including total assets, health distribution, and alert counts",
                input_schema={
                    "type": "object",
                    "properties": {}
                }
            ),
            MCPTool(
                name="chat_with_copilot",
                description="Chat with the AI Maintenance Copilot to get insights, suggestions, or ask questions about assets",
                input_schema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Your question or request to the AI Copilot"
                        },
                        "asset_id": {
                            "type": "string",
                            "description": "Optional: Context asset for the conversation"
                        }
                    },
                    "required": ["message"]
                }
            ),
            MCPTool(
                name="get_copilot_suggestions",
                description="Get AI-generated maintenance suggestions for an asset",
                input_schema={
                    "type": "object",
                    "properties": {
                        "asset_id": {
                            "type": "string",
                            "description": "The asset to get suggestions for"
                        }
                    },
                    "required": ["asset_id"]
                }
            ),
            MCPTool(
                name="check_drift",
                description="Check if there's data or concept drift for an asset's ML model",
                input_schema={
                    "type": "object",
                    "properties": {
                        "asset_id": {
                            "type": "string",
                            "description": "The asset to check for drift"
                        }
                    },
                    "required": ["asset_id"]
                }
            ),
            MCPTool(
                name="create_alert",
                description="Create a new alert for an asset",
                input_schema={
                    "type": "object",
                    "properties": {
                        "asset_id": {
                            "type": "string",
                            "description": "The asset to create alert for"
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["info", "warning", "critical"],
                            "description": "Alert severity level"
                        },
                        "message": {
                            "type": "string",
                            "description": "Alert message describing the issue"
                        }
                    },
                    "required": ["asset_id", "severity", "message"]
                }
            ),
        ]
    
    def list_resources(self) -> List[MCPResource]:
        """
        List available MCP resources.
        
        Returns:
            List of resource definitions.
        """
        return [
            MCPResource(
                uri="sensormind://assets",
                name="All Assets",
                description="List of all monitored assets with health status"
            ),
            MCPResource(
                uri="sensormind://alerts/active",
                name="Active Alerts",
                description="Currently active alerts requiring attention"
            ),
            MCPResource(
                uri="sensormind://dashboard",
                name="Dashboard Stats",
                description="Platform overview statistics"
            ),
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an MCP tool.
        
        Args:
            name: Tool name to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        tool_handlers = {
            "get_all_assets": self._get_all_assets,
            "get_asset_health": self._get_asset_health,
            "get_predictions": self._get_predictions,
            "get_prediction_explanation": self._get_prediction_explanation,
            "get_alerts": self._get_alerts,
            "get_dashboard_stats": self._get_dashboard_stats,
            "chat_with_copilot": self._chat_with_copilot,
            "get_copilot_suggestions": self._get_copilot_suggestions,
            "check_drift": self._check_drift,
            "create_alert": self._create_alert,
        }
        
        handler = tool_handlers.get(name)
        if not handler:
            return {"error": f"Unknown tool: {name}"}
        
        try:
            return await handler(**arguments)
        except Exception as e:
            return {"error": str(e)}
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Read an MCP resource.
        
        Args:
            uri: Resource URI to read
            
        Returns:
            Resource content
        """
        if uri == "sensormind://assets":
            return await self._get_all_assets()
        elif uri == "sensormind://alerts/active":
            return await self._get_alerts(status="active")
        elif uri == "sensormind://dashboard":
            return await self._get_dashboard_stats()
        else:
            return {"error": f"Unknown resource: {uri}"}
    
    # =========================================================================
    # Tool Implementations
    # =========================================================================
    
    async def _get_all_assets(
        self,
        limit: int = 50,
        risk_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all assets."""
        params = {"limit": limit}
        if risk_level:
            params["risk_level"] = risk_level
            
        response = await self._client.get(
            f"{self.api_url}/api/v1/assets",
            headers=self._get_headers(),
            params=params
        )
        
        if response.status_code == 200:
            assets = response.json()
            return {
                "success": True,
                "count": len(assets),
                "assets": assets
            }
        return {"error": f"API error: {response.status_code}"}
    
    async def _get_asset_health(self, asset_id: str) -> Dict[str, Any]:
        """Get detailed health for an asset."""
        response = await self._client.get(
            f"{self.api_url}/api/v1/assets/{asset_id}",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            asset = response.json()
            return {
                "success": True,
                "asset_id": asset_id,
                "name": asset.get("name"),
                "type": asset.get("type"),
                "health_score": asset.get("health_score"),
                "risk_level": asset.get("risk_level"),
                "location": asset.get("location"),
                "status": "healthy" if asset.get("health_score", 0) > 70 else "needs_attention"
            }
        return {"error": f"Asset not found: {asset_id}"}
    
    async def _get_predictions(
        self,
        asset_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get predictions for an asset."""
        response = await self._client.get(
            f"{self.api_url}/api/v1/predictions/asset/{asset_id}",
            headers=self._get_headers(),
            params={"limit": limit}
        )
        
        if response.status_code == 200:
            predictions = response.json()
            return {
                "success": True,
                "asset_id": asset_id,
                "prediction_count": len(predictions),
                "predictions": predictions
            }
        return {"error": f"Failed to get predictions: {response.status_code}"}
    
    async def _get_prediction_explanation(self, prediction_id: str) -> Dict[str, Any]:
        """Get XAI explanation for a prediction."""
        response = await self._client.get(
            f"{self.api_url}/api/v1/predictions/{prediction_id}/explain",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "prediction_id": prediction_id,
                "explanation": response.json()
            }
        return {"error": f"Explanation not found: {prediction_id}"}
    
    async def _get_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get alerts."""
        params = {"limit": limit}
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
            
        response = await self._client.get(
            f"{self.api_url}/api/v1/alerts",
            headers=self._get_headers(),
            params=params
        )
        
        if response.status_code == 200:
            alerts = response.json()
            return {
                "success": True,
                "count": len(alerts),
                "alerts": alerts
            }
        return {"error": f"Failed to get alerts: {response.status_code}"}
    
    async def _get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        response = await self._client.get(
            f"{self.api_url}/api/v1/dashboard/stats",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "stats": response.json()
            }
        return {"error": f"Failed to get stats: {response.status_code}"}
    
    async def _chat_with_copilot(
        self,
        message: str,
        asset_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Chat with AI Copilot."""
        payload = {"message": message}
        if asset_id:
            payload["asset_id"] = asset_id
            
        response = await self._client.post(
            f"{self.api_url}/api/v1/copilot/chat",
            headers=self._get_headers(),
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result.get("response"),
                "suggestions": result.get("suggestions", [])
            }
        return {"error": f"Copilot error: {response.status_code}"}
    
    async def _get_copilot_suggestions(self, asset_id: str) -> Dict[str, Any]:
        """Get maintenance suggestions."""
        response = await self._client.get(
            f"{self.api_url}/api/v1/copilot/suggestions/{asset_id}",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "asset_id": asset_id,
                "suggestions": response.json()
            }
        return {"error": f"Failed to get suggestions: {response.status_code}"}
    
    async def _check_drift(self, asset_id: str) -> Dict[str, Any]:
        """Check for model drift."""
        response = await self._client.get(
            f"{self.api_url}/api/v1/ml/drift/{asset_id}",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "asset_id": asset_id,
                "drift_info": response.json()
            }
        return {"error": f"Failed to check drift: {response.status_code}"}
    
    async def _create_alert(
        self,
        asset_id: str,
        severity: str,
        message: str
    ) -> Dict[str, Any]:
        """Create a new alert."""
        # Note: This would need a proper endpoint in the backend
        return {
            "success": True,
            "message": f"Alert created for asset {asset_id}",
            "severity": severity,
            "alert_message": message,
            "note": "Alert creation endpoint needed in backend"
        }


# =========================================================================
# MCP Server Runner (for standalone mode)
# =========================================================================

async def run_mcp_server():
    """
    Run the MCP server in standalone mode.
    
    This can be used for testing or as a reference implementation.
    """
    import sys
    
    server = SensorMindMCPServer(
        api_url="https://server-failure-prediction-system-mlops.onrender.com"
    )
    
    print("🧠 SensorMind MCP Server")
    print("=" * 50)
    print("\nAvailable Tools:")
    for tool in server.list_tools():
        print(f"  • {tool.name}: {tool.description[:60]}...")
    
    print("\nAvailable Resources:")
    for resource in server.list_resources():
        print(f"  • {resource.uri}: {resource.description}")
    
    print("\n" + "=" * 50)
    print("Server ready for MCP connections\n")
    
    # Interactive mode
    while True:
        try:
            cmd = input("\nEnter tool name (or 'quit'): ").strip()
            if cmd.lower() == 'quit':
                break
            if cmd.lower() == 'list':
                for tool in server.list_tools():
                    print(f"  {tool.name}")
                continue
                
            args_str = input("Enter arguments (JSON): ").strip() or "{}"
            args = json.loads(args_str)
            
            result = await server.call_tool(cmd, args)
            print(json.dumps(result, indent=2))
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    await server.close()
    print("\nServer stopped.")


if __name__ == "__main__":
    asyncio.run(run_mcp_server())
