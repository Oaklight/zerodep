# Runner Benchmark

Apple-to-apple performance comparison between zerodep runner, [`sh`](https://pypi.org/project/sh/), and raw `subprocess`.

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

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
| Simple Command | 0.76 ms | 1.89 ms | 5.9 ms | 2.5x slower | **3.1x faster** |
| Output Capture | 17.7 ms | 15.9 ms | 21.4 ms | **1.1x faster** | **1.3x faster** |
| Stdin Input | 17.3 ms | 17.6 ms | 21.4 ms | ~same | **1.2x faster** |
| Streaming Lines | 15.8 ms | 17.7 ms | 23.5 ms | 1.1x slower | **1.3x faster** |
| Env Passing | 18.6 ms | 13.5 ms | 25.4 ms | **1.4x faster** | **1.9x faster** |

## Key Takeaways

- **Consistently faster than sh** -- zerodep runner is 1.2-3.1x faster than `sh` across all scenarios. The `sh` library's magic API and dynamic attribute resolution add measurable overhead.
- **Near-parity with raw subprocess** -- for real workloads (output capture, stdin, env passing), zerodep runner matches or beats raw `subprocess.run`, despite providing structured results, timeout escalation, and streaming callbacks.
- **Simple command overhead** -- the 2.5x gap on `echo hello` reflects zerodep's `Popen`-based architecture (needed for timeout escalation and streaming) vs `subprocess.run`'s optimized fast path. This fixed overhead (~1 ms) is negligible for any command that does real work.
- **Environment passing is 1.4x faster** -- zerodep's `env_extra` avoids the `{**os.environ, ...}` dict copy that both `sh` and raw subprocess require.
- **Feature advantage is the real story** -- unlike raw subprocess, zerodep provides SIGTERM-to-SIGKILL timeout escalation, streaming callbacks with simultaneous capture, command allowlist/blocklist, and environment isolation -- all with comparable performance.

## Run It Yourself

```bash
pip install pytest pytest-benchmark sh
pytest runner/test_runner_benchmark.py --benchmark-only -v
```
