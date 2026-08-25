# Rate Limiter Benchmark

Apple-to-apple performance comparison between zerodep ratelimit and [`limits`](https://pypi.org/project/limits/) / [`limiter`](https://pypi.org/project/limiter/) (token-bucket).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** limits 5.8.0, limiter 0.5.0 (token-bucket 0.3.0)
    - **Last Updated:** 2026-08-25

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `ratelimit.py` | 4-algorithm rate limiter, stdlib only |
| **limits** | *(reference)* | Multi-strategy rate limiter with pluggable backends |
| **limiter** | *(reference)* | Token bucket decorator, wraps C-level `token-bucket` |

## What Is Benchmarked

Single-key `acquire()` / `hit()` / `consume()` throughput — pure in-memory computation, no I/O. All limiters configured with rate=10000/s to avoid hitting the limit during the benchmark.

## Test Scenarios

| Scenario | Description |
|----------|-------------|
| Token Bucket acquire | zerodep `TokenBucketLimiter.acquire()` |
| Fixed Window acquire | zerodep `FixedWindowLimiter.acquire()` |
| Sliding Window acquire | zerodep `SlidingWindowLimiter.acquire()` |
| GCRA acquire | zerodep `GCRALimiter.acquire()` |
| Token Bucket peek | zerodep read-only state check |
| Fixed Window peek | zerodep read-only state check |
| Fixed Window hit (limits) | `limits` FixedWindowRateLimiter with MemoryStorage |
| Moving Window hit (limits) | `limits` MovingWindowRateLimiter with MemoryStorage |
| Sliding Window hit (limits) | `limits` SlidingWindowCounterRateLimiter with MemoryStorage |
| Fixed Window test (limits) | `limits` read-only check |
| Token Bucket consume (limiter) | `limiter` raw token-bucket consume (C-level backend) |
| Token Bucket decorator (limiter) | `limiter` decorator overhead |

## Results

### zerodep vs limits (same algorithm comparison)

| Operation | zerodep (ns) | limits (ns) | Speedup |
|-----------|-------------|-------------|---------|
| Fixed Window acquire vs hit | ~575 | ~3,478 | **6.0x** |
| Sliding Window acquire vs hit | ~873 | ~6,261 | **7.2x** |
| Fixed Window peek vs test | ~722 | ~2,318 | **3.2x** |

### zerodep vs limiter (token bucket comparison)

| Operation | zerodep (ns) | limiter (ns) | Ratio |
|-----------|-------------|-------------|-------|
| Token Bucket acquire vs consume | ~762 | ~571 | 1.3x slower |
| — | — | decorator: ~84,000 | zerodep 110x faster |

!!! note
    `limiter`'s raw `consume()` is faster because it returns a plain `bool` with no result object allocation. Its decorator mode adds ~84μs overhead per call, making it **110x slower** than zerodep's `acquire()`.

### All algorithms (zerodep)

| Algorithm | acquire (ns) | peek (ns) |
|-----------|-------------|-----------|
| FixedWindow | ~575 | ~722 |
| GCRA | ~740 | — |
| TokenBucket | ~762 | ~922 |
| SlidingWindow | ~873 | — |

### Multi-threaded throughput (ThreadSafeLimiter)

| Scenario | Before optimization | After optimization | Improvement |
|----------|--------------------|--------------------|-------------|
| 4 threads, same key | 4,590 ns/op | 4,732 ns/op | GIL-bound |
| 4 threads, different keys | 4,713 ns/op | 2,686 ns/op | **+76%** |

Per-key locking allows different keys to run fully concurrently.

## Optimization History

| Step | TokenBucket (ns) | Improvement |
|------|-----------------|-------------|
| Baseline (frozen dataclass) | 1,338 | — |
| `__slots__` Result class | 996 | +34% |
| Inline hot-path methods | 813 | +65% |
| Remove `int()`/`round()` | 762 | **+75%** |

## CI Benchmark Dashboard

<iframe src="https://oaklight.github.io/zerodep/dev/bench/" style="width:100%;height:400px;border:none;"></iframe>
