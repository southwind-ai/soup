# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-07-07

### Changed

- `BM25Strategy` now also indexes `examples` when building searchable text
  (previously only `name` + `description` + `tags`). `examples` act as
  "training phrases": short, realistic user utterances that close vocabulary
  gaps between how a skill is described and how users actually ask for it.
  See `benchmarks/routing_benchmark.py` for a measured recall improvement
  (57% -> 90% on a 15-skill/23-query benchmark).

### Added

- `benchmarks/routing_benchmark.py`: a realistic multi-skill routing-quality
  benchmark (precision/recall/false-positive rate) for `BM25Strategy`.

## [0.2.0] - 2026-06-30

### Changed

- Refactored `Soup` into a spec-compliant [Agent Skills](https://agentskills.io/specification)
  router: skills can now be defined in code, loaded from `SKILL.md` files, or
  loaded from a local/remote skills collection (including GitHub/GitLab repos).
- Replaced `KeywordStrategy` and `TagStrategy` with a single deterministic
  `BM25Strategy` for lexical ranking. Removed the unused `LLMClassifierStrategy`
  and its example.

### Added

- Tests for `BM25Strategy`.

## [0.1.0] - 2026-06-29

### Added

- Initial release: Soup, a provider-agnostic context router for LLMs.

[0.2.1]: https://github.com/southwind-ai/soup/releases/tag/v0.2.1
[0.2.0]: https://github.com/southwind-ai/soup/releases/tag/v0.2.0
[0.1.0]: https://github.com/southwind-ai/soup/releases/tag/v0.1.0
