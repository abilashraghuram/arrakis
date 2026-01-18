"""Tests for search_tools gateway tool."""

from __future__ import annotations

from typing import Any

import pytest

from cintegrity.gateway.manager import Tool, ToolManager, ToolSpec
from cintegrity.gateway.tools.search_tools import search_tools

# =============================================================================
# Test Fixtures
# =============================================================================


def make_tool(name: str, description: str, input_schema: dict[str, Any], server: str | None = None) -> Tool:
    """Create a Tool for testing."""
    spec = ToolSpec(name=name, description=description, inputSchema=input_schema)

    async def execute(args: Any) -> Any:
        return {"result": "ok"}

    return Tool(spec=spec, execute=execute, server=server)


@pytest.fixture
def manager_with_tools() -> ToolManager:
    """Create a ToolManager with sample tools."""
    manager = ToolManager()

    # MCP tools (with server)
    manager.add(
        make_tool(
            name="mcp_search_appliance",
            description="Search for network appliances",
            input_schema={
                "type": "object",
                "properties": {"name": {"type": "string", "description": "Appliance name"}},
                "required": ["name"],
            },
            server="versa_conductor",
        )
    )

    manager.add(
        make_tool(
            name="mcp_get_status",
            description="Get appliance status by UUID",
            input_schema={
                "type": "object",
                "properties": {"uuid": {"type": "string", "description": "Appliance UUID"}},
                "required": ["uuid"],
            },
            server="versa_conductor",
        )
    )

    # Function call tool (no server)
    manager.add(
        make_tool(
            name="send_email",
            description="Send email notification",
            input_schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                },
                "required": ["to", "subject"],
            },
            server=None,
        )
    )

    return manager


# =============================================================================
# search_tools Tests
# =============================================================================


class TestSearchTools:
    """Tests for search_tools gateway function."""

    @pytest.mark.anyio
    async def test_returns_tools_list(self, manager_with_tools: ToolManager) -> None:
        result = await search_tools(manager_with_tools, query="appliance")
        assert "tools" in result
        assert isinstance(result["tools"], list)

    @pytest.mark.anyio
    async def test_includes_name(self, manager_with_tools: ToolManager) -> None:
        result = await search_tools(manager_with_tools, query="appliance")
        assert len(result["tools"]) >= 1
        assert "name" in result["tools"][0]

    @pytest.mark.anyio
    async def test_includes_description(self, manager_with_tools: ToolManager) -> None:
        result = await search_tools(manager_with_tools, query="appliance")
        tool = result["tools"][0]
        assert "description" in tool
        assert isinstance(tool["description"], str)

    @pytest.mark.anyio
    async def test_includes_input_schema(self, manager_with_tools: ToolManager) -> None:
        result = await search_tools(manager_with_tools, query="appliance")
        tool = result["tools"][0]
        assert "inputSchema" in tool
        assert isinstance(tool["inputSchema"], dict)

    @pytest.mark.anyio
    async def test_includes_import_path(self, manager_with_tools: ToolManager) -> None:
        result = await search_tools(manager_with_tools, query="appliance")
        tool = result["tools"][0]
        assert "import_path" in tool
        assert tool["import_path"].startswith("from cintegrity.")

    @pytest.mark.anyio
    async def test_mcp_tool_import_path_format(self, manager_with_tools: ToolManager) -> None:
        result = await search_tools(manager_with_tools, query="search appliance")
        tools = [t for t in result["tools"] if t["name"] == "mcp_search_appliance"]
        assert len(tools) == 1
        assert tools[0]["import_path"] == "from cintegrity.mcp_tools.versa_conductor import mcp_search_appliance"

    @pytest.mark.anyio
    async def test_function_call_import_path_format(self, manager_with_tools: ToolManager) -> None:
        result = await search_tools(manager_with_tools, query="email")
        tools = [t for t in result["tools"] if t["name"] == "send_email"]
        assert len(tools) == 1
        assert tools[0]["import_path"] == "from cintegrity.function_calls import send_email"

    @pytest.mark.anyio
    async def test_empty_query_returns_empty(self, manager_with_tools: ToolManager) -> None:
        result = await search_tools(manager_with_tools, query="")
        assert result["tools"] == []

    @pytest.mark.anyio
    async def test_no_match_returns_empty(self, manager_with_tools: ToolManager) -> None:
        result = await search_tools(manager_with_tools, query="xyznonexistent123")
        assert result["tools"] == []

    @pytest.mark.anyio
    async def test_max_5_results(self, manager_with_tools: ToolManager) -> None:
        # Add more tools to exceed 5
        for i in range(10):
            manager_with_tools.add(
                make_tool(
                    name=f"test_tool_{i}",
                    description=f"Test tool number {i} for testing",
                    input_schema={},
                    server=None,
                )
            )

        result = await search_tools(manager_with_tools, query="test tool")
        assert len(result["tools"]) <= 5

    @pytest.mark.anyio
    async def test_schema_includes_required_fields(self, manager_with_tools: ToolManager) -> None:
        result = await search_tools(manager_with_tools, query="search appliance")
        tools = [t for t in result["tools"] if t["name"] == "mcp_search_appliance"]
        assert len(tools) == 1
        schema = tools[0]["inputSchema"]
        assert "properties" in schema
        assert "required" in schema
        assert "name" in schema["required"]


class TestSearchToolsIntegration:
    """Integration tests for search_tools with ToolManager."""

    @pytest.mark.anyio
    async def test_multi_word_query_finds_relevant_tools(self, manager_with_tools: ToolManager) -> None:
        result = await search_tools(manager_with_tools, query="appliance status")
        # Should find mcp_get_status which has "status" in name
        names = [t["name"] for t in result["tools"]]
        assert "mcp_get_status" in names

    @pytest.mark.anyio
    async def test_search_by_argument_name(self, manager_with_tools: ToolManager) -> None:
        result = await search_tools(manager_with_tools, query="uuid")
        names = [t["name"] for t in result["tools"]]
        assert "mcp_get_status" in names

    @pytest.mark.anyio
    async def test_results_have_complete_schema_for_workflow(self, manager_with_tools: ToolManager) -> None:
        """Verify results contain everything needed to write execute_workflow code."""
        result = await search_tools(manager_with_tools, query="appliance")

        for tool in result["tools"]:
            # Must have import path for imports
            assert "import_path" in tool
            assert "from cintegrity" in tool["import_path"]

            # Must have name for function call
            assert "name" in tool

            # Must have inputSchema to know arguments
            assert "inputSchema" in tool

            # If schema has properties, they should be accessible
            if "properties" in tool["inputSchema"]:
                for prop_name, prop_def in tool["inputSchema"]["properties"].items():
                    assert isinstance(prop_name, str)
                    assert "type" in prop_def
