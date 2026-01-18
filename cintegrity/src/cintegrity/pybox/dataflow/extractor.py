"""Origin extraction - extract which tool outputs flow into inputs.

When a tool is called, we need to know which previous tool outputs
contributed to the input (SINK analysis for data flow).
"""

from typing import Any, Protocol

from .base import TrackedValue


class OriginExtractor(Protocol):
    """Protocol for extracting origins from values."""

    def extract(self, value: Any) -> frozenset[str]:
        """Return all call_ids that contributed to this value."""
        ...

    def extract_per_arg(self, kwargs: dict[str, Any]) -> dict[str, frozenset[str]]:
        """Return per-argument origins mapping.

        Args:
            kwargs: Tool arguments

        Returns:
            Dict mapping argument name to set of call_ids that contributed
        """
        ...


def extract_origins(value: Any) -> frozenset[str]:
    """Recursively extract all origin call_ids from a value.

    Traverses nested structures (dict, list, tuple) to find
    all TrackedValue instances and collect their origins.
    """
    origins: set[str] = set()
    _collect(value, origins)
    return frozenset(origins)


def _collect(value: Any, origins: set[str]) -> None:
    if isinstance(value, TrackedValue):
        origins.update(o.call_id for o in value.origins)
        _collect(value.value, origins)
    elif isinstance(value, dict):
        for v in value.values():
            _collect(v, origins)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _collect(v, origins)


class RecursiveOriginExtractor:
    """Default implementation using recursive extraction."""

    def extract(self, value: Any) -> frozenset[str]:
        """Extract all origins from a value (flat)."""
        return extract_origins(value)

    def extract_per_arg(self, kwargs: dict[str, Any]) -> dict[str, frozenset[str]]:
        """Extract origins per argument.

        Returns dict mapping argument name to its origins.
        Only includes arguments that have origins (non-empty).
        """
        result: dict[str, frozenset[str]] = {}
        for arg_name, arg_value in kwargs.items():
            origins = extract_origins(arg_value)
            if origins:  # Only include if there are origins
                result[arg_name] = origins
        return result
