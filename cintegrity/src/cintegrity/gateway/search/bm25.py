"""BM25 search strategy implementation."""

from __future__ import annotations

import math
from collections import Counter

from ..manager import ToolSpec
from .base import SearchResult, build_searchable_text


class BM25SearchStrategy:
    """BM25 (Best Matching 25) search strategy.

    Standard probabilistic ranking algorithm used by search engines.
    Matches Anthropic's tool_search_tool_bm25 variant.

    BM25 Formula:
        score(D,Q) = Σ IDF(qi) * (f(qi,D) * (k1 + 1)) / (f(qi,D) + k1 * (1 - b + b * |D|/avgdl))

    Where:
        - IDF(qi) = log((N - n(qi) + 0.5) / (n(qi) + 0.5) + 1)
        - f(qi,D) = frequency of term qi in document D
        - |D| = document length
        - avgdl = average document length
        - k1, b = tuning parameters
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        """Initialize BM25 strategy.

        Args:
            k1: Term frequency saturation parameter (1.2-2.0 typical)
            b: Length normalization parameter (0.75 typical)
        """
        self.k1 = k1
        self.b = b
        self._tools: dict[str, ToolSpec] = {}
        self._doc_freqs: Counter[str] = Counter()
        self._doc_lens: dict[str, int] = {}
        self._avg_doc_len: float = 0.0
        self._tokenized: dict[str, list[str]] = {}

    def index(self, tools: dict[str, ToolSpec]) -> None:
        """Build BM25 index from tools."""
        self._tools = tools
        self._doc_freqs = Counter()
        self._doc_lens = {}
        self._tokenized = {}

        if not tools:
            self._avg_doc_len = 0.0
            return

        # Tokenize all documents
        for name, spec in tools.items():
            text = build_searchable_text(spec)
            tokens = self._tokenize(text)
            self._tokenized[name] = tokens
            self._doc_lens[name] = len(tokens)

            # Count document frequency for each unique term
            for term in set(tokens):
                self._doc_freqs[term] += 1

        # Calculate average document length
        total_len = sum(self._doc_lens.values())
        self._avg_doc_len = total_len / len(tools)

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Search using BM25 ranking."""
        query_tokens = self._tokenize(query)
        if not query_tokens or not self._tools:
            return []

        scores: list[tuple[float, ToolSpec]] = []
        n_docs = len(self._tools)

        for name, spec in self._tools.items():
            doc_tokens = self._tokenized[name]
            doc_len = self._doc_lens[name]
            term_freqs = Counter(doc_tokens)

            score = 0.0
            for term in query_tokens:
                if term not in term_freqs:
                    continue

                # IDF component
                df = self._doc_freqs.get(term, 0)
                idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1)

                # TF component with length normalization
                tf = term_freqs[term]
                tf_norm = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * doc_len / self._avg_doc_len))

                score += idf * tf_norm

            if score > 0:
                scores.append((score, spec))

        # Sort by score descending
        scores.sort(key=lambda x: -x[0])
        return [SearchResult(spec=spec, score=score) for score, spec in scores[:limit]]

    def _tokenize(self, text: str) -> list[str]:
        """Simple whitespace tokenizer with lowercasing."""
        return text.lower().split()
