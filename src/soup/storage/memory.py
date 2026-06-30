"""In-memory storage backend (the default)."""

from __future__ import annotations

from soup.models.skill import Skill
from soup.storage.base import SkillStorage


class InMemoryStorage(SkillStorage):
    """Stores skills in a plain dict, keyed by name.

    Insertion order is preserved, which gives deterministic output for skills
    that are otherwise equal in priority.
    """

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def add(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def remove(self, name: str) -> bool:
        return self._skills.pop(name, None) is not None

    def all(self) -> list[Skill]:
        return list(self._skills.values())

    def clear(self) -> None:
        self._skills.clear()
