---
title: Home
hide:
  - navigation
---

# zerodep

Zero-dependency, single-file Python implementations of popular libraries — stdlib only, Python 3.10+.

## Overview

Each module is a **self-contained single file** that you can copy directly into your project. No `pip install` required.

## Available Modules

### Web & Networking

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [HTTP Client](modules/http.md) | Sync + async REST client | `httpx` |
| [SSE Client](modules/sse.md) | Server-Sent Events client with auto-reconnect | `httpx-sse` |

### Data Formats

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [YAML](modules/yaml.md) | YAML parser and serializer (common subset) | `PyYAML` |
| [JSONC](modules/jsonc.md) | JSONC parser (JSON with comments and trailing commas) | `commentjson` |
| [TOON](modules/toon.md) | TOON (Token-Oriented Object Notation) encoder/decoder | `toon_format` |

### Data Validation

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [Validate](modules/validate.md) | Runtime TypedDict/dataclass validator with JSON Schema generation | `pydantic` |

### Text & Markup

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [Markdown](modules/markdown.md) | Markdown to HTML renderer (CommonMark subset + GFM tables) | `mistune` |
| [HTML Parser](modules/soup.md) | HTML parser with BeautifulSoup-like API (find, select, CSS selectors) | `beautifulsoup4` |
| [Diff](modules/diff.md) | Unified diff parser, patch apply/reverse, three-way merge | `unidiff` |

### Search & Retrieval

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [Sparse Search](modules/search.md) | BM25/BM25+/BM25L/BM25F + TF-IDF full-text search engine | `rank-bm25` |

### Configuration

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [Dotenv](modules/dotenv.md) | .env file parser (load_dotenv, dotenv_values) | `python-dotenv` |

### CLI & Terminal

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [ANSI Colors](modules/ansi.md) | ANSI terminal styling: colors, attributes, detection, strip/visible_len | — |
| [Tabulate](modules/tabulate.md) | Table formatting with multiple output styles | `tabulate` |
| [Prompts](modules/prompt.md) | Interactive CLI prompts (confirm, select, text) | `questionary` |

### Security & Encoding

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [AES](modules/aes.md) | AES encryption: ECB, CBC, CTR, GCM modes (pure Python + OpenSSL via ctypes) | `pycryptodome` |
| [QR Code](modules/qr.md) | QR Code generation with terminal rendering | `qrcode` |

### Infrastructure & Tools

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [Retry](modules/retry.md) | Decorator-based retry with configurable backoff strategies | `tenacity` |
| [Scheduler](modules/scheduler.md) | In-process task scheduler with cron, interval, one-shot triggers | `APScheduler` |
| [Structured Logging](modules/structlog.md) | Structured logging with pretty console output | `structlog` |
| [VCS](modules/vcs.md) | Git/Hg/Jujutsu CLI wrapper (diff, status, log, blame) | — |

## Philosophy

- **Zero external dependencies** — only Python standard library
- **Single file** — copy one `.py` file into your project
- **Python 3.10+** — leverages modern Python features
- **Correctness first** — apple-to-apple tests against reference libraries
- **Performance parity** — benchmarked against popular alternatives
