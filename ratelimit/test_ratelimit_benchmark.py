"""Benchmarks for zerodep ratelimit module vs ``limits`` and ``limiter`` libraries."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from ratelimit import (
    FixedWindowLimiter,
    GCRALimiter,
    SlidingWindowLimiter,
    TokenBucketLimiter,
)

limits = pytest.importorskip("limits")
from limits import parse as limits_parse  # noqa: E402
from limits import storage as limits_storage  # noqa: E402
from limits import strategies as limits_strategies  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def limits_fixed_window():
    backend = limits_storage.MemoryStorage()
    return limits_strategies.FixedWindowRateLimiter(backend)


@pytest.fixture
def limits_moving_window():
    backend = limits_storage.MemoryStorage()
    return limits_strategies.MovingWindowRateLimiter(backend)


@pytest.fixture
def limits_sliding_window():
    backend = limits_storage.MemoryStorage()
    return limits_strategies.SlidingWindowCounterRateLimiter(backend)


RATE = limits_parse("10000/second")


# ---------------------------------------------------------------------------
# zerodep benchmarks
# ---------------------------------------------------------------------------


class TestZerodepBenchmarks:
    def test_token_bucket_acquire(self, benchmark):
        limiter = TokenBucketLimiter(rate=10000.0, capacity=10000)
        benchmark(limiter.acquire, "bench-key")

    def test_fixed_window_acquire(self, benchmark):
        limiter = FixedWindowLimiter(limit=10000, window_seconds=1.0)
        benchmark(limiter.acquire, "bench-key")

    def test_sliding_window_acquire(self, benchmark):
        limiter = SlidingWindowLimiter(limit=10000, window_seconds=1.0)
        benchmark(limiter.acquire, "bench-key")

    def test_gcra_acquire(self, benchmark):
        limiter = GCRALimiter(rate=10000.0, burst=9999)
        benchmark(limiter.acquire, "bench-key")

    def test_token_bucket_peek(self, benchmark):
        limiter = TokenBucketLimiter(rate=10000.0, capacity=10000)
        benchmark(limiter.peek, "bench-key")

    def test_fixed_window_peek(self, benchmark):
        limiter = FixedWindowLimiter(limit=10000, window_seconds=1.0)
        benchmark(limiter.peek, "bench-key")


# ---------------------------------------------------------------------------
# limits library benchmarks
# ---------------------------------------------------------------------------


class TestLimitsBenchmarks:
    def test_fixed_window_hit(self, benchmark, limits_fixed_window):
        benchmark(limits_fixed_window.hit, RATE, "bench-key")

    def test_moving_window_hit(self, benchmark, limits_moving_window):
        benchmark(limits_moving_window.hit, RATE, "bench-key")

    def test_sliding_window_hit(self, benchmark, limits_sliding_window):
        benchmark(limits_sliding_window.hit, RATE, "bench-key")

    def test_fixed_window_test(self, benchmark, limits_fixed_window):
        benchmark(limits_fixed_window.test, RATE, "bench-key")


# ---------------------------------------------------------------------------
# limiter library benchmarks (token bucket only)
# ---------------------------------------------------------------------------

try:
    from limiter import Limiter as _Limiter

    _HAS_LIMITER = True
except ImportError:
    _HAS_LIMITER = False


@pytest.mark.skipif(not _HAS_LIMITER, reason="limiter not installed")
class TestLimiterBenchmarks:
    def test_token_bucket_consume(self, benchmark):
        lim = _Limiter(rate=10000, capacity=10000)
        benchmark(lim.limiter.consume, "bench-key")

    def test_token_bucket_decorator(self, benchmark):
        lim = _Limiter(rate=10000, capacity=10000)

        @lim
        def noop():
            pass

        benchmark(noop)
