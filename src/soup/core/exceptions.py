"""Exceptions raised by Soup."""

from __future__ import annotations


class SoupError(Exception):
    """Base class for all Soup errors."""


class MissingDependencyError(SoupError):
    """Raised when a skill references another that is not registered."""

    def __init__(self, skill_name: str, missing: str) -> None:
        self.skill_name = skill_name
        self.missing = missing
        super().__init__(f"Skill {skill_name!r} references unknown skill {missing!r}")


class SkillParseError(SoupError):
    """Raised when a ``SKILL.md`` file is malformed or violates the spec."""


class SkillSourceError(SoupError):
    """Raised when a skill source (path or remote URL) cannot be loaded."""
