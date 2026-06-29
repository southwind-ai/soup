"""The selection pipeline: chains strategies into a single selection step."""

from __future__ import annotations

from soup.models.harness import Harness
from soup.strategies.base import SelectionStrategy


class SelectionPipeline:
    """Runs an ordered list of strategies and **unions** their results.

    A harness is selected if *any* strategy selects it; the first occurrence
    determines its position, so the pipeline is deterministic. Union (rather
    than chained filtering) is used so that complementary signals -- e.g. an
    exact tag match and a fuzzy keyword match -- add recall instead of fighting
    each other.

    Args:
        strategies: The strategies to run, in order.
    """

    def __init__(self, strategies: list[SelectionStrategy] | None = None) -> None:
        self._strategies: list[SelectionStrategy] = list(strategies or [])

    @property
    def strategies(self) -> list[SelectionStrategy]:
        """The strategies currently in the pipeline (a copy)."""
        return list(self._strategies)

    def add(self, strategy: SelectionStrategy) -> None:
        """Append ``strategy`` to the end of the pipeline."""
        self._strategies.append(strategy)

    def select(self, query: str, harnesses: list[Harness]) -> list[Harness]:
        """Return the union of every strategy's selection, de-duplicated."""
        seen: set[str] = set()
        selected: list[Harness] = []
        for strategy in self._strategies:
            for harness in strategy.select(query, harnesses):
                if harness.name not in seen:
                    seen.add(harness.name)
                    selected.append(harness)
        return selected
