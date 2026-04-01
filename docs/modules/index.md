---
title: Module Overview
---

# Module Overview

Each zerodep module is a **self-contained single `.py` file** that you can copy directly into your project. No `pip install` required at runtime.

## All Modules

### Web & Networking

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [httpclient](http.md) | Sync + async REST client with connection pooling, proxy, and auth | `httpx` |
| [sse](sse.md) | Server-Sent Events client with auto-reconnect | `httpx-sse` |

### Agent Protocols

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [jsonrpc](jsonrpc.md) | JSON-RPC 2.0 protocol: data types, dispatcher, async transport | `jsonrpcserver` |
| [a2a](a2a.md) | Google A2A protocol: JSON-RPC 2.0, SSE streaming, task management | `a2a-python` |
| [acp](acp.md) | Anthropic ACP protocol: JSON-RPC 2.0 over stdio, async client/agent | `acp-python` |
| [skills](skills.md) | Agent Skills runtime: parse, discover, manage, select skills | -- |

### Data Formats

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [xml](xml.md) | XML ↔ dict converter with fault-tolerant parsing and LLM tag extraction | `xmltodict` |
| [yaml](yaml.md) | YAML parser and serializer (common subset) | `PyYAML` |
| [jsonc](jsonc.md) | JSONC parser (JSON with comments and trailing commas) | `commentjson` |
| [toon](toon.md) | TOON (Token-Oriented Object Notation) encoder/decoder | `toon_format` |
| [frontmatter](frontmatter.md) | Frontmatter parser and serializer (YAML/TOML/JSON) | `python-frontmatter` |

### Data Validation

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [validate](validate.md) | Runtime TypedDict/dataclass validator with JSON Schema generation | `pydantic` |

### Text & Markup

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [markdown](markdown.md) | Markdown to HTML renderer (CommonMark subset + GFM tables) | `mistune` |
| [soup](soup.md) | HTML parser with BeautifulSoup-like API (find, select, CSS selectors) | `beautifulsoup4` |
| [diff](diff.md) | Unified diff parser, patch apply/reverse, three-way merge | `unidiff` |

### Search & Retrieval

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [search](search.md) | BM25/BM25+/BM25L/BM25F + TF-IDF full-text search with Bayesian calibration | `rank-bm25` |

### Configuration

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [dotenv](dotenv.md) | .env file parser (load_dotenv, dotenv_values) | `python-dotenv` |
| [config](config.md) | Unified config loader (env vars, .env, JSON/YAML/TOML/INI) | `python-decouple` |

### CLI & Terminal

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [ansi](ansi.md) | ANSI terminal styling: colors, attributes, detection, strip/visible_len | -- |
| [tabulate](tabulate.md) | Table formatting with multiple output styles | `tabulate` |
| [prompt](prompt.md) | Interactive CLI prompts (confirm, select, text) | `questionary` |

### Security

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [aes](aes.md) | AES encryption: ECB, CBC, CTR, GCM modes (pure Python + OpenSSL via ctypes) | `pycryptodome` |

### Infrastructure & Tools

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [cache](cache.md) | In-memory cache with TTL, LRU/LFU eviction, and async support | -- |
| [retry](retry.md) | Decorator-based retry with configurable backoff strategies | `tenacity` |
| [scheduler](scheduler.md) | In-process task scheduler with cron, interval, one-shot triggers | `APScheduler` |
| [structlog](structlog.md) | Structured logging with pretty console output | `structlog` |
| [vcs](vcs.md) | Git/Hg/Jujutsu CLI wrapper (diff, status, log, blame) | -- |
| [runner](runner.md) | Structured subprocess execution with timeout escalation | -- |
| [filelock](filelock.md) | Cross-platform advisory file lock (fcntl/msvcrt) | -- |
| [qr](qr.md) | QR Code generation with terminal rendering | `qrcode` |

## Inter-Module Dependencies

Most zerodep modules are fully standalone. The following modules depend on other zerodep modules:

```mermaid
graph LR
    a2a --> jsonrpc
    acp --> jsonrpc
    config --> dotenv
    config --> yaml
    config --> jsonc
    frontmatter --> yaml
    skills --> frontmatter
    skills --> search
    sse --> httpclient
    vcs --> diff
```

When using the [CLI tool](../guide/cli.md), dependencies are resolved automatically. For manual installation, ensure all required modules are present.
