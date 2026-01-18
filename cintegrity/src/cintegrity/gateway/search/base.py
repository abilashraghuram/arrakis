"""Search strategy protocol and base utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ..manager import ToolSpec


@dataclass
class SearchResult:
    """A tool search result with relevance score."""

    spec: ToolSpec
    score: float


class SearchStrategy(Protocol):
    """Protocol for swappable search strategies.

    Implementations must provide:
    - index(): Build search index from tools
    - search(): Search for tools matching query
    """

    def index(self, tools: dict[str, ToolSpec]) -> None:
        """Build search index from tools. Called when tools change."""
        ...

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Search for tools matching query. Returns 3-5 most relevant."""
        ...


def build_searchable_text(spec: ToolSpec) -> str:
    """Build searchable text from all indexed fields.

    Mirrors Anthropic's tool_search_tool indexed fields:
    - tool names
    - tool descriptions
    - argument names (from inputSchema.properties)
    - argument descriptions (from inputSchema.properties.*.description)
    """
    parts = [spec.name, spec.description or ""]

    # Include argument names and descriptions from inputSchema
    input_schema = spec.inputSchema
    if input_schema and "properties" in input_schema:
        properties: dict[str, Any] = input_schema["properties"]
        for arg_name, arg_def in properties.items():
            parts.append(arg_name)
            if isinstance(arg_def, dict) and "description" in arg_def:
                parts.append(arg_def["description"])

    return " ".join(parts)
