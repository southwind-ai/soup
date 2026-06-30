"""BM25-based selection strategy.

This strategy mirrors Ratel's broad philosophy: deterministic lexical retrieval
with no embeddings and no vector database.
"""

from __future__ import annotations

import math
from collections import Counter

from soup.models.harness import Harness
from soup.strategies.base import SelectionStrategy
from soup.utils.text import tokenize_list


class BM25Strategy(SelectionStrategy):
    """Select harnesses using BM25 ranking over semantic harness text.

    Each harness is projected to a deterministic textual document built from
    meaningful fields: ``name``, ``description``, ``tags``, ``instructions``,
    and ``examples``.

    Args:
        top_k: Maximum number of harnesses to return. ``None`` keeps all
            harnesses with positive score.
        min_score: Minimum BM25 score required for a harness to be selected.
        k1: BM25 term-frequency saturation parameter.
        b: BM25 length normalization parameter.
    """

    def __init__(
        self,
        *,
        top_k: int | None = None,
        min_score: float = 0.0,
        k1: float = 0.9,
        b: float = 0.4,
    ) -> None:
        if top_k is not None and top_k < 1:
            msg = "top_k must be >= 1 when provided"
            raise ValueError(msg)
        if min_score < 0:
            msg = "min_score must be >= 0"
            raise ValueError(msg)
        if k1 <= 0:
            msg = "k1 must be > 0"
            raise ValueError(msg)
        if not 0 <= b <= 1:
            msg = "b must be between 0 and 1"
            raise ValueError(msg)
        self._top_k = top_k
        self._min_score = min_score
        self._k1 = k1
        self._b = b

    def _searchable_text(self, harness: Harness) -> str:
        parts = [harness.name]
        if harness.description:
            parts.append(harness.description)
        parts.extend(harness.tags)
        parts.append(harness.instructions)
        parts.extend(harness.examples)
        return "\n".join(parts)

    def select(self, query: str, harnesses: list[Harness]) -> list[Harness]:
        query_terms = tokenize_list(query)
        if not query_terms or not harnesses:
            return []

        documents = [tokenize_list(self._searchable_text(h)) for h in harnesses]
        lengths = [len(doc) for doc in documents]
        total_length = sum(lengths)
        if total_length == 0:
            return []
        avgdl = total_length / len(documents)

        # Document frequency of each query term.
        doc_freq: Counter[str] = Counter()
        query_vocab = set(query_terms)
        for doc in documents:
            present = set(doc) & query_vocab
            doc_freq.update(present)

        n_docs = len(documents)
        query_tf = Counter(query_terms)

        scored: list[tuple[float, int, Harness]] = []
        zipped = zip(harnesses, documents, lengths, strict=False)
        for idx, (harness, doc_tokens, dl) in enumerate(zipped):
            if dl == 0:
                continue
            tf = Counter(doc_tokens)
            score = 0.0
            norm = self._k1 * (1 - self._b + self._b * (dl / avgdl))
            for term, qtf in query_tf.items():
                term_tf = tf.get(term, 0)
                if term_tf == 0:
                    continue
                df = doc_freq.get(term, 0)
                # Smoothed Robertson/Sparck Jones idf variant.
                idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
                score += idf * ((term_tf * (self._k1 + 1)) / (term_tf + norm)) * qtf

            if score > 0 and score >= self._min_score:
                scored.append((score, idx, harness))

        scored.sort(key=lambda item: (-item[0], item[1]))
        selected = [h for _, _, h in scored]
        if self._top_k is not None:
            return selected[: self._top_k]
        return selected
