"""Soup: a provider-agnostic Agent Skills router for LLMs.

Define many small `Agent Skills <https://agentskills.io/specification>`_ -- in
code or as ``SKILL.md`` files -- and let Soup inject only the relevant ones into
each LLM call.

Quickstart:
    >>> from soup import Soup
    >>> soup = Soup()
    >>> _ = soup.register(
    ...     name="frontend",
    ...     description="Frontend guidance. Use for React/UI work.",
    ...     instructions="Use React 19.",
    ... )
    >>> soup.prepare("Build a react button")[:10]
    '# Frontend'
"""

from __future__ import annotations

from soup.builders import ContextBuilder, MarkdownContextBuilder
from soup.core.exceptions import (
    MissingDependencyError,
    SkillParseError,
    SkillSourceError,
    SoupError,
)
from soup.core.pipeline import SelectionPipeline
from soup.core.resolver import DependencyResolver
from soup.core.soup import Soup
from soup.models.skill import Skill
from soup.sources import load_remote, load_skill_dir, load_skills_collection, parse_skill_md
from soup.storage import InMemoryStorage, SkillStorage
from soup.strategies import (
    BM25Strategy,
    SelectionStrategy,
)

__version__ = "0.2.0"

__all__ = [
    "BM25Strategy",
    "ContextBuilder",
    "DependencyResolver",
    "InMemoryStorage",
    "MarkdownContextBuilder",
    "MissingDependencyError",
    "SelectionPipeline",
    "SelectionStrategy",
    "Skill",
    "SkillParseError",
    "SkillSourceError",
    "SkillStorage",
    "Soup",
    "SoupError",
    "__version__",
    "load_remote",
    "load_skill_dir",
    "load_skills_collection",
    "parse_skill_md",
]
