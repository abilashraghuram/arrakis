"""Test data flow tracking with user's example scenario."""

import pytest

from cintegrity.pybox.bridge import DirectToolBridge
from cintegrity.pybox.dataflow import TrackingStrategy
from cintegrity.pybox.engine import WorkflowEngine


@pytest.mark.anyio
async def test_user_example_data_flow():
    """
    User's example:
        a, b, c = toolA()
        a = transformed(a)  # local transformation
        d = toolB(a, b)
        result = toolC(c, d)

    Expected data flow:
        toolA#0 -> toolB#0 (a, b came from toolA)
        toolA#0 -> toolC#0 (c came from toolA)
        toolB#0 -> toolC#0 (d came from toolB)
    """
    bridge = DirectToolBridge()

    async def toolA() -> dict:
        return {"a": 10, "b": 20, "c": 30}

    async def toolB(a: int, b: int) -> int:
        return a + b

    async def toolC(c: int, d: int) -> int:
        return c * d

    bridge.register("toolA", toolA)
    bridge.register("toolB", toolB)
    bridge.register("toolC", toolC)
    engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

    # Simulate the workflow
    code = """
from cintegrity.tools import toolA, toolB, toolC

async def workflow():
    # a, b, c = toolA() - get values from toolA
    data = await toolA()
    a = data["a"]
    b = data["b"]
    c = data["c"]

    # a = transformed(a) - local transformation (origins preserved!)
    a = a * 2

    # d = toolB(a, b)
    d = await toolB(a=a, b=b)

    # result = toolC(c, d)
    result = await toolC(c=c, d=d)
    return result
"""
    execution = await engine.execute(code)
    exported = execution.to_dict()

    # Should have 3 tool calls
    assert len(exported["calls"]) == 3

    # Verify the calls
    call_a = exported["calls"][0]
    call_b = exported["calls"][1]
    call_c = exported["calls"][2]

    assert call_a["tool_name"] == "toolA"
    assert call_b["tool_name"] == "toolB"
    assert call_c["tool_name"] == "toolC"

    # toolA has no input origins (it's the source)
    assert call_a["input_origins"] == {}

    # toolB's inputs (a, b) came from toolA - per-argument tracking!
    assert "a" in call_b["input_origins"]
    assert "b" in call_b["input_origins"]
    assert "toolA#0" in call_b["input_origins"]["a"]
    assert "toolA#0" in call_b["input_origins"]["b"]

    # toolC's inputs: c from toolA, d from toolB - per-argument tracking!
    assert "c" in call_c["input_origins"]
    assert "d" in call_c["input_origins"]
    assert "toolA#0" in call_c["input_origins"]["c"]
    assert "toolB#0" in call_c["input_origins"]["d"]

    # Check data_flow edges (now include 'args' field)
    edges = exported["data_flow"]["edges"]

    # toolA -> toolB edge (via args a, b)
    toolA_to_toolB = [e for e in edges if e["source"] == "toolA#0" and e["sink"] == "toolB#0"]
    assert len(toolA_to_toolB) == 1
    assert set(toolA_to_toolB[0]["args"]) == {"a", "b"}

    # toolA -> toolC edge (via arg c)
    toolA_to_toolC = [e for e in edges if e["source"] == "toolA#0" and e["sink"] == "toolC#0"]
    assert len(toolA_to_toolC) == 1
    assert toolA_to_toolC[0]["args"] == ["c"]

    # toolB -> toolC edge (via arg d)
    toolB_to_toolC = [e for e in edges if e["source"] == "toolB#0" and e["sink"] == "toolC#0"]
    assert len(toolB_to_toolC) == 1
    assert toolB_to_toolC[0]["args"] == ["d"]

    print("\n=== Data Flow JSON ===")
    print(execution.to_json())


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_user_example_data_flow())
