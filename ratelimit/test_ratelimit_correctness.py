"""Correctness tests for zerodep ratelimit module."""

from __future__ import annotations

import asyncio
import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from ratelimit import (
    FixedWindowLimiter,
    GCRALimiter,
    RateLimiter,
    RateLimitExceeded,
    RateLimitResult,
    SlidingWindowLimiter,
    ThreadSafeLimiter,
    TokenBucketLimiter,
    create_limiter,
    parse_quota,
    ratelimit,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeClock:
    """Deterministic clock for testing."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    def test_token_bucket_is_rate_limiter(self):
        assert isinstance(TokenBucketLimiter(rate=1.0, capacity=1), RateLimiter)

    def test_fixed_window_is_rate_limiter(self):
        assert isinstance(FixedWindowLimiter(limit=1, window_seconds=1.0), RateLimiter)

    def test_sliding_window_is_rate_limiter(self):
        assert isinstance(
            SlidingWindowLimiter(limit=1, window_seconds=1.0), RateLimiter
        )

    def test_gcra_is_rate_limiter(self):
        assert isinstance(GCRALimiter(rate=1.0, burst=0), RateLimiter)

    def test_thread_safe_is_rate_limiter(self):
        inner = TokenBucketLimiter(rate=1.0, capacity=1)
        assert isinstance(ThreadSafeLimiter(inner), RateLimiter)


# ---------------------------------------------------------------------------
# RateLimitResult
# ---------------------------------------------------------------------------


class TestRateLimitResult:
    def test_allowed_result(self):
        r = RateLimitResult(
            allowed=True, limit=10, remaining=9, reset_at=100.0, retry_after=None
        )
        assert r.allowed is True
        assert r.remaining == 9
        assert r.retry_after is None

    def test_denied_result(self):
        r = RateLimitResult(
            allowed=False, limit=10, remaining=0, reset_at=100.0, retry_after=5.0
        )
        assert r.allowed is False
        assert r.retry_after == 5.0

    def test_frozen(self):
        r = RateLimitResult(
            allowed=True, limit=10, remaining=9, reset_at=100.0, retry_after=None
        )
        with pytest.raises(AttributeError):
            r.allowed = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    def test_token_bucket_rejects_zero_rate(self):
        with pytest.raises(ValueError, match="rate must be positive"):
            TokenBucketLimiter(rate=0, capacity=10)

    def test_token_bucket_rejects_negative_capacity(self):
        with pytest.raises(ValueError, match="capacity must be positive"):
            TokenBucketLimiter(rate=1.0, capacity=-1)

    def test_fixed_window_rejects_zero_limit(self):
        with pytest.raises(ValueError, match="limit must be positive"):
            FixedWindowLimiter(limit=0, window_seconds=60.0)

    def test_fixed_window_rejects_negative_window(self):
        with pytest.raises(ValueError, match="window_seconds must be positive"):
            FixedWindowLimiter(limit=10, window_seconds=-1.0)

    def test_sliding_window_rejects_zero_limit(self):
        with pytest.raises(ValueError, match="limit must be positive"):
            SlidingWindowLimiter(limit=0, window_seconds=60.0)

    def test_gcra_rejects_zero_rate(self):
        with pytest.raises(ValueError, match="rate must be positive"):
            GCRALimiter(rate=0)

    def test_gcra_rejects_negative_burst(self):
        with pytest.raises(ValueError, match="burst must be non-negative"):
            GCRALimiter(rate=1.0, burst=-1)


# ---------------------------------------------------------------------------
# Token Bucket
# ---------------------------------------------------------------------------


class TestTokenBucket:
    def test_initial_burst(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=1.0, capacity=5, clock=clock)
        for i in range(5):
            r = limiter.acquire("k")
            assert r.allowed, f"request {i} should be allowed"
            assert r.remaining == 5 - i - 1

    def test_denied_after_capacity(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=1.0, capacity=3, clock=clock)
        for _ in range(3):
            limiter.acquire("k")
        r = limiter.acquire("k")
        assert r.allowed is False
        assert r.remaining == 0
        assert r.retry_after is not None and r.retry_after > 0

    def test_refill_over_time(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=2.0, capacity=4, clock=clock)
        for _ in range(4):
            limiter.acquire("k")
        assert limiter.acquire("k").allowed is False
        clock.advance(1.0)
        r = limiter.acquire("k")
        assert r.allowed is True
        assert r.remaining == 1

    def test_refill_caps_at_capacity(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=10.0, capacity=5, clock=clock)
        limiter.acquire("k")
        clock.advance(100.0)
        r = limiter.peek("k")
        assert r.remaining == 5

    def test_multi_token_acquire(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=1.0, capacity=10, clock=clock)
        r = limiter.acquire("k", tokens=7)
        assert r.allowed is True
        assert r.remaining == 3
        r = limiter.acquire("k", tokens=5)
        assert r.allowed is False

    def test_key_isolation(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=1.0, capacity=2, clock=clock)
        limiter.acquire("a")
        limiter.acquire("a")
        assert limiter.acquire("a").allowed is False
        assert limiter.acquire("b").allowed is True

    def test_peek_does_not_consume(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=1.0, capacity=3, clock=clock)
        r1 = limiter.peek("k")
        r2 = limiter.peek("k")
        assert r1.remaining == r2.remaining == 3

    def test_retry_after_accuracy(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=2.0, capacity=2, clock=clock)
        limiter.acquire("k")
        limiter.acquire("k")
        r = limiter.acquire("k")
        assert r.allowed is False
        assert r.retry_after == 0.5


# ---------------------------------------------------------------------------
# Fixed Window
# ---------------------------------------------------------------------------


class TestFixedWindow:
    def test_allows_within_limit(self):
        clock = FakeClock()
        limiter = FixedWindowLimiter(limit=5, window_seconds=60.0, clock=clock)
        for i in range(5):
            r = limiter.acquire("k")
            assert r.allowed, f"request {i} should be allowed"

    def test_denies_over_limit(self):
        clock = FakeClock()
        limiter = FixedWindowLimiter(limit=3, window_seconds=60.0, clock=clock)
        for _ in range(3):
            limiter.acquire("k")
        r = limiter.acquire("k")
        assert r.allowed is False
        assert r.retry_after is not None and r.retry_after > 0

    def test_window_reset(self):
        clock = FakeClock()
        limiter = FixedWindowLimiter(limit=2, window_seconds=10.0, clock=clock)
        limiter.acquire("k")
        limiter.acquire("k")
        assert limiter.acquire("k").allowed is False
        clock.advance(10.0)
        r = limiter.acquire("k")
        assert r.allowed is True
        assert r.remaining == 1

    def test_multi_token_acquire(self):
        clock = FakeClock()
        limiter = FixedWindowLimiter(limit=10, window_seconds=60.0, clock=clock)
        r = limiter.acquire("k", tokens=4)
        assert r.allowed is True
        assert r.remaining == 6
        r = limiter.acquire("k", tokens=7)
        assert r.allowed is False

    def test_key_isolation(self):
        clock = FakeClock()
        limiter = FixedWindowLimiter(limit=1, window_seconds=60.0, clock=clock)
        limiter.acquire("a")
        assert limiter.acquire("a").allowed is False
        assert limiter.acquire("b").allowed is True

    def test_peek_does_not_consume(self):
        clock = FakeClock()
        limiter = FixedWindowLimiter(limit=3, window_seconds=60.0, clock=clock)
        limiter.acquire("k")
        r1 = limiter.peek("k")
        r2 = limiter.peek("k")
        assert r1.remaining == r2.remaining == 2

    def test_retry_after_points_to_window_end(self):
        clock = FakeClock(start=100.0)
        limiter = FixedWindowLimiter(limit=1, window_seconds=30.0, clock=clock)
        limiter.acquire("k")
        clock.advance(5.0)
        r = limiter.acquire("k")
        assert r.allowed is False
        assert r.retry_after == pytest.approx(25.0, abs=0.1)


# ---------------------------------------------------------------------------
# Sliding Window
# ---------------------------------------------------------------------------


class TestSlidingWindow:
    def test_allows_within_limit(self):
        clock = FakeClock()
        limiter = SlidingWindowLimiter(limit=5, window_seconds=60.0, clock=clock)
        for i in range(5):
            r = limiter.acquire("k")
            assert r.allowed, f"request {i} should be allowed"

    def test_denies_over_limit(self):
        clock = FakeClock()
        limiter = SlidingWindowLimiter(limit=3, window_seconds=60.0, clock=clock)
        for _ in range(3):
            limiter.acquire("k")
        r = limiter.acquire("k")
        assert r.allowed is False

    def test_window_roll(self):
        clock = FakeClock()
        limiter = SlidingWindowLimiter(limit=4, window_seconds=10.0, clock=clock)
        for _ in range(4):
            limiter.acquire("k")
        assert limiter.acquire("k").allowed is False
        clock.advance(10.0)
        assert limiter.acquire("k").allowed is False
        clock.advance(5.0)
        r = limiter.acquire("k")
        assert r.allowed is True

    def test_boundary_smoothing(self):
        clock = FakeClock()
        limiter = SlidingWindowLimiter(limit=10, window_seconds=10.0, clock=clock)
        clock.advance(9.0)
        for _ in range(8):
            limiter.acquire("k")
        clock.advance(1.5)
        assert limiter.acquire("k").allowed is True
        assert limiter.acquire("k").allowed is True
        assert limiter.acquire("k").allowed is False

    def test_multi_token_acquire(self):
        clock = FakeClock()
        limiter = SlidingWindowLimiter(limit=10, window_seconds=60.0, clock=clock)
        r = limiter.acquire("k", tokens=6)
        assert r.allowed is True
        r = limiter.acquire("k", tokens=5)
        assert r.allowed is False

    def test_key_isolation(self):
        clock = FakeClock()
        limiter = SlidingWindowLimiter(limit=1, window_seconds=60.0, clock=clock)
        limiter.acquire("a")
        assert limiter.acquire("a").allowed is False
        assert limiter.acquire("b").allowed is True

    def test_peek_does_not_consume(self):
        clock = FakeClock()
        limiter = SlidingWindowLimiter(limit=5, window_seconds=60.0, clock=clock)
        limiter.acquire("k")
        limiter.acquire("k")
        r1 = limiter.peek("k")
        r2 = limiter.peek("k")
        assert r1.remaining == r2.remaining


# ---------------------------------------------------------------------------
# GCRA
# ---------------------------------------------------------------------------


class TestGCRA:
    def test_initial_burst(self):
        clock = FakeClock()
        limiter = GCRALimiter(rate=1.0, burst=4, clock=clock)
        for i in range(5):
            r = limiter.acquire("k")
            assert r.allowed, f"request {i} should be allowed"

    def test_denied_after_burst(self):
        clock = FakeClock()
        limiter = GCRALimiter(rate=1.0, burst=2, clock=clock)
        for _ in range(3):
            limiter.acquire("k")
        r = limiter.acquire("k")
        assert r.allowed is False
        assert r.retry_after is not None and r.retry_after > 0

    def test_recovery_over_time(self):
        clock = FakeClock()
        limiter = GCRALimiter(rate=2.0, burst=1, clock=clock)
        limiter.acquire("k")
        limiter.acquire("k")
        assert limiter.acquire("k").allowed is False
        clock.advance(0.5)
        assert limiter.acquire("k").allowed is True

    def test_no_burst(self):
        clock = FakeClock()
        limiter = GCRALimiter(rate=10.0, burst=0, clock=clock)
        assert limiter.acquire("k").allowed is True
        assert limiter.acquire("k").allowed is False
        clock.advance(0.1)
        assert limiter.acquire("k").allowed is True

    def test_multi_token(self):
        clock = FakeClock()
        limiter = GCRALimiter(rate=10.0, burst=9, clock=clock)
        r = limiter.acquire("k", tokens=5)
        assert r.allowed is True
        r = limiter.acquire("k", tokens=6)
        assert r.allowed is False

    def test_key_isolation(self):
        clock = FakeClock()
        limiter = GCRALimiter(rate=1.0, burst=0, clock=clock)
        limiter.acquire("a")
        assert limiter.acquire("a").allowed is False
        assert limiter.acquire("b").allowed is True

    def test_peek_does_not_consume(self):
        clock = FakeClock()
        limiter = GCRALimiter(rate=1.0, burst=2, clock=clock)
        r1 = limiter.peek("k")
        r2 = limiter.peek("k")
        assert r1.remaining == r2.remaining


# ---------------------------------------------------------------------------
# Eviction
# ---------------------------------------------------------------------------


class TestEviction:
    def test_token_bucket_evicts_stale_keys(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=1.0, capacity=2, clock=clock)
        for i in range(200):
            limiter.acquire(f"k{i}")
        assert len(limiter._buckets) == 200
        clock.advance(100.0)
        for _ in range(128):
            limiter.acquire("trigger")
        assert len(limiter._buckets) < 200

    def test_fixed_window_evicts_stale_keys(self):
        clock = FakeClock()
        limiter = FixedWindowLimiter(limit=10, window_seconds=5.0, clock=clock)
        for i in range(200):
            limiter.acquire(f"k{i}")
        assert len(limiter._windows) == 200
        clock.advance(15.0)
        for _ in range(128):
            limiter.acquire("trigger")
        assert len(limiter._windows) < 200

    def test_sliding_window_evicts_stale_keys(self):
        clock = FakeClock()
        limiter = SlidingWindowLimiter(limit=10, window_seconds=5.0, clock=clock)
        for i in range(200):
            limiter.acquire(f"k{i}")
        assert len(limiter._states) == 200
        clock.advance(20.0)
        for _ in range(128):
            limiter.acquire("trigger")
        assert len(limiter._states) < 200

    def test_gcra_evicts_stale_keys(self):
        clock = FakeClock()
        limiter = GCRALimiter(rate=1.0, burst=0, clock=clock)
        for i in range(200):
            limiter.acquire(f"k{i}")
        assert len(limiter._tats) == 200
        clock.advance(10.0)
        for _ in range(128):
            limiter.acquire("trigger")
        assert len(limiter._tats) < 200


# ---------------------------------------------------------------------------
# Quota string parsing
# ---------------------------------------------------------------------------


class TestParseQuota:
    def test_basic_slash(self):
        q = parse_quota("100/s")
        assert q == {"limit": 100, "period": 1.0, "burst": None}

    def test_per_notation(self):
        q = parse_quota("10 per minute")
        assert q == {"limit": 10, "period": 60.0, "burst": None}

    def test_with_burst(self):
        q = parse_quota("50/s burst 100")
        assert q == {"limit": 50, "period": 1.0, "burst": 100}

    def test_plurals(self):
        q = parse_quota("5/seconds")
        assert q["period"] == 1.0
        q = parse_quota("5/minutes")
        assert q["period"] == 60.0
        q = parse_quota("5/hours")
        assert q["period"] == 3600.0

    def test_all_units(self):
        for unit, expected in [
            ("s", 1.0),
            ("sec", 1.0),
            ("second", 1.0),
            ("m", 60.0),
            ("min", 60.0),
            ("minute", 60.0),
            ("h", 3600.0),
            ("hr", 3600.0),
            ("hour", 3600.0),
            ("d", 86400.0),
            ("day", 86400.0),
        ]:
            q = parse_quota(f"1/{unit}")
            assert q["period"] == expected, f"unit {unit!r} failed"

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="invalid quota string"):
            parse_quota("not-a-quota")

    def test_unknown_unit(self):
        with pytest.raises(ValueError, match="unknown time unit"):
            parse_quota("10/fortnight")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class TestCreateLimiter:
    def test_token_bucket(self):
        lim = create_limiter("token_bucket", "10/s")
        assert isinstance(lim, TokenBucketLimiter)

    def test_fixed_window(self):
        lim = create_limiter("fixed_window", "100/m")
        assert isinstance(lim, FixedWindowLimiter)

    def test_sliding_window(self):
        lim = create_limiter("sliding_window", "100/m")
        assert isinstance(lim, SlidingWindowLimiter)

    def test_gcra(self):
        lim = create_limiter("gcra", "10/s burst 20")
        assert isinstance(lim, GCRALimiter)

    def test_unknown_algorithm(self):
        with pytest.raises(ValueError, match="unknown algorithm"):
            create_limiter("leaky_bucket", "10/s")

    def test_with_clock(self):
        clock = FakeClock()
        lim = create_limiter("token_bucket", "10/s", clock=clock)
        r = lim.acquire("k")
        assert r.allowed is True


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------


class TestDecorator:
    def test_sync_decorator_allows(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=10.0, capacity=5, clock=clock)

        @ratelimit(limiter=limiter)
        def func():
            return 42

        assert func() == 42

    def test_sync_decorator_raises(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=1.0, capacity=1, clock=clock)

        @ratelimit(limiter=limiter)
        def func():
            return 42

        assert func() == 42
        with pytest.raises(RateLimitExceeded):
            func()

    def test_async_decorator_allows(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=10.0, capacity=5, clock=clock)

        @ratelimit(limiter=limiter)
        async def func():
            return 42

        assert asyncio.run(func()) == 42

    def test_async_decorator_raises(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=1.0, capacity=1, clock=clock)

        @ratelimit(limiter=limiter)
        async def func():
            return 42

        asyncio.run(func())
        with pytest.raises(RateLimitExceeded):
            asyncio.run(func())

    def test_decorator_with_quota_string(self):
        @ratelimit("1000/s")
        def func():
            return 42

        assert func() == 42

    def test_no_quota_no_limiter_raises(self):
        with pytest.raises(ValueError, match="either 'quota' or 'limiter'"):
            ratelimit()


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


class TestContextManager:
    def test_sync_context_manager(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=10.0, capacity=5, clock=clock)
        with ratelimit(limiter=limiter) as result:
            assert result.allowed is True

    def test_sync_context_manager_raises(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=1.0, capacity=1, clock=clock)
        with ratelimit(limiter=limiter):
            pass
        with pytest.raises(RateLimitExceeded):
            with ratelimit(limiter=limiter):
                pass

    def test_async_context_manager(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=10.0, capacity=5, clock=clock)

        async def run():
            async with ratelimit(limiter=limiter) as result:
                return result.allowed

        assert asyncio.run(run()) is True


# ---------------------------------------------------------------------------
# Wait-and-retry
# ---------------------------------------------------------------------------


class TestWaitAndRetry:
    def test_sync_wait_succeeds(self):
        limiter = TokenBucketLimiter(rate=100.0, capacity=1)
        limiter.acquire("__default__")
        rl = ratelimit(limiter=limiter, timeout=1.0)
        with rl:
            pass

    def test_sync_wait_timeout(self):
        clock = FakeClock()
        limiter = TokenBucketLimiter(rate=0.1, capacity=1, clock=clock)
        limiter.acquire("__default__")
        rl = ratelimit(limiter=limiter, timeout=0.01)
        with pytest.raises(RateLimitExceeded):
            rl._acquire_or_wait()

    def test_async_wait_succeeds(self):
        limiter = TokenBucketLimiter(rate=100.0, capacity=1)
        limiter.acquire("__default__")

        async def run():
            rl = ratelimit(limiter=limiter, timeout=1.0)
            async with rl:
                pass

        asyncio.run(run())


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------


class TestThreadSafe:
    def test_concurrent_access(self):
        limiter = ThreadSafeLimiter(TokenBucketLimiter(rate=0.001, capacity=100))
        lock = threading.Lock()
        counts = {"allowed": 0, "denied": 0}

        def worker():
            for _ in range(50):
                r = limiter.acquire("k")
                with lock:
                    if r.allowed:
                        counts["allowed"] += 1
                    else:
                        counts["denied"] += 1

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert counts["allowed"] + counts["denied"] == 200
        # With rate=0.001/s and capacity=100, essentially no refill
        # happens during the test, so exactly 100 acquires succeed.
        assert counts["allowed"] == 100

    def test_peek_is_threadsafe(self):
        inner = TokenBucketLimiter(rate=10.0, capacity=5)
        limiter = ThreadSafeLimiter(inner)
        r = limiter.peek("k")
        assert r.remaining == 5


# ---------------------------------------------------------------------------
# RateLimitExceeded
# ---------------------------------------------------------------------------


class TestRateLimitExceeded:
    def test_has_result(self):
        result = RateLimitResult(
            allowed=False, limit=10, remaining=0, reset_at=100.0, retry_after=5.0
        )
        exc = RateLimitExceeded(result)
        assert exc.result is result
        assert "retry_after=5.0" in str(exc)
