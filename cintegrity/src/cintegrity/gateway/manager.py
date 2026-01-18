"""Tool management - storage, creation, and retrieval.

This module consolidates tool infrastructure:
- ToolSpec: Tool schema (MCP aligned)
- Tool: Runtime tool representation
- MCPToolDefinition: MCP tool metadata DTO
- ToolManager: Storage, lookup, and factory methods
"""

from __future__ import annotations

import inspect
import textwrap
import typing
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from .errors import DuplicateToolError, MCPToolError, ToolNotFoundError

if TYPE_CHECKING:
    from fastmcp import Client

    from .search.base import SearchResult, SearchStrategy


# =============================================================================
# Data Models
# =============================================================================


@dataclass(frozen=True)
class ToolSpec:
    """Tool schema - MCP aligned."""

    name: str
    description: str
    inputSchema: dict[str, Any]
    outputSchema: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema,
        }
        if self.outputSchema is not None:
            result["outputSchema"] = self.outputSchema
        return result


@dataclass(frozen=True)
class Tool:
    """Represents a tool (function call or MCP) that can be executed.

    A tool is either:
    - Function call: A Python function (server=None)
    - MCP: A tool from an MCP server (server=<server_name>)
    """

    spec: ToolSpec
    execute: Callable[[Any], Awaitable[Any]]
    server: str | None = None

    async def call(self, args: Any) -> Any:
        """Execute the tool with the given arguments."""
        return await self.execute(args)

    @property
    def is_function_call(self) -> bool:
        """Returns True if this is a function call (Python function) tool."""
        return self.server is None

    @property
    def is_mcp(self) -> bool:
        """Returns True if this is an MCP server tool."""
        return self.server is not None


@dataclass(frozen=True)
class MCPToolDefinition:
    """MCP tool definition from server (DTO)."""

    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any] | None


# =============================================================================
# Schema Inference
# =============================================================================


def spec_from_callable(
    fn: Callable[[Any], Any],
    *,
    name: str | None = None,
    description: str | None = None,
    inputSchema: dict[str, Any] | None = None,
    outputSchema: dict[str, Any] | None = None,
) -> ToolSpec:
    """Create a ToolSpec from a Python callable."""
    resolved_name = fn.__name__ if name is None else name
    resolved_description = _first_docline(fn) if description is None else description
    resolved_input_schema = _infer_input_schema(fn) if inputSchema is None else inputSchema
    resolved_output_schema = _infer_output_schema(fn) if outputSchema is None else outputSchema
    return ToolSpec(
        name=resolved_name,
        description=resolved_description,
        inputSchema=resolved_input_schema,
        outputSchema=resolved_output_schema,
    )


def _first_docline(fn: Callable[..., Any]) -> str:
    doc = inspect.getdoc(fn) or ""
    doc = textwrap.dedent(doc).strip()
    return doc.splitlines()[0].strip() if doc else ""


def _infer_input_schema(fn: Callable[[Any], Any]) -> dict[str, Any]:
    signature = inspect.signature(fn)
    params = list(signature.parameters.values())
    if len(params) != 1:
        raise TypeError(f"tool '{fn.__name__}' must accept exactly one argument")

    hints = get_type_hints(fn)
    if params[0].name not in hints:
        raise TypeError(f"tool '{fn.__name__}' argument must be type-annotated")

    annotation = hints[params[0].name]
    if not _is_typeddict(annotation):
        raise TypeError(f"tool '{fn.__name__}' argument must be a TypedDict")
    return _typeddict_to_schema(annotation)


def _infer_output_schema(fn: Callable[[Any], Any]) -> dict[str, Any] | None:
    hints = get_type_hints(fn)
    if "return" not in hints:
        return None
    return_type = hints["return"]
    if return_type is None or return_type is type(None):
        return {"type": "null"}
    if _is_typeddict(return_type):
        return _typeddict_to_schema(return_type)
    try:
        return _type_to_schema(return_type)
    except TypeError:
        return None


def _type_to_schema(annotation: Any) -> dict[str, Any]:
    origin = get_origin(annotation)
    args = get_args(annotation)
    required = getattr(typing, "Required", None)
    not_required = getattr(typing, "NotRequired", None)
    if origin is not None and args and origin in (required, not_required):
        return _type_to_schema(args[0])

    if annotation in (Any, object):
        return {}
    if annotation is None or annotation is type(None):
        return {"type": "null"}
    if annotation is str:
        return {"type": "string"}
    if annotation is bool:
        return {"type": "boolean"}
    if annotation in (int, float):
        return {"type": "number"}
    if _is_typeddict(annotation):
        return _typeddict_to_schema(annotation)
    if origin in (list, tuple) and args:
        return {"type": "array", "items": _type_to_schema(args[0])}
    if origin in (dict, Mapping) and len(args) == 2:
        if args[0] is not str:
            raise TypeError("only dict[str, T] is supported")
        return {"type": "object", "additionalProperties": _type_to_schema(args[1])}
    raise TypeError(f"unsupported type: {annotation!r}")


def _is_typeddict(tp: Any) -> bool:
    return isinstance(tp, type) and issubclass(tp, dict) and hasattr(tp, "__annotations__") and hasattr(tp, "__total__")


def _typeddict_to_schema(tp: type) -> dict[str, Any]:
    annotations: dict[str, Any] = dict(get_type_hints(tp, include_extras=True))
    properties = {k: _type_to_schema(v) for k, v in annotations.items()}

    total = bool(getattr(tp, "__total__", True))
    required_wrapper = getattr(typing, "Required", None)
    not_required_wrapper = getattr(typing, "NotRequired", None)

    required_keys: list[str] = []
    for key, ann in annotations.items():
        origin = get_origin(ann)
        if origin is required_wrapper:
            required_keys.append(key)
        elif origin is not_required_wrapper:
            continue
        elif total:
            required_keys.append(key)

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required_keys:
        schema["required"] = sorted(set(required_keys))
    return schema


# =============================================================================
# Local Server Schema Inference
# =============================================================================


def _infer_local_input_schema(fn: Callable[..., Any]) -> dict[str, Any]:
    """Infer JSON Schema from function parameters."""
    sig = inspect.signature(fn)
    hints = get_type_hints(fn)

    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue

        param_type = hints.get(name, Any)
        origin = get_origin(param_type)

        # Extract inner type from Optional[T] (Union[T, None])
        is_optional = False
        if origin is Union:
            args = get_args(param_type)
            if type(None) in args:
                is_optional = True
                non_none = [t for t in args if t is not type(None)]
                if non_none:
                    param_type = non_none[0]

        properties[name] = _type_to_schema(param_type)

        if param.default is inspect.Parameter.empty and not is_optional:
            required.append(name)

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = sorted(required)
    return schema


def _infer_local_output_schema(fn: Callable[..., Any]) -> dict[str, Any] | None:
    """Infer output JSON Schema from return type annotation.

    Uses Pydantic's model_json_schema() for Pydantic models.
    """
    hints = get_type_hints(fn)
    if "return" not in hints:
        return None

    return_type = hints["return"]
    if return_type is None or return_type is type(None):
        return {"type": "null"}

    # Pydantic model - use its built-in schema generation
    if hasattr(return_type, "model_json_schema"):
        return return_type.model_json_schema()

    # TypedDict
    if _is_typeddict(return_type):
        return _typeddict_to_schema(return_type)

    # Basic types (str, int, list, dict, etc.)
    return _type_to_schema(return_type)


# =============================================================================
# MCP Result Parsing
# =============================================================================


def parse_mcp_result(result: Any, output_schema: dict[str, Any] | None = None) -> Any:
    """Parse FastMCP result - unwrap {"result": value} wrapper.

    Returns:
        - Unstructured output (scalars): Plain value (int, str, bool, etc.)
        - Structured output (objects): Dict with semantic field names
    """
    if result.is_error:
        raise MCPToolError(result.content[0].text)

    content = result.structured_content

    # Unwrap FastMCP's {"result": value} wrapper
    if isinstance(content, dict) and "result" in content and len(content) == 1:
        return content["result"]

    return content


def _unwrap_output_schema(schema: dict[str, Any] | None) -> dict[str, Any] | None:
    """Transform FastMCP's wrapped schema to match parse_mcp_result behavior.

    FastMCP wraps scalar returns as {"result": value} with schema:
        {"type": "object", "properties": {"result": {"type": "integer"}}}

    But parse_mcp_result unwraps this to return the scalar directly.
    This function transforms the schema to match runtime behavior.

    Args:
        schema: Output schema from FastMCP

    Returns:
        Unwrapped schema matching actual runtime return value
    """
    if not schema or schema.get("type") != "object":
        return schema

    props = schema.get("properties", {})

    # Check for FastMCP's single-key "result" wrapper pattern
    if len(props) == 1 and "result" in props:
        return props["result"]  # Return inner schema

    # Keep structured outputs with multiple fields as-is
    return schema


# =============================================================================
# Tool Manager
# =============================================================================


class ToolManager:
    """Manages tools - storage, lookup, and factory methods."""

    def __init__(self, search_strategy: SearchStrategy | None = None) -> None:
        self._tools: dict[str, Tool] = {}
        self._search: SearchStrategy | None = search_strategy

    # --- Execution ---

    async def call(self, name: str, args: Any) -> Any:
        """Execute a tool by name."""
        tool = self.get(name)
        return await tool.call(args)

    # --- Storage ---

    def add(self, tool: Tool) -> None:
        """Add a tool to the registry."""
        if tool.spec.name in self._tools:
            raise DuplicateToolError(tool.spec.name)
        self._tools[tool.spec.name] = tool
        self._rebuild_search_index()

    def get(self, name: str) -> Tool:
        """Get a tool by name."""
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool not found: {name}")
        return self._tools[name]

    def has(self, name: str) -> bool:
        """Check if tool exists."""
        return name in self._tools

    def remove(self, name: str) -> Tool:
        """Remove and return a tool."""
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool not found: {name}")
        tool = self._tools.pop(name)
        self._rebuild_search_index()
        return tool

    def tool_names(self) -> frozenset[str]:
        """Return all tool names."""
        return frozenset(self._tools.keys())

    def specs(self) -> list[ToolSpec]:
        """Return all tool specifications."""
        return [t.spec for t in self._tools.values()]

    # --- Query by type ---

    def function_calls(self) -> list[Tool]:
        """Return all function call (Python function) tools."""
        return [t for t in self._tools.values() if t.is_function_call]

    def mcp_tools(self) -> list[Tool]:
        """Return all MCP server tools."""
        return [t for t in self._tools.values() if t.is_mcp]

    def mcp_servers(self) -> set[str]:
        """Return set of all connected MCP server names."""
        return {t.server for t in self._tools.values() if t.server is not None}

    # --- Factory: Function Call Tools ---

    def add_function_call(
        self,
        fn: Callable[[Any], Any],
        *,
        name: str | None = None,
        description: str | None = None,
        inputSchema: dict[str, Any] | None = None,
        outputSchema: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Add a Python function as a function call tool."""
        spec = spec_from_callable(
            fn,
            name=name,
            description=description,
            inputSchema=inputSchema,
            outputSchema=outputSchema,
        )

        async def execute(args: Any) -> Any:
            result = fn(args)
            if inspect.isawaitable(result):
                return await result
            return result

        tool = Tool(spec=spec, execute=execute, server=None)
        self.add(tool)
        return tool.spec

    # --- Factory: MCP Tools ---

    def add_mcp_server(
        self,
        server: str,
        client: Client,
        tools: list[MCPToolDefinition],
    ) -> list[ToolSpec]:
        """Add tools from an MCP server to the registry."""
        specs: list[ToolSpec] = []

        for tool_def in tools:
            # Use mcp_ prefix for all MCP tools
            prefixed_name = f"mcp_{tool_def.name}"

            spec = ToolSpec(
                name=prefixed_name,
                description=tool_def.description,
                inputSchema=tool_def.input_schema,
                outputSchema=_unwrap_output_schema(tool_def.output_schema),
            )

            # Capture loop variables properly
            async def execute(
                args: Any,
                _client: Client = client,
                _name: str = tool_def.name,
                _output_schema: dict[str, Any] | None = tool_def.output_schema,
            ) -> Any:
                result = await _client.call_tool(_name, args)
                return parse_mcp_result(result, _output_schema)

            tool = Tool(spec=spec, execute=execute, server=server)
            self.add(tool)
            specs.append(tool.spec)

        return specs

    def add_local_server(
        self,
        server: str,
        tools: ModuleType | Sequence[Callable[..., Awaitable[Any]]],
    ) -> list[ToolSpec]:
        """Add local async functions as tools under a server namespace.

        Similar to add_mcp_server but for local functions without network.
        Tools get prefixed with mcp_ and are searchable via search_tools.

        Input schemas are inferred from function parameters.
        Output schemas are inferred from return type annotations (Pydantic models).

        Args:
            server: Server name (e.g., "versa")
            tools: Module or list of async functions with type annotations.
                If a module, all public async functions are registered.
        """
        # Extract async functions from module
        if isinstance(tools, ModuleType):
            tool_list = []
            for name in dir(tools):
                if name.startswith("_"):
                    continue
                fn = getattr(tools, name)
                if inspect.iscoroutinefunction(fn):
                    tool_list.append(fn)
        else:
            tool_list = list(tools)

        specs: list[ToolSpec] = []

        for fn in tool_list:
            prefixed_name = f"mcp_{fn.__name__}"
            description = _first_docline(fn)
            input_schema = _infer_local_input_schema(fn)
            output_schema = _infer_local_output_schema(fn)

            spec = ToolSpec(
                name=prefixed_name,
                description=description,
                inputSchema=input_schema,
                outputSchema=output_schema,
            )

            async def execute(args: Any, _fn: Callable[..., Awaitable[Any]] = fn) -> Any:
                return await _fn(**args)

            tool = Tool(spec=spec, execute=execute, server=server)
            self.add(tool)
            specs.append(tool.spec)

        return specs

    def remove_mcp_server(self, server: str) -> list[str]:
        """Remove all tools from an MCP server."""
        to_remove = [name for name, tool in self._tools.items() if tool.server == server]
        for name in to_remove:
            del self._tools[name]
        if to_remove:
            self._rebuild_search_index()
        return to_remove

    # --- Search ---

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Search for tools matching query.

        Uses the configured search strategy (BM25 by default).
        Returns 3-5 most relevant tools with their schemas.
        """
        if self._search is None:
            # Lazy initialization of default search strategy
            from .search.bm25 import BM25SearchStrategy

            self._search = BM25SearchStrategy()
            self._rebuild_search_index()

        return self._search.search(query, limit)

    def _rebuild_search_index(self) -> None:
        """Rebuild search index after tool changes."""
        if self._search is not None:
            specs = {name: tool.spec for name, tool in self._tools.items()}
            self._search.index(specs)

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
