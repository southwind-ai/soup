# Architecture

Soup is intentionally tiny. It does **one** thing: pick the relevant context for
an LLM call and inject it. The design optimizes for extensibility without ever
editing the core.

## Component overview

```
prepare(payload)
   │
   ├─ extract_query        (core/messages.py)   payload  -> query text
   │
   ├─ SelectionPipeline    (core/pipeline.py)    query    -> selected harnesses
   │     ├─ BM25Strategy (default)
   │     └─ <your strategies>
   │
   ├─ priority sort         (core/soup.py)
   │
   ├─ DependencyResolver    (core/resolver.py)   + extends/dependencies, ordered
   │
   ├─ ContextBuilder        (builders/)          harnesses -> context string
   │
   └─ inject_context        (core/messages.py)   payload + context -> payload
```

Every collaborator is an abstraction with a default implementation, injected
into `Soup` via its constructor. There are no singletons and no global state.

## SOLID notes

- **Single responsibility**: storage stores, strategies select, the resolver
  composes, the builder renders, the adapter (de)serializes payloads. `Soup` only
  orchestrates.
- **Open/closed**: add behavior by implementing `SelectionStrategy`,
  `ContextBuilder`, or `HarnessStorage` — never by modifying the core.
- **Liskov**: all backends/strategies/builders are substitutable behind their
  ABCs.
- **Interface segregation**: the abstractions are minimal (`select`, `build`,
  CRUD on storage).
- **Dependency inversion**: `Soup` depends on abstractions, with defaults wired
  in the constructor (constructor injection).

## Why Pydantic for `Harness`?

- Validation at creation time (priority, non-empty name/instructions).
- Frozen/immutable instances are safe to cache and share across requests.
- `model_dump` / `model_validate` give robust serialization for free — the
  enabler for future YAML / SQL / Redis storage backends, which only need to
  round-trip dicts.

## `extends` vs `dependencies`

Both pull referenced harnesses in transitively and render them *before* the
referencing harness. They differ in intent:

- **`extends`** expresses *specialization/composition*: `nextjs` extends `react`
  extends `frontend`. This is what makes harnesses composable and reusable across
  projects, and combined with `version` gives you shareable, versioned context
  modules.
- **`dependencies`** expresses a *companion* requirement: "whenever `sql` is
  used, also include `security`".

The resolver performs a cycle-safe depth-first expansion, so nested hierarchies
and accidental cycles are handled and always terminate.

## Selection: union, not chain

The pipeline **unions** strategy results. Complementary signals (a precise tag
match plus a fuzzy keyword match) increase recall instead of filtering each other
out. A harness is included if any strategy selects it; first occurrence
determines order, keeping output deterministic.

## Priority

`priority` currently breaks ties in selection ordering (higher first). It is also
the reserved hook for future **context compression** — when a token budget is
exceeded, lower-priority harnesses will be the first to be summarized or dropped.
