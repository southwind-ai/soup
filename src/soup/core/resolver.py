"""Resolves skill composition (``extends``) and ``dependencies``.

Given a set of selected skills, this expands the graph to pull in every parent
(``extends``) and dependency, transitively, and returns them in a valid order:
a referenced skill always appears *before* the skill that pulls it in. Cycles
are detected and broken so resolution always terminates.
"""

from __future__ import annotations

from soup.core.exceptions import MissingDependencyError
from soup.models.skill import Skill
from soup.storage.base import SkillStorage


class DependencyResolver:
    """Expands selected skills with their parents and dependencies.

    Args:
        storage: Where to look up referenced skills.
        strict: If ``True`` (default), referencing an unregistered skill raises
            :class:`MissingDependencyError`. If ``False`` the missing reference
            is skipped.
    """

    def __init__(self, storage: SkillStorage, *, strict: bool = True) -> None:
        self._storage = storage
        self._strict = strict

    def resolve(self, selected: list[Skill]) -> list[Skill]:
        """Return ``selected`` plus all transitive references, dependency-first.

        Args:
            selected: The skills chosen by the selection pipeline. Their
                relative order (e.g. by priority) is preserved for roots.

        Returns:
            The fully expanded, de-duplicated, dependency-ordered list.

        Raises:
            MissingDependencyError: If ``strict`` and a reference is unknown.
        """
        ordered: list[Skill] = []
        done: set[str] = set()
        on_stack: set[str] = set()

        def visit(skill: Skill) -> None:
            if skill.name in done:
                return
            if skill.name in on_stack:
                # Cycle: the skill is already being resolved upstream, so it
                # will be appended once that frame completes. Break here.
                return
            on_stack.add(skill.name)
            for ref in skill.references:
                referenced = self._storage.get(ref)
                if referenced is None:
                    if self._strict:
                        raise MissingDependencyError(skill.name, ref)
                    continue
                visit(referenced)
            on_stack.discard(skill.name)
            if skill.name not in done:
                done.add(skill.name)
                ordered.append(skill)

        for skill in selected:
            visit(skill)
        return ordered
