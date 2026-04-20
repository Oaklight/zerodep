# Cache Benchmark

Apple-to-apple performance comparison between zerodep cache and [`cachetools`](https://pypi.org/project/cachetools/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** cachetools 7.0.5
    - **Last Updated:** 2026-04-20

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
| LRU Get/Set | 894 μs | 928 μs | **1.0x faster** |
| LRU Eviction Pressure | 1,503 μs | 1,572 μs | **1.0x faster** |
| LFU Eviction Pressure | 1,855 μs | 1,850 μs | ~same |
| TTL Expiry | 3,587 μs | 3,520 μs | ~same |
| Decorator (LRU) | 170 μs | 202 μs | **1.2x faster** |
| Decorator (TTL) | 226 μs | 233 μs | ~same |
| hashkey | 400 μs | 430 μs | **1.1x faster** |
| typedkey | 1,018 μs | 1,256 μs | **1.2x faster** |
| Mixed Workload | 748 μs | 774 μs | **1.0x faster** |

## Key Takeaways

- **Core cache operations are on par** -- LRU get/set, LRU eviction, TTL expiry, and mixed workloads are within noise margin of cachetools, with zerodep slightly faster on LRU and mixed workloads.
- **LFU eviction is ~equal** -- after bypassing `__touch` in `popitem`, LFU eviction pressure is on par with cachetools.
- **Decorator overhead: zerodep now wins on both LRU and TTL** -- LRU decorator is **1.2x faster** (previously ~same), TTL decorator is now at parity (previously 1.3x slower). The optimized decorator wrapper path eliminates the previous TTL overhead.
- **hashkey is 1.1x faster, typedkey is 1.2x faster** -- zerodep's `_HashedTuple` implementation edges out cachetools on key generation.
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
