# JSONC Parser

A zero-dependency JSONC (JSON with Comments) parser that supports single-line comments (`//`, `#`), block comments (`/* */`), and trailing commas.

## Features

- **Single-line comments**: `//` and `#` styles
- **Block comments**: `/* ... */` (including multiline)
- **Trailing commas**: In objects and arrays
- **Drop-in replacement**: Same API as stdlib `json` module
- **String-safe**: Comments inside quoted strings are preserved
- **Error reporting**: `JSONCDecodeError` with position information

## Quick Start

```python
from jsonc import loads, load, dumps, dump

# Parse JSONC string
config = loads("""
{
    // Database settings
    "host": "localhost",
    "port": 5432,  // default PostgreSQL port
    "options": {
        "ssl": true,
        "timeout": 30,  # seconds
    },
}
""")

# Parse JSONC file
with open("config.jsonc") as f:
    config = load(f)

# Serialize (pass-through to json.dumps)
text = dumps(config, indent=2)
```

## API

### `loads(text, **kwargs)`

Deserialize a JSONC string to a Python object. Strips comments and trailing commas before delegating to `json.loads`.

All keyword arguments accepted by `json.loads` are supported (`cls`, `object_hook`, `parse_float`, `parse_int`, `parse_constant`, `object_pairs_hook`).

### `load(fp, **kwargs)`

Deserialize a JSONC file-like object. Reads the stream and passes to `loads`.

### `dumps(obj, **kwargs)` / `dump(obj, fp, **kwargs)`

Pass-through to `json.dumps` / `json.dump` for API compatibility.

### `JSONCDecodeError`

Subclass of `json.JSONDecodeError`, raised when JSONC parsing fails.

## Comment Styles

```jsonc
{
    // C-style single-line comment
    "a": 1,

    # Python-style single-line comment
    "b": 2,

    /* C-style block comment */
    "c": 3,

    /*
     * Multiline
     * block comment
     */
    "d": 4
}
```

## Trailing Commas

```jsonc
{
    "array": [1, 2, 3,],
    "nested": {
        "key": "value",
    },
}
```

## Comparison with commentjson

| Feature | zerodep JSONC | commentjson |
|---------|--------------|-------------|
| `//` comments | Yes | Yes |
| `#` comments | Yes | Yes |
| `/* */` comments | Yes | No (PyPI 0.9.0) |
| Trailing commas | Yes | Yes |
| Dependencies | None (stdlib only) | `lark-parser` |
| Implementation | Regex + `json.loads` | LALR parser + reconstruct |
| Maintained | Active | Abandoned (2021) |
