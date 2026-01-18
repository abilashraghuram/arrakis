from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

import anyio
from fastmcp import Client
from fastmcp.client.transports import (
    SSETransport,
    StdioTransport,
    StreamableHttpTransport,
)

from .config import MCPServerConfig
from .manager import MCPToolDefinition, ToolSpec

SHUTDOWN_TIMEOUT_SECONDS = 2.0

if TYPE_CHECKING:
    from .manager import ToolManager


class MCPConnector:
    """Handles MCP server connection lifecycle."""

    def __init__(self, manager: ToolManager) -> None:
        self._manager = manager
        self._exit_stack = contextlib.AsyncExitStack()
        self._connected: set[str] = set()

    async def connect(self, config: MCPServerConfig) -> list[ToolSpec]:
        """Connect to an MCP server and add its tools to the manager."""
        if config.name in self._connected:
            raise RuntimeError(f"Already connected: {config.name}")

        if config.transport == "stdio":
            if config.command is None:
                raise ValueError(f"MCP server '{config.name}': stdio transport requires 'command'")
            transport = StdioTransport(
                command=config.command,
                args=config.args or [],
                env=config.env or None,
                cwd=config.cwd,
            )
        elif config.transport == "sse":
            if config.url is None:
                raise ValueError(f"MCP server '{config.name}': sse transport requires 'url'")
            transport = SSETransport(
                url=config.url,
                headers=config.headers or {},
            )
        elif config.transport in ("http", "streamable-http"):
            if config.url is None:
                raise ValueError(f"MCP server '{config.name}': {config.transport} transport requires 'url'")
            transport = StreamableHttpTransport(
                url=config.url,
                headers=config.headers or {},
            )
        else:
            raise ValueError(f"Unsupported transport: {config.transport}")

        client = Client(transport)
        client = await self._exit_stack.enter_async_context(client)
        self._connected.add(config.name)

        tools_result = await client.list_tools()
        tool_definitions = [
            MCPToolDefinition(
                name=t.name,
                description=t.description or "",
                input_schema=t.inputSchema,
                output_schema=t.outputSchema,
            )
            for t in tools_result
        ]

        return self._manager.add_mcp_server(config.name, client, tool_definitions)

    async def disconnect(self, server_name: str) -> list[str]:
        """Disconnect from an MCP server and remove its tools."""
        if server_name not in self._connected:
            raise RuntimeError(f"Not connected: {server_name}")

        removed = self._manager.remove_mcp_server(server_name)
        self._connected.discard(server_name)
        return removed

    def is_connected(self, server_name: str) -> bool:
        return server_name in self._connected

    async def close(self) -> None:
        """Close all connections with timeout to avoid blocking on stuck SSE streams."""
        with anyio.move_on_after(SHUTDOWN_TIMEOUT_SECONDS):
            await self._exit_stack.aclose()
        self._connected.clear()

    async def __aenter__(self) -> MCPConnector:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
