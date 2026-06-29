"""Resolves harness composition (``extends``) and ``dependencies``.

Given a set of selected harnesses, this expands the graph to pull in every
parent (``extends``) and dependency, transitively, and returns them in a valid
order: a referenced harness always appears *before* the harness that pulls it
in. Cycles are detected and broken so resolution always terminates.
"""

from __future__ import annotations

from soup.core.exceptions import MissingDependencyError
from soup.models.harness import Harness
from soup.storage.base import HarnessStorage


class DependencyResolver:
    """Expands selected harnesses with their parents and dependencies.

    Args:
        storage: Where to look up referenced harnesses.
        strict: If ``True`` (default), referencing an unregistered harness
            raises :class:`MissingDependencyError`. If ``False`` the missing
            reference is skipped.
    """

    def __init__(self, storage: HarnessStorage, *, strict: bool = True) -> None:
        self._storage = storage
        self._strict = strict

    def resolve(self, selected: list[Harness]) -> list[Harness]:
        """Return ``selected`` plus all transitive references, dependency-first.

        Args:
            selected: The harnesses chosen by the selection pipeline. Their
                relative order (e.g. by priority) is preserved for roots.

        Returns:
            The fully expanded, de-duplicated, dependency-ordered list.

        Raises:
            MissingDependencyError: If ``strict`` and a reference is unknown.
        """
        ordered: list[Harness] = []
        done: set[str] = set()
        on_stack: set[str] = set()

        def visit(harness: Harness) -> None:
            if harness.name in done:
                return
            if harness.name in on_stack:
                # Cycle: the harness is already being resolved upstream, so it
                # will be appended once that frame completes. Break here.
                return
            on_stack.add(harness.name)
            for ref in harness.references:
                referenced = self._storage.get(ref)
                if referenced is None:
                    if self._strict:
                        raise MissingDependencyError(harness.name, ref)
                    continue
                visit(referenced)
            on_stack.discard(harness.name)
            if harness.name not in done:
                done.add(harness.name)
                ordered.append(harness)

        for harness in selected:
            visit(harness)
        return ordered
