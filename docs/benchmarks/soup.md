# Soup Benchmark

Apple-to-apple performance comparison between zerodep soup and [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** beautifulsoup4 4.14.3
    - **Last Updated:** 2026-04-21

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
| Small | 276.5 us | 740.3 us | 2.7x faster |
| Medium | 2,190.0 us | 6,140.0 us | 2.8x faster |
| Large | 24,580.0 us | 63,020.0 us | 2.6x faster |

## Serialization Performance (Mean)

| Data Size | zerodep | beautifulsoup4 | Speedup |
|-----------|---------|----------------|---------|
| Small | 307.3 us | 986.4 us | 3.2x faster |
| Medium | 2,230.0 us | 8,310.0 us | 3.7x faster |
| Large | 25,290.0 us | 83,800.0 us | 3.3x faster |

## Tree Operations Performance (Mean)

| Data Size | zerodep | beautifulsoup4 | Speedup |
|-----------|---------|----------------|---------|
| Small | 333.9 us | 888.8 us | 2.7x faster |
| Medium | 2,370.0 us | 6,810.0 us | 2.9x faster |
| Large | 26,780.0 us | 67,650.0 us | 2.5x faster |

## Key Takeaways

- **2.5-3.7x faster across all sizes and operations** -- zerodep builds a minimal DOM tree directly from `html.parser` without the abstraction layers (NavigableString, PageElement hierarchy, soupsieve integration) that BeautifulSoup carries.
- **Serialization shows the largest speedup** -- 3.2-3.7x faster, as zerodep's lightweight node structure has less overhead during tree-to-string conversion.
- **Consistent advantage across workloads** -- parsing (2.7-2.8x), serialization (3.2-3.7x), and tree operations (2.5-2.9x) all show strong gains, with only a slight narrowing on the largest documents.
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
