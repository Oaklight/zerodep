# Soup Benchmark

Apple-to-apple performance comparison between zerodep soup and [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** beautifulsoup4 4.14.3
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `soup.py` | Single-file HTML parser, stdlib only |
| **beautifulsoup4** | *(reference)* | Popular HTML/XML parser with `html.parser` backend |

## Data Sizes Tested

| Label | Description |
|-------|-------------|
| Small | Simple HTML page with a few elements (~200 chars) |
| Medium | Structured page with navigation, lists, and nested divs (~2 KB) |
| Large | Complex page with tables, forms, scripts, and deep nesting (~10 KB) |

## Parse + Query Performance (Mean)

| Data Size | zerodep | beautifulsoup4 | Speedup |
|-----------|---------|----------------|---------|
| Small | 207.6 us | 651.0 us | 3.1x faster |
| Medium | 1,796.2 us | 5,482.2 us | 3.1x faster |
| Large | 22,110.0 us | 48,220.6 us | 2.2x faster |

## Key Takeaways

- **2.2-3.1x faster across all sizes** -- zerodep builds a minimal DOM tree directly from `html.parser` without the abstraction layers (NavigableString, PageElement hierarchy, soupsieve integration) that BeautifulSoup carries.
- **Largest speedup on small/medium documents** -- the 3.1x advantage on small and medium inputs narrows to 2.2x on large documents, suggesting the per-element overhead advantage is partially offset by increased tree-management work in complex pages.
- **Zero pip dependencies** -- zerodep uses only `re` and `html.parser` from the standard library. BeautifulSoup requires `soupsieve` and optionally `lxml` or `html5lib`.

## Run It Yourself

```bash
pip install pytest pytest-benchmark beautifulsoup4
pytest soup/test_soup_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/soup.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
