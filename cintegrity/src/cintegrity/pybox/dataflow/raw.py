"""Raw value wrapper - no data flow tracking.

Pass-through implementation for when origin tracking is disabled.
"""

from collections.abc import Iterator
from typing import Any

from ..provenance import Origin


class RawValue:
    """No origin tracking - pass-through wrapper.

    Implements TrackedValue protocol. Returns empty origins.
    """

    def __init__(self, value: Any) -> None:
        self._value = value

    @property
    def value(self) -> Any:
        """Get raw value."""
        return self._value

    @property
    def origins(self) -> frozenset[Origin]:
        """Returns empty origins - no tracking."""
        return frozenset()

    def __getitem__(self, key: Any) -> Any:
        """Delegate indexing to underlying value."""
        return self._value[key]

    def __iter__(self) -> Iterator[Any]:
        """Delegate iteration to underlying value."""
        return iter(self._value)

    def __len__(self) -> int:
        return len(self._value)

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f"RawValue({self._value!r})"

    def __bool__(self) -> bool:
        return bool(self._value)


class RawWrapper:
    """Factory implementing ValueWrapper protocol - no origin tracking."""

    def wrap(self, value: Any, origin: Origin) -> RawValue:
        """Wrap value without tracking origin."""
        return RawValue(value)

    def literal(self, value: Any) -> RawValue:
        """Wrap a literal value."""
        return RawValue(value)
