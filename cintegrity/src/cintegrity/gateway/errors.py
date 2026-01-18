"""Gateway errors."""

from __future__ import annotations


class ToolExecutionError(RuntimeError):
    def __init__(self, *, tool_name: str, cause: BaseException):
        self.tool_name = tool_name
        self.cause = cause
        super().__init__(f"tool '{tool_name}': {type(cause).__name__}: {cause}")


class WorkflowError(RuntimeError):
    def __init__(self, *, run_id: str, stage: str, cause: BaseException):
        self.run_id = run_id
        self.stage = stage
        self.cause = cause
        super().__init__(f"{type(cause).__name__}: {cause}")


class ToolNotFoundError(Exception):
    """Raised when a tool is not found."""

    pass


class MCPToolError(RuntimeError):
    """Raised when an MCP tool returns isError=True.

    Framework-agnostic error that adapters convert to framework-specific exceptions:
    - LangChain: ToolException
    - Google ADK: passes through or returns error dict
    """

    pass


class DuplicateToolError(ValueError):
    """Raised when trying to add a tool with a name that already exists."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Tool already exists: {name}")
