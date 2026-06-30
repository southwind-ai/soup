"""Using Soup with the OpenAI SDK.

Soup transforms the messages you already build; OpenAI never knows it's there.

    pip install openai
    export OPENAI_API_KEY=...
    python examples/openai_example.py
"""

from __future__ import annotations

from common import build_soup


def main() -> None:
    from openai import OpenAI

    soup = build_soup()
    client = OpenAI()

    messages = [{"role": "user", "content": "Build a React button with Tailwind"}]

    # Inject only the relevant skills (frontend + react) as a system message.
    prepared = soup.prepare(messages)

    response = client.chat.completions.create(model="gpt-4o-mini", messages=prepared)
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
