"""End-to-end pipeline tests: tool registration → search → workflow execution → provenance."""

import json
from typing import Any, TypedDict

import pytest

from cintegrity.adapters.tool_bridge import MCPToolBridge
from cintegrity.gateway.manager import ToolManager
from cintegrity.gateway.tools.execute_workflow import execute_workflow
from cintegrity.gateway.tools.search_tools import search_tools
from cintegrity.pybox.bridge import DirectToolBridge
from cintegrity.pybox.dataflow import TrackingStrategy
from cintegrity.pybox.engine import WorkflowEngine

# =============================================================================
# Test Fixtures - Tool Definitions
# =============================================================================


class SearchArgs(TypedDict):
    query: str


class SearchResult(TypedDict):
    items: list[dict[str, Any]]
    total: int


async def search_products(args: SearchArgs) -> SearchResult:
    """Search for products by keyword."""
    query = args["query"]
    return {
        "items": [
            {"id": 1, "name": f"{query} Product A", "price": 100},
            {"id": 2, "name": f"{query} Product B", "price": 200},
        ],
        "total": 2,
    }


class GetDetailsArgs(TypedDict):
    product_id: int


class ProductDetails(TypedDict):
    id: int
    name: str
    price: int
    stock: int
    category: str


async def get_product_details(args: GetDetailsArgs) -> ProductDetails:
    """Get detailed information about a product."""
    return {
        "id": args["product_id"],
        "name": f"Product {args['product_id']}",
        "price": 100 * args["product_id"],
        "stock": 50,
        "category": "electronics",
    }


class CalculateArgs(TypedDict):
    price: int
    quantity: int


class CalculateResult(TypedDict):
    subtotal: int
    tax: float
    total: float


async def calculate_total(args: CalculateArgs) -> CalculateResult:
    """Calculate order total with tax."""
    subtotal = args["price"] * args["quantity"]
    tax = subtotal * 0.08
    return {"subtotal": subtotal, "tax": tax, "total": subtotal + tax}


class CreateOrderArgs(TypedDict):
    product_id: int
    quantity: int
    total: float


class OrderResult(TypedDict):
    order_id: str
    status: str


async def create_order(args: CreateOrderArgs) -> OrderResult:
    """Create a new order."""
    return {
        "order_id": f"ORD-{args['product_id']}-{args['quantity']}",
        "status": "confirmed",
    }


class NotifyArgs(TypedDict):
    order_id: str
    message: str


async def send_notification(args: NotifyArgs) -> dict[str, bool]:
    """Send a notification about an order."""
    return {"sent": True}


@pytest.fixture
def manager_with_tools() -> ToolManager:
    """Create a ToolManager with e-commerce tools registered."""
    manager = ToolManager()
    manager.add_function_call(search_products)
    manager.add_function_call(get_product_details)
    manager.add_function_call(calculate_total)
    manager.add_function_call(create_order)
    manager.add_function_call(send_notification)
    return manager


# =============================================================================
# Full Pipeline Tests
# =============================================================================


class TestFullPipeline:
    """Test the complete pipeline: registration → search → execute → provenance."""

    @pytest.mark.anyio
    async def test_search_then_execute_single_tool(self, manager_with_tools: ToolManager):
        """Search for a tool, then execute a workflow using it."""
        # Step 1: Search for tools
        results = await search_tools(manager_with_tools, query="search products")

        # Verify search returns relevant tools with schemas
        assert len(results["tools"]) >= 1
        search_tool = next(t for t in results["tools"] if t["name"] == "search_products")
        assert "inputSchema" in search_tool
        assert search_tool["inputSchema"]["properties"]["query"]["type"] == "string"

        # Step 2: Execute workflow using the discovered tool
        code = """
from cintegrity.tools import search_products

async def workflow():
    result = await search_products(query="laptop")
    return result
"""
        result = await execute_workflow(manager_with_tools, planner_code=code)

        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert "laptop" in result["items"][0]["name"]

    @pytest.mark.anyio
    async def test_search_then_execute_multi_tool_workflow(self, manager_with_tools: ToolManager):
        """Search for tools, then execute a multi-step workflow."""
        # Step 1: Search for calculation tools
        results = await search_tools(manager_with_tools, query="calculate order")

        tool_names = [t["name"] for t in results["tools"]]
        assert "calculate_total" in tool_names or "create_order" in tool_names

        # Step 2: Execute multi-tool workflow
        code = """
from cintegrity.tools import search_products, get_product_details, calculate_total

async def workflow():
    # Search for products
    search_result = await search_products(query="phone")

    # Get first product ID
    first_item = search_result["items"][0]
    product_id = first_item["id"]

    # Get product details
    details = await get_product_details(product_id=product_id)

    # Calculate total for 2 units
    total = await calculate_total(price=details["price"], quantity=2)
    return total
"""
        result = await execute_workflow(manager_with_tools, planner_code=code)

        assert "subtotal" in result
        assert "tax" in result
        assert "total" in result
        # Price 100 * quantity 2 = 200 subtotal
        assert result["subtotal"] == 200

    @pytest.mark.anyio
    async def test_full_ecommerce_workflow_with_provenance(self):
        """Complete e-commerce flow with full provenance tracking."""
        bridge = DirectToolBridge()

        # Register all tools
        bridge.register("search_products", lambda **kw: search_products(kw))
        bridge.register("get_product_details", lambda **kw: get_product_details(kw))
        bridge.register("calculate_total", lambda **kw: calculate_total(kw))
        bridge.register("create_order", lambda **kw: create_order(kw))
        bridge.register("send_notification", lambda **kw: send_notification(kw))

        engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

        code = """
from cintegrity.tools import search_products, get_product_details, calculate_total, create_order, send_notification

async def workflow():
    # Step 1: Search for products
    search_result = await search_products(query="laptop")

    # Step 2: Get details for first product
    first_item = search_result["items"][0]
    details = await get_product_details(product_id=first_item["id"])

    # Step 3: Calculate total
    pricing = await calculate_total(price=details["price"], quantity=3)

    # Step 4: Create order
    order = await create_order(product_id=details["id"], quantity=3, total=pricing["total"])

    # Step 5: Send notification
    notification = await send_notification(order_id=order["order_id"], message="Order confirmed")

    return {"order": order, "notification": notification}
"""
        execution = await engine.execute(code)
        exported = execution.to_dict()

        # Verify all 5 tool calls were tracked
        assert len(exported["calls"]) == 5

        call_names = [c["tool_name"] for c in exported["calls"]]
        assert call_names == [
            "search_products",
            "get_product_details",
            "calculate_total",
            "create_order",
            "send_notification",
        ]

        # Verify data flow graph
        data_flow = exported["data_flow"]
        assert len(data_flow["nodes"]) == 5

        # Verify edges capture data dependencies
        edges = data_flow["edges"]
        assert len(edges) >= 4  # At least 4 data flow edges

        # Verify specific data flows
        # search_products -> get_product_details (product_id)
        search_to_details = [
            e for e in edges if e["source"] == "search_products#0" and e["sink"] == "get_product_details#0"
        ]
        assert len(search_to_details) == 1
        assert "product_id" in search_to_details[0]["args"]

        # get_product_details -> calculate_total (price)
        details_to_calc = [
            e for e in edges if e["source"] == "get_product_details#0" and e["sink"] == "calculate_total#0"
        ]
        assert len(details_to_calc) == 1
        assert "price" in details_to_calc[0]["args"]

        # Verify JSON export is valid
        json_str = execution.to_json()
        parsed = json.loads(json_str)
        assert "calls" in parsed
        assert "data_flow" in parsed


class TestDataFlowAccuracy:
    """Test per-argument origin tracking accuracy in complex scenarios."""

    @pytest.mark.anyio
    async def test_diamond_dependency_pattern(self):
        """Test diamond pattern: A -> B, A -> C, B -> D, C -> D."""
        bridge = DirectToolBridge()

        async def tool_a() -> dict:
            return {"x": 10, "y": 20}

        async def tool_b(x: int) -> dict:
            return {"b_result": x * 2}

        async def tool_c(y: int) -> dict:
            return {"c_result": y * 3}

        async def tool_d(b_val: int, c_val: int) -> dict:
            return {"final": b_val + c_val}

        bridge.register("tool_a", tool_a)
        bridge.register("tool_b", tool_b)
        bridge.register("tool_c", tool_c)
        bridge.register("tool_d", tool_d)

        engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

        code = """
from cintegrity.tools import tool_a, tool_b, tool_c, tool_d

async def workflow():
    # A produces both x and y
    a_result = await tool_a()

    # B consumes x
    b_result = await tool_b(x=a_result["x"])

    # C consumes y
    c_result = await tool_c(y=a_result["y"])

    # D consumes outputs from both B and C
    d_result = await tool_d(b_val=b_result["b_result"], c_val=c_result["c_result"])

    return d_result
"""
        execution = await engine.execute(code)
        exported = execution.to_dict()

        # Verify call order
        assert len(exported["calls"]) == 4

        # Verify tool_d's input origins
        call_d = exported["calls"][3]
        assert call_d["tool_name"] == "tool_d"
        assert "b_val" in call_d["input_origins"]
        assert "c_val" in call_d["input_origins"]
        assert "tool_b#0" in call_d["input_origins"]["b_val"]
        assert "tool_c#0" in call_d["input_origins"]["c_val"]

        # Verify data flow edges
        edges = exported["data_flow"]["edges"]

        # A -> B
        a_to_b = [e for e in edges if e["source"] == "tool_a#0" and e["sink"] == "tool_b#0"]
        assert len(a_to_b) == 1
        assert "x" in a_to_b[0]["args"]

        # A -> C
        a_to_c = [e for e in edges if e["source"] == "tool_a#0" and e["sink"] == "tool_c#0"]
        assert len(a_to_c) == 1
        assert "y" in a_to_c[0]["args"]

        # B -> D
        b_to_d = [e for e in edges if e["source"] == "tool_b#0" and e["sink"] == "tool_d#0"]
        assert len(b_to_d) == 1
        assert "b_val" in b_to_d[0]["args"]

        # C -> D
        c_to_d = [e for e in edges if e["source"] == "tool_c#0" and e["sink"] == "tool_d#0"]
        assert len(c_to_d) == 1
        assert "c_val" in c_to_d[0]["args"]

    @pytest.mark.anyio
    async def test_fan_out_fan_in_pattern(self):
        """Test fan-out fan-in: A -> (B, C, D) -> E."""
        bridge = DirectToolBridge()

        async def source() -> dict:
            return {"a": 1, "b": 2, "c": 3}

        async def process_a(val: int) -> int:
            return val * 10

        async def process_b(val: int) -> int:
            return val * 20

        async def process_c(val: int) -> int:
            return val * 30

        async def aggregate(x: int, y: int, z: int) -> dict:
            return {"sum": x + y + z}

        bridge.register("source", source)
        bridge.register("process_a", process_a)
        bridge.register("process_b", process_b)
        bridge.register("process_c", process_c)
        bridge.register("aggregate", aggregate)

        engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

        code = """
from cintegrity.tools import source, process_a, process_b, process_c, aggregate

async def workflow():
    data = await source()

    # Fan out
    result_a = await process_a(val=data["a"])
    result_b = await process_b(val=data["b"])
    result_c = await process_c(val=data["c"])

    # Fan in
    final = await aggregate(x=result_a, y=result_b, z=result_c)
    return final
"""
        execution = await engine.execute(code)
        exported = execution.to_dict()

        assert len(exported["calls"]) == 5

        # Verify aggregate's input origins from all three processors
        call_aggregate = exported["calls"][4]
        assert call_aggregate["tool_name"] == "aggregate"
        assert "process_a#0" in call_aggregate["input_origins"]["x"]
        assert "process_b#0" in call_aggregate["input_origins"]["y"]
        assert "process_c#0" in call_aggregate["input_origins"]["z"]

        # Verify edges
        edges = exported["data_flow"]["edges"]

        # All processors feed into aggregate
        agg_inputs = [e for e in edges if e["sink"] == "aggregate#0"]
        assert len(agg_inputs) == 3

        source_edges = [e["source"] for e in agg_inputs]
        assert "process_a#0" in source_edges
        assert "process_b#0" in source_edges
        assert "process_c#0" in source_edges

    @pytest.mark.anyio
    async def test_chained_transformations_preserve_origin(self):
        """Test that local transformations preserve data origins."""
        bridge = DirectToolBridge()

        async def fetch_data() -> dict:
            return {"value": 100}

        async def process(transformed: int) -> dict:
            return {"result": transformed}

        bridge.register("fetch_data", fetch_data)
        bridge.register("process", process)

        engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

        code = """
from cintegrity.tools import fetch_data, process

async def workflow():
    data = await fetch_data()
    value = data["value"]

    # Multiple local transformations
    value = value * 2
    value = value + 50
    value = value // 3

    result = await process(transformed=value)
    return result
"""
        execution = await engine.execute(code)
        exported = execution.to_dict()

        # process should still know its input came from fetch_data
        call_process = exported["calls"][1]
        assert "fetch_data#0" in call_process["input_origins"]["transformed"]

    @pytest.mark.anyio
    async def test_nested_data_structure_origin_tracking(self):
        """Test origin tracking through nested data structures."""
        bridge = DirectToolBridge()

        async def get_user() -> dict:
            return {
                "user": {
                    "profile": {"name": "Alice", "age": 30},
                    "preferences": {"theme": "dark"},
                }
            }

        async def greet(name: str, theme: str) -> str:
            return f"Hello {name}! Theme: {theme}"

        bridge.register("get_user", get_user)
        bridge.register("greet", greet)

        engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

        code = """
from cintegrity.tools import get_user, greet

async def workflow():
    user_data = await get_user()

    # Deep nested access
    name = user_data["user"]["profile"]["name"]
    theme = user_data["user"]["preferences"]["theme"]

    result = await greet(name=name, theme=theme)
    return result
"""
        execution = await engine.execute(code)
        exported = execution.to_dict()

        # greet should track both arguments from get_user
        call_greet = exported["calls"][1]
        assert "get_user#0" in call_greet["input_origins"]["name"]
        assert "get_user#0" in call_greet["input_origins"]["theme"]


class TestTrackingStrategies:
    """Compare TRANSPARENT and INSTRUMENTED tracking strategies."""

    @pytest.mark.anyio
    async def test_transparent_strategy_basic_tracking(self):
        """Test TRANSPARENT strategy tracks basic data flow."""
        bridge = DirectToolBridge()

        async def producer() -> dict:
            return {"value": 42}

        async def consumer(data: dict) -> dict:
            return {"received": data["value"]}

        bridge.register("producer", producer)
        bridge.register("consumer", consumer)

        engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

        code = """
from cintegrity.tools import producer, consumer

async def workflow():
    data = await producer()
    result = await consumer(data=data)
    return result
"""
        execution = await engine.execute(code)

        assert len(execution.calls) == 2
        assert "producer#0" in execution.calls[1].all_input_origins()

    @pytest.mark.anyio
    async def test_instrumented_strategy_basic_tracking(self):
        """Test INSTRUMENTED strategy tracks basic data flow."""
        bridge = DirectToolBridge()

        async def producer() -> dict:
            return {"value": 42}

        async def consumer(data: dict) -> dict:
            return {"received": data["value"]}

        bridge.register("producer", producer)
        bridge.register("consumer", consumer)

        engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.INSTRUMENTED)

        code = """
from cintegrity.tools import producer, consumer

async def workflow():
    data = await producer()
    result = await consumer(data=data)
    return result
"""
        execution = await engine.execute(code)

        assert len(execution.calls) == 2
        assert "producer#0" in execution.calls[1].all_input_origins()

    @pytest.mark.anyio
    async def test_both_strategies_produce_same_data_flow(self):
        """Both strategies should produce identical data flow graphs for the same workflow."""

        async def tool_a() -> dict:
            return {"x": 10}

        async def tool_b(val: int) -> dict:
            return {"y": val * 2}

        workflow_code = """
from cintegrity.tools import tool_a, tool_b

async def workflow():
    a = await tool_a()
    b = await tool_b(val=a["x"])
    return b
"""
        results = {}

        for strategy in [TrackingStrategy.TRANSPARENT, TrackingStrategy.INSTRUMENTED]:
            bridge = DirectToolBridge()
            bridge.register("tool_a", tool_a)
            bridge.register("tool_b", tool_b)

            engine = WorkflowEngine(bridge=bridge, tracking_strategy=strategy)
            execution = await engine.execute(workflow_code)
            results[strategy] = execution.to_dict()

        # Both should have same call structure
        for strategy in [TrackingStrategy.TRANSPARENT, TrackingStrategy.INSTRUMENTED]:
            assert len(results[strategy]["calls"]) == 2
            assert results[strategy]["calls"][0]["tool_name"] == "tool_a"
            assert results[strategy]["calls"][1]["tool_name"] == "tool_b"

        # Both should track the data flow
        for strategy in [TrackingStrategy.TRANSPARENT, TrackingStrategy.INSTRUMENTED]:
            call_b = results[strategy]["calls"][1]
            assert "tool_a#0" in call_b["input_origins"]["val"]

    @pytest.mark.anyio
    async def test_no_tracking_strategy(self):
        """Test NONE strategy doesn't track data flow but still executes."""
        bridge = DirectToolBridge()

        async def tool_a() -> dict:
            return {"x": 10}

        async def tool_b(val: int) -> dict:
            return {"y": val * 2}

        bridge.register("tool_a", tool_a)
        bridge.register("tool_b", tool_b)

        engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.NONE)

        code = """
from cintegrity.tools import tool_a, tool_b

async def workflow():
    a = await tool_a()
    b = await tool_b(val=a["x"])
    return b
"""
        execution = await engine.execute(code)

        # Calls should still be recorded
        assert len(execution.calls) == 2

        # But no origin tracking
        assert len(execution.calls[1].input_origins) == 0


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    @pytest.mark.anyio
    async def test_empty_workflow_no_tool_calls(self):
        """Workflow with no tool calls."""
        bridge = DirectToolBridge()

        async def unused_tool() -> dict:
            return {"data": "unused"}

        bridge.register("unused_tool", unused_tool)
        engine = WorkflowEngine(bridge=bridge)

        code = """
from cintegrity.tools import unused_tool

async def workflow():
    result = 1 + 2 + 3
    return result
"""
        execution = await engine.execute(code)

        assert len(execution.calls) == 0
        assert execution.returned == 6

    @pytest.mark.anyio
    async def test_same_tool_called_many_times(self):
        """Same tool called multiple times gets unique IDs."""
        bridge = DirectToolBridge()

        call_count = 0

        async def counter() -> int:
            nonlocal call_count
            call_count += 1
            return call_count

        bridge.register("counter", counter)
        engine = WorkflowEngine(bridge=bridge)

        code = """
from cintegrity.tools import counter

async def workflow():
    a = await counter()
    b = await counter()
    c = await counter()
    d = await counter()
    e = await counter()
    return a.value + b.value + c.value + d.value + e.value
"""
        execution = await engine.execute(code)

        assert len(execution.calls) == 5
        assert execution.calls[0].call_id == "counter#0"
        assert execution.calls[1].call_id == "counter#1"
        assert execution.calls[2].call_id == "counter#2"
        assert execution.calls[3].call_id == "counter#3"
        assert execution.calls[4].call_id == "counter#4"

        assert execution.returned == 15  # 1+2+3+4+5

    @pytest.mark.anyio
    async def test_tool_returning_none(self):
        """Tool that returns None."""
        bridge = DirectToolBridge()

        async def void_tool() -> None:
            pass

        bridge.register("void_tool", void_tool)
        engine = WorkflowEngine(bridge=bridge)

        code = """
from cintegrity.tools import void_tool

async def workflow():
    result = await void_tool()
    return result
"""
        execution = await engine.execute(code)

        assert len(execution.calls) == 1
        assert execution.calls[0].output_value is None

    @pytest.mark.anyio
    async def test_tool_with_complex_nested_output(self):
        """Tool returning deeply nested structures."""
        bridge = DirectToolBridge()

        async def complex_output() -> dict:
            return {
                "level1": {
                    "level2": {
                        "level3": {
                            "data": [1, 2, {"nested_list_dict": True}],
                        }
                    }
                },
                "array": [[1, 2], [3, 4]],
            }

        async def processor(value: Any) -> dict:
            return {"processed": True, "input_type": type(value).__name__}

        bridge.register("complex_output", complex_output)
        bridge.register("processor", processor)

        engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

        code = """
from cintegrity.tools import complex_output, processor

async def workflow():
    data = await complex_output()
    deep_value = data["level1"]["level2"]["level3"]["data"][2]
    result = await processor(value=deep_value)
    return result
"""
        execution = await engine.execute(code)
        exported = execution.to_dict()

        # Verify tracking through nested access
        assert "complex_output#0" in exported["calls"][1]["input_origins"]["value"]

    @pytest.mark.anyio
    async def test_multiple_origins_merged(self):
        """Argument receives data from multiple tools."""
        bridge = DirectToolBridge()

        async def get_a() -> int:
            return 10

        async def get_b() -> int:
            return 20

        async def combine(total: int) -> dict:
            return {"result": total}

        bridge.register("get_a", get_a)
        bridge.register("get_b", get_b)
        bridge.register("combine", combine)

        engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

        code = """
from cintegrity.tools import get_a, get_b, combine

async def workflow():
    a = await get_a()
    b = await get_b()
    total = a + b
    result = await combine(total=total)
    return result
"""
        execution = await engine.execute(code)
        exported = execution.to_dict()

        # combine's 'total' argument should have origins from both get_a and get_b
        call_combine = exported["calls"][2]
        origins = call_combine["input_origins"]["total"]
        assert "get_a#0" in origins
        assert "get_b#0" in origins

    @pytest.mark.anyio
    async def test_list_iteration_preserves_origin(self):
        """Iterating over a list preserves origin for each element."""
        bridge = DirectToolBridge()

        async def get_items() -> list:
            return [{"id": 1}, {"id": 2}, {"id": 3}]

        async def process_item(item: dict) -> dict:
            return {"processed_id": item["id"]}

        bridge.register("get_items", get_items)
        bridge.register("process_item", process_item)

        engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

        code = """
from cintegrity.tools import get_items, process_item

async def workflow():
    items = await get_items()
    first = items[0]
    result = await process_item(item=first)
    return result
"""
        execution = await engine.execute(code)
        exported = execution.to_dict()

        # process_item should know its input came from get_items
        call_process = exported["calls"][1]
        assert "get_items#0" in call_process["input_origins"]["item"]


class TestErrorHandling:
    """Error handling scenarios."""

    @pytest.mark.anyio
    async def test_tool_not_imported_error(self):
        """Using a tool that wasn't imported raises error."""
        bridge = DirectToolBridge()

        async def available_tool() -> dict:
            return {"data": "test"}

        bridge.register("available_tool", available_tool)
        engine = WorkflowEngine(bridge=bridge)

        code = """
from cintegrity.tools import available_tool

async def workflow():
    # Try to use a tool that wasn't imported
    result = await nonexistent_tool()
    return result
"""
        with pytest.raises(Exception):  # Should raise some form of error
            await engine.execute(code)

    @pytest.mark.anyio
    async def test_import_nonexistent_tool_error(self):
        """Importing a tool that doesn't exist raises error."""
        bridge = DirectToolBridge()

        async def real_tool() -> dict:
            return {"data": "test"}

        bridge.register("real_tool", real_tool)
        engine = WorkflowEngine(bridge=bridge)

        code = """
from cintegrity.tools import fake_tool_that_doesnt_exist

async def workflow():
    result = await fake_tool_that_doesnt_exist()
    return result
"""
        with pytest.raises(Exception):
            await engine.execute(code)

    @pytest.mark.anyio
    async def test_tool_execution_error_propagates(self):
        """Tool that raises an exception propagates error."""
        bridge = DirectToolBridge()

        async def failing_tool() -> dict:
            raise ValueError("Intentional failure")

        bridge.register("failing_tool", failing_tool)
        engine = WorkflowEngine(bridge=bridge)

        code = """
from cintegrity.tools import failing_tool

async def workflow():
    result = await failing_tool()
    return result
"""
        with pytest.raises(Exception):
            await engine.execute(code)

    @pytest.mark.anyio
    async def test_syntax_error_in_workflow(self):
        """Syntax error in workflow code raises error."""
        bridge = DirectToolBridge()

        async def tool() -> dict:
            return {}

        bridge.register("tool", tool)
        engine = WorkflowEngine(bridge=bridge)

        code = """
from cintegrity.tools import tool

async def workflow():
    # Invalid Python syntax
    result = await tool(
    return result
"""
        with pytest.raises(SyntaxError):
            await engine.execute(code)


class TestMCPBridgeIntegration:
    """Test MCPToolBridge integration with ToolManager."""

    @pytest.mark.anyio
    async def test_mcp_bridge_executes_via_manager(self, manager_with_tools: ToolManager):
        """MCPToolBridge correctly delegates to ToolManager."""
        bridge = MCPToolBridge(manager_with_tools)
        engine = WorkflowEngine(bridge=bridge)

        code = """
from cintegrity.tools import search_products

async def workflow():
    result = await search_products(query="test")
    return result
"""
        execution = await engine.execute(code)

        assert len(execution.calls) == 1
        assert execution.calls[0].tool_name == "search_products"
        assert execution.calls[0].output_value["total"] == 2

    @pytest.mark.anyio
    async def test_mcp_bridge_multi_tool_with_provenance(self, manager_with_tools: ToolManager):
        """MCPToolBridge tracks provenance across multiple tools."""
        bridge = MCPToolBridge(manager_with_tools)
        engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

        code = """
from cintegrity.tools import search_products, calculate_total

async def workflow():
    search_result = await search_products(query="item")
    first_item = search_result["items"][0]
    total = await calculate_total(price=first_item["price"], quantity=5)
    return total
"""
        execution = await engine.execute(code)
        exported = execution.to_dict()

        assert len(exported["calls"]) == 2

        # Verify provenance tracking
        call_calc = exported["calls"][1]
        assert "search_products#0" in call_calc["input_origins"]["price"]


class TestProvenanceExport:
    """Test provenance export formats."""

    @pytest.mark.anyio
    async def test_json_export_is_valid(self):
        """Exported JSON is valid and parseable."""
        bridge = DirectToolBridge()

        async def tool_a() -> dict:
            return {"value": 1}

        async def tool_b(x: int) -> dict:
            return {"result": x}

        bridge.register("tool_a", tool_a)
        bridge.register("tool_b", tool_b)

        engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

        code = """
from cintegrity.tools import tool_a, tool_b

async def workflow():
    a = await tool_a()
    b = await tool_b(x=a["value"])
    return b
"""
        execution = await engine.execute(code)
        json_str = execution.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)

        # Should have required fields
        assert "returned" in parsed
        assert "calls" in parsed
        assert "data_flow" in parsed
        assert "nodes" in parsed["data_flow"]
        assert "edges" in parsed["data_flow"]

    @pytest.mark.anyio
    async def test_data_flow_nodes_have_timestamps(self):
        """Data flow nodes include timestamps."""
        bridge = DirectToolBridge()

        async def tool() -> dict:
            return {}

        bridge.register("tool", tool)
        engine = WorkflowEngine(bridge=bridge)

        code = """
from cintegrity.tools import tool

async def workflow():
    result = await tool()
    return result
"""
        execution = await engine.execute(code)
        exported = execution.to_dict()

        node = exported["data_flow"]["nodes"][0]
        assert "id" in node
        assert "tool" in node
        assert "timestamp" in node
        assert isinstance(node["timestamp"], float)

    @pytest.mark.anyio
    async def test_data_flow_edges_have_args(self):
        """Data flow edges include argument names."""
        bridge = DirectToolBridge()

        async def producer() -> dict:
            return {"a": 1, "b": 2}

        async def consumer(x: int, y: int) -> dict:
            return {"sum": x + y}

        bridge.register("producer", producer)
        bridge.register("consumer", consumer)

        engine = WorkflowEngine(bridge=bridge, tracking_strategy=TrackingStrategy.TRANSPARENT)

        code = """
from cintegrity.tools import producer, consumer

async def workflow():
    data = await producer()
    result = await consumer(x=data["a"], y=data["b"])
    return result
"""
        execution = await engine.execute(code)
        exported = execution.to_dict()

        edges = exported["data_flow"]["edges"]
        assert len(edges) == 1

        edge = edges[0]
        assert edge["source"] == "producer#0"
        assert edge["sink"] == "consumer#0"
        assert "args" in edge
        assert "x" in edge["args"]
        assert "y" in edge["args"]
