"""MCP gateway server creation.

Provides a simple interface for creating an MCP gateway server with cintegrity tools.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any


def build_mcp_gateway(
    function_calls: Sequence[Callable[[Any], Any]] | None = None,
    mcp_config: dict[str, Any] | None = None,
) -> Any:
    """Create an MCP gateway server.

    Returns a FastMCP server configured with cintegrity tools.
    Call mcp.run(transport="stdio"|"sse"|"streamable-http") to start.

    Args:
        function_calls: Sequence of Python functions to register as function call tools
        mcp_config: MCP server configuration dictionary

    Returns:
        FastMCP server instance
    """
    from ..gateway.server import create_gateway

    return create_gateway(
        function_calls=function_calls,
        mcp_config=mcp_config,
    )
