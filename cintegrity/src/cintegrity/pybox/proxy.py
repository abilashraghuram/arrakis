"""Tool proxy - wraps tool calls to track provenance.

Core component that:
1. Extracts origins from inputs (SINK)
2. Calls the underlying tool via bridge
3. Tags output with origin (SOURCE) using ValueWrapper
4. Records the call for audit trail
"""

import logging
import time
from typing import Any

from .bridge import ToolBridge
from .dataflow.base import TrackedValue, ValueWrapper
from .dataflow.extractor import OriginExtractor, RecursiveOriginExtractor
from .dataflow.transparent import TransparentWrapper
from .provenance import Origin, ToolCallRecord
from .resolver import RecursiveValueResolver, ValueResolver

_log = logging.getLogger("cintegrity.pybox.proxy")


class ProvenanceStore:
    """Stores provenance records during execution."""

    def __init__(self) -> None:
        self._records: list[ToolCallRecord] = []
        self._counts: dict[str, int] = {}

    def next_call_id(self, tool_name: str) -> str:
        count = self._counts.get(tool_name, 0)
        self._counts[tool_name] = count + 1
        return f"{tool_name}#{count}"

    def record(self, record: ToolCallRecord) -> None:
        self._records.append(record)

    def get_records(self) -> tuple[ToolCallRecord, ...]:
        return tuple(self._records)

    def clear(self) -> None:
        self._records.clear()
        self._counts.clear()


class ToolProxy:
    """Wraps a tool to track provenance.

    Uses ValueWrapper ABC to create tracked values, allowing
    different data flow tracking strategies to be used.
    """

    def __init__(
        self,
        tool_name: str,
        bridge: ToolBridge,
        store: ProvenanceStore,
        wrapper: ValueWrapper | None = None,
        extractor: OriginExtractor | None = None,
        resolver: ValueResolver | None = None,
    ) -> None:
        self._tool_name = tool_name
        self._bridge = bridge
        self._store = store
        self._wrapper = wrapper or TransparentWrapper()
        self._extractor = extractor or RecursiveOriginExtractor()
        self._resolver = resolver or RecursiveValueResolver()

    async def __call__(self, **kwargs: Any) -> TrackedValue:
        """Execute tool and return tracked result.

        Args:
            **kwargs: Tool arguments (may contain TrackedValue wrappers)

        Returns:
            TrackedValue wrapping the tool result with provenance origin
        """
        # 1. Extract per-argument origins (SINK analysis)
        per_arg_origins = self._extractor.extract_per_arg(kwargs)
        # Convert frozenset to tuple for frozen dataclass
        input_origins = {arg: tuple(sorted(origins)) for arg, origins in per_arg_origins.items()}

        # 2. Generate call ID and timestamp
        call_id = self._store.next_call_id(self._tool_name)
        timestamp = time.time()

        # 3. Resolve TrackedValue wrappers for actual tool call
        resolved_kwargs = {k: self._resolver.resolve(v) for k, v in kwargs.items()}

        # Log tool execution start
        _log.info(
            f"Executing: {self._tool_name}({', '.join(f'{k}={v!r}' for k, v in resolved_kwargs.items())})",
            extra={
                "event": "tool_execute_start",
                "call_id": call_id,
                "tool_name": self._tool_name,
                "input_value": resolved_kwargs,
            },
        )

        # 4. Execute tool via bridge with timing
        start = time.perf_counter()
        try:
            result = await self._bridge.call(self._tool_name, **resolved_kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            # Log tool execution success
            _log.info(
                f"Completed: {self._tool_name} -> {result!r} [{duration_ms:.2f}ms]",
                extra={
                    "event": "tool_execute_complete",
                    "call_id": call_id,
                    "tool_name": self._tool_name,
                    "output_value": result,
                    "duration_ms": duration_ms,
                },
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            _log.error(
                f"Failed: {self._tool_name} [{duration_ms:.2f}ms]",
                extra={
                    "event": "tool_execute_error",
                    "call_id": call_id,
                    "tool_name": self._tool_name,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "duration_ms": duration_ms,
                },
                exc_info=True,
            )
            raise

        # 5. Record for audit trail
        record = ToolCallRecord(
            call_id=call_id,
            tool_name=self._tool_name,
            input_value=resolved_kwargs,
            input_origins=input_origins,
            output_value=result,
            timestamp=timestamp,
            duration_ms=duration_ms,
        )
        self._store.record(record)

        # 6. Tag result with origin (SOURCE) using wrapper
        origin = Origin(call_id=call_id, tool_name=self._tool_name, timestamp=timestamp)
        return self._wrapper.wrap(result, origin)
