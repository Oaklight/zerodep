# Profiler Benchmark

Apple-to-apple performance comparison between zerodep profiler and [`pyinstrument`](https://pypi.org/project/pyinstrument/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** pyinstrument
    - **Last Updated:** 2026-09-28

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `profiler.py` | cProfile wrapper with HTML output |
| **pyinstrument** | *(reference)* | Statistical profiler with call stack recording |

## Tests Performed

| Test | Description |
|------|-------------|
| Profiler Overhead | Profile a CPU-bound workload, measure profiling overhead |
| Output Generation | Generate text + HTML reports from profiling data |
| TracingProfiler Overhead | Per-call tracing overhead on CPU-bound workload |
| Tracing Output Generation | Generate reports from tracing data |
| Multi-Thread Overhead | Profile multi-threaded workload |

## Run It Yourself

```bash
pip install pytest pytest-benchmark pyinstrument
pytest profiler/test_profiler_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/profiler.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
