"""Context builder interface.

A builder turns the final, ordered list of harnesses into a single string that
gets injected into the LLM call. Swapping the builder is how you change the
output format (Markdown, XML, plain text, ...) without touching the core.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from soup.models.harness import Harness


class ContextBuilder(ABC):
    """Renders selected harnesses into an injectable context block."""

    @abstractmethod
    def build(self, harnesses: list[Harness]) -> str:
        """Render ``harnesses`` into a single context string.

        Args:
            harnesses: The resolved, ordered harnesses to render.

        Returns:
            The rendered context (empty string if ``harnesses`` is empty).
        """
