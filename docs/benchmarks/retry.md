# Retry Benchmark

Apple-to-apple performance comparison between zerodep retry and [`tenacity`](https://pypi.org/project/tenacity/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **Tool:** pytest-benchmark (mean values reported)

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `retry.py` | stdlib-only retry decorator |
| **tenacity** | *(reference)* | Popular retry library |

## Performance Comparison (Mean)

| Test | zerodep | tenacity | Speedup |
|------|---------|----------|---------|
| Decorator overhead | 377 ns | 8.4 us | ~22x faster |
| Retry with 2 failures | 2.5 us | 9.5 us | ~4x faster |
| Backoff calculation | 3.0 us | 30 us | ~10x faster |

## Key Takeaways

- **Decorator overhead** is ~22x lower than tenacity, making zerodep retry nearly free for hot-path decoration.
- **Retry execution** with actual failures is ~4x faster, as zerodep avoids the overhead of tenacity's statistics tracking and wait-chain abstraction.
- **Backoff calculation** is ~10x faster due to direct arithmetic vs. tenacity's composable wait object pipeline.
- zerodep has **zero pip dependencies** -- it uses only `time`, `functools`, `random`, `asyncio`, and `inspect` from the standard library.

## Run It Yourself

```bash
pip install pytest pytest-benchmark tenacity
pytest retry/test_retry_benchmark.py --benchmark-only -v
```
