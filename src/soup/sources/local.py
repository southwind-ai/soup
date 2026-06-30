"""Loading skills from the local filesystem.

Two shapes are supported, matching the spec's on-disk layout:

* a **skill directory** -- a folder containing a ``SKILL.md`` file, and
* a **skills collection** -- a folder whose immediate children are skill
  directories.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from soup.core.exceptions import SkillSourceError
from soup.models.skill import Skill
from soup.sources.skill_md import parse_skill_md

SKILL_FILENAME = "SKILL.md"


def is_skill_dir(path: Path) -> bool:
    """Return whether ``path`` is a directory containing a ``SKILL.md`` file."""
    return path.is_dir() and (path / SKILL_FILENAME).is_file()


def load_skill_dir(path: Path, *, overrides: dict[str, Any] | None = None) -> Skill:
    """Load the single skill defined by the ``SKILL.md`` in ``path``.

    Args:
        path: A directory containing a ``SKILL.md`` file.
        overrides: Explicit Soup field values that win over file ``metadata``.

    Raises:
        SkillSourceError: If ``path`` is not a skill directory.
    """
    if not is_skill_dir(path):
        msg = f"{path} is not a skill directory (no {SKILL_FILENAME})"
        raise SkillSourceError(msg)
    text = (path / SKILL_FILENAME).read_text(encoding="utf-8")
    return parse_skill_md(text, dir_name=path.name, overrides=overrides)


def load_skills_collection(
    path: Path,
    *,
    options: dict[str, dict[str, Any]] | None = None,
) -> list[Skill]:
    """Load every skill directory directly under ``path``.

    Args:
        path: A directory whose immediate children are skill directories.
        options: Per-skill Soup field overrides keyed by skill name.

    Returns:
        The loaded skills in sorted directory-name order (deterministic).

    Raises:
        SkillSourceError: If ``path`` is not a directory or has no skills.
    """
    if not path.is_dir():
        msg = f"{path} is not a directory"
        raise SkillSourceError(msg)

    options = options or {}
    skills: list[Skill] = []
    for child in sorted(path.iterdir(), key=lambda p: p.name):
        if not is_skill_dir(child):
            continue
        skills.append(load_skill_dir(child, overrides=options.get(child.name)))

    if not skills:
        msg = f"No skill directories (containing {SKILL_FILENAME}) found under {path}"
        raise SkillSourceError(msg)
    return skills


def load_local(
    path: Path,
    *,
    overrides: dict[str, Any] | None = None,
    options: dict[str, dict[str, Any]] | None = None,
) -> list[Skill]:
    """Load skills from ``path``, auto-detecting directory vs. collection.

    A directory containing ``SKILL.md`` is loaded as a single skill (with
    ``overrides`` applied); otherwise it is treated as a collection (with
    per-skill ``options`` applied).
    """
    if is_skill_dir(path):
        return [load_skill_dir(path, overrides=overrides)]
    return load_skills_collection(path, options=options)
