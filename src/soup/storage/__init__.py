"""Storage backends for skills."""

from soup.storage.base import SkillStorage
from soup.storage.memory import InMemoryStorage

__all__ = ["InMemoryStorage", "SkillStorage"]
