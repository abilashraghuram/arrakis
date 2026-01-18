"""End-to-end provenance tracking tests."""

import pytest

from cintegrity.pybox.bridge import DirectToolBridge
from cintegrity.pybox.engine import WorkflowEngine


@pytest.mark.anyio
async def test_single_tool_call_tracking():
    """Verify single tool call is tracked with correct origin."""
    bridge = DirectToolBridge()

    async def search(query: str) -> dict:
        return {"results": [{"id": 1, "name": query}]}

    bridge.register("search", search)
    engine = WorkflowEngine(bridge=bridge)

    code = """
from cintegrity.tools import search

async def workflow():
    result = await search(query="test")
    return result
"""
    execution = await engine.execute(code)

    assert len(execution.calls) == 1
    assert execution.calls[0].tool_name == "search"
    assert execution.calls[0].call_id == "search#0"
    assert execution.calls[0].output_value == {"results": [{"id": 1, "name": "test"}]}


@pytest.mark.anyio
async def test_multiple_tool_calls():
    """Verify multiple tool calls are tracked separately."""
    bridge = DirectToolBridge()

    async def search(query: str) -> dict:
        return {"data": [{"id": 1}]}

    async def fetch(id: int) -> dict:
        return {"name": f"item-{id}"}

    bridge.register("search", search)
    bridge.register("fetch", fetch)
    engine = WorkflowEngine(bridge=bridge)

    code = """
from cintegrity.tools import search, fetch

async def workflow():
    search_result = await search(query="test")
    fetch_result = await fetch(id=1)
    return {"search": search_result.value, "fetch": fetch_result.value}
"""
    execution = await engine.execute(code)

    assert len(execution.calls) == 2
    assert execution.calls[0].call_id == "search#0"
    assert execution.calls[1].call_id == "fetch#0"


@pytest.mark.anyio
async def test_taint_propagation_between_tools():
    """Verify data flow tracking (SOURCE -> SINK).

    Taint is tracked when TaggedValue is passed directly to another tool.
    The resolver unwraps it before calling the actual tool.
    """
    bridge = DirectToolBridge()

    async def search(query: str) -> dict:
        return {"id": 1, "name": query}

    async def process(item: dict) -> dict:
        return {"processed": item["id"]}

    bridge.register("search", search)
    bridge.register("process", process)
    engine = WorkflowEngine(bridge=bridge)

    # Pass TaggedValue directly (not .value) to preserve taint
    code = """
from cintegrity.tools import search, process

async def workflow():
    search_result = await search(query="test")
    result = await process(item=search_result)
    return result
"""
    execution = await engine.execute(code)

    assert len(execution.calls) == 2
    # Second call should have first call as input origin (taint tracking)
    # Per-argument tracking: input_origins is now dict[arg_name, tuple[call_ids]]
    assert "search#0" in execution.calls[1].all_input_origins()
    # More granular: check the specific argument
    assert "item" in execution.calls[1].input_origins
    assert "search#0" in execution.calls[1].input_origins["item"]


@pytest.mark.anyio
async def test_nested_taint_propagation():
    """Verify taint propagation through nested structures.

    Taint is tracked when TaggedValue is passed directly.
    Accessing .value loses taint (coarse-grained tracking limitation).
    """
    bridge = DirectToolBridge()

    async def get_data() -> list:
        return [{"name": "a"}, {"name": "b"}]

    async def process_items(items: list) -> dict:
        return {"count": len(items)}

    bridge.register("get_data", get_data)
    bridge.register("process_items", process_items)
    engine = WorkflowEngine(bridge=bridge)

    # Pass TaggedValue directly to preserve taint
    code = """
from cintegrity.tools import get_data, process_items

async def workflow():
    data = await get_data()
    result = await process_items(items=data)
    return result
"""
    execution = await engine.execute(code)

    assert len(execution.calls) == 2
    # process_items should know its input came from get_data
    assert "get_data#0" in execution.calls[1].all_input_origins()
    assert "items" in execution.calls[1].input_origins
    assert "get_data#0" in execution.calls[1].input_origins["items"]


@pytest.mark.anyio
async def test_no_taint_for_literals():
    """Verify literal values have no taint origins."""
    bridge = DirectToolBridge()

    async def echo(value: str) -> str:
        return f"echo: {value}"

    bridge.register("echo", echo)
    engine = WorkflowEngine(bridge=bridge)

    code = """
from cintegrity.tools import echo

async def workflow():
    result = await echo(value="hello")
    return result
"""
    execution = await engine.execute(code)

    assert len(execution.calls) == 1
    # No previous tool calls, so no input origins
    assert len(execution.calls[0].input_origins) == 0


@pytest.mark.anyio
async def test_same_tool_called_multiple_times():
    """Verify same tool called multiple times gets unique call IDs."""
    bridge = DirectToolBridge()

    async def increment(n: int) -> int:
        return n + 1

    bridge.register("increment", increment)
    engine = WorkflowEngine(bridge=bridge)

    code = """
from cintegrity.tools import increment

async def workflow():
    a = await increment(n=1)
    b = await increment(n=2)
    c = await increment(n=3)
    return a.value + b.value + c.value
"""
    execution = await engine.execute(code)

    assert len(execution.calls) == 3
    assert execution.calls[0].call_id == "increment#0"
    assert execution.calls[1].call_id == "increment#1"
    assert execution.calls[2].call_id == "increment#2"


@pytest.mark.anyio
async def test_sync_tool_function():
    """Verify synchronous tool functions work correctly."""
    bridge = DirectToolBridge()

    def sync_add(a: int, b: int) -> int:
        return a + b

    bridge.register("add", sync_add)
    engine = WorkflowEngine(bridge=bridge)

    code = """
from cintegrity.tools import add

async def workflow():
    result = await add(a=2, b=3)
    return result
"""
    execution = await engine.execute(code)

    assert len(execution.calls) == 1
    assert execution.calls[0].output_value == 5
    # returned is TaggedValue; access .value for raw result
    assert execution.returned.value == 5
