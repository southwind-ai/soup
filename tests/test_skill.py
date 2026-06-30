"""Tests for the Skill model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from soup import Skill


def test_minimal_skill() -> None:
    s = Skill(name="react", description="React rules. Use for React.", instructions="Use hooks.")
    assert s.name == "react"
    assert s.instructions == "Use hooks."
    assert s.tags == ()
    assert s.priority == 0
    assert s.metadata == {}


def test_description_is_required() -> None:
    with pytest.raises(ValidationError):
        Skill(name="x", instructions="i")  # type: ignore[call-arg]


def test_empty_description_rejected() -> None:
    with pytest.raises(ValidationError):
        Skill(name="x", description="", instructions="i")


def test_description_max_length() -> None:
    with pytest.raises(ValidationError):
        Skill(name="x", description="d" * 1025, instructions="i")


def test_compatibility_max_length() -> None:
    with pytest.raises(ValidationError):
        Skill(name="x", description="d", instructions="i", compatibility="c" * 501)


@pytest.mark.parametrize("name", ["pdf-processing", "react", "data2vec", "a", "x9-y9"])
def test_valid_names(name: str) -> None:
    assert Skill(name=name, description="d", instructions="i").name == name


@pytest.mark.parametrize(
    "name",
    ["React", "-react", "react-", "re--act", "with space", "under_score", "a" * 65, ""],
)
def test_invalid_names_rejected(name: str) -> None:
    with pytest.raises(ValidationError):
        Skill(name=name, description="d", instructions="i")


def test_name_is_stripped() -> None:
    assert Skill(name="  react  ", description="d", instructions="i").name == "react"


def test_sequences_accept_lists_and_strings() -> None:
    s = Skill(name="x", description="d", instructions="i", tags=["a", "b"], extends="parent")
    assert s.tags == ("a", "b")
    assert s.extends == ("parent",)


def test_list_fields_split_comma_separated_strings() -> None:
    s = Skill(
        name="x",
        description="d",
        instructions="i",
        tags="pdf, forms",
        dependencies="files,http",
        extends="base",
    )
    assert s.tags == ("pdf", "forms")
    assert s.dependencies == ("files", "http")
    assert s.extends == ("base",)


def test_allowed_tools_space_separated_string() -> None:
    s = Skill(name="x", description="d", instructions="i", allowed_tools="Read Bash Write")
    assert s.allowed_tools == ("Read", "Bash", "Write")


def test_metadata_values_coerced_to_strings() -> None:
    s = Skill(name="x", description="d", instructions="i", metadata={"version": 1, "k": True})
    assert s.metadata == {"version": "1", "k": "True"}


def test_references_order_extends_then_dependencies() -> None:
    s = Skill(
        name="x",
        description="d",
        instructions="i",
        extends=["base"],
        dependencies=["dep"],
    )
    assert s.references == ("base", "dep")


def test_empty_instructions_rejected() -> None:
    with pytest.raises(ValidationError):
        Skill(name="x", description="d", instructions="")


def test_skill_is_frozen() -> None:
    s = Skill(name="x", description="d", instructions="i")
    with pytest.raises(ValidationError):
        s.name = "y"  # type: ignore[misc]


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        Skill(name="x", description="d", instructions="i", unknown="nope")  # type: ignore[call-arg]


def test_none_sequence_coerced_to_empty() -> None:
    s = Skill(name="x", description="d", instructions="i", tags=None)  # type: ignore[arg-type]
    assert s.tags == ()


def test_roundtrip_serialization() -> None:
    s = Skill(
        name="x",
        description="d",
        instructions="i",
        tags=["a"],
        version="1.0",
        priority=5,
        license="MIT",
        allowed_tools=["Read"],
    )
    data = s.model_dump()
    restored = Skill.model_validate(data)
    assert restored == s
