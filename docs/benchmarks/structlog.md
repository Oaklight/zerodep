# Structured Logging Benchmark

Apple-to-apple performance comparison between zerodep structured logging and [`structlog`](https://pypi.org/project/structlog/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `structlog.py` | stdlib-only structured logger |
| **structlog** | *(reference)* | Popular structured logging library |

## Performance Comparison (Mean)

| Test | zerodep | structlog | Speedup |
|------|---------|-----------|---------|
| Simple log | 5.0 us | 5.7 us | 1.1x faster |
| Bound log | 5.0 us | 7.3 us | 1.5x faster |
| JSON rendering | 5.5 us | 10.9 us | 2.0x faster |
| Bind + log | 5.7 us | 12.9 us | 2.3x faster |

## Key Takeaways

- **1.1-2.3x faster** -- zerodep outperforms structlog across all scenarios, with the advantage growing as operations become more complex.
- **Simple logging is near-parity** -- for basic log calls, both libraries are fast (~5 us), with zerodep only marginally ahead.
- **Biggest wins on complex operations** -- JSON rendering (2.0x) and context propagation with bind + log (2.3x) show the largest speedups, where structlog's processor chain and wrapper overhead become more visible.
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
