"""Benchmark: zerodep cache vs cachetools."""

import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from cache import (
    LFUCache,
    LRUCache,
    TTLCache,
    hashkey,
    lru_cache,
    ttl_cache,
    typedkey,
)

cachetools = pytest.importorskip("cachetools", reason="cachetools not installed")


# ── LRU get/set throughput ──


class TestLRUGetSet:
    N = 500

    def test_zerodep(self, benchmark):
        c = LRUCache(maxsize=256)

        def run():
            for i in range(self.N):
                c[i] = i
            for i in range(self.N):
                c.get(i)

        benchmark(run)

    def test_cachetools(self, benchmark):
        c = cachetools.LRUCache(maxsize=256)

        def run():
            for i in range(self.N):
                c[i] = i
            for i in range(self.N):
                c.get(i)

        benchmark(run)


# ── Eviction pressure (write-heavy, cache always full) ──


class TestEvictionPressure:
    N = 1000

    def test_zerodep_lru(self, benchmark):
        c = LRUCache(maxsize=64)

        def run():
            for i in range(self.N):
                c[i] = i

        benchmark(run)

    def test_cachetools_lru(self, benchmark):
        c = cachetools.LRUCache(maxsize=64)

        def run():
            for i in range(self.N):
                c[i] = i

        benchmark(run)

    def test_zerodep_lfu(self, benchmark):
        c = LFUCache(maxsize=64)

        def run():
            for i in range(self.N):
                c[i] = i

        benchmark(run)

    def test_cachetools_lfu(self, benchmark):
        c = cachetools.LFUCache(maxsize=64)

        def run():
            for i in range(self.N):
                c[i] = i

        benchmark(run)


# ── TTL expiry sweep ──


class TestTTLExpiry:
    N = 500

    def test_zerodep(self, benchmark):
        def run():
            c = TTLCache(maxsize=self.N, ttl=0.001)
            for i in range(self.N):
                c[i] = i
            time.sleep(0.002)
            c.expire()

        benchmark(run)

    def test_cachetools(self, benchmark):
        def run():
            c = cachetools.TTLCache(maxsize=self.N, ttl=0.001)
            for i in range(self.N):
                c[i] = i
            time.sleep(0.002)
            c.expire()

        benchmark(run)


# ── Decorator overhead (function succeeds immediately) ──


class TestDecoratorOverhead:
    def test_zerodep_lru(self, benchmark):
        @lru_cache(maxsize=128)
        def fn(x):
            return x * 2

        def run():
            for i in range(200):
                fn(i % 50)

        benchmark(run)

    def test_cachetools_lru(self, benchmark):
        @cachetools.cached(cache=cachetools.LRUCache(maxsize=128))
        def fn(x):
            return x * 2

        def run():
            for i in range(200):
                fn(i % 50)

        benchmark(run)

    def test_zerodep_ttl(self, benchmark):
        @ttl_cache(maxsize=128, ttl=60)
        def fn(x):
            return x * 2

        def run():
            for i in range(200):
                fn(i % 50)

        benchmark(run)

    def test_cachetools_ttl(self, benchmark):
        @cachetools.cached(cache=cachetools.TTLCache(maxsize=128, ttl=60))
        def fn(x):
            return x * 2

        def run():
            for i in range(200):
                fn(i % 50)

        benchmark(run)


# ── Key function performance ──


class TestKeyFunction:
    ARGS = (1, "hello", 3.14, True)
    KWARGS = {"a": 1, "b": "two", "c": None}

    def test_zerodep_hashkey(self, benchmark):
        def run():
            for _ in range(500):
                hashkey(*self.ARGS, **self.KWARGS)

        benchmark(run)

    def test_cachetools_hashkey(self, benchmark):
        def run():
            for _ in range(500):
                cachetools.keys.hashkey(*self.ARGS, **self.KWARGS)

        benchmark(run)

    def test_zerodep_typedkey(self, benchmark):
        def run():
            for _ in range(500):
                typedkey(*self.ARGS, **self.KWARGS)

        benchmark(run)

    def test_cachetools_typedkey(self, benchmark):
        def run():
            for _ in range(500):
                cachetools.keys.typedkey(*self.ARGS, **self.KWARGS)

        benchmark(run)


# ── Mixed read/write workload ──


class TestMixedWorkload:
    def test_zerodep(self, benchmark):
        c = LRUCache(maxsize=128)

        def run():
            for i in range(300):
                c[i] = i
            for i in range(300):
                c.get(i)
            for i in range(0, 300, 3):
                c.pop(i, None)
            for i in range(300, 450):
                c[i] = i

        benchmark(run)

    def test_cachetools(self, benchmark):
        c = cachetools.LRUCache(maxsize=128)

        def run():
            for i in range(300):
                c[i] = i
            for i in range(300):
                c.get(i)
            for i in range(0, 300, 3):
                c.pop(i, None)
            for i in range(300, 450):
                c[i] = i

        benchmark(run)
