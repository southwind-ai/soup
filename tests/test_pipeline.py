"""Tests for the selection pipeline."""

from __future__ import annotations

from soup import Harness, KeywordStrategy, SelectionPipeline, TagStrategy


def _harnesses() -> list[Harness]:
    return [
        Harness(name="frontend", instructions="i", tags=["react"]),
        Harness(name="sql", instructions="i", tags=["database"]),
    ]


def test_empty_pipeline_selects_nothing() -> None:
    assert SelectionPipeline().select("frontend", _harnesses()) == []


def test_pipeline_unions_results() -> None:
    harnesses = _harnesses()
    pipe = SelectionPipeline([KeywordStrategy(), TagStrategy()])
    # 'frontend' hits keyword (name), 'database' hits tag.
    out = pipe.select("frontend database", harnesses)
    assert {h.name for h in out} == {"frontend", "sql"}


def test_pipeline_deduplicates() -> None:
    harnesses = _harnesses()
    # Both strategies match 'react' tag -> still appears once.
    pipe = SelectionPipeline([KeywordStrategy(), TagStrategy()])
    out = pipe.select("react", harnesses)
    assert [h.name for h in out] == ["frontend"]


def test_add_strategy() -> None:
    pipe = SelectionPipeline()
    assert pipe.strategies == []
    pipe.add(TagStrategy())
    assert len(pipe.strategies) == 1


def test_strategies_property_is_copy() -> None:
    pipe = SelectionPipeline([TagStrategy()])
    pipe.strategies.clear()
    assert len(pipe.strategies) == 1
