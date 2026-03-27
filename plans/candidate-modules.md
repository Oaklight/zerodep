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
| `sse/` | httpx-sse | Low-level SSE parser + high-level client with auto-reconnect, exponential backoff, sync + async, depends on httpclient | — |
| `soup/` | beautifulsoup4 | HTML parser with find/find_all/select/CSS selectors, built on stdlib html.parser | beautifulsoup4 |
| `prompt/` | questionary | confirm/select/text prompts, arrow key navigation, ANSI colors, cross-platform (termios + msvcrt) | — |
| `markdown/` | mistune | CommonMark subset (ATX/Setext headings, emphasis, code spans/blocks, links, images, lists, blockquotes, thematic breaks, backslash escapes, autolinks, hard breaks) + GFM tables | mistune |

## httpclient Pending Features

- Connection pooling — pool keyed by (host, port, scheme), keep-alive, stale connection detection. Currently each request creates a new connection.

## Tier 1 — High Value, Not Yet Started

### JWT (JSON Web Tokens)
- **Replaces**: PyJWT, python-jose
- **Why**: API gateway auth, OAuth, agent-to-agent authentication
- **stdlib basis**: hmac, hashlib, base64, json
- **Scope**: HS256/HS384/HS512 signing + verification, encode/decode, claims validation (exp, nbf, iss, aud)

### Rate Limiter
- **Replaces**: ratelimit, aiolimiter
- **Why**: LLM APIs all have rate limits. Token bucket / sliding window needed for managing API calls.
- **stdlib basis**: time, threading, asyncio
- **Scope**: Token bucket and/or sliding window, sync + async, decorator interface

## Tier 2 — Valuable, Moderate Complexity

### WebSocket Client
- **Replaces**: websockets, websocket-client
- **Why**: OpenAI Realtime API, agent real-time communication
- **stdlib basis**: asyncio, hashlib, struct, ssl
- **Scope**: RFC 6455 client, text/binary frames, ping/pong, close handshake, sync + async

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

### Cron Expression Parser
- **Replaces**: croniter
- **stdlib basis**: datetime, re
- **Scope**: Standard 5-field cron parsing, next/prev occurrence calculation

### MessagePack
- **Replaces**: msgpack
- **stdlib basis**: struct
- **Scope**: Pack/unpack, compatible with msgpack spec

### PNG Encoder
- **Replaces**: Pillow (for simple generation)
- **stdlib basis**: zlib, struct
- **Scope**: Generate simple PNG images
- **Synergy**: QR module could output PNG directly

## Recommended Priority Order (remaining work)
1. Rate limiter (essential for API management)
2. JWT (auth layer)
3. WebSocket client (real-time APIs)
