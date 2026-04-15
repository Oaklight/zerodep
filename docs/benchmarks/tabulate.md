# Tabulate Benchmark

Apple-to-apple performance comparison between zerodep tabulate and [`tabulate`](https://pypi.org/project/tabulate/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** tabulate 0.10.0
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `tabulate.py` | Single-file table formatter, stdlib only |
| **tabulate** | *(reference)* | Popular table formatting library |

## Data Sizes Tested

| Label | Description |
|-------|-------------|
| Small | Simple 3-column, 3-row table |
| Medium | 10-column, 20-row table with mixed types |
| Large | 15-column, 100-row table with numbers and strings |

## Format Performance (Mean)

| Data Size | zerodep | tabulate | Speedup |
|-----------|---------|----------|---------|
| Small | 45.1 us | 144.2 us | 3.2x faster |
| Medium | 335.1 us | 1,428.8 us | 4.3x faster |
| Large | 5,405.9 us | 21,904.8 us | 4.1x faster |

## Key Takeaways

- **3.2-4.3x faster formatting** -- single-file implementation avoids the overhead of the reference library's multi-module dispatch and feature negotiation.
- **Speed advantage grows with data size** -- zerodep's streamlined column-width calculation and row rendering scale more efficiently, reaching 4.3x on medium tables.
- **Zero pip dependencies** -- zerodep uses only `re`, `math`, `unicodedata`, and `dataclasses` from the standard library.

## Run It Yourself

```bash
pip install pytest pytest-benchmark tabulate
pytest tabulate/test_tabulate_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/tabulate.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
