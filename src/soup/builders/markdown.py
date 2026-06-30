"""Markdown context builder (the default)."""

from __future__ import annotations

from collections.abc import Callable

from soup.builders.base import ContextBuilder
from soup.models.skill import Skill


def _default_title(skill: Skill) -> str:
    """Turn ``api-design`` / ``api_design`` into ``Api Design``."""
    return skill.name.replace("-", " ").replace("_", " ").title()


class MarkdownContextBuilder(ContextBuilder):
    """Renders skills as Markdown sections.

    Example output::

        # Frontend
        Use React 19.

        # React
        Prefer hooks.

    Args:
        heading_level: Markdown heading level for each skill (1 -> ``#``).
        include_description: Render the description under the heading.
        include_examples: Render the examples block.
        preamble: Optional text inserted before all sections.
        title: Callable mapping a skill to its heading text.
        examples_label: Heading text for the examples block.
    """

    def __init__(
        self,
        *,
        heading_level: int = 1,
        include_description: bool = True,
        include_examples: bool = True,
        preamble: str | None = None,
        title: Callable[[Skill], str] = _default_title,
        examples_label: str = "Examples",
    ) -> None:
        if not 1 <= heading_level <= 6:
            msg = "heading_level must be between 1 and 6"
            raise ValueError(msg)
        self._hashes = "#" * heading_level
        self._include_description = include_description
        self._include_examples = include_examples
        self._preamble = preamble
        self._title = title
        self._examples_label = examples_label

    def _render_one(self, skill: Skill) -> str:
        lines = [f"{self._hashes} {self._title(skill)}"]
        if self._include_description and skill.description:
            lines.append("")
            lines.append(skill.description.strip())
        lines.append("")
        lines.append(skill.instructions.strip())
        if self._include_examples and skill.examples:
            lines.append("")
            lines.append(f"{self._hashes}# {self._examples_label}")
            for example in skill.examples:
                lines.append("")
                lines.append(example.strip())
        return "\n".join(lines)

    def build(self, skills: list[Skill]) -> str:
        if not skills:
            return ""
        blocks = [self._render_one(s) for s in skills]
        if self._preamble:
            blocks.insert(0, self._preamble.strip())
        return "\n\n".join(blocks)
