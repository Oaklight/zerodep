# JSON Schema Benchmark

Performance comparison between zerodep jsonschema and [`allof-merge`](https://www.npmjs.com/package/allof-merge) (JavaScript).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Node.js:** 22 (for allof-merge)
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** allof-merge 0.6.8 (via persistent Node.js process)
    - **Last Updated:** 2026-04-25

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `jsonschema.py` | stdlib-only JSON Schema flattener (full pipeline) |
| **allof-merge** | *(reference)* | JavaScript library for `$ref` + `allOf` resolution |

## Test Schemas

Benchmarks use five complexity tiers from trivial to synthetic large-scale:

| Tier | Description |
|------|-------------|
| Tiny | Simple object, no composition keywords (passthrough baseline) |
| Small | Single `anyOf` nullable pattern |
| Medium | `$ref` + `allOf` + `anyOf` combined |
| Large | Multiple `$ref` + nested `allOf` + `oneOf` |
| XLarge | Synthetic: 50 fields, 10 `$defs`, mixed `allOf`/`anyOf`/`oneOf` |

## Performance Comparison

| Tier | zerodep | allof-merge (JS) | Ratio |
|------|---------|-------------------|-------|
| Tiny | 19.8 us | 104 us | **5.3x faster** |
| Small | 35.7 us | 143 us | **4.0x faster** |
| Medium | 103.8 us | 236 us | **2.3x faster** |
| Large | 292.5 us | 486 us | **1.7x faster** |
| XLarge | 1.96 ms | 4.92 ms | **2.5x faster** |

!!! note "Fair Comparison"
    The JS benchmark uses a persistent Node.js process (like readability) to eliminate subprocess startup overhead. Only the actual `merge()` call time is measured. zerodep runs the full 4-phase pipeline (`flatten_schema`) while allof-merge only performs `$ref` + `allOf` resolution.

## Correctness Verification

In addition to 57 standalone unit tests, 13 cross-implementation correctness tests verify structural equivalence between zerodep (Phase 1+2 only) and allof-merge:

- **Structural match** across all 5 tiers
- **allOf fully resolved** (no residual `allOf` keywords)
- **`$ref` fully resolved** by zerodep in all contexts

## Key Takeaways

- **zerodep is 1.7-5.3x faster** than allof-merge across all complexity tiers, even though zerodep runs a fuller pipeline
- **zerodep does more** -- it also simplifies `anyOf`/`oneOf` and strips unsupported keys, which allof-merge does not
- **Zero dependencies** -- zerodep needs only the stdlib, while allof-merge requires Node.js + npm
- **Correct** -- output is structurally equivalent to allof-merge for the shared `$ref` + `allOf` scope

## Run It Yourself

```bash
# Install JS dependencies
cd jsonschema && npm install

# Run benchmarks
pip install pytest pytest-benchmark
pytest jsonschema/test_jsonschema_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/jsonschema.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
