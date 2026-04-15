# Runner Benchmark

Apple-to-apple performance comparison between zerodep runner, [`sh`](https://pypi.org/project/sh/), and raw `subprocess`.

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** sh 2.2.2
    - **Last Updated:** 2026-04-15

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
| Simple Command | 0.99 ms | 1.61 ms | 27.9 ms | 1.6x slower | **17.3x faster** |
| Output Capture | 18.9 ms | 19.2 ms | 50.6 ms | ~same | **2.6x faster** |
| Stdin Input | 18.1 ms | 18.7 ms | 37.7 ms | ~same | **2.0x faster** |
| Streaming Lines | 18.5 ms | 18.5 ms | 35.9 ms | ~same | **1.9x faster** |
| Env Passing | 18.5 ms | 18.7 ms | 39.7 ms | ~same | **2.1x faster** |

## Key Takeaways

- **Consistently faster than sh** -- zerodep runner is 1.9-17.3x faster than `sh` across all scenarios. The `sh` library's magic API and dynamic attribute resolution add significant overhead.
- **Near-parity with raw subprocess** -- for real workloads (output capture, stdin, streaming, env passing), zerodep runner matches raw `subprocess.run` within noise margin, despite providing structured results, timeout escalation, and streaming callbacks.
- **Simple command overhead** -- the 1.6x gap on `echo hello` reflects zerodep's `Popen`-based architecture (needed for timeout escalation and streaming) vs `subprocess.run`'s optimized fast path. This fixed overhead (~0.6 ms) is negligible for any command that does real work.
- **Feature advantage is the real story** -- unlike raw subprocess, zerodep provides SIGTERM-to-SIGKILL timeout escalation, streaming callbacks with simultaneous capture, command allowlist/blocklist, and environment isolation -- all with comparable performance.

## Run It Yourself

```bash
pip install pytest pytest-benchmark sh
pytest runner/test_runner_benchmark.py --benchmark-only -v
```
