# Integration examples

## Splitting a monolithic prompt into skills

**Before** — one large system prompt covering unrelated topics:

```python
SYSTEM_PROMPT = """
You are a coding assistant.

When writing React components: use React 19 function components, prefer
composition, keep accessibility semantics in markup.

When writing SQL: always use parameterized queries, add indexes for frequent
filters, review query plans before optimizing.

When writing Terraform: pin provider versions, use remote state, tag every
resource with an owner.
"""

response = client.chat.completions.create(
    model="gpt-5",
    messages=[{"role": "system", "content": SYSTEM_PROMPT}, *history],
)
```

**After** — each topic becomes its own skill; only the relevant one(s) get
injected per request:

```python
from soup import Soup

soup = Soup()

soup.register(
    name="react-ui",
    description="React UI implementation patterns. Use for React components, hooks, and layout tasks.",
    instructions="Use React 19 function components. Prefer composition and colocated state. Keep accessibility semantics in markup.",
    tags=["react", "ui", "components"],
)
soup.register(
    name="sql-postgres",
    description="Postgres SQL guidance. Use for query design and indexing tasks.",
    instructions="Always use parameterized queries. Add indexes for frequent filters. Review query plans before optimizing.",
    tags=["sql", "postgres", "database"],
)
soup.register(
    name="terraform",
    description="Terraform infrastructure conventions. Use for Terraform/IaC tasks.",
    instructions="Pin provider versions. Use remote state. Tag every resource with an owner.",
    tags=["terraform", "infra", "iac"],
)

response = client.chat.completions.create(
    model="gpt-5",
    messages=soup.prepare([{"role": "system", "content": BASE_SYSTEM_PROMPT}, *history]),
)
```

`BASE_SYSTEM_PROMPT` (persona/tone/global rules that apply to *every* request)
stays as-is — only the topic-specific blocks move into skills. `soup.prepare`
merges its selected context into that existing leading system message.

## Splitting heuristics

When extracting skills from an existing prompt or docs, cut along whichever
axis the content already follows:

- **By domain/topic** — one skill per subject area (frontend, backend, infra).
- **By tool/integration** — one skill per external system (Stripe, Postgres,
  S3).
- **By workflow step** — one skill per stage of a multi-step process (intake,
  triage, resolution) if the prompt is a single procedural document.

Don't split so finely that skills lose coherence (a skill should be a complete,
self-contained instruction block), and don't leave one skill so broad it's
really the old monolithic prompt in disguise.

## Wiring into a `SKILL.md`-file catalog instead of inline code

Prefer this when the catalog is large, maintained by non-engineers, or shared
across repos/languages.

```
skills/
├── react-ui/
│   └── SKILL.md
├── sql-postgres/
│   └── SKILL.md
└── terraform/
    └── SKILL.md
```

```markdown
---
name: react-ui
description: React UI implementation patterns. Use for React components, hooks, and layout tasks.
metadata:
  tags: "react, ui, components"
---

Use React 19 function components. Prefer composition and colocated state.
Keep accessibility semantics in markup.
```

```python
soup = Soup()
soup.register("./skills")  # loads every skill directory under it
```

## Wiring into common call-site shapes

**A plain function that returns a prompt string:**

```python
def build_prompt(user_query: str) -> str:
    return soup.prepare(f"Answer this: {user_query}")
```

**A FastAPI/Flask handler building chat messages:**

```python
@app.post("/chat")
def chat(req: ChatRequest):
    messages = soup.prepare([{"role": "user", "content": req.message}])
    return llm_client.chat(messages=messages)
```

**LangChain**: apply `soup.prepare` to the message list right before invoking
the chain/model, same as any other provider — Soup only transforms the
prompt/messages object, it does not need a LangChain-specific integration.

In every case, `soup.prepare` is the *only* new call — everything downstream
keeps working on the same `str`/`messages` shape it already expected.
