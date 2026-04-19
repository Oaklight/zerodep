# Article Extractor (Readability)

Zero-dependency article content extractor inspired by Mozilla Readability.js -- stdlib only, Python 3.10+.

## Overview

The `readability` module extracts the main article content from web pages, removing navigation, ads, sidebars, and other clutter. It ports the core algorithm from [Mozilla Readability.js](https://github.com/mozilla/readability) and builds on the zerodep [`soup`](soup.md) module for HTML parsing and manipulation.

| File | Description | Dependencies |
|------|-------------|--------------|
| `readability.py` | Pure Python implementation | `soup` module (stdlib only) |

### Key Features

- **Content extraction** -- identifies and extracts the main article body from cluttered web pages
- **Metadata extraction** -- title, author, excerpt, published time, site name, language, text direction
- **JSON-LD support** -- extracts structured metadata from Schema.org JSON-LD blocks
- **OpenGraph / meta tags** -- falls back to og:title, og:description, article:author, etc.
- **Smart title refinement** -- strips site name suffixes from `<title>` tags (e.g. "Article Title | Site Name" → "Article Title")
- **2-level retry** -- first pass aggressively removes unlikely candidates; if result is too short, retries with relaxed filtering
- **Readability check** -- quick heuristic to determine if a page is likely an article before full extraction

## How to Use in Your Project

Copy both required files into your project:

```bash
cp soup/soup.py your_project/
cp readability/readability.py your_project/
```

Then import:

```python
from readability import extract, is_probably_readable
```

## Usage Examples

### Basic Article Extraction

```python
from readability import extract

html = """
<html><head><title>My Blog Post - My Site</title></head>
<body>
  <nav>Navigation links...</nav>
  <article>
    <h1>My Blog Post</h1>
    <p>This is the main content of the article with enough text
    to be considered meaningful content by the readability algorithm.</p>
    <p>More paragraphs with substantive content...</p>
  </article>
  <aside>Sidebar ads...</aside>
  <footer>Copyright...</footer>
</body></html>
"""

result = extract(html)
print(result.title)    # "My Blog Post"
print(result.text)     # Clean plain text of the article
print(result.content)  # Clean HTML of the article
print(result.length)   # Character count of extracted text
```

### Check if a Page is Readable

```python
from readability import is_probably_readable

# Quick check before doing full extraction
if is_probably_readable(html):
    result = extract(html)
else:
    print("This page doesn't appear to contain an article")
```

### Extract with URL for Metadata

```python
result = extract(html, url="https://example.com/article/123")
print(result.title)
print(result.author)
print(result.excerpt)
print(result.site_name)
print(result.published_time)
print(result.lang)
print(result.dir)   # "ltr" or "rtl"
```

### Working with JSON-LD Metadata

Pages with Schema.org JSON-LD get richer metadata:

```python
html = """
<html><head>
<script type="application/ld+json">
{
  "@type": "Article",
  "headline": "Breaking News Story",
  "author": {"name": "Jane Doe"},
  "datePublished": "2026-01-15T10:30:00Z",
  "description": "A summary of the breaking news."
}
</script>
</head><body>
<article><p>Long article content here...</p></article>
</body></html>
"""

result = extract(html)
print(result.title)           # "Breaking News Story"
print(result.author)          # "Jane Doe"
print(result.published_time)  # "2026-01-15T10:30:00Z"
print(result.excerpt)         # "A summary of the breaking news."
```

## Algorithm Overview

The readability algorithm follows Mozilla Readability.js's approach:

1. **Pre-clean** -- remove `<script>`, `<style>`, `<link>`, `<noscript>` tags
2. **Remove unlikely candidates** -- elements whose class/id matches patterns like "sidebar", "comment", "footer", "nav"
3. **Transform divs to paragraphs** -- divs with no block-level children become `<p>` tags for scoring
4. **Score paragraphs** -- assign content scores based on text length, comma count, and class/id heuristics; propagate scores to parent and grandparent nodes
5. **Select best candidate** -- pick the highest-scoring node
6. **Assemble article** -- merge high-scoring siblings into the article container
7. **Sanitize** -- remove low-quality elements (forms, empty nodes, high link-density sections)
8. **Retry if needed** -- if the extracted content is too short (<250 chars), retry without the aggressive candidate filtering

## API Reference

### `extract(html, url=None)`

Extract the main article content from an HTML string.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `html` | `str` | -- | The HTML string to extract from. |
| `url` | `str \| None` | `None` | Optional URL for metadata resolution. |

**Returns:** `ReadabilityResult` dataclass.

### `is_probably_readable(html, min_score=20, min_content_length=140)`

Quick heuristic check whether the HTML likely contains an article.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `html` | `str` | -- | The HTML string to check. |
| `min_score` | `float` | `20` | Minimum score threshold. |
| `min_content_length` | `int` | `140` | Minimum text length per node. |

**Returns:** `bool`

### `ReadabilityResult`

| Field | Type | Description |
|-------|------|-------------|
| `title` | `str` | Article title (refined from `<title>` or metadata) |
| `content` | `str` | Cleaned HTML of the article body |
| `text` | `str` | Plain text of the article body |
| `author` | `str \| None` | Author name |
| `excerpt` | `str \| None` | Article summary / description |
| `site_name` | `str \| None` | Site name |
| `published_time` | `str \| None` | Publication timestamp |
| `lang` | `str \| None` | Language code (e.g. `"en"`) |
| `dir` | `str \| None` | Text direction (`"ltr"` or `"rtl"`) |
| `length` | `int` | Character count of the plain text |

## Comparison with Alternatives

| Feature | zerodep readability | readability-lxml | Mozilla Readability.js |
|---------|-------------------|------------------|----------------------|
| Language | Python | Python | JavaScript |
| Dependencies | None (stdlib + soup) | lxml, cssselect | jsdom (Node.js) |
| Files | Single file + soup | Package | Package |
| JSON-LD metadata | Yes | No | Yes |
| OpenGraph metadata | Yes | Partial | Yes |
| Title refinement | Yes | Yes | Yes |
| RTL support | Yes | No | Yes |

**When to use zerodep:** You need article extraction in Python with zero pip dependencies.

**When to use readability-lxml:** You already have lxml in your stack and need maximum compatibility.

**When to use Mozilla Readability.js:** You're working in Node.js or need the reference implementation.

## Benchmark

Performance comparison against `readability-lxml` and Mozilla Readability.js.

See [Readability Benchmark](../benchmarks/readability.md) for detailed results.
