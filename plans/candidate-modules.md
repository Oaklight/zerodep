# zerodep — Module Roadmap

## Completed

Modules with implementation, correctness tests, and benchmarks.

| Module | Replaces | Scope | Benchmark Against |
|--------|----------|-------|-------------------|
| `aes/` | pycryptodome | ECB/CBC/CTR/GCM modes, AES-128/192/256, pure Python + OpenSSL ctypes, PKCS7 padding, GCM AEAD authentication | pycryptodome |
| `qr/` | qrcode | ISO 18004 QR Code Model 2, versions 1-40, all 4 ECC levels, numeric/alphanumeric/byte/ECI encoding | qrcode |
| `httpclient/` | httpx | Sync + async HTTP/1.1 REST client, streaming responses, multipart uploads, auto-redirect, SSL verification, Client/AsyncClient sessions | httpx |
| `dotenv/` | python-dotenv | load_dotenv, dotenv_values, find_dotenv, get/set/unset_key, variable interpolation, export prefix, escape sequences | python-dotenv |
| `yaml/` | PyYAML | Parser + serializer for common YAML subset (mappings, sequences, flow style, block scalars, multi-document, type resolution; no anchors/aliases/tags) | PyYAML |
| `jsonc/` | commentjson | JSON with `//`, `#`, `/* */` comments and trailing commas, drop-in replacement for stdlib json | commentjson |
| `structlog/` | structlog | Processor pipeline, bound loggers, console/JSON/key-value renderers, stdlib Logger wrapping, colored output | structlog |
| `toon/` | toon_format | TOON encoder/decoder, tabular mode, customizable delimiters (comma/tab/pipe), 30-60% token reduction vs JSON | toon_format |
| `retry/` | tenacity | @retry decorator + retry_call(), exponential/linear/fixed backoff, full/equal/none jitter, exception/result/status predicates, sync + async, on_retry callback | tenacity |
| `tabulate/` | tabulate | Multiple table formats (plain, simple, grid, pipe, github, rst, latex, html, mediawiki, etc.), column alignment, number formatting, CJK-aware widths | tabulate |
| `validate/` | pydantic (subset) | validate() for TypedDict/dataclass, Annotated constraints (Gt/Ge/Lt/Le/MinLen/MaxLen/Match/Predicate), discriminated unions, type coercion, json_schema() generation | pydantic |
| `sse/` | httpx-sse | Low-level SSE parser + high-level client with auto-reconnect, exponential backoff, sync + async, depends on httpclient | httpx-sse |
| `soup/` | beautifulsoup4 | HTML parser with find/find_all/select/CSS selectors, built on stdlib html.parser | beautifulsoup4 |
| `prompt/` | questionary | confirm/select/text prompts, arrow key navigation, ANSI colors, cross-platform (termios + msvcrt) | — |
| `markdown/` | mistune | CommonMark subset (ATX/Setext headings, emphasis, code spans/blocks, links, images, lists, blockquotes, thematic breaks, backslash escapes, autolinks, hard breaks) + GFM tables | mistune |
| `diff/` | unidiff | Unified diff parser, patch applicator, three-way merge, conflict markers | unidiff |
| `vcs/` | — | VCS CLI wrapper (Git/SVN/Hg backend protocol), status/log/blame/diff, subprocess-based | — |
| `ansi/` | — | ANSI escape code primitives, fg/bg/style helpers, color depth detection, strip_ansi, visible_len, cursor control | — |
| `scheduler/` | APScheduler | In-process task scheduler, 5-field cron expressions, interval/one-shot triggers, async jobs, per-job callbacks, event listeners, job pause/resume, misfire grace time | APScheduler, croniter, schedule |
| `search/sparse_search` | rank-bm25 | BM25/BM25+/BM25L/BM25F + TF-IDF+Cosine, inverted index with reverse index for fast delete, dynamic add/remove/update, metadata filtering, JSON/SQLite persistence, pluggable tokenizer | rank-bm25 |

## httpclient Pending Features

- Connection pooling — pool keyed by (host, port, scheme), keep-alive, stale connection detection. Currently each request creates a new connection.

## Tier 1 — High Value, Not Yet Started

### Rate Limiter
- **Replaces**: ratelimit, aiolimiter
- **Why**: LLM APIs all have rate limits. Token bucket / sliding window needed for managing API calls.
- **stdlib basis**: time, threading, asyncio
- **Scope**: Token bucket and/or sliding window, sync + async, decorator interface, per-key limits
- **Benchmark against**: ratelimit, aiolimiter

### JWT (JSON Web Tokens)
- **Replaces**: PyJWT, python-jose
- **Why**: API gateway auth, OAuth, agent-to-agent authentication
- **stdlib basis**: hmac, hashlib, base64, json
- **Scope**: HS256/HS384/HS512 signing + verification, encode/decode, claims validation (exp, nbf, iss, aud)
- **Benchmark against**: PyJWT

### Template Engine
- **Replaces**: Jinja2 (subset)
- **Why**: Code generation, email templates, config file rendering, LLM prompt templating — Jinja2 is a heavy dependency with MarkupSafe C extension
- **stdlib basis**: re, string
- **Scope**: Variable substitution (`{{ var }}`), conditionals (`{% if %}`), for loops (`{% for %}`), filters (`{{ x | upper }}`), template inheritance (`{% extends %}`), includes, auto-escaping
- **Benchmark against**: Jinja2

### Cache
- **Replaces**: cachetools, diskcache (in-memory subset)
- **Why**: In-memory caching with TTL and eviction goes beyond stdlib `lru_cache` — commonly needed for API response caching, memoization with expiry
- **stdlib basis**: threading, time, collections
- **Scope**: TTL cache, LRU cache, per-key TTL, max size with eviction, decorator interface, sync + async, cache stats
- **Benchmark against**: cachetools

## Tier 2 — Valuable, Moderate Complexity

### WebSocket Client
- **Replaces**: websockets, websocket-client
- **Why**: OpenAI Realtime API, agent real-time communication
- **stdlib basis**: asyncio, hashlib, struct, ssl
- **Scope**: RFC 6455 client, text/binary frames, ping/pong, close handshake, sync + async
- **Benchmark against**: websockets

### Semver
- **Replaces**: semver, packaging.version
- **Why**: Version comparison, dependency resolution, release management
- **stdlib basis**: re
- **Scope**: Parse, compare, bump (major/minor/patch), range matching (^, ~, >=, etc.), pre-release/build metadata
- **Benchmark against**: semver

### Config
- **Replaces**: python-decouple, dynaconf (subset)
- **Why**: Unified config loading from multiple sources with type coercion — a common pattern in 12-factor apps
- **stdlib basis**: os, json
- **Scope**: Load from env vars, .env files, JSON/YAML/TOML files, type coercion (int, bool, list), defaults, required checks, prefix support
- **Synergy**: dotenv, yaml, jsonc modules

### Event Emitter
- **Replaces**: pyee, pymitter
- **Why**: Decoupled pub/sub within applications, plugin systems, middleware hooks
- **stdlib basis**: threading, asyncio, inspect
- **Scope**: on/off/once/emit, wildcard patterns, typed events, sync + async handlers, max listeners

## Tier 3 — Niche but Useful

### TOTP/HOTP
- **Replaces**: pyotp
- **stdlib basis**: hmac, hashlib, struct, time
- **Scope**: RFC 4226 (HOTP) + RFC 6238 (TOTP), URI generation for QR codes
- **Synergy**: QR module can render TOTP provisioning URIs

### Base58
- **Replaces**: base58
- **stdlib basis**: Pure math
- **Scope**: encode/decode, check encoding (Bitcoin-style)

### MessagePack
- **Replaces**: msgpack
- **stdlib basis**: struct
- **Scope**: Pack/unpack, compatible with msgpack spec

### PNG Encoder
- **Replaces**: Pillow (for simple generation)
- **stdlib basis**: zlib, struct
- **Scope**: Generate simple PNG images
- **Synergy**: QR module could output PNG directly

### Slug
- **Replaces**: python-slugify
- **stdlib basis**: re, unicodedata
- **Scope**: Unicode text to URL-safe slug, transliteration, custom separator, max length

### Color
- **Replaces**: colour, colormath (subset)
- **stdlib basis**: colorsys (stdlib), re
- **Scope**: Parse/convert between hex, RGB, HSL, HSV; named colors; darken/lighten/mix
- **Synergy**: ansi module

## Recommended Priority Order (remaining work)

1. **Rate limiter** — essential for API management, every LLM app needs this
2. **JWT** — auth layer, widely needed for web/API projects
3. **Template engine** — replaces a heavy dep (Jinja2+MarkupSafe), broad use cases
4. **Cache** — goes beyond stdlib lru_cache, very practical
5. **WebSocket client** — real-time APIs (OpenAI Realtime, etc.)
6. **Semver** — lightweight but broadly useful

## search/ — Architecture & Optimization Notes

### Module structure

`search/` is a top-level directory designed for multiple search-related single-file modules:

| File | Status | Scope |
|------|--------|-------|
| `sparse_search.py` | Done | BM25 family + TF-IDF, inverted index, persistence |
| `dense_search.py` | Planned | Vector search (HNSW/LSH/brute-force), accept external embeddings |
| `fusion.py` | Planned | RRF / linear hybrid fusion of sparse + dense results |
| `mmr.py` | Planned | Maximal Marginal Relevance for result diversification |

### BM25 variant coverage

Single unified implementation with parameter-driven variant selection:

- **BM25** (delta=0): classic Okapi BM25
- **BM25+** (delta>0): lower-bound TF correction (Lv & Zhai 2011)
- **BM25L** (variant="bm25l"): long-document penalty fix (Lv & Zhai 2011)
- **BM25F** (field_weights={...}): multi-field weighted search
- **TF-IDF** (variant="tfidf"): cosine similarity ranking
- All combinations compose freely (e.g. BM25LF+ = bm25l + field_weights + delta)

Deferred: **BM25TP** (term proximity), **BM25T/BM25-adpt** (require training data).

### Tokenizer decision

No separate tokenizer module. `sparse_search.py` provides a basic default tokenizer (Unicode word split + lowercase). Interface accepts `Callable[[str], list[str]]` for external tokenizers (e.g. `jieba.lcut` for Chinese).

Rationale: tokenization is a deep domain (CJK, stemming, phonetics, etc.); a shallow zero-dep implementation adds little value. Users in RAG projects typically already have a tokenizer.

### Performance vs rank-bm25

| Operation | sparse_search | rank-bm25 | Ratio |
|-----------|--------------|-----------|-------|
| Search (200 docs) | 1.8 μs | 61.6 μs | **35x faster** |
| Search (1000 docs) | 1.8 μs | 239 μs | **131x faster** |
| Indexing (1000 docs) | 47 ms | 8.6 ms | 5.5x slower |

Search speed advantage: inverted index traverses only matching postings O(matched_docs) vs rank-bm25's full corpus scan O(N). Indexing slower due to richer structures (reverse index, metadata, persistence support).

### Optimization investigation (2026-03-28)

Three optimizations were prototyped in a `sparse_search_fast.py` variant and benchmarked:

| Optimization | Target | Result | Adopted? |
|-------------|--------|--------|----------|
| **Counter batch counting** — `Counter(tokens)` then bulk write instead of per-token dict update | `_insert` | No improvement; unique term ratio too high, Counter object overhead negates C-side counting | No |
| **Reverse index** — `_doc_terms: dict[str, set[str]]` so delete scans only the doc's terms, not entire vocab | `_delete` | **12.9x faster** (2.9ms vs 37ms for 100 deletes from 1000 docs) | **Yes** |
| **SQLite in-memory batch** — `sqlite3.connect(":memory:")` + `executemany` + `GROUP BY` for bulk insert | `add_batch` | 2.8x slower; SQLite overhead exceeds Python dict at this scale | No |
| **Flat composite key** — `(term, doc_id, field)` single dict instead of 3-level nesting | Not prototyped | Rejected at design stage: breaks O(1) `_index[term]` lookup needed for search, would require secondary index that recreates 2-level nesting | No |

Conclusion: only the reverse index optimization provides a real improvement. Python dicts are already C-backed hash maps; the bottleneck is Python interpreter loop overhead, not the data structure itself. ctypes to system C libraries (libc) cannot bypass this.
