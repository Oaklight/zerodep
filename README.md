# zerodep

Zero-dependency, single-file Python implementations of popular libraries — stdlib only, Python 3.10+.

零依赖、单文件的 Python 常用库实现 —— 仅使用标准库，支持 Python 3.10+。

## Modules

| Module | Description | Benchmark Against |
|--------|-------------|-------------------|
| `aes/` | AES encryption: ECB, CBC, CTR, GCM modes (pure Python + OpenSSL via ctypes) | `pycryptodome` |
| `qr/` | QR Code generation with terminal rendering | `qrcode` |
| `httpclient/` | Sync + async REST client | `httpx` |
| `dotenv/` | .env file parser (load_dotenv, dotenv_values) | `python-dotenv` |
| `yaml/` | YAML parser and serializer (common subset) | `PyYAML` |
| `jsonc/` | JSONC parser (JSON with comments and trailing commas) | `commentjson` |
| `structlog/` | Structured logging with pretty console output | `structlog` |
| `toon/` | TOON (Token-Oriented Object Notation) encoder/decoder | `toon_format` |
| `tabulate/` | Table formatting with multiple output styles | `tabulate` |
| `retry/` | Retry decorator with configurable backoff strategies | `tenacity` |
| `validate/` | Runtime TypedDict/dataclass validator with JSON Schema generation | `pydantic` |
| `sse/` | Server-Sent Events client with auto-reconnect | `httpx-sse` |
| `soup/` | HTML parser with BeautifulSoup-like API (find, select, CSS selectors) | `beautifulsoup4` |
| `prompt/` | Interactive CLI prompts (confirm, select, text) | `questionary` |
| `markdown/` | Markdown to HTML renderer (CommonMark subset + GFM tables) | `mistune` |
| `ansi/` | ANSI terminal styling: colors, attributes, detection, strip/visible_len | — |
| `diff/` | Unified diff parser, patch apply/reverse, three-way merge | `unidiff` |
| `vcs/` | Git/Hg/Jujutsu CLI wrapper (diff, status, log, blame) | — |
| `scheduler/` | In-process task scheduler with cron, interval, one-shot triggers | `APScheduler` |
| `search/` | BM25/BM25+/BM25L/BM25F + TF-IDF full-text search engine | `rank-bm25` |

## Usage

Each module is a **self-contained single file** that you can copy directly into your project. No installation required.

Some modules have optional **sibling dependencies** on other zerodep modules (e.g. `structlog` can use `ansi` for color support). These are loaded via guarded imports — if the sibling module is absent, the module falls back to inline constants and remains fully functional.

## License

MIT
