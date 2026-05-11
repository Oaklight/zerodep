# TOON Encoder/Decoder

A zero-dependency TOON (Token-Oriented Object Notation) encoder and decoder. TOON is a compact, human-readable serialization format designed for LLM contexts, achieving 30-60% token reduction compared to JSON.

> **Replaces:** `toon-format`

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
- **options**: Optional `EncodeOptions` dict with `indent`, `delimiter`, `lengthMarker`

### `decode(text, options=None)`

Decode a TOON-formatted string to a Python value.

- **text**: TOON-formatted string
- **options**: Optional `DecodeOptions` dict with `indent`, `strict`

### `ToonDecodeError`

Raised when TOON decoding fails.

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

# With length marker
encode(data, EncodeOptions(lengthMarker="#"))
# [#3]: 1,2,3

# Custom indent
encode({"a": {"b": 1}}, EncodeOptions(indent=4))
# a:
#     b: 1
```

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
| Callable | `null` |

## Comparison with toon_format

| Feature | zerodep TOON | toon_format |
|---------|-------------|-------------|
| Dependencies | None (stdlib only) | `typing-extensions` |
| Files | Single file | 18 source files |
| Token counting | Not included | Requires `tiktoken` |
| CLI | Not included | Included |
| encode/decode | Full support | Full support |
| Encode speed | 5.3 - 695.7 us | 7.8 - 952.6 us (1.3-1.5x slower) |
| Decode speed | 13.4 - 1,463.3 us | 15.4 - 1,559.1 us (1.1x slower) |
| Token savings vs JSON | 38-71% fewer characters | Same (identical format) |
