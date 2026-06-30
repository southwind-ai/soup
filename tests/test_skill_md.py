"""Tests for the SKILL.md parser, including spec validation and metadata mapping."""

from __future__ import annotations

import textwrap

import pytest

from soup import SkillParseError, parse_skill_md


def _doc(frontmatter: str, body: str = "Use pypdf for extraction.") -> str:
    return f"---\n{textwrap.dedent(frontmatter).strip()}\n---\n\n{body}\n"


# -- valid parsing ----------------------------------------------------------


def test_parses_minimal_valid_skill() -> None:
    skill = parse_skill_md(
        _doc(
            """
            name: pdf-processing
            description: Extract PDF text, fill forms. Use for PDF tasks.
            """
        )
    )
    assert skill.name == "pdf-processing"
    assert skill.description.startswith("Extract PDF text")
    assert skill.instructions == "Use pypdf for extraction."


def test_body_becomes_instructions() -> None:
    doc = _doc("name: x\ndescription: A skill. Use it.", body="Line one.\nLine two.")
    skill = parse_skill_md(doc)
    assert skill.instructions == "Line one.\nLine two."


def test_parses_spec_fields() -> None:
    skill = parse_skill_md(
        _doc(
            """
            name: pdf-processing
            description: Extract PDF text. Use for PDF.
            license: MIT
            compatibility: Requires network access.
            allowed-tools: Read Bash Write
            """
        )
    )
    assert skill.license == "MIT"
    assert skill.compatibility == "Requires network access."
    assert skill.allowed_tools == ("Read", "Bash", "Write")


def test_crlf_and_bom_tolerated() -> None:
    raw = "\ufeff---\r\nname: x\r\ndescription: A skill. Use it.\r\n---\r\n\r\nBody here.\r\n"
    skill = parse_skill_md(raw)
    assert skill.name == "x"
    assert skill.instructions == "Body here."


# -- metadata -> soup field mapping -----------------------------------------


def test_metadata_maps_soup_fields() -> None:
    skill = parse_skill_md(
        _doc(
            """
            name: pdf-processing
            description: Extract PDF text. Use for PDF.
            metadata:
              version: "1.0"
              dependencies: "files, http"
              extends: "base"
              priority: "10"
              tags: "pdf, forms"
            """
        )
    )
    assert skill.version == "1.0"
    assert skill.dependencies == ("files", "http")
    assert skill.extends == ("base",)
    assert skill.priority == 10
    assert skill.tags == ("pdf", "forms")
    # Canonical metadata is preserved as strings.
    assert skill.metadata["version"] == "1.0"


def test_overrides_take_precedence_over_metadata() -> None:
    skill = parse_skill_md(
        _doc(
            """
            name: pdf-processing
            description: Extract PDF text. Use for PDF.
            metadata:
              version: "1.0"
              priority: "10"
            """
        ),
        overrides={"version": "2.0", "dependencies": ["files"]},
    )
    assert skill.version == "2.0"
    assert skill.dependencies == ("files",)
    assert skill.priority == 10


# -- spec validation / invalid input ----------------------------------------


def test_missing_frontmatter_raises() -> None:
    with pytest.raises(SkillParseError, match="frontmatter"):
        parse_skill_md("Just a markdown body, no frontmatter.")


def test_missing_name_raises() -> None:
    with pytest.raises(SkillParseError, match="name"):
        parse_skill_md(_doc("description: Some skill. Use it."))


def test_missing_description_raises() -> None:
    with pytest.raises(SkillParseError, match="description"):
        parse_skill_md(_doc("name: x"))


def test_invalid_name_format_raises() -> None:
    with pytest.raises(SkillParseError, match="name"):
        parse_skill_md(_doc("name: Not_Valid\ndescription: A skill. Use it."))


def test_name_must_match_directory() -> None:
    with pytest.raises(SkillParseError, match="match its directory"):
        parse_skill_md(
            _doc("name: pdf-processing\ndescription: A skill. Use it."),
            dir_name="something-else",
        )


def test_name_matching_directory_ok() -> None:
    skill = parse_skill_md(
        _doc("name: pdf-processing\ndescription: A skill. Use it."),
        dir_name="pdf-processing",
    )
    assert skill.name == "pdf-processing"


def test_description_too_long_raises() -> None:
    long_desc = "d" * 1025
    with pytest.raises(SkillParseError, match="1024"):
        parse_skill_md(_doc(f"name: x\ndescription: {long_desc}"))


def test_empty_body_raises() -> None:
    with pytest.raises(SkillParseError, match="body"):
        parse_skill_md("---\nname: x\ndescription: A skill. Use it.\n---\n\n   \n")


def test_unexpected_top_level_key_is_ignored() -> None:
    skill = parse_skill_md(
        _doc(
            "name: x\ndescription: A skill. Use it.\nversion: '1.0'\nargument-hint: foo"
        )
    )
    assert skill.name == "x"


def test_non_mapping_frontmatter_raises() -> None:
    with pytest.raises(SkillParseError, match="mapping"):
        parse_skill_md("---\n- just\n- a\n- list\n---\n\nBody.")
