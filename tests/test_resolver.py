"""Tests for the dependency/extends resolver."""

from __future__ import annotations

import pytest

from soup import DependencyResolver, Harness, InMemoryStorage, MissingDependencyError


def _storage(*harnesses: Harness) -> InMemoryStorage:
    s = InMemoryStorage()
    for h in harnesses:
        s.add(h)
    return s


def test_no_references_returns_input() -> None:
    a = Harness(name="a", instructions="i")
    resolver = DependencyResolver(_storage(a))
    assert resolver.resolve([a]) == [a]


def test_extends_included_parent_first() -> None:
    frontend = Harness(name="frontend", instructions="i")
    react = Harness(name="react", instructions="i", extends=["frontend"])
    resolver = DependencyResolver(_storage(frontend, react))
    out = resolver.resolve([react])
    assert [h.name for h in out] == ["frontend", "react"]


def test_nested_extends() -> None:
    frontend = Harness(name="frontend", instructions="i")
    react = Harness(name="react", instructions="i", extends=["frontend"])
    nextjs = Harness(name="nextjs", instructions="i", extends=["react"])
    resolver = DependencyResolver(_storage(frontend, react, nextjs))
    out = resolver.resolve([nextjs])
    assert [h.name for h in out] == ["frontend", "react", "nextjs"]


def test_dependencies_included() -> None:
    design = Harness(name="design-system", instructions="i")
    frontend = Harness(name="frontend", instructions="i", dependencies=["design-system"])
    resolver = DependencyResolver(_storage(design, frontend))
    out = resolver.resolve([frontend])
    assert [h.name for h in out] == ["design-system", "frontend"]


def test_deduplicates_shared_dependency() -> None:
    base = Harness(name="base", instructions="i")
    a = Harness(name="a", instructions="i", extends=["base"])
    b = Harness(name="b", instructions="i", extends=["base"])
    resolver = DependencyResolver(_storage(base, a, b))
    out = resolver.resolve([a, b])
    assert [h.name for h in out] == ["base", "a", "b"]


def test_direct_cycle_terminates() -> None:
    a = Harness(name="a", instructions="i", extends=["b"])
    b = Harness(name="b", instructions="i", extends=["a"])
    resolver = DependencyResolver(_storage(a, b))
    out = resolver.resolve([a])
    assert {h.name for h in out} == {"a", "b"}


def test_self_cycle_terminates() -> None:
    a = Harness(name="a", instructions="i", dependencies=["a"])
    resolver = DependencyResolver(_storage(a))
    out = resolver.resolve([a])
    assert [h.name for h in out] == ["a"]


def test_missing_reference_strict_raises() -> None:
    a = Harness(name="a", instructions="i", dependencies=["ghost"])
    resolver = DependencyResolver(_storage(a), strict=True)
    with pytest.raises(MissingDependencyError) as exc:
        resolver.resolve([a])
    assert exc.value.missing == "ghost"
    assert exc.value.harness_name == "a"


def test_missing_reference_lenient_skips() -> None:
    a = Harness(name="a", instructions="i", dependencies=["ghost"])
    resolver = DependencyResolver(_storage(a), strict=False)
    out = resolver.resolve([a])
    assert [h.name for h in out] == ["a"]
