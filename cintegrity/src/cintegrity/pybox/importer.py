"""AST-based import parsing for workflow code."""

from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass
class ParsedImport:
    """A parsed import statement."""

    tool_name: str  # The imported name (e.g., "mcp_search_appliance")
    module_path: str  # Full module path (e.g., "cintegrity.mcp_tools.versa_conductor")
    alias: str | None  # Import alias if any (e.g., "search" from "import ... as search")


class WorkflowImportError(Exception):
    """Raised when import parsing fails."""

    pass


def parse_imports(code: str) -> tuple[list[ParsedImport], str]:
    """Parse import statements and return imports + remaining code.

    Args:
        code: Python code with import statements

    Returns:
        Tuple of (parsed imports, code without imports)

    Raises:
        WorkflowImportError: If invalid import found
    """
    tree = ast.parse(code)
    imports: list[ParsedImport] = []
    other_nodes: list[ast.stmt] = []

    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            # Handle: from cintegrity.mcp_tools.server import tool1, tool2
            if node.module and node.module.startswith("cintegrity."):
                for alias in node.names:
                    imports.append(
                        ParsedImport(
                            tool_name=alias.name,
                            module_path=node.module,
                            alias=alias.asname,
                        )
                    )
            else:
                raise WorkflowImportError(f"Only imports from 'cintegrity.*' allowed, got: {node.module}")
        elif isinstance(node, ast.Import):
            raise WorkflowImportError("Use 'from cintegrity.* import tool' syntax, not 'import ...'")
        else:
            other_nodes.append(node)

    # Reconstruct code without imports
    new_tree = ast.Module(body=other_nodes, type_ignores=[])
    code_without_imports = ast.unparse(new_tree)

    return imports, code_without_imports


def validate_imports(
    imports: list[ParsedImport],
    available_tools: set[str],
) -> None:
    """Validate that all imported tools exist.

    Args:
        imports: Parsed imports
        available_tools: Set of available tool names from bridge

    Raises:
        WorkflowImportError: If tool doesn't exist
    """
    for imp in imports:
        if imp.tool_name not in available_tools:
            raise WorkflowImportError(f"Tool '{imp.tool_name}' not found. Available tools: {sorted(available_tools)}")
