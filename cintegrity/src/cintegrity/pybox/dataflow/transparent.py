"""Transparent data flow tracking via dunder methods.

TransparentValue preserves origins through natural Python operations
like indexing, iteration, and arithmetic.
"""

from collections.abc import Hashable, Iterator
from typing import Any

from ..provenance import Origin
from .base import TrackedValue


class TransparentValue:
    """Transparent wrapper that preserves origins through operations.

    Implements TrackedValue protocol. Uses dunder methods for natural access:
    - result["data"] returns TransparentValue with same origins
    - result + other merges origins from both operands
    - for item in result yields TransparentValue for each item
    """

    __slots__ = ("_value", "_origins")

    _value: Any
    _origins: frozenset[Origin]

    def __init__(self, value: Any, origins: frozenset[Origin]) -> None:
        object.__setattr__(self, "_value", value)
        object.__setattr__(self, "_origins", origins)

    @property
    def value(self) -> Any:
        """Access raw value (loses origin tracking)."""
        return self._value

    @property
    def origins(self) -> frozenset[Origin]:
        """Get origins that contributed to this value."""
        return self._origins

    # --- Container operations (preserve origins) ---

    def __getitem__(self, key: Any) -> "TransparentValue":
        """Indexing: result["data"] or result[0]"""
        return TransparentValue(self._value[key], self._origins)

    def __iter__(self) -> Iterator["TransparentValue"]:
        """Iteration: for item in result"""
        for item in self._value:
            yield TransparentValue(item, self._origins)

    def __len__(self) -> int:
        return len(self._value)

    def __contains__(self, item: Any) -> bool:
        return item in self._value

    # --- Attribute access and method calls ---

    def __getattr__(self, name: str) -> "TransparentValue":
        """Attribute access: result.some_field"""
        return TransparentValue(getattr(self._value, name), self._origins)

    def __call__(self, *args: Any, **kwargs: Any) -> "TransparentValue":
        """Method calls: result.lower(), result.startswith('x'), etc.

        When __getattr__ returns a wrapped method, calling it invokes __call__.
        This enables natural method chaining while preserving provenance.

        Example:
            name = result["name"]        # TransparentValue wrapping "Hello"
            lower = name.lower           # TransparentValue wrapping str.lower method
            lower()                      # __call__ invokes str.lower() -> "hello"
        """
        # Unwrap any TransparentValue arguments to get raw values
        unwrapped_args = tuple(arg.value if isinstance(arg, TrackedValue) else arg for arg in args)
        unwrapped_kwargs = {k: v.value if isinstance(v, TrackedValue) else v for k, v in kwargs.items()}

        # Merge origins from all TrackedValue arguments
        merged_origins = self._origins
        for arg in args:
            if isinstance(arg, TrackedValue):
                merged_origins = merged_origins | arg.origins
        for v in kwargs.values():
            if isinstance(v, TrackedValue):
                merged_origins = merged_origins | v.origins

        # Call the underlying callable and wrap the result
        result = self._value(*unwrapped_args, **unwrapped_kwargs)
        return TransparentValue(result, merged_origins)

    # --- Comparison (return raw bool, not TransparentValue) ---

    def __eq__(self, other: Any) -> bool:
        other_val = other.value if isinstance(other, TrackedValue) else other
        return self._value == other_val

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other: Any) -> bool:
        other_val = other.value if isinstance(other, TrackedValue) else other
        return self._value < other_val

    def __le__(self, other: Any) -> bool:
        other_val = other.value if isinstance(other, TrackedValue) else other
        return self._value <= other_val

    def __gt__(self, other: Any) -> bool:
        other_val = other.value if isinstance(other, TrackedValue) else other
        return self._value > other_val

    def __ge__(self, other: Any) -> bool:
        other_val = other.value if isinstance(other, TrackedValue) else other
        return self._value >= other_val

    # --- Arithmetic (merge origins) ---

    def _merge_origins(self, other: Any) -> frozenset[Origin]:
        """Merge origins from this value and other."""
        if isinstance(other, TrackedValue):
            return self._origins | other.origins
        return self._origins

    def _unwrap(self, other: Any) -> Any:
        """Unwrap TrackedValue to raw value."""
        return other.value if isinstance(other, TrackedValue) else other

    def __add__(self, other: Any) -> "TransparentValue":
        return TransparentValue(self._value + self._unwrap(other), self._merge_origins(other))

    def __radd__(self, other: Any) -> "TransparentValue":
        return TransparentValue(self._unwrap(other) + self._value, self._merge_origins(other))

    def __sub__(self, other: Any) -> "TransparentValue":
        return TransparentValue(self._value - self._unwrap(other), self._merge_origins(other))

    def __rsub__(self, other: Any) -> "TransparentValue":
        return TransparentValue(self._unwrap(other) - self._value, self._merge_origins(other))

    def __mul__(self, other: Any) -> "TransparentValue":
        return TransparentValue(self._value * self._unwrap(other), self._merge_origins(other))

    def __rmul__(self, other: Any) -> "TransparentValue":
        return TransparentValue(self._unwrap(other) * self._value, self._merge_origins(other))

    def __truediv__(self, other: Any) -> "TransparentValue":
        return TransparentValue(self._value / self._unwrap(other), self._merge_origins(other))

    def __rtruediv__(self, other: Any) -> "TransparentValue":
        return TransparentValue(self._unwrap(other) / self._value, self._merge_origins(other))

    def __floordiv__(self, other: Any) -> "TransparentValue":
        return TransparentValue(self._value // self._unwrap(other), self._merge_origins(other))

    def __rfloordiv__(self, other: Any) -> "TransparentValue":
        return TransparentValue(self._unwrap(other) // self._value, self._merge_origins(other))

    def __mod__(self, other: Any) -> "TransparentValue":
        return TransparentValue(self._value % self._unwrap(other), self._merge_origins(other))

    def __rmod__(self, other: Any) -> "TransparentValue":
        return TransparentValue(self._unwrap(other) % self._value, self._merge_origins(other))

    def __neg__(self) -> "TransparentValue":
        return TransparentValue(-self._value, self._origins)

    def __pos__(self) -> "TransparentValue":
        return TransparentValue(+self._value, self._origins)

    def __abs__(self) -> "TransparentValue":
        return TransparentValue(abs(self._value), self._origins)

    # --- String operations ---

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f"TransparentValue({self._value!r}, origins={len(self._origins)})"

    # --- Boolean ---

    def __bool__(self) -> bool:
        return bool(self._value)

    # --- Hash (for use in sets/dicts) ---

    def __hash__(self) -> int:
        # Hash based on value only, not origins
        if isinstance(self._value, Hashable):
            return hash(self._value)
        return id(self)

    # --- Dict-like methods (if value is dict) ---

    def keys(self) -> Any:
        """Return keys of underlying dict."""
        return self._value.keys()

    def values(self) -> Iterator["TransparentValue"]:
        """Yield values wrapped with origins."""
        for v in self._value.values():
            yield TransparentValue(v, self._origins)

    def items(self) -> Iterator[tuple[Any, "TransparentValue"]]:
        """Yield (key, value) pairs with values wrapped."""
        for k, v in self._value.items():
            yield k, TransparentValue(v, self._origins)

    def get(self, key: Any, default: Any = None) -> "TransparentValue":
        """Get value by key, preserving origins."""
        val = self._value.get(key, default)
        return TransparentValue(val, self._origins)

    # --- Factory methods ---

    @classmethod
    def from_tool(cls, value: Any, origin: Origin) -> "TransparentValue":
        """Create from tool output with single origin."""
        return cls(value=value, origins=frozenset([origin]))

    @classmethod
    def literal(cls, value: Any) -> "TransparentValue":
        """Create from literal value with no origins."""
        return cls(value=value, origins=frozenset())


class TransparentWrapper:
    """Factory implementing ValueWrapper protocol for transparent data flow tracking."""

    def wrap(self, value: Any, origin: Origin) -> TransparentValue:
        """Wrap a tool result with provenance origin."""
        return TransparentValue.from_tool(value, origin)

    def literal(self, value: Any) -> TransparentValue:
        """Wrap a literal value (no origins)."""
        return TransparentValue(value, frozenset())
