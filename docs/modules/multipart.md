# Multipart

Zero-dependency multipart/form-data parser and encoder -- stdlib only, Python 3.10+.

> **Replaces:** `python-multipart`

## Overview

The `multipart` module parses and encodes `multipart/form-data` bodies per RFC 7578 / RFC 2046. Designed for HTTP file upload handling without any third-party dependencies.

| File | Description | Dependencies |
|------|-------------|--------------|
| `multipart/multipart.py` | Multipart parser & encoder | None (stdlib only) |

### Key Features

- **Boundary-split parsing** — fast byte-level splitting with robust boundary detection
- **Content-Transfer-Encoding** — supports `base64` and `quoted-printable` decoding
- **RFC 5987 filename*** — decodes extended filename parameters (e.g. `filename*=UTF-8''...`)
- **Security limits** — configurable `max_part_size` (10 MB), `max_parts` (1000), `max_header_size` (16 KB)
- **Frozen dataclass output** — parsed parts are immutable `Part` objects with `.text` and `.is_file` helpers
- **Encode support** — build multipart bodies from fields and file tuples
- **~590 lines** — single file, no dependencies

## How to Use in Your Project

```bash
cp multipart/multipart.py your_project/
```

```python
from multipart import parse_multipart, encode_multipart, Part
```

## Usage Examples

### Parse a Multipart Body

```python
from multipart import parse_multipart

body = b"--boundary\r\nContent-Disposition: form-data; name=\"field1\"\r\n\r\nvalue1\r\n--boundary--\r\n"
parts = parse_multipart(body, "multipart/form-data; boundary=boundary")

for part in parts:
    print(part.name, part.text)  # "field1" "value1"
```

### Encode Fields and Files

```python
from multipart import encode_multipart

body, content_type = encode_multipart(
    fields={"username": "alice", "bio": "Hello world"},
    files={"avatar": ("photo.png", b"\x89PNG...", "image/png")},
)
# content_type: "multipart/form-data; boundary=..."
# body: ready to send as HTTP request body
```

### File Upload Fields

```python
from multipart import encode_multipart

# Files can be specified in several forms:
files = {
    "doc": b"raw bytes",                              # auto filename, octet-stream
    "report": ("report.pdf", pdf_bytes),               # named file
    "image": ("photo.jpg", jpg_bytes, "image/jpeg"),   # named file with MIME type
}
body, content_type = encode_multipart(files=files)
```

### Round-Trip

```python
from multipart import encode_multipart, parse_multipart

# Encode
body, ct = encode_multipart(
    fields={"name": "Alice"},
    files={"doc": ("readme.txt", b"Hello!", "text/plain")},
)

# Parse back
parts = parse_multipart(body, ct)
for part in parts:
    if part.is_file:
        print(f"File: {part.filename}, size: {len(part.data)}")
    else:
        print(f"Field: {part.name} = {part.text}")
```

### Security Limits

```python
from multipart import parse_multipart

# Restrict to 1 MB per part and 10 parts max
parts = parse_multipart(body, content_type, max_part_size=1_000_000, max_parts=10)

# Disable limits (not recommended for untrusted input)
parts = parse_multipart(body, content_type, max_part_size=0, max_parts=0)
```

### Extract Boundary

```python
from multipart import extract_boundary

boundary = extract_boundary("multipart/form-data; boundary=abc123")
print(boundary)  # "abc123"

# Also handles quoted boundaries
boundary = extract_boundary('multipart/form-data; boundary="my-boundary"')
print(boundary)  # "my-boundary"
```

## API Reference

### `parse_multipart(body, content_type, *, max_part_size=10MB, max_parts=1000)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `body` | `bytes` | Raw request body |
| `content_type` | `str` | Full Content-Type header or bare boundary string |
| `max_part_size` | `int` | Max bytes per part (0 to disable) |
| `max_parts` | `int` | Max number of parts (0 to disable) |

Returns `list[Part]`.

### `encode_multipart(fields=None, files=None, *, boundary=None)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `fields` | `dict \| list[tuple]` | Text form fields |
| `files` | `dict \| list[tuple]` | File uploads (see formats above) |
| `boundary` | `str \| None` | Custom boundary (auto-generated if None) |

Returns `(body_bytes, content_type_header)`.

### `extract_boundary(content_type)`

Extracts the boundary string from a Content-Type header. Returns the boundary as a string.

### `Part` (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Form field name |
| `data` | `bytes` | Raw content bytes |
| `filename` | `str \| None` | Original filename (None for text fields) |
| `content_type` | `str` | MIME type (default: `"text/plain"`) |
| `headers` | `dict[str, str]` | All MIME headers (keys lowercased) |

Properties:

- `.text` — decode data as text using charset from content_type (or UTF-8)
- `.is_file` — True if the part has a filename

### Exceptions

| Exception | Description |
|-----------|-------------|
| `MultipartError` | Base exception |
| `MultipartParseError` | Malformed input, missing boundary, limits exceeded |
| `MultipartEncodeError` | Invalid encode arguments |

## Notes and Caveats

!!! info "RFC Compliance"
    Implements RFC 7578 (multipart/form-data) and RFC 2046 (MIME multipart). Handles edge cases like preamble/epilogue, missing final boundary, and CRLF/LF normalization.

!!! tip "Content-Transfer-Encoding"
    Parts with `Content-Transfer-Encoding: base64` or `quoted-printable` are automatically decoded. This is rare in HTTP but common in email MIME.

!!! warning "Memory"
    The parser loads the entire body into memory. For very large file uploads, consider a streaming parser instead.

- **Python version**: Requires Python 3.10+.
- **Performance**: 1.4–4x faster than python-multipart for parsing. See benchmarks below.

## Benchmark

See [Multipart Benchmark](../benchmarks/multipart.md) for performance measurements.
