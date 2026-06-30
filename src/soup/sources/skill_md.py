"""Parsing of ``SKILL.md`` files into :class:`~soup.models.skill.Skill` objects.

A ``SKILL.md`` file is YAML frontmatter (between ``---`` fences) followed by a
Markdown body, per the `Agent Skills spec <https://agentskills.io/specification>`_::

    ---
    name: pdf-processing
    description: Extract PDF text, fill forms, and merge files. Use for PDF tasks.
    metadata:
      version: "1.0"
      dependencies: "files"
      tags: "pdf, forms"
    ---

    Use pypdf for extraction...

The frontmatter supplies the spec fields (``name``, ``description``,
``license``, ``compatibility``, ``allowed-tools``, ``metadata``). The Markdown
body becomes the skill's ``instructions``. Soup's own routing extensions
(``version``, ``dependencies``, ``extends``, ``priority``, ``tags``) are read
from spec-compliant ``metadata`` and may be overridden by explicit
``register()`` options.
"""

from __future__ import annotations

import re
from typing import Any

import yaml

from soup.core.exceptions import SkillParseError
from soup.models.skill import (
    MAX_DESCRIPTION_LENGTH,
    MAX_NAME_LENGTH,
    NAME_PATTERN,
    Skill,
)

#: Soup routing extensions, read from ``metadata`` (or ``register()`` options).
_SOUP_FIELDS = frozenset({"version", "dependencies", "extends", "priority", "tags"})

_FRONTMATTER_RE = re.compile(
    r"\A\ufeff?---[ \t]*\r?\n(?P<frontmatter>.*?)\r?\n---[ \t]*\r?\n?(?P<body>.*)\Z",
    re.DOTALL,
)


def split_frontmatter(text: str) -> tuple[str, str]:
    """Split ``text`` into its raw YAML frontmatter and Markdown body.

    Raises:
        SkillParseError: If ``text`` lacks a leading ``---`` fenced block.
    """
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        msg = "SKILL.md must start with a YAML frontmatter block delimited by '---'"
        raise SkillParseError(msg)
    return match.group("frontmatter"), match.group("body")


def parse_skill_md(
    text: str,
    *,
    dir_name: str | None = None,
    overrides: dict[str, Any] | None = None,
) -> Skill:
    """Parse the contents of a ``SKILL.md`` file into a :class:`Skill`.

    Args:
        text: The full ``SKILL.md`` contents (frontmatter + Markdown body).
        dir_name: The skill's parent directory name. When given, the spec rule
            "name must match the directory name" is enforced.
        overrides: Explicit Soup field values (from ``register()``) that take
            precedence over anything read from ``metadata``.

    Returns:
        The parsed, validated skill. The Markdown body becomes ``instructions``.

    Raises:
        SkillParseError: If the frontmatter is missing/invalid, required fields
            are absent, the name/description violate the spec, or the name does
            not match ``dir_name``.
    """
    raw_frontmatter, body = split_frontmatter(text)

    try:
        loaded = yaml.safe_load(raw_frontmatter)
    except yaml.YAMLError as exc:  # pragma: no cover - exercised via parser tests
        msg = f"Invalid YAML frontmatter: {exc}"
        raise SkillParseError(msg) from exc

    if loaded is None:
        loaded = {}
    if not isinstance(loaded, dict):
        msg = "SKILL.md frontmatter must be a YAML mapping"
        raise SkillParseError(msg)
    frontmatter: dict[str, Any] = {str(k): v for k, v in loaded.items()}

    # Unknown top-level frontmatter keys are ignored.

    name = frontmatter.get("name")
    if not isinstance(name, str) or not name.strip():
        msg = "SKILL.md frontmatter must define a non-empty 'name'"
        raise SkillParseError(msg)
    name = name.strip()
    if len(name) > MAX_NAME_LENGTH or not NAME_PATTERN.fullmatch(name):
        msg = (
            f"Invalid skill name {name!r}: use 1-64 lowercase letters, numbers "
            "and single hyphens (no leading/trailing/consecutive hyphens)"
        )
        raise SkillParseError(msg)
    if dir_name is not None and name != dir_name:
        msg = f"Skill name {name!r} must match its directory name {dir_name!r}"
        raise SkillParseError(msg)

    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        msg = "SKILL.md frontmatter must define a non-empty 'description'"
        raise SkillParseError(msg)
    if len(description) > MAX_DESCRIPTION_LENGTH:
        msg = f"Description exceeds {MAX_DESCRIPTION_LENGTH} characters"
        raise SkillParseError(msg)

    instructions = body.strip()
    if not instructions:
        msg = "SKILL.md must have a non-empty Markdown body (the instructions)"
        raise SkillParseError(msg)

    metadata = _normalize_metadata(frontmatter.get("metadata"))

    fields: dict[str, Any] = {
        "name": name,
        "description": description,
        "instructions": instructions,
        "metadata": metadata,
    }
    if frontmatter.get("license") is not None:
        fields["license"] = frontmatter["license"]
    if frontmatter.get("compatibility") is not None:
        fields["compatibility"] = frontmatter["compatibility"]
    if frontmatter.get("allowed-tools") is not None:
        fields["allowed_tools"] = frontmatter["allowed-tools"]

    # Soup extensions: metadata first, then explicit register() overrides win.
    for key in _SOUP_FIELDS:
        if key in metadata:
            fields[key] = metadata[key]
    if overrides:
        for key, value in overrides.items():
            if value is not None:
                fields[key] = value

    try:
        return Skill(**fields)
    except ValueError as exc:
        msg = f"Invalid skill {name!r}: {exc}"
        raise SkillParseError(msg) from exc


def _normalize_metadata(value: Any) -> dict[str, str]:
    """Coerce a frontmatter ``metadata`` mapping to ``dict[str, str]``."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        msg = "'metadata' must be a mapping of string keys to string values"
        raise SkillParseError(msg)
    return {str(k): str(v) for k, v in value.items()}
