"""Tool bridge protocol for connecting external tool sources to the provenance engine."""

import asyncio
from collections.abc import Callable
from typing import Any, Protocol


class ToolBridge(Protocol):
    """Protocol for bridging external tool sources to the provenance engine.

    Implementations provide tools from various sources (remote servers, local functions, etc.).
    """

    def list_tools(self) -> list[str]:
        """List available tool names."""
        ...

    async def call(self, tool_name: str, **kwargs: Any) -> Any:
        """Execute a tool and return its raw result."""
        ...


class DirectToolBridge:
    """Bridge for Python callables (functions, methods).

    Use when tools are defined directly in Python.
    """

    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, fn: Callable[..., Any]) -> None:
        """Register a tool function."""
        self._tools[name] = fn

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    async def call(self, tool_name: str, **kwargs: Any) -> Any:
        fn = self._tools[tool_name]
        result = fn(**kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result
