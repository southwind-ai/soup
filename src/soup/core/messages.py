"""Adapters for the two supported input shapes: string prompts and chat messages.

Soup accepts whatever you already pass to your LLM and returns the same shape,
so integration is (almost) invisible.
"""

from __future__ import annotations

from typing import Any

#: A single chat message, e.g. ``{"role": "user", "content": "..."}``.
type ChatMessage = dict[str, Any]

#: A list of chat messages.
type Messages = list[ChatMessage]


def _text_from_content(content: Any) -> str:
    """Best-effort extraction of plain text from a message ``content`` value.

    Handles plain strings and the list-of-parts shape used by some providers
    (``[{"type": "text", "text": "..."}]``).
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return str(content)


def extract_query(payload: str | Messages) -> str:
    """Derive the text used to drive harness selection.

    For a string prompt the whole string is used. For chat messages, the text
    of all ``user`` messages is concatenated (falling back to every message if
    there are no user messages).

    Args:
        payload: A string prompt or a list of chat messages.

    Returns:
        The query text.
    """
    if isinstance(payload, str):
        return payload
    user_texts = [_text_from_content(m.get("content")) for m in payload if m.get("role") == "user"]
    if not user_texts:
        user_texts = [_text_from_content(m.get("content")) for m in payload]
    return "\n".join(t for t in user_texts if t)


def inject_context(
    payload: str | Messages,
    context: str,
    *,
    system_role: str = "system",
) -> str | Messages:
    """Return a copy of ``payload`` with ``context`` injected.

    * For a string prompt, ``context`` is prepended (separated by a blank line).
    * For chat messages, ``context`` is merged into a leading message whose role
      is ``system_role`` if its content is a string, otherwise a new system
      message is inserted at the front.

    The input is never mutated. If ``context`` is empty, ``payload`` is returned
    unchanged (a shallow copy for lists).

    Args:
        payload: A string prompt or a list of chat messages.
        context: The rendered context block to inject.
        system_role: Role name to use for the injected/merged system message.

    Returns:
        A new payload of the same type as the input.
    """
    if isinstance(payload, str):
        if not context:
            return payload
        return f"{context}\n\n{payload}"

    messages = [dict(m) for m in payload]
    if not context:
        return messages

    if messages and messages[0].get("role") == system_role:
        existing = messages[0].get("content")
        if isinstance(existing, str):
            merged = f"{context}\n\n{existing}" if existing else context
            messages[0] = {**messages[0], "content": merged}
            return messages

    messages.insert(0, {"role": system_role, "content": context})
    return messages
