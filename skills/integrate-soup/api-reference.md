# Skill field reference

Details you need at planning time, before `soup-ai` is installed in the target
repo, that the cheat sheet in `SKILL.md` doesn't cover.

## `Skill` fields

| Field           | Group    | Type              | Notes                                              |
| --------------- | -------- | ----------------- | --------------------------------------------------- |
| `name`          | required | `str`             | Spec naming rules; matches directory name for `SKILL.md`. |
| `description`   | required | `str`             | Primary routing signal — be specific.               |
| `instructions`  | required | `str`             | Injected context; the `SKILL.md` Markdown body.     |
| `license`       | spec     | `str \| None`     | License name or bundled file reference.             |
| `compatibility` | spec     | `str \| None`     | Environment requirements (max 500 chars).           |
| `allowed_tools` | spec     | `list[str]`       | Pre-approved tools (`allowed-tools`, experimental).  |
| `metadata`      | spec     | `dict[str, str]`  | Arbitrary key-value map; stores Soup's extensions in `SKILL.md`. |
| `tags`          | soup     | `list[str]`       | Extra keywords folded into BM25 search text.        |
| `examples`      | soup     | `list[str]`       | Rendered after instructions.                        |
| `priority`      | soup     | `int`             | Tie-breaker in selection order (higher first).      |
| `dependencies`  | soup     | `list[str]`       | Companion skills always included alongside this one.|
| `extends`       | soup     | `list[str]`       | Parent skills this one specializes (composition).   |
| `version`       | soup     | `str \| None`     | Version string for shareable/versioned skill modules.|

List fields accept a comma-separated string too (e.g. `tags="pdf, forms"`).

## `SKILL.md` file format

Use this when the plan calls for file-based skills instead of inline
`soup.register(...)` calls:

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

The Markdown body becomes `instructions`. `name` must be lowercase
letters/numbers/hyphens (1-64 chars) and match its directory name. Soup's own
routing extensions (`version`, `dependencies`, `extends`, `priority`, `tags`)
live under spec-compliant `metadata`.

## `extends` vs `dependencies`

Both pull referenced skills in transitively, rendered parent-first — decide
which one applies when the extracted skills have a natural hierarchy:

- `extends`: specialization — `nextjs` extends `react` extends `frontend`.
- `dependencies`: companion requirement — "whenever `sql` is used, also
  include `security`".

Cycles are detected and broken; missing references raise
`MissingDependencyError` unless `strict_dependencies=False`.
