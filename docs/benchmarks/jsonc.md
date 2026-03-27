# JSONC Benchmark

Apple-to-apple performance comparison between zerodep JSONC and [`commentjson`](https://pypi.org/project/commentjson/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

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
| Small | 8.7 us | 781.6 us | 90x faster |
| Medium | 52.3 us | 5,859.0 us | 112x faster |
| Large | 1,068.7 us | 128,453.0 us | 120x faster |

## Key Takeaways

- **90-120x faster** -- zerodep is dramatically faster across all data sizes, with the advantage increasing as input grows.
- **Regex vs. LALR** -- the performance gap comes from the approach: zerodep strips comments via lightweight regex then delegates to C-accelerated `json.loads`, while commentjson builds a full parse tree using a Lark LALR parser before reconstructing the data.
- **Scales better** -- the speedup ratio improves from 90x to 120x as data size increases, showing that the regex approach has much lower per-element overhead.
- **Zero pip dependencies** -- zerodep uses only `re` and `json` from the standard library.

## Run It Yourself

```bash
pip install pytest pytest-benchmark commentjson
pytest jsonc/test_jsonc_benchmark.py --benchmark-only -v
```
