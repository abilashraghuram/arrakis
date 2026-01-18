"""Search for tools by query."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from ...logger import get_logger

if TYPE_CHECKING:
    from ..manager import ToolManager


_log = get_logger("cintegrity.gateway.tools.search_tools")


async def search_tools(manager: ToolManager, *, query: str) -> dict[str, Any]:
    """Search for tools by name, description, or argument names.

    Returns matching tools WITH their full schemas.
    """
    _log.info(f"Search query: {query}", extra={"event": "search_tools_start", "query": query})

    start_time = time.perf_counter()
    results = manager.search(query, limit=5)

    def to_tool_dict(spec: Any, server: str | None) -> dict[str, Any]:
        prefix = f"cintegrity.mcp_tools.{server}" if server else "cintegrity.function_calls"
        return {
            "name": spec.name,
            "description": spec.description,
            "inputSchema": spec.inputSchema,
            **({"outputSchema": spec.outputSchema} if spec.outputSchema else {}),
            "import_path": f"from {prefix} import {spec.name}",
        }

    tool_dicts = [to_tool_dict(r.spec, manager.get(r.spec.name).server) for r in results]
    duration_ms = (time.perf_counter() - start_time) * 1000

    top_tools = [t["name"] for t in tool_dicts[:3]]
    _log.info(
        f"Search completed: {len(tool_dicts)} results [Duration: {duration_ms:.2f}ms]",
        extra={
            "event": "search_tools_complete",
            "query": query,
            "result_count": len(tool_dicts),
            "top_results": top_tools,
            "duration_ms": duration_ms,
        },
    )

    return {"tools": tool_dicts}
