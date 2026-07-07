---
name: integrate-soup
description: >-
  Integrate the soup-ai Python library (a provider-agnostic Agent Skills
  router for LLMs) into the user's existing codebase. Scans the repository for
  where LLM prompts/messages are built, drafts a concrete integration plan,
  then implements it by splitting monolithic prompts into Soup skills and
  wiring soup.prepare() into the call site(s). Use when the user asks to
  integrate, add, wire up, or set up Soup / soup-ai / soup-router in their
  project, or wants to stop shipping one giant system prompt on every LLM call.
---

# Integrate Soup

Soup ([PyPI](https://pypi.org/project/soup-ai/), [GitHub](https://github.com/southwind-ai/soup))
is a tiny library: you register many small **Agent Skills** (name +
description + instructions, in code or as `SKILL.md` files), and on every call
`soup.prepare(payload)` returns the same prompt/messages with only the
relevant skills' instructions injected — via deterministic BM25 lexical
ranking, no embeddings or vector DB. It works with any provider (OpenAI,
Anthropic, Gemini, Ollama, LiteLLM, LangChain, ...) because it only transforms
the prompt/messages object the user already has.

Follow this workflow. Do not skip the plan step — always show the plan and get
confirmation before writing code, unless the user has already explicitly asked
for a fully autonomous integration.

## Workflow

Track progress with a todo list mirroring these steps.

### 1. Discover

Build a mental model of the target repo before touching anything:

- **Package manager & Python version**: look for `uv.lock` (uv), `poetry.lock`
  (poetry), `Pipfile` (pipenv), or plain `requirements*.txt`/`pyproject.toml`.
  Soup requires Python **3.12+** — check the project's supported range and
  flag a conflict instead of silently proceeding.
- **Where LLM calls happen**: grep for provider SDK usage and prompt
  construction — `openai`, `anthropic`, `google.generativeai`, `litellm`,
  `ollama`, `langchain`, `.chat.completions.create(`, `.messages.create(`,
  `client.responses.create(`, `system_prompt`, `SYSTEM_PROMPT`, prompt
  template files (`.md`, `.txt`, `.j2`, f-strings building `messages=[...]`).
- **Current prompt shape**: is there one large monolithic system prompt? Several
  prompt templates per feature/tool/route? Existing "skills"/"tools" metadata
  already half-implemented by hand? This tells you the natural skill
  boundaries (see "Splitting a prompt into skills" below).
- **Conventions**: existing code style, DI patterns (is there already a
  services/container module to add a `Soup` singleton to?), test setup, and
  whether skills should live as `SKILL.md` files (bigger/reusable catalogs) or
  inline `soup.register(...)` calls (few, simple, code-owned skills).

### 2. Draft a plan

Present a concrete plan and wait for confirmation before editing anything.
Include:

- The exact **skills** you'll create: name, one-line description, and where
  their instructions come from (extracted from the existing monolithic
  prompt/docs, not invented).
- Whether skills will be **inline** (`soup.register(name=..., description=...,
  instructions=...)`) or **`SKILL.md` files** under a `skills/` directory, and
  why.
- The **call site(s)** where `soup.prepare(payload)` will wrap the existing
  prompt/messages right before the LLM call — list exact file:line locations.
- The **dependency change**: add `soup-ai` via the detected package manager.
- Anything you're explicitly *not* changing (e.g. leaving an unrelated
  monolithic prompt alone because it's not LLM-facing routing content).

### 3. Implement

- Add the dependency: `uv add soup-ai`, `poetry add soup-ai`, or
  `pip install soup-ai` / append to `requirements.txt`, matching what's
  already used in the repo.
- Create the skills exactly as planned. Write real, specific `description`s
  (see "Writing skills that route well" below) — vague descriptions make BM25
  selection fail silently.
- Instantiate one `Soup()` per app (module-level singleton, or wherever the
  repo already wires up shared clients/services — follow existing conventions,
  don't invent a new DI pattern).
- At each identified call site, wrap the existing prompt/messages with
  `soup.prepare(...)` immediately before it's sent to the LLM. `prepare`
  accepts and returns the same shape (`str` in/out, or chat `messages` list
  in/out), so the surrounding code should need minimal changes.
- Match the codebase's existing style, formatting, and linting — run its
  formatter/linter on touched files if one is configured.

### 4. Verify

- Run the project's existing test suite and linters if present.
- Do a smoke import/run to confirm nothing broke.
- Summarize what changed, and tell the user how to add more skills later
  (register more skills; nothing else needs to change).

## Core API cheat sheet

```python
from soup import Soup

soup = Soup()  # optional: storage=, pipeline=, strategies=, builder=, strict_dependencies=, system_role=

# Register a skill — dispatches on the argument shape:
soup.register(name="pdf", description="...", instructions="...")   # inline, in code
soup.register("./skills/pdf-processing")                            # one local SKILL.md dir
soup.register("./skills")                                           # a folder of skill dirs
soup.register("https://github.com/org/repo", ref="main")            # remote convention: /skills/<name>/SKILL.md

# The one call to make at every LLM call site — same shape in, same shape out:
prompt = soup.prepare("raw user prompt string")
messages = soup.prepare([{"role": "user", "content": "..."}])
```

For the full `Skill` field table, the `SKILL.md` frontmatter shape, and
`extends`/`dependencies` composition semantics, see
[api-reference.md](api-reference.md).

## Writing skills that route well

BM25 needs distinguishing lexical signal — a vague `description` means a skill
never gets selected. When extracting skills from an existing prompt:

- One skill = one cohesive topic/tool/workflow. Don't dump the whole old
  prompt into a single skill — that defeats the purpose.
- `description` states **what** it covers and **when** to use it, using the
  vocabulary real user queries will contain (not internal jargon).
- Add `tags` for the domain's key nouns (e.g. `["pdf", "forms", "documents"]`).
- Keep `instructions` scoped to that one topic only.

For worked before/after examples of splitting a monolithic prompt and wiring
`soup.prepare()` into common call-site shapes, see [examples.md](examples.md).
