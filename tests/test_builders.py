"""Tests for context builders."""

from __future__ import annotations

import pytest

from soup import MarkdownContextBuilder, Skill


def _skill(name: str, instructions: str, **kwargs: object) -> Skill:
    kwargs.setdefault("description", "d")
    return Skill(name=name, instructions=instructions, **kwargs)  # type: ignore[arg-type]


def test_empty_returns_empty_string() -> None:
    assert MarkdownContextBuilder().build([]) == ""


def test_single_skill() -> None:
    s = Skill(name="frontend", description="d", instructions="Use React 19.")
    out = MarkdownContextBuilder(include_description=False).build([s])
    assert out == "# Frontend\n\nUse React 19."


def test_title_humanizes_name() -> None:
    s = _skill("api-design", "i")
    out = MarkdownContextBuilder().build([s])
    assert out.startswith("# Api Design")


def test_description_included() -> None:
    s = Skill(name="x", description="A summary", instructions="do it")
    out = MarkdownContextBuilder().build([s])
    assert "A summary" in out
    assert out.index("A summary") < out.index("do it")


def test_description_can_be_disabled() -> None:
    s = Skill(name="x", description="A summary", instructions="do it")
    out = MarkdownContextBuilder(include_description=False).build([s])
    assert "A summary" not in out


def test_examples_rendered() -> None:
    s = _skill("x", "i", examples=["ex1", "ex2"])
    out = MarkdownContextBuilder(include_description=False).build([s])
    assert "## Examples" in out
    assert "ex1" in out
    assert "ex2" in out


def test_examples_can_be_disabled() -> None:
    s = _skill("x", "i", examples=["ex1"])
    out = MarkdownContextBuilder(include_examples=False).build([s])
    assert "ex1" not in out


def test_heading_level() -> None:
    s = _skill("x", "i")
    out = MarkdownContextBuilder(heading_level=3).build([s])
    assert out.startswith("### X")


def test_invalid_heading_level() -> None:
    with pytest.raises(ValueError, match="heading_level"):
        MarkdownContextBuilder(heading_level=0)


def test_preamble() -> None:
    s = _skill("x", "i")
    out = MarkdownContextBuilder(preamble="GUIDELINES").build([s])
    assert out.startswith("GUIDELINES")


def test_custom_title() -> None:
    s = _skill("x", "i")
    out = MarkdownContextBuilder(title=lambda sk: sk.name.upper()).build([s])
    assert out.startswith("# X")


def test_multiple_skills_separated() -> None:
    a = Skill(name="a", description="d", instructions="ia")
    b = Skill(name="b", description="d", instructions="ib")
    out = MarkdownContextBuilder(include_description=False).build([a, b])
    assert out == "# A\n\nia\n\n# B\n\nib"
