# zerodep — Module Roadmap

## Completed

Modules with implementation, correctness tests, and benchmarks.

| Module | Replaces | Scope | Benchmark Against |
|--------|----------|-------|-------------------|
| `aes/` | pycryptodome | ECB/CBC/CTR/GCM modes, AES-128/192/256, pure Python + OpenSSL ctypes, PKCS7 padding, GCM AEAD authentication | pycryptodome |
| `qr/` | qrcode | ISO 18004 QR Code Model 2, versions 1-40, all 4 ECC levels, numeric/alphanumeric/byte/ECI encoding | qrcode |
| `httpclient/` | httpx | Sync + async HTTP/1.1 REST client, streaming responses, multipart uploads, auto-redirect, SSL verification, Client/AsyncClient sessions, connection pooling, auto decompression, proxy support, Basic/Digest auth | httpx |
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
| `frontmatter/` | python-frontmatter | Parse and serialize YAML/TOML/JSON file-header metadata, Document model, loads/dumps/load/dump API, auto-detect format | python-frontmatter |
| `config/` | python-decouple, dynaconf (subset) | Unified config loading from env vars, .env files, JSON/JSONC/YAML/TOML/INI files, type coercion (bool/int/float/list), Csv/Choices helpers, prefix support, nested key access | python-decouple |

### Competitive Analysis (2026-03-28)

How much value does each zerodep module provide over the original library?

**Strong** — replaces heavy C extensions or deep dependency chains, or offers architectural advantages:

| Module | Replaces | Original Weight | zerodep Advantage |
|--------|----------|----------------|-------------------|
| `httpclient` | httpx | 7 transitive deps (httpcore, h11, anyio, sniffio, certifi, idna), ~3.7 MB total | Eliminates deepest dependency chain in the collection |
| `validate` | pydantic | pydantic-core 4.6 MB C extension + 4 deps, ~8.4 MB total | Eliminates heaviest C extension; cross-platform compilation pain |
| `aes` | pycryptodome | ~4.8 MB platform-specific C extension wheels | Pure Python + OpenSSL ctypes dual path; no compilation needed |
| `search` | rank-bm25 | Full corpus scan O(N) per query | Inverted index: **35-131x faster search**; architectural superiority |

**Moderate** — eliminates C extensions or indirect dependency chains:

| Module | Replaces | Original Weight | zerodep Advantage |
|--------|----------|----------------|-------------------|
| `yaml` | PyYAML | 2.3 MB C extension (libyaml binding) | No C compilation; but feature subset (no anchors/aliases) |
| `soup` | beautifulsoup4 | Depends on soupsieve (~256 KB) + typing-extensions | Eliminates soupsieve dependency |
| `qr` | qrcode | Optional dep on Pillow (~50 MB) for image output | Terminal rendering without Pillow |
| `frontmatter` | python-frontmatter | Depends on PyYAML (2.3 MB C ext) | Eliminates transitive PyYAML dependency |
| `jsonc` | commentjson | Depends on lark-parser (~276 KB parser framework) | Much lighter; no parser framework needed |
| `scheduler` | APScheduler | Moderate weight, async support varies | Unified sync+async, lighter |
| `sse` | httpx-sse | Depends on httpx (see above) | Pairs with zerodep httpclient to eliminate full httpx chain |

**Convenience** — original library is already zero-dep and lightweight; value is mainly single-file vendoring and zerodep ecosystem coherence:

| Module | Replaces | Original Weight | Note |
|--------|----------|----------------|------|
| `dotenv` | python-dotenv | Zero deps, 104 KB, pure Python | Original already lightweight |
| `retry` | tenacity | Zero deps, 184 KB, pure Python | Original already lightweight |
| `structlog` | structlog | Zero deps, 72 KB, pure Python | Original already lightweight |
| `tabulate` | tabulate | Zero deps, 30 KB, pure Python | Original already lightweight |
| `markdown` | mistune | Near-zero deps, 53 KB | Original already lightweight |
| `diff` | unidiff | Zero deps, 14 KB | Original smaller than our impl |
| `toon` | toon_format | Niche format | Ecosystem value, not replacement value |
| `config` | python-decouple | Zero deps, lightweight | Synergy with dotenv/yaml/jsonc modules |
| `ansi` | — | No direct competitor | Utility module, no replacement story |
| `vcs` | — | No direct competitor | Utility module, no replacement story |
| `prompt` | — | No direct competitor | Utility module, no replacement story |

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
- **Competitive note**: Jinja2 only depends on MarkupSafe (67 KB C ext, has pure Python fallback). Total ~1 MB. Replacement value is **low** — Jinja2 is already lightweight. Only justified if adding differentiated features (e.g. stream_parse for LLM output extraction) or for zerodep ecosystem completeness

### Cache
- **Replaces**: cachetools, diskcache (in-memory subset)
- **Why**: In-memory caching with TTL and eviction goes beyond stdlib `lru_cache` — commonly needed for API response caching, memoization with expiry. cachetools is used by google-auth (large downstream). stdlib `lru_cache` has no TTL, no eviction policies beyond LRU, no async support
- **stdlib basis**: threading, time, collections
- **Scope**: TTL cache, LRU/LFU/FIFO eviction, per-key TTL, max size with eviction, decorator interface, sync + async, cache stats
- **Benchmark against**: cachetools
- **Competitive note**: cachetools is zero-dep (184 KB) but lacks async support entirely. Our async cache decorator would be a genuine differentiator. Cache classes: LRUCache, TTLCache, LFUCache, FIFOCache + `@cached`/`@acached` decorators

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

### XML
- **Replaces**: xmltodict (dict ↔ XML layer) + custom LLM tag extraction
- **Why**: XML remains common in enterprise APIs, RSS, SVG, and increasingly in LLM prompt/output structuring; stdlib `xml.etree.ElementTree` is strict and verbose
- **stdlib basis**: xml.etree.ElementTree, re
- **Scope**:
  - **Standard layer**: `loads(xml) → dict`, `dumps(dict) → xml` — xmltodict-style bidirectional conversion, attribute handling, namespace support
  - **Lenient layer**: `extract_tags(text, tag)` — fault-tolerant extraction of XML-like tags from LLM output (unclosed tags, malformed nesting, streaming-friendly)
- **Synergy**: soup (HTML counterpart), frontmatter (metadata extraction), toon (LLM-optimized format)
- **Benchmark against**: xmltodict

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

Prioritized by replacement value (dependency weight eliminated + feature gap filled):

1. **Cache** — fills a real stdlib gap (no TTL/eviction/async in `lru_cache`), async support differentiates from cachetools
2. **Rate limiter** — essential for API management, every LLM app needs this
3. **JWT** — auth layer, widely needed for web/API projects
4. **WebSocket client** — real-time APIs (OpenAI Realtime, etc.)
5. **Semver** — lightweight but broadly useful
6. **Template engine** — Jinja2 is already lightweight (~1 MB, 1 dep); only worthwhile with differentiated features or for ecosystem completeness

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
