"""Tests for the message adapters."""

from __future__ import annotations

from soup.core.messages import extract_query, inject_context

# -- extract_query ----------------------------------------------------------


def test_extract_from_string() -> None:
    assert extract_query("hello world") == "hello world"


def test_extract_from_user_messages() -> None:
    payload = [
        {"role": "system", "content": "be nice"},
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "second"},
    ]
    assert extract_query(payload) == "first\nsecond"


def test_extract_fallback_when_no_user() -> None:
    payload = [{"role": "system", "content": "only system"}]
    assert extract_query(payload) == "only system"


def test_extract_from_content_parts() -> None:
    payload = [{"role": "user", "content": [{"type": "text", "text": "part one"}, "loose"]}]
    assert extract_query(payload) == "part one\nloose"


def test_extract_handles_none_content() -> None:
    payload = [{"role": "user", "content": None}]
    assert extract_query(payload) == ""


def test_extract_handles_non_text_content() -> None:
    payload = [{"role": "user", "content": 42}]
    assert extract_query(payload) == "42"


# -- inject_context ---------------------------------------------------------


def test_inject_into_string() -> None:
    assert inject_context("PROMPT", "CTX") == "CTX\n\nPROMPT"


def test_inject_empty_context_string_unchanged() -> None:
    assert inject_context("PROMPT", "") == "PROMPT"


def test_inject_inserts_system_message() -> None:
    payload = [{"role": "user", "content": "hi"}]
    out = inject_context(payload, "CTX")
    assert isinstance(out, list)
    assert out[0] == {"role": "system", "content": "CTX"}
    assert out[1] == {"role": "user", "content": "hi"}


def test_inject_merges_existing_system_string() -> None:
    payload = [
        {"role": "system", "content": "base"},
        {"role": "user", "content": "hi"},
    ]
    out = inject_context(payload, "CTX")
    assert isinstance(out, list)
    assert out[0]["content"] == "CTX\n\nbase"
    assert len(out) == 2


def test_inject_merges_empty_system() -> None:
    payload = [{"role": "system", "content": ""}]
    out = inject_context(payload, "CTX")
    assert isinstance(out, list)
    assert out[0]["content"] == "CTX"


def test_inject_inserts_when_system_content_not_string() -> None:
    payload = [{"role": "system", "content": [{"type": "text", "text": "x"}]}]
    out = inject_context(payload, "CTX")
    assert isinstance(out, list)
    assert len(out) == 2
    assert out[0] == {"role": "system", "content": "CTX"}


def test_inject_does_not_mutate_input() -> None:
    payload = [{"role": "user", "content": "hi"}]
    inject_context(payload, "CTX")
    assert payload == [{"role": "user", "content": "hi"}]


def test_inject_empty_context_returns_copy() -> None:
    payload = [{"role": "user", "content": "hi"}]
    out = inject_context(payload, "")
    assert isinstance(out, list)
    assert out == payload
    assert out is not payload


def test_inject_custom_system_role() -> None:
    payload = [{"role": "user", "content": "hi"}]
    out = inject_context(payload, "CTX", system_role="developer")
    assert isinstance(out, list)
    assert out[0]["role"] == "developer"
