"""BM25-based selection strategy.

This strategy mirrors Ratel's broad philosophy: deterministic lexical retrieval
with no embeddings and no vector database.
"""

from __future__ import annotations

import math
from collections import Counter

from soup.models.skill import Skill
from soup.strategies.base import SelectionStrategy
from soup.utils.text import tokenize_list

#: Stopwords removed during BM25 scoring.
_STOPWORDS = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "but", "by", "can", "do",
        "for", "from", "how", "i", "in", "into", "is", "it", "its", "me", "my",
        "of", "on", "or", "that", "the", "their", "then", "this", "to", "use",
        "used", "using", "want", "wants", "was", "what", "when", "which", "will",
        "with", "you", "your",
    }
)


def _content_terms(text: str) -> list[str]:
    """Tokenize ``text`` and drop stopwords (selection-only filtering)."""
    return [term for term in tokenize_list(text) if term not in _STOPWORDS]


class BM25Strategy(SelectionStrategy):
    """Select skills with BM25 over routing metadata.

    Searchable text is ``name`` + ``description`` + ``tags``.

    Args:
        top_k: Maximum number of skills to return. ``None`` keeps all skills
            scoring at least ``min_score``.
        min_score: Minimum BM25 score required for a skill to be selected.
            Defaults to ``1.5``.
        k1: BM25 term-frequency saturation parameter.
        b: BM25 length normalization parameter.
    """

    def __init__(
        self,
        *,
        top_k: int | None = None,
        min_score: float = 1.5,
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

    def _searchable_text(self, skill: Skill) -> str:
        parts = [skill.name, skill.description]
        parts.extend(skill.tags)
        return "\n".join(parts)

    def select(self, query: str, skills: list[Skill]) -> list[Skill]:
        return [skill for skill, _ in self.rank(query, skills)]

    def rank(self, query: str, skills: list[Skill]) -> list[tuple[Skill, float]]:
        """Return ``(skill, score)`` pairs, highest score first."""
        query_terms = _content_terms(query)
        if not query_terms or not skills:
            return []

        documents = [_content_terms(self._searchable_text(s)) for s in skills]
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

        scored: list[tuple[float, int, Skill]] = []
        zipped = zip(skills, documents, lengths, strict=False)
        for idx, (skill, doc_tokens, dl) in enumerate(zipped):
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
                scored.append((score, idx, skill))

        scored.sort(key=lambda item: (-item[0], item[1]))
        ranked = [(skill, score) for score, _, skill in scored]
        if self._top_k is not None:
            return ranked[: self._top_k]
        return ranked
