---
title: Module Overview
---

# Module Overview

Each zerodep module is a **self-contained single `.py` file** that you can copy directly into your project. No `pip install` required at runtime.

## All Modules

### Web & Networking

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [httpclient](http.md) | Sync + async REST client | `httpx` |
| [sse](sse.md) | Server-Sent Events client with auto-reconnect | `httpx-sse` |

### Data Formats

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
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
| [search](search.md) | BM25/BM25+/BM25L/BM25F + TF-IDF full-text search engine | `rank-bm25` |

### Configuration

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [dotenv](dotenv.md) | .env file parser (load_dotenv, dotenv_values) | `python-dotenv` |

### CLI & Terminal

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [ansi](ansi.md) | ANSI terminal styling: colors, attributes, detection, strip/visible_len | -- |
| [tabulate](tabulate.md) | Table formatting with multiple output styles | `tabulate` |
| [prompt](prompt.md) | Interactive CLI prompts (confirm, select, text) | `questionary` |

### Security & Encoding

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [aes](aes.md) | AES encryption: ECB, CBC, CTR, GCM modes (pure Python + OpenSSL via ctypes) | `pycryptodome` |
| [qr](qr.md) | QR Code generation with terminal rendering | `qrcode` |

### Infrastructure & Tools

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [retry](retry.md) | Decorator-based retry with configurable backoff strategies | `tenacity` |
| [scheduler](scheduler.md) | In-process task scheduler with cron, interval, one-shot triggers | `APScheduler` |
| [structlog](structlog.md) | Structured logging with pretty console output | `structlog` |
| [vcs](vcs.md) | Git/Hg/Jujutsu CLI wrapper (diff, status, log, blame) | -- |
