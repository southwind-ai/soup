"""Context builder interface.

A builder turns the final, ordered list of skills into a single string that
gets injected into the LLM call. Swapping the builder is how you change the
output format (Markdown, XML, plain text, ...) without touching the core.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from soup.models.skill import Skill


class ContextBuilder(ABC):
    """Renders selected skills into an injectable context block."""

    @abstractmethod
    def build(self, skills: list[Skill]) -> str:
        """Render ``skills`` into a single context string.

        Args:
            skills: The resolved, ordered skills to render.

        Returns:
            The rendered context (empty string if ``skills`` is empty).
        """
