"""Tests for storage backends."""

from __future__ import annotations

from soup import Harness, InMemoryStorage


def _h(name: str) -> Harness:
    return Harness(name=name, instructions="i")


def test_add_and_get() -> None:
    s = InMemoryStorage()
    s.add(_h("a"))
    assert s.get("a") is not None
    assert s.get("missing") is None


def test_add_overwrites() -> None:
    s = InMemoryStorage()
    s.add(Harness(name="a", instructions="first"))
    s.add(Harness(name="a", instructions="second"))
    assert len(s) == 1
    got = s.get("a")
    assert got is not None
    assert got.instructions == "second"


def test_remove() -> None:
    s = InMemoryStorage()
    s.add(_h("a"))
    assert s.remove("a") is True
    assert s.remove("a") is False


def test_all_preserves_insertion_order() -> None:
    s = InMemoryStorage()
    for name in ["c", "a", "b"]:
        s.add(_h(name))
    assert [h.name for h in s.all()] == ["c", "a", "b"]


def test_clear() -> None:
    s = InMemoryStorage()
    s.add(_h("a"))
    s.clear()
    assert len(s) == 0


def test_dunder_helpers() -> None:
    s = InMemoryStorage()
    s.add(_h("a"))
    assert "a" in s
    assert "missing" not in s
    assert 123 not in s  # type: ignore[comparison-overlap]
    assert len(s) == 1
    assert [h.name for h in s] == ["a"]
