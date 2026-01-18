"""Core factory for creating agent framework tool wrappers.

This module provides shared logic for creating tool wrappers across different
agent frameworks (LangChain, Google ADK, raw tools, etc.).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ..gateway.errors import ToolExecutionError, WorkflowError
from ..gateway.prompts import WORKFLOW_DESCRIPTION
from ..gateway.tools.execute_tool import execute_tool as _execute_tool
from ..gateway.tools.execute_workflow import execute_workflow as _execute_workflow
from ..gateway.tools.search_tools import search_tools as _search_tools

if TYPE_CHECKING:
    from ..gateway.manager import ToolManager


def create_agent_tools(
    manager: ToolManager,
    *,
    workflow_error_converter: Callable[[Exception], Exception] | None = None,
    tool_error_converter: Callable[[Exception], Exception] | None = None,
) -> tuple[
    Callable[[str], dict[str, Any]],
    Callable[[str], Any],
    Callable[[str, dict[str, Any]], Any],
]:
    """Factory for creating agent framework tool wrappers.

    Creates 3 tool functions (MCP-aligned):

    1. search_tools(query) - Search for tools by name/description
    2. execute_workflow(planner_code) - Execute multi-step workflow
    3. execute_tool(tool_name, args) - Execute single tool

    Args:
        manager: ToolManager instance with registered tools
        workflow_error_converter: Optional function to convert workflow exceptions
        tool_error_converter: Optional function to convert tool exceptions

    Returns:
        Tuple of (search_tools, execute_workflow, execute_tool)
    """

    def search_tools(query: str) -> dict[str, Any]:
        """Search for tools by name, description, or argument names."""
        return asyncio.run(_search_tools(manager, query=query))

    def execute_workflow(planner_code: str) -> Any:
        try:
            return asyncio.run(
                _execute_workflow(
                    manager,
                    planner_code=planner_code,
                )
            )
        except WorkflowError as exc:
            if workflow_error_converter:
                raise workflow_error_converter(exc) from exc
            raise
        except Exception as exc:
            if workflow_error_converter:
                raise workflow_error_converter(exc) from exc
            raise

    execute_workflow.__doc__ = WORKFLOW_DESCRIPTION

    def execute_tool(tool_name: str, args: dict[str, Any]) -> Any:
        """Execute a single tool by name with JSON args."""
        try:
            return asyncio.run(_execute_tool(manager, tool_name=tool_name, args=args))
        except ToolExecutionError as exc:
            if tool_error_converter:
                raise tool_error_converter(exc) from exc
            raise
        except Exception as exc:
            if tool_error_converter:
                raise tool_error_converter(exc) from exc
            raise

    return (
        search_tools,
        execute_workflow,
        execute_tool,
    )
