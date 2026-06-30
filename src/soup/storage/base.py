"""Abstract storage interface for skills.

The core never talks to a concrete backend; it depends only on this protocol.
That keeps the door open for filesystem, YAML, SQL or Redis backends without
touching the core (Dependency Inversion Principle).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from soup.models.skill import Skill


class SkillStorage(ABC):
    """Read/write store of :class:`~soup.models.skill.Skill` objects.

    Implementations are keyed by skill name; registering a skill with an
    existing name overwrites the previous one.
    """

    @abstractmethod
    def add(self, skill: Skill) -> None:
        """Insert or replace ``skill`` in the store."""

    @abstractmethod
    def get(self, name: str) -> Skill | None:
        """Return the skill named ``name`` or ``None`` if absent."""

    @abstractmethod
    def remove(self, name: str) -> bool:
        """Delete the skill named ``name``.

        Returns:
            ``True`` if a skill was removed, ``False`` if it was not present.
        """

    @abstractmethod
    def all(self) -> list[Skill]:
        """Return every stored skill."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all skills."""

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and self.get(name) is not None

    def __iter__(self) -> Iterator[Skill]:
        return iter(self.all())

    def __len__(self) -> int:
        return len(self.all())
