# llms.txt Parser

A zero-dependency parser for the [llms.txt specification](https://llmstxt.org/) — parse llms.txt files into structured data and discover per-page markdown URLs.

## Features

- **Spec-compliant parsing**: H1 title, blockquote description, detail paragraphs, H2 sections with link entries
- **Optional section handling**: `## Optional` entries separated automatically per spec semantics
- **Unified URL discovery**: `find_candidates()` searches parsed llms.txt entries with heuristic fallback
- **Lenient parsing**: only H1 title is required; everything else gracefully degrades
- **Immutable results**: frozen dataclasses for parse output
- **Zero dependencies**: stdlib only (`re`, `urllib.parse`, `dataclasses`)

## Quick Start

```python
from llmstxt import parse, find_candidates

# Parse an llms.txt file
doc = parse("""# My Project

> A brief description of the project.

Some extra detail here.

## Docs

- [Guide](https://example.com/guide.md): The main guide
- [API](https://example.com/api.md): API reference

## Optional

- [Advanced](https://example.com/advanced.md): Advanced topics
""")

print(doc.title)        # 'My Project'
print(doc.description)  # 'A brief description of the project.'
print(doc.details)      # 'Some extra detail here.'
print(doc.sections)     # {'Docs': [FileEntry(name='Guide', ...), ...]}
print(doc.optional)     # [FileEntry(name='Advanced', ...)]
```

## API

### `parse(text)`

Parse llms.txt content into a structured `LlmsTxt` object.

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | `str` | Raw text content of an llms.txt file |

**Returns:** `LlmsTxt` — parsed result.

**Raises:** `LlmsTxtError` — if the required H1 title is missing or input is empty.

### `find_candidates(url, doc=None)`

Find candidate markdown resources for a given URL.

When `doc` is provided, searches all sections and optional entries for URL matches (exact > extension variation > path prefix). If no match is found (or `doc` is `None`), falls back to heuristic URL generation.

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | The page URL to look up |
| `doc` | `LlmsTxt \| None` | Optional parsed llms.txt to search in |

**Returns:** `list[FileEntry]` — candidates ordered by match quality.

### `LlmsTxt`

Frozen dataclass representing a parsed llms.txt file.

| Field | Type | Description |
|-------|------|-------------|
| `title` | `str` | H1 heading (project/site name) |
| `description` | `str` | Blockquote summary, or `""` |
| `details` | `str` | Paragraphs between blockquote and first H2, or `""` |
| `sections` | `dict[str, list[FileEntry]]` | H2 section name → entries (excludes "Optional") |
| `optional` | `list[FileEntry]` | Entries from the `## Optional` section |

### `FileEntry`

Frozen dataclass representing a single link entry.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Display name of the link |
| `url` | `str` | URL of the linked resource |
| `notes` | `str` | Text after `: ` separator, or `""` |

### `LlmsTxtError`

Exception raised when parsing fails (missing H1 title or empty input).

## Usage Examples

### Search parsed llms.txt for a URL

```python
from llmstxt import parse, find_candidates

doc = parse(llms_txt_content)

# Exact and extension-based matching
results = find_candidates(
    "https://docs.example.com/guide.html", doc=doc
)
# Finds entries like guide.html.md, guide.md, etc.

# Prefix matching — find all entries under a path
results = find_candidates(
    "https://docs.example.com/tutorials", doc=doc
)
# Returns all entries whose URL starts with /tutorials/
```

### Heuristic fallback (no llms.txt available)

```python
from llmstxt import find_candidates

# No doc provided — generates candidate .md URLs by convention
results = find_candidates("https://example.com/docs/guide")
for entry in results:
    print(entry.url)
# https://example.com/docs/guide.md
# https://example.com/docs/guide/index.md
# https://example.com/docs/guide/index.html.md
```

### Typical discovery workflow

```python
import urllib.request
from llmstxt import parse, find_candidates, LlmsTxtError

page_url = "https://example.com/docs/guide"
site_root = "https://example.com"

# Try to fetch and parse site's llms.txt
try:
    llms_txt = urllib.request.urlopen(f"{site_root}/llms.txt").read().decode()
    doc = parse(llms_txt)
except (Exception, LlmsTxtError):
    doc = None

# Unified lookup — uses llms.txt if available, heuristic otherwise
candidates = find_candidates(page_url, doc=doc)
for entry in candidates:
    print(f"Try: {entry.url}")
```

## Matching Strategy

`find_candidates()` returns results ordered by match quality:

1. **Exact match** — entry URL equals input URL (after stripping query/fragment)
2. **Extension variation** — `guide.html` ↔ `guide.html.md`, `guide` ↔ `guide.md`
3. **Path prefix** — input path is a prefix of entry path or vice versa
4. **Heuristic fallback** — if no llms.txt matches, generates `{url}.md`, `{url}/index.md`, `{url}/index.html.md`

## Notes

- The parser is **lenient**: only the H1 title is required. Missing blockquote, details, or sections result in empty strings/lists.
- The `## Optional` section is treated specially per the spec — its entries go to `LlmsTxt.optional`, not `sections`.
- Case-sensitive: only exact `## Optional` (capital O) triggers special handling.
- Windows line endings (`\r\n`) are normalized automatically.
- `find_candidates()` strips query strings and fragments from URLs before matching.
