# TOON Benchmark

Apple-to-apple performance comparison between zerodep TOON and [`toon_format`](https://github.com/toon-format/toon-python).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **Tool:** pytest-benchmark (mean values reported)
    - **Reference:** toon-format @91413d14 (spec 4.4)
    - **Last Updated:** 2026-10-22

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `toon.py` | Single-file encoder/decoder, stdlib only |
| **toon_format** | *(reference)* | 7-file package, no core dependencies |

## Data Sizes Tested

| Label | Description |
|-------|-------------|
| Small | Simple 3-field object (`{id, name, active}`) |
| Medium | Nested object with 20-row tabular array + nested config |
| Large | 5 departments x 4 teams x 5 members (deep nesting, ~100 objects) |

## Encode Performance (Mean)

| Data Size | zerodep | toon_format | Speedup |
|-----------|---------|-------------|---------|
| Small | 6.5 us | 6.6 us | 1.0x |
| Medium | 127.1 us | 126.7 us | 1.0x |
| Large | 869.8 us | 1,093.3 us | 1.3x faster |

## Decode Performance (Mean)

| Data Size | zerodep | toon_format | Speedup |
|-----------|---------|-------------|---------|
| Small | 12.6 us | 9.7 us | 0.8x |
| Medium | 114.5 us | 118.3 us | 1.0x |
| Large | 810.8 us | 787.6 us | 1.0x |

## Token Efficiency (TOON vs JSON)

| Data Size | JSON (chars) | TOON (chars) | Savings |
|-----------|-------------|-------------|---------|
| Small | 52 | 32 | 38.5% |
| Medium | 2,171 | 638 | 70.6% |
| Large | 16,829 | 4,882 | 71.0% |

## Key Takeaways

- **Encode at parity to ~1.3x faster** -- the port follows the reference algorithms; the large-document difference comes from the single-file layout, not a different format.
- **Decode at parity** -- small documents are slightly slower, medium and large documents are within noise.
- **38-71% fewer characters than JSON** -- TOON's tabular array format and bare-key syntax achieve dramatic size reduction on structured data. Savings increase with tabular data density.
- **Zero pip dependencies** -- the module uses only the Python standard library.

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
