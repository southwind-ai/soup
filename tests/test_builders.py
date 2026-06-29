"""Tests for context builders."""

from __future__ import annotations

import pytest

from soup import Harness, MarkdownContextBuilder


def test_empty_returns_empty_string() -> None:
    assert MarkdownContextBuilder().build([]) == ""


def test_single_harness() -> None:
    h = Harness(name="frontend", instructions="Use React 19.")
    out = MarkdownContextBuilder().build([h])
    assert out == "# Frontend\n\nUse React 19."


def test_title_humanizes_name() -> None:
    h = Harness(name="api-design", instructions="i")
    out = MarkdownContextBuilder().build([h])
    assert out.startswith("# Api Design")


def test_description_included() -> None:
    h = Harness(name="x", instructions="do it", description="A summary")
    out = MarkdownContextBuilder().build([h])
    assert "A summary" in out
    assert out.index("A summary") < out.index("do it")


def test_description_can_be_disabled() -> None:
    h = Harness(name="x", instructions="do it", description="A summary")
    out = MarkdownContextBuilder(include_description=False).build([h])
    assert "A summary" not in out


def test_examples_rendered() -> None:
    h = Harness(name="x", instructions="i", examples=["ex1", "ex2"])
    out = MarkdownContextBuilder().build([h])
    assert "## Examples" in out
    assert "ex1" in out
    assert "ex2" in out


def test_examples_can_be_disabled() -> None:
    h = Harness(name="x", instructions="i", examples=["ex1"])
    out = MarkdownContextBuilder(include_examples=False).build([h])
    assert "ex1" not in out


def test_heading_level() -> None:
    h = Harness(name="x", instructions="i")
    out = MarkdownContextBuilder(heading_level=3).build([h])
    assert out.startswith("### X")


def test_invalid_heading_level() -> None:
    with pytest.raises(ValueError, match="heading_level"):
        MarkdownContextBuilder(heading_level=0)


def test_preamble() -> None:
    h = Harness(name="x", instructions="i")
    out = MarkdownContextBuilder(preamble="GUIDELINES").build([h])
    assert out.startswith("GUIDELINES")


def test_custom_title() -> None:
    h = Harness(name="x", instructions="i")
    out = MarkdownContextBuilder(title=lambda hh: hh.name.upper()).build([h])
    assert out.startswith("# X")


def test_multiple_harnesses_separated() -> None:
    a = Harness(name="a", instructions="ia")
    b = Harness(name="b", instructions="ib")
    out = MarkdownContextBuilder().build([a, b])
    assert out == "# A\n\nia\n\n# B\n\nib"
