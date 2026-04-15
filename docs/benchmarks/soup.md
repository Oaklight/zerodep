# Soup Benchmark

Apple-to-apple performance comparison between zerodep soup and [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

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
| Small | 149.2 us | 446.2 us | 2.99x faster |
| Medium | 1,236.6 us | 3,683.9 us | 2.98x faster |
| Large | 12,662.5 us | 37,061.8 us | 2.93x faster |

## Key Takeaways

- **~3x faster across all sizes** -- zerodep builds a minimal DOM tree directly from `html.parser` without the abstraction layers (NavigableString, PageElement hierarchy, soupsieve integration) that BeautifulSoup carries.
- **Consistent speedup** -- the 2.9-3.0x advantage holds regardless of document complexity, indicating the overhead is per-element rather than per-document.
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
