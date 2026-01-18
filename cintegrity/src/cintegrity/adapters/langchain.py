from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from ..gateway.errors import WorkflowError
from ..gateway.manager import ToolManager
from ..gateway.search.all import AllToolsSearchStrategy
from .prompt import SYSTEM_PROMPT
from .shared import create_agent_tools


def build_langchain_tools(
    *,
    function_calls: Sequence[Callable[[Any], Any]] | None = None,
    mcp_config: dict[str, Any] | None = None,
) -> tuple[list[Any], str, Callable[..., Any]]:
    """Build LangChain tools with cintegrity integration.

    Note: For MCP server integration, use the MCP Gateway server instead
    (create_gateway). Sync adapters support local function_calls only.

    Args:
        function_calls: Python functions to register as local tools
        mcp_config: Deprecated - raises NotImplementedError. Use MCP Gateway.

    Returns:
        Tuple of (langchain_tools, system_prompt, add_function_call_fn)

    Example:
        tools, system_prompt, _ = build_langchain_tools(
            function_calls=[my_tool],
        )
        agent = create_agent(tools=tools, system_prompt=system_prompt)
    """
    try:
        from langchain_core.tools import (  # pyrefly: ignore[missing-import]
            ToolException as LangChainToolException,
        )
        from langchain_core.tools import (  # pyrefly: ignore[missing-import]
            tool as langchain_tool,
        )
        from pydantic import BaseModel
    except ImportError as exc:
        raise ImportError(
            "cintegrity agent framework integration requires langchain-core. Install with: pip install langchain-core"
        ) from exc

    # MCP connections not supported in sync adapters due to anyio context manager
    # limitations. Use the MCP Gateway server instead for MCP integration.
    if mcp_config:
        raise NotImplementedError(
            "MCP connections are not supported in sync adapters due to anyio "
            "context manager limitations. Use one of these alternatives:\n"
            "1. Use the MCP Gateway server: create_gateway(mcp_config=...)\n"
            "2. Use function_calls for local Python functions\n"
            "3. Connect to external MCP servers through the Gateway"
        )

    # Initialize ToolManager with AllTools search strategy (returns all tools)
    search_strategy = AllToolsSearchStrategy()
    manager = ToolManager(search_strategy=search_strategy)

    # Register local function call tools
    for fn in function_calls or []:
        manager.add_function_call(fn)

    # Exception converters for LangChain
    def convert_workflow_error(exc: Exception) -> Exception:
        if isinstance(exc, WorkflowError):
            return LangChainToolException(f"{exc.stage} error: {exc}")
        return LangChainToolException(f"{type(exc).__name__}: {exc}")

    def convert_tool_error(exc: Exception) -> Exception:
        return LangChainToolException(str(exc))

    # Create base tool functions with exception conversion (MCP-aligned 3 tools)
    (
        base_search,
        base_workflow,
        base_execute,
    ) = create_agent_tools(
        manager,
        workflow_error_converter=convert_workflow_error,
        tool_error_converter=convert_tool_error,
    )

    # Apply LangChain decorators to standard tools
    search_tools = langchain_tool(base_search)
    execute_workflow = langchain_tool(base_workflow)

    class ExecuteToolArgs(BaseModel):
        tool_name: str
        args: dict[str, Any]

    execute_tool = langchain_tool(args_schema=ExecuteToolArgs)(base_execute)

    langchain_tools = [search_tools, execute_workflow, execute_tool]

    return (
        langchain_tools,
        SYSTEM_PROMPT,
        manager.add_function_call,
    )
