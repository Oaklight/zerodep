# Structured Logging Benchmark

Apple-to-apple performance comparison between zerodep structured logging and [`structlog`](https://pypi.org/project/structlog/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** structlog 25.5.0
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `structlog.py` | stdlib-only structured logger |
| **structlog** | *(reference)* | Popular structured logging library |

## Performance Comparison (Mean)

| Test | zerodep | structlog | Speedup |
|------|---------|-----------|---------|
| Simple log | 8.8 us | 10.9 us | 1.2x faster |
| Bound log | 10.2 us | 15.4 us | 1.5x faster |
| JSON rendering | 8.3 us | 9.9 us | 1.2x faster |
| Bind + log | 10.0 us | 17.0 us | 1.7x faster |

## Key Takeaways

- **1.2-1.7x faster** -- zerodep outperforms structlog across all scenarios, with the advantage growing as operations involve context binding.
- **Simple logging and JSON rendering are near-parity** -- for basic log calls and JSON output, both libraries perform similarly (~8-11 us), with zerodep about 1.2x ahead.
- **Biggest wins on context operations** -- bound logging (1.5x) and bind + log (1.7x) show the largest speedups, where structlog's processor chain and wrapper overhead become more visible.
- **Zero pip dependencies** -- zerodep uses only `json`, `logging`, `io`, and `time` from the standard library.

## Run It Yourself

```bash
pip install pytest pytest-benchmark structlog
pytest structlog/test_structlog_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/structlog.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
