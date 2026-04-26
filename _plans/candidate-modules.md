# zerodep — Module Candidates

## 1. Extensions to Existing Modules

Incremental features that add clear value to shipped modules.

### qr → Image Output

Terminal half-block rendering is the only output format. PNG (via `zlib` + `struct`) and SVG (string templating) are both stdlib-achievable and cover the two most common non-terminal use cases.

- **PNG**: pairs with a potential standalone `png` module (shared encoder)
- **SVG**: simpler, no binary encoding, good for web embedding

### sparse_search → Hybrid Fusion / MMR

The sparse engine (BM25/TF-IDF) is complete. Two lightweight additions sit on top without touching the core index:

- **RRF (Reciprocal Rank Fusion)**: merge sparse + external dense results into a single ranking. ~50 lines, no deps, high RAG value.
- **MMR (Maximal Marginal Relevance)**: result diversification. Requires a similarity function but no index changes.

Both accept pre-computed result lists, so they work regardless of where the dense scores come from.

### markdown → GFM Strikethrough + Task Lists

Two commonly expected GFM extensions missing from the current CommonMark subset:

- `~~strikethrough~~` → `<del>` — small parser addition
- `- [ ] task` / `- [x] task` → checkbox list items — small renderer addition

Low effort, high perceived completeness.

### soup → CSS Pseudo-selectors

Current selector engine covers tag, class, id, attributes, combinators, and `:nth-child()`. The most commonly needed additions:

- `:first-child`, `:last-child`, `:only-child` — trivial index checks
- `:not(selector)` — invert match of a simple selector

These cover the majority of real-world CSS selector usage beyond what's already supported.

### validate → Field / Model Validators

The biggest API gap vs pydantic. Currently there's no hook for custom per-field or cross-field validation logic beyond `Predicate`. Adding:

- `@field_validator("field_name")` equivalent for TypedDict/dataclass
- `@model_validator` for cross-field checks

would close the most common complaint about the subset.

### aes → PBKDF2 Key Derivation Convenience

"Encrypt this with a password" is the #1 use case. `hashlib.pbkdf2_hmac` is already in stdlib — wrapping it as `derive_key(password, salt, key_size)` with sensible defaults (iterations, hash algo) is trivial and saves every user from re-inventing the same 5-line wrapper.

### qr → PNG / SVG Output (standalone encoder)

PNG encoding (via `zlib` + `struct`) is ~80 lines and could live as a small internal helper or a standalone `png` module that QR imports via sibling path. SVG is even simpler (string templating). Either would eliminate the "terminal only" limitation that is the module's biggest gap.

## 2. New Modules

### Tier 1 — High Value

#### Rate Limiter
- **Replaces**: ratelimit, aiolimiter
- **Why**: every LLM API caller needs this; no stdlib equivalent
- **Scope**: token bucket and/or sliding window, sync + async, decorator interface, per-key limits
- **stdlib basis**: time, threading, asyncio

### Tier 2 — Valuable, Moderate Complexity

#### WebSocket Client
- **Replaces**: websockets, websocket-client
- **Why**: real-time AI APIs (OpenAI Realtime, etc.), agent streaming — growing demand from LLM ecosystem
- **Scope**: RFC 6455 client, text/binary frames, ping/pong, close handshake, sync + async
- **stdlib basis**: asyncio, hashlib, struct, ssl
- **Note**: subsystem-level complexity comparable to httpclient; websockets lib has moderate weight (~500 KB + deps)

#### JWT (JSON Web Tokens)
- **Replaces**: PyJWT, python-jose
- **Why**: agent-to-agent auth (A2A, ACP), API gateway tokens; trivial implementation (~150 lines) over pure stdlib
- **Scope**: HS256/HS384/HS512 signing + verification, encode/decode, claims validation (exp, nbf, iss, aud)
- **stdlib basis**: hmac, hashlib, base64, json
- **Note**: PyJWT is already zero-dep and lightweight (37 KB). Value is ecosystem coherence, not weight reduction

## 3. Not Worth Doing

Things that sound valuable but don't fit the single-file, zero-dep, pure-Python constraints.

### YAML Anchors / Aliases / Tags

The full YAML spec (anchors, aliases, merge keys, custom tags, complex keys) is enormous. Edge cases around circular references, tag resolution, and merge semantics make a correct implementation very hard to maintain in a single file. Our subset covers 95%+ of real-world config files. Users needing full YAML should use PyYAML.

### HTTP/2 / HTTP/3

HTTP/2 requires HPACK header compression, multiplexed streams, flow control, and server push handling. HTTP/3 adds QUIC (UDP-based transport). The protocol complexity is far beyond single-file scope. httpx + httpcore + h2 exist precisely because this is a multi-thousand-line problem. Our HTTP/1.1 client covers REST API consumption well.

### Dense Vector Search (without numpy)

Pure Python matrix operations are 100-1000x slower than numpy for dot products and distance calculations at any meaningful scale. A zero-dep vector search engine would be unusably slow for datasets beyond a few hundred documents. Users doing embedding-based search already have numpy in their stack. The sparse engine's RRF fusion can accept externally computed dense scores without us owning the dense index.

### Full Pydantic Replacement (BaseModel)

Pydantic's full surface area — BaseModel, field/model validators, computed fields, serialization modes, settings management, plugin system — is massive. Our `validate` module targets TypedDict/dataclass validation (the 80% use case) and should stay focused there. Chasing BaseModel parity means competing with pydantic-core's Rust performance on their turf.

### Template Engine (Jinja2 Clone)

Jinja2 is ~1 MB with only one dependency (MarkupSafe, which has a pure Python fallback). Replacement value is very low. Building a feature-complete template engine (inheritance, macros, sandboxing, autoescaping, custom loaders) is a subsystem-scale effort for minimal dependency savings. Python's `str.format` and `string.Template` cover simple cases.

### proto2 / gRPC Services

proto2 is legacy; new projects use proto3. gRPC requires HTTP/2 (see above), TLS, and a complex service definition layer. Our protobuf module targets the "decode/encode proto3 without installing google-protobuf" use case and should stay there.

### Distributed / Persistent Scheduler

Distributed scheduling requires consensus, leader election, and shared state — all far beyond single-file scope. Persistent job stores (database-backed) pull in I/O complexity and schema management. Our scheduler targets in-process task scheduling and should stay there. Users needing distributed scheduling should use Celery/APScheduler with a broker.

### Additional Symmetric Ciphers (ChaCha20, DES, 3DES)

AES is the universal standard. Adding other ciphers expands the maintenance surface without proportional user value. Users needing ChaCha20-Poly1305 or legacy ciphers typically need a full crypto library (key exchange, signatures, certificates) which is fundamentally beyond zero-dep scope.

### Event Emitter

Simple pub/sub is ~30 lines of Python. The libraries it would replace (pyee, pymitter) are already tiny. A zerodep module adds no meaningful value over `dict[str, list[Callable]]` with a thin wrapper. Not worth the maintenance cost.

### TOTP/HOTP

pyotp is already zero-dep and tiny (15 KB). The implementation is ~80 lines of HMAC math. QR synergy exists but the use case is narrow — most TOTP users are in web apps where they already have dependencies. Not enough standalone value.

### Slug / Base58 / Color

Too trivial or too niche:
- **Slug**: `re.sub` + `unicodedata.normalize` — 5-10 lines, not worth a module
- **Base58**: blockchain-only encoding, tiny user base
- **Color**: `colorsys` is already in stdlib; the gap is minimal

### MessagePack

protobuf already covers efficient binary serialization. Adding a second binary format creates ecosystem confusion about which to recommend. msgpack's pure-Python fallback is already lightweight.

### Full CommonMark Compliance

The CommonMark spec has hundreds of edge cases around emphasis precedence, link reference resolution, list continuation, and lazy paragraph continuation. Our subset handles real-world markdown well. Chasing 100% spec compliance means an explosion of parser complexity for diminishing returns.
