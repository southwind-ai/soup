"""Tests for selection strategies."""

from __future__ import annotations

import pytest

from soup import (
    Harness,
    KeywordStrategy,
    LLMClassifierStrategy,
    TagStrategy,
)


@pytest.fixture
def harnesses() -> list[Harness]:
    return [
        Harness(
            name="frontend",
            instructions="i",
            tags=["react", "ui"],
            description="Build user interfaces",
        ),
        Harness(name="backend", instructions="i", tags=["api", "server"]),
        Harness(name="sql", instructions="i", tags=["database"]),
    ]


# -- KeywordStrategy --------------------------------------------------------


def test_keyword_matches_name(harnesses: list[Harness]) -> None:
    out = KeywordStrategy().select("help me with the backend", harnesses)
    assert [h.name for h in out] == ["backend"]


def test_keyword_matches_tag(harnesses: list[Harness]) -> None:
    out = KeywordStrategy(include_description=False).select("a react thing", harnesses)
    assert [h.name for h in out] == ["frontend"]


def test_keyword_matches_description(harnesses: list[Harness]) -> None:
    out = KeywordStrategy().select("design user interfaces", harnesses)
    assert "frontend" in [h.name for h in out]


def test_keyword_description_can_be_disabled(harnesses: list[Harness]) -> None:
    out = KeywordStrategy(include_description=False).select("interfaces", harnesses)
    assert out == []


def test_keyword_empty_query(harnesses: list[Harness]) -> None:
    assert KeywordStrategy().select("", harnesses) == []


def test_keyword_min_matches() -> None:
    h = Harness(name="api", instructions="i", tags=["rest", "http"])
    strict = KeywordStrategy(include_description=False, min_matches=2)
    assert strict.select("rest", [h]) == []
    assert strict.select("rest http", [h]) == [h]


def test_keyword_invalid_min_matches() -> None:
    with pytest.raises(ValueError, match="min_matches"):
        KeywordStrategy(min_matches=0)


# -- TagStrategy ------------------------------------------------------------


def test_tag_matches_query_token(harnesses: list[Harness]) -> None:
    out = TagStrategy().select("something about database stuff", harnesses)
    assert [h.name for h in out] == ["sql"]


def test_tag_no_match(harnesses: list[Harness]) -> None:
    assert TagStrategy().select("frontend", harnesses) == []  # 'frontend' isn't a tag


def test_tag_explicit_tags(harnesses: list[Harness]) -> None:
    out = TagStrategy(explicit_tags=["api"]).select("", harnesses)
    assert [h.name for h in out] == ["backend"]


def test_tag_empty(harnesses: list[Harness]) -> None:
    assert TagStrategy().select("", harnesses) == []


# -- LLMClassifierStrategy --------------------------------------------------


def test_llm_classifier_selects_returned_names(harnesses: list[Harness]) -> None:
    strat = LLMClassifierStrategy(lambda q, c: ["sql", "backend"])
    out = strat.select("anything", harnesses)
    assert [h.name for h in out] == ["sql", "backend"]


def test_llm_classifier_ignores_unknown_by_default(harnesses: list[Harness]) -> None:
    strat = LLMClassifierStrategy(lambda q, c: ["sql", "ghost"])
    out = strat.select("anything", harnesses)
    assert [h.name for h in out] == ["sql"]


def test_llm_classifier_strict_unknown(harnesses: list[Harness]) -> None:
    strat = LLMClassifierStrategy(lambda q, c: ["ghost"], ignore_unknown_names=False)
    with pytest.raises(ValueError, match="unknown harness"):
        strat.select("anything", harnesses)


def test_llm_classifier_empty_candidates() -> None:
    called = False

    def classifier(q: str, c: list[Harness]) -> list[str]:
        nonlocal called
        called = True
        return []

    assert LLMClassifierStrategy(classifier).select("q", []) == []
    assert called is False
