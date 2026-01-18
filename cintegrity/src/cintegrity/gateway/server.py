"""cintegrity MCP Gateway - follows official SDK patterns."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from types import ModuleType
from typing import Any

from fastmcp import Context, FastMCP
from pydantic import Field

from .config import parse_mcp_config
from .connector import MCPConnector
from .errors import ToolExecutionError, WorkflowError
from .manager import ToolManager
from .prompts import WORKFLOW_DESCRIPTION
from .tools.execute_tool import execute_tool as _execute_tool
from .tools.execute_workflow import execute_workflow as _execute_workflow
from .tools.search_tools import search_tools as _search_tools


@dataclass
class GatewayContext:
    """Lifespan context holding initialized resources."""

    manager: ToolManager
    connector: MCPConnector


def create_gateway(
    function_calls: Sequence[Callable[[Any], Any]] | None = None,
    mcp_config: dict[str, Any] | None = None,
    local_servers: dict[str, ModuleType | Sequence[Callable[..., Any]]] | None = None,
) -> FastMCP[GatewayContext]:
    """Create a cintegrity MCP gateway server.

    Follows the official MCP SDK pattern: create FastMCP with lifespan,
    define tools at creation time, call run() to start.

    Args:
        function_calls: Python functions to register as function call tools
        mcp_config: MCP server config dict to connect to external servers
        local_servers: Dict mapping server names to modules or lists of async functions.
            Input/output schemas are inferred from type annotations.
            Tools are added with mcp_ prefix and searchable via search_tools.
            Example: {"versa": versa_tools} or {"versa": [get_status, ...]}

    Returns:
        Configured FastMCP server ready to run
    """
    _function_calls = function_calls or []
    _mcp_config = mcp_config
    _local_servers = local_servers or {}

    @asynccontextmanager
    async def gateway_lifespan(_server: FastMCP) -> AsyncIterator[GatewayContext]:
        """Initialize manager and connect to external MCP servers."""
        import logging

        logger = logging.getLogger("cintegrity.gateway")

        manager = ToolManager()
        for fn in _function_calls:
            manager.add_function_call(fn)

        # Add local servers (embedded tools that don't need network)
        for server_name, tools in _local_servers.items():
            specs = manager.add_local_server(server_name, tools)
            logger.info(f"Added local server '{server_name}' with {len(specs)} tools")

        connector = MCPConnector(manager)

        if _mcp_config:
            configs = parse_mcp_config(_mcp_config)
            for config in configs:
                try:
                    logger.info(f"Connecting to MCP server: {config.name} ({config.url})")
                    await connector.connect(config)
                    logger.info(f"Connected to {config.name}, loaded {len(manager)} tools")
                except Exception as e:
                    logger.error(f"Failed to connect to {config.name}: {e}")
                    # Continue without this server rather than failing entirely

        logger.info(f"Gateway initialized with {len(manager)} tools")

        try:
            yield GatewayContext(manager=manager, connector=connector)
        finally:
            await connector.close()

    mcp: FastMCP[GatewayContext] = FastMCP(
        "cintegrity-gateway",
        lifespan=gateway_lifespan,
    )

    # --- Tools ---

    def _get_gateway_context(ctx: Context) -> GatewayContext:
        """Extract GatewayContext from request context."""
        if ctx.request_context is None:
            raise RuntimeError("Request context not available")
        return ctx.request_context.lifespan_context  # type: ignore[return-value]

    @mcp.tool()
    async def search_tools(
        ctx: Context,
        query: str = Field(
            description=(
                "Search query - natural language or keywords.\n"
                "Examples: 'appliance status', 'search network', 'get user'"
            )
        ),
    ) -> dict[str, Any]:
        """Search for tools by name, description, or argument names.

        ALWAYS call this before execute_workflow to find relevant tools and get their schemas.

        Returns matching tools WITH their full schemas:
        - name: Tool name (use in imports)
        - description: What the tool does
        - inputSchema: JSON Schema with required fields and argument types
        - import_path: Python import statement for execute_workflow
        """
        gateway_ctx = _get_gateway_context(ctx)
        return await _search_tools(gateway_ctx.manager, query=query)

    @mcp.tool(description=WORKFLOW_DESCRIPTION)
    async def execute_workflow(
        ctx: Context,
        planner_code: str = Field(description="Restricted Python code defining `def workflow():` with imports inside."),
    ) -> Any:
        """Execute a multi-step workflow written in restricted Python."""
        gateway_ctx = _get_gateway_context(ctx)
        try:
            return await _execute_workflow(
                gateway_ctx.manager,
                planner_code=planner_code,
                ctx=ctx,
            )
        except WorkflowError as exc:
            raise RuntimeError(f"{exc.stage} error: {exc}") from exc

    @mcp.tool()
    async def execute_tool(
        ctx: Context,
        tool_name: str = Field(
            description=(
                "The tool's import name from list_tools() output.\n"
                "Examples: 'mcp_search_appliance', 'send_email'\n"
                "NOT the path - just the tool name itself."
            )
        ),
        args: dict[str, Any] = Field(
            description=(
                "Keyword arguments matching the tool's inputSchema.\nCall read_tool() first to see required fields."
            )
        ),
    ) -> Any:
        """Execute a single tool directly (prefer execute_workflow for multi-step operations)."""
        gateway_ctx = _get_gateway_context(ctx)
        try:
            return await _execute_tool(gateway_ctx.manager, tool_name=tool_name, args=args)
        except ToolExecutionError as exc:
            raise RuntimeError(str(exc)) from exc

    # MCP Prompt for workflow dialect documentation
    @mcp.prompt()
    def workflow_dialect() -> str:
        """Get the restricted Python dialect rules for execute_workflow.

        Use this prompt to understand the workflow code format before writing workflows.
        """
        return WORKFLOW_DESCRIPTION

    # MCP Resource for workflow dialect documentation
    @mcp.resource("cintegrity://docs/workflow-dialect")
    def workflow_dialect_resource() -> str:
        """Restricted Python dialect documentation for execute_workflow."""
        return WORKFLOW_DESCRIPTION

    return mcp
