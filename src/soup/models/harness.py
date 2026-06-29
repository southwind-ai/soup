"""The :class:`Harness` model, the atomic unit of context in Soup.

A harness is a small, self-contained chunk of instructions (a skill, a best
practice, a coding rule). Soup stores many of them and injects only the ones
relevant to a given request.

Pydantic (instead of ``dataclasses``) is used on purpose:

* **Validation**: priorities, names and references are validated at creation
  time, surfacing mistakes early instead of at prompt-build time.
* **Serialization**: ``model_dump``/``model_validate`` give us free, robust
  (de)serialization. This is what makes future YAML / database / Redis storage
  backends trivial -- they just round-trip dicts.
* **Immutability**: harnesses are frozen, so they can be safely shared and
  cached across requests without defensive copying.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Harness(BaseModel):
    """A modular, reusable unit of LLM context.

    Attributes:
        name: Unique identifier of the harness (e.g. ``"react"``).
        description: Human-readable summary, also used as a selection signal.
        tags: Keywords used by tag-based selection strategies.
        instructions: The actual context injected into the LLM call.
        examples: Optional illustrative snippets appended after instructions.
        priority: Relative importance. Higher wins ties and is reserved for
            future context-compression. Defaults to ``0``.
        dependencies: Names of harnesses that must be included whenever this
            one is selected (companion context).
        extends: Names of "parent" harnesses this one specializes. Parents are
            always included and rendered *before* the child, enabling
            composition hierarchies (``nextjs`` -> ``react`` -> ``frontend``).
        version: Free-form version string, useful for sharing/reusing harnesses
            across projects.
        metadata: Arbitrary user data, ignored by the core but available to
            custom strategies and builders.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    instructions: str = Field(min_length=1)
    description: str | None = None
    tags: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()
    priority: int = 0
    dependencies: tuple[str, ...] = ()
    extends: tuple[str, ...] = ()
    version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            msg = "Harness name must not be blank"
            raise ValueError(msg)
        return stripped

    @field_validator("tags", "examples", "dependencies", "extends", mode="before")
    @classmethod
    def _coerce_sequence(cls, value: Any) -> Any:
        """Accept lists (the ergonomic public API) and normalize to tuples."""
        if value is None:
            return ()
        if isinstance(value, str):
            return (value,)
        return tuple(value)

    @property
    def references(self) -> tuple[str, ...]:
        """All harness names this one pulls in (``extends`` first, then deps)."""
        return (*self.extends, *self.dependencies)
