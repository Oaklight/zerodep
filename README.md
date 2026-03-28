# zerodep

Zero-dependency, single-file Python implementations of popular libraries — stdlib only, Python 3.10+.

零依赖、单文件的 Python 常用库实现 —— 仅使用标准库，支持 Python 3.10+。

## Modules

**Web & Networking**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `httpclient/` | Sync + async REST client with connection pooling, proxy, and auth | `httpx` |
| `sse/` | Server-Sent Events client with auto-reconnect | `httpx-sse` |

**Data Formats**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `yaml/` | YAML parser and serializer (common subset) | `PyYAML` |
| `jsonc/` | JSONC parser (JSON with comments and trailing commas) | `commentjson` |
| `toon/` | TOON (Token-Oriented Object Notation) encoder/decoder | `toon_format` |
| `frontmatter/` | Frontmatter parser and serializer (YAML/TOML/JSON file-header metadata) | `python-frontmatter` |

**Data Validation**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `validate/` | Runtime TypedDict/dataclass validator with JSON Schema generation | `pydantic` |

**Text & Markup**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `markdown/` | Markdown to HTML renderer (CommonMark subset + GFM tables) | `mistune` |
| `soup/` | HTML parser with BeautifulSoup-like API (find, select, CSS selectors) | `beautifulsoup4` |
| `diff/` | Unified diff parser, patch apply/reverse, three-way merge | `unidiff` |

**Search & Retrieval**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `search/` | BM25/BM25+/BM25L/BM25F + TF-IDF full-text search engine | `rank-bm25` |

**Configuration**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `dotenv/` | .env file parser (load_dotenv, dotenv_values) | `python-dotenv` |

**CLI & Terminal**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `ansi/` | ANSI terminal styling: colors, attributes, detection, strip/visible_len | — |
| `tabulate/` | Table formatting with multiple output styles | `tabulate` |
| `prompt/` | Interactive CLI prompts (confirm, select, text) | `questionary` |

**Security & Encoding**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `aes/` | AES encryption: ECB, CBC, CTR, GCM modes (pure Python + OpenSSL via ctypes) | `pycryptodome` |
| `qr/` | QR Code generation with terminal rendering | `qrcode` |

**Infrastructure & Tools**

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `retry/` | Retry decorator with configurable backoff strategies | `tenacity` |
| `scheduler/` | In-process task scheduler with cron, interval, one-shot triggers | `APScheduler` |
| `structlog/` | Structured logging with pretty console output | `structlog` |
| `vcs/` | Git/Hg/Jujutsu CLI wrapper (diff, status, log, blame) | — |

## Usage

Each module is a **self-contained single file** that you can copy directly into your project. No installation required.

Some modules have optional **sibling dependencies** on other zerodep modules (e.g. `structlog` can use `ansi` for color support). These are loaded via guarded imports — if the sibling module is absent, the module falls back to inline constants and remains fully functional.

## License

MIT
