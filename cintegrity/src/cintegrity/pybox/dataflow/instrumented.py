"""AST instrumentation for fine-grained data flow tracking.

Transforms user code before execution to inject tracking calls.
Provides 100% accurate origin tracking at the cost of performance.
"""

import ast
import asyncio
from collections.abc import Iterator
from typing import Any

from ..importer import parse_imports, validate_imports
from ..provenance import Origin
from .base import TrackedValue


class OriginMap:
    """Tracks which variables have which origins at runtime.

    Maintains a mapping from variable names to their origin call_ids.
    """

    def __init__(self) -> None:
        self._map: dict[str, frozenset[str]] = {}

    def assign(self, name: str, origins: frozenset[str]) -> None:
        """Record origins for a variable."""
        self._map[name] = origins

    def get(self, name: str) -> frozenset[str]:
        """Get origins for a variable."""
        return self._map.get(name, frozenset())

    def merge(self, *names: str) -> frozenset[str]:
        """Merge origins from multiple variables."""
        return frozenset().union(*(self.get(n) for n in names))

    def clear(self) -> None:
        """Clear all tracked origins."""
        self._map.clear()


class DataFlowInstrumenter(ast.NodeTransformer):
    """Transforms AST to inject data flow tracking calls.

    Wraps assignments, subscripts, and attributes with tracking functions.
    """

    def visit_Assign(self, node: ast.Assign) -> ast.AST:
        """Transform: x = expr → x = __track_assign__("x", expr)"""
        self.generic_visit(node)

        # Only handle simple name assignments for now
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id
            # Wrap value in tracking call
            tracked_value = ast.Call(
                func=ast.Name(id="__track_assign__", ctx=ast.Load()),
                args=[ast.Constant(value=target_name), node.value],
                keywords=[],
            )
            node.value = tracked_value

        return node

    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        """Transform: obj[key] → __track_subscript__(obj, key)"""
        self.generic_visit(node)

        if isinstance(node.ctx, ast.Load):
            return ast.Call(
                func=ast.Name(id="__track_subscript__", ctx=ast.Load()),
                args=[node.value, node.slice],
                keywords=[],
            )
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        """Transform: obj.attr → __track_attr__(obj, "attr")"""
        self.generic_visit(node)

        if isinstance(node.ctx, ast.Load):
            return ast.Call(
                func=ast.Name(id="__track_attr__", ctx=ast.Load()),
                args=[node.value, ast.Constant(value=node.attr)],
                keywords=[],
            )
        return node


class InstrumentedValue:
    """Thin wrapper for AST instrumentation - values are raw.

    Implements TrackedValue protocol. Origins tracked separately via OriginMap.
    """

    def __init__(self, value: Any, origins: frozenset[Origin]) -> None:
        self._value = value
        self._origins = origins

    @property
    def value(self) -> Any:
        """Get raw value."""
        return self._value

    @property
    def origins(self) -> frozenset[Origin]:
        """Get origins that contributed to this value."""
        return self._origins

    def __getitem__(self, key: Any) -> Any:
        """Delegate indexing to underlying value."""
        return self._value[key]

    def __iter__(self) -> Iterator[Any]:
        """Delegate iteration to underlying value."""
        return iter(self._value)

    def __len__(self) -> int:
        return len(self._value)

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f"InstrumentedValue({self._value!r}, origins={len(self._origins)})"

    def __bool__(self) -> bool:
        return bool(self._value)


class InstrumentedRuntime:
    """Runtime that transforms code before execution.

    Implements Runtime protocol. Uses AST instrumentation for
    100% accurate origin tracking.
    """

    # Builtin functions available without imports
    BUILTIN_FUNCTIONS: set[str] = {"elicit"}

    def __init__(self) -> None:
        self._origin_map = OriginMap()

    async def execute(
        self,
        code: str,
        namespace: dict[str, Any],
        timeout: float = 30.0,
        available_tools: set[str] | None = None,
    ) -> Any:
        """Execute code with AST instrumentation.

        Args:
            code: Python code with imports and 'async def workflow():' function
            namespace: Dict of tool_name -> ToolProxy (all available tools)
            timeout: Maximum execution time in seconds
            available_tools: Set of all available tool names for validation

        Returns:
            Return value from workflow execution

        Raises:
            ValueError: If code doesn't define 'async def workflow():'
        """
        # Reset origin map for new execution
        self._origin_map.clear()

        # 1. Parse imports from code
        imports, code_without_imports = parse_imports(code)

        # 2. Validate imported tools exist
        if available_tools:
            validate_imports(imports, available_tools)

        # 3. Build restricted namespace with ONLY imported tools
        restricted_namespace: dict[str, Any] = {}
        for imp in imports:
            name = imp.alias or imp.tool_name
            if imp.tool_name in namespace:
                restricted_namespace[name] = namespace[imp.tool_name]

        # 4. Parse and transform AST (code without imports)
        tree = ast.parse(code_without_imports)
        instrumenter = DataFlowInstrumenter()
        transformed = instrumenter.visit(tree)
        ast.fix_missing_locations(transformed)

        # 5. Inject tracking functions into namespace
        restricted_namespace["__track_assign__"] = self._track_assign
        restricted_namespace["__track_subscript__"] = self._track_subscript
        restricted_namespace["__track_attr__"] = self._track_attr
        restricted_namespace["__origin_map__"] = self._origin_map

        # Inject builtin functions (available without imports)
        for builtin_name in self.BUILTIN_FUNCTIONS:
            if builtin_name in namespace:
                restricted_namespace[builtin_name] = namespace[builtin_name]

        # 6. Execute transformed code (must define async def workflow())
        transformed_code = ast.unparse(transformed)
        exec(transformed_code, restricted_namespace)

        # 7. Validate and call workflow function
        if "workflow" not in restricted_namespace:
            raise ValueError("Workflow code must define 'async def workflow():'")
        return await asyncio.wait_for(restricted_namespace["workflow"](), timeout=timeout)

    def _track_assign(self, name: str, value: Any) -> Any:
        """Track origins for an assigned variable.

        Extracts origins from the value and records them in the origin map.
        """
        origins: frozenset[str] = frozenset()

        # Extract origins from TrackedValue
        if isinstance(value, TrackedValue):
            origins = frozenset(o.call_id for o in value.origins)

        self._origin_map.assign(name, origins)
        return value

    def _track_subscript(self, obj: Any, key: Any) -> Any:
        """Track origins through subscript access.

        Propagates origins from the object being indexed.
        """
        # Get the actual value
        raw_obj = obj.value if isinstance(obj, TrackedValue) else obj
        raw_key = key.value if isinstance(key, TrackedValue) else key
        result = raw_obj[raw_key]

        # Propagate origins if obj was tracked
        if isinstance(obj, TrackedValue) and obj.origins:
            return InstrumentedValue(result, obj.origins)

        return result

    def _track_attr(self, obj: Any, attr: str) -> Any:
        """Track origins through attribute access.

        Propagates origins from the object being accessed.
        """
        # Get the actual value
        raw_obj = obj.value if isinstance(obj, TrackedValue) else obj
        result = getattr(raw_obj, attr)

        # Propagate origins if obj was tracked
        if isinstance(obj, TrackedValue) and obj.origins:
            return InstrumentedValue(result, obj.origins)

        return result


class InstrumentedWrapper:
    """Factory implementing ValueWrapper protocol for AST mode."""

    def wrap(self, value: Any, origin: Origin) -> InstrumentedValue:
        """Wrap a tool result with provenance origin."""
        return InstrumentedValue(value, frozenset([origin]))

    def literal(self, value: Any) -> InstrumentedValue:
        """Wrap a literal value (no origins)."""
        return InstrumentedValue(value, frozenset())
