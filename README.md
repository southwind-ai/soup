# Soup

**Soup is a provider-agnostic Agent Skills router for LLMs.**

You define a large number of [**Agent Skills**](https://agentskills.io/specification)
(rules, best practices, instructions) — in code, as `SKILL.md` files or with remote sources. On every
LLM call, Soup injects **only the skills that are actually relevant** to the
request.

## Why?

Monolithic prompts do not scale once your skill catalog spans multiple domains,
tools, and workflows. Soup routes only the relevant Agent Skills for each
request, so you do not ship unrelated instruction blocks on every call.

- **Reducing tokens** sent on each call.
- **Improving context quality** (only relevant instructions).
- **Avoiding monolithic prompts**.
- Making context **modular, composable and reusable** across projects, using the
  open Agent Skills format so your skills are portable.

Soup is completely independent from the LLM provider. It works with OpenAI,
Anthropic, Gemini, Ollama, LiteLLM, LangChain, etc. — because it just transforms
the prompt/messages you already have.

## Install

```bash
pip install soup-ai        # or: uv add soup-ai
```

Requires Python 3.12+. Runtime dependencies are `pydantic` and `pyyaml`.

## Quickstart

```python
from soup import Soup

soup = Soup()

soup.register(
    name="react-ui",
    description="React UI implementation patterns. Use for React components, hooks, and layout tasks.",
    instructions="""
Use React 19 function components.
Prefer composition and colocated state.
Keep accessibility semantics in markup.
""",
    tags=["react", "ui", "components"],
)

soup.register(
    name="sql-postgres",
    description="Postgres SQL guidance. Use for query design and indexing tasks.",
    instructions="""
Use parameterized queries.
Add indexes for frequent filters.
Review query plans before optimization.
""",
    tags=["sql", "postgres", "database"],
)

# String prompt in, string prompt out:
prompt = soup.prepare("I need guidance on building a React dashboard card component with hooks.")

# ...or chat messages in, chat messages out:
messages = soup.prepare(
    [{"role": "user", "content": "I need guidance on building a React dashboard card component with hooks."}]
)
```

The integration is meant to be invisible:

```python
response = client.responses.create(
    model="gpt-5",
    input=soup.prepare(messages),
)
```

## Registering skills

`register()` is the single entry point. It dispatches on what you give it.

```python
# 1. Define a skill in code (name, description and instructions are required):
soup.register(
    name="pdf-processing",
    description="Extract PDF text, fill forms, and merge files. Use for PDF tasks.",
    instructions="Use pypdf for extraction...",
)

# 2. Load a single local skill directory (a folder containing SKILL.md):
soup.register("./skills/pdf-processing")

# 3. Load a whole local collection (a folder of skill directories):
soup.register("./skills")

# 4. Load from a GitHub or GitLab repo over raw HTTP (no git required):
soup.register("https://github.com/vercel-labs/skills", ref="main")
soup.register("https://gitlab.com/group/project", ref="main")
```

Soup's optional routing behavior stays simple. For a single skill, pass overrides
as keyword arguments; for a collection or repo, pass per-skill `options`:

```python
soup.register("./skills/pdf-processing", dependencies=["files"], version="1.0")

soup.register(
    "./skills",
    options={
        "pdf-processing": {"dependencies": ["files"], "priority": 10},
        "data-analysis": {"version": "2.1"},
    },
)
```

## Core concepts

### Skill

A `Skill` is the atomic unit of context and follows the Agent Skills spec.

| Field           | Group    | Type               | Purpose                                                  |
| --------------- | -------- | ------------------ | -------------------------------------------------------- |
| `name`          | required | `str`              | Unique identifier (spec naming rules; matches dir name). |
| `description`   | required | `str`              | What it does and when to use it; primary routing signal. |
| `instructions`  | required | `str`              | The context injected; the `SKILL.md` Markdown body.      |
| `license`       | spec     | `str \| None`      | License name or bundled file reference.                  |
| `compatibility` | spec     | `str \| None`      | Environment requirements (max 500 chars).                |
| `allowed_tools` | spec     | `list[str]`        | Pre-approved tools (`allowed-tools`, experimental).      |
| `metadata`      | spec     | `dict[str, str]`   | Arbitrary key-value mapping; stores Soup extensions.     |
| `tags`          | soup     | `list[str]`        | Keywords for tag-aware selection.                        |
| `examples`      | soup     | `list[str]`        | Optional examples rendered after the instructions.       |
| `priority`      | soup     | `int`              | Tie-breaker; reserved for future compression.            |
| `dependencies`  | soup     | `list[str]`        | Skills to always include alongside this one.             |
| `extends`       | soup     | `list[str]`        | Parent skills this one specializes (composition).        |
| `version`       | soup     | `str \| None`      | Version string for sharing/reuse.                        |

### SKILL.md files

A `SKILL.md` file is YAML frontmatter followed by a Markdown body. Soup's own
routing extensions live under spec-compliant `metadata` (string values are
canonical; comma-separated strings are parsed into lists):

```markdown
---
name: pdf-processing
description: Extract PDF text, fill forms, and merge files. Use for PDF tasks.
license: MIT
metadata:
  version: "1.0"
  dependencies: "files"
  tags: "pdf, forms, documents"
  priority: "10"
---

Use pypdf for extraction. Validate inputs before merging...
```

The Markdown body becomes the skill's `instructions`. The `name` must follow the
spec rules (lowercase letters, numbers and hyphens, 1–64 chars) and match its
directory name.

### Composition & versioning (`extends`)

Skills are **composable and versionable**, so you can build hierarchies and
reuse rules across projects without duplication:

```python
soup.register(name="frontend", description="Frontend basics. Use for UI work.",
              tags=["ui"], instructions="Accessibility first.")
soup.register(name="react", description="React rules. Use for React apps.",
              version="1.0", extends=["frontend"], tags=["react"], instructions="Use hooks.")
soup.register(name="nextjs", description="Next.js conventions. Use for Next.js.",
              version="2.1", extends=["react"], tags=["nextjs"], instructions="Use the app router.")
```

Selecting `nextjs` automatically pulls in `react` and `frontend`, rendered
parent-first. `dependencies` work the same way (transitive inclusion) but express
a companion relationship rather than specialization. Cycles are detected and
broken, and missing references raise `MissingDependencyError` (configurable).

### Selection strategies

By default, Soup uses a single built-in selector: **`BM25Strategy`** (no
embeddings, no vector DB, no RAG).

If you need custom behavior, you can still add your own strategy:

```python
from soup import SelectionStrategy

class RegexStrategy(SelectionStrategy):
    def select(self, query, skills):
        ...

soup.add_strategy(RegexStrategy())
```

For architecture and design details, see [`docs/architecture.md`](./docs/architecture.md).

## Examples

See [`examples/`](./examples) for complete, runnable integrations with
**OpenAI**, **OpenRouter**, **Anthropic**, **LiteLLM** and **Ollama**.

## Development

```bash
uv venv && uv pip install -e ".[dev]"
ruff check .
mypy
basedpyright
pytest --cov=soup --cov-report=term-missing
```

## Roadmap

V1 loads `SKILL.md` instructions and metadata only. Full Agent Skills support —
exposing bundled `scripts/`, `references/`, and `assets/` files to the
LLM/runtime — is tracked as a follow-up.

## License

MIT.
