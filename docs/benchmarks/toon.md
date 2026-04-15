# TOON Benchmark

Apple-to-apple performance comparison between zerodep TOON and [`toon_format`](https://github.com/toon-format/toon-python).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** toon_format 0.9.0b1
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `toon.py` | Single-file encoder/decoder, stdlib only |
| **toon_format** | *(reference)* | 18-file package with typing-extensions dependency |

## Data Sizes Tested

| Label | Description |
|-------|-------------|
| Small | Simple 3-field object (`{id, name, active}`) |
| Medium | Nested object with 20-row tabular array + nested config |
| Large | 5 departments x 4 teams x 5 members (deep nesting, ~100 objects) |

## Encode Performance (Mean)

| Data Size | zerodep | toon_format | Speedup |
|-----------|---------|-------------|---------|
| Small | 7.0 us | 9.9 us | 1.4x faster |
| Medium | 168.8 us | 205.7 us | 1.2x faster |
| Large | 995.4 us | 1,238.4 us | 1.2x faster |

## Decode Performance (Mean)

| Data Size | zerodep | toon_format | Speedup |
|-----------|---------|-------------|---------|
| Small | 16.3 us | 18.9 us | 1.2x faster |
| Medium | 259.1 us | 277.3 us | 1.1x faster |
| Large | 1,770.2 us | 1,873.0 us | 1.1x faster |

## Token Efficiency (TOON vs JSON)

| Data Size | JSON (chars) | TOON (chars) | Savings |
|-----------|-------------|-------------|---------|
| Small | 52 | 32 | 38.5% |
| Medium | 2,171 | 638 | 70.6% |
| Large | 16,829 | 4,882 | 71.0% |

## Key Takeaways

- **1.2-1.4x faster encode** -- consolidating 18 source files into a single file reduces import and dispatch overhead.
- **1.1-1.2x faster decode** -- single-file layout eliminates cross-module function call overhead.
- **38-71% fewer characters than JSON** -- TOON's tabular array format and bare-key syntax achieve dramatic size reduction on structured data. Savings increase with tabular data density.
- **Zero pip dependencies** -- zerodep uses only `re`, `math`, `dataclasses`, and `collections.abc` from the standard library.

## Run It Yourself

```bash
pip install pytest pytest-benchmark
pip install git+https://github.com/toon-format/toon-python.git
pytest toon/test_toon_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/toon.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
