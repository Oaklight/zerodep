# Tabulate

Zero-dependency table formatting with multiple output styles -- stdlib only, Python 3.10+.

## Overview

The Tabulate module pretty-prints tabular data as formatted text tables. It supports 7 output formats, flexible header modes, column alignment, number formatting, and CJK-aware column widths -- all without any third-party dependencies.

| File | Description | Dependencies |
|------|-------------|--------------|
| `tabulate.py` | Pure Python implementation | None (stdlib only: `re`, `math`, `unicodedata`, `dataclasses`) |

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp tabulate/tabulate.py your_project/
```

Then import directly:

```python
from tabulate import tabulate
```

## Usage Examples

### Basic Table

```python
from tabulate import tabulate

data = [["Alice", 24], ["Bob", 30]]
print(tabulate(data, headers=["Name", "Age"]))
# Name      Age
# ------  -----
# Alice      24
# Bob        30
```

### Grid Format

```python
print(tabulate(data, headers=["Name", "Age"], tablefmt="grid"))
# +--------+-------+
# | Name   |   Age |
# +========+=======+
# | Alice  |    24 |
# | Bob    |    30 |
# +--------+-------+
```

### GitHub Markdown

```python
print(tabulate(data, headers=["Name", "Age"], tablefmt="github"))
# | Name   |   Age |
# |--------|-------|
# | Alice  |    24 |
# | Bob    |    30 |
```

### Pipe Format (Markdown)

```python
print(tabulate(data, headers=["Name", "Age"], tablefmt="pipe"))
# | Name   |   Age |
# |:-------|------:|
# | Alice  |    24 |
# | Bob    |    30 |
```

### Different Input Shapes

```python
# List of dicts
data = [{"name": "Alice", "age": 24}, {"name": "Bob", "age": 30}]
print(tabulate(data, headers="keys"))

# Dict of lists
data = {"name": ["Alice", "Bob"], "age": [24, 30]}
print(tabulate(data, headers="keys"))
```

### Number Formatting

```python
data = [[3.14159, 2.71828], [1.41421, 1.73205]]
print(tabulate(data, headers=["Pi-ish", "E-ish"], floatfmt=".2f"))
# Pi-ish    E-ish
# --------  -------
# 3.14      2.72
# 1.41      1.73
```

### Row Index

```python
data = [["Alice", 24], ["Bob", 30]]
print(tabulate(data, headers=["Name", "Age"], showindex=True))
#       Name      Age
# --  ------  -----
#  0  Alice      24
#  1  Bob        30
```

### Column Alignment

```python
data = [["Alice", 24], ["Bob", 30]]
print(tabulate(data, headers=["Name", "Age"], colalign=("center", "left")))
```

## Supported Formats

| Format | Description |
|--------|-------------|
| `plain` | No borders or separators |
| `simple` | Simple header separator (default) |
| `grid` | Full grid with borders |
| `pipe` | Markdown pipe table with alignment |
| `orgtbl` | Emacs Org-mode table |
| `pretty` | Centered, boxed table |
| `github` | GitHub-flavored markdown |

## API Reference

### `tabulate(tabular_data, headers, tablefmt, floatfmt, numalign, stralign, missingval, showindex, colalign)`

Format tabular data as a pretty-printed text table.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `tabular_data` | `Any` | -- | Input data: list of lists, list of dicts, dict of lists, or iterable of iterables. |
| `headers` | `Any` | `()` | Column headers: list/tuple of strings, `"firstrow"`, `"keys"`, or empty tuple. |
| `tablefmt` | `str` | `"simple"` | Output format: `"plain"`, `"simple"`, `"grid"`, `"pipe"`, `"orgtbl"`, `"pretty"`, `"github"`. |
| `floatfmt` | `str` | `"g"` | Format string for float values. |
| `numalign` | `str` | `"decimal"` | Numeric column alignment: `"right"`, `"left"`, `"center"`, `"decimal"`. |
| `stralign` | `str` | `"left"` | Text column alignment: `"right"`, `"left"`, `"center"`. |
| `missingval` | `str` | `""` | String to display for `None` values. |
| `showindex` | `bool \| str \| Sequence` | `False` | Prepend row indices. `True`, `"always"`, or a sequence of index values. |
| `colalign` | `Sequence[str] \| None` | `None` | Per-column alignment overrides. |

**Returns:** The formatted table as a string.

**Raises:** `ValueError` if `tablefmt` is not recognised.

## Comparison with tabulate

| Feature | zerodep tabulate | tabulate |
|---------|-----------------|----------|
| Dependencies | None (stdlib only) | None |
| Files | Single file | Package (multiple files) |
| Table formats | 7 (plain, simple, grid, pipe, orgtbl, pretty, github) | 20+ |
| CJK support | Yes (via `WIDE_CHARS_MODE`) | Yes |
| Multiline cells | No | Yes |
| Format speed (small) | 32.5 us | 93.8 us (2.89x slower) |
| Format speed (large) | 3.9 ms | 13.8 ms (3.56x slower) |

**When to use zerodep:** You need fast table formatting with common output styles and zero dependencies.

**When to use tabulate:** You need niche output formats (latex, rst, mediawiki) or multiline cell support.

## Benchmark

Benchmarked against `tabulate` across small, medium, and large table sizes.

See [Tabulate Benchmark](../benchmarks/tabulate.md) for detailed results.
