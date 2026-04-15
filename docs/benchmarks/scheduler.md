# Scheduler Benchmark

Apple-to-apple performance comparison between zerodep scheduler and [`APScheduler`](https://pypi.org/project/APScheduler/), [`croniter`](https://pypi.org/project/croniter/), and [`schedule`](https://pypi.org/project/schedule/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** APScheduler 3.11.2, schedule 1.2.2, croniter 6.2.2
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `scheduler.py` | stdlib-only in-process scheduler |
| **APScheduler** | *(reference)* | Full-featured job scheduling library |
| **croniter** | *(reference)* | Cron expression parser and iterator |
| **schedule** | *(reference)* | Simple in-process scheduling |

## Performance Comparison (Mean)

| Test | zerodep | croniter | APScheduler | schedule | Speedup |
|------|---------|----------|-------------|----------|---------|
| Cron parsing (5 expressions) | 33.2 μs | 278.6 μs | 150.0 μs | N/A | 4.5x--8.4x faster |
| Next fire time (5 expressions) | 40.9 μs | 593.3 μs | 121.2 μs | N/A | 3.0x--14.5x faster |
| Batch next fire time (100 iterations) | 541.5 μs | 3,492.0 μs | 809.6 μs | N/A | 1.5x--6.4x faster |
| Job add overhead (100 jobs) | 447.6 μs | N/A | N/A | 523.9 μs | 1.2x faster |

## Key Takeaways

- **Cron parsing** is 4.5x faster than APScheduler and 8.4x faster than croniter, thanks to a minimal set-based parser.
- **Next fire time calculation** is 3.0x--14.5x faster, as zerodep uses direct datetime arithmetic without timezone overhead.
- **Batch computation** (100 consecutive fire times) maintains the speed advantage at scale (1.5x--6.4x faster).
- **Job add overhead** is comparable to `schedule` (1.2x faster), both adopting a lightweight design.
- zerodep has **zero pip dependencies** -- it uses only `threading`, `asyncio`, `datetime`, `inspect`, and `logging` from the standard library.

## Run It Yourself

```bash
pip install pytest pytest-benchmark APScheduler croniter schedule
pytest scheduler/test_scheduler_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/scheduler.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
