# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- **Frontmatter module**: parse and serialize YAML/TOML/JSON file-header metadata.
- **Scheduler module**: zero-dependency in-process task scheduler with cron expression support.
- **Sparse Search module**: BM25 family (BM25, BM25+, BM25L) and TF-IDF full-text search engine.
- `zerodep` CLI tool for module discovery and dependency-aware copying.

### Changed

- Migrated module metadata from `__version__`/`__deps__` to PEP 723 inline script metadata (frontmatter).
- Reverse index optimization for sparse search performance improvement.

## [0.1.0] - 2026-03-27

### Added

- **AES module**: AES encryption/decryption with ECB, CBC, CTR, and GCM modes; supports 128/192/256-bit keys.
- **QR Code module**: QR code generation with zero external dependencies.
- **HTTP Client module**: synchronous and asynchronous HTTP client with streaming response and file upload support.
- **Dotenv module**: `.env` file parser and loader.
- **YAML module**: YAML parser and emitter.
- **JSONC module**: JSON with Comments (JSONC) parser.
- **Retry module**: configurable retry decorator with backoff strategies.
- **Structured Logging module**: structured logging with JSON output and terminal color support.
- **TOON module**: Token-Oriented Object Notation serializer/deserializer.
- **Tabulate module**: plain-text table formatting.
- **Soup module**: lightweight HTML parsing.
- **Prompt module**: interactive terminal prompt utilities.
- **Validate module**: TypedDict/dataclass runtime validator with JSON Schema generation.
- **SSE module**: Server-Sent Events (SSE) client.
- **Markdown module**: Markdown to HTML renderer.
- **Diff module**: unified and context diff generation.
- **VCS module**: version control system utilities.
- **ANSI module**: ANSI terminal styling with automatic color detection.
- `__version__` attribute added to all modules for cross-module compatibility checks.
- `ty` type checker configuration in `pyproject.toml`.
- CI workflow for compatibility testing across Python 3.10–3.13.

### Fixed

- Async client body reading race condition in HTTP client.
- Type errors across multiple modules detected by `ty` type checker.

### Changed

- Aligned terminal color detection logic across prompt, structlog, and ansi modules.
- Replaced `httpbin.org` with local test server for reliable HTTP correctness tests.

### Removed

- `typing_extensions` dependency from validate module.
