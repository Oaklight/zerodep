# Cache

Zero-dependency in-memory caching with TTL, eviction policies, and sync+async decorator support.

## Overview

The Cache module provides `MutableMapping`-based cache classes with four eviction policies (LRU, FIFO, LFU, TTL) and a `cached()` decorator that auto-detects sync/async functions. Requires **Python 3.10+**, **no pip dependencies**.

| File | Description | Dependencies |
|------|-------------|--------------|
| `cache.py` | Pure Python implementation | None (stdlib only: `collections`, `functools`, `time`, `threading`, `asyncio`, `inspect`) |

## Key Features

- **Four cache classes** -- `LRUCache`, `FIFOCache`, `LFUCache`, `TTLCache`, all implementing `MutableMapping`
- **Sync + async decorators** -- `cached()` auto-detects coroutine functions and uses the appropriate lock type
- **Convenience decorators** -- `lru_cache()`, `ttl_cache()`, `lfu_cache()`, `fifo_cache()` with triple-form support (`@dec`, `@dec()`, `@dec(args)`)
- **Thread-safe** -- optional `lock` parameter accepting `threading.Lock` (sync) or `asyncio.Lock` (async)
- **TTL expiration** -- global TTL per cache with lazy expiry and explicit `expire()` method
- **O(1) LFU** -- doubly-linked frequency list for constant-time eviction and access
- **Cache statistics** -- `cache_info()` returning `CacheInfo(hits, misses, maxsize, currsize)` when `info=True`
- **Custom key functions** -- `hashkey`, `methodkey`, `typedkey` for flexible cache key generation
- **Custom sizing** -- `getsizeof` parameter for weighted cache entries

## How to Use in Your Project

Copy the single `.py` file into your project:

```bash
cp cache/cache.py your_project/
```

Then import directly:

```python
from cache import LRUCache, TTLCache, cached, lru_cache, ttl_cache
```

## Usage Examples

### Convenience Decorators

```python
from cache import lru_cache, ttl_cache, lfu_cache, fifo_cache

# LRU cache (like functools.lru_cache but with more features)
@lru_cache(maxsize=256)
def fibonacci(n):
    return n if n < 2 else fibonacci(n - 1) + fibonacci(n - 2)

# TTL cache -- entries expire after 60 seconds
@ttl_cache(maxsize=100, ttl=60)
def fetch_config(key):
    return load_from_db(key)

# LFU cache -- evicts least frequently used
@lfu_cache(maxsize=128)
def get_user(user_id):
    return db.query(user_id)

# FIFO cache -- evicts oldest entry
@fifo_cache(maxsize=64)
def parse_template(name):
    return compile_template(name)
```

All convenience decorators support the triple form:

```python
# Bare decorator (defaults)
@lru_cache
def f(x): ...

# Empty parentheses (same as bare)
@lru_cache()
def f(x): ...

# With arguments
@lru_cache(maxsize=512)
def f(x): ...
```

### Async Support

```python
import asyncio
from cache import lru_cache, ttl_cache, cached, LRUCache

# Convenience decorators auto-detect async
@lru_cache(maxsize=128)
async def fetch_user(user_id):
    return await db.get_user(user_id)

# TTL cache for API responses
@ttl_cache(maxsize=50, ttl=300)
async def get_weather(city):
    return await api.get(f"/weather/{city}")

# Low-level cached() with async lock
@cached(LRUCache(maxsize=128), lock=asyncio.Lock(), info=True)
async def expensive_query(params):
    return await run_query(params)

async def main():
    result = await fetch_user(42)
    info = expensive_query.cache_info()
    print(f"Hits: {info.hits}, Misses: {info.misses}")

asyncio.run(main())
```

### Cache Classes Directly

```python
from cache import LRUCache, TTLCache, FIFOCache, LFUCache

# LRU cache as a dict-like container
cache = LRUCache(maxsize=100)
cache["key1"] = "value1"
cache["key2"] = "value2"
print(cache["key1"])      # "value1" -- also marks as recently used
print(len(cache))         # 2

# TTL cache -- items expire automatically
import time
ttl = TTLCache(maxsize=100, ttl=10)  # 10-second TTL
ttl["session"] = {"user": "alice"}
time.sleep(11)
print(ttl.get("session"))  # None -- expired

# Explicit expiry sweep
ttl.expire()               # Remove all expired entries
```

### Cache Statistics

```python
from cache import lru_cache

@lru_cache(maxsize=128, info=True)
def compute(x, y):
    return x ** y

compute(2, 10)  # miss
compute(2, 10)  # hit
compute(3, 10)  # miss

info = compute.cache_info()
print(info)  # CacheInfo(hits=1, misses=2, maxsize=128, currsize=2)

compute.cache_clear()
info = compute.cache_info()
print(info.currsize)  # 0
```

### Thread Safety

```python
import threading
from cache import cached, LRUCache

@cached(LRUCache(maxsize=256), lock=threading.Lock())
def thread_safe_lookup(key):
    return expensive_computation(key)
```

!!! note "Lock Release During Computation"
    The lock is released while the wrapped function executes, so other threads aren't blocked during slow computations. On re-acquisition, `setdefault()` is used to handle race conditions where another thread may have already populated the cache entry.

### Custom Key Functions

```python
from cache import cached, LRUCache, methodkey, typedkey

# For methods -- ignores `self` in cache key
class MyService:
    @cached(LRUCache(maxsize=128), key=methodkey)
    def get_data(self, query):
        return self.db.execute(query)

# Type-aware keys -- treats f(1) and f(1.0) as different calls
@cached(LRUCache(maxsize=128), key=typedkey)
def convert(value):
    return process(value)
```

### Custom Sizing

```python
from cache import LRUCache

# Weighted cache -- size based on value length
cache = LRUCache(maxsize=1000, getsizeof=len)
cache["small"] = "hi"       # size 2
cache["large"] = "x" * 500  # size 500
print(cache.currsize)        # 502
```

## API Reference

### Cache Classes

#### `Cache(maxsize, getsizeof=None)`

Abstract base class implementing `MutableMapping`. All cache types inherit from this.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `maxsize` | `int` | -- | Maximum cache size. |
| `getsizeof` | `Callable \| None` | `None` | Function `(value) -> int` for custom sizing. Defaults to 1 per entry. |

| Property | Type | Description |
|----------|------|-------------|
| `maxsize` | `int` | Maximum cache size. |
| `currsize` | `int` | Current cache size. |

---

#### `LRUCache(maxsize, getsizeof=None)`

Least Recently Used cache. Accessing an item moves it to the end (most recently used). Evicts the least recently used item when full.

---

#### `FIFOCache(maxsize, getsizeof=None)`

First In, First Out cache. Accessing an item does **not** change its position. Evicts the oldest inserted item when full.

---

#### `LFUCache(maxsize, getsizeof=None)`

Least Frequently Used cache. Tracks access frequency using an O(1) doubly-linked frequency list. Evicts the least frequently accessed item when full.

---

#### `TTLCache(maxsize, ttl, timer=time.monotonic, getsizeof=None)`

LRU cache with time-to-live expiration.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `maxsize` | `int` | -- | Maximum cache size. |
| `ttl` | `float` | -- | Time-to-live in seconds for all entries. |
| `timer` | `Callable` | `time.monotonic` | Timer function returning current time. |
| `getsizeof` | `Callable \| None` | `None` | Custom sizing function. |

| Method | Description |
|--------|-------------|
| `expire(time=None)` | Remove all entries expired as of `time` (default: now). |

---

### Key Functions

#### `hashkey(*args, **kwargs)`

Default key function. Returns a hashable tuple of positional and keyword arguments.

#### `methodkey(self, *args, **kwargs)`

Key function for methods. Ignores the first positional argument (`self`).

#### `typedkey(*args, **kwargs)`

Like `hashkey` but includes argument types in the key, so `f(1)` and `f(1.0)` produce different keys.

---

### Decorators

#### `cached(cache, *, key=hashkey, lock=None, info=False)`

General-purpose caching decorator. Auto-detects sync/async functions.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cache` | `MutableMapping \| None` | -- | Cache instance. Pass `None` to disable caching (passthrough). |
| `key` | `Callable` | `hashkey` | Key function for building cache keys. |
| `lock` | `Lock \| None` | `None` | `threading.Lock` (sync) or `asyncio.Lock` (async) for thread safety. |
| `info` | `bool` | `False` | If `True`, adds `cache_info()` and `cache_clear()` methods to the wrapper. |

**Wrapper attributes** (when `info=True`):

- `cache_info() -> CacheInfo` -- returns `CacheInfo(hits, misses, maxsize, currsize)`.
- `cache_clear()` -- clears the cache and resets statistics.
- `__wrapped__` -- reference to the original function.

---

#### `lru_cache(fn=None, *, maxsize=128, key=hashkey, lock=None, info=True)`

Convenience decorator using `LRUCache`.

#### `ttl_cache(fn=None, *, maxsize=128, ttl=600, timer=time.monotonic, key=hashkey, lock=None, info=True)`

Convenience decorator using `TTLCache`.

#### `lfu_cache(fn=None, *, maxsize=128, key=hashkey, lock=None, info=True)`

Convenience decorator using `LFUCache`.

#### `fifo_cache(fn=None, *, maxsize=128, key=hashkey, lock=None, info=True)`

Convenience decorator using `FIFOCache`.

All convenience decorators support `@dec`, `@dec()`, and `@dec(args)` forms.

---

### `CacheInfo`

Named tuple returned by `cache_info()`.

| Field | Type | Description |
|-------|------|-------------|
| `hits` | `int` | Number of cache hits. |
| `misses` | `int` | Number of cache misses. |
| `maxsize` | `int \| None` | Maximum cache size, or `None` if unknown. |
| `currsize` | `int` | Current number of entries. |

## Comparison with cachetools / functools.lru_cache

| Feature | zerodep cache | cachetools | functools.lru_cache |
|---------|--------------|------------|---------------------|
| Dependencies | None (stdlib only) | None | stdlib |
| LRU | Yes | Yes | Yes |
| FIFO | Yes | Yes | No |
| LFU | Yes | Yes | No |
| TTL | Yes | Yes | No |
| Async decorator | **Yes** | **No** | **No** |
| Custom key functions | Yes | Yes | typed=True only |
| Custom sizing | Yes | Yes | No |
| Thread-safe option | Yes (lock param) | Yes (lock param) | Built-in |
| cache_info() | Yes | Yes | Yes |
| MutableMapping | Yes | Yes | No |
| Implementation | Single file (~1050 lines) | Package (~1200 lines) | C extension |

**When to use zerodep:** You need async caching support, zero pip dependencies, or single-file vendoring.

**When to use cachetools:** You need `cachedmethod`, `TLRUCache` (per-item TTL function), `RRCache` (random replacement), or `MRUCache`.

**When to use functools.lru_cache:** Simple LRU with no TTL/eviction needs and you want the fastest possible C-backed implementation.

## Benchmark

Benchmarked against `cachetools` across LRU get/set, eviction pressure, TTL expiry, decorator overhead, key functions, and mixed workloads.

See [Cache Benchmark](../benchmarks/cache.md) for detailed results.
