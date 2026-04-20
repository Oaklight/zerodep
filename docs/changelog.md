# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Performance

- **A2A module**: optimized serialization and deserialization paths — `to_dict()` now avoids `dataclasses.asdict()`-style deep copy overhead. Serialization is now **2.2-2.6x faster** than a2a-protocol (previously 1.4-2.1x slower). Deserialization narrowed from 1.8-4.1x slower to **1.1-1.7x slower** via optimized enum resolution and type dispatch. JSON round-trip is now **1.4-1.5x faster** end-to-end.
- **Cache module**: optimized decorator wrapper path — LRU decorator overhead is now **1.2x faster** than cachetools (previously ~same). TTL decorator overhead reached parity with cachetools (previously 1.3x slower).
- **QR module**: optimized encoding path — short inputs are now only 1.1x slower (previously 2.1x slower). Medium (URL) and long inputs are now **1.1-1.2x faster** than the `qrcode` library (previously 1.7-1.9x slower).
- **Readability module**: optimized scoring and tree-walking algorithms — small pages **2.1x faster** (previously 1.7x faster), medium pages now **1.2x faster** (previously 2x slower). Large pages improved from 2x slower to 1.4x slower vs readability-lxml.

## [2026.4.20] - 2026-04-20

### New Modules

- **Readability module**: zero-dependency article content extractor ported from Mozilla Readability.js. `extract()` performs full article extraction with metadata (title, author, excerpt, published_time, site_name, lang, dir). `is_probably_readable()` provides a quick readability heuristic check. Supports JSON-LD and OpenGraph metadata extraction. 2-level retry (ruthless on/off) for robust extraction. 18 Mozilla Readability.js test fixtures for cross-validation. Three-way benchmark: zerodep vs readability-lxml vs Mozilla JS. Depends on `soup` module (no pip dependencies).

### Enhancements

- **Soup module**: extended with tree mutation and serialization APIs — `append()`, `insert()`, `extract()`, `replace_with()`, `unwrap()` for tree manipulation; `to_html()` / `__str__()` for HTML serialization; `__setitem__` / `__delitem__` for attribute setting/deletion; `Soup.new_tag()` factory method for creating detached Tag nodes.

### Performance

- **Cache module**: optimized `TypedKey` construction — one-shot tuple construction and removed redundant `sorted()` call. Previously 1.3x slower than cachetools, now **1.2x faster**.
- **Cache module**: optimized LFU eviction — bypass `__touch` in `popitem`. Previously 1.4x slower than cachetools, now **~equal**.
- **PersistDict module**: optimized SQLite write performance — `PRAGMA synchronous=NORMAL`, `commit_every` parameter for batched writes, deferred commits. Reduces per-write fsync overhead for bulk operations.
- **Semver module**: optimized parse, comparison, and property access — replaced custom `_InfinityType`/`_NegativeInfinityType` sentinel classes with plain integer tuples, inlined `_parse_letter_version`/`_parse_local_version`/`_cmpkey` into `__init__`, used `match.groups()` tuple destructuring instead of `groupdict()`, cached `__str__` result, pre-compiled local version split regex, direct `_pre`/`_post`/`_dev` attribute access in boolean properties. Parse **~1.3x faster**, sort **~1.4x faster**, compare **~1.4x faster**, property access **~4.5x faster**.
- No regression on LRU, TTL, or mixed workload benchmarks (cache). No regression on read/iterate benchmarks (persistdict). All semver correctness tests pass.

### Bug Fixes

- **Docs**: fixed ReadTheDocs build failure caused by `search` → `sparse_search` module rename.

## [2026.4.15] - 2026-04-15

### New Commands

- **`zerodep bump`**: auto-detect changed modules (via content hash comparison against git tags) and bump their frontmatter version. Supports `--patch` (default), `--minor`, and `--major` levels. Optionally accepts specific module names. Regenerates `manifest.json` after bumping.
- **`zerodep new`**: scaffold a new module directory with template files — module source (with frontmatter, copyright, and `__all__`), correctness test file. Accepts `--category`, `--tier`, and `--deps` options.

### Enhancements

- **`zerodep version-check --strict`**: new flag that exits with code 1 when any module needs a version bump, enabling CI integration.

### CI

- **Release workflow**: new GitHub Actions workflow (`.github/workflows/release.yml`) that automates the full release process — lint, test, auto-detect CalVer version, bump module versions, update project version, commit, tag, and create GitHub Release. Triggered via `workflow_dispatch` with optional manual version override.
- **Benchmark version-check**: added non-blocking `version-check` step to benchmark workflow as a reminder for unbumped modules.
- Raised benchmark alert threshold from 150% to 200% to reduce false positives from CI runner variance.

### Bug Fixes

- **a2a module**: fixed `StrEnum` string representation test for Python 3.11+ (use `.value` attribute instead of f-string formatting).
- **httpclient module**: switched benchmark tests from `httpbin.org` to local test server for reliability.

### Refactoring

- **Complexity reduction**: refactored 19 modules to bring all functions under cognitive complexity 20 (complexipy) and cyclomatic complexity 20 (ruff C901). Modules refactored: cache, validate, tabulate, dotenv, runner, xml, diff, soup, sse, search, scheduler, depdetect, qr, acp, yaml, toon, protobuf, markdown, httpclient.
- Refactoring patterns used: per-type dispatch tables, try-parse extraction, phase-based decomposition, helper function extraction — all within single-file constraint.
- **qr module**: updated copyright notice to reflect substantial refactoring (no longer a direct port).

### Benchmark

- Custom HTML report generator with light/dark theme toggle and per-module benchmark pages for docs embedding.
- Corrected benchmark report color thresholds and AES classification.

### Internal

- Added `complexipy>=5.2.0` dev dependency and `[tool.complexipy]` configuration in `pyproject.toml`.
- Enabled ruff `C901` lint rule with `max-complexity = 20` in `pyproject.toml`.

## [2026.4.11] - 2026-04-11

### Breaking Changes

- **Versioning**: adopted [CalVer](https://calver.org/) (`YYYY.M.patch`) for project-level releases. Individual modules continue to use independent SemVer. Each release represents a stable snapshot of the CLI and all modules.

### New Commands

- **`zerodep dep-graph`**: display module dependency relationships — table view for all modules, or detailed view with transitive impact analysis for a single module (`zerodep dep-graph yaml`).
- **`zerodep dep-check`**: auto-detect changed modules (via content hash comparison against git tags), then run correctness tests for changed modules and all their downstream dependents. Exits with code 1 on test failure for CI integration. Accepts optional module names to check specific modules (`zerodep dep-check yaml config`).
- **`zerodep version-check`**: check which modules have been modified since their declared version tag (existed before, now refactored to share logic with `dep-check`).

### Enhancements

- **Module frontmatter**: added `note` field to all modules pointing to CLI documentation, warning that manual file copy may miss required dependencies.
- **`zerodep add`**: now replaces the generic frontmatter note with a module-specific install command (e.g., `zerodep add config`) when copying files to the user's project.
- **Module versioning**: corrected all module-level versions to reflect actual per-module change history instead of blanket project-version bumps. Modules like `cache` (0.2.0), `prompt` (0.2.0), and `tabulate` (0.1.0) now show their true version.

### Internal

- Extracted `_find_changed_modules()` helper from `cmd_version_check` to share change-detection logic between `version-check` and `dep-check`.
- Added `_build_reverse_deps()`, `_transitive_dependents()`, and `_find_test_file()` utility functions.

## [0.4.1] - 2026-04-10

### Performance

- **Validate module**: added `@functools.lru_cache(maxsize=None)` caching to `_typeddict_fields()`, `_dataclass_fields()`, `_find_discriminator()`, `_is_typeddict()`, `_is_dataclass_type()`, and `_unwrap_annotated()` internal helpers. Eliminates redundant `get_type_hints()` and type introspection calls. Simple validation **3x faster** (9.9 → 3.3 us), bulk data validation now **2x faster than pydantic**.

### Bug Fixes

- **Validate module**: added `_strip_required()` helper to unwrap `Required[T]`/`NotRequired[T]` wrappers before discriminated union matching. Previously, discriminated union dispatch could fail when union members used `Required[Literal[...]]` field annotations.

## [0.4.0] - 2026-04-09

### New Modules

- **Semver module**: PEP 440 version parser and comparator — zero-dependency drop-in replacement for `packaging.version`. Supports full PEP 440 version scheme including epochs, pre/post/dev releases, local versions, and letter normalization. Benchmarked ~2x faster than `packaging` for sorting.
- **Protobuf module**: Zero-dependency proto3 encoder/decoder using Python dataclass schemas. Supports all proto3 scalar types (int32/64, uint32/64, sint32/64, fixed32/64, sfixed32/64, float32, double, bool, string, bytes), nested messages, packed repeated fields, map fields, enums, oneof groups, and unknown field preservation. Schema defined via `@message` decorator + `field(number)` + `Annotated` type aliases — no `.proto` files or `protoc` needed. Proto3 semantics: zero-value fields omitted, packed repeated scalars by default.
- **Persistent Dict module**: `MutableMapping`-based persistent dictionary with pluggable backends (JSON file, SQLite) and pluggable serialization (JSON by default, no pickle). Thread-safe, atomic writes, namespace support via SQLite tables. Factory function `open()` auto-detects backend from file extension.
- **Dep Detect module**: dependency detection and verification utility.

### Enhancements

- **zerodep CLI**: new `outdated` command — compares local file content hashes against the upstream manifest, detecting actual content changes while ignoring metadata-only updates (version bumps).
- **zerodep CLI**: `content_hash` field in manifest — SHA-256 digest of module file content with frontmatter stripped, enabling reliable change detection.
- **zerodep CLI**: `last_updated` field in manifest — ISO 8601 timestamp of the last git commit touching each module's primary file.
- **zerodep CLI**: manifest generation now skips `build/` and `dist/` directories to avoid registering stale build artifacts.
- **Skills module**: `to_markdown()` and `from_dict()` methods for round-trip SKILL.md serialization — programmatic skill authoring, templating, and migration.
- **Skills module**: BM25 index caching — avoids redundant index rebuilds on repeated `select()` calls with the same skill set.
- **Skills module**: `min_score` threshold on `SkillRegistry.select()` — filters out low-relevance results before injection into system prompts.
- **Skills module**: recursive directory discovery (`discover(..., recursive=True)`) — supports hierarchical skill layouts like `category/sub-skill/`.
- **Skills module**: priority/override mechanism (`register(override=True)`, `discover(override=True)`) — enables project > user > system skill precedence.
- **Skills module**: resource content inlining (`to_prompt(inline_resources=True)`) — embeds scripts/references/assets file contents directly in the activation prompt XML.
- **Skills module**: compatibility-based filtering (`filter_compatible()`, `available_tools` parameter on `select()`) — filters skills by tool requirements against the current environment.
- **AES module**: `aes_ecb_padded_size()` utility function — calculates ciphertext size after PKCS7 padding without performing encryption.

## [0.3.0] - 2026-04-01

### New Modules

- **File Lock module**: cross-platform advisory file lock using only stdlib. `fcntl.flock` on Unix/macOS, `msvcrt.locking` with exponential-backoff polling on Windows. Context manager support, non-blocking `try_lock()`, auto parent-dir creation.
- **JSON-RPC module**: JSON-RPC 2.0 protocol implementation with core data types (`JSONRPCError`, `JSONRPCRequest`, `JSONRPCResponse`), exception hierarchy, method dispatcher with streaming support, and async transport over newline-delimited JSON streams. Benchmarked ~12-17x faster than `jsonrpcserver`.

### Enhancements

- **Search module**: Bayesian BM25 probabilistic calibration -- converts unbounded BM25 scores to calibrated [0,1] probabilities via sigmoid likelihood, composite prior, and Bayesian posterior. Supports auto-estimation of α/β from corpus statistics and optional base-rate correction. Calibration state persisted in JSON and SQLite.
- **A2A module**: extracted inline JSON-RPC layer into shared `jsonrpc` module; `A2AError` now subclasses `JSONRPCException` for unified error handling.
- **ACP module**: extracted inline JSON-RPC layer into shared `jsonrpc` module; replaced 39-entry hardcoded camelCase rename map with algorithmic regex-based conversion; unified serialization to A2A-style single recursive `to_dict()` with empty collection filtering.

### Style

- Modernized type annotations: replaced `Optional`/`Dict`/`List` with PEP 604/585 style.
- Added `__all__` exports to all modules.
- Standardized section divider style across modules.
- Added `slots=True` to frozen dataclasses.
- Renamed httpclient test files for naming consistency.
- Standardized test file docstring format.

## [0.2.2] - 2026-03-31

### Enhancements

- **HTTP Client**: added `HttpClientError` as the common base exception; renamed `ConnectionError` / `TimeoutError` to `HttpConnectionError` / `HttpTimeoutError` to avoid shadowing Python builtins (backward-compatible aliases kept).
- **Config module**: added `ConfigError` base exception for `UndefinedValueError`.
- **Frontmatter module**: `HandlerError` now carries a `handler` context field.
- **VCS module**: `CommandError` now captures partial output on timeout and includes a `timeout` field.

### Internal Improvements

- Standardized error type conventions across all subsystem modules: two-level hierarchy, `<Module><Noun>Error` naming, f-string messages with context fields.
- Documented subprocess execution conventions (binary discovery, timeout, encoding, return codes).
- Documented sync/async API mirroring conventions (naming, phase annotations, shared logic extraction).
- Documented large module internal layering conventions (section markers, ordering, phase annotations).
- All 8 patterns in `internals.md` are now Standardized or Implemented.

## [0.2.1] - 2026-03-30

### Enhancements

- **VCS module**: `Mercurial` and `Jujutsu` constructors accept `merge_func` parameter for explicit three-way merge injection; `detect()` forwards it to the backend.
- **Config module**: `Config` constructor accepts `loaders` and `dotenv_loader` parameters for explicit file-format loader and dotenv injection.
- **SSE module**: `SSEClient` and `AsyncSSEClient` constructors accept `transport` parameter for explicit HTTP transport injection; reconnection error handling adapts automatically.

### Internal Improvements

- Introduced `_Unset` sentinel pattern across vcs, config, and sse modules for three-state injection parameters (`_UNSET` = auto-discover, `None` = disabled, callable = injected).
- Added "Explicit Injection" section to internals documentation (English and Chinese).

## [0.2.0] - 2026-03-30

### New Modules

- **Scheduler module**: zero-dependency in-process task scheduler with cron expression support.
- **Sparse Search module**: BM25 family (BM25, BM25+, BM25L) and TF-IDF full-text search engine.
- **Frontmatter module**: parse and serialize YAML/TOML/JSON file-header metadata.
- **Config module**: unified multi-source configuration loader with env vars, .env files, JSON/JSONC/YAML/TOML/INI support, type coercion, and prefix support.
- **Cache module**: in-memory caching with LRU/FIFO/LFU/TTL eviction, sync+async decorator support, thread-safe, cache statistics.
- **Runner module**: structured subprocess execution with sync+async APIs, streaming output (callbacks + iterators), SIGTERM-to-SIGKILL timeout escalation, environment isolation, and command allowlist/blocklist.
- **XML module**: xmltodict-compatible dict-to-XML converter with LLM tag extraction.

### Enhancements

- **HTTP Client**: connection pooling with configurable pool size and idle timeout.
- **HTTP Client**: transparent gzip/deflate auto-decompression for regular and streaming responses.
- **HTTP Client**: HTTP/HTTPS proxy support with CONNECT tunneling.
- **HTTP Client**: Basic and Digest authentication with automatic 401 challenge-response.
- **VCS module**: workspace, branch, and commit lifecycle operations.
- `zerodep` CLI tool for module discovery and dependency-aware copying.
- **zerodep CLI**: recursive module scanning with nested directory support and duplicate name detection.
- Migrated module metadata from `__version__`/`__deps__` to PEP 723 inline script metadata (frontmatter).
- Reverse index optimization for sparse search performance improvement.

### Bug Fixes

- **Runner**: align async partial output handling and process reaping with sync path.
- **Scheduler**: tighten lock discipline around job state transitions to fix race conditions.
- **HTTP Client**: resolve sync/async drifts and enrich error context.
- **HTTP Client**: resolve `ty` type-check errors.

### Internal Improvements

- **Tier 1 refactoring**: normalize sibling import patterns across config, sse, and vcs modules; lazy-load config sibling modules and diff module in vcs to reduce import-time side effects; align terminal color detection across prompt and structlog; annotate cleanup paths with tier classification comments.
- **Tier 2 refactoring**: reorganize httpclient into 12-layer internal sections for clarity; add 14-section structure and sync/async alignment audit to runner; clarify scheduler concurrency model and add error conventions.

## [0.1.0] - 2026-03-27

### Added

- **AES module**: AES encryption/decryption with ECB, CBC, CTR, and GCM modes; supports 128/192/256-bit keys.
- **QR Code module**: QR code generation with zero external dependencies.
- **HTTP Client module**: synchronous and asynchronous HTTP client with streaming response and file upload support.
- **Dotenv module**: `.env` file parser and loader.
- **YAML module**: YAML parser and emitter.
- **JSONC module**: JSON with Comments (JSONC) parser.
- **Retry module**: configurable retry decorator with backoff strategies.
- **Structured Logging module**: structured logging with JSON output and terminal color support.
- **TOON module**: Token-Oriented Object Notation serializer/deserializer.
- **Tabulate module**: plain-text table formatting.
- **Soup module**: lightweight HTML parsing.
- **Prompt module**: interactive terminal prompt utilities.
- **Validate module**: TypedDict/dataclass runtime validator with JSON Schema generation.
- **SSE module**: Server-Sent Events (SSE) client.
- **Markdown module**: Markdown to HTML renderer.
- **Diff module**: unified and context diff generation.
- **VCS module**: version control system utilities.
- **ANSI module**: ANSI terminal styling with automatic color detection.
- `__version__` attribute added to all modules for cross-module compatibility checks.
- `ty` type checker configuration in `pyproject.toml`.
- CI workflow for compatibility testing across Python 3.10–3.13.

### Fixed

- Async client body reading race condition in HTTP client.
- Type errors across multiple modules detected by `ty` type checker.

### Changed

- Aligned terminal color detection logic across prompt, structlog, and ansi modules.
- Replaced `httpbin.org` with local test server for reliable HTTP correctness tests.

### Removed

- `typing_extensions` dependency from validate module.
