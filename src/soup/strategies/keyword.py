"""Keyword-based selection strategy."""

from __future__ import annotations

from soup.models.harness import Harness
from soup.strategies.base import SelectionStrategy
from soup.utils.text import tokenize


class KeywordStrategy(SelectionStrategy):
    """Selects harnesses whose words appear in the request.

    A harness matches when at least ``min_matches`` of its keywords (taken from
    its name, tags and -- optionally -- description) appear as whole tokens in
    the query.

    Args:
        include_description: Whether to mine the description for keywords.
        min_matches: Minimum number of overlapping tokens required to match.
    """

    def __init__(self, *, include_description: bool = True, min_matches: int = 1) -> None:
        if min_matches < 1:
            msg = "min_matches must be >= 1"
            raise ValueError(msg)
        self._include_description = include_description
        self._min_matches = min_matches

    def _keywords(self, harness: Harness) -> set[str]:
        words = tokenize(harness.name)
        for tag in harness.tags:
            words |= tokenize(tag)
        if self._include_description and harness.description:
            words |= tokenize(harness.description)
        return words

    def select(self, query: str, harnesses: list[Harness]) -> list[Harness]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        selected = []
        for harness in harnesses:
            overlap = self._keywords(harness) & query_tokens
            if len(overlap) >= self._min_matches:
                selected.append(harness)
        return selected
