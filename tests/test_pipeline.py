"""Tests for the selection pipeline."""

from __future__ import annotations

from soup import Harness, SelectionPipeline, SelectionStrategy


def _harnesses() -> list[Harness]:
    return [
        Harness(name="frontend", instructions="i", tags=["react"]),
        Harness(name="sql", instructions="i", tags=["database"]),
    ]


class _NameMatchStrategy(SelectionStrategy):
    def __init__(self, *names: str) -> None:
        self._names = set(names)

    def select(self, query: str, harnesses: list[Harness]) -> list[Harness]:
        _ = query
        return [h for h in harnesses if h.name in self._names]


def test_empty_pipeline_selects_nothing() -> None:
    assert SelectionPipeline().select("frontend", _harnesses()) == []


def test_pipeline_unions_results() -> None:
    harnesses = _harnesses()
    pipe = SelectionPipeline([_NameMatchStrategy("frontend"), _NameMatchStrategy("sql")])
    out = pipe.select("whatever", harnesses)
    assert {h.name for h in out} == {"frontend", "sql"}


def test_pipeline_deduplicates() -> None:
    harnesses = _harnesses()
    pipe = SelectionPipeline([_NameMatchStrategy("frontend"), _NameMatchStrategy("frontend")])
    out = pipe.select("whatever", harnesses)
    assert [h.name for h in out] == ["frontend"]


def test_add_strategy() -> None:
    pipe = SelectionPipeline()
    assert pipe.strategies == []
    pipe.add(_NameMatchStrategy("frontend"))
    assert len(pipe.strategies) == 1


def test_strategies_property_is_copy() -> None:
    pipe = SelectionPipeline([_NameMatchStrategy("frontend")])
    pipe.strategies.clear()
    assert len(pipe.strategies) == 1
