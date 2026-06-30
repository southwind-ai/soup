"""Tests for the BM25-based selection strategy."""

from __future__ import annotations

from soup import BM25Strategy, Harness


def _harnesses() -> list[Harness]:
    return [
        Harness(
            name="frontend",
            instructions="Use React 19 and functional components.",
            tags=["react", "ui"],
            description="Frontend engineering guidance",
        ),
        Harness(
            name="backend",
            instructions="Build HTTP APIs and database integrations.",
            tags=["api", "server"],
            description="Backend service design",
        ),
        Harness(
            name="testing",
            instructions="Write pytest unit tests and meaningful integration tests.",
            tags=["tests", "pytest"],
            description="Testing and QA best practices",
        ),
    ]


def test_bm25_selects_relevant_harnesses() -> None:
    out = BM25Strategy().select("help me with react components", _harnesses())
    assert [h.name for h in out] == ["frontend"]


def test_bm25_ranks_by_relevance() -> None:
    out = BM25Strategy().select("pytest tests", _harnesses())
    assert out[0].name == "testing"


def test_bm25_top_k_limits_results() -> None:
    out = BM25Strategy(top_k=1).select("react api pytest", _harnesses())
    assert len(out) == 1


def test_bm25_min_score_filters_weak_matches() -> None:
    out = BM25Strategy(min_score=2.0).select("backend", _harnesses())
    assert out == []


def test_bm25_empty_query_returns_empty() -> None:
    assert BM25Strategy().select("", _harnesses()) == []
