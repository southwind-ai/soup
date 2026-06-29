"""Using Soup with a local Ollama model.

# install & run ollama, then pull a model:
ollama pull llama3.1
pip install ollama
python examples/ollama_example.py
"""

from __future__ import annotations

from common import build_soup


def main() -> None:
    import ollama

    soup = build_soup()

    messages = [{"role": "user", "content": "Give me secure SQL tips for Postgres"}]

    # 'sql' is selected, which depends on 'security' -> both injected automatically.
    prepared = soup.prepare(messages)

    response = ollama.chat(model="llama3.1", messages=prepared)
    print(response["message"]["content"])


if __name__ == "__main__":
    main()
