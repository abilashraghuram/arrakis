"""Factory for creating tool proxies with shared provenance store."""

from .bridge import ToolBridge
from .dataflow.base import ValueWrapper
from .dataflow.extractor import OriginExtractor
from .proxy import ProvenanceStore, ToolProxy
from .resolver import ValueResolver


class ProxyFactory:
    """Creates ToolProxy instances with shared state.

    Accepts ValueWrapper to support different data flow tracking strategies.
    """

    def __init__(
        self,
        bridge: ToolBridge,
        wrapper: ValueWrapper | None = None,
        store: ProvenanceStore | None = None,
        extractor: OriginExtractor | None = None,
        resolver: ValueResolver | None = None,
    ) -> None:
        self._bridge = bridge
        self._wrapper = wrapper
        self._store = store or ProvenanceStore()
        self._extractor = extractor
        self._resolver = resolver

    @property
    def store(self) -> ProvenanceStore:
        return self._store

    def create(self, tool_name: str) -> ToolProxy:
        return ToolProxy(
            tool_name=tool_name,
            bridge=self._bridge,
            store=self._store,
            wrapper=self._wrapper,
            extractor=self._extractor,
            resolver=self._resolver,
        )
