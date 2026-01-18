"""Unit tests for TransparentValue fine-grained data flow tracking."""

import pytest

from cintegrity.pybox.bridge import DirectToolBridge
from cintegrity.pybox.dataflow import TrackingStrategy
from cintegrity.pybox.dataflow.transparent import TransparentValue
from cintegrity.pybox.engine import WorkflowEngine
from cintegrity.pybox.provenance import Origin


class TestTransparentValueUnit:
    """Unit tests for TransparentValue dunder methods."""

    def test_indexing_preserves_origins(self) -> None:
        """Indexing returns new TransparentValue with same origins."""
        origin = Origin(call_id="search#0", tool_name="search", timestamp=1.0)
        value = TransparentValue({"data": [1, 2, 3]}, frozenset([origin]))

        result = value["data"]
        assert isinstance(result, TransparentValue)
        assert result.value == [1, 2, 3]
        assert origin in result.origins

    def test_nested_indexing_preserves_origins(self) -> None:
        """Chained indexing preserves origins."""
        origin = Origin(call_id="search#0", tool_name="search", timestamp=1.0)
        value = TransparentValue({"data": [{"id": 1}, {"id": 2}]}, frozenset([origin]))

        result = value["data"][0]["id"]
        assert isinstance(result, TransparentValue)
        assert result.value == 1
        assert origin in result.origins

    def test_iteration_preserves_origins(self) -> None:
        """Iterating yields TransparentValues with same origins."""
        origin = Origin(call_id="search#0", tool_name="search", timestamp=1.0)
        value = TransparentValue([1, 2, 3], frozenset([origin]))

        items = list(value)
        assert len(items) == 3
        for item in items:
            assert isinstance(item, TransparentValue)
            assert origin in item.origins

    def test_arithmetic_merges_origins(self) -> None:
        """Arithmetic operations merge origins from both operands."""
        origin1 = Origin(call_id="get_price#0", tool_name="get_price", timestamp=1.0)
        origin2 = Origin(call_id="get_tax#0", tool_name="get_tax", timestamp=2.0)

        price = TransparentValue(100, frozenset([origin1]))
        tax = TransparentValue(10, frozenset([origin2]))

        total = price + tax
        assert isinstance(total, TransparentValue)
        assert total.value == 110
        assert origin1 in total.origins
        assert origin2 in total.origins

    def test_arithmetic_with_literal(self) -> None:
        """Arithmetic with literal preserves original origins."""
        origin = Origin(call_id="get_price#0", tool_name="get_price", timestamp=1.0)
        price = TransparentValue(100, frozenset([origin]))

        result = price * 2
        assert isinstance(result, TransparentValue)
        assert result.value == 200
        assert origin in result.origins

    def test_comparison_returns_bool(self) -> None:
        """Comparison operations return raw bool, not TransparentValue."""
        origin = Origin(call_id="search#0", tool_name="search", timestamp=1.0)
        value = TransparentValue(10, frozenset([origin]))

        assert value == 10
        assert value != 5
        assert value > 5
        assert value < 15
        assert isinstance(value == 10, bool)

    def test_dict_get_preserves_origins(self) -> None:
        """Dict .get() preserves origins."""
        origin = Origin(call_id="search#0", tool_name="search", timestamp=1.0)
        value = TransparentValue({"key": "value"}, frozenset([origin]))

        result = value.get("key")
        assert isinstance(result, TransparentValue)
        assert result.value == "value"
        assert origin in result.origins

    def test_dict_items_preserves_origins(self) -> None:
        """Dict .items() yields values with origins."""
        origin = Origin(call_id="search#0", tool_name="search", timestamp=1.0)
        value = TransparentValue({"a": 1, "b": 2}, frozenset([origin]))

        for k, v in value.items():
            assert isinstance(v, TransparentValue)
            assert origin in v.origins


@pytest.mark.anyio
async def test_origins_preserved_through_indexing():
    """Origins survive result['data'][0] access in workflow."""
    bridge = DirectToolBridge()

    async def search(query: str) -> dict:
        return {"data": [{"id": 1, "name": "test"}]}

    async def process(item: dict) -> dict:
        return {"processed": item["id"]}

    bridge.register("search", search)
    bridge.register("process", process)
    engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

    # Access nested data - origins should be preserved!
    code = """
from cintegrity.tools import search, process

async def workflow():
    search_result = await search(query="test")
    item = search_result["data"][0]
    result = await process(item=item)
    return result
"""
    execution = await engine.execute(code)

    assert len(execution.calls) == 2
    # Origins preserved through indexing
    assert "search#0" in execution.calls[1].all_input_origins()
    assert "item" in execution.calls[1].input_origins
    assert "search#0" in execution.calls[1].input_origins["item"]


@pytest.mark.anyio
async def test_origins_merged_in_arithmetic():
    """Arithmetic operations merge origins from both operands."""
    bridge = DirectToolBridge()

    async def get_price() -> int:
        return 100

    async def get_tax() -> int:
        return 10

    async def submit(total: int) -> dict:
        return {"submitted": total}

    bridge.register("get_price", get_price)
    bridge.register("get_tax", get_tax)
    bridge.register("submit", submit)
    engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

    code = """
from cintegrity.tools import get_price, get_tax, submit

async def workflow():
    price = await get_price()
    tax = await get_tax()
    total = price + tax
    result = await submit(total=total)
    return result
"""
    execution = await engine.execute(code)

    assert len(execution.calls) == 3
    # submit should have origins from BOTH get_price and get_tax (merged in 'total' arg)
    all_origins = execution.calls[2].all_input_origins()
    assert "get_price#0" in all_origins
    assert "get_tax#0" in all_origins
    # Both origins flow through the 'total' argument
    assert "total" in execution.calls[2].input_origins
    assert "get_price#0" in execution.calls[2].input_origins["total"]
    assert "get_tax#0" in execution.calls[2].input_origins["total"]


@pytest.mark.anyio
async def test_origins_preserved_through_iteration():
    """Origins preserved when iterating over results."""
    bridge = DirectToolBridge()

    async def get_items() -> list:
        return [{"id": 1}, {"id": 2}]

    async def process_item(item: dict) -> dict:
        return {"processed": item["id"]}

    bridge.register("get_items", get_items)
    bridge.register("process_item", process_item)
    engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

    code = """
from cintegrity.tools import get_items, process_item

async def workflow():
    items = await get_items()
    first_item = items[0]
    result = await process_item(item=first_item)
    return result
"""
    execution = await engine.execute(code)

    assert len(execution.calls) == 2
    assert "get_items#0" in execution.calls[1].all_input_origins()
    assert "item" in execution.calls[1].input_origins
    assert "get_items#0" in execution.calls[1].input_origins["item"]


@pytest.mark.anyio
async def test_none_strategy_no_tracking():
    """NONE strategy doesn't track origins."""
    bridge = DirectToolBridge()

    async def search(query: str) -> dict:
        return {"data": [1, 2, 3]}

    async def process(data: list) -> dict:
        return {"count": len(data)}

    bridge.register("search", search)
    bridge.register("process", process)
    engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.NONE)

    code = """
from cintegrity.tools import search, process

async def workflow():
    search_result = await search(query="test")
    result = await process(data=search_result)
    return result
"""
    execution = await engine.execute(code)

    assert len(execution.calls) == 2
    # No origin tracking with NONE strategy
    assert len(execution.calls[1].input_origins) == 0
