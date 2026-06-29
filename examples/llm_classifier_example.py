"""Optional: use a real LLM to classify which harnesses are relevant.

Soup never imports an LLM SDK. You supply a callable; here we back it with
OpenAI, but any model/provider works the same way. This is most useful when
keyword/tag matching isn't precise enough.

    pip install openai
    export OPENAI_API_KEY=...
    python examples/llm_classifier_example.py
"""

from __future__ import annotations

import json

from common import build_soup

from soup import Harness, LLMClassifierStrategy, Soup


def make_openai_classifier(model: str = "gpt-4o-mini"):
    """Return a classifier callable that asks an LLM to pick harness names."""
    from openai import OpenAI

    client = OpenAI()

    def classify(query: str, candidates: list[Harness]) -> list[str]:
        catalog = "\n".join(f"- {h.name}: {h.description or ''}" for h in candidates)
        prompt = (
            "Given the user request and the catalog of context modules, return a "
            'JSON array of the names that are relevant. Request: "'
            f'{query}"\n\nCatalog:\n{catalog}'
        )
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        data = json.loads(content)
        return data.get("names", []) if isinstance(data, dict) else list(data)

    return classify


def main() -> None:
    # Reuse the catalog from common, but drive selection with the LLM classifier.
    base = build_soup()
    soup = Soup(strategies=[LLMClassifierStrategy(make_openai_classifier())])
    soup.register_many(base.harnesses)

    print(soup.build_context("I'm building a server-rendered React app"))


if __name__ == "__main__":
    main()
