# Structured Logging Benchmark

Apple-to-apple performance comparison between zerodep structured logging and [`structlog`](https://pypi.org/project/structlog/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** structlog 25.5.0
    - **Last Updated:** 2026-04-21

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `structlog.py` | stdlib-only structured logger |
| **structlog** | *(reference)* | Popular structured logging library |

## Performance Comparison (Mean)

| Test | zerodep | structlog | Speedup |
|------|---------|-----------|---------|
| Simple log | 10.2 us | 14.0 us | 1.4x faster |
| Bound log | 12.7 us | 19.9 us | 1.6x faster |
| JSON rendering | 10.0 us | 12.4 us | 1.2x faster |
| Bind + log | 11.5 us | 23.0 us | 2.0x faster |

## Key Takeaways

- **1.2-2.0x faster** -- zerodep outperforms structlog across all scenarios, with the advantage growing as operations involve context binding.
- **Simple logging and JSON rendering are near-parity** -- for basic log calls and JSON output, both libraries perform similarly (~10-14 us), with zerodep about 1.2-1.4x ahead.
- **Biggest wins on context operations** -- bound logging (1.6x) and bind + log (2.0x) show the largest speedups, where structlog's processor chain and wrapper overhead become more visible.
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
