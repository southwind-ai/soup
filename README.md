# Soup

**Soup is a provider-agnostic context router for LLMs.**

You define a large number of small, reusable modules called **harnesses** (rules,
best practices, instructions, harnesses for skills). On every LLM call, Soup
injects **only the harnesses that are actually relevant** to the request.

Soup is **not** a prompt template engine, an agent framework, a tool runner, or a
RAG/vector-database. It does exactly one thing, well:

> automatically select the right context to inject into an LLM call.

## Why?

Monolithic system prompts are wasteful and noisy. As your guidelines grow you
end up sending thousands of tokens of `react` rules to a `sql` question. Soup
fixes that by:

- **Reducing tokens** sent on each call.
- **Improving context quality** (only relevant instructions).
- **Avoiding monolithic prompts**.
- Making context **modular, composable and reusable** across projects.

Soup is completely independent from the LLM provider. It works with OpenAI,
Anthropic, Gemini, Ollama, LiteLLM, LangChain, etc. — because it just transforms
the prompt/messages you already have.

## Install

```bash
pip install soup-context        # or: uv add soup-context
```

Requires Python 3.12+. The only runtime dependency is `pydantic`.

## Quickstart

```python
from soup import Soup

soup = Soup()

soup.register(
    name="frontend",
    tags=["react", "tailwind"],
    instructions="""
Use React 19.
Use functional components.
Never use CSS modules.
""",
)

# String prompt in, string prompt out:
prompt = soup.prepare("Help me build a react button")

# ...or chat messages in, chat messages out:
messages = soup.prepare([{"role": "user", "content": "Help me build a react button"}])
```

The integration is meant to be invisible:

```python
response = client.responses.create(
    model="gpt-5",
    input=soup.prepare(messages),
)
```

## Core concepts

### Harness

A `Harness` is the atomic unit of context.

| Field          | Type              | Purpose                                            |
| -------------- | ----------------- | -------------------------------------------------- |
| `name`         | `str`             | Unique identifier.                                 |
| `instructions` | `str`             | The context injected into the call.                |
| `description`  | `str \| None`     | Summary, also used as a selection signal.          |
| `tags`         | `list[str]`       | Keywords for tag-based selection.                  |
| `examples`     | `list[str]`       | Optional examples rendered after the instructions. |
| `priority`     | `int`             | Tie-breaker; reserved for future compression.      |
| `dependencies` | `list[str]`       | Harnesses to always include alongside this one.    |
| `extends`      | `list[str]`       | Parent harnesses this one specializes (composition).|
| `version`      | `str \| None`     | Version string for sharing/reuse.                  |
| `metadata`     | `dict[str, Any]`  | Arbitrary user data.                               |

> **Why Pydantic and not `dataclass`?** Pydantic gives us validation at creation
> time, frozen/immutable instances safe to cache and share, and free, robust
> serialization (`model_dump`/`model_validate`). That serialization is exactly
> what makes future YAML / database / Redis storage backends trivial — they just
> round-trip dicts — so the choice pays for itself in the architecture.

### Composition & versioning (`extends`)

Harnesses are **composable and versionable**, so you can build hierarchies and
reuse rules across projects without duplication:

```python
soup.register(name="frontend", tags=["ui"], instructions="Accessibility first.")
soup.register(name="react", version="1.0", extends=["frontend"], tags=["react"],
              instructions="Use hooks.")
soup.register(name="nextjs", version="2.1", extends=["react"], tags=["nextjs"],
              instructions="Use the app router.")
```

Selecting `nextjs` automatically pulls in `react` and `frontend`, rendered
parent-first. `dependencies` work the same way (transitive inclusion) but express
a companion relationship rather than specialization. Cycles are detected and
broken, and missing references raise `MissingDependencyError` (configurable).

### Selection strategies

Selection is a **pipeline of small strategies** — no embeddings, no vector DB,
no RAG. Each strategy receives `(query, harnesses)` and returns a subset; the
pipeline unions the results.

- `KeywordStrategy` — matches words from name/tags/description against the query.
- `TagStrategy` — matches tags only (precise, low-noise).
- `LLMClassifierStrategy` — optional; delegates to a callable you provide (which
  can call any LLM). Soup never imports an SDK.

Add your own:

```python
from soup import SelectionStrategy

class RegexStrategy(SelectionStrategy):
    def select(self, query, harnesses):
        ...

soup.add_strategy(RegexStrategy())
```

### Context builder

The builder renders the resolved harnesses into the injected block. The default
`MarkdownContextBuilder` is fully configurable (heading level, examples,
preamble, custom titles); swap it for any `ContextBuilder` to change the format.

### Storage

Storage is abstracted behind `HarnessStorage`. The default is `InMemoryStorage`.
The interface is designed so filesystem / YAML / database / Redis backends can be
added **without touching the core**.

## Architecture

```
src/soup/
    models/       # Harness (pydantic)
    storage/      # HarnessStorage (ABC) + InMemoryStorage
    strategies/   # SelectionStrategy (ABC) + Keyword/Tag/LLMClassifier
    builders/     # ContextBuilder (ABC) + MarkdownContextBuilder
    core/         # Soup facade, SelectionPipeline, DependencyResolver, messages
    utils/        # small text helpers
tests/
examples/
docs/
```

The design follows SOLID: every collaborator (storage, pipeline, builder) is an
abstraction injected into `Soup`, with sensible defaults. Extend behavior by
adding strategies/builders/backends, not by editing the core. No singletons.

## Examples

See [`examples/`](./examples) for complete, runnable integrations with
**OpenAI**, **Anthropic**, **LiteLLM** and **Ollama**.

## Development

```bash
uv venv && uv pip install -e ".[dev]"
ruff check .
mypy
pytest --cov=soup --cov-report=term-missing
```

## License

MIT.
