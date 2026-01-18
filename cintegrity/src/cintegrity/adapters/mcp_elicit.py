"""MCP-specific elicitation adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from fastmcp import Context


class ElicitProtocol(Protocol):
    """Protocol for eliciting user input during workflow execution.

    This abstraction allows different elicitation implementations
    to be used interchangeably without coupling the workflow engine.
    """

    async def __call__(
        self,
        message: str,
        response_type: type | None = None,
    ) -> Any:
        """Request user input with optional type constraint.

        Args:
            message: Human-readable prompt to show the user
            response_type: Expected type (int, str, dict, etc.) for validation

        Returns:
            User-provided value (pre-unwrapped from transport format)

        Raises:
            RuntimeError: If user declines or cancels the request
        """
        ...


class MCPElicitAdapter:
    """Adapter that wraps FastMCP Context.elicit() to match ElicitProtocol.

    Handles MCP-specific response types and unwraps values from
    AcceptedElicitation/DeclinedElicitation/CancelledElicitation.
    """

    def __init__(self, ctx: Context) -> None:
        """Initialize adapter with MCP context.

        Args:
            ctx: FastMCP Context with elicit capability
        """
        self._ctx = ctx

    async def __call__(
        self,
        message: str,
        response_type: type | None = None,
    ) -> Any:
        """Request user input via MCP elicitation protocol.

        Args:
            message: Human-readable prompt for the user
            response_type: Expected type (int, str, dict, etc.)

        Returns:
            User-provided value (FastMCP auto-unwraps scalars)

        Raises:
            RuntimeError: If user declines or cancels
        """
        from fastmcp.server.elicitation import (
            AcceptedElicitation,
            DeclinedElicitation,
        )

        result = await self._ctx.elicit(message=message, response_type=response_type)

        if isinstance(result, AcceptedElicitation):
            return result.data
        elif isinstance(result, DeclinedElicitation):
            raise RuntimeError(f"User declined elicitation: {message}")
        else:  # CancelledElicitation
            raise RuntimeError(f"User cancelled elicitation: {message}")
