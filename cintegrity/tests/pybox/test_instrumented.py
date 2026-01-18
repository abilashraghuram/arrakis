"""Unit tests for AST instrumentation data flow tracking."""

from cintegrity.pybox.dataflow.instrumented import (
    DataFlowInstrumenter,
    InstrumentedValue,
    InstrumentedWrapper,
    OriginMap,
)
from cintegrity.pybox.provenance import Origin


class TestOriginMap:
    """Unit tests for OriginMap tracking."""

    def test_assign_and_get(self) -> None:
        """OriginMap stores and retrieves origins."""
        origin_map = OriginMap()
        origins = frozenset(["search#0"])

        origin_map.assign("x", origins)
        result = origin_map.get("x")

        assert result == origins

    def test_get_unknown_returns_empty(self) -> None:
        """Getting unknown variable returns empty frozenset."""
        origin_map = OriginMap()
        result = origin_map.get("unknown")
        assert result == frozenset()

    def test_merge_multiple_variables(self) -> None:
        """merge() combines origins from multiple variables."""
        origin_map = OriginMap()
        origin_map.assign("a", frozenset(["tool_a#0"]))
        origin_map.assign("b", frozenset(["tool_b#0"]))

        merged = origin_map.merge("a", "b")

        assert "tool_a#0" in merged
        assert "tool_b#0" in merged

    def test_merge_with_unknown(self) -> None:
        """merge() handles unknown variables gracefully."""
        origin_map = OriginMap()
        origin_map.assign("a", frozenset(["tool_a#0"]))

        merged = origin_map.merge("a", "unknown")

        assert merged == frozenset(["tool_a#0"])

    def test_clear(self) -> None:
        """clear() removes all tracked origins."""
        origin_map = OriginMap()
        origin_map.assign("x", frozenset(["search#0"]))

        origin_map.clear()

        assert origin_map.get("x") == frozenset()


class TestInstrumentedValue:
    """Unit tests for InstrumentedValue wrapper."""

    def test_value_property(self) -> None:
        """InstrumentedValue.value returns underlying value."""
        origin = Origin(call_id="test#0", tool_name="test", timestamp=1.0)
        value = InstrumentedValue({"data": 1}, frozenset([origin]))

        assert value.value == {"data": 1}

    def test_origins_property(self) -> None:
        """InstrumentedValue.origins returns stored origins."""
        origin = Origin(call_id="test#0", tool_name="test", timestamp=1.0)
        value = InstrumentedValue({"data": 1}, frozenset([origin]))

        assert origin in value.origins

    def test_indexing_delegates(self) -> None:
        """Indexing delegates to underlying value."""
        origin = Origin(call_id="test#0", tool_name="test", timestamp=1.0)
        value = InstrumentedValue({"key": "val"}, frozenset([origin]))

        result = value["key"]
        assert result == "val"

    def test_iteration_delegates(self) -> None:
        """Iteration delegates to underlying value."""
        origin = Origin(call_id="test#0", tool_name="test", timestamp=1.0)
        value = InstrumentedValue([1, 2, 3], frozenset([origin]))

        items = list(value)
        assert items == [1, 2, 3]

    def test_len(self) -> None:
        """len() works on InstrumentedValue."""
        origin = Origin(call_id="test#0", tool_name="test", timestamp=1.0)
        value = InstrumentedValue([1, 2, 3], frozenset([origin]))

        assert len(value) == 3

    def test_str(self) -> None:
        """str() works on InstrumentedValue."""
        origin = Origin(call_id="test#0", tool_name="test", timestamp=1.0)
        value = InstrumentedValue("hello", frozenset([origin]))

        assert str(value) == "hello"

    def test_repr(self) -> None:
        """repr() shows InstrumentedValue wrapper."""
        origin = Origin(call_id="test#0", tool_name="test", timestamp=1.0)
        value = InstrumentedValue(42, frozenset([origin]))

        assert "InstrumentedValue" in repr(value)

    def test_bool_true(self) -> None:
        """bool() on truthy value."""
        origin = Origin(call_id="test#0", tool_name="test", timestamp=1.0)
        assert bool(InstrumentedValue([1], frozenset([origin])))

    def test_bool_false(self) -> None:
        """bool() on falsy value."""
        origin = Origin(call_id="test#0", tool_name="test", timestamp=1.0)
        assert not bool(InstrumentedValue([], frozenset([origin])))


class TestInstrumentedWrapper:
    """Unit tests for InstrumentedWrapper factory."""

    def test_wrap_returns_instrumented_value(self) -> None:
        """wrap() returns InstrumentedValue with origin."""
        wrapper = InstrumentedWrapper()
        origin = Origin(call_id="test#0", tool_name="test", timestamp=1.0)

        result = wrapper.wrap({"data": 1}, origin)

        assert isinstance(result, InstrumentedValue)
        assert result.value == {"data": 1}
        assert origin in result.origins

    def test_literal_returns_empty_origins(self) -> None:
        """literal() returns InstrumentedValue with no origins."""
        wrapper = InstrumentedWrapper()

        result = wrapper.literal("hello")

        assert isinstance(result, InstrumentedValue)
        assert result.value == "hello"
        assert result.origins == frozenset()


class TestDataFlowInstrumenter:
    """Unit tests for AST transformation."""

    def test_transforms_simple_assign(self) -> None:
        """Simple assignment gets tracking wrapper."""
        import ast

        code = "x = 5"
        tree = ast.parse(code)

        instrumenter = DataFlowInstrumenter()
        transformed = instrumenter.visit(tree)

        # Should have __track_assign__ call
        transformed_code = ast.unparse(transformed)
        assert "__track_assign__" in transformed_code
        # ast.unparse may use single or double quotes
        assert "'x'" in transformed_code or '"x"' in transformed_code

    def test_transforms_subscript_load(self) -> None:
        """Subscript read gets tracking wrapper."""
        import ast

        code = "y = data['key']"
        tree = ast.parse(code)

        instrumenter = DataFlowInstrumenter()
        transformed = instrumenter.visit(tree)

        transformed_code = ast.unparse(transformed)
        assert "__track_subscript__" in transformed_code

    def test_transforms_attribute_load(self) -> None:
        """Attribute read gets tracking wrapper."""
        import ast

        code = "y = obj.attr"
        tree = ast.parse(code)

        instrumenter = DataFlowInstrumenter()
        transformed = instrumenter.visit(tree)

        transformed_code = ast.unparse(transformed)
        assert "__track_attr__" in transformed_code
