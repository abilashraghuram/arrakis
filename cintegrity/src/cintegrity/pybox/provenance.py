"""Provenance tracking domain models.

All models are frozen dataclasses for immutability.
Includes JSON export for frontend consumption.
"""

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Origin:
    """Where data came from (SOURCE)."""

    call_id: str  # "search#0", "database#1"
    tool_name: str  # "search", "database"
    timestamp: float

    def to_dict(self) -> dict[str, Any]:
        """Export as JSON-serializable dict."""
        return {
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class TaggedValue:
    """Value with provenance metadata."""

    value: Any
    origins: frozenset[Origin]

    @classmethod
    def from_tool(cls, value: Any, origin: Origin) -> "TaggedValue":
        return cls(value=value, origins=frozenset([origin]))

    @classmethod
    def literal(cls, value: Any) -> "TaggedValue":
        return cls(value=value, origins=frozenset())


@dataclass(frozen=True)
class ToolCallRecord:
    """Audit record of a tool call."""

    call_id: str
    tool_name: str
    input_value: Any
    input_origins: dict[str, tuple[str, ...]]  # Per-argument origins: {"arg": ("toolA#0",)}
    output_value: Any
    timestamp: float
    duration_ms: float | None = None  # Execution duration in milliseconds

    def to_dict(self) -> dict[str, Any]:
        """Export as JSON-serializable dict."""
        result = {
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "input_value": _serialize_value(self.input_value),
            "input_origins": {arg: list(origins) for arg, origins in self.input_origins.items()},
            "output_value": _serialize_value(self.output_value),
            "timestamp": self.timestamp,
        }
        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms
        return result

    def all_input_origins(self) -> frozenset[str]:
        """Get all unique origin call_ids across all arguments."""
        all_origins: set[str] = set()
        for origins in self.input_origins.values():
            all_origins.update(origins)
        return frozenset(all_origins)


@dataclass(frozen=True)
class DataFlowEdge:
    """Edge in data flow graph: source_call_id -> sink_call_id."""

    source: str  # call_id of data source (e.g., "search#0")
    sink: str  # call_id of data consumer (e.g., "process#0")


@dataclass(frozen=True)
class ExecutionResult:
    """Result of workflow execution with full audit trail."""

    returned: Any
    calls: tuple[ToolCallRecord, ...]

    def to_dict(self) -> dict[str, Any]:
        """Export as JSON-serializable dict for frontend."""
        return {
            "returned": _serialize_value(_unwrap_value(self.returned)),
            "calls": [call.to_dict() for call in self.calls],
            "data_flow": self._build_data_flow(),
        }

    def to_json(self, indent: int = 2) -> str:
        """Export as JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def _build_data_flow(self) -> dict[str, Any]:
        """Build data flow graph from call records.

        Returns:
            Dict with nodes (tool calls) and edges (data dependencies with argument info)
        """
        nodes = []
        edges = []

        for call in self.calls:
            nodes.append(
                {
                    "id": call.call_id,
                    "tool": call.tool_name,
                    "timestamp": call.timestamp,
                }
            )

            # Create edges with argument granularity
            # Group by source to consolidate which args came from same source
            source_to_args: dict[str, list[str]] = {}
            for arg_name, origins in call.input_origins.items():
                for origin_id in origins:
                    if origin_id not in source_to_args:
                        source_to_args[origin_id] = []
                    source_to_args[origin_id].append(arg_name)

            for source_id, args in source_to_args.items():
                edges.append(
                    {
                        "source": source_id,
                        "sink": call.call_id,
                        "args": sorted(args),  # Which arguments carried data from this source
                    }
                )

        return {"nodes": nodes, "edges": edges}


def _serialize_value(value: Any) -> Any:
    """Recursively serialize value for JSON.

    Handles common types and falls back to string representation.
    """
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _serialize_value(v) for k, v in value.items()}
    if isinstance(value, frozenset):
        return sorted(_serialize_value(v) for v in value)
    # For complex objects, use string representation
    return str(value)


def _unwrap_value(value: Any) -> Any:
    """Unwrap TrackedValue to raw value for serialization."""
    # Check if it has a .value attribute (TrackedValue protocol)
    if hasattr(value, "value") and hasattr(value, "origins"):
        return value.value
    return value
