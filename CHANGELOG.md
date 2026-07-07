# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.2.0]: https://github.com/southwind-ai/soup/releases/tag/v0.2.0
[0.1.0]: https://github.com/southwind-ai/soup/releases/tag/v0.1.0
