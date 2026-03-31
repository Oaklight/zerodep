---
title: Module Overview
---

# Module Overview

Each zerodep module is a **self-contained single `.py` file** that you can copy directly into your project. No `pip install` required at runtime.

## All Modules

### Network

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [httpclient](http.md) | Sync + async REST client | `httpx` |
| [sse](sse.md) | Server-Sent Events client with auto-reconnect | `httpx-sse` |

### Terminal

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [ansi](ansi.md) | ANSI terminal styling: colors, attributes, detection, strip/visible_len | -- |
| [markdown](markdown.md) | Markdown to HTML renderer (CommonMark subset + GFM tables) | `mistune` |
| [prompt](prompt.md) | Interactive CLI prompts (confirm, select, text) | `questionary` |
| [tabulate](tabulate.md) | Table formatting with multiple output styles | `tabulate` |

### Data

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [config](config.md) | Unified config loader (env vars, .env, JSON/YAML/TOML/INI) | `python-decouple` |
| [dotenv](dotenv.md) | .env file parser (load_dotenv, dotenv_values) | `python-dotenv` |
| [frontmatter](frontmatter.md) | Frontmatter parser and serializer (YAML/TOML/JSON) | `python-frontmatter` |
| [jsonc](jsonc.md) | JSONC parser (JSON with comments and trailing commas) | `commentjson` |
| [soup](soup.md) | HTML parser with BeautifulSoup-like API (find, select, CSS selectors) | `beautifulsoup4` |
| [toon](toon.md) | TOON (Token-Oriented Object Notation) encoder/decoder | `toon_format` |
| [validate](validate.md) | Runtime TypedDict/dataclass validator with JSON Schema generation | `pydantic` |
| [xml](xml.md) | XML to dict converter with fault-tolerant parsing | `xmltodict` |
| [yaml](yaml.md) | YAML parser and serializer (common subset) | `PyYAML` |

### Crypto

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [aes](aes.md) | AES encryption: ECB, CBC, CTR, GCM modes (pure Python + OpenSSL via ctypes) | `pycryptodome` |

### Process

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [runner](runner.md) | Structured subprocess execution with timeout escalation | -- |
| [scheduler](scheduler.md) | In-process task scheduler with cron, interval, one-shot triggers | `APScheduler` |

### Dev Tools

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [diff](diff.md) | Unified diff parser, patch apply/reverse, three-way merge | `unidiff` |
| [vcs](vcs.md) | Git/Hg/Jujutsu CLI wrapper (diff, status, log, blame) | -- |

### Utility

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [cache](cache.md) | In-memory cache with TTL, LRU/LFU eviction, and async support | -- |
| [qr](qr.md) | QR Code generation with terminal rendering | `qrcode` |
| [retry](retry.md) | Decorator-based retry with configurable backoff strategies | `tenacity` |
| [search](search.md) | BM25/BM25+/BM25L/BM25F + TF-IDF full-text search engine | `rank-bm25` |
| [structlog](structlog.md) | Structured logging with pretty console output | `structlog` |
