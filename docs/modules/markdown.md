# Markdown

Markdown to HTML renderer -- zero dependencies, stdlib only, Python 3.10+.

## Overview

The Markdown module provides a drop-in replacement for `mistune.html()` to render common Markdown to HTML. It supports a CommonMark subset plus GFM tables -- all without any third-party dependencies.

| File | Description | Dependencies |
|------|-------------|--------------|
| `markdown.py` | Pure Python implementation | None (stdlib only) |

The renderer uses a two-phase architecture: a block-level parser (line-based state machine) feeds into an inline parser (regex with a placeholder system to prevent double-escaping), producing HTML string output directly without an intermediate AST.

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp markdown/markdown.py your_project/
```

Then import directly:

```python
from markdown import render
```

## API Reference

### `render(text)`

Convert Markdown text to HTML.

```python
def render(text: str) -> str
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `text` | `str` | -- | Markdown source string. |

**Returns:** `str` -- HTML string.

**Example:**

```python
from markdown import render

html = render("# Hello\n\nThis is **bold**.")
# '<h1>Hello</h1>\n<p>This is <strong>bold</strong>.</p>\n'
```

## Usage Examples

### Basic Rendering

```python
from markdown import render

html = render("""
# My Document

This is a paragraph with **bold**, *italic*, and `code`.

## Code Block

```python
def hello():
    print("world")
``\`

> A blockquote with **emphasis**.

- Item 1
- Item 2
  - Nested item
""")
```

### Headings

```python
# ATX headings
render("# Heading 1")        # <h1>Heading 1</h1>
render("## Heading 2")       # <h2>Heading 2</h2>
render("### Heading 3")      # <h3>Heading 3</h3>

# Setext headings
render("Heading 1\n=========")  # <h1>Heading 1</h1>
render("Heading 2\n---------")  # <h2>Heading 2</h2>
```

### Emphasis

```python
render("*italic*")            # <em>italic</em>
render("**bold**")            # <strong>bold</strong>
render("***bold italic***")   # <em><strong>bold italic</strong></em>
```

### Links and Images

```python
# Inline link
render("[click](https://example.com)")
# <a href="https://example.com">click</a>

# Link with title
render('[click](https://example.com "Title")')
# <a href="https://example.com" title="Title">click</a>

# Reference link
render("[click][ref]\n\n[ref]: https://example.com")

# Image
render("![alt text](https://example.com/img.png)")
# <img src="https://example.com/img.png" alt="alt text" />
```

### Lists

```python
# Unordered
render("- item 1\n- item 2\n- item 3")

# Ordered
render("1. first\n2. second\n3. third")

# Nested
render("- parent\n  - child\n  - child\n- sibling")
```

### Tables (GFM)

```python
render("""
| Name  | Age |
| ----- | --- |
| Alice | 30  |
| Bob   | 25  |
""")
```

Column alignment is supported via `:---` (left), `:---:` (center), and `---:` (right) syntax.

### Fenced Code Blocks

```python
render("```python\ndef foo():\n    pass\n```")
# Produces <pre><code class="language-python">...</code></pre>
```

## Supported Features

| Feature | Syntax | Example |
|---------|--------|---------|
| ATX headings | `# ` to `###### ` | `# Title` |
| Setext headings | `===` / `---` underlines | `Title\n====` |
| Paragraphs | Blank line separated | Two blank lines |
| Emphasis (italic) | `*text*` or `_text_` | `*italic*` |
| Emphasis (bold) | `**text**` or `__text__` | `**bold**` |
| Bold italic | `***text***` | `***both***` |
| Inline code | `` `code` `` | `` `var` `` |
| Fenced code blocks | ` ``` ` or `~~~` | With optional language tag |
| Indented code blocks | 4-space indent | `    code` |
| Block quotes | `> ` prefix | `> quoted`, supports nesting |
| Unordered lists | `- `, `* `, `+ ` | `- item`, supports nesting |
| Ordered lists | `1. ` | `1. first`, supports `start` attribute |
| Inline links | `[text](url)` | With optional title |
| Reference links | `[text][ref]` | `[ref]: url` definitions |
| Images | `![alt](url)` | With optional title |
| Thematic breaks | `---`, `***`, `___` | Horizontal rule |
| Hard line breaks | Two trailing spaces or `\` | Line break within paragraph |
| Backslash escapes | `\*`, `\_`, etc. | Escape special characters |
| Autolinks | `<https://...>` | `<user@example.com>` |
| GFM tables | Pipe syntax | With column alignment |
| HTML escaping | Automatic | `<`, `>`, `&` escaped |

## Not Supported

- Raw HTML passthrough (escaped for safety)
- Footnotes, definition lists
- Math/LaTeX
- Strikethrough, task lists
- Anchors/aliases

## Security

- All text content is HTML-escaped via `html.escape()`
- Code blocks only escape HTML, no Markdown processing inside
- URLs are checked against harmful protocols (`javascript:`, `vbscript:`, `file:`, `data:`) -- blocked URLs are replaced with `#harmful-link`

## Notes and Caveats

!!! info "Single-Function API"
    Unlike mistune which provides a full parser/renderer class hierarchy, this module exposes a single `render()` function. This is intentional -- for the common use case of converting Markdown to HTML, no configuration is needed.

!!! info "CommonMark Subset"
    This renderer targets the most commonly used Markdown features. It does not aim for 100% CommonMark spec compliance, but covers all features typically found in LLM output and documentation.

- **Python version:** Requires Python 3.10+ (uses `X | Y` union type syntax).
- **Output compatibility:** Produces HTML output that matches `mistune.html()` for all supported features.
- **Performance:** 1.8--2.6x faster than mistune across small, medium, and large documents.

## Benchmark

Benchmarked against `mistune` across three document sizes (small, medium, large).

See [Markdown Benchmark](../benchmarks/markdown.md) for detailed results.
