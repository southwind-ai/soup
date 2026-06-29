"""Small text helpers shared by selection strategies."""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> set[str]:
    """Lower-case ``text`` and split it into a set of alphanumeric tokens.

    Args:
        text: Arbitrary input text.

    Returns:
        The set of distinct lowercase tokens.
    """
    return set(_TOKEN_RE.findall(text.lower()))


def normalize(text: str) -> str:
    """Return a lowercase, whitespace-collapsed version of ``text``."""
    return " ".join(text.lower().split())
