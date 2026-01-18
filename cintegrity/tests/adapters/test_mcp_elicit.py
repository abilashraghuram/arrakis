"""Unit tests for MCP elicitation adapter."""

from unittest.mock import AsyncMock, Mock

import pytest

from cintegrity.adapters.mcp_elicit import MCPElicitAdapter


@pytest.mark.anyio
async def test_adapter_unwraps_accepted():
    """Test that adapter extracts .data from AcceptedElicitation.

    Note: FastMCP's Context.elicit() automatically unwraps scalar types,
    so when response_type=int, the user provides {"value": 42} but
    AcceptedElicitation.data contains just 42 (the unwrapped integer).
    """
    from fastmcp.server.elicitation import AcceptedElicitation

    mock_ctx = Mock()
    # FastMCP unwraps scalar types automatically, so data is just the integer
    mock_ctx.elicit = AsyncMock(return_value=AcceptedElicitation(action="accept", data=42))

    adapter = MCPElicitAdapter(mock_ctx)
    result = await adapter("What is c?", int)

    # Result is the unwrapped scalar value
    assert result == 42
    assert isinstance(result, int)
    mock_ctx.elicit.assert_called_once_with(message="What is c?", response_type=int)


@pytest.mark.anyio
async def test_adapter_raises_on_decline():
    """Test that adapter raises RuntimeError for DeclinedElicitation."""
    from fastmcp.server.elicitation import DeclinedElicitation

    mock_ctx = Mock()
    mock_ctx.elicit = AsyncMock(return_value=DeclinedElicitation(action="decline"))

    adapter = MCPElicitAdapter(mock_ctx)

    with pytest.raises(RuntimeError, match="User declined elicitation"):
        await adapter("What is c?", int)


@pytest.mark.anyio
async def test_adapter_raises_on_cancel():
    """Test that adapter raises RuntimeError for CancelledElicitation."""
    from fastmcp.server.elicitation import CancelledElicitation

    mock_ctx = Mock()
    mock_ctx.elicit = AsyncMock(return_value=CancelledElicitation(action="cancel"))

    adapter = MCPElicitAdapter(mock_ctx)

    with pytest.raises(RuntimeError, match="User cancelled elicitation"):
        await adapter("What is c?", int)
