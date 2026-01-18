"""Gateway bridge adapter for connecting ToolManager to pybox engine."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..gateway.manager import ToolManager


class MCPToolBridge:
    """Bridge that adapts ToolManager to pybox's ToolBridge protocol.

    Connects the gateway's tool management layer to the core provenance engine.
    Despite the name, works with any ToolManager regardless of backend
    (MCP servers, local functions, hybrid).
    """

    def __init__(self, tool_manager: ToolManager) -> None:
        """Initialize with a ToolManager instance.

        Args:
            tool_manager: Gateway ToolManager instance with registered tools
        """
        self._manager = tool_manager

    def list_tools(self) -> list[str]:
        """List available tool names from the ToolManager."""
        return [spec.name for spec in self._manager.specs()]

    async def call(self, tool_name: str, **kwargs: Any) -> Any:
        """Execute a tool via the ToolManager."""
        return await self._manager.call(tool_name, kwargs)
