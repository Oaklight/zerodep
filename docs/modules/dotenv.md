# Dotenv

.env file parser and loader -- zero dependencies, stdlib only, Python 3.10+.

> **Replaces:** `python-dotenv`

## Overview

The Dotenv module provides a drop-in replacement for `python-dotenv` core functionality. It can parse `.env` files, load variables into `os.environ`, and manipulate key-value pairs in `.env` files -- all without any third-party dependencies.

| File | Description | Dependencies |
|------|-------------|--------------|
| `dotenv.py` | Pure Python implementation | None (stdlib only) |

The module supports all common `.env` syntax: comments, single/double/unquoted values, `export` prefixes, multiline double-quoted values, and variable interpolation with `$VAR`, `${VAR}`, and `${VAR:-default}`.

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp dotenv/dotenv.py your_project/
```

Then import directly:

```python
from dotenv import load_dotenv, dotenv_values, find_dotenv
```

## API Reference

### `load_dotenv(dotenv_path, stream, verbose, interpolate, override, encoding)`

Read a `.env` file and set `os.environ`.

```python
def load_dotenv(
    dotenv_path: str | os.PathLike[str] | None = None,
    stream: IO[str] | None = None,
    verbose: bool = False,
    interpolate: bool = True,
    override: bool = False,
    encoding: str = "utf-8",
) -> bool
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `dotenv_path` | `str \| os.PathLike \| None` | `None` | Path to the `.env` file. If `None`, uses `find_dotenv()`. |
| `stream` | `IO[str] \| None` | `None` | A text stream to read from (overrides `dotenv_path`). |
| `verbose` | `bool` | `False` | Print a warning to stderr when the file is missing. |
| `interpolate` | `bool` | `True` | Expand `$VAR` and `${VAR}` references in values. |
| `override` | `bool` | `False` | If `True`, overwrite existing environment variables. |
| `encoding` | `str` | `"utf-8"` | File encoding. |

**Returns:** `bool` -- `True` if a file was found and loaded.

**Example:**

```python
from dotenv import load_dotenv

# Load .env from auto-detected path
load_dotenv()

# Load a specific file, overriding existing env vars
load_dotenv("/path/to/config.env", override=True)
```

---

### `dotenv_values(dotenv_path, stream, verbose, interpolate, override, encoding)`

Parse a `.env` file and return a dict **without** modifying `os.environ`.

```python
def dotenv_values(
    dotenv_path: str | os.PathLike[str] | None = None,
    stream: IO[str] | None = None,
    verbose: bool = False,
    interpolate: bool = True,
    override: bool = False,
    encoding: str = "utf-8",
) -> dict[str, str | None]
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `dotenv_path` | `str \| os.PathLike \| None` | `None` | Path to the `.env` file. If `None`, uses `find_dotenv()`. |
| `stream` | `IO[str] \| None` | `None` | A text stream to read from (overrides `dotenv_path`). |
| `verbose` | `bool` | `False` | Print a warning to stderr when the file is missing. |
| `interpolate` | `bool` | `True` | Expand `$VAR` and `${VAR}` references in values. |
| `override` | `bool` | `False` | Unused, kept for API compatibility with `python-dotenv`. |
| `encoding` | `str` | `"utf-8"` | File encoding. |

**Returns:** `dict[str, str | None]` -- Dictionary mapping variable names to their values.

**Example:**

```python
from dotenv import dotenv_values

config = dotenv_values(".env")
db_host = config.get("DB_HOST")
```

---

### `find_dotenv(filename, raise_error_if_not_found, usecwd)`

Walk up from the calling file's directory (or cwd) to find a `.env` file.

```python
def find_dotenv(
    filename: str = ".env",
    raise_error_if_not_found: bool = False,
    usecwd: bool = False,
) -> str
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `filename` | `str` | `".env"` | Name of the file to search for. |
| `raise_error_if_not_found` | `bool` | `False` | Raise `IOError` if the file is not found. |
| `usecwd` | `bool` | `False` | Start from the current working directory instead of the calling file's directory. |

**Returns:** `str` -- Absolute path to the found file, or an empty string if not found.

**Example:**

```python
from dotenv import find_dotenv

path = find_dotenv()                     # search up from caller's directory
path = find_dotenv(usecwd=True)          # search up from cwd
path = find_dotenv(".env.production")    # look for a custom filename
```

---

### `get_key(dotenv_path, key_to_get, encoding)`

Get a single value from a `.env` file.

```python
def get_key(
    dotenv_path: str | os.PathLike[str],
    key_to_get: str,
    encoding: str = "utf-8",
) -> str | None
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `dotenv_path` | `str \| os.PathLike` | -- | Path to the `.env` file. |
| `key_to_get` | `str` | -- | The key to retrieve. |
| `encoding` | `str` | `"utf-8"` | File encoding. |

**Returns:** `str | None` -- The value for the key, or `None` if not found.

**Example:**

```python
from dotenv import get_key

secret = get_key(".env", "SECRET_KEY")
```

---

### `set_key(dotenv_path, key_to_set, value_to_set, quote_mode, export, encoding)`

Set a key=value pair in a `.env` file, creating the file if needed.

```python
def set_key(
    dotenv_path: str | os.PathLike[str],
    key_to_set: str,
    value_to_set: str,
    quote_mode: str = "always",
    export: bool = False,
    encoding: str = "utf-8",
) -> tuple[bool, str, str]
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `dotenv_path` | `str \| os.PathLike` | -- | Path to the `.env` file. |
| `key_to_set` | `str` | -- | The key to set. |
| `value_to_set` | `str` | -- | The value to set. |
| `quote_mode` | `str` | `"always"` | Quoting strategy: `"always"`, `"auto"`, or `"never"`. |
| `export` | `bool` | `False` | Whether to prefix the line with `export`. |
| `encoding` | `str` | `"utf-8"` | File encoding. |

**Returns:** `tuple[bool, str, str]` -- Tuple of `(success, key, value)`.

**Example:**

```python
from dotenv import set_key

set_key(".env", "DB_HOST", "localhost")
set_key(".env", "API_KEY", "s3cret", quote_mode="auto")
set_key(".env", "PATH_VAR", "/usr/local/bin", export=True)
```

---

### `unset_key(dotenv_path, key_to_unset, quote_mode, encoding)`

Remove a key from a `.env` file.

```python
def unset_key(
    dotenv_path: str | os.PathLike[str],
    key_to_unset: str,
    quote_mode: str = "always",
    encoding: str = "utf-8",
) -> tuple[bool, str]
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `dotenv_path` | `str \| os.PathLike` | -- | Path to the `.env` file. |
| `key_to_unset` | `str` | -- | The key to remove. |
| `quote_mode` | `str` | `"always"` | Unused, kept for API compatibility. |
| `encoding` | `str` | `"utf-8"` | File encoding. |

**Returns:** `tuple[bool, str]` -- Tuple of `(success, key)`.

**Example:**

```python
from dotenv import unset_key

unset_key(".env", "OLD_VARIABLE")
```

## Usage Examples

### Basic Load

```python
from dotenv import load_dotenv
import os

# Automatically find and load .env
load_dotenv()

# Access variables from os.environ
database_url = os.environ.get("DATABASE_URL")
debug_mode = os.environ.get("DEBUG")
```

### Parse Without Modifying Environment

```python
from dotenv import dotenv_values

config = dotenv_values(".env")

# Use values directly from the dict
print(config["APP_NAME"])
print(config["SECRET_KEY"])
```

### Variable Interpolation

Given a `.env` file:

```dotenv
BASE_DIR=/opt/myapp
DATA_DIR=${BASE_DIR}/data
LOG_DIR=${BASE_DIR}/logs
DEFAULT_PORT=${PORT:-8080}
```

```python
from dotenv import dotenv_values

config = dotenv_values(".env")
print(config["DATA_DIR"])        # /opt/myapp/data
print(config["LOG_DIR"])         # /opt/myapp/logs
print(config["DEFAULT_PORT"])    # 8080 (fallback, since PORT is not set)
```

### Override Behavior

```python
import os
from dotenv import load_dotenv

os.environ["EXISTING"] = "original"

# Default: does NOT overwrite existing env vars
load_dotenv()
print(os.environ["EXISTING"])  # "original"

# With override=True: overwrites existing env vars
load_dotenv(override=True)
print(os.environ["EXISTING"])  # value from .env file
```

### Reading From a Stream

```python
import io
from dotenv import load_dotenv, dotenv_values

env_content = """
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
"""

# Parse from a string stream
config = dotenv_values(stream=io.StringIO(env_content))
print(config)  # {'DB_HOST': 'localhost', 'DB_PORT': '5432', 'DB_NAME': 'myapp'}
```

## Supported Features

The parser supports the following `.env` file syntax:

| Feature | Syntax | Example |
|---------|--------|---------|
| Simple values | `KEY=value` | `HOST=localhost` |
| Double-quoted | `KEY="value"` | `MSG="hello world"` |
| Single-quoted | `KEY='value'` | `MSG='no $interpolation'` |
| Unquoted | `KEY=value` | `PORT=8080` |
| Comments | `# comment` | `# This is a comment` |
| Inline comments | `KEY=value # comment` | `PORT=8080 # default port` |
| Export prefix | `export KEY=value` | `export PATH=/usr/bin` |
| Empty values | `KEY=` | `EMPTY=` |
| Key without value | `KEY` | `UNDEFINED` (parsed as `None`) |
| Multiline (double-quoted) | `KEY="line1\nline2"` | Actual newlines inside `"..."` |
| Escape sequences | `\n`, `\t`, `\\`, `\"`, `\$` | Inside double-quoted values |
| Variable interpolation | `$VAR`, `${VAR}` | `URL=http://$HOST:$PORT` |
| Default values | `${VAR:-default}` | `PORT=${PORT:-3000}` |
| UTF-8 BOM | Automatically stripped | -- |

**Interpolation resolution order:** file-local variables first, then `os.environ`, then empty string.

**Single-quoted values** are treated as literals -- no escape processing or interpolation is performed.

## Notes and Caveats

!!! info "API Compatibility with python-dotenv"
    This module is designed as a drop-in replacement for `python-dotenv`. The public function signatures (`load_dotenv`, `dotenv_values`, `find_dotenv`, `get_key`, `set_key`, `unset_key`) match `python-dotenv` so you can swap one for the other without changing your code.

!!! info "override Parameter in dotenv_values"
    The `override` parameter in `dotenv_values()` is accepted but unused -- it exists solely for signature compatibility with `python-dotenv`. Since `dotenv_values()` does not modify `os.environ`, the parameter has no effect.

!!! info "quote_mode Parameter in unset_key"
    The `quote_mode` parameter in `unset_key()` is accepted but unused -- it exists solely for signature compatibility with `python-dotenv`.

- **Python version:** Requires Python 3.10+ (uses `X | Y` union type syntax).
- **File creation:** `set_key()` creates the `.env` file (and parent directories) if it does not exist.
- **Encoding:** All functions default to UTF-8. UTF-8 BOM is automatically stripped during parsing.
- **No CLI:** Unlike `python-dotenv`, this module does not provide a command-line interface.

## Benchmark

Benchmarked against `python-dotenv` across three `.env` file sizes (10, 50, 500 entries).

See [Dotenv Benchmark](../benchmarks/dotenv.md) for detailed results.
