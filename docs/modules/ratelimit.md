# Rate Limiter

Zero-dependency multi-algorithm rate limiter with sync + async support — stdlib only, Python 3.10+.

> **Replaces:** `limits`, `pyrate-limiter`, `aiolimiter`, `limiter`

## Overview

The ratelimit module provides four in-memory rate-limiting algorithms behind a common `RateLimiter` protocol, plus convenience wrappers (decorator, context manager, string quota notation).

| File | Description | Dependencies |
|------|-------------|--------------|
| `ratelimit.py` | 4 algorithms + convenience API | None (stdlib only) |

## Algorithms

| Algorithm | Class | Best for |
|-----------|-------|----------|
| Token Bucket | `TokenBucketLimiter` | Per-IP throttling, smooth rate with burst tolerance |
| Fixed Window | `FixedWindowLimiter` | Simple counter-per-window, lowest overhead |
| Sliding Window Counter | `SlidingWindowLimiter` | Accurate without boundary-burst artifacts |
| GCRA | `GCRALimiter` | Constant-rate shaping via single TAT timestamp |

## Features

- **4 algorithms** behind a common `RateLimiter` Protocol
- **Sync + async** — `acquire()`/`peek()` and `aacquire()`/`apeek()` on all classes
- **Decorator + context manager** — `@ratelimit("10/s")` or `with ratelimit("5/m")`
- **String quota notation** — parse `"100/s"`, `"10 per minute burst 20"`
- **Thread-safe wrapper** — `ThreadSafeLimiter` with per-key locking
- **Wait-and-retry** — block up to `timeout` seconds for quota
- **Injectable clock** — deterministic testing via `clock` parameter
- **Amortized eviction** — stale keys cleaned every 128 acquire calls

## How to Use in Your Project

```bash
zerodep add ratelimit
# or copy ratelimit/ratelimit.py into your project
```

## Quick Start

### Direct usage

```python
from ratelimit import TokenBucketLimiter

limiter = TokenBucketLimiter(rate=10.0, capacity=20)
result = limiter.acquire("client-ip")
if not result.allowed:
    return 429, {"Retry-After": str(result.retry_after)}
```

### Factory with string quota

```python
from ratelimit import create_limiter

limiter = create_limiter("sliding_window", "100/m burst 200")
result = limiter.acquire("user-123")
```

### Decorator

```python
from ratelimit import ratelimit

@ratelimit("10/s", algorithm="token_bucket")
def handle_request():
    ...

@ratelimit("5/s")
async def async_handler():
    ...
```

### Context manager

```python
from ratelimit import ratelimit

with ratelimit("5/m", key="user-1") as result:
    print(f"remaining: {result.remaining}")

async with ratelimit("5/m", key="user-1") as result:
    await do_work()
```

### Wait-and-retry

```python
from ratelimit import ratelimit

# Block up to 5 seconds waiting for quota
with ratelimit("10/s", timeout=5.0):
    do_work()
```

### Thread safety

```python
from ratelimit import TokenBucketLimiter, ThreadSafeLimiter

limiter = ThreadSafeLimiter(TokenBucketLimiter(rate=100.0, capacity=100))
# Safe to call from multiple threads — per-key locking
result = limiter.acquire("client-ip")
```

### Async API

```python
from ratelimit import TokenBucketLimiter

limiter = TokenBucketLimiter(rate=10.0, capacity=20)
result = await limiter.aacquire("client-ip")
state = await limiter.apeek("client-ip")
```

## RateLimitResult

Every `acquire()` / `peek()` call returns a `RateLimitResult`:

| Field | Type | Description |
|-------|------|-------------|
| `allowed` | `bool` | Whether the request is permitted |
| `limit` | `int \| float` | Total quota (capacity or window limit) |
| `remaining` | `int \| float` | Remaining quota (may be float for fractional tokens) |
| `reset_at` | `float` | Monotonic timestamp when quota replenishes |
| `retry_after` | `float \| None` | Seconds to wait before retrying (`None` when allowed) |

## Quota String Format

```
<N>/<unit>                  "100/s", "10/m", "5/h", "1/d"
<N> per <unit>              "10 per minute"
<N>/<unit> burst <B>        "100/s burst 200"
<N> per <unit> burst <B>    "10 per minute burst 20"
```

Supported units: `s`/`sec`/`second`, `m`/`min`/`minute`, `h`/`hr`/`hour`, `d`/`day` (plurals accepted).

## Performance

Benchmarked against `limits` (most popular Python rate limiter) and `limiter` (C-extension token bucket):

| Algorithm | zerodep (ns/op) | limits (ns/op) | Speedup |
|-----------|----------------|----------------|---------|
| FixedWindow | ~575 | ~3,478 | **6.0x** |
| TokenBucket | ~762 | — | — |
| GCRA | ~740 | — | — |
| SlidingWindow | ~873 | ~6,261 | **7.2x** |

FixedWindow is within 5% of `token-bucket` library's C-extension performance (~549 ns/op).
