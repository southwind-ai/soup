"""Using Soup with LiteLLM (one API for many providers).

pip install litellm
export OPENAI_API_KEY=...   # or any provider LiteLLM supports
python examples/litellm_example.py
"""

from __future__ import annotations

from common import build_soup


def main() -> None:
    from litellm import completion

    soup = build_soup()

    messages = [{"role": "user", "content": "How should I structure a Next.js project?"}]
    prepared = soup.prepare(messages)

    response = completion(model="gpt-4o-mini", messages=prepared)
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
