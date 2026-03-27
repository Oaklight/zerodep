# zerodep — Candidate Module Roadmap

## httpclient Pending Features
- Connection pooling (high complexity) — pool keyed by (host, port, scheme), keep-alive, stale connection detection

## Tier 1 — High Value for Agentic/LLM Development

### SSE Client (Server-Sent Events)
- **Replaces**: httpx-sse, aiohttp SSE
- **Why**: Nearly all LLM APIs (OpenAI, Anthropic, Google) use SSE for streaming responses. Natural extension of httpclient.
- **stdlib basis**: Extends existing httpclient (http.client, asyncio streams)
- **Scope**: Parse `text/event-stream` format (event, data, id, retry fields), sync + async, iterator/async iterator interface
- **Synergy**: Depends on streaming response support in httpclient (done)
- **Priority**: Highest — completes the LLM API client stack

### JWT (JSON Web Tokens)
- **Replaces**: PyJWT, python-jose
- **Why**: API gateway auth, OAuth, agent-to-agent authentication. Web/API dev essential.
- **stdlib basis**: hmac, hashlib, base64, json
- **Scope**: HS256/HS384/HS512 signing + verification, encode/decode, claims validation (exp, nbf, iss, aud)
- **Priority**: High

### Rate Limiter
- **Replaces**: ratelimit, aiolimiter
- **Why**: LLM APIs all have rate limits. Token bucket / sliding window needed for managing API calls.
- **stdlib basis**: time, threading, asyncio
- **Scope**: Token bucket and/or sliding window, sync + async, decorator interface
- **Priority**: High

### Validate (TypedDict/Dataclass Runtime Validator)
- **Replaces**: pydantic (validation subset), beartype, typeguard
- **Why**: LLM tool schemas, API data validation, llm-rosetta IR validation. Define types once with stdlib TypedDict/dataclass, get validation + JSON Schema generation.
- **stdlib basis**: typing, typing_extensions (get_type_hints, Annotated), inspect, dataclasses
- **Scope**:
  - `validate(data, TypedDict)` — recursive structural validation against TypedDict/dataclass definitions
  - Constraint annotations via `Annotated`: Gt, Ge, Lt, Le, MinLen, MaxLen, Match, Predicate
  - `Required`/`NotRequired`, `Literal`, `Union` discriminated validation
  - Structured `ValidationError` with field path, expected type, actual value
  - `json_schema(TypedDict)` — generate JSON Schema (LLM API common subset) from type definitions
  - Optional type coercion (`coerce=True`)
- **Design principle**: Enhance stdlib types, not replace them — no BaseModel, no new declaration system
- **Synergy**: Direct consumer: llm-rosetta IR validation + tool schema generation
- **Priority**: High

## Tier 2 — Valuable, Moderate Complexity

### WebSocket Client
- **Replaces**: websockets, websocket-client
- **Why**: OpenAI Realtime API, agent real-time communication
- **stdlib basis**: asyncio, hashlib, struct, ssl
- **Scope**: RFC 6455 client, text/binary frames, ping/pong, close handshake, sync + async

### Markdown → HTML
- **Replaces**: markdown, mistune
- **Why**: LLM output rendering to web UI
- **stdlib basis**: re, html
- **Scope**: CommonMark subset (headings, lists, code blocks, links, emphasis, tables)

## Tier 3 — Niche but Useful

### TOTP/HOTP
- **Replaces**: pyotp
- **stdlib basis**: hmac, hashlib, struct, time
- **Scope**: RFC 4226 (HOTP) + RFC 6238 (TOTP), URI generation for QR codes

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
- **Scope**: Generate simple PNG images, natural complement to QR module
- **Synergy**: QR module could output PNG directly

## Recommended Priority Order (for agentic/LLM focus)
1. SSE client (completes LLM streaming stack)
2. Rate limiter (essential for API management)
3. Validate (TypedDict runtime validation + JSON Schema generation)
4. JWT (auth layer)
5. WebSocket client (real-time APIs)
