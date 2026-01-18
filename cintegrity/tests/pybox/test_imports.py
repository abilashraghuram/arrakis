"""Tests for workflow import parsing."""

import pytest

from cintegrity.pybox.importer import (
    ParsedImport,
    WorkflowImportError,
    parse_imports,
    validate_imports,
)


class TestParseImports:
    """Tests for parse_imports function."""

    def test_single_import(self) -> None:
        """Parse single import statement."""
        code = """
from cintegrity.mcp_tools.versa import mcp_search

async def workflow():
    result = await mcp_search(name="x")
    return result
"""
        imports, remaining = parse_imports(code)

        assert len(imports) == 1
        assert imports[0].tool_name == "mcp_search"
        assert imports[0].module_path == "cintegrity.mcp_tools.versa"
        assert imports[0].alias is None
        assert "from cintegrity" not in remaining
        assert "await mcp_search" in remaining

    def test_multiple_imports_same_line(self) -> None:
        """Parse multiple imports from same module."""
        code = """
from cintegrity.mcp_tools.versa import mcp_search, mcp_status

async def workflow():
    result = await mcp_search(name="x")
    return result
"""
        imports, _ = parse_imports(code)

        assert len(imports) == 2
        names = {i.tool_name for i in imports}
        assert names == {"mcp_search", "mcp_status"}

    def test_multiple_imports_separate_lines(self) -> None:
        """Parse multiple import statements."""
        code = """
from cintegrity.mcp_tools.versa import mcp_search
from cintegrity.function_calls import send_email

async def workflow():
    result = await mcp_search(name="x")
    return result
"""
        imports, _ = parse_imports(code)

        assert len(imports) == 2
        names = {i.tool_name for i in imports}
        assert names == {"mcp_search", "send_email"}

    def test_import_with_alias(self) -> None:
        """Parse import with alias."""
        code = """
from cintegrity.mcp_tools.versa import mcp_search_appliance as search

async def workflow():
    result = await search(name="x")
    return result
"""
        imports, _ = parse_imports(code)

        assert len(imports) == 1
        assert imports[0].tool_name == "mcp_search_appliance"
        assert imports[0].alias == "search"

    def test_invalid_import_module(self) -> None:
        """Reject imports from non-cintegrity modules."""
        code = """
from os import path

async def workflow():
    result = path.join("a", "b")
    return result
"""
        with pytest.raises(WorkflowImportError, match="Only imports from 'cintegrity.*'"):
            parse_imports(code)

    def test_plain_import_rejected(self) -> None:
        """Reject plain import statements."""
        code = """
import cintegrity.mcp_tools.versa
"""
        with pytest.raises(WorkflowImportError, match="Use 'from cintegrity"):
            parse_imports(code)

    def test_code_without_imports_preserved(self) -> None:
        """Code without imports remains intact."""
        code = """
from cintegrity.mcp_tools.versa import mcp_search

async def workflow():
    x = 1
    y = 2
    result = await mcp_search(query=str(x + y))
    return result
"""
        _, remaining = parse_imports(code)

        assert "x = 1" in remaining
        assert "y = 2" in remaining
        assert "await mcp_search" in remaining
        assert "return result" in remaining


class TestValidateImports:
    """Tests for validate_imports function."""

    def test_valid_imports(self) -> None:
        """Validate imports that exist."""
        imports = [
            ParsedImport("mcp_search", "cintegrity.mcp_tools.versa", None),
            ParsedImport("send_email", "cintegrity.function_calls", None),
        ]
        available = {"mcp_search", "send_email", "other_tool"}

        # Should not raise
        validate_imports(imports, available)

    def test_unknown_tool_raises(self) -> None:
        """Raise error for unknown tool."""
        imports = [
            ParsedImport("nonexistent_tool", "cintegrity.mcp_tools.versa", None),
        ]
        available = {"mcp_search", "send_email"}

        with pytest.raises(WorkflowImportError, match="not found"):
            validate_imports(imports, available)

    def test_error_shows_available_tools(self) -> None:
        """Error message shows available tools."""
        imports = [
            ParsedImport("bad_tool", "cintegrity.mcp_tools.versa", None),
        ]
        available = {"tool_a", "tool_b"}

        with pytest.raises(WorkflowImportError, match="tool_a"):
            validate_imports(imports, available)


@pytest.mark.anyio
async def test_workflow_with_imports() -> None:
    """End-to-end test: workflow with imports executes correctly."""
    from cintegrity.pybox.bridge import DirectToolBridge
    from cintegrity.pybox.engine import WorkflowEngine

    bridge = DirectToolBridge()

    async def search(query: str) -> dict:
        return {"data": [{"id": 1, "name": query}]}

    bridge.register("mcp_search", search)
    engine = WorkflowEngine(bridge=bridge)

    code = """
from cintegrity.mcp_tools.versa import mcp_search

async def workflow():
    result = await mcp_search(query="test")
    return result
"""

    execution = await engine.execute(code)

    assert len(execution.calls) == 1
    assert execution.calls[0].tool_name == "mcp_search"
    # Check return value
    assert execution.returned is not None


@pytest.mark.anyio
async def test_only_imported_tools_available() -> None:
    """Tools not imported should not be accessible."""
    from cintegrity.pybox.bridge import DirectToolBridge
    from cintegrity.pybox.engine import WorkflowEngine

    bridge = DirectToolBridge()

    async def tool_a() -> str:
        return "a"

    async def tool_b() -> str:
        return "b"

    bridge.register("tool_a", tool_a)
    bridge.register("tool_b", tool_b)
    engine = WorkflowEngine(bridge=bridge)

    # Only import tool_a, try to use tool_b
    code = """
from cintegrity.function_calls import tool_a

async def workflow():
    result = await tool_b()
    return result
"""

    with pytest.raises(NameError, match="tool_b"):
        await engine.execute(code)


@pytest.mark.anyio
async def test_import_alias_works() -> None:
    """Import aliases work correctly."""
    from cintegrity.pybox.bridge import DirectToolBridge
    from cintegrity.pybox.engine import WorkflowEngine

    bridge = DirectToolBridge()

    async def very_long_tool_name(x: int) -> int:
        return x * 2

    bridge.register("very_long_tool_name", very_long_tool_name)
    engine = WorkflowEngine(bridge=bridge)

    code = """
from cintegrity.function_calls import very_long_tool_name as short

async def workflow():
    result = await short(x=5)
    return result
"""

    execution = await engine.execute(code)

    assert len(execution.calls) == 1
    assert execution.calls[0].tool_name == "very_long_tool_name"


@pytest.mark.anyio
async def test_return_statement_works() -> None:
    """Return statement returns value directly."""
    from cintegrity.pybox.bridge import DirectToolBridge
    from cintegrity.pybox.engine import WorkflowEngine

    bridge = DirectToolBridge()

    async def get_value() -> int:
        return 42

    bridge.register("get_value", get_value)
    engine = WorkflowEngine(bridge=bridge)

    code = """
from cintegrity.function_calls import get_value

async def workflow():
    val = await get_value()
    return {"result": val}
"""

    execution = await engine.execute(code)

    # The returned value should have the dict structure
    returned = execution.returned
    # Unwrap if it's a TrackedValue
    if hasattr(returned, "value"):
        returned = returned.value
    assert returned == {"result": 42}


@pytest.mark.anyio
async def test_invalid_import_fails_early() -> None:
    """Invalid imports fail with clear error."""
    from cintegrity.pybox.bridge import DirectToolBridge
    from cintegrity.pybox.engine import WorkflowEngine

    bridge = DirectToolBridge()

    async def real_tool() -> str:
        return "real"

    bridge.register("real_tool", real_tool)
    engine = WorkflowEngine(bridge=bridge)

    code = """
from cintegrity.function_calls import fake_tool

async def workflow():
    result = await fake_tool()
    return result
"""

    with pytest.raises(WorkflowImportError, match="fake_tool.*not found"):
        await engine.execute(code)


@pytest.mark.anyio
async def test_provenance_tracking_with_imports() -> None:
    """Provenance tracking works with import-based workflow."""
    from cintegrity.pybox.bridge import DirectToolBridge
    from cintegrity.pybox.engine import WorkflowEngine

    bridge = DirectToolBridge()

    async def search(query: str) -> dict:
        return {"data": [{"id": 1, "name": query}]}

    async def process(item: dict) -> dict:
        return {"processed": item["id"]}

    bridge.register("search", search)
    bridge.register("process", process)
    engine = WorkflowEngine(bridge=bridge)

    code = """
from cintegrity.mcp_tools.server import search, process

async def workflow():
    search_result = await search(query="test")
    item = search_result["data"][0]
    result = await process(item=item)
    return result
"""

    execution = await engine.execute(code)

    assert len(execution.calls) == 2
    # Check provenance - process should have origins from search
    assert "search#0" in execution.calls[1].all_input_origins()
