"""Workflow engine - orchestrates code execution with provenance tracking."""

from typing import Any

from .bridge import ToolBridge
from .dataflow import TrackingStrategy
from .dataflow.base import ValueWrapper
from .dataflow.instrumented import InstrumentedRuntime, InstrumentedWrapper
from .dataflow.raw import RawWrapper
from .dataflow.transparent import TransparentWrapper
from .factory import ProxyFactory
from .provenance import ExecutionResult
from .runtime.base import Runtime
from .runtime.local import LocalRuntime


def get_wrapper(strategy: TrackingStrategy) -> ValueWrapper:
    """Factory function for tracking strategy.

    Args:
        strategy: Which data flow tracking implementation to use

    Returns:
        ValueWrapper instance for the selected strategy
    """
    if strategy == TrackingStrategy.TRANSPARENT:
        return TransparentWrapper()
    elif strategy == TrackingStrategy.INSTRUMENTED:
        return InstrumentedWrapper()
    else:
        return RawWrapper()


def get_runtime(strategy: TrackingStrategy, default: Runtime) -> Runtime:
    """Get runtime for strategy.

    Instrumented strategy requires its own runtime for AST transformation.

    Args:
        strategy: Which data flow tracking implementation
        default: Default runtime to use if not instrumented

    Returns:
        Runtime instance appropriate for the strategy
    """
    if strategy == TrackingStrategy.INSTRUMENTED:
        return InstrumentedRuntime()
    return default


class WorkflowEngine:
    """Executes LLM-generated Python code with provenance tracking.

    DIP: Depends on Runtime and ValueWrapper ABCs, not concrete implementations.
    Strategy pattern allows swapping data flow tracking at runtime.

    Usage:
        bridge = ...  # ToolBridge implementation
        engine = WorkflowEngine(bridge=bridge)
        result = await engine.execute(code)

        # With custom strategy:
        engine = WorkflowEngine(
            bridge=bridge,
            tracking_strategy=TrackingStrategy.INSTRUMENTED
        )
    """

    def __init__(
        self,
        bridge: ToolBridge,
        runtime: Runtime | None = None,
        tracking_strategy: TrackingStrategy = TrackingStrategy.TRANSPARENT,
    ) -> None:
        """Initialize workflow engine.

        Args:
            bridge: ToolBridge for executing tools
            runtime: Runtime implementation (default: LocalRuntime)
            tracking_strategy: Which data flow tracking to use (default: TRANSPARENT)
        """
        self._bridge = bridge
        self._strategy = tracking_strategy
        self._wrapper = get_wrapper(tracking_strategy)
        self._runtime = get_runtime(tracking_strategy, runtime or LocalRuntime())

    async def execute(
        self,
        code: str,
        timeout: float = 30.0,
        elicit_fn: Any | None = None,
    ) -> ExecutionResult:
        """Execute workflow code with provenance tracking.

        Args:
            code: Python code with imports and return statement
            timeout: Maximum execution time in seconds
            elicit_fn: Optional callable for requesting user input during execution

        Returns:
            ExecutionResult with return value and provenance records
        """
        # 1. Create factory with fresh provenance store and wrapper
        factory = ProxyFactory(bridge=self._bridge, wrapper=self._wrapper)

        # 2. Build namespace with ALL tool proxies
        namespace: dict[str, Any] = {}
        available_tools: set[str] = set()
        for tool_name in self._bridge.list_tools():
            namespace[tool_name] = factory.create(tool_name)
            available_tools.add(tool_name)

        # Inject elicit as built-in if provided
        if elicit_fn is not None:
            namespace["elicit"] = elicit_fn

        # 3. Execute in runtime (runtime will filter to only imported tools + builtins)
        result = await self._runtime.execute(
            code,
            namespace,
            timeout,
            available_tools=available_tools,
        )

        # 4. Return result with provenance
        return ExecutionResult(
            returned=result,
            calls=factory.store.get_records(),
        )
