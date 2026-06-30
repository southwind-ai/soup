"""Tests for the selection pipeline."""

from __future__ import annotations

from soup import SelectionPipeline, SelectionStrategy, Skill


def _skills() -> list[Skill]:
    return [
        Skill(name="frontend", description="d", instructions="i", tags=("react",)),
        Skill(name="sql", description="d", instructions="i", tags=("database",)),
    ]


class _NameMatchStrategy(SelectionStrategy):
    def __init__(self, *names: str) -> None:
        self._names = set(names)

    def select(self, query: str, skills: list[Skill]) -> list[Skill]:
        _ = query
        return [s for s in skills if s.name in self._names]


def test_empty_pipeline_selects_nothing() -> None:
    assert SelectionPipeline().select("frontend", _skills()) == []


def test_pipeline_unions_results() -> None:
    skills = _skills()
    pipe = SelectionPipeline([_NameMatchStrategy("frontend"), _NameMatchStrategy("sql")])
    out = pipe.select("whatever", skills)
    assert {s.name for s in out} == {"frontend", "sql"}


def test_pipeline_deduplicates() -> None:
    skills = _skills()
    pipe = SelectionPipeline([_NameMatchStrategy("frontend"), _NameMatchStrategy("frontend")])
    out = pipe.select("whatever", skills)
    assert [s.name for s in out] == ["frontend"]


def test_add_strategy() -> None:
    pipe = SelectionPipeline()
    assert pipe.strategies == []
    pipe.add(_NameMatchStrategy("frontend"))
    assert len(pipe.strategies) == 1


def test_strategies_property_is_copy() -> None:
    pipe = SelectionPipeline([_NameMatchStrategy("frontend")])
    pipe.strategies.clear()
    assert len(pipe.strategies) == 1
