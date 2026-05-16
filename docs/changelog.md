# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### New Modules

- **multipart module**: zero-dependency multipart/form-data parser and encoder per RFC 7578 / RFC 2046. `parse_multipart()` parses request bodies using a boundary-split algorithm with `bytes.find()` for C-level performance. `encode_multipart()` encodes form fields and file uploads. `extract_boundary()` extracts boundary from Content-Type headers. `Part` frozen dataclass with name, data, filename, content_type, headers, `.text` and `.is_file` properties. Robust boundary detection (validates preceding/following bytes to avoid false matches). Content-Transfer-Encoding support (base64, quoted-printable). RFC 5987 `filename*` parameter decoding. Security limits: max_part_size (10 MB), max_parts (1000), max_header_size (16 KB). Single file, ~590 lines, stdlib only. 57 correctness tests + 11 benchmarks (3-7x faster than python-multipart).

### Features

- **httpclient**: Add SOCKS5 proxy support (RFC 1928) with username/password authentication (RFC 1929). Both `Client` and `AsyncClient` now accept `proxy="socks5://[user:pass@]host:port"`. Implemented directly in the module with zero external dependencies. Benchmarked ~6-15x faster than `httpx[socks]`.

### Bug Fixes

- **httpclient**: Remove redundant global `asyncio.Lock()` / `threading.Lock()` from `AsyncClient` / `Client` that serialized concurrent requests and could cause deadlocks. Connection pools already provide internal fine-grained locking.

## [2026.5.2.1] - 2026-05-02

### Bug Fixes

- **CLI**: `version-check` and `bump` no longer incorrectly auto-bump brand-new modules that have no prior release tag. New modules now display `"new (initial release)"` instead of `"new (needs version bump)"` and are excluded from auto-bump targets.
- **Module versions**: Reverted incorrect version bump on 5 new modules — httpserver (0.1.0), websocket (0.1.0), cdp (0.1.0), useragent (0.1.0), synctex (0.2.0).

## [2026.5.2] - 2026-05-02

### New Modules

- **websocket module**: zero-dependency RFC 6455 WebSocket client with sync + async support. `WebSocketClient` and `AsyncWebSocketClient` for `ws://` and `wss://` connections. Full protocol implementation: upgrade handshake, text frame encoding/decoding with client-side masking, ping/pong auto-response, close frame exchange with status codes. Custom headers for auth tokens, subprotocol negotiation, configurable timeouts. Context manager support (`with`/`async with`). TLS with optional certificate verification. Single file, ~1000 lines, stdlib only (`socket`, `ssl`, `asyncio`, `hashlib`, `struct`). 27 correctness tests (sync + async, echo, timeout, custom server, URL parsing) + 8 benchmarks (vs `websockets` — JSON-RPC roundtrip, large payload, burst messages, connection setup).
- **cdp module**: zero-dependency Chrome DevTools Protocol client for headless browser automation. `CDPClient` and `AsyncCDPClient` communicating over WebSocket with command/response ID matching and event buffering. High-level API: `get_rendered_text()` and `get_rendered_html()` for one-call SPA content extraction. Low-level API: `create_target()`, `close_target()`, `navigate()` (with `Page.loadEventFired` waiting), `evaluate()` (with exception propagation), `set_user_agent()`, and raw `send_command()`. Auto-discovers browser debugger WebSocket URL via `/json/version`. Depends on sibling `websocket` module. ~900 lines, stdlib only. 18 correctness tests (mock CDP server + optional real Chromium) + 10 benchmarks (full render pipeline, multi-target, JS eval throughput, command throughput).
- **httpserver module**: zero-dependency async HTTP server with Flask/microdot-compatible decorator-based routing. Built on `asyncio.start_server()` with raw HTTP/1.1 parsing. `@app.route(path, methods=)`, `@app.get()`, `@app.post()` etc. for route registration. Path parameters with type conversion (`<name>`, `<int:id>`, `<float:price>`, `<path:filepath>`). Return value coercion (dict → JSON, str → text, bytes → binary, tuple → status/headers, None → 204). `StreamingResponse` with chunked encoding for SSE. `FileResponse` for static file serving with directory traversal prevention. `before_request`/`after_request`/`errorhandler` middleware hooks. Sync handlers auto-wrapped via `asyncio.to_thread()`. Graceful shutdown with SIGINT/SIGTERM handling. Single file, ~1000 lines, stdlib only. 58 correctness tests + 26 benchmarks (vs Flask, microdot, bottle — serial, concurrent, sync/async, large payload).
- **SyncTeX module**: zero-dependency SyncTeX parser for bidirectional search between PDF and source. Parses `.synctex` and `.synctex.gz` files produced by TeX engines. `parse_synctex()` extracts input file mappings, page hbox records, and preamble metadata. `inverse_search()` maps PDF page coordinates back to source file and line number using a multi-phase spatial matching algorithm. `forward_search()` maps source file and line number to PDF page coordinates. Supports configurable path prefix stripping for Docker/remote builds. 29 correctness tests.
- **useragent module**: lightweight Chrome/Edge User-Agent string generator with Client Hints headers. `generate()` creates realistic UA strings with matching `Sec-CH-UA-*` headers for Windows, macOS, Linux (desktop) and Android (mobile). Supports low-entropy hints (always included) and high-entropy hints via `accept_ch()` (platform version, architecture, bitness, model, full version list). Deterministic output via `random.seed()`. Single file, ~470 lines, stdlib `random` only. 47 correctness tests + 8 benchmarks (2-3x faster than ua-generator). Inspired by [ua-generator](https://github.com/iamdual/ua-generator) (Apache-2.0).

### Infrastructure

- Added `websockets` to benchmark CI workflow for websocket and cdp performance tracking.
- Added `ua-generator` to benchmark CI workflow for useragent performance tracking.
- Added automated PyPI publish workflow (`.github/workflows/pypi.yml`) triggered on GitHub Release, with change detection to skip version-only bumps.
- Added `AGENTS.md` (unified AI coding assistant instructions) with `CLAUDE.md` symlink for cross-tool compatibility (Claude Code, Codex, Cursor, Copilot, Gemini CLI).

### Enhancements

- **CLI**: added `--from FILE` flag to `zerodep new` for creating modules from existing Python source files. Automatically injects frontmatter if missing (respects shebang/encoding lines), preserves existing frontmatter with CLI override support, and warns on third-party imports.

## [2026.4.27] - 2026-04-27

### New Modules

- **llms.txt module**: zero-dependency parser for the [llms.txt specification](https://llmstxt.org/). `parse()` extracts structured data (title, description, details, H2 sections, Optional entries) from llms.txt files. `find_candidates()` provides unified URL discovery — searches parsed llms.txt entries (exact > extension variation > path prefix) with heuristic `.md` URL fallback when no llms.txt is available. `discover()` probes any URL's root for `/llms.txt` and `/llms-full.txt`, returning raw content via `DiscoveryResult`. Frozen dataclasses (`LlmsTxt`, `FileEntry`, `DiscoveryResult`) for immutable results. 55 correctness tests + 4 benchmarks.
- **PNG module**: zero-dependency PNG/BMP image codec with matrix compression API. `decode_png`/`encode_png` for PNG images (grayscale/RGB/RGBA, 8/16-bit, all 5 row filters), `decode_bmp`/`encode_bmp` for BMP (24/32-bit uncompressed), `convert()` for mode conversion between L/LA/RGB/RGBA, and `matrix_to_png`/`png_to_matrix` for 2D numeric data compression via PNG row filters with lossless float round-trip through tEXt metadata. 104 correctness tests (apple-to-apple vs Pillow) + 24 benchmark tests.

### New Features

- **Protobuf module**: added `byte_size()` method for computing serialized message size without materializing bytes. Useful for pre-allocating buffers and protocol frame length calculation.
- **QR module**: added `qr_to_svg()` and `qr_to_png()` for rendering QR codes as SVG and PNG images. SVG uses a single `<path>` element (zero deps); PNG renders grayscale via sibling `png` module (lazy import). Both support configurable scale, quiet zone border, and foreground/background colors. 24 render tests.
- **Validate module**: added `FieldValidator` and `model_validator` for custom validation logic. `FieldValidator` is an `Annotated`-based constraint that can transform values and raise `ValueError`/`AssertionError` on failure (unlike `Predicate` which only returns bool). `model_validator` is a decorator to register cross-field validators on TypedDict/dataclass types, run after all field validation passes. 18 new tests. Version 0.4.2 → 0.5.0.
- **Sparse Search module**: added post-retrieval re-ranking utilities for hybrid search and RAG pipelines. `rrf()` implements Reciprocal Rank Fusion (Cormack et al., SIGIR 2009) for merging multiple ranked result lists (e.g. BM25 sparse + dense vector search) with per-list weights and top_k truncation. `mmr()` implements Maximal Marginal Relevance for result diversification with user-provided similarity function and internal min-max score normalization. `jaccard_similarity()` provides a set-based similarity building block for MMR. All three are standalone functions operating on generic `list[Result]`. 31 new correctness tests + 5 benchmarks. Version 0.3.2 → 0.4.0.

### Enhancements

- **Markdown module**: added GFM strikethrough (`~~text~~` → `<del>`), task lists (`- [ ]` / `- [x]` with checkbox and class attributes), and extended autolinks (bare `https://` / `http://` URLs auto-linked with trailing punctuation stripping). All outputs match mistune with GFM plugins. 28 new correctness tests + 4 GFM benchmarks. Version 0.3.1 → 0.4.0.
- **Soup module**: added CSS pseudo-selector support — `:first-child`, `:last-child`, `:only-child`, and `:not(selector)`. Covers the most commonly needed structural pseudo-classes. `:not()` accepts any simple selector (tag, class, ID, attribute, or nested pseudo). Added CSS select and pseudo-select benchmarks. Version 0.5.0 → 0.6.0.

### Performance

- **PNG module**: optimized BMP codec, PNG row filters, and mode conversion. BMP decode/encode replaced per-pixel BGR↔RGB loops with `bytearray` slice assignment (C-level ops) — **42-44x speedup** (from 193-265x slower to ~4.6-6.1x slower vs Pillow). PNG row filters optimized: list comprehension + `zip` for Up filter, prefix handling for Sub filter, local variable caching for Paeth. Pre-allocated pixel buffers in decode/encode paths. 7 lossless mode conversions (L↔RGB↔RGBA etc.) converted from per-pixel loops to slice operations. PNG decode/encode ~10% faster overall.
- **Protobuf module**: comprehensive encode/decode optimization — encoder dispatch binding on FieldInfo (eliminates 11-way if/elif), per-field specialized `_is_default` checks, inline 1-byte tag decode fast-path (field numbers 1-15), write-to-buffer varint/scalar encoders (eliminates intermediate `bytes` allocation), cached map entry type metadata (`_MapMeta`), batch message construction via `__dict__.update`. Encode **~41-65% faster**, decode **~7-27% faster**, roundtrip **~39% faster** for large messages.

### Infrastructure

- Refined module categories from 7 to 12 fine-grained groups: network, protocol, serialization, validation, text, config, terminal, crypto, image, process, storage, devtools.
- Renamed `scripts/` → `_scripts/` (internal convention).
- Auto-generate `modules/index.md` during docs build from `manifest.json` + config.
- Fixed `version-check` false positives caused by old project-level SemVer tag collisions and wrong primary file selection.

## [2026.4.25] - 2026-04-25

### New Modules

- **JSON Schema module**: zero-dependency JSON Schema flattening & sanitization. `flatten_schema()` resolves `$ref`, merges `allOf` (deep-merge with type intersection, numeric constraint tightening, required union), simplifies `anyOf`/`oneOf` (nullable detection, single-variant unwrap), and strips unsupported keywords. Each phase is independently callable: `resolve_refs`, `merge_allof`, `simplify_unions`, `sanitize`. Benchmarked against `allof-merge` (JS) across 5 complexity tiers — **1.7-5.3x faster**. 57 unit tests + 13 cross-implementation correctness tests.
- **Readability module**: zero-dependency article content extractor ported from Mozilla Readability.js. `extract()` performs full article extraction with metadata (title, author, excerpt, published_time, site_name, lang, dir). `is_probably_readable()` provides a quick readability heuristic check. Supports JSON-LD and OpenGraph metadata extraction. 2-level retry (ruthless on/off) for robust extraction. 18 Mozilla Readability.js test fixtures for cross-validation. Three-way benchmark: zerodep vs readability-lxml vs Mozilla JS. Depends on `soup` module (no pip dependencies).

### Enhancements

- **Soup module**: extended with tree mutation and serialization APIs — `append()`, `insert()`, `extract()`, `replace_with()`, `unwrap()` for tree manipulation; `to_html()` / `__str__()` for HTML serialization; `__setitem__` / `__delitem__` for attribute setting/deletion; `Soup.new_tag()` factory method for creating detached Tag nodes.

### Performance

- **A2A module**: optimized serialization and deserialization paths — `to_dict()` now avoids `dataclasses.asdict()`-style deep copy overhead. Serialization is now **2.2-2.6x faster** than a2a-protocol (previously 1.4-2.1x slower). Deserialization narrowed from 1.8-4.1x slower to **1.1-1.7x slower** via optimized enum resolution and type dispatch. JSON round-trip is now **1.4-1.5x faster** end-to-end.
- **Cache module**: optimized `TypedKey` construction, decorator wrapper path, and LFU eviction. LRU decorator overhead is now **1.2x faster** than cachetools. TTL decorator reached parity. LFU eviction now **~equal** (previously 1.4x slower).
- **PersistDict module**: optimized SQLite write performance — `PRAGMA synchronous=NORMAL`, `commit_every` parameter for batched writes, deferred commits.
- **QR module**: optimized encoding path — short inputs now only 1.1x slower (previously 2.1x). Medium/long inputs now **1.1-1.2x faster** (previously 1.7-1.9x slower).
- **Readability module**: optimized scoring and tree-walking — small pages **2.1x faster**, medium pages now **1.2x faster** (previously 2x slower). Large pages improved from 2x slower to 1.4x slower vs readability-lxml.
- **Semver module**: optimized parse, comparison, and property access. Parse **~1.3x faster**, sort **~1.4x faster**, compare **~1.4x faster**, property access **~4.5x faster**.

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
