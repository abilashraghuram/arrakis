"""Runtime protocol.

Defines the interface for code execution environments.
"""

from typing import Any, Protocol


class Runtime(Protocol):
    """Protocol for code execution environments.

    Implementations:
    - LocalRuntime: exec() in current process (dev/test)
    - FirecrackerRuntime: microVM isolation (production)
    - SeatbeltRuntime: macOS sandbox (production)
    """

    async def execute(
        self,
        code: str,
        namespace: dict[str, Any],
        timeout: float = 30.0,
        available_tools: set[str] | None = None,
    ) -> Any:
        """Execute workflow code and return result.

        Args:
            code: Python code with imports and return statement
            namespace: Dict of tool_name -> ToolProxy (all available tools)
            timeout: Maximum execution time in seconds
            available_tools: Set of all available tool names for validation

        Returns:
            Return value from workflow execution
        """
        ...
