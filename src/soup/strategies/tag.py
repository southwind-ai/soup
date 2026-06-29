"""Tag-based selection strategy."""

from __future__ import annotations

from collections.abc import Iterable

from soup.models.harness import Harness
from soup.strategies.base import SelectionStrategy
from soup.utils.text import tokenize


class TagStrategy(SelectionStrategy):
    """Selects harnesses whose tags are mentioned in the request.

    Unlike :class:`KeywordStrategy`, this matches *only* against tags, making it
    a precise, low-noise signal. Tags may be matched against the free-form query
    text, or against an explicit set of tags supplied per request.

    Args:
        explicit_tags: Optional fixed set of tags to match against on every
            request, in addition to (or instead of) tags found in the query.
    """

    def __init__(self, explicit_tags: Iterable[str] | None = None) -> None:
        self._explicit_tags = {t.lower() for t in explicit_tags} if explicit_tags else set()

    def select(self, query: str, harnesses: list[Harness]) -> list[Harness]:
        query_tokens = tokenize(query) | self._explicit_tags
        if not query_tokens:
            return []
        selected = []
        for harness in harnesses:
            harness_tags = {t.lower() for t in harness.tags}
            if harness_tags & query_tokens:
                selected.append(harness)
        return selected
