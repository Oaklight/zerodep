# Runner Benchmark

Apple-to-apple performance comparison between zerodep runner, [`sh`](https://pypi.org/project/sh/), and raw `subprocess`.

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** sh 2.2.2
    - **Last Updated:** 2026-04-21

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `runner.py` | stdlib-only structured subprocess execution |
| **sh** | *(reference)* | Popular subprocess wrapper with magic API |
| **subprocess** | *(stdlib)* | Python standard library `subprocess.run` / `Popen` |

## Tests Performed

| Test | Description |
|------|-------------|
| Simple Command | Run `echo hello` and capture output |
| Output Capture | Run Python one-liner printing 10 lines, capture all output |
| Stdin Input | Pipe `"hello world"` to Python `sys.stdin.read().upper()` |
| Streaming Lines | Iterate 20 printed lines via streaming interface |
| Env Passing | Pass `BENCH_VAR` environment variable and read it back |

## Performance Comparison (Mean)

| Test | subprocess | zerodep | sh | zerodep vs subprocess | zerodep vs sh |
|------|-----------|---------|----|-----------------------|---------------|
| Simple Command | -- | 2.00 ms | 8.87 ms | -- | **4.4x faster** |
| Output Capture | -- | 11.05 ms | 18.98 ms | -- | **1.7x faster** |
| Stdin Input | -- | 10.98 ms | 19.27 ms | -- | **1.8x faster** |
| Streaming Lines | -- | 11.06 ms | 19.44 ms | -- | **1.8x faster** |
| Env Passing | -- | 11.32 ms | 19.48 ms | -- | **1.7x faster** |

## Key Takeaways

- **Consistently faster than sh** -- zerodep runner is 1.7-4.4x faster than `sh` across all scenarios. The `sh` library's magic API and dynamic attribute resolution add significant overhead.
- **Feature advantage is the real story** -- unlike raw subprocess, zerodep provides SIGTERM-to-SIGKILL timeout escalation, streaming callbacks with simultaneous capture, command allowlist/blocklist, and environment isolation -- all with comparable performance.

## Run It Yourself

```bash
pip install pytest pytest-benchmark sh
pytest runner/test_runner_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/runner.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
