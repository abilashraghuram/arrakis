"""Tests for elicitation support in workflow execution."""

from typing import Any

import pytest

from cintegrity.pybox.engine import WorkflowEngine


@pytest.mark.anyio
async def test_elicit_provides_user_value():
    """Test that elicit() pauses and receives user input."""

    # Mock elicit function that returns the actual value
    async def mock_elicit(message: str, response_type=None):
        assert "parameter 'c'" in message
        return 42  # Simulated user input (already unwrapped)

    # Mock bridge with no tools
    class MockBridge:
        def list_tools(self):
            return []

        async def call(self, tool_name: str, **kwargs: Any) -> Any:
            pass

    bridge = MockBridge()
    engine = WorkflowEngine(bridge=bridge)

    code = """
async def workflow():
    c = await elicit(message="Value for parameter 'c'?", response_type=int)
    return {"c": c}
"""

    result = await engine.execute(code, elicit_fn=mock_elicit)
    assert result.returned == {"c": 42}


@pytest.mark.anyio
async def test_elicit_declined_raises_error():
    """Test that declined elicitation raises RuntimeError in workflow."""

    async def mock_elicit_declined(message: str, response_type=None):
        # Simulate the wrapper function raising RuntimeError for decline
        raise RuntimeError(f"User declined elicitation: {message}")

    class MockBridge:
        def list_tools(self):
            return []

        async def call(self, tool_name: str, **kwargs: Any) -> Any:
            pass

    bridge = MockBridge()
    engine = WorkflowEngine(bridge=bridge)

    code = """
async def workflow():
    c = await elicit(message="Value for c?", response_type=int)
    return {"c": c}
"""

    # Expect RuntimeError to propagate from workflow
    with pytest.raises(RuntimeError, match="User declined elicitation"):
        await engine.execute(code, elicit_fn=mock_elicit_declined)


@pytest.mark.anyio
async def test_elicit_without_function_fails():
    """Test that using elicit() without providing elicit_fn raises NameError."""

    class MockBridge:
        def list_tools(self):
            return []

        async def call(self, tool_name: str, **kwargs: Any) -> Any:
            pass

    bridge = MockBridge()
    engine = WorkflowEngine(bridge=bridge)

    code = """
async def workflow():
    c = await elicit(message="Value?", response_type=int)
    return c
"""

    # Without elicit_fn, 'elicit' won't be in namespace -> NameError
    with pytest.raises(NameError, match="'elicit' is not defined"):
        await engine.execute(code, elicit_fn=None)
