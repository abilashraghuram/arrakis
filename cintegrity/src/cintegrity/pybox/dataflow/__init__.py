"""Data flow tracking strategies.

Provides swappable implementations for provenance/origin tracking.
"""

from enum import Enum, auto


class TrackingStrategy(Enum):
    """Data flow tracking strategy selection."""

    TRANSPARENT = auto()  # Dunder methods preserve origins (~2-5% overhead)
    INSTRUMENTED = auto()  # AST transformation (~5-30x overhead, 100% accurate)
    NONE = auto()  # No origin tracking
