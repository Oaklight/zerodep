# zerodep

[![PyPI](https://img.shields.io/pypi/v/zerodep?color=green)](https://pypi.org/project/zerodep/)
[![GitHub Release](https://img.shields.io/github/v/release/Oaklight/zerodep?color=green)](https://github.com/Oaklight/zerodep/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/pypi/pyversions/zerodep?color=green)](https://pypi.org/project/zerodep/)
[![CI](https://img.shields.io/github/actions/workflow/status/Oaklight/zerodep/ci.yml?label=CI)](https://github.com/Oaklight/zerodep/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/readthedocs/zerodep)](https://zerodep.readthedocs.io)

Zero-dependency, single-file Python implementations of popular libraries — stdlib only, Python 3.10+.

零依赖、单文件的 Python 常用库实现 —— 仅使用标准库，支持 Python 3.10+。

[English Docs](https://zerodep.readthedocs.io/en/) | [中文文档](https://zerodep.readthedocs.io/zh-cn/)

## Quick Start

```bash
pip install zerodep          # install the CLI
zerodep add yaml retry       # copy modules into your project
```

```python
from yaml import load, dump

data = load("name: Alice\nage: 30")
print(data)  # {'name': 'Alice', 'age': 30}
```

Each module is a **self-contained single `.py` file** — copy it into your project and import. No `pip install` needed at runtime.

## Modules

**Agent Protocols**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `jsonrpc/` | JSON-RPC 2.0 protocol: data types, dispatcher, async transport | `jsonrpcserver` |
| `a2a/` | Google A2A protocol: JSON-RPC 2.0, SSE streaming, task management | `a2a-python` |
| `acp/` | Anthropic ACP protocol: JSON-RPC 2.0 over stdio, async client/agent | `acp-python` |
| `skills/` | Agent Skills runtime: parse, discover, manage, select skills | — |

**Web & Networking**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `httpclient/` | Sync + async REST client with connection pooling, proxy, and auth | `httpx` |
| `sse/` | Server-Sent Events client with auto-reconnect | `httpx-sse` |

**Data Formats**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `xml/` | XML ↔ dict converter with fault-tolerant parsing and LLM tag extraction | `xmltodict` |
| `yaml/` | YAML parser and serializer (common subset) | `PyYAML` |
| `jsonc/` | JSONC parser (JSON with comments and trailing commas) | `commentjson` |
| `toon/` | TOON (Token-Oriented Object Notation) encoder/decoder | `toon_format` |
| `frontmatter/` | Frontmatter parser and serializer (YAML/TOML/JSON) | `python-frontmatter` |

**Data Validation**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `validate/` | Runtime TypedDict/dataclass validator with JSON Schema generation | `pydantic` |
| `semver/` | PEP 440 version parser and comparator | `packaging` |

**Text & Markup**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `markdown/` | Markdown → HTML renderer (CommonMark subset + GFM tables) | `mistune` |
| `soup/` | HTML parser with BeautifulSoup-like API (find, select, CSS selectors) | `beautifulsoup4` |
| `diff/` | Unified diff parser, patch apply/reverse, three-way merge | `unidiff` |

**Search & Retrieval**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `sparse_search/` | BM25/BM25+/BM25L/BM25F + TF-IDF full-text search with Bayesian calibration | `rank-bm25` |

**Configuration**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `dotenv/` | .env file parser (load_dotenv, dotenv_values) | `python-dotenv` |
| `config/` | Unified config loader (env vars, .env, JSON/YAML/TOML/INI) | `python-decouple` |

**CLI & Terminal**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `ansi/` | ANSI terminal styling: colors, attributes, detection, strip/visible_len | — |
| `tabulate/` | Table formatting with multiple output styles | `tabulate` |
| `prompt/` | Interactive CLI prompts (confirm, select, text) | `questionary` |

**Security**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `aes/` | AES encryption: ECB, CBC, CTR, GCM modes (pure Python + OpenSSL via ctypes) | `pycryptodome` |

**Infrastructure & Tools**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `cache/` | In-memory cache with TTL, LRU/LFU eviction, sync + async decorators | — |
| `retry/` | Retry decorator with configurable backoff strategies | `tenacity` |
| `scheduler/` | In-process task scheduler with cron, interval, one-shot triggers | `APScheduler` |
| `structlog/` | Structured logging with pretty console output | `structlog` |
| `runner/` | Structured subprocess execution with timeout escalation | — |
| `vcs/` | Git/Hg/Jujutsu CLI wrapper (diff, status, log, blame) | — |
| `filelock/` | Cross-platform advisory file lock (fcntl/msvcrt) | — |
| `qr/` | QR Code generation with terminal rendering | `qrcode` |
| `persistdict/` | Persistent dict with JSON file and SQLite backends | — |
| `depdetect/` | Dependency detection and verification utility | — |

## Versioning

- **Project**: [CalVer](https://calver.org/) `YYYY.M.D` (e.g., `2026.4.15`)
- **Modules**: independent [SemVer](https://semver.org/) per module (e.g., `0.4.1`)

Releases are automated via the [Release workflow](https://github.com/Oaklight/zerodep/actions/workflows/release.yml) — lint, test, bump module versions, tag, and create a GitHub Release in one step.

## Documentation

- **English**: [zerodep.readthedocs.io/en/](https://zerodep.readthedocs.io/en/)
- **中文**: [zerodep.readthedocs.io/zh-cn/](https://zerodep.readthedocs.io/zh-cn/)

## License

[MIT](LICENSE)
