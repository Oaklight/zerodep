# XML

XML ↔ dict converter with fault-tolerant LLM tag extraction -- zero dependencies, stdlib only, Python 3.10+.

> **Replaces:** `xmltodict`

## Overview

The XML module provides an xmltodict-compatible bidirectional XML ↔ dict converter, plus a fault-tolerant tag extractor designed for LLM output parsing. It is a drop-in replacement for [`xmltodict`](https://pypi.org/project/xmltodict/) for the vast majority of use cases -- parsing sitemaps, RSS/Atom feeds, enterprise API responses, and LLM-structured output.

| File | Description | Dependencies |
|------|-------------|--------------|
| `xml.py` | Pure Python XML converter with LLM tag extraction | None (stdlib only) |

Two layers are provided:

- **Standard layer:** `parse()` / `unparse()` for xmltodict-compatible dict ↔ XML conversion
- **Lenient layer:** `extract_tags()` for fault-tolerant extraction of XML-like tags from LLM output

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp xml/xml.py your_project/
```

Then import directly:

```python
from xml import parse, unparse, extract_tags
```

!!! warning "Module Name Collision"
    The file is named `xml.py`, which shadows Python's stdlib `xml` package. The module handles this internally via `sys.path` / `sys.modules` manipulation. If you need to use stdlib `xml` alongside this module, consider renaming the file.

## API Reference

### `parse(xml_input, **kwargs)`

Parse an XML document into a Python dict. Compatible with `xmltodict.parse()`.

```python
def parse(
    xml_input: str | bytes | IO[bytes],
    *,
    encoding: str | None = None,
    process_namespaces: bool = False,
    namespace_separator: str = ":",
    disable_entities: bool = True,
    process_comments: bool = False,
    xml_attribs: bool = True,
    attr_prefix: str = "@",
    cdata_key: str = "#text",
    force_cdata: bool = False,
    cdata_separator: str = "",
    postprocessor: Callable | None = None,
    dict_constructor: type = dict,
    strip_whitespace: bool = True,
    force_list: bool | tuple[str, ...] | Callable | None = None,
    comment_key: str = "#comment",
) -> dict | None
```

**Key Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `xml_input` | `str \| bytes \| IO[bytes]` | *(required)* | XML string, bytes, or file-like object. |
| `attr_prefix` | `str` | `"@"` | Prefix for attribute keys in the output dict. |
| `cdata_key` | `str` | `"#text"` | Key for text content in the output dict. |
| `force_list` | `bool \| tuple \| Callable \| None` | `None` | Force list creation for specified elements. |
| `strip_whitespace` | `bool` | `True` | Strip whitespace from text nodes. |
| `disable_entities` | `bool` | `True` | Block entity declarations for XXE security. |
| `postprocessor` | `Callable \| None` | `None` | `(path, key, value) -> (key, value)` or `None` to skip. |

**Returns:** `dict | None` -- Parsed dict, or `None` for empty documents.

**Raises:** `XMLError` if the XML is malformed.

**Example:**

```python
d = parse('<root><name>Alice</name><age>30</age></root>')
# {'root': {'name': 'Alice', 'age': '30'}}
```

---

### `unparse(input_dict, **kwargs)`

Convert a Python dict into an XML string. Compatible with `xmltodict.unparse()`.

```python
def unparse(
    input_dict: dict,
    *,
    output: IO[str] | None = None,
    encoding: str = "utf-8",
    full_document: bool = True,
    short_empty_elements: bool = False,
    pretty: bool = False,
    indent: str = "\t",
    newl: str = "\n",
    attr_prefix: str = "@",
    cdata_key: str = "#text",
    preprocessor: Callable | None = None,
    namespace_separator: str = ":",
    namespaces: dict[str, str] | None = None,
    comment_key: str = "#comment",
) -> str | None
```

**Key Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `input_dict` | `dict` | *(required)* | Dictionary with a single root key. |
| `output` | `IO[str] \| None` | `None` | If provided, write to stream and return `None`. |
| `full_document` | `bool` | `True` | Include `<?xml ...?>` declaration. |
| `pretty` | `bool` | `False` | Pretty-print with indentation. |
| `indent` | `str` | `"\t"` | Indentation string (used when `pretty` is True). |

**Returns:** `str` if `output` is `None`, otherwise `None`.

**Raises:** `XMLError` if the dict cannot be serialized.

**Example:**

```python
xml_str = unparse({'root': {'name': 'Alice'}}, full_document=False)
# '<root><name>Alice</name></root>'
```

---

### `extract_tags(text, tag, *, first_only)`

Extract XML-like tags from text, tolerating malformed XML. Designed for LLM output.

```python
def extract_tags(
    text: str,
    tag: str | None = None,
    *,
    first_only: bool = False,
) -> list[ExtractedTag]
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `text` | `str` | *(required)* | Raw text containing XML-like tags. |
| `tag` | `str \| None` | `None` | Extract only tags with this name, or all if `None`. |
| `first_only` | `bool` | `False` | Return after finding the first match. |

**Returns:** `list[ExtractedTag]`

**Example:**

```python
tags = extract_tags('<answer>42</answer>', 'answer')
# [ExtractedTag(tag='answer', content='42', attrs={}, is_closed=True)]
```

---

### `class ExtractedTag`

Dataclass representing an extracted tag.

| Field | Type | Description |
|-------|------|-------------|
| `tag` | `str` | Tag name (e.g. `"answer"`). |
| `content` | `str` | Text content between open and close tags. |
| `attrs` | `dict[str, str]` | Attributes on the opening tag. |
| `is_closed` | `bool` | `True` if a matching close tag was found. |

---

### `class XMLError(Exception)`

Raised when XML parsing or serialization fails.

---

### Aliases

| Alias | Target | Convention |
|-------|--------|------------|
| `loads` | `parse` | zerodep convention |
| `dumps` | `unparse` | zerodep convention |

## Usage Examples

### Parse a Sitemap

```python
from xml import parse

sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/</loc>
    <lastmod>2024-01-01</lastmod>
  </url>
  <url>
    <loc>https://example.com/about</loc>
    <lastmod>2024-01-02</lastmod>
  </url>
</urlset>"""

d = parse(sitemap_xml)
for url in d["urlset"]["url"]:
    print(url["loc"], url["lastmod"])
```

### Parse an RSS Feed

```python
from xml import parse

rss_xml = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>My Blog</title>
    <item>
      <title>First Post</title>
      <link>https://example.com/first</link>
    </item>
    <item>
      <title>Second Post</title>
      <link>https://example.com/second</link>
    </item>
  </channel>
</rss>"""

d = parse(rss_xml)
for item in d["rss"]["channel"]["item"]:
    print(item["title"], item["link"])
```

### Round-Trip Conversion

```python
from xml import parse, unparse

original = {'catalog': {'book': [
    {'@id': '1', 'title': 'Python', 'price': '29.99'},
    {'@id': '2', 'title': 'Rust', 'price': '39.99'},
]}}

xml_str = unparse(original, pretty=True, full_document=False)
print(xml_str)

restored = parse(xml_str)
assert restored == original
```

### Extract LLM Output Tags

```python
from xml import extract_tags

llm_output = """Let me think about this.

<thinking>
The user wants to know the capital of France.
This is a straightforward factual question.
</thinking>

<answer>
The capital of France is Paris.
</answer>"""

thinking = extract_tags(llm_output, "thinking")
answer = extract_tags(llm_output, "answer")
print(thinking[0].content.strip())
print(answer[0].content.strip())
```

### Handle Streaming Truncation

```python
from xml import extract_tags

# LLM output was cut off mid-stream
partial_output = "<response>The answer is 42 and the reason is"

tags = extract_tags(partial_output, "response")
print(tags[0].content)    # "The answer is 42 and the reason is"
print(tags[0].is_closed)  # False — tag was not closed
```

### Force List for Single Elements

```python
from xml import parse

# Without force_list, a single <item> is a scalar
d = parse('<root><item>only one</item></root>')
print(type(d['root']['item']))  # str

# With force_list, it's always a list
d = parse('<root><item>only one</item></root>', force_list=('item',))
print(type(d['root']['item']))  # list
```

## Conventions

### Attribute Handling

XML attributes are prefixed with `@` (configurable via `attr_prefix`):

```python
parse('<item id="1" type="book">hello</item>')
# {'item': {'@id': '1', '@type': 'book', '#text': 'hello'}}
```

### Text Content

Text content is stored under `#text` (configurable via `cdata_key`):

```python
parse('<tag attr="val">content</tag>')
# {'tag': {'@attr': 'val', '#text': 'content'}}
```

### List Coalescing

Same-name siblings automatically become lists:

```python
parse('<root><item>a</item><item>b</item></root>')
# {'root': {'item': ['a', 'b']}}
```

### Empty Elements

Empty elements produce `None`:

```python
parse('<root><empty/></root>')
# {'root': {'empty': None}}
```

## Notes and Caveats

!!! warning "Security: Entity Expansion"
    By default, `disable_entities=True` blocks XML entity declarations to prevent XXE (XML External Entity) attacks. Only set `disable_entities=False` if you trust the XML source.

!!! info "Module Name Collision"
    The module is named `xml.py`, which collides with Python's stdlib `xml` package. The module handles this transparently during import. However, if your project also needs direct access to `xml.etree.ElementTree` or other stdlib `xml` sub-modules, you may need to rename the file.

- **Python version:** Requires Python 3.10+ (uses `X | Y` union type hint syntax).
- **Streaming:** `item_depth` / `item_callback` streaming mode is not yet supported but the SAX-based architecture allows adding it in the future.
- **Namespace processing:** Set `process_namespaces=True` to expand namespace URIs. By default, namespace prefixes are preserved as-is.

## Benchmark

Benchmarked against `xmltodict` across three input sizes (small, medium, large) for both parse and unparse operations, plus standalone `extract_tags` performance.

See [XML Benchmark](../benchmarks/xml.md) for detailed results.
