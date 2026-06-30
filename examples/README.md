# Soup examples

Each example shares the same skill catalog defined in [`common.py`](./common.py),
which demonstrates composition (`nextjs` → `react` → `frontend`) and dependencies
(`sql` → `security`).

| File                                                   | Provider                          |
| ------------------------------------------------------ | --------------------------------- |
| [`openai_example.py`](./openai_example.py)             | OpenAI (chat messages)            |
| [`openrouter_example.py`](./openrouter_example.py)     | OpenRouter (OpenAI-compatible)    |
| [`anthropic_example.py`](./anthropic_example.py)       | Anthropic (separate `system`)     |
| [`litellm_example.py`](./litellm_example.py)           | LiteLLM (multi-provider)          |
| [`ollama_example.py`](./ollama_example.py)             | Ollama (local models)             |

Run the catalog demo without any API key:

```bash
python examples/common.py
```

The two key integration shapes are:

- **Chat messages** (OpenAI, OpenRouter, LiteLLM, Ollama): `soup.prepare(messages)` returns
  the same messages with a relevant `system` message injected.
- **Separate system prompt** (Anthropic): `soup.build_context(prompt)` returns
  just the rendered context string for the `system` parameter.
