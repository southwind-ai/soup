"""Optional LLM-backed selection strategy.

Soup stays provider-agnostic: it never imports an SDK. Instead you inject a
callable that, given the query and the candidates, returns the names of the
harnesses to keep. You decide which model/SDK powers that callable.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Protocol, runtime_checkable

from soup.models.harness import Harness
from soup.strategies.base import SelectionStrategy


@runtime_checkable
class HarnessClassifier(Protocol):
    """Callable that picks relevant harness names for a query.

    Implementations typically prompt an LLM with the candidate names and
    descriptions and parse back the chosen names.
    """

    def __call__(self, query: str, candidates: list[Harness]) -> Iterable[str]:
        """Return the names of the harnesses relevant to ``query``."""
        ...


class LLMClassifierStrategy(SelectionStrategy):
    """Delegates selection to a user-supplied classifier callable.

    Args:
        classifier: A callable (or :class:`HarnessClassifier`) returning the
            names of the harnesses to keep.
        ignore_unknown_names: If ``True`` (default), names returned by the
            classifier that are not among the candidates are silently dropped;
            if ``False`` a :class:`ValueError` is raised.
    """

    def __init__(
        self,
        classifier: HarnessClassifier | Callable[[str, list[Harness]], Iterable[str]],
        *,
        ignore_unknown_names: bool = True,
    ) -> None:
        self._classifier = classifier
        self._ignore_unknown_names = ignore_unknown_names

    def select(self, query: str, harnesses: list[Harness]) -> list[Harness]:
        if not harnesses:
            return []
        by_name = {h.name: h for h in harnesses}
        chosen = list(self._classifier(query, harnesses))
        selected = []
        for name in chosen:
            harness = by_name.get(name)
            if harness is None:
                if self._ignore_unknown_names:
                    continue
                msg = f"Classifier returned unknown harness name: {name!r}"
                raise ValueError(msg)
            selected.append(harness)
        return selected
