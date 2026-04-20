# Cache Benchmark

Apple-to-apple performance comparison between zerodep cache and [`cachetools`](https://pypi.org/project/cachetools/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** cachetools 7.0.5
    - **Last Updated:** 2026-04-21

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `cache.py` | stdlib-only cache with sync+async support |
| **cachetools** | *(reference)* | Popular caching library (no async support) |

## Tests Performed

| Test | Description |
|------|-------------|
| LRU Get/Set | 500 set + 500 get operations on LRUCache (maxsize=256) |
| LRU Eviction Pressure | 1000 writes into LRUCache (maxsize=64), constant eviction |
| LFU Eviction Pressure | 1000 writes into LFUCache (maxsize=64), constant eviction |
| TTL Expiry | Insert 500 items, wait for expiry, call `expire()` |
| Decorator Overhead (LRU) | 200 cached function calls (50 unique keys) via `@lru_cache` |
| Decorator Overhead (TTL) | 200 cached function calls (50 unique keys) via `@ttl_cache` |
| hashkey | 500 calls to `hashkey(1, "hello", 3.14, True, a=1, b="two", c=None)` |
| typedkey | 500 calls to `typedkey(1, "hello", 3.14, True, a=1, b="two", c=None)` |
| Mixed Workload | 300 writes + 300 reads + 100 deletes + 150 writes on LRUCache (maxsize=128) |

## Performance Comparison (Mean)

| Test | zerodep | cachetools | Ratio |
|------|---------|------------|-------|
| LRU Get/Set | 1,000 μs | 1,110 μs | **1.1x faster** |
| LRU Eviction Pressure | 1,880 μs | 2,030 μs | **1.1x faster** |
| LFU Eviction Pressure | 1,750 μs | 1,890 μs | **1.1x faster** |
| TTL Expiry | 3,600 μs | 3,540 μs | ~same |
| Decorator (LRU) | 228 μs | 267 μs | **1.2x faster** |
| Decorator (TTL) | 304 μs | 300 μs | ~same |
| hashkey | 629 μs | 642 μs | ~same |
| typedkey | 1,280 μs | 1,650 μs | **1.3x faster** |
| Mixed Workload | 835 μs | 921 μs | **1.1x faster** |

## Key Takeaways

- **Core cache operations are 1.1x faster** -- LRU get/set, LRU eviction, LFU eviction, and mixed workloads consistently show zerodep ~1.1x faster than cachetools.
- **LFU eviction now also wins** -- LFU eviction pressure is **1.1x faster**, up from ~same in previous runs.
- **Decorator overhead: LRU is 1.2x faster, TTL at parity** -- the LRU decorator remains **1.2x faster**, while TTL decorator is at parity.
- **typedkey is 1.3x faster** -- zerodep's `_HashedTuple` implementation shows a clear edge on type-aware key generation. hashkey is at parity.
- **Async support is the key differentiator** -- cachetools has **no async decorator support at all**. zerodep's `cached()` and all convenience decorators auto-detect async functions and use `asyncio.Lock` for concurrency safety.

## Run It Yourself

```bash
pip install pytest pytest-benchmark cachetools
pytest cache/test_cache_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/cache.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
