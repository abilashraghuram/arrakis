"""All tools search strategy - returns all tools regardless of query."""

from __future__ import annotations

from ..manager import ToolSpec
from .base import SearchResult


class AllToolsSearchStrategy:
    """Search strategy that returns all tools regardless of query.

    Useful for small tool sets or debugging where you want the agent
    to see all available tools without filtering.
    """

    def __init__(self) -> None:
        """Initialize all-tools strategy."""
        self._tools: dict[str, ToolSpec] = {}

    def index(self, tools: dict[str, ToolSpec]) -> None:
        """Store tools for later retrieval."""
        self._tools = tools

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Return all tools with neutral score.

        Args:
            query: Ignored - returns all tools
            limit: Maximum number of tools to return

        Returns:
            All tools (up to limit) with score 1.0
        """
        results = [SearchResult(spec=spec, score=1.0) for spec in self._tools.values()]
        return results[:limit]
