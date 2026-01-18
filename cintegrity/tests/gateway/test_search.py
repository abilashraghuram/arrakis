"""Tests for BM25 search strategy."""

from __future__ import annotations

import pytest

from cintegrity.gateway.manager import ToolSpec
from cintegrity.gateway.search.base import SearchResult, build_searchable_text
from cintegrity.gateway.search.bm25 import BM25SearchStrategy

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_tools() -> dict[str, ToolSpec]:
    """Sample tools for testing search."""
    return {
        "mcp_search_appliance": ToolSpec(
            name="mcp_search_appliance",
            description="Search for network appliances by name or location",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Appliance name to search",
                    },
                    "location": {"type": "string", "description": "Branch location"},
                },
                "required": ["name"],
            },
        ),
        "mcp_get_appliance_status": ToolSpec(
            name="mcp_get_appliance_status",
            description="Get the current status of a specific appliance",
            inputSchema={
                "type": "object",
                "properties": {
                    "uuid": {"type": "string", "description": "Appliance UUID"},
                },
                "required": ["uuid"],
            },
        ),
        "mcp_list_users": ToolSpec(
            name="mcp_list_users",
            description="List all users in the organization",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max users to return"},
                },
            },
        ),
        "mcp_get_user": ToolSpec(
            name="mcp_get_user",
            description="Get details for a specific user by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User identifier"},
                },
                "required": ["user_id"],
            },
        ),
        "mcp_network_status": ToolSpec(
            name="mcp_network_status",
            description="Get overall network health and connectivity status",
            inputSchema={"type": "object", "properties": {}},
        ),
        "send_email": ToolSpec(
            name="send_email",
            description="Send an email notification to recipients",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Email recipient"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
        ),
    }


# =============================================================================
# build_searchable_text Tests
# =============================================================================


class TestBuildSearchableText:
    """Tests for build_searchable_text utility."""

    def test_includes_name(self) -> None:
        spec = ToolSpec(name="my_tool", description="", inputSchema={})
        text = build_searchable_text(spec)
        assert "my_tool" in text

    def test_includes_description(self) -> None:
        spec = ToolSpec(name="tool", description="Does something useful", inputSchema={})
        text = build_searchable_text(spec)
        assert "Does something useful" in text

    def test_includes_argument_names(self) -> None:
        spec = ToolSpec(
            name="tool",
            description="",
            inputSchema={
                "type": "object",
                "properties": {"user_id": {"type": "string"}},
            },
        )
        text = build_searchable_text(spec)
        assert "user_id" in text

    def test_includes_argument_descriptions(self) -> None:
        spec = ToolSpec(
            name="tool",
            description="",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string", "description": "The user name"}},
            },
        )
        text = build_searchable_text(spec)
        assert "The user name" in text

    def test_handles_empty_schema(self) -> None:
        spec = ToolSpec(name="tool", description="desc", inputSchema={})
        text = build_searchable_text(spec)
        assert text == "tool desc"

    def test_handles_none_description(self) -> None:
        spec = ToolSpec(name="tool", description=None, inputSchema={})  # type: ignore
        text = build_searchable_text(spec)
        assert "tool" in text


# =============================================================================
# BM25SearchStrategy Tests
# =============================================================================


class TestBM25SearchStrategy:
    """Tests for BM25 search strategy."""

    def test_empty_index_returns_empty(self) -> None:
        strategy = BM25SearchStrategy()
        strategy.index({})
        results = strategy.search("anything")
        assert results == []

    def test_empty_query_returns_empty(self, sample_tools: dict[str, ToolSpec]) -> None:
        strategy = BM25SearchStrategy()
        strategy.index(sample_tools)
        results = strategy.search("")
        assert results == []

    def test_single_word_query_finds_match(self, sample_tools: dict[str, ToolSpec]) -> None:
        strategy = BM25SearchStrategy()
        strategy.index(sample_tools)
        results = strategy.search("appliance")
        assert len(results) >= 1
        names = [r.spec.name for r in results]
        assert "mcp_search_appliance" in names or "mcp_get_appliance_status" in names

    def test_multi_word_query_finds_matches(self, sample_tools: dict[str, ToolSpec]) -> None:
        strategy = BM25SearchStrategy()
        strategy.index(sample_tools)
        results = strategy.search("appliance status")
        assert len(results) >= 1
        names = [r.spec.name for r in results]
        assert "mcp_get_appliance_status" in names

    def test_case_insensitive(self, sample_tools: dict[str, ToolSpec]) -> None:
        strategy = BM25SearchStrategy()
        strategy.index(sample_tools)
        lower = strategy.search("user")
        upper = strategy.search("USER")
        mixed = strategy.search("User")
        assert [r.spec.name for r in lower] == [r.spec.name for r in upper]
        assert [r.spec.name for r in lower] == [r.spec.name for r in mixed]

    def test_respects_limit(self, sample_tools: dict[str, ToolSpec]) -> None:
        strategy = BM25SearchStrategy()
        strategy.index(sample_tools)
        results = strategy.search("network", limit=2)
        assert len(results) <= 2

    def test_results_sorted_by_score_descending(self, sample_tools: dict[str, ToolSpec]) -> None:
        strategy = BM25SearchStrategy()
        strategy.index(sample_tools)
        results = strategy.search("appliance")
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_by_argument_name(self, sample_tools: dict[str, ToolSpec]) -> None:
        strategy = BM25SearchStrategy()
        strategy.index(sample_tools)
        results = strategy.search("uuid")
        assert len(results) >= 1
        assert results[0].spec.name == "mcp_get_appliance_status"

    def test_search_by_argument_description(self, sample_tools: dict[str, ToolSpec]) -> None:
        strategy = BM25SearchStrategy()
        strategy.index(sample_tools)
        results = strategy.search("recipient")
        assert len(results) >= 1
        assert results[0].spec.name == "send_email"

    def test_no_match_returns_empty(self, sample_tools: dict[str, ToolSpec]) -> None:
        strategy = BM25SearchStrategy()
        strategy.index(sample_tools)
        results = strategy.search("xyznonexistent123")
        assert results == []

    def test_reindex_updates_search(self) -> None:
        strategy = BM25SearchStrategy()
        tools1 = {"tool_a": ToolSpec(name="tool_a", description="Alpha tool", inputSchema={})}
        strategy.index(tools1)

        results = strategy.search("alpha")
        assert len(results) == 1

        tools2 = {"tool_b": ToolSpec(name="tool_b", description="Beta tool", inputSchema={})}
        strategy.index(tools2)

        results = strategy.search("alpha")
        assert len(results) == 0

        results = strategy.search("beta")
        assert len(results) == 1

    def test_returns_search_result_objects(self, sample_tools: dict[str, ToolSpec]) -> None:
        strategy = BM25SearchStrategy()
        strategy.index(sample_tools)
        results = strategy.search("user")
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(isinstance(r.spec, ToolSpec) for r in results)
        assert all(isinstance(r.score, float) for r in results)

    def test_ranks_combined_term_matches_higher(self, sample_tools: dict[str, ToolSpec]) -> None:
        strategy = BM25SearchStrategy()
        strategy.index(sample_tools)
        results = strategy.search("appliance status")
        assert results[0].spec.name == "mcp_get_appliance_status"

    def test_finds_by_semantic_terms(self, sample_tools: dict[str, ToolSpec]) -> None:
        strategy = BM25SearchStrategy()
        strategy.index(sample_tools)
        results = strategy.search("network health")
        assert len(results) >= 1
        assert results[0].spec.name == "mcp_network_status"


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Edge case tests for BM25 search."""

    def test_special_characters_in_query(self, sample_tools: dict[str, ToolSpec]) -> None:
        strategy = BM25SearchStrategy()
        strategy.index(sample_tools)
        results = strategy.search("user@email.com")
        assert isinstance(results, list)

    def test_very_long_query(self, sample_tools: dict[str, ToolSpec]) -> None:
        strategy = BM25SearchStrategy()
        strategy.index(sample_tools)
        long_query = "search for appliance " * 100
        results = strategy.search(long_query)
        assert isinstance(results, list)

    def test_single_tool_index(self) -> None:
        strategy = BM25SearchStrategy()
        tools = {"only_tool": ToolSpec(name="only_tool", description="The only tool", inputSchema={})}
        strategy.index(tools)
        results = strategy.search("only")
        assert len(results) == 1
        assert results[0].spec.name == "only_tool"

    def test_tool_with_empty_description(self) -> None:
        strategy = BM25SearchStrategy()
        tools = {"tool": ToolSpec(name="findme", description="", inputSchema={})}
        strategy.index(tools)
        results = strategy.search("findme")
        assert len(results) == 1

    def test_tool_with_complex_schema(self) -> None:
        strategy = BM25SearchStrategy()
        tools = {
            "complex_tool": ToolSpec(
                name="complex_tool",
                description="A complex tool",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "nested": {
                            "type": "object",
                            "properties": {"deep": {"type": "string"}},
                        },
                        "searchable_arg": {
                            "type": "string",
                            "description": "Find me by this description",
                        },
                    },
                },
            )
        }
        strategy.index(tools)
        results = strategy.search("Find me")
        assert len(results) == 1
