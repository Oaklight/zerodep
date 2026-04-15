# Scheduler Benchmark

Apple-to-apple performance comparison between zerodep scheduler and [`APScheduler`](https://pypi.org/project/APScheduler/), [`croniter`](https://pypi.org/project/croniter/), and [`schedule`](https://pypi.org/project/schedule/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **Tool:** pytest-benchmark (mean values reported)

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
| Cron parsing (5 expressions) | ~20 us | ~236 us | ~74 us | N/A | 3.6x--11.5x faster |
| Next fire time (5 expressions) | ~28 us | ~436 us | ~127 us | N/A | 4.5x--15.3x faster |
| Batch next fire time (100 iterations) | ~310 us | ~2,523 us | ~575 us | N/A | 1.9x--8.1x faster |
| Job add overhead (100 jobs) | ~377 us | N/A | N/A | ~349 us | ~1.1x |

## Key Takeaways

- **Cron parsing** is 3.6x faster than APScheduler and 11.5x faster than croniter, thanks to a minimal set-based parser.
- **Next fire time calculation** is 4.5x--15x faster, as zerodep uses direct datetime arithmetic without timezone overhead.
- **Batch computation** (100 consecutive fire times) maintains the speed advantage at scale.
- **Job add overhead** is comparable to `schedule`, which has a similarly lightweight design.
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
