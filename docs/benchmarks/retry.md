# Retry Benchmark

Apple-to-apple performance comparison between zerodep retry and [`tenacity`](https://pypi.org/project/tenacity/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** tenacity 9.1.4
    - **Last Updated:** 2026-04-21

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `retry.py` | stdlib-only retry decorator |
| **tenacity** | *(reference)* | Popular retry library |

## Performance Comparison (Mean)

| Test | zerodep | tenacity | Speedup |
|------|---------|----------|---------|
| Decorator overhead | 0.5 μs | 19.8 μs | 37.3x faster |
| Retry with 2 failures | 246.9 μs | 322.1 μs | 1.3x faster |
| Backoff calculation | 5.6 μs | 14.6 μs | 2.6x faster |

## Key Takeaways

- **Decorator overhead** is ~37x lower than tenacity, making zerodep retry nearly free for hot-path decoration.
- **Retry execution** with actual failures is ~1.3x faster, as zerodep avoids the overhead of tenacity's statistics tracking and wait-chain abstraction.
- **Backoff calculation** is ~2.6x faster due to direct arithmetic vs. tenacity's composable wait object pipeline.
- zerodep has **zero pip dependencies** -- it uses only `time`, `functools`, `random`, `asyncio`, and `inspect` from the standard library.

## Run It Yourself

```bash
pip install pytest pytest-benchmark tenacity
pytest retry/test_retry_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/retry.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
