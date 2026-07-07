# Routing benchmarks

Toy two-skill examples (like the README's Quickstart) don't expose how
`BM25Strategy` behaves on a realistic catalog. This directory holds scripts
that measure routing quality against a bigger, product-style skill set.

## `routing_benchmark.py`

A ~15-skill support/product catalog (billing, account security, API auth,
DevOps, etc.) plus a labeled set of realistic user queries — most phrased
without echoing the skill's `description` wording — comparing:

- **baseline**: retrieval over `name` + `description` + `tags` only.
- **with examples**: also indexing `examples` ("training phrases" authors
  attach to a skill), which is what `BM25Strategy` does by default.

```bash
python benchmarks/routing_benchmark.py
```

Sample output:

```
=== baseline: name + description + tags ===
Hit@1        : 57%  (12/21)
Recall       : 57%  (12/21)
False-pos rate: 0%  (0/2 unrelated queries wrongly matched)

=== with examples (current BM25Strategy) ===
Hit@1        : 86%  (18/21)
Recall       : 90%  (19/21)
False-pos rate: 0%  (0/2 unrelated queries wrongly matched)
```

Takeaway: BM25 is lexical, not semantic — a query sharing zero words with a
skill's `description`/`tags` (e.g. "help me speed up my website" for a
`performance-optimization` skill) will not match on those fields alone.
Attaching a handful of realistic `examples` per skill closes most of that
gap cheaply, without adding embeddings or an extra LLM call. It won't catch
every paraphrase — treat it the same way you'd treat intent "training
phrases" in a traditional NLU system: something you author and iterate on
against real query logs, not a one-time setup.
