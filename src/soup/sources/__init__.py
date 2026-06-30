"""Skill sources: load skills from the filesystem or remote repositories."""

from soup.sources.local import (
    is_skill_dir,
    load_local,
    load_skill_dir,
    load_skills_collection,
)
from soup.sources.remote import is_remote_url, load_remote
from soup.sources.skill_md import parse_skill_md, split_frontmatter

__all__ = [
    "is_remote_url",
    "is_skill_dir",
    "load_local",
    "load_remote",
    "load_skill_dir",
    "load_skills_collection",
    "parse_skill_md",
    "split_frontmatter",
]
