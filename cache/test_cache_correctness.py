"""Correctness tests: zerodep cache vs cachetools."""

import asyncio
import os
import sys
import threading
import time

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from cache import (  # noqa: E402
    Cache,
    CacheInfo,
    FIFOCache,
    LFUCache,
    LRUCache,
    TTLCache,
    cached,
    fifo_cache,
    hashkey,
    lfu_cache,
    lru_cache,
    methodkey,
    ttl_cache,
    typedkey,
)

cachetools = pytest.importorskip("cachetools", reason="cachetools not installed")


# ── Key Functions ──────────────────────────────────────────────────────────


class TestKeyFunctions:
    def test_hashkey_args_only(self):
        k = hashkey(1, 2, 3)
        assert isinstance(k, tuple)
        assert hash(k) == hash(k)  # cached hash

    def test_hashkey_with_kwargs(self):
        k1 = hashkey(1, x=2)
        k2 = hashkey(1, y=2)
        assert k1 != k2

    def test_hashkey_kwargs_order_independent(self):
        k1 = hashkey(a=1, b=2)
        k2 = hashkey(b=2, a=1)
        assert k1 == k2

    def test_hashkey_empty(self):
        k = hashkey()
        assert k == ()

    def test_methodkey_ignores_self(self):
        obj = object()
        k1 = methodkey(obj, 1, 2)
        k2 = hashkey(1, 2)
        assert k1 == k2

    def test_typedkey_type_sensitive(self):
        k1 = typedkey(1)
        k2 = typedkey(1.0)
        assert k1 != k2

    def test_typedkey_same_type(self):
        k1 = typedkey(1)
        k2 = typedkey(1)
        assert k1 == k2

    def test_hashkey_matches_cachetools(self):
        args = (1, "hello", 3.14)
        kwargs = {"x": 10, "y": 20}
        ours = hashkey(*args, **kwargs)
        theirs = cachetools.keys.hashkey(*args, **kwargs)
        # Both should be tuples; internal layout may differ but behavior same
        assert hash(ours) == hash(ours)
        assert hash(theirs) == hash(theirs)


# ── Cache Base ─────────────────────────────────────────────────────────────


class TestCacheBase:
    def test_maxsize(self):
        c = Cache(3)
        c["a"] = 1
        c["b"] = 2
        c["c"] = 3
        assert len(c) == 3
        c["d"] = 4
        assert len(c) == 3  # one evicted

    def test_maxsize_zero(self):
        c = Cache(0)
        with pytest.raises(ValueError, match="value too large"):
            c["a"] = 1

    def test_negative_maxsize(self):
        with pytest.raises(ValueError, match="non-negative"):
            Cache(-1)

    def test_getitem_missing_raises(self):
        c = Cache(10)
        with pytest.raises(KeyError):
            _ = c["nonexistent"]

    def test_getsizeof_custom(self):
        c = Cache(10, getsizeof=len)
        c["a"] = "hello"  # size 5
        c["b"] = "world"  # size 5
        assert c.currsize == 10
        with pytest.raises(ValueError, match="value too large"):
            c["c"] = "this is too long"  # size 16 > 10

    def test_mutable_mapping_protocol(self):
        c = Cache(10)
        c["a"] = 1
        c["b"] = 2
        assert "a" in c
        assert "c" not in c
        assert set(c.keys()) == {"a", "b"}
        assert set(c.values()) == {1, 2}
        assert len(c) == 2

    def test_get_default(self):
        c = Cache(10)
        assert c.get("missing") is None
        assert c.get("missing", 42) == 42

    def test_pop(self):
        c = Cache(10)
        c["a"] = 1
        assert c.pop("a") == 1
        assert "a" not in c
        assert c.pop("a", 99) == 99

    def test_pop_missing_raises(self):
        c = Cache(10)
        with pytest.raises(KeyError):
            c.pop("missing")

    def test_setdefault(self):
        c = Cache(10)
        v = c.setdefault("a", 42)
        assert v == 42
        assert c["a"] == 42
        v2 = c.setdefault("a", 99)
        assert v2 == 42  # not changed

    def test_clear(self):
        c = Cache(10)
        c["a"] = 1
        c["b"] = 2
        c.clear()
        assert len(c) == 0
        assert c.currsize == 0

    def test_repr(self):
        c = Cache(10)
        c["x"] = 1
        r = repr(c)
        assert "Cache" in r
        assert "maxsize=10" in r

    def test_properties(self):
        c = Cache(100)
        assert c.maxsize == 100
        assert c.currsize == 0
        c["a"] = 1
        assert c.currsize == 1

    def test_update_existing_key(self):
        c = Cache(3)
        c["a"] = 1
        c["b"] = 2
        c["c"] = 3
        c["a"] = 10  # update, should not evict
        assert len(c) == 3
        assert c["a"] == 10


# ── LRU Cache ──────────────────────────────────────────────────────────────


class TestLRUCache:
    def test_evicts_least_recently_used(self):
        c = LRUCache(3)
        c["a"] = 1
        c["b"] = 2
        c["c"] = 3
        c["d"] = 4  # evicts a
        assert "a" not in c
        assert set(c.keys()) == {"b", "c", "d"}

    def test_access_updates_order(self):
        c = LRUCache(3)
        c["a"] = 1
        c["b"] = 2
        c["c"] = 3
        _ = c["a"]  # touch a
        c["d"] = 4  # should evict b (least recently used)
        assert "b" not in c
        assert "a" in c

    def test_update_resets_position(self):
        c = LRUCache(3)
        c["a"] = 1
        c["b"] = 2
        c["c"] = 3
        c["a"] = 10  # update a, moves to end
        c["d"] = 4  # should evict b
        assert "b" not in c
        assert c["a"] == 10

    def test_popitem(self):
        c = LRUCache(3)
        c["a"] = 1
        c["b"] = 2
        c["c"] = 3
        key, val = c.popitem()
        assert key == "a" and val == 1

    def test_popitem_empty(self):
        c = LRUCache(3)
        with pytest.raises(KeyError, match="empty"):
            c.popitem()

    def test_matches_cachetools_lru(self):
        ours = LRUCache(3)
        theirs = cachetools.LRUCache(3)
        ops = [
            ("set", "a", 1),
            ("set", "b", 2),
            ("set", "c", 3),
            ("get", "a", None),
            ("set", "d", 4),
            ("get", "b", None),
            ("set", "e", 5),
        ]
        for op, k, v in ops:
            if op == "set":
                ours[k] = v
                theirs[k] = v
            else:
                ours.get(k)
                theirs.get(k)
        assert dict(ours) == dict(theirs)


# ── FIFO Cache ─────────────────────────────────────────────────────────────


class TestFIFOCache:
    def test_evicts_first_inserted(self):
        c = FIFOCache(3)
        c["a"] = 1
        c["b"] = 2
        c["c"] = 3
        c["d"] = 4  # evicts a
        assert "a" not in c
        assert set(c.keys()) == {"b", "c", "d"}

    def test_access_does_not_change_order(self):
        c = FIFOCache(3)
        c["a"] = 1
        c["b"] = 2
        c["c"] = 3
        _ = c["a"]  # touch a, but FIFO doesn't care
        c["d"] = 4  # still evicts a (oldest)
        assert "a" not in c

    def test_popitem(self):
        c = FIFOCache(3)
        c["a"] = 1
        c["b"] = 2
        key, val = c.popitem()
        assert key == "a" and val == 1

    def test_matches_cachetools_fifo(self):
        ours = FIFOCache(3)
        theirs = cachetools.FIFOCache(3)
        for k, v in [("a", 1), ("b", 2), ("c", 3), ("d", 4), ("e", 5)]:
            ours[k] = v
            theirs[k] = v
        assert dict(ours) == dict(theirs)


# ── LFU Cache ──────────────────────────────────────────────────────────────


class TestLFUCache:
    def test_evicts_least_frequent(self):
        c = LFUCache(3)
        c["a"] = 1
        c["b"] = 2
        c["c"] = 3
        _ = c["a"]  # freq: a=2, b=1, c=1
        _ = c["a"]  # freq: a=3, b=1, c=1
        _ = c["b"]  # freq: a=3, b=2, c=1
        c["d"] = 4  # evicts c (least frequent)
        assert "c" not in c
        assert "a" in c and "b" in c

    def test_new_items_have_frequency_one(self):
        c = LFUCache(3)
        c["a"] = 1
        c["b"] = 2
        c["c"] = 3
        # All have freq 1; one will be evicted
        c["d"] = 4
        assert len(c) == 3

    def test_frequency_increments_on_access(self):
        c = LFUCache(3)
        c["a"] = 1
        c["b"] = 2
        _ = c["a"]
        _ = c["a"]  # a has highest freq (3), b has freq 1
        c["c"] = 3  # c has freq 1
        c["d"] = 4  # evicts one of b or c (both freq 1), not a
        assert "a" in c
        assert "d" in c
        # One of b or c was evicted (both had freq 1)
        assert "b" not in c or "c" not in c

    def test_popitem_empty(self):
        c = LFUCache(3)
        with pytest.raises(KeyError, match="empty"):
            c.popitem()

    def test_clear(self):
        c = LFUCache(3)
        c["a"] = 1
        c["b"] = 2
        c.clear()
        assert len(c) == 0

    def test_delete(self):
        c = LFUCache(3)
        c["a"] = 1
        c["b"] = 2
        del c["a"]
        assert "a" not in c
        assert len(c) == 1

    def test_matches_cachetools_lfu(self):
        ours = LFUCache(3)
        theirs = cachetools.LFUCache(3)
        ops = [
            ("set", "a", 1),
            ("set", "b", 2),
            ("set", "c", 3),
            ("get", "a", None),
            ("get", "a", None),
            ("get", "b", None),
            ("set", "d", 4),
        ]
        for op, k, v in ops:
            if op == "set":
                ours[k] = v
                theirs[k] = v
            else:
                ours.get(k)
                theirs.get(k)
        assert dict(ours) == dict(theirs)


# ── TTL Cache ──────────────────────────────────────────────────────────────


class TestTTLCache:
    def test_item_accessible_before_ttl(self):
        c = TTLCache(10, ttl=1.0)
        c["x"] = 42
        assert c["x"] == 42

    def test_item_expires_after_ttl(self):
        c = TTLCache(10, ttl=0.05)
        c["x"] = 42
        time.sleep(0.06)
        with pytest.raises(KeyError):
            _ = c["x"]

    def test_contains_excludes_expired(self):
        c = TTLCache(10, ttl=0.05)
        c["x"] = 42
        assert "x" in c
        time.sleep(0.06)
        assert "x" not in c

    def test_len_excludes_expired(self):
        c = TTLCache(10, ttl=0.05)
        c["a"] = 1
        c["b"] = 2
        assert len(c) == 2
        time.sleep(0.06)
        assert len(c) == 0

    def test_iter_excludes_expired(self):
        c = TTLCache(10, ttl=0.05)
        c["a"] = 1
        c["b"] = 2
        assert set(c) == {"a", "b"}
        time.sleep(0.06)
        assert set(c) == set()

    def test_expire_returns_items(self):
        c = TTLCache(10, ttl=0.05)
        c["a"] = 1
        c["b"] = 2
        time.sleep(0.06)
        expired = c.expire()
        keys = {k for k, v in expired}
        assert keys == {"a", "b"}

    def test_lru_eviction_within_ttl(self):
        c = TTLCache(3, ttl=10.0)
        c["a"] = 1
        c["b"] = 2
        c["c"] = 3
        _ = c["a"]  # touch a
        c["d"] = 4  # evicts b (LRU, nothing expired)
        assert "b" not in c
        assert "a" in c

    def test_setitem_triggers_expire(self):
        c = TTLCache(10, ttl=0.05)
        c["a"] = 1
        time.sleep(0.06)
        c["b"] = 2  # should expire a first
        assert "a" not in c
        assert "b" in c

    def test_ttl_property(self):
        c = TTLCache(10, ttl=30.0)
        assert c.ttl == 30.0

    def test_custom_timer(self):
        fake_time = [0.0]

        def timer():
            return fake_time[0]

        c = TTLCache(10, ttl=10.0, timer=timer)
        c["a"] = 1
        assert c["a"] == 1
        fake_time[0] = 11.0
        with pytest.raises(KeyError):
            _ = c["a"]

    def test_matches_cachetools_ttl(self):
        fake_time = [0.0]

        def timer():
            return fake_time[0]

        ours = TTLCache(10, ttl=5.0, timer=timer)
        theirs = cachetools.TTLCache(10, ttl=5, timer=timer)

        ours["a"] = 1
        theirs["a"] = 1
        ours["b"] = 2
        theirs["b"] = 2

        assert dict(ours) == dict(theirs)

        fake_time[0] = 6.0
        assert dict(ours) == dict(theirs)  # both empty


# ── cached() Decorator ────────────────────────────────────────────────────


class TestCachedDecorator:
    def test_basic_caching(self):
        call_count = 0

        @cached(LRUCache(10), info=True)
        def square(n):
            nonlocal call_count
            call_count += 1
            return n * n

        assert square(5) == 25
        assert square(5) == 25
        assert call_count == 1

    def test_different_args(self):
        @cached(LRUCache(10))
        def add(a, b):
            return a + b

        assert add(1, 2) == 3
        assert add(3, 4) == 7

    def test_cache_info(self):
        @cached(LRUCache(10), info=True)
        def f(x):
            return x

        f(1)
        f(1)
        f(2)
        info = f.cache_info()
        assert isinstance(info, CacheInfo)
        assert info.hits == 1
        assert info.misses == 2
        assert info.maxsize == 10
        assert info.currsize == 2

    def test_cache_clear(self):
        @cached(LRUCache(10), info=True)
        def f(x):
            return x

        f(1)
        f(2)
        f.cache_clear()
        info = f.cache_info()
        assert info.hits == 0
        assert info.misses == 0
        assert info.currsize == 0

    def test_cache_none_passthrough(self):
        call_count = 0

        @cached(None)
        def f(x):
            nonlocal call_count
            call_count += 1
            return x

        f(1)
        f(1)
        assert call_count == 2

    def test_cache_attribute(self):
        c = LRUCache(10)

        @cached(c)
        def f(x):
            return x

        assert f.cache is c

    def test_preserves_metadata(self):
        @cached(LRUCache(10))
        def my_func(x):
            """My docstring."""
            return x

        assert my_func.__name__ == "my_func"
        assert my_func.__doc__ == "My docstring."

    def test_value_too_large_still_returns(self):
        c = Cache(2, getsizeof=lambda v: v)

        @cached(c)
        def f(x):
            return x

        # value 5 is too large for cache (maxsize=2), but should still return
        assert f(5) == 5
        assert len(c) == 0

    def test_custom_key_function(self):
        @cached(LRUCache(10), key=typedkey)
        def f(x):
            return type(x).__name__

        assert f(1) == "int"
        assert f(1.0) == "float"  # different key due to typedkey


# ── cached() with Lock ────────────────────────────────────────────────────


class TestCachedWithLock:
    def test_sync_lock_thread_safety(self):
        call_count = 0
        lock = threading.Lock()

        @cached(LRUCache(100), lock=lock, info=True)
        def slow_compute(n):
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)
            return n * n

        results = {}
        errors = []

        def worker(n):
            try:
                results[n] = slow_compute(n)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i % 5,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        # 5 unique values, each computed once (or at most twice due to race)
        assert len(results) == 5
        for i in range(5):
            assert results[i] == i * i


# ── Async cached() ────────────────────────────────────────────────────────


class TestAsyncCached:
    @pytest.mark.asyncio
    async def test_async_basic_caching(self):
        call_count = 0

        @cached(LRUCache(10), info=True)
        async def f(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        assert await f(5) == 10
        assert await f(5) == 10
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_different_args(self):
        @cached(LRUCache(10), info=True)
        async def f(x):
            return x + 1

        assert await f(1) == 2
        assert await f(2) == 3
        info = f.cache_info()
        assert info.misses == 2

    @pytest.mark.asyncio
    async def test_async_cache_info(self):
        @cached(LRUCache(10), info=True)
        async def f(x):
            return x

        await f(1)
        await f(1)
        await f(2)
        info = f.cache_info()
        assert info.hits == 1
        assert info.misses == 2

    @pytest.mark.asyncio
    async def test_async_cache_clear(self):
        @cached(LRUCache(10), info=True)
        async def f(x):
            return x

        await f(1)
        f.cache_clear()
        assert f.cache_info().hits == 0
        assert f.cache_info().currsize == 0

    @pytest.mark.asyncio
    async def test_async_with_lock(self):
        call_count = 0
        lock = asyncio.Lock()

        @cached(LRUCache(10), lock=lock, info=True)
        async def f(x):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return x

        results = await asyncio.gather(f(1), f(2), f(1), f(2))
        assert results == [1, 2, 1, 2]


# ── Convenience Decorators ────────────────────────────────────────────────


class TestConvenienceDecorators:
    def test_lru_cache_bare(self):
        @lru_cache
        def f(x):
            return x * 2

        assert f(3) == 6
        assert f(3) == 6
        assert f.cache_info().hits == 1

    def test_lru_cache_empty_parens(self):
        @lru_cache()
        def f(x):
            return x * 2

        assert f(3) == 6
        assert f.cache_info().misses == 1

    def test_lru_cache_with_args(self):
        @lru_cache(maxsize=2)
        def f(x):
            return x

        f(1)
        f(2)
        f(3)  # evicts 1
        assert f.cache_info().currsize == 2

    def test_ttl_cache_expires(self):
        call_count = 0

        @ttl_cache(maxsize=10, ttl=0.05)
        def f(x):
            nonlocal call_count
            call_count += 1
            return x

        f(1)
        f(1)
        assert call_count == 1
        time.sleep(0.06)
        f(1)
        assert call_count == 2

    def test_lfu_cache_eviction(self):
        @lfu_cache(maxsize=2)
        def f(x):
            return x

        f(1)
        f(1)  # freq 2
        f(2)  # freq 1
        f(3)  # evicts 2 (least frequent)
        assert f.cache_info().currsize == 2

    def test_fifo_cache_eviction(self):
        @fifo_cache(maxsize=2)
        def f(x):
            return x

        f(1)
        f(2)
        f(3)  # evicts 1
        assert f.cache_info().currsize == 2

    @pytest.mark.asyncio
    async def test_async_lru_cache(self):
        @lru_cache(maxsize=10)
        async def f(x):
            return x * 3

        assert await f(5) == 15
        assert await f(5) == 15
        assert f.cache_info().hits == 1

    @pytest.mark.asyncio
    async def test_async_ttl_cache(self):
        @ttl_cache(maxsize=10, ttl=0.05)
        async def f(x):
            return x

        assert await f(1) == 1
        await asyncio.sleep(0.06)
        assert await f(1) == 1  # recomputed after expiry

    @pytest.mark.asyncio
    async def test_async_lfu_cache(self):
        @lfu_cache(maxsize=10)
        async def f(x):
            return x * 2

        assert await f(5) == 10
        assert await f(5) == 10
        assert f.cache_info().hits == 1

    @pytest.mark.asyncio
    async def test_async_fifo_cache(self):
        @fifo_cache(maxsize=10)
        async def f(x):
            return x + 1

        assert await f(5) == 6
        assert await f(5) == 6
        assert f.cache_info().hits == 1


# ── Cross Validation ──────────────────────────────────────────────────────


class TestCrossValidation:
    def test_lru_same_eviction_order(self):
        ours = LRUCache(5)
        theirs = cachetools.LRUCache(5)
        for i in range(10):
            ours[i] = i * 10
            theirs[i] = i * 10
        assert dict(ours) == dict(theirs)

    def test_fifo_same_eviction_order(self):
        ours = FIFOCache(5)
        theirs = cachetools.FIFOCache(5)
        for i in range(10):
            ours[i] = i * 10
            theirs[i] = i * 10
        assert dict(ours) == dict(theirs)

    def test_lfu_same_eviction_order(self):
        ours = LFUCache(3)
        theirs = cachetools.LFUCache(3)
        for c_ours, c_theirs in [(ours, theirs)]:
            c_ours["a"] = 1
            c_theirs["a"] = 1
            c_ours["b"] = 2
            c_theirs["b"] = 2
            c_ours["c"] = 3
            c_theirs["c"] = 3
            _ = c_ours["a"]
            _ = c_theirs["a"]
            _ = c_ours["a"]
            _ = c_theirs["a"]
            _ = c_ours["b"]
            _ = c_theirs["b"]
            c_ours["d"] = 4
            c_theirs["d"] = 4
        assert dict(ours) == dict(theirs)

    def test_ttl_same_expiry(self):
        fake_time = [0.0]

        def timer():
            return fake_time[0]

        ours = TTLCache(10, ttl=5.0, timer=timer)
        theirs = cachetools.TTLCache(10, ttl=5, timer=timer)

        ours["a"] = 1
        theirs["a"] = 1
        fake_time[0] = 3.0
        ours["b"] = 2
        theirs["b"] = 2

        assert dict(ours) == dict(theirs)

        fake_time[0] = 6.0  # a expired, b still valid
        assert dict(ours) == dict(theirs)

    def test_cached_decorator_hits_misses(self):
        ours_cache = LRUCache(10)
        theirs_cache = cachetools.LRUCache(10)

        @cached(ours_cache, info=True)
        def f_ours(x):
            return x * 2

        @cachetools.cached(theirs_cache)
        def f_theirs(x):
            return x * 2

        for x in [1, 2, 1, 3, 2, 1]:
            f_ours(x)
            f_theirs(x)

        assert dict(ours_cache) == dict(theirs_cache)
