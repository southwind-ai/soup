"""The :class:`Skill` model, the atomic unit of context in Soup.

A skill follows the open `Agent Skills specification
<https://agentskills.io/specification>`_: it is a small, self-contained chunk
of instructions identified by a ``name`` and a triggering ``description``. Soup
stores many of them and injects only the ones relevant to a given request.

The model carries three groups of fields:

* **Required** (``name``, ``description``, ``instructions``) -- the heart of any
  skill. ``instructions`` is the Markdown body of a ``SKILL.md`` file.
* **Spec fields** (``license``, ``compatibility``, ``metadata``,
  ``allowed_tools``) -- the optional frontmatter defined by the spec.
* **Soup fields** (``tags``, ``examples``, ``priority``, ``dependencies``,
  ``extends``, ``version``) -- Soup's own routing/composition extensions. When a
  skill is loaded from a ``SKILL.md`` file these are read from spec-compliant
  ``metadata`` (or explicit ``register()`` options).

Pydantic (instead of ``dataclasses``) is used on purpose:

* **Validation**: names, descriptions and references are validated at creation
  time -- enforcing the spec's naming/length rules -- surfacing mistakes early
  instead of at prompt-build time.
* **Serialization**: ``model_dump``/``model_validate`` give us free, robust
  (de)serialization, making alternative storage backends trivial.
* **Immutability**: skills are frozen, so they can be safely shared and cached
  across requests without defensive copying.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

#: Spec rule: 1-64 chars, lowercase alphanumerics and single hyphens, no
#: leading/trailing/consecutive hyphens.
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500


class Skill(BaseModel):
    """A modular, reusable unit of LLM context (an Agent Skill).

    Attributes:
        name: Unique skill identifier (e.g. ``"pdf-processing"``). Must follow
            the spec naming rules (lowercase alphanumerics and hyphens, 1-64
            chars, no leading/trailing/consecutive hyphens).
        description: When-and-what summary used as the primary selection signal.
            Required by the spec; 1-1024 characters.
        instructions: The actual context injected into the LLM call -- the
            Markdown body of a ``SKILL.md`` file.
        license: Spec field: license name or reference to a bundled file.
        compatibility: Spec field: environment requirements (<=500 chars).
        allowed_tools: Spec field (``allowed-tools``): pre-approved tools the
            skill may use.
        metadata: Spec field: arbitrary key-value mapping. Soup stores its own
            extensions here when skills are file-loaded (see ``version``,
            ``dependencies``, ``extends``, ``priority``, ``tags``).
        tags: Soup field: keywords used by tag-aware selection strategies.
        examples: Soup field: illustrative snippets appended after instructions.
        priority: Soup field: relative importance. Higher wins ties and is
            reserved for future context-compression. Defaults to ``0``.
        dependencies: Soup field: names of skills that must be included whenever
            this one is selected (companion context).
        extends: Soup field: names of "parent" skills this one specializes.
            Parents are always included and rendered *before* the child.
        version: Soup field: free-form version string for sharing/reuse.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    # -- required ---------------------------------------------------------
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    description: str = Field(min_length=1, max_length=MAX_DESCRIPTION_LENGTH)
    instructions: str = Field(min_length=1)

    # -- spec fields ------------------------------------------------------
    license: str | None = None
    compatibility: str | None = Field(default=None, max_length=MAX_COMPATIBILITY_LENGTH)
    allowed_tools: tuple[str, ...] = ()
    metadata: dict[str, str] = Field(default_factory=dict)

    # -- soup fields ------------------------------------------------------
    tags: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()
    priority: int = 0
    dependencies: tuple[str, ...] = ()
    extends: tuple[str, ...] = ()
    version: str | None = None

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if not NAME_PATTERN.fullmatch(stripped):
            msg = (
                f"Invalid skill name {value!r}: use 1-64 lowercase letters, "
                "numbers and single hyphens (no leading/trailing/consecutive hyphens)"
            )
            raise ValueError(msg)
        return stripped

    @field_validator("tags", "dependencies", "extends", mode="before")
    @classmethod
    def _coerce_csv_sequence(cls, value: Any) -> Any:
        """Normalize list fields, splitting comma-separated strings.

        Strings are the canonical metadata format, so ``"files, http"`` becomes
        ``("files", "http")`` while lists pass through untouched.
        """
        if value is None:
            return ()
        if isinstance(value, str):
            return tuple(item.strip() for item in value.split(",") if item.strip())
        return tuple(value)

    @field_validator("examples", mode="before")
    @classmethod
    def _coerce_examples(cls, value: Any) -> Any:
        """Normalize examples; a bare string is treated as a single example."""
        if value is None:
            return ()
        if isinstance(value, str):
            return (value,)
        return tuple(value)

    @field_validator("allowed_tools", mode="before")
    @classmethod
    def _coerce_tools(cls, value: Any) -> Any:
        """Normalize ``allowed-tools``; the spec uses a space-separated string."""
        if value is None:
            return ()
        if isinstance(value, str):
            return tuple(value.split())
        return tuple(value)

    @field_validator("metadata", mode="before")
    @classmethod
    def _coerce_metadata(cls, value: Any) -> Any:
        """Coerce metadata values to strings (the spec's canonical format)."""
        if value is None:
            return {}
        if isinstance(value, dict):
            return {str(k): str(v) for k, v in value.items()}
        return value

    @property
    def references(self) -> tuple[str, ...]:
        """All skill names this one pulls in (``extends`` first, then deps)."""
        return (*self.extends, *self.dependencies)
