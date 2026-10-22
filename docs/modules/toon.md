# TOON Encoder/Decoder

A zero-dependency TOON (Token-Oriented Object Notation) encoder and decoder. TOON is a compact, human-readable serialization format designed for LLM contexts, achieving 30-60% token reduction compared to JSON.

> **Replaces:** `toon-format`

This module implements **TOON 4.4** and passes all **564** official
conformance fixtures (160 encode, 404 decode). The vendored fixture set is
gated in CI by `toon/test_toon_conformance.py`.

## Features

- **Compact encoding**: 30-60% fewer tokens than JSON
- **Human-readable**: YAML-like indentation with CSV-like tabular arrays
- **Roundtrip fidelity**: `decode(encode(data)) == data` for JSON-compatible types
- **Type normalization**: Handles Python types (datetime, Decimal, set, Path, tuple)
- **Multiple delimiters**: Comma, tab, and pipe separators
- **Strict/lenient modes**: Configurable validation on decode

## Quick Start

```python
from toon import encode, decode

# Encode Python data to TOON
data = {"name": "Alice", "age": 30, "active": True}
text = encode(data)
# name: Alice
# age: 30
# active: true

# Decode TOON back to Python
result = decode(text)
assert result == data

# Tabular arrays are compact
employees = [
    {"id": 1, "name": "Alice", "dept": "eng"},
    {"id": 2, "name": "Bob", "dept": "sales"},
]
print(encode(employees))
# [2]{id,name,dept}:
#   1,Alice,eng
#   2,Bob,sales
```

## API

### `encode(value, options=None)`

Encode a Python value into TOON format.

- **value**: Any JSON-serializable value, plus Python types (datetime, Decimal, set, Path, tuple)
- **options**: Optional `EncodeOptions` dict with `indent`, `delimiter`. Unknown keys raise `TypeError`.

### `decode(text, options=None)`

Decode a TOON-formatted string to a Python value.

- **text**: TOON-formatted string, or UTF-8 encoded `bytes` / `bytearray`
- **options**: Optional `DecodeOptions` dict with `indent`, `strict`. Unknown keys raise `TypeError`.

### `ToonDecodeError`

Raised when TOON decoding fails: malformed input, an invalid escape sequence,
a trailing backslash in a quoted value, or input that is not valid UTF-8.

`ToonDecodeError` subclasses `Exception`, not `ValueError`, so
`except ValueError` around `decode()` does not catch malformed input — catch
`ToonDecodeError` instead. Every decode failure the module raises is this
type.

## Encoding Options

```python
from toon import encode, EncodeOptions

data = [1, 2, 3]

# Tab-separated
encode(data, EncodeOptions(delimiter="\t"))
# [3	]: 1	2	3

# Pipe-separated
encode(data, EncodeOptions(delimiter="|"))
# [3|]: 1|2|3

# Custom indent
encode({"a": {"b": 1}}, EncodeOptions(indent=4))
# a:
#     b: 1
```

The pre-4.0 `lengthMarker` option is not part of TOON 4.4: encoders never
emit `[#N]`, and passing `lengthMarker` raises `ValueError`.

## TOON Format Overview

### Objects

```
name: Alice
age: 30
active: true
```

### Inline Arrays

```
[3]: 1,2,3
```

### Tabular Arrays

```
[2]{id,name}:
  1,Alice
  2,Bob
```

### Nested Structures

```
user:
  name: Alice
  tags[2]: dev,python
```

## Type Normalization

| Python Type | TOON Representation |
|-------------|-------------------|
| `None` | `null` |
| `bool` | `true` / `false` |
| `int`, `float` | Numeric literal |
| `str` | Unquoted or quoted |
| `datetime` | ISO 8601 string |
| `Decimal` | Float value |
| `set`, `frozenset` | Sorted array |
| `tuple` | Array (order preserved) |
| `Path` | String path |
| `inf`, `nan` | `null` |
| `-0.0` | `0` |
| Callable | `TypeError` (outside the data model) |

## Comparison with toon_format

| Feature | zerodep TOON | toon_format |
|---------|-------------|-------------|
| Dependencies | None (stdlib only) | None (core encode/decode) |
| Files | Single file | 7 source files |
| Token counting | Not included | Requires `tiktoken` |
| CLI | Not included | Included |
| encode/decode | Full support | Full support |
| Encode speed | 6.5 - 869.8 us | 6.6 - 1,093.3 us (mean, parity) |
| Decode speed | 12.6 - 810.8 us | 9.7 - 787.6 us (mean, parity) |
| Token savings vs JSON | 38-71% fewer characters | Same (identical format) |
