# SyncTeX Parser

SyncTeX bidirectional search parser -- zero dependencies, stdlib only, Python 3.10+.

## Overview

The SyncTeX module parses `.synctex` and `.synctex.gz` files produced by TeX engines (with `-synctex=1`) and provides spatial queries for both directions:

- **Inverse search** -- PDF position → source file and line number
- **Forward search** -- source file and line number → PDF position

Pure Python, no external dependencies.

| File | Description | Dependencies |
|------|-------------|--------------|
| `synctex.py` | Pure Python implementation | None (stdlib only: `gzip`, `re`, `dataclasses`) |

### Key Features

- **SyncTeX parsing** -- reads both plain `.synctex` and gzip-compressed `.synctex.gz` files
- **Inverse search** -- maps PDF page coordinates (in PDF points) to source file and line number
- **Forward search** -- maps source file and line number to PDF page coordinates
- **Path normalization** -- strips configurable prefixes (e.g. `/workspace/` for Docker builds) and `./` from input paths
- **Spatial matching** -- multi-phase closest-box algorithm: vertical containment, horizontal containment, then nearest fallback

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp synctex/synctex.py your_project/
```

Then import directly:

```python
from synctex import parse_synctex, inverse_search, forward_search, SyncTeXData
```

## Usage Examples

### Basic Inverse Search

```python
from synctex import parse_synctex, inverse_search

# Parse a SyncTeX file
data = parse_synctex("main.synctex.gz")

# Find source location for a point on page 1
result = inverse_search(data, page=1, x=150.0, y=300.0)
if result:
    print(f"{result['file']}:{result['line']}")
    # e.g. "main.tex:42"
```

### Docker / Remote Builds

```python
from synctex import parse_synctex, inverse_search

# Strip Docker workspace prefix from paths
data = parse_synctex("main.synctex.gz", strip_prefix="/workspace/")

result = inverse_search(data, page=2, x=100.0, y=200.0)
# result["file"] will be "chapter1.tex" instead of "/workspace/chapter1.tex"
```

### Forward Search (Source → PDF)

```python
from synctex import parse_synctex, forward_search

data = parse_synctex("main.synctex.gz", strip_prefix="/workspace/")

# Jump from source line to PDF position
result = forward_search(data, file="main.tex", line=42)
if result:
    print(f"Page {result['page']}, x={result['x']}, y={result['y']}")
    # e.g. "Page 1, x=150.0, y=300.0"
```

### Inspecting Parsed Data

```python
from synctex import parse_synctex

data = parse_synctex("main.synctex")

# List all input files
for tag, path in data.inputs.items():
    print(f"  [{tag}] {path}")

# Count boxes per page
for page, boxes in data.pages.items():
    print(f"  Page {page}: {len(boxes)} hboxes")

# Check preamble values
print(f"Magnification: {data.magnification}")
print(f"Unit: {data.unit}")
```

## API Reference

### Functions

| Function | Description |
|----------|-------------|
| `parse_synctex(path, *, strip_prefix="")` | Parse a `.synctex` or `.synctex.gz` file |
| `inverse_search(data, page, x, y)` | Find source location for a PDF coordinate |
| `forward_search(data, file, line)` | Find PDF position for a source location |

### Classes

| Class | Description |
|-------|-------------|
| `SyncTeXData` | Parsed SyncTeX data with inputs, pages, magnification, unit, offsets |
| `HBox` | Horizontal box record with tag, line, x, y, width, height, depth |

### `parse_synctex(synctex_path, *, strip_prefix="")`

Parse a SyncTeX file and return a `SyncTeXData` object.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `synctex_path` | `str` | Path to `.synctex` or `.synctex.gz` file |
| `strip_prefix` | `str` | Prefix to remove from input file paths (default: `""`) |

**Returns:** `SyncTeXData`

**Raises:** `FileNotFoundError` if the file does not exist.

---

### `inverse_search(data, page, x, y)`

Find the source file and line for a point on a PDF page.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `SyncTeXData` | Parsed data from `parse_synctex()` |
| `page` | `int` | 1-based page number |
| `x` | `float` | Horizontal position in PDF points (72 DPI) |
| `y` | `float` | Vertical position in PDF points (72 DPI) |

**Returns:** `{"file": str, "line": int}` or `None` if no match found.

---

### `forward_search(data, file, line)`

Find the PDF page and position for a source file and line number.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `SyncTeXData` | Parsed data from `parse_synctex()` |
| `file` | `str` | Source file path (relative, as stored in `data.inputs`) |
| `line` | `int` | 1-based line number in the source file |

**Returns:** `{"page": int, "x": float, "y": float}` or `None` if no match found.

---

### `SyncTeXData`

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `inputs` | `dict[int, str]` | `{}` | File tag to path mapping |
| `pages` | `dict[int, list[HBox]]` | `{}` | Page number to hbox list |
| `magnification` | `int` | `1000` | TeX magnification factor |
| `unit` | `int` | `1` | Coordinate unit in scaled points |
| `x_offset` | `int` | `0` | Horizontal offset |
| `y_offset` | `int` | `0` | Vertical offset |

---

### `HBox`

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `tag` | `int` | -- | Input file tag |
| `line` | `int` | -- | Source line number |
| `x` | `int` | -- | Left edge in scaled points |
| `y` | `int` | -- | Baseline position in scaled points |
| `width` | `int` | `0` | Box width |
| `height` | `int` | `0` | Box height (above baseline) |
| `depth` | `int` | `0` | Box depth (below baseline) |
