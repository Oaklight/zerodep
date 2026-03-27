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

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| [AES](modules/aes.md) | AES encryption: ECB, CBC, CTR, GCM modes (pure Python + OpenSSL via ctypes) | `pycryptodome` |
| [QR Code](modules/qr.md) | QR Code generation with terminal rendering | `qrcode` |
| [HTTP Client](modules/http.md) | Sync + async REST client | `httpx` |
| [Dotenv](modules/dotenv.md) | .env file parser (load_dotenv, dotenv_values) | `python-dotenv` |
| [YAML](modules/yaml.md) | YAML parser and serializer (common subset) | `PyYAML` |
| [JSONC](modules/jsonc.md) | JSONC parser (JSON with comments and trailing commas) | `commentjson` |
| [Structured Logging](modules/structlog.md) | Structured logging with pretty console output | `structlog` |
| [Retry](modules/retry.md) | Decorator-based retry with configurable backoff strategies | `tenacity` |
| [TOON](modules/toon.md) | TOON (Token-Oriented Object Notation) encoder/decoder | `toon_format` |
| [Tabulate](modules/tabulate.md) | Table formatting with multiple output styles | `tabulate` |
| [Validate](modules/validate.md) | Runtime TypedDict/dataclass validator with JSON Schema generation | `pydantic` |
| [SSE Client](modules/sse.md) | Server-Sent Events client with auto-reconnect | `httpx-sse` |
| [HTML Parser](modules/soup.md) | HTML parser with BeautifulSoup-like API (find, select, CSS selectors) | `beautifulsoup4` |
| [Prompts](modules/prompt.md) | Interactive CLI prompts (confirm, select, text) | `questionary` |
| [Markdown](modules/markdown.md) | Markdown to HTML renderer (CommonMark subset + GFM tables) | `mistune` |

## Philosophy

- **Zero external dependencies** — only Python standard library
- **Single file** — copy one `.py` file into your project
- **Python 3.10+** — leverages modern Python features
- **Correctness first** — apple-to-apple tests against reference libraries
- **Performance parity** — benchmarked against popular alternatives
