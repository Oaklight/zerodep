# Cache Benchmark

Apple-to-apple performance comparison between zerodep cache and [`cachetools`](https://pypi.org/project/cachetools/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

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
| LRU Get/Set | 734 us | 695 us | 0.95x |
| LRU Eviction Pressure | 1,251 us | 1,196 us | 0.96x |
| LFU Eviction Pressure | 2,284 us | 3,680 us | **1.6x faster** |
| TTL Expiry | 4,368 us | 4,119 us | 0.94x |
| Decorator (LRU) | 258 us | 143 us | 0.56x |
| Decorator (TTL) | 214 us | 167 us | 0.78x |
| hashkey | 232 us | 271 us | **1.2x faster** |
| typedkey | 950 us | 899 us | 0.94x |
| Mixed Workload | 623 us | 604 us | 0.97x |

## Key Takeaways

- **LFU is 1.6x faster** -- zerodep's O(1) doubly-linked frequency list outperforms cachetools' counter-based LFU under eviction pressure.
- **Cache class operations are on par** -- LRU get/set, eviction, TTL expiry, and mixed workloads are within 5% of cachetools.
- **Decorator overhead is higher** -- cachetools' simpler wrapper path is ~1.3-1.8x faster for decorated function calls. This is a fixed per-call overhead (tens of nanoseconds) that is negligible for any non-trivial wrapped function.
- **hashkey is 1.2x faster** -- zerodep's `_HashedTuple` implementation edges out cachetools on key generation.
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
