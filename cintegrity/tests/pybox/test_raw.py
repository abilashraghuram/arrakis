"""Unit tests for RawValue - no origin tracking implementation."""

import pytest

from cintegrity.pybox.bridge import DirectToolBridge
from cintegrity.pybox.dataflow import TrackingStrategy
from cintegrity.pybox.dataflow.raw import RawValue, RawWrapper
from cintegrity.pybox.engine import WorkflowEngine
from cintegrity.pybox.provenance import Origin


class TestRawValueUnit:
    """Unit tests for RawValue - verifies no origin tracking."""

    def test_value_property(self) -> None:
        """RawValue.value returns underlying value."""
        raw = RawValue({"data": [1, 2, 3]})
        assert raw.value == {"data": [1, 2, 3]}

    def test_origins_always_empty(self) -> None:
        """RawValue always returns empty origins."""
        raw = RawValue({"data": [1, 2, 3]})
        assert raw.origins == frozenset()

    def test_indexing_returns_raw(self) -> None:
        """Indexing returns raw value, not RawValue."""
        raw = RawValue({"data": [1, 2, 3]})
        result = raw["data"]
        # RawValue indexing returns raw value
        assert result == [1, 2, 3]

    def test_iteration_returns_raw(self) -> None:
        """Iteration returns raw values."""
        raw = RawValue([1, 2, 3])
        items = list(raw)
        assert items == [1, 2, 3]

    def test_len(self) -> None:
        """len() works on RawValue."""
        raw = RawValue([1, 2, 3])
        assert len(raw) == 3

    def test_str(self) -> None:
        """str() works on RawValue."""
        raw = RawValue("hello")
        assert str(raw) == "hello"

    def test_repr(self) -> None:
        """repr() shows RawValue wrapper."""
        raw = RawValue(42)
        assert "RawValue" in repr(raw)

    def test_bool_true(self) -> None:
        """bool() on truthy value."""
        assert bool(RawValue([1]))
        assert bool(RawValue(1))
        assert bool(RawValue("hello"))

    def test_bool_false(self) -> None:
        """bool() on falsy value."""
        assert not bool(RawValue([]))
        assert not bool(RawValue(0))
        assert not bool(RawValue(""))


class TestRawWrapperUnit:
    """Unit tests for RawWrapper factory."""

    def test_wrap_returns_raw_value(self) -> None:
        """wrap() returns RawValue ignoring origin."""
        wrapper = RawWrapper()
        origin = Origin(call_id="test#0", tool_name="test", timestamp=1.0)

        result = wrapper.wrap({"data": 1}, origin)

        assert isinstance(result, RawValue)
        assert result.value == {"data": 1}
        # Origin is ignored - no origin tracking
        assert result.origins == frozenset()

    def test_literal_returns_raw_value(self) -> None:
        """literal() returns RawValue."""
        wrapper = RawWrapper()

        result = wrapper.literal("hello")

        assert isinstance(result, RawValue)
        assert result.value == "hello"
        assert result.origins == frozenset()


@pytest.mark.anyio
async def test_none_strategy_workflow_no_tracking():
    """NONE strategy workflow has no origin tracking."""
    bridge = DirectToolBridge()

    async def get_data() -> dict:
        return {"items": [1, 2, 3]}

    async def process(items: list) -> dict:
        return {"count": len(items)}

    bridge.register("get_data", get_data)
    bridge.register("process", process)
    engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.NONE)

    code = """
from cintegrity.tools import get_data, process

async def workflow():
    data = await get_data()
    result = await process(items=data)
    return result
"""
    execution = await engine.execute(code)

    assert len(execution.calls) == 2
    # No origin tracking - input_origins empty
    assert len(execution.calls[1].input_origins) == 0


@pytest.mark.anyio
async def test_none_strategy_multiple_tools():
    """NONE strategy with multiple tool calls."""
    bridge = DirectToolBridge()

    async def tool_a() -> int:
        return 10

    async def tool_b() -> int:
        return 20

    async def combine(a: int, b: int) -> int:
        return a + b

    bridge.register("tool_a", tool_a)
    bridge.register("tool_b", tool_b)
    bridge.register("combine", combine)
    engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.NONE)

    code = """
from cintegrity.tools import tool_a, tool_b, combine

async def workflow():
    a = await tool_a()
    b = await tool_b()
    result = await combine(a=a, b=b)
    return result
"""
    execution = await engine.execute(code)

    assert len(execution.calls) == 3
    # No origins tracked for any call
    for call in execution.calls:
        assert len(call.input_origins) == 0
