# XML Benchmark

Apple-to-apple performance comparison between zerodep XML and [`xmltodict`](https://pypi.org/project/xmltodict/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** xmltodict 1.0.4
    - **Last Updated:** 2026-04-21

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
| Small | 14.9 μs | 17.4 μs | **1.2x faster** |
| Medium | 380.7 μs | 442.6 μs | **1.2x faster** |
| Large | 5,210.0 μs | 5,750.0 μs | **1.1x faster** |

## Unparse Performance (Mean)

| Data Size | zerodep | xmltodict | Speedup |
|-----------|---------|-----------|---------|
| Small | 14.6 μs | 19.9 μs | **1.4x faster** |
| Medium | 278.1 μs | 455.1 μs | **1.6x faster** |
| Large | 4,030.0 μs | 6,480.0 μs | **1.6x faster** |

## extract_tags Performance (Mean)

| Operation | Time |
|-----------|------|
| Extract all tags (100 tags) | 569.2 μs |
| Extract filtered (50 matches) | 346.5 μs |
| Extract first only | 7.7 μs |

## Key Takeaways

- **Parse is 1.1-1.2x faster** -- zerodep now edges ahead of xmltodict across all document sizes, including small inputs.
- **Unparse is 1.4-1.6x faster** -- serialization is where zerodep shows a clear advantage, with the gap widening on larger documents.
- **extract_tags has no competitor** -- this is a unique feature for LLM output parsing. The `first_only=True` optimization is extremely fast (~7.7 μs).
- **Both use expat** -- unlike YAML/JSON where zerodep reimplements the parser, both zerodep and xmltodict use the same C-based expat parser underneath, so unparse speedup comes from more efficient string construction.

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
