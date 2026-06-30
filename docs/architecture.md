# Architecture

Soup is intentionally tiny. It does **one** thing: pick the relevant skills for
an LLM call and inject them. The design optimizes for extensibility without ever
editing the core.

## Component overview

```
register(source)
   │
   ├─ sources/           SKILL.md / dir / collection / GitHub|GitLab -> Skill(s)
   │     ├─ skill_md.py  (YAML frontmatter + Markdown body, spec validation)
   │     ├─ local.py     (skill dir, skills collection)
   │     └─ remote.py    (raw HTTP, no git)
   │
prepare(payload)
   │
   ├─ extract_query        (core/messages.py)   payload  -> query text
   │
   ├─ SelectionPipeline    (core/pipeline.py)    query    -> selected skills
   │     ├─ BM25Strategy (default)
   │     └─ <your strategies>
   │
   ├─ priority sort         (core/soup.py)
   │
   ├─ DependencyResolver    (core/resolver.py)   + extends/dependencies, ordered
   │
   ├─ ContextBuilder        (builders/)          skills -> context string
   │
   └─ inject_context        (core/messages.py)   payload + context -> payload
```

Every collaborator is an abstraction with a default implementation, injected
into `Soup` via its constructor. There are no singletons and no global state.

## Agent Skills compliance

A `Skill` mirrors the open [Agent Skills spec](https://agentskills.io/specification):

- **Required**: `name`, `description`, `instructions`.
- **Spec fields**: `license`, `compatibility`, `metadata`, `allowed_tools`.
- **Soup fields**: `tags`, `examples`, `priority`, `dependencies`, `extends`,
  `version`.

`SKILL.md` files are parsed with PyYAML: frontmatter must be valid YAML, the
`name` must follow the spec naming rules and match its directory, the
`description` is required and length-bounded, and the Markdown body becomes
`instructions`. Soup's own routing extensions are stored in spec-compliant
`metadata` (`metadata.version`, `metadata.dependencies`, `metadata.extends`,
`metadata.priority`, `metadata.tags`). String values are canonical; list fields
accept comma-separated strings.

## Sources

`register()` dispatches by input shape (no user-facing `load_*` methods):

- a `Skill` instance,
- keyword fields (a code-defined skill),
- a local **skill directory** (contains `SKILL.md`),
- a local **skills collection** (a folder of skill directories),
- a **GitHub/GitLab repository URL** (raw HTTP, default convention
  `/skills/<skill>/SKILL.md`, with `ref=` for branch/tag/commit).

Single sources accept keyword overrides; collections and repositories accept
per-skill `options`.

## SOLID notes

- **Single responsibility**: storage stores, strategies select, the resolver
  composes, the builder renders, the sources parse/load, the adapter
  (de)serializes payloads. `Soup` only orchestrates.
- **Open/closed**: add behavior by implementing `SelectionStrategy`,
  `ContextBuilder`, or `SkillStorage` — never by modifying the core.
- **Liskov**: all backends/strategies/builders are substitutable behind their
  ABCs.
- **Interface segregation**: the abstractions are minimal (`select`, `build`,
  CRUD on storage).
- **Dependency inversion**: `Soup` depends on abstractions, with defaults wired
  in the constructor (constructor injection).

## Why Pydantic for `Skill`?

- Validation at creation time (spec naming/length rules, non-empty
  name/description/instructions).
- Frozen/immutable instances are safe to cache and share across requests.
- `model_dump` / `model_validate` give robust serialization for free — the
  enabler for alternative storage backends, which only need to round-trip dicts.

## `extends` vs `dependencies`

Both pull referenced skills in transitively and render them *before* the
referencing skill. They differ in intent:

- **`extends`** expresses *specialization/composition*: `nextjs` extends `react`
  extends `frontend`. Combined with `version` this gives shareable, versioned
  skill modules.
- **`dependencies`** expresses a *companion* requirement: "whenever `sql` is
  used, also include `security`".

The resolver performs a cycle-safe depth-first expansion, so nested hierarchies
and accidental cycles are handled and always terminate.

## Selection: union, not chain

The pipeline **unions** strategy results. Complementary signals (a precise tag
match plus a fuzzy keyword match) increase recall instead of filtering each other
out. A skill is included if any strategy selects it; first occurrence determines
order, keeping output deterministic.

## Priority

`priority` currently breaks ties in selection ordering (higher first). It is also
the reserved hook for future **context compression** — when a token budget is
exceeded, lower-priority skills will be the first to be summarized or dropped.
