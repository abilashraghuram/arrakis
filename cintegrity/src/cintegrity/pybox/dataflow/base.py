"""Protocols for data flow tracking.

Defines TrackedValue and ValueWrapper protocols for dependency inversion.
"""

from collections.abc import Iterator
from typing import Any, Protocol, runtime_checkable

from ..provenance import Origin


@runtime_checkable
class TrackedValue(Protocol):
    """Protocol for tracked values with provenance.

    Implementations must preserve origins through operations.
    """

    @property
    def value(self) -> Any:
        """Get raw unwrapped value."""
        ...

    @property
    def origins(self) -> frozenset[Origin]:
        """Get origins that contributed to this value."""
        ...

    def __getitem__(self, key: Any) -> "TrackedValue":
        """Index access preserves origins."""
        ...

    def __iter__(self) -> Iterator["TrackedValue"]:
        """Iteration preserves origins."""
        ...


class ValueWrapper(Protocol):
    """Protocol for creating tracked values."""

    def wrap(self, value: Any, origin: Origin) -> TrackedValue:
        """Wrap a tool result with provenance origin.

        Args:
            value: Raw value from tool execution
            origin: Provenance origin for tracking

        Returns:
            TrackedValue wrapping the result
        """
        ...

    def literal(self, value: Any) -> TrackedValue:
        """Wrap a literal value (no origins).

        Args:
            value: Literal value (not from tool)

        Returns:
            TrackedValue with empty origins
        """
        ...
