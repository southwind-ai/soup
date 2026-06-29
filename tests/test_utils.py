"""Tests for text utilities."""

from __future__ import annotations

from soup.utils import normalize, tokenize


def test_tokenize_lowercases_and_splits() -> None:
    assert tokenize("React-19 and FastAPI!") == {"react", "19", "and", "fastapi"}


def test_tokenize_empty() -> None:
    assert tokenize("") == set()


def test_normalize_collapses_whitespace_and_lowercases() -> None:
    assert normalize("  Hello   WORLD\n") == "hello world"
