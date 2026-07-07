"""Tests for the BM25-based selection strategy."""

from __future__ import annotations

from soup import BM25Strategy, Skill


def _skills() -> list[Skill]:
    return [
        Skill(
            name="frontend",
            instructions="Use React 19 and functional components.",
            tags=("react", "ui"),
            description="Frontend engineering guidance",
        ),
        Skill(
            name="backend",
            instructions="Build HTTP APIs and database integrations.",
            tags=("api", "server"),
            description="Backend service design",
        ),
        Skill(
            name="testing",
            instructions="Write pytest unit tests and meaningful integration tests.",
            tags=("tests", "pytest"),
            description="Testing and QA best practices",
        ),
    ]


def test_bm25_selects_relevant_skills() -> None:
    out = BM25Strategy(min_score=0.0).select("help me with react components", _skills())
    assert [s.name for s in out] == ["frontend"]


def test_bm25_ranks_by_relevance() -> None:
    out = BM25Strategy().select("pytest tests", _skills())
    assert out[0].name == "testing"


def test_bm25_top_k_limits_results() -> None:
    out = BM25Strategy(min_score=0.0, top_k=1).select("react api pytest", _skills())
    assert len(out) == 1


def test_bm25_min_score_filters_weak_matches() -> None:
    out = BM25Strategy(min_score=2.0).select("backend", _skills())
    assert out == []


def test_bm25_empty_query_returns_empty() -> None:
    assert BM25Strategy().select("", _skills()) == []


def test_bm25_matches_via_examples_not_description() -> None:
    """Examples act as training phrases, closing vocabulary gaps.

    Uses a multi-skill corpus (rather than a single skill) since BM25's idf
    is degenerate over a corpus of one document: every term looks "common"
    when there is only one document to be rare against.
    """
    sql_skill = Skill(
        name="sql-postgres",
        description="Postgres SQL guidance for query design and indexing.",
        instructions="Use parameterized queries.",
        tags=("sql", "postgres"),
        examples=("my database is slow, what should I check?",),
    )
    other_skill = Skill(
        name="react-ui",
        description="React UI implementation patterns for components and hooks.",
        instructions="Use function components.",
        tags=("react", "ui"),
        examples=("help me speed up my website",),
    )
    out = BM25Strategy().select(
        "My database is slow, what should I check?", [sql_skill, other_skill]
    )
    assert out == [sql_skill]


def test_bm25_ignores_examples_when_absent() -> None:
    skill = Skill(
        name="sql-postgres",
        description="Postgres SQL guidance for query design and indexing.",
        instructions="Use parameterized queries.",
        tags=("sql", "postgres"),
    )
    out = BM25Strategy().select("My database is slow, what should I check?", [skill])
    assert out == []
