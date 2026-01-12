"""
SensorMind MCP Module

This module provides Model Context Protocol (MCP) integration,
allowing AI assistants to interact with SensorMind's predictive
maintenance capabilities.
"""

from ml.mcp.server import (
    SensorMindMCPServer,
    MCPTool,
    MCPResource,
)

__all__ = [
    "SensorMindMCPServer",
    "MCPTool",
    "MCPResource",
]
