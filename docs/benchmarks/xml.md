# XML Benchmark

Apple-to-apple performance comparison between zerodep XML and [`xmltodict`](https://pypi.org/project/xmltodict/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `xml.py` | stdlib-only XML ↔ dict converter with LLM tag extraction |
| **xmltodict** | *(reference)* | Popular XML ↔ dict converter using expat |

## Data Sizes Tested

| Label | Description |
|-------|-------------|
| Small | Simple element with 3 children |
| Medium | Sitemap XML with 25 URL entries |
| Large | Product catalog with 200 items, attributes, and nested tags |

## Parse Performance (Mean)

| Data Size | zerodep | xmltodict | Speedup |
|-----------|---------|-----------|---------|
| Small | 8.0 μs | 9.9 μs | 1.2x faster |
| Medium | 176.4 μs | 240.1 μs | 1.4x faster |
| Large | 2,587.8 μs | 3,172.2 μs | 1.2x faster |

## Unparse Performance (Mean)

| Data Size | zerodep | xmltodict | Speedup |
|-----------|---------|-----------|---------|
| Small | 9.2 μs | 13.0 μs | 1.4x faster |
| Medium | 221.4 μs | 289.1 μs | 1.3x faster |
| Large | 2,955.7 μs | 4,094.9 μs | 1.4x faster |

## extract_tags Performance (Mean)

| Operation | Time |
|-----------|------|
| Extract all tags (100 tags) | 315.3 μs |
| Extract filtered (50 matches) | 198.6 μs |
| Extract first only | 4.5 μs |

## Key Takeaways

- **Parse is ~1.2-1.4x faster** -- zerodep consistently outperforms xmltodict across all data sizes.
- **Unparse is ~1.3-1.4x faster** -- serialization performance gap is even more consistent.
- **extract_tags has no competitor** -- this is a unique feature for LLM output parsing. The `first_only=True` optimization is extremely fast (~4.5 μs).
- **Both use expat** -- unlike YAML/JSON where zerodep reimplements the parser, both zerodep and xmltodict use the same C-based expat parser underneath, so the speedup comes from more efficient dict construction.

## Run It Yourself

```bash
pip install pytest pytest-benchmark xmltodict
pytest xml/test_xml_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/xml.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
