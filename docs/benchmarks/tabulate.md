# Tabulate Benchmark

Apple-to-apple performance comparison between zerodep tabulate and [`tabulate`](https://pypi.org/project/tabulate/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

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
| Small | 32.5 us | 93.8 us | 2.89x faster |
| Medium | 266.4 us | 910.1 us | 3.42x faster |
| Large | 3,883.4 us | 13,804.4 us | 3.56x faster |

## Key Takeaways

- **2.9-3.6x faster formatting** -- single-file implementation avoids the overhead of the reference library's multi-module dispatch and feature negotiation.
- **Speed advantage grows with data size** -- zerodep's streamlined column-width calculation and row rendering scale more efficiently.
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
