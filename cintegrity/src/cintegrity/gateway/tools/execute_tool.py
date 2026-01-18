"""Execute a single tool."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from ...logger import get_logger
from ..errors import ToolExecutionError

if TYPE_CHECKING:
    from ..manager import ToolManager


_log = get_logger("cintegrity.gateway.tools.execute_tool")


async def execute_tool(manager: ToolManager, *, tool_name: str, args: Any) -> Any:
    """Execute a single tool by name.

    Args:
        manager: ToolManager instance containing the tools
        tool_name: Name of the tool to execute
        args: Arguments to pass to the tool

    Returns:
        Tool execution result

    Raises:
        ToolExecutionError: If tool execution fails
    """
    _log.info(
        f"Tool: {tool_name}",
        extra={
            "event": "tool_execute_start",
            "tool_name": tool_name,
            "input_args": args,
        },
    )

    start_time = time.perf_counter()
    try:
        result = await manager.call(tool_name, args)
        duration_ms = (time.perf_counter() - start_time) * 1000

        _log.info(
            f"Tool: {tool_name} [Duration: {duration_ms:.2f}ms]",
            extra={
                "event": "tool_execute_complete",
                "tool_name": tool_name,
                "duration_ms": duration_ms,
                "output": result,
            },
        )
        return result
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000
        _log.error(
            f"Tool: {tool_name} FAILED [Duration: {duration_ms:.2f}ms]",
            extra={
                "event": "tool_execute_error",
                "tool_name": tool_name,
                "duration_ms": duration_ms,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
            exc_info=True,
        )
        raise ToolExecutionError(tool_name=tool_name, cause=exc) from exc
