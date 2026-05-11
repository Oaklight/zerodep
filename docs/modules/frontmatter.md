# Frontmatter

Frontmatter parser and serializer (YAML, TOML, JSON) -- zero dependencies, stdlib only, Python 3.10+.

> **Replaces:** `python-frontmatter`

## Overview

The frontmatter module parses and serializes file-header metadata (frontmatter) in YAML, TOML, or JSON format. YAML `---` frontmatter is the de facto standard used by Jekyll, Hugo, Astro, MkDocs, Obsidian, and many other tools. This module provides a drop-in alternative to [`python-frontmatter`](https://pypi.org/project/python-frontmatter/) with zero external dependencies.

| File | Description | Dependencies |
|------|-------------|--------------|
| `frontmatter.py` | Frontmatter parser and serializer | `yaml` (sibling module) |

## How to Use in Your Project

Copy the module file and its dependency into your project:

```bash
cp frontmatter/frontmatter.py your_project/
cp yaml/yaml.py your_project/
```

Then import directly:

```python
from frontmatter import loads, dumps, Document
```

## Supported Formats

| Format | Delimiter | Parser | Notes |
|--------|-----------|--------|-------|
| YAML | `---` ... `---` | Sibling `yaml` module | Default; covers 90%+ of real-world frontmatter |
| TOML | `+++` ... `+++` | `tomllib` (Python 3.11+ stdlib) | Read-only via stdlib; simple serialization built-in |
| JSON | `{` ... `}` | stdlib `json` | Object at start of file, no delimiters needed |

## API Reference

### `loads(text, *, handler=None)`

Parse a text string with frontmatter.

```python
def loads(text: str, *, handler: str | None = None) -> Document
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `text` | `str` | *(required)* | The full document text. |
| `handler` | `str \| None` | `None` | Force a specific format (`"yaml"`, `"toml"`, `"json"`). Auto-detects if `None`. |

**Returns:** A `Document` with parsed metadata and body content.

**Example:**

```python
doc = loads("---\ntitle: Hello World\ntags: [python, zerodep]\n---\nBody text.")
doc.metadata  # {'title': 'Hello World', 'tags': ['python', 'zerodep']}
doc.content   # 'Body text.'
```

---

### `load(source, *, handler=None)`

Parse a file with frontmatter.

```python
def load(
    source: IO[str] | str | Path,
    *,
    handler: str | None = None,
) -> Document
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `source` | `IO[str] \| str \| Path` | *(required)* | A file path or open text stream. |
| `handler` | `str \| None` | `None` | Force format. Auto-detects if `None`. |

**Returns:** A `Document` with parsed metadata and body content.

**Example:**

```python
doc = load("post.md")
doc = load(Path("post.md"))
with open("post.md") as f:
    doc = load(f)
```

---

### `dumps(doc, *, handler="yaml", **kwargs)`

Serialize a `Document` to a string with frontmatter.

```python
def dumps(
    doc: Document,
    *,
    handler: str = "yaml",
    **kwargs: Any,
) -> str
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `doc` | `Document` | *(required)* | The document to serialize. |
| `handler` | `str` | `"yaml"` | Output format (`"yaml"`, `"toml"`, `"json"`). |
| `**kwargs` | `Any` | | Passed to the underlying serializer. |

**Returns:** The full document text with frontmatter and body.

**Example:**

```python
doc = Document({"title": "Hello"}, "Body text.")
text = dumps(doc)
# ---
# title: Hello
# ---
# Body text.
```

---

### `dump(doc, dest, *, handler="yaml", **kwargs)`

Serialize a `Document` to a file.

```python
def dump(
    doc: Document,
    dest: IO[str] | str | Path,
    *,
    handler: str = "yaml",
    **kwargs: Any,
) -> None
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `doc` | `Document` | *(required)* | The document to serialize. |
| `dest` | `IO[str] \| str \| Path` | *(required)* | A file path or open text stream. |
| `handler` | `str` | `"yaml"` | Output format. |

---

### `check(text)`

Check whether a text string contains frontmatter.

```python
def check(text: str) -> bool
```

**Returns:** `True` if frontmatter is detected.

---

### `detect_handler(text)`

Detect the frontmatter format.

```python
def detect_handler(text: str) -> str | None
```

**Returns:** `"yaml"`, `"toml"`, `"json"`, or `None`.

---

### `class Document`

A dataclass with frontmatter metadata and body content.

```python
@dataclasses.dataclass
class Document:
    metadata: dict[str, Any]
    content: str
```

Supports dict-like access on metadata: `doc["key"]`, `doc["key"] = val`, `"key" in doc`, `doc.get("key")`, `doc.keys()`, `doc.values()`, `doc.items()`.

---

### Exceptions

- **`FrontmatterError`** -- base exception for parsing errors.
- **`HandlerError(FrontmatterError)`** -- raised when a requested handler is not available.

## Usage Examples

### Parse a Markdown File with YAML Frontmatter

```python
from frontmatter import loads

text = """---
title: My Post
date: 2026-03-28
tags:
  - python
  - zerodep
---
# Introduction

This is the body content.
"""

doc = loads(text)
print(doc.metadata["title"])  # 'My Post'
print(doc.metadata["tags"])   # ['python', 'zerodep']
print(doc.content)            # '# Introduction\n\nThis is the body content.\n'
```

### Create and Serialize a Document

```python
from frontmatter import Document, dumps

doc = Document(
    metadata={"title": "New Post", "draft": True},
    content="Hello, world!\n",
)
print(dumps(doc))
# ---
# title: New Post
# draft: true
# ---
# Hello, world!
```

### JSON Frontmatter

```python
from frontmatter import loads

text = '{"title": "Hello", "count": 42}\nSome content after JSON.'
doc = loads(text)
print(doc.metadata)  # {'title': 'Hello', 'count': 42}
```

### TOML Frontmatter (Python 3.11+)

```python
from frontmatter import loads

text = """+++
title = "Hugo Post"
date = 2026-03-28
+++
Content here.
"""

doc = loads(text)
print(doc.metadata["title"])  # 'Hugo Post'
```

### Roundtrip: Parse, Modify, Serialize

```python
from frontmatter import load, dump

doc = load("post.md")
doc["draft"] = False
doc["tags"].append("published")
dump(doc, "post.md")
```

## Notes and Caveats

!!! info "YAML Handler Dependency"
    The YAML handler requires the sibling `yaml` module. Place `yaml.py` in a sibling directory or on `sys.path`. The module will raise `HandlerError` if YAML parsing is attempted without it.

!!! info "TOML Support"
    TOML parsing requires Python 3.11+ (`tomllib` in stdlib). TOML serialization supports flat key-value pairs only; nested tables will raise `FrontmatterError` (use YAML for nested data).

- **Python version:** Requires Python 3.10+ (uses `X | Y` union type hint syntax).
- **BOM handling:** Leading UTF-8 BOM (`\ufeff`) is stripped before detection.
- **Windows line endings:** CRLF (`\r\n`) is handled correctly in both parsing and detection.
- **No frontmatter:** If no frontmatter is detected, the entire text is returned as `content` with empty `metadata`.

## Benchmark

Benchmarked against `python-frontmatter` across three input sizes (small, medium, large) for both parse and serialize operations.

See [Frontmatter Benchmark](../benchmarks/frontmatter.md) for detailed results.
