# Extended JSON Parser (jsonx)

A zero-dependency extended JSON parser that supports JSONC (JSON with Comments), JSONL/NDJSON (newline-delimited JSON), single-line comments (`//`, `#`), block comments (`/* */`), and trailing commas.

> **Replaces:** `commentjson`, `json5` (partial)

## Features

- **Single-line comments**: `//` and `#` styles
- **Block comments**: `/* ... */` (including multiline)
- **Trailing commas**: In objects and arrays
- **JSONL/NDJSON**: Newline-delimited JSON parsing and serialization
- **Drop-in replacement**: Same API as stdlib `json` module, with one deliberate difference — `dumps` / `dump` refuse `NaN` and `Infinity` by default, because those constants are not valid JSON
- **String-safe**: Comments inside quoted strings are preserved
- **Error reporting**: `JSONCDecodeError` with position information

## Quick Start

```python
from jsonx import loads, load, dumps, dump

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

Deserialize a JSONC string to a Python object. Strips comments and trailing commas before delegating to `json.loads`; a document that is already plain JSON skips that preprocessing pass. Passing `cls` or a hook (`object_hook`, `object_pairs_hook`, `parse_float`, `parse_int`, `parse_constant`) opts out of the fast path, so the callback is never invoked on a speculative parse. Only `str` is accepted; passing `bytes` raises `TypeError`, so decode bytes first.

All keyword arguments accepted by `json.loads` are supported (`cls`, `object_hook`, `parse_float`, `parse_int`, `parse_constant`, `object_pairs_hook`).

### `load(fp, **kwargs)`

Deserialize a JSONC file-like object. Reads the stream and passes to `loads`.

### `dumps(obj, **kwargs)` / `dump(obj, fp, **kwargs)`

Pass-through to `json.dumps` / `json.dump`, except for `allow_nan`, which
defaults to `False`: a non-finite float raises `ValueError` instead of being
written as the bare `NaN` / `Infinity` constants, which `JSON.parse`, Go's
`encoding/json` and serde all reject. Pass `allow_nan=True` when the consumer
is known to accept Python's constants.

```python
>>> dumps({"x": float("nan")})
ValueError: Out of range float values are not JSON compliant
>>> dumps({"x": float("nan")}, allow_nan=True)
'{"x": NaN}'
```

`dumps_lines` / `dump_lines` forward the same default to `json.dumps`, so
the JSONL helpers behave identically.

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

| Feature | zerodep jsonx | commentjson |
|---------|--------------|-------------|
| `//` comments | Yes | Yes |
| `#` comments | Yes | Yes |
| `/* */` comments | Yes | No (PyPI 0.9.0) |
| Trailing commas | Yes | Yes |
| JSONL/NDJSON | Yes | No |
| Dependencies | None (stdlib only) | `lark-parser` |
| Implementation | Regex + `json.loads` | LALR parser + reconstruct |
| Maintained | Active | Abandoned (2021) |
