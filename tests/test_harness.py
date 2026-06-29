"""Tests for the Harness model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from soup import Harness


def test_minimal_harness() -> None:
    h = Harness(name="react", instructions="Use hooks.")
    assert h.name == "react"
    assert h.instructions == "Use hooks."
    assert h.tags == ()
    assert h.priority == 0
    assert h.metadata == {}


def test_sequences_accept_lists_and_strings() -> None:
    h = Harness(name="x", instructions="i", tags=["a", "b"], extends="parent")
    assert h.tags == ("a", "b")
    assert h.extends == ("parent",)


def test_references_order_extends_then_dependencies() -> None:
    h = Harness(
        name="x",
        instructions="i",
        extends=["base"],
        dependencies=["dep"],
    )
    assert h.references == ("base", "dep")


def test_name_is_stripped() -> None:
    assert Harness(name="  react  ", instructions="i").name == "react"


def test_blank_name_rejected() -> None:
    with pytest.raises(ValidationError):
        Harness(name="   ", instructions="i")


def test_empty_instructions_rejected() -> None:
    with pytest.raises(ValidationError):
        Harness(name="x", instructions="")


def test_harness_is_frozen() -> None:
    h = Harness(name="x", instructions="i")
    with pytest.raises(ValidationError):
        h.name = "y"  # type: ignore[misc]


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        Harness(name="x", instructions="i", unknown="nope")  # type: ignore[call-arg]


def test_none_sequence_coerced_to_empty() -> None:
    h = Harness(name="x", instructions="i", tags=None)  # type: ignore[arg-type]
    assert h.tags == ()


def test_roundtrip_serialization() -> None:
    h = Harness(name="x", instructions="i", tags=["a"], version="1.0", priority=5)
    data = h.model_dump()
    restored = Harness.model_validate(data)
    assert restored == h
