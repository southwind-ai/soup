"""Tests for the dependency/extends resolver."""

from __future__ import annotations

import pytest

from soup import DependencyResolver, InMemoryStorage, MissingDependencyError, Skill


def _skill(name: str, **kwargs: object) -> Skill:
    return Skill(name=name, description="d", instructions="i", **kwargs)  # type: ignore[arg-type]


def _storage(*skills: Skill) -> InMemoryStorage:
    s = InMemoryStorage()
    for skill in skills:
        s.add(skill)
    return s


def test_no_references_returns_input() -> None:
    a = _skill("a")
    resolver = DependencyResolver(_storage(a))
    assert resolver.resolve([a]) == [a]


def test_extends_included_parent_first() -> None:
    frontend = _skill("frontend")
    react = _skill("react", extends=["frontend"])
    resolver = DependencyResolver(_storage(frontend, react))
    out = resolver.resolve([react])
    assert [s.name for s in out] == ["frontend", "react"]


def test_nested_extends() -> None:
    frontend = _skill("frontend")
    react = _skill("react", extends=["frontend"])
    nextjs = _skill("nextjs", extends=["react"])
    resolver = DependencyResolver(_storage(frontend, react, nextjs))
    out = resolver.resolve([nextjs])
    assert [s.name for s in out] == ["frontend", "react", "nextjs"]


def test_dependencies_included() -> None:
    design = _skill("design-system")
    frontend = _skill("frontend", dependencies=["design-system"])
    resolver = DependencyResolver(_storage(design, frontend))
    out = resolver.resolve([frontend])
    assert [s.name for s in out] == ["design-system", "frontend"]


def test_deduplicates_shared_dependency() -> None:
    base = _skill("base")
    a = _skill("a", extends=["base"])
    b = _skill("b", extends=["base"])
    resolver = DependencyResolver(_storage(base, a, b))
    out = resolver.resolve([a, b])
    assert [s.name for s in out] == ["base", "a", "b"]


def test_direct_cycle_terminates() -> None:
    a = _skill("a", extends=["b"])
    b = _skill("b", extends=["a"])
    resolver = DependencyResolver(_storage(a, b))
    out = resolver.resolve([a])
    assert {s.name for s in out} == {"a", "b"}


def test_self_cycle_terminates() -> None:
    a = _skill("a", dependencies=["a"])
    resolver = DependencyResolver(_storage(a))
    out = resolver.resolve([a])
    assert [s.name for s in out] == ["a"]


def test_missing_reference_strict_raises() -> None:
    a = _skill("a", dependencies=["ghost"])
    resolver = DependencyResolver(_storage(a), strict=True)
    with pytest.raises(MissingDependencyError) as exc:
        resolver.resolve([a])
    assert exc.value.missing == "ghost"
    assert exc.value.skill_name == "a"


def test_missing_reference_lenient_skips() -> None:
    a = _skill("a", dependencies=["ghost"])
    resolver = DependencyResolver(_storage(a), strict=False)
    out = resolver.resolve([a])
    assert [s.name for s in out] == ["a"]
