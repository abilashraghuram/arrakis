"""Tests for provenance JSON export."""

import json

import pytest

from cintegrity.pybox.bridge import DirectToolBridge
from cintegrity.pybox.dataflow import TrackingStrategy
from cintegrity.pybox.engine import WorkflowEngine
from cintegrity.pybox.provenance import (
    ExecutionResult,
    Origin,
    ToolCallRecord,
    _serialize_value,
)


class TestSerializeValue:
    """Tests for _serialize_value helper."""

    def test_primitives(self) -> None:
        """Primitives serialize as-is."""
        assert _serialize_value(None) is None
        assert _serialize_value("hello") == "hello"
        assert _serialize_value(42) == 42
        assert _serialize_value(3.14) == 3.14
        assert _serialize_value(True) is True

    def test_list(self) -> None:
        """Lists serialize recursively."""
        assert _serialize_value([1, 2, 3]) == [1, 2, 3]
        assert _serialize_value([{"a": 1}]) == [{"a": 1}]

    def test_dict(self) -> None:
        """Dicts serialize recursively."""
        assert _serialize_value({"key": "value"}) == {"key": "value"}
        assert _serialize_value({"nested": {"a": 1}}) == {"nested": {"a": 1}}

    def test_frozenset(self) -> None:
        """Frozensets convert to sorted lists."""
        result = _serialize_value(frozenset(["b", "a", "c"]))
        assert result == ["a", "b", "c"]

    def test_complex_object(self) -> None:
        """Complex objects convert to string."""

        class Custom:
            def __str__(self) -> str:
                return "CustomObject"

        result = _serialize_value(Custom())
        assert result == "CustomObject"


class TestOriginExport:
    """Tests for Origin.to_dict()."""

    def test_to_dict(self) -> None:
        """Origin exports to dict."""
        origin = Origin(call_id="search#0", tool_name="search", timestamp=1234.5)

        result = origin.to_dict()

        assert result == {
            "call_id": "search#0",
            "tool_name": "search",
            "timestamp": 1234.5,
        }


class TestToolCallRecordExport:
    """Tests for ToolCallRecord.to_dict()."""

    def test_to_dict_simple(self) -> None:
        """ToolCallRecord exports inputs and outputs."""
        record = ToolCallRecord(
            call_id="search#0",
            tool_name="search",
            input_value={"query": "test"},
            input_origins={},  # No taint - empty dict
            output_value={"results": [1, 2, 3]},
            timestamp=1234.5,
        )

        result = record.to_dict()

        assert result["call_id"] == "search#0"
        assert result["tool_name"] == "search"
        assert result["input_value"] == {"query": "test"}
        assert result["input_origins"] == {}  # Per-argument format
        assert result["output_value"] == {"results": [1, 2, 3]}
        assert result["timestamp"] == 1234.5

    def test_to_dict_with_origins(self) -> None:
        """ToolCallRecord exports per-argument input_origins."""
        record = ToolCallRecord(
            call_id="process#0",
            tool_name="process",
            input_value={"a": "from_search", "b": "from_fetch"},
            input_origins={
                "a": ("search#0",),
                "b": ("fetch#0",),
            },
            output_value={"done": True},
            timestamp=1234.5,
        )

        result = record.to_dict()

        # Per-argument origins
        assert result["input_origins"] == {
            "a": ["search#0"],
            "b": ["fetch#0"],
        }


class TestExecutionResultExport:
    """Tests for ExecutionResult.to_dict() and to_json()."""

    def test_to_dict_structure(self) -> None:
        """ExecutionResult exports with data_flow graph."""
        records = (
            ToolCallRecord(
                call_id="search#0",
                tool_name="search",
                input_value={"query": "test"},
                input_origins={},
                output_value={"data": [1, 2]},
                timestamp=1.0,
            ),
            ToolCallRecord(
                call_id="process#0",
                tool_name="process",
                input_value={"items": [1, 2]},
                input_origins={"items": ("search#0",)},
                output_value={"count": 2},
                timestamp=2.0,
            ),
        )
        result = ExecutionResult(returned={"count": 2}, calls=records)

        exported = result.to_dict()

        assert "returned" in exported
        assert "calls" in exported
        assert "data_flow" in exported
        assert len(exported["calls"]) == 2

    def test_data_flow_graph(self) -> None:
        """Data flow graph contains nodes and edges with arg info."""
        records = (
            ToolCallRecord(
                call_id="search#0",
                tool_name="search",
                input_value={},
                input_origins={},
                output_value={},
                timestamp=1.0,
            ),
            ToolCallRecord(
                call_id="process#0",
                tool_name="process",
                input_value={"data": {}},
                input_origins={"data": ("search#0",)},
                output_value={},
                timestamp=2.0,
            ),
        )
        result = ExecutionResult(returned=None, calls=records)

        flow = result.to_dict()["data_flow"]

        # Check nodes
        assert len(flow["nodes"]) == 2
        assert flow["nodes"][0]["id"] == "search#0"
        assert flow["nodes"][1]["id"] == "process#0"

        # Check edges (search#0 -> process#0 via 'data' arg)
        assert len(flow["edges"]) == 1
        assert flow["edges"][0] == {
            "source": "search#0",
            "sink": "process#0",
            "args": ["data"],
        }

    def test_to_json(self) -> None:
        """to_json() produces valid JSON string."""
        records = (
            ToolCallRecord(
                call_id="test#0",
                tool_name="test",
                input_value={"key": "value"},
                input_origins={},
                output_value=42,
                timestamp=1.0,
            ),
        )
        result = ExecutionResult(returned=42, calls=records)

        json_str = result.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["returned"] == 42
        assert len(parsed["calls"]) == 1


@pytest.mark.anyio
async def test_workflow_export_integration():
    """End-to-end test: workflow execution produces exportable result."""
    bridge = DirectToolBridge()

    async def search(query: str) -> dict:
        return {"data": [{"id": 1, "name": query}]}

    async def process(item: dict) -> dict:
        return {"processed": item["id"]}

    bridge.register("search", search)
    bridge.register("process", process)
    engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

    code = """
from cintegrity.tools import search, process

async def workflow():
    search_result = await search(query="test")
    item = search_result["data"][0]
    result = await process(item=item)
    return result
"""
    execution = await engine.execute(code)

    # Export to dict
    exported = execution.to_dict()

    assert "returned" in exported
    assert "calls" in exported
    assert "data_flow" in exported

    # Verify data flow edge exists (search#0 -> process#0)
    edges = exported["data_flow"]["edges"]
    assert any(e["source"] == "search#0" and e["sink"] == "process#0" for e in edges)

    # Export to JSON should not raise
    json_str = execution.to_json()
    parsed = json.loads(json_str)
    assert parsed["data_flow"]["nodes"][0]["tool"] == "search"


@pytest.mark.anyio
async def test_complex_data_flow_export():
    """Test export with multiple data flow paths."""
    bridge = DirectToolBridge()

    async def get_price() -> int:
        return 100

    async def get_tax() -> int:
        return 10

    async def calculate(price: int, tax: int) -> int:
        return price + tax

    bridge.register("get_price", get_price)
    bridge.register("get_tax", get_tax)
    bridge.register("calculate", calculate)
    engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

    code = """
from cintegrity.tools import get_price, get_tax, calculate

async def workflow():
    price = await get_price()
    tax = await get_tax()
    total = price + tax
    result = await calculate(price=total, tax=0)
    return result
"""
    execution = await engine.execute(code)
    exported = execution.to_dict()

    # Should have 3 tool calls
    assert len(exported["calls"]) == 3

    # calculate#0 should have edges from both get_price#0 and get_tax#0
    edges = exported["data_flow"]["edges"]
    calc_sources = [e["source"] for e in edges if e["sink"] == "calculate#0"]
    assert "get_price#0" in calc_sources
    assert "get_tax#0" in calc_sources
