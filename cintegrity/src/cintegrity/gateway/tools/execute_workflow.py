"""Execute multi-step workflows."""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...adapters.tool_bridge import MCPToolBridge
from ...logger import get_logger
from ...pybox.dataflow import TrackingStrategy
from ...pybox.dataflow.base import TrackedValue
from ...pybox.engine import WorkflowEngine

if TYPE_CHECKING:
    from fastmcp import Context

    from ..manager import ToolManager


_log = get_logger("cintegrity.gateway.tools.execute_workflow")
_AUDIT_DIR = Path("logs")


async def execute_workflow(
    manager: ToolManager,
    planner_code: str,
    timeout: float = 30.0,
    ctx: Context | None = None,
) -> Any:
    """Execute Python workflow code.

    Args:
        manager: Tool manager instance with available tools
        planner_code: Python workflow code to execute
        timeout: Maximum execution time in seconds (default: 30)
        ctx: MCP context for elicitation support (optional)

    Returns:
        The raw value of the result (unwrapped from TaggedValue if applicable)
    """
    run_id = uuid.uuid4().hex
    start_time = time.perf_counter()

    _log.info("=" * 80)
    _log.info("WORKFLOW EXECUTION START")
    _log.info(f"Run ID: {run_id}")
    _log.info(f"Available Tools: {len(manager.tool_names())}")
    _log.info("=" * 80)
    _log.info("PLANNER CODE:")
    _log.info("-" * 80)
    for i, line in enumerate(planner_code.split("\n"), 1):
        _log.info(f"{i:3d} | {line}")
    _log.info("-" * 80)
    _log.info("")

    # Create bridge and engine (data flow tracking disabled for now)
    bridge = MCPToolBridge(manager)
    engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.NONE)

    # Create MCP elicitation adapter if context available
    from ...adapters.mcp_elicit import MCPElicitAdapter

    elicit_fn = MCPElicitAdapter(ctx) if ctx is not None else None

    # Execute workflow
    try:
        result = await engine.execute(planner_code, timeout=timeout, elicit_fn=elicit_fn)
        duration_ms = (time.perf_counter() - start_time) * 1000

        _log.info("")
        _log.info("=" * 80)
        _log.info("WORKFLOW COMPLETED SUCCESSFULLY")
        _log.info(f"Duration: {duration_ms:.2f}ms")
        _log.info(f"Tool Calls: {len(result.calls)}")
        _log.info(f"Result: {result.returned!r}")
        _log.info("=" * 80)
        _log.info("")

        # Write audit trail to JSON file
        try:
            _AUDIT_DIR.mkdir(parents=True, exist_ok=True)
            audit_file = _AUDIT_DIR / f"workflow-{run_id}.json"
            audit_file.write_text(result.to_json(indent=2))
            _log.info(f"Audit trail saved: {audit_file}")
        except (OSError, PermissionError) as e:
            _log.warning(f"Could not write audit trail: {e}")

        # Unwrap TrackedValue to return raw value
        returned = result.returned
        if isinstance(returned, TrackedValue):
            return returned.value
        return returned

    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000
        _log.error("")
        _log.error("=" * 80)
        _log.error("WORKFLOW FAILED")
        _log.error(f"Duration: {duration_ms:.2f}ms")
        _log.error(f"Error: {type(exc).__name__}: {exc}")
        _log.error("=" * 80)
        _log.error("", exc_info=True)
        raise
