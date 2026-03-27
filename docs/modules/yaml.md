# YAML

YAML parser and serializer (common subset) -- zero dependencies, stdlib only, Python 3.10+.

## Overview

The YAML module provides a safe YAML parser and serializer covering the most commonly used subset of the YAML specification. It is designed as a drop-in replacement for `PyYAML`'s `safe_load` / `safe_dump` for typical configuration files and data exchange, without requiring any external dependency.

| File | Description | Dependencies |
|------|-------------|--------------|
| `yaml.py` | Pure Python YAML parser and serializer | None (stdlib only) |

Only **safe types** are produced during parsing: `dict`, `list`, `str`, `int`, `float`, `bool`, and `None`.

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp yaml/yaml.py your_project/
```

Then import directly:

```python
from yaml import load, dump
```

## API Reference

### `load(text)`

Parse a YAML string and return a Python object. Equivalent to PyYAML's `yaml.safe_load()`.

```python
def load(text: str) -> Any
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `text` | `str` | YAML document string. |

**Returns:** `Any` -- Parsed Python object (`dict`, `list`, `str`, `int`, `float`, `bool`, or `None`).

**Raises:** `YAMLError` if the YAML is malformed.

**Example:**

```python
data = load("name: Alice\nage: 30")
# {'name': 'Alice', 'age': 30}
```

---

### `load_all(text)`

Parse a multi-document YAML string. Yields one Python object per YAML document (separated by `---`).

```python
def load_all(text: str) -> Iterator[Any]
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `text` | `str` | Multi-document YAML string. |

**Yields:** Parsed Python objects, one per document.

**Example:**

```python
for doc in load_all("---\na: 1\n---\nb: 2"):
    print(doc)
# {'a': 1}
# {'b': 2}
```

---

### `dump(data, stream, *, default_flow_style, indent, sort_keys, allow_unicode)`

Serialize a Python object to a YAML string.

```python
def dump(
    data: Any,
    stream: IO[str] | None = None,
    *,
    default_flow_style: bool | None = None,
    indent: int = 2,
    sort_keys: bool = True,
    allow_unicode: bool = True,
) -> str | None
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `Any` | *(required)* | Python object to serialize. |
| `stream` | `IO[str] \| None` | `None` | If provided, write to this stream and return `None`. |
| `default_flow_style` | `bool \| None` | `None` | `True` for flow (inline) style, `False` for block, `None` for auto. |
| `indent` | `int` | `2` | Number of spaces per indentation level. |
| `sort_keys` | `bool` | `True` | Sort mapping keys alphabetically. |
| `allow_unicode` | `bool` | `True` | Allow unicode characters in output. |

**Returns:** `str` if `stream` is `None`, otherwise `None`.

**Example:**

```python
text = dump({"name": "Alice", "age": 30})
print(text)
# age: 30
# name: Alice
```

---

### `dump_all(documents, stream, *, default_flow_style, indent, sort_keys, allow_unicode)`

Serialize multiple Python objects as a multi-document YAML string.

```python
def dump_all(
    documents: list[Any] | tuple[Any, ...],
    stream: IO[str] | None = None,
    *,
    default_flow_style: bool | None = None,
    indent: int = 2,
    sort_keys: bool = True,
    allow_unicode: bool = True,
) -> str | None
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `documents` | `list[Any] \| tuple[Any, ...]` | *(required)* | Iterable of Python objects to serialize. |
| `stream` | `IO[str] \| None` | `None` | If provided, write to this stream and return `None`. |
| `default_flow_style` | `bool \| None` | `None` | `True` for flow style, `False` for block, `None` for auto. |
| `indent` | `int` | `2` | Number of spaces per indentation level. |
| `sort_keys` | `bool` | `True` | Sort mapping keys alphabetically. |
| `allow_unicode` | `bool` | `True` | Allow unicode characters in output. |

**Returns:** `str` if `stream` is `None`, otherwise `None`.

**Example:**

```python
text = dump_all([{"a": 1}, {"b": 2}])
print(text)
# a: 1
# ---
# b: 2
```

---

### `class YAMLError(Exception)`

Raised when YAML parsing fails. Includes the line number where the error occurred.

```python
class YAMLError(Exception): ...
```

## Usage Examples

### Parse a Configuration File

```python
from yaml import load

config_text = """
server:
  host: 0.0.0.0
  port: 8080
  debug: false

database:
  url: postgres://localhost/mydb
  pool_size: 5

logging:
  level: INFO
  handlers:
    - console
    - file
"""

config = load(config_text)
print(config["server"]["port"])   # 8080
print(config["logging"]["level"]) # 'INFO'
```

### Dump Data to YAML

```python
from yaml import dump

data = {
    "users": [
        {"name": "Alice", "role": "admin"},
        {"name": "Bob", "role": "user"},
    ],
    "version": 2,
}

text = dump(data)
print(text)
```

### Multi-Document Stream

```python
from yaml import load_all, dump_all

# Parse
yaml_text = """---
name: service-a
port: 8001
---
name: service-b
port: 8002
"""
for doc in load_all(yaml_text):
    print(doc["name"], doc["port"])

# Dump
output = dump_all([
    {"name": "service-a", "port": 8001},
    {"name": "service-b", "port": 8002},
])
print(output)
```

### Flow Style Output

```python
from yaml import dump

data = {"colors": ["red", "green", "blue"], "count": 3}
print(dump(data, default_flow_style=True))
# {colors: [red, green, blue], count: 3}
```

### Writing to a File

```python
from yaml import dump

config = {"debug": True, "workers": 4}

with open("config.yaml", "w") as f:
    dump(config, f)
```

## Supported YAML Subset

### Supported Features

- **Scalars:** strings, integers (decimal, hex `0x`, octal `0`, binary `0b`), floats, booleans (`true`/`false`/`yes`/`no`/`on`/`off`), null (`null`/`~`), special floats (`.inf`, `.nan`)
- **Mappings:** block-style and flow-style (`{key: value}`)
- **Sequences:** block-style and flow-style (`[a, b, c]`)
- **Block scalars:** literal (`|`) and folded (`>`) with chomping indicators (`-`, `+`)
- **Quoted strings:** single-quoted and double-quoted with escape sequences
- **Comments:** line comments (`#`) and inline comments
- **Multi-document streams:** `---` and `...` markers
- **Nested structures:** arbitrarily nested mappings and sequences
- **Underscore separators:** `1_000_000` in numeric literals

### Not Supported

- **Anchors and aliases** (`&anchor`, `*alias`)
- **Tags** (`!!str`, `!custom`)
- **Merge keys** (`<<:`)
- **Complex mapping keys** (multi-line keys, sequence/mapping as keys)
- **Directives** (`%YAML`, `%TAG`)

## Notes and Caveats

!!! warning "YAML 1.1 Boolean Compatibility"
    This parser follows YAML 1.1 conventions and treats `yes`, `no`, `on`, `off` (case-insensitive) as boolean values. If you need these as literal strings, wrap them in quotes: `"yes"`, `'no'`. This matches PyYAML's default behavior but differs from YAML 1.2, which only recognizes `true` and `false`.

!!! info "Safe Types Only"
    This module only produces safe Python types during parsing: `dict`, `list`, `str`, `int`, `float`, `bool`, and `None`. No arbitrary Python objects are constructed, making it safe to use with untrusted input. This is equivalent to PyYAML's `safe_load()` -- there is no `unsafe_load()` equivalent.

- **Python version:** Requires Python 3.10+ (uses `X | Y` union type hint syntax).
- **Circular references:** The serializer detects circular references and raises `YAMLError` instead of entering infinite recursion.
- **Key sorting:** By default, `dump()` sorts mapping keys alphabetically. Pass `sort_keys=False` to preserve insertion order.
- **Module name collision:** If you name the file `yaml.py` in your project, it may shadow a system-installed `PyYAML` package. This is intentional for zero-dep usage but be aware of the potential conflict.

## Benchmark

Benchmarked against `PyYAML` across three input sizes (small, medium, large) for both load and dump operations.

See [YAML Benchmark](../benchmarks/yaml.md) for detailed results.
