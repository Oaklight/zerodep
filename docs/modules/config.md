# Config

Unified configuration loader -- zero dependencies, stdlib only, Python 3.10+.

> **Replaces:** `python-decouple`, `dynaconf`, `environs`, `pydantic-settings`

## Overview

The Config module provides a drop-in replacement for `python-decouple` and `dynaconf` (subset) core functionality. It loads settings from multiple sources -- environment variables, `.env` files, and config files (JSON, JSONC, YAML, TOML, INI) -- with type coercion, prefix support, and nested key access, following the [12-factor app](https://12factor.net/config) pattern.

| File | Description | Dependencies |
|------|-------------|--------------|
| `config.py` | Pure Python implementation | `dotenv`, `yaml`, `jsonc` (all optional sibling modules) |

The module supports all common configuration patterns: environment variable lookups with prefix namespacing, `.env` file auto-discovery, nested key access via separators, and built-in type coercion for `bool`, `int`, `float`, `list`, `tuple`, plus `Csv` and `Choices` helpers.

## How to Use in Your Project

Copy the single `.py` file into your project:

```bash
cp config/config.py your_project/
```

For full functionality, also copy the optional sibling modules:

```bash
cp dotenv/dotenv.py your_project/   # .env file support
cp yaml/yaml.py your_project/       # YAML config file support
cp jsonc/jsonc.py your_project/     # JSONC config file support
```

Then import directly:

```python
from config import config, setup, Config, Csv, Choices
```

## Source Priority

Configuration values are resolved in this order (highest priority first):

| Priority | Source | Description |
|----------|--------|-------------|
| 1 (highest) | Environment variables | `os.environ`, with optional prefix |
| 2 | `.env` file | Via sibling `dotenv` module, auto-discovered or explicit path |
| 3 | Config file | JSON, JSONC, YAML, TOML, or INI file |
| 4 (lowest) | Default value | Passed to `get()` / `__call__()` |

## API Reference

### `Config(dotenv_path, config_path, prefix, separator)`

Main configuration class. Loads from multiple sources and resolves values by priority.

```python
class Config:
    def __init__(
        self,
        *,
        dotenv_path: str | os.PathLike | None | _Auto = _AUTO,
        config_path: str | os.PathLike | None = None,
        prefix: str = "",
        separator: str = "__",
    ) -> None
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `dotenv_path` | `str \| os.PathLike \| None` | `_AUTO` | Path to `.env` file. `_AUTO` = auto-discover, `None` = disable. |
| `config_path` | `str \| os.PathLike \| None` | `None` | Path to config file (format detected from extension). |
| `prefix` | `str` | `""` | Prefix for env var lookups (e.g. `"MYAPP_"`). |
| `separator` | `str` | `"__"` | Separator for nested key access. |

**Example:**

```python
from config import Config

cfg = Config(config_path="settings.yaml", prefix="MYAPP_")
debug = cfg("DEBUG", default=False, cast=bool)
db_host = cfg("DATABASE__HOST", default="localhost")
```

---

### `Config.__call__(key, default, cast)` / `Config.get(key, default, cast)`

Retrieve a configuration value.

```python
def get(
    self,
    key: str,
    *,
    default: Any = MISSING,
    cast: type | Callable | None = None,
) -> Any
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `key` | `str` | -- | Configuration key to look up. |
| `default` | `Any` | `MISSING` | Fallback if key is not found. Omit to require the key. |
| `cast` | `type \| Callable \| None` | `None` | Type or callable to coerce the value. |

**Returns:** The resolved (and optionally cast) configuration value.

**Raises:** `UndefinedValueError` if key is missing and no default is given.

**Example:**

```python
cfg = Config(dotenv_path=None)

port = cfg("PORT", default=8000, cast=int)
debug = cfg("DEBUG", default=False, cast=bool)
hosts = cfg("ALLOWED_HOSTS", cast=Csv())
```

---

### `Config.has(key)`

Check whether a key exists in any source.

```python
def has(self, key: str) -> bool
```

---

### `Config.as_dict()`

Return a merged, flattened dict of all config sources.

```python
def as_dict(self) -> dict[str, Any]
```

---

### `setup(dotenv_path, config_path, prefix, separator)`

Initialize the module-level `Config` instance.

```python
def setup(
    *,
    dotenv_path=_AUTO,
    config_path=None,
    prefix="",
    separator="__",
) -> Config
```

**Returns:** The newly created `Config` instance.

---

### `config(key, default, cast)`

Module-level convenience function. Auto-creates a default `Config` if `setup()` was not called.

```python
def config(
    key: str,
    *,
    default: Any = MISSING,
    cast: type | Callable | None = None,
) -> Any
```

**Example:**

```python
from config import config, setup

setup(prefix="MYAPP_")
port = config("PORT", default=8000, cast=int)
debug = config("DEBUG", default=False, cast=bool)
```

---

### `Csv(cast, delimiter, strip, post_process)`

Parse comma-separated values with optional per-item casting.

```python
class Csv:
    def __init__(
        self,
        cast: Callable = str,
        delimiter: str = ",",
        strip: str = " %s",
        post_process: Callable = list,
    ) -> None
```

**Example:**

```python
Csv()("a, b, c")           # ["a", "b", "c"]
Csv(cast=int)("1,2,3")     # [1, 2, 3]
Csv(delimiter=";")("a;b")  # ["a", "b"]
Csv(post_process=tuple)("a,b")  # ("a", "b")
```

---

### `Choices(choices, cast)`

Validate that a value belongs to a fixed set.

```python
class Choices:
    def __init__(
        self,
        choices: Sequence[Any],
        cast: Callable = str,
    ) -> None
```

**Example:**

```python
Choices(["dev", "staging", "prod"])("dev")  # "dev"
Choices([1, 2, 3], cast=int)("2")           # 2
Choices(["a", "b"])("c")                    # raises ValueError
```

## Usage Examples

### Basic Environment Variables

```python
from config import config, setup

setup(prefix="MYAPP_", dotenv_path=None)

# Reads MYAPP_PORT from os.environ
port = config("PORT", default=8000, cast=int)
debug = config("DEBUG", default=False, cast=bool)
```

### Load From .env File

```python
from config import Config

# Auto-discover .env file
cfg = Config()
db_host = cfg("DB_HOST")
db_port = cfg("DB_PORT", cast=int)

# Or specify explicit path
cfg = Config(dotenv_path="/path/to/.env")
```

### Load From Config Files

```python
from config import Config

# JSON config
cfg = Config(dotenv_path=None, config_path="config.json")

# YAML config (requires sibling yaml module)
cfg = Config(dotenv_path=None, config_path="settings.yaml")

# TOML config (requires Python 3.11+)
cfg = Config(dotenv_path=None, config_path="config.toml")

# INI config
cfg = Config(dotenv_path=None, config_path="settings.ini")
```

### Nested Key Access

Given `config.yaml`:

```yaml
database:
  host: localhost
  port: 5432
  name: myapp
```

```python
from config import Config

cfg = Config(dotenv_path=None, config_path="config.yaml")
host = cfg("database__host")           # "localhost"
port = cfg("database__port", cast=int)  # 5432
```

Environment variables override nested config:

```bash
export database__host=production-db.example.com
```

```python
host = cfg("database__host")  # "production-db.example.com"
```

### Priority Override

```python
import os
from config import Config

# config.json: {"APP_MODE": "config"}
# .env:         APP_MODE=dotenv
# os.environ:   APP_MODE=environ

cfg = Config(dotenv_path=".env", config_path="config.json")
cfg("APP_MODE")  # "environ" (env var wins)

del os.environ["APP_MODE"]
cfg("APP_MODE")  # "dotenv" (.env wins over config file)
```

## Supported Config File Formats

| Extension | Parser | Requirement |
|-----------|--------|-------------|
| `.json` | stdlib `json` | -- |
| `.jsonc` | sibling `jsonc` module, falls back to `json` | jsonc (optional) |
| `.yaml`, `.yml` | sibling `yaml` module | yaml (required) |
| `.toml` | stdlib `tomllib` | Python 3.11+ |
| `.ini`, `.cfg` | stdlib `configparser` | -- |

## Built-in Type Coercion

| `cast` | Behavior |
|--------|----------|
| `int` | `int(value)` |
| `float` | `float(value)` |
| `bool` | Truthy: `"1"`, `"true"`, `"yes"`, `"on"`, `"t"`, `"y"` / Falsy: `"0"`, `"false"`, `"no"`, `"off"`, `"f"`, `"n"`, `""` |
| `list` | Try JSON array first, then comma-split |
| `tuple` | Same as `list` but returns `tuple` |
| `Csv(...)` | Configurable CSV parsing |
| `Choices(...)` | Value whitelist validation |
| Any callable | Called as `cast(value)` |

## Notes and Caveats

!!! info "API Compatibility with python-decouple"
    The `config()` function and `Csv`/`Choices` helpers match `python-decouple`'s API, so you can swap one for the other with minimal code changes. The `Config` class adds extra features (config files, nested keys) not available in `python-decouple`.

!!! info "Sibling Module Dependencies"
    The `dotenv`, `yaml`, and `jsonc` sibling modules are **optional**. Without them, the corresponding features are gracefully disabled: `.env` auto-discovery is skipped, YAML config files raise `ImportError`, and JSONC falls back to plain JSON parsing.

!!! info "INI Section Flattening"
    For `.ini`/`.cfg` files, sections are flattened into separator-joined keys. For example, `[database]` section with `host = localhost` becomes `database__host`.

- **Python version:** Requires Python 3.10+ (uses `X | Y` union type syntax).
- **TOML support:** Requires Python 3.11+ (uses stdlib `tomllib`).
- **Case sensitivity:** Environment variable lookups are case-sensitive. Config file nested lookups are case-insensitive.

## Benchmark

Benchmarked against `python-decouple` across env var lookups, type coercion, and CSV parsing.

See [Config Benchmark](../benchmarks/config.md) for detailed results.
