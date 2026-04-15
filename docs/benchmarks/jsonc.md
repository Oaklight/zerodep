# JSONC Benchmark

Apple-to-apple performance comparison between zerodep JSONC and [`commentjson`](https://pypi.org/project/commentjson/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** commentjson 0.9.0
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `jsonc.py` | Regex-based comment stripping + stdlib `json.loads` |
| **commentjson** | *(reference)* | Lark LALR parser + AST reconstruction + stdlib `json.loads` |

## Data Sizes Tested

| Label | Description |
|-------|-------------|
| Small | 5-key object with `//` comments |
| Medium | Nested config (~40 lines) with `//`, `#` comments and trailing commas |
| Large | 100-item object with inline `//` comments and trailing commas |

## Performance Comparison (Mean)

| Data Size | zerodep | commentjson | Speedup |
|-----------|---------|-------------|---------|
| Small | 14.6 us | 1,150.8 us | 79x faster |
| Medium | 91.5 us | 8,466.3 us | 93x faster |
| Large | 1,809.7 us | 218,981.4 us | 121x faster |

## Key Takeaways

- **79--121x faster** -- zerodep is dramatically faster across all data sizes, with the advantage increasing as input grows.
- **Regex vs. LALR** -- the performance gap comes from the approach: zerodep strips comments via lightweight regex then delegates to C-accelerated `json.loads`, while commentjson builds a full parse tree using a Lark LALR parser before reconstructing the data.
- **Scales better** -- the speedup ratio improves from 79x to 121x as data size increases, showing that the regex approach has much lower per-element overhead.
- **Zero pip dependencies** -- zerodep uses only `re` and `json` from the standard library.

## Run It Yourself

```bash
pip install pytest pytest-benchmark commentjson
pytest jsonc/test_jsonc_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/jsonc.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
