"""Protocol conformance tests for data flow tracking and runtime implementations."""

import pytest

from cintegrity.pybox.dataflow.base import TrackedValue
from cintegrity.pybox.dataflow.instrumented import (
    InstrumentedValue,
    InstrumentedWrapper,
)
from cintegrity.pybox.dataflow.raw import RawValue, RawWrapper
from cintegrity.pybox.dataflow.transparent import TransparentValue, TransparentWrapper
from cintegrity.pybox.provenance import Origin


class TestTrackedValueProtocol:
    """Test that all implementations satisfy TrackedValue protocol."""

    def test_transparent_value_satisfies_protocol(self) -> None:
        """TransparentValue implements TrackedValue protocol."""
        origin = Origin(call_id="test#0", tool_name="test", timestamp=1.0)
        value = TransparentValue({"data": [1, 2]}, frozenset([origin]))

        # Protocol requires these properties/methods
        assert isinstance(value.value, dict)
        assert isinstance(value.origins, frozenset)
        _ = value["data"]  # __getitem__
        _ = list(value)  # __iter__ (iterates dict keys)

        # isinstance check with @runtime_checkable
        assert isinstance(value, TrackedValue)

    def test_instrumented_value_satisfies_protocol(self) -> None:
        """InstrumentedValue implements TrackedValue protocol."""
        origin = Origin(call_id="test#0", tool_name="test", timestamp=1.0)
        value = InstrumentedValue({"data": [1, 2]}, frozenset([origin]))

        # Protocol requires these properties/methods
        assert isinstance(value.value, dict)
        assert isinstance(value.origins, frozenset)
        _ = value["data"]  # __getitem__
        _ = list(value)  # __iter__ (iterates dict keys)

        # isinstance check with @runtime_checkable
        assert isinstance(value, TrackedValue)

    def test_raw_value_satisfies_protocol(self) -> None:
        """RawValue implements TrackedValue protocol."""
        value = RawValue({"data": [1, 2]})

        # Protocol requires these properties/methods
        assert isinstance(value.value, dict)
        assert isinstance(value.origins, frozenset)
        _ = value["data"]  # __getitem__
        _ = list(value)  # __iter__ (iterates dict keys)

        # isinstance check with @runtime_checkable
        assert isinstance(value, TrackedValue)


class TestValueWrapperProtocol:
    """Test that all wrappers satisfy ValueWrapper protocol."""

    @pytest.fixture
    def origin(self) -> Origin:
        return Origin(call_id="test#0", tool_name="test", timestamp=1.0)

    def test_transparent_wrapper_wrap(self, origin: Origin) -> None:
        """TransparentWrapper.wrap returns TrackedValue."""
        wrapper = TransparentWrapper()

        result = wrapper.wrap({"data": 1}, origin)

        assert isinstance(result, TrackedValue)
        assert result.value == {"data": 1}
        assert origin in result.origins

    def test_transparent_wrapper_literal(self) -> None:
        """TransparentWrapper.literal returns TrackedValue with no origins."""
        wrapper = TransparentWrapper()

        result = wrapper.literal("hello")

        assert isinstance(result, TrackedValue)
        assert result.value == "hello"
        assert result.origins == frozenset()

    def test_instrumented_wrapper_wrap(self, origin: Origin) -> None:
        """InstrumentedWrapper.wrap returns TrackedValue."""
        wrapper = InstrumentedWrapper()

        result = wrapper.wrap({"data": 1}, origin)

        assert isinstance(result, TrackedValue)
        assert result.value == {"data": 1}
        assert origin in result.origins

    def test_instrumented_wrapper_literal(self) -> None:
        """InstrumentedWrapper.literal returns TrackedValue with no origins."""
        wrapper = InstrumentedWrapper()

        result = wrapper.literal("hello")

        assert isinstance(result, TrackedValue)
        assert result.value == "hello"
        assert result.origins == frozenset()

    def test_raw_wrapper_wrap(self, origin: Origin) -> None:
        """RawWrapper.wrap returns TrackedValue (with no tracking)."""
        wrapper = RawWrapper()

        result = wrapper.wrap({"data": 1}, origin)

        assert isinstance(result, TrackedValue)
        assert result.value == {"data": 1}
        # RawWrapper ignores origin
        assert result.origins == frozenset()

    def test_raw_wrapper_literal(self) -> None:
        """RawWrapper.literal returns TrackedValue."""
        wrapper = RawWrapper()

        result = wrapper.literal("hello")

        assert isinstance(result, TrackedValue)
        assert result.value == "hello"
        assert result.origins == frozenset()


class TestTrackedValueBehaviors:
    """Test behavioral differences between implementations."""

    @pytest.fixture
    def origin(self) -> Origin:
        return Origin(call_id="search#0", tool_name="search", timestamp=1.0)

    def test_transparent_indexing_preserves_origins(self, origin: Origin) -> None:
        """TransparentValue indexing preserves origins."""
        value = TransparentValue({"data": [1, 2, 3]}, frozenset([origin]))

        result = value["data"]

        assert isinstance(result, TransparentValue)
        assert origin in result.origins

    def test_instrumented_indexing_returns_raw(self, origin: Origin) -> None:
        """InstrumentedValue indexing returns raw value (origins tracked via OriginMap)."""
        value = InstrumentedValue({"data": [1, 2, 3]}, frozenset([origin]))

        result = value["data"]

        # Returns raw value - origins tracked externally
        assert result == [1, 2, 3]
        assert not isinstance(result, InstrumentedValue)

    def test_raw_indexing_returns_raw(self) -> None:
        """RawValue indexing returns raw value."""
        value = RawValue({"data": [1, 2, 3]})

        result = value["data"]

        assert result == [1, 2, 3]
        assert not isinstance(result, RawValue)

    def test_transparent_iteration_preserves_origins(self, origin: Origin) -> None:
        """TransparentValue iteration yields tracked items."""
        value = TransparentValue([1, 2, 3], frozenset([origin]))

        items = list(value)

        assert all(isinstance(item, TransparentValue) for item in items)
        assert all(origin in item.origins for item in items)

    def test_instrumented_iteration_returns_raw(self, origin: Origin) -> None:
        """InstrumentedValue iteration returns raw items."""
        value = InstrumentedValue([1, 2, 3], frozenset([origin]))

        items = list(value)

        assert items == [1, 2, 3]
        assert all(not isinstance(item, InstrumentedValue) for item in items)

    def test_raw_iteration_returns_raw(self) -> None:
        """RawValue iteration returns raw items."""
        value = RawValue([1, 2, 3])

        items = list(value)

        assert items == [1, 2, 3]
