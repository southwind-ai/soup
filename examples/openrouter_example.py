"""Using Soup with OpenRouter via the OpenAI-compatible client.

OpenRouter exposes an OpenAI-compatible API, so we can use the `openai` SDK
with a custom base URL.

    pip install openai
    export OPENROUTER_API_KEY=...
    python examples/openrouter_example.py
"""

from __future__ import annotations

import os

from common import build_soup


def main() -> None:
    from openai import OpenAI

    soup = build_soup()

    api_key = os.environ["OPENROUTER_API_KEY"]
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    messages = [{"role": "user", "content": "Build a React button with Tailwind"}]

    # Inject only the relevant skills (frontend + react) as a system message.
    prepared = soup.prepare(messages)

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=prepared,
        extra_headers={
            # Optional but recommended by OpenRouter for attribution/rate policies.
            "HTTP-Referer": "https://github.com/southwind-ai/soup",
            "X-Title": "Soup",
        },
    )
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
