"""Tests for the Soup facade."""

from __future__ import annotations

import pytest

from soup import (
    Harness,
    MarkdownContextBuilder,
    SelectionPipeline,
    Soup,
)
from soup.strategies.base import SelectionStrategy


class _SelectByName(SelectionStrategy):
    def __init__(self, *names: str) -> None:
        self._names = set(names)

    def select(self, query: str, harnesses: list[Harness]) -> list[Harness]:
        _ = query
        return [h for h in harnesses if h.name in self._names]


def test_register_with_kwargs() -> None:
    soup = Soup()
    h = soup.register(name="frontend", instructions="Use React.")
    assert h.name == "frontend"
    assert soup.get("frontend") is h


def test_register_with_instance() -> None:
    soup = Soup()
    h = Harness(name="x", instructions="i")
    assert soup.register(h) is h
    assert soup.get("x") == h


def test_register_instance_and_fields_conflict() -> None:
    soup = Soup()
    with pytest.raises(ValueError, match="not both"):
        soup.register(Harness(name="x", instructions="i"), name="y")  # type: ignore[call-overload]


def test_register_metadata_none_is_dropped() -> None:
    soup = Soup()
    h = soup.register(name="x", instructions="i", metadata=None)
    assert h.metadata == {}


def test_register_many_and_unregister() -> None:
    soup = Soup()
    soup.register_many([Harness(name="a", instructions="i"), Harness(name="b", instructions="i")])
    assert {h.name for h in soup.harnesses} == {"a", "b"}
    assert soup.unregister("a") is True
    assert soup.unregister("a") is False


def test_prepare_string_injects_relevant_only() -> None:
    soup = Soup()
    soup.register(name="frontend", instructions="Use React 19.", tags=["react"])
    soup.register(name="sql", instructions="Use indexes.", tags=["database"])
    out = soup.prepare("help with my react component")
    assert "Use React 19." in out
    assert "Use indexes." not in out


def test_prepare_messages_returns_messages() -> None:
    soup = Soup()
    soup.register(name="frontend", instructions="Use React 19.", tags=["react"])
    out = soup.prepare([{"role": "user", "content": "react please"}])
    assert isinstance(out, list)
    assert out[0]["role"] == "system"
    assert "Use React 19." in out[0]["content"]


def test_prepare_no_match_is_passthrough() -> None:
    soup = Soup()
    soup.register(name="frontend", instructions="Use React 19.", tags=["react"])
    assert soup.prepare("completely unrelated topic") == "completely unrelated topic"


def test_prepare_resolves_extends() -> None:
    soup = Soup()
    soup.register(name="frontend", instructions="Accessibility first.")
    soup.register(name="react", instructions="Use hooks.", tags=["react"], extends=["frontend"])
    out = soup.prepare("a react question")
    assert "Accessibility first." in out
    assert "Use hooks." in out
    assert out.index("Accessibility first.") < out.index("Use hooks.")


def test_select_orders_by_priority() -> None:
    soup = Soup()
    soup.register(name="low", instructions="i", tags=["x"], priority=1)
    soup.register(name="high", instructions="i", tags=["x"], priority=10)
    selected = soup.select("x")
    assert [h.name for h in selected] == ["high", "low"]


def test_add_strategy() -> None:
    soup = Soup(strategies=[])
    soup.register(name="frontend", instructions="i", tags=["react"])
    assert soup.select("react") == []
    soup.add_strategy(_SelectByName("frontend"))
    assert [h.name for h in soup.select("react")] == ["frontend"]


def test_custom_pipeline() -> None:
    pipeline = SelectionPipeline([_SelectByName("frontend")])
    soup = Soup(pipeline=pipeline)
    soup.register(name="frontend", instructions="i", tags=["react"])
    assert [h.name for h in soup.select("react")] == ["frontend"]


def test_custom_builder() -> None:
    soup = Soup(builder=MarkdownContextBuilder(heading_level=2))
    soup.register(name="frontend", instructions="Use React.", tags=["react"])
    out = soup.build_context("react")
    assert out.startswith("## Frontend")


def test_custom_strategy_integration() -> None:
    soup = Soup(strategies=[_SelectByName("frontend")])
    soup.register(name="frontend", instructions="Use React.")
    soup.register(name="sql", instructions="Use indexes.")
    out = soup.build_context("anything")
    assert "Use React." in out
    assert "Use indexes." not in out


def test_strict_dependencies_default_raises_on_prepare() -> None:
    from soup import MissingDependencyError

    soup = Soup()
    soup.register(name="frontend", instructions="i", tags=["react"], dependencies=["ghost"])
    with pytest.raises(MissingDependencyError):
        soup.prepare("react")


def test_non_strict_dependencies() -> None:
    soup = Soup(strict_dependencies=False)
    soup.register(
        name="frontend", instructions="Use React.", tags=["react"], dependencies=["ghost"]
    )
    out = soup.prepare("react")
    assert "Use React." in out
