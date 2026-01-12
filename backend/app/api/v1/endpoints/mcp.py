"""
MCP (Model Context Protocol) API Endpoint

This endpoint exposes SensorMind's MCP server capabilities via REST API,
allowing AI assistants to interact with the platform.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/mcp", tags=["MCP - Model Context Protocol"])


# =========================================================================
# Schemas
# =========================================================================

class MCPToolSchema(BaseModel):
    """Tool definition for MCP."""
    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPResourceSchema(BaseModel):
    """Resource definition for MCP."""
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"


class MCPCallToolRequest(BaseModel):
    """Request to call an MCP tool."""
    name: str
    arguments: Dict[str, Any] = {}


class MCPReadResourceRequest(BaseModel):
    """Request to read an MCP resource."""
    uri: str


# =========================================================================
# MCP Server Instance (lazy loaded)
# =========================================================================

_mcp_server = None


def get_mcp_server():
    """Get or create MCP server instance."""
    global _mcp_server
    if _mcp_server is None:
        from ml.mcp.server import SensorMindMCPServer
        _mcp_server = SensorMindMCPServer(
            api_url=f"http://localhost:{settings.PORT if hasattr(settings, 'PORT') else 8000}",
        )
    return _mcp_server


# =========================================================================
# MCP Endpoints
# =========================================================================

@router.get("/info", response_model=Dict[str, Any])
async def get_mcp_info():
    """
    Get MCP server information.
    
    Returns information about the SensorMind MCP server including
    its capabilities and version.
    """
    return {
        "name": "SensorMind MCP Server",
        "version": "1.0.0",
        "protocol_version": "2024-11-05",
        "capabilities": {
            "tools": True,
            "resources": True,
            "prompts": False,
            "logging": False
        },
        "description": "AI-Powered Predictive Maintenance Platform MCP Interface"
    }


@router.get("/tools", response_model=List[MCPToolSchema])
async def list_tools():
    """
    List available MCP tools.
    
    Returns all tools that AI assistants can use to interact with
    SensorMind's predictive maintenance capabilities.
    """
    server = get_mcp_server()
    tools = server.list_tools()
    return [
        MCPToolSchema(
            name=t.name,
            description=t.description,
            input_schema=t.input_schema
        )
        for t in tools
    ]


@router.get("/resources", response_model=List[MCPResourceSchema])
async def list_resources():
    """
    List available MCP resources.
    
    Returns all resources that AI assistants can read to get
    information about assets, alerts, and platform status.
    """
    server = get_mcp_server()
    resources = server.list_resources()
    return [
        MCPResourceSchema(
            uri=r.uri,
            name=r.name,
            description=r.description,
            mime_type=r.mime_type
        )
        for r in resources
    ]


@router.post("/tools/call", response_model=Dict[str, Any])
async def call_tool(request: MCPCallToolRequest):
    """
    Execute an MCP tool.
    
    Allows AI assistants to call any available tool with the
    provided arguments.
    
    Example:
    ```json
    {
        "name": "get_asset_health",
        "arguments": {"asset_id": "pump-001"}
    }
    ```
    """
    server = get_mcp_server()
    
    # Validate tool exists
    tool_names = [t.name for t in server.list_tools()]
    if request.name not in tool_names:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{request.name}' not found. Available: {tool_names}"
        )
    
    result = await server.call_tool(request.name, request.arguments)
    return result


@router.post("/resources/read", response_model=Dict[str, Any])
async def read_resource(request: MCPReadResourceRequest):
    """
    Read an MCP resource.
    
    Returns the content of a resource identified by its URI.
    
    Example:
    ```json
    {
        "uri": "sensormind://assets"
    }
    ```
    """
    server = get_mcp_server()
    
    # Validate resource exists
    resource_uris = [r.uri for r in server.list_resources()]
    if request.uri not in resource_uris:
        raise HTTPException(
            status_code=404,
            detail=f"Resource '{request.uri}' not found. Available: {resource_uris}"
        )
    
    result = await server.read_resource(request.uri)
    return result


@router.get("/health")
async def mcp_health():
    """Health check for MCP server."""
    return {
        "status": "healthy",
        "mcp_version": "2024-11-05",
        "server": "SensorMind"
    }
