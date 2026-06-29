"""Using Soup with the Anthropic SDK.

Anthropic takes ``system`` separately from ``messages``, so we build the context
block directly with :meth:`Soup.build_context` and pass it as ``system``.

    pip install anthropic
    export ANTHROPIC_API_KEY=...
    python examples/anthropic_example.py
"""

from __future__ import annotations

from common import build_soup


def main() -> None:
    import anthropic

    soup = build_soup()
    client = anthropic.Anthropic()

    user_prompt = "Write a SQL query to list active users"

    # Anthropic wants the system prompt separately:
    system = soup.build_context(user_prompt)

    message = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=1024,
        system=system or "You are a helpful assistant.",
        messages=[{"role": "user", "content": user_prompt}],
    )
    print(message.content[0].text)


if __name__ == "__main__":
    main()
