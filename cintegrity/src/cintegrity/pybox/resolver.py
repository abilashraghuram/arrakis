"""Value resolver - unwrap TrackedValue to raw values for tool calls.

Tools receive raw Python values, not TrackedValue wrappers.
"""

from typing import Any, Protocol

from .dataflow.base import TrackedValue


class ValueResolver(Protocol):
    """Protocol for resolving TrackedValue wrappers to raw values."""

    def resolve(self, value: Any) -> Any:
        """Recursively unwrap TrackedValue to raw value."""
        ...


def resolve_value(value: Any) -> Any:
    """Recursively resolve TrackedValue wrappers to raw values."""
    if isinstance(value, TrackedValue):
        return resolve_value(value.value)
    if isinstance(value, dict):
        return {k: resolve_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_value(v) for v in value]
    if isinstance(value, tuple):
        return tuple(resolve_value(v) for v in value)
    return value


class RecursiveValueResolver:
    """Default implementation using recursive resolution."""

    def resolve(self, value: Any) -> Any:
        return resolve_value(value)
