"""Soup: a provider-agnostic context router for LLMs.

Define many small :class:`~soup.models.harness.Harness` modules and let Soup
inject only the relevant ones into each LLM call.

Quickstart:
    >>> from soup import Soup
    >>> soup = Soup()
    >>> _ = soup.register(name="frontend", tags=["react"], instructions="Use React 19.")
    >>> soup.prepare("Build a react button")[:10]
    '# Frontend'
"""

from __future__ import annotations

from soup.builders import ContextBuilder, MarkdownContextBuilder
from soup.core.exceptions import MissingDependencyError, SoupError
from soup.core.pipeline import SelectionPipeline
from soup.core.resolver import DependencyResolver
from soup.core.soup import Soup
from soup.models.harness import Harness
from soup.storage import HarnessStorage, InMemoryStorage
from soup.strategies import (
    BM25Strategy,
    SelectionStrategy,
)

__version__ = "0.1.0"

__all__ = [
    "BM25Strategy",
    "ContextBuilder",
    "DependencyResolver",
    "Harness",
    "HarnessStorage",
    "InMemoryStorage",
    "MarkdownContextBuilder",
    "MissingDependencyError",
    "SelectionPipeline",
    "SelectionStrategy",
    "Soup",
    "SoupError",
    "__version__",
]
