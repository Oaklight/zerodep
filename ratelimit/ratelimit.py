# /// zerodep
# version = "0.1.0"
# deps = []
# tier = "subsystem"
# category = "network"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///
"""Multi-algorithm rate limiter with zero dependencies.

Provides four in-memory rate-limiting algorithms behind a common
``RateLimiter`` protocol, plus convenience wrappers (decorator, context
manager, async support, string quota notation).

Algorithms:

- **Token bucket** — smooth rate with configurable burst tolerance.
- **Fixed window** — simplest counter-per-window, lowest overhead.
- **Sliding window counter** — accurate without boundary-burst artifacts.
- **GCRA** (Generic Cell Rate Algorithm) — constant-rate shaping via a
  single TAT (Theoretical Arrival Time) timestamp.

Typical usage::

    limiter = TokenBucketLimiter(rate=10.0, capacity=20)
    result = limiter.acquire("client-ip")
    if not result.allowed:
        return 429, {"Retry-After": str(result.retry_after)}

    # Or with convenience API
    @ratelimit("10/s", algorithm="sliding_window")
    def handle_request(): ...

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.
"""

from __future__ import annotations

import asyncio
import math
import re
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, Protocol, runtime_checkable

__all__: list[str] = [
    "RateLimitResult",
    "RateLimiter",
    "TokenBucketLimiter",
    "FixedWindowLimiter",
    "SlidingWindowLimiter",
    "GCRALimiter",
    "ThreadSafeLimiter",
    "RateLimitExceeded",
    "ratelimit",
    "create_limiter",
    "parse_quota",
]

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    """Outcome of a rate-limit check.

    Attributes:
        allowed: Whether the request is permitted.
        limit: Total quota (bucket capacity or window limit).
        remaining: Remaining quota (>= 0).
        reset_at: Monotonic timestamp when quota fully replenishes or
            the current window ends.
        retry_after: Seconds to wait before retrying.  ``None`` when
            ``allowed`` is ``True``.
    """

    allowed: bool
    limit: int
    remaining: int
    reset_at: float
    retry_after: float | None


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class RateLimiter(Protocol):
    """Common interface for all rate-limiter implementations."""

    def acquire(self, key: str, tokens: int = 1) -> RateLimitResult:
        """Check and consume *tokens* units of quota for *key*."""
        ...

    def peek(self, key: str) -> RateLimitResult:
        """Return current quota state for *key* without consuming."""
        ...


# ---------------------------------------------------------------------------
# Eviction mixin
# ---------------------------------------------------------------------------

_EVICT_INTERVAL = 128


class _EvictionMixin:
    """Amortised stale-key eviction for in-memory stores.

    Subclasses must set ``_call_count: int`` and implement
    ``_evict_stale(now)`` to remove expired entries.
    """

    _call_count: int

    def _maybe_evict(self, now: float) -> None:
        self._call_count += 1
        if self._call_count >= _EVICT_INTERVAL:
            self._call_count = 0
            self._evict_stale(now)

    def _evict_stale(self, now: float) -> None:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Token bucket
# ---------------------------------------------------------------------------


@dataclass
class _Bucket:
    tokens: float
    last_refill: float


class TokenBucketLimiter(_EvictionMixin):
    """Token-bucket rate limiter.

    Tokens are replenished lazily on each ``acquire`` call.

    Args:
        rate: Tokens added per second.
        capacity: Maximum tokens the bucket can hold (burst size).
        clock: Callable returning current monotonic time.
    """

    def __init__(
        self,
        rate: float,
        capacity: int,
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if rate <= 0:
            raise ValueError(f"rate must be positive, got {rate}")
        if capacity <= 0:
            raise ValueError(f"capacity must be positive, got {capacity}")
        self.rate = rate
        self.capacity = capacity
        self._clock = clock or time.monotonic
        self._buckets: dict[str, _Bucket] = {}
        self._call_count = 0

    def acquire(self, key: str, tokens: int = 1) -> RateLimitResult:
        now = self._clock()
        self._maybe_evict(now)
        bucket = self._get_or_create(key, now)
        self._refill(bucket, now)

        if bucket.tokens >= tokens:
            bucket.tokens -= tokens
            return RateLimitResult(
                allowed=True,
                limit=self.capacity,
                remaining=int(bucket.tokens),
                reset_at=now + (self.capacity - bucket.tokens) / self.rate,
                retry_after=None,
            )

        deficit = tokens - bucket.tokens
        retry_after = deficit / self.rate
        return RateLimitResult(
            allowed=False,
            limit=self.capacity,
            remaining=int(bucket.tokens),
            reset_at=now + self.capacity / self.rate,
            retry_after=round(retry_after, 3),
        )

    def peek(self, key: str) -> RateLimitResult:
        now = self._clock()
        bucket = self._get_or_create(key, now)
        self._refill(bucket, now)
        return RateLimitResult(
            allowed=bucket.tokens >= 1,
            limit=self.capacity,
            remaining=int(bucket.tokens),
            reset_at=now + (self.capacity - bucket.tokens) / self.rate,
            retry_after=None,
        )

    def _get_or_create(self, key: str, now: float) -> _Bucket:
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = _Bucket(tokens=float(self.capacity), last_refill=now)
            self._buckets[key] = bucket
        return bucket

    def _refill(self, bucket: _Bucket, now: float) -> None:
        elapsed = now - bucket.last_refill
        if elapsed > 0:
            bucket.tokens = min(self.capacity, bucket.tokens + elapsed * self.rate)
            bucket.last_refill = now

    def _evict_stale(self, now: float) -> None:
        stale = [
            k
            for k, b in self._buckets.items()
            if b.tokens + (now - b.last_refill) * self.rate >= self.capacity
        ]
        for k in stale:
            del self._buckets[k]


# ---------------------------------------------------------------------------
# Fixed window
# ---------------------------------------------------------------------------


@dataclass
class _FixedWindow:
    count: int
    window_start: float


class FixedWindowLimiter(_EvictionMixin):
    """Fixed-window rate limiter.

    Divides time into non-overlapping windows.  Each key gets at most
    ``limit`` requests per window.

    Args:
        limit: Maximum requests per window.
        window_seconds: Window duration in seconds.
        clock: Callable returning current monotonic time.
    """

    def __init__(
        self,
        limit: int,
        window_seconds: float,
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if limit <= 0:
            raise ValueError(f"limit must be positive, got {limit}")
        if window_seconds <= 0:
            raise ValueError(f"window_seconds must be positive, got {window_seconds}")
        self.limit = limit
        self.window_seconds = window_seconds
        self._clock = clock or time.monotonic
        self._windows: dict[str, _FixedWindow] = {}
        self._call_count = 0

    def acquire(self, key: str, tokens: int = 1) -> RateLimitResult:
        now = self._clock()
        self._maybe_evict(now)
        window = self._get_or_reset(key, now)

        if window.count + tokens <= self.limit:
            window.count += tokens
            remaining = self.limit - window.count
            reset_at = window.window_start + self.window_seconds
            return RateLimitResult(
                allowed=True,
                limit=self.limit,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=None,
            )

        reset_at = window.window_start + self.window_seconds
        retry_after = max(0.0, reset_at - now)
        return RateLimitResult(
            allowed=False,
            limit=self.limit,
            remaining=max(0, self.limit - window.count),
            reset_at=reset_at,
            retry_after=round(retry_after, 3),
        )

    def peek(self, key: str) -> RateLimitResult:
        now = self._clock()
        window = self._get_or_reset(key, now)
        remaining = max(0, self.limit - window.count)
        reset_at = window.window_start + self.window_seconds
        return RateLimitResult(
            allowed=remaining >= 1,
            limit=self.limit,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=None,
        )

    def _get_or_reset(self, key: str, now: float) -> _FixedWindow:
        window = self._windows.get(key)
        if window is None or now - window.window_start >= self.window_seconds:
            window = _FixedWindow(count=0, window_start=now)
            self._windows[key] = window
        return window

    def _evict_stale(self, now: float) -> None:
        stale = [
            k
            for k, w in self._windows.items()
            if now - w.window_start >= self.window_seconds * 2
        ]
        for k in stale:
            del self._windows[k]


# ---------------------------------------------------------------------------
# Sliding window counter
# ---------------------------------------------------------------------------


@dataclass
class _SlidingState:
    prev_count: int
    prev_start: float
    curr_count: int
    curr_start: float


class SlidingWindowLimiter(_EvictionMixin):
    """Sliding-window counter rate limiter.

    Blends the previous window's count with the current window's count
    weighted by overlap fraction, eliminating boundary-burst artifacts.

    Args:
        limit: Maximum requests per window.
        window_seconds: Window duration in seconds.
        clock: Callable returning current monotonic time.
    """

    def __init__(
        self,
        limit: int,
        window_seconds: float,
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if limit <= 0:
            raise ValueError(f"limit must be positive, got {limit}")
        if window_seconds <= 0:
            raise ValueError(f"window_seconds must be positive, got {window_seconds}")
        self.limit = limit
        self.window_seconds = window_seconds
        self._clock = clock or time.monotonic
        self._states: dict[str, _SlidingState] = {}
        self._call_count = 0

    def acquire(self, key: str, tokens: int = 1) -> RateLimitResult:
        now = self._clock()
        self._maybe_evict(now)
        state = self._get_or_create(key, now)
        self._advance(state, now)

        effective = self._effective_count(state, now)
        if effective + tokens <= self.limit:
            state.curr_count += tokens
            new_effective = self._effective_count(state, now)
            remaining = max(0, self.limit - math.ceil(new_effective))
            reset_at = state.curr_start + self.window_seconds
            return RateLimitResult(
                allowed=True,
                limit=self.limit,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=None,
            )

        reset_at = state.curr_start + self.window_seconds
        retry_after = max(0.0, reset_at - now)
        remaining = max(0, self.limit - math.ceil(effective))
        return RateLimitResult(
            allowed=False,
            limit=self.limit,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=round(retry_after, 3),
        )

    def peek(self, key: str) -> RateLimitResult:
        now = self._clock()
        state = self._get_or_create(key, now)
        self._advance(state, now)
        effective = self._effective_count(state, now)
        remaining = max(0, self.limit - math.ceil(effective))
        reset_at = state.curr_start + self.window_seconds
        return RateLimitResult(
            allowed=remaining >= 1,
            limit=self.limit,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=None,
        )

    def _get_or_create(self, key: str, now: float) -> _SlidingState:
        state = self._states.get(key)
        if state is None:
            state = _SlidingState(
                prev_count=0,
                prev_start=now - self.window_seconds,
                curr_count=0,
                curr_start=now,
            )
            self._states[key] = state
        return state

    def _advance(self, state: _SlidingState, now: float) -> None:
        """Roll forward, jumping directly to the correct window."""
        if now < state.curr_start + self.window_seconds:
            return
        elapsed_windows = int((now - state.curr_start) / self.window_seconds)
        if elapsed_windows == 1:
            state.prev_count = state.curr_count
            state.prev_start = state.curr_start
            state.curr_count = 0
            state.curr_start = state.prev_start + self.window_seconds
        else:
            state.prev_count = 0
            state.prev_start = (
                state.curr_start + (elapsed_windows - 1) * self.window_seconds
            )
            state.curr_count = 0
            state.curr_start = state.prev_start + self.window_seconds

    def _effective_count(self, state: _SlidingState, now: float) -> float:
        elapsed_in_curr = now - state.curr_start
        overlap = max(0.0, 1.0 - elapsed_in_curr / self.window_seconds)
        return state.curr_count + state.prev_count * overlap

    def _evict_stale(self, now: float) -> None:
        cutoff = now - self.window_seconds * 3
        stale = [k for k, s in self._states.items() if s.curr_start < cutoff]
        for k in stale:
            del self._states[k]


# ---------------------------------------------------------------------------
# GCRA (Generic Cell Rate Algorithm)
# ---------------------------------------------------------------------------


class GCRALimiter(_EvictionMixin):
    """GCRA (Generic Cell Rate Algorithm) rate limiter.

    Maintains a single TAT (Theoretical Arrival Time) per key.
    Mathematically equivalent to a leaky bucket but with simpler state.

    Args:
        rate: Requests allowed per second.
        burst: Maximum burst size above the steady rate.
        clock: Callable returning current monotonic time.
    """

    def __init__(
        self,
        rate: float,
        burst: int = 0,
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if rate <= 0:
            raise ValueError(f"rate must be positive, got {rate}")
        if burst < 0:
            raise ValueError(f"burst must be non-negative, got {burst}")
        self.rate = rate
        self.burst = burst
        self._emission_interval = 1.0 / rate
        self._delay_tolerance = burst * self._emission_interval
        self._limit = burst + 1
        self._clock = clock or time.monotonic
        self._tats: dict[str, float] = {}
        self._call_count = 0

    def acquire(self, key: str, tokens: int = 1) -> RateLimitResult:
        now = self._clock()
        self._maybe_evict(now)
        tat = self._tats.get(key, now)
        increment = self._emission_interval * tokens

        new_tat = max(tat, now) + increment
        allow_at = new_tat - self._delay_tolerance - self._emission_interval

        if now < allow_at:
            retry_after = allow_at - now
            remaining = max(
                0,
                int((self._delay_tolerance - (tat - now)) / self._emission_interval),
            )
            return RateLimitResult(
                allowed=False,
                limit=self._limit,
                remaining=remaining,
                reset_at=tat,
                retry_after=round(retry_after, 3),
            )

        self._tats[key] = new_tat
        remaining = max(
            0,
            int((self._delay_tolerance - (new_tat - now)) / self._emission_interval),
        )
        return RateLimitResult(
            allowed=True,
            limit=self._limit,
            remaining=remaining,
            reset_at=new_tat,
            retry_after=None,
        )

    def peek(self, key: str) -> RateLimitResult:
        now = self._clock()
        tat = self._tats.get(key, now)
        remaining = max(
            0,
            int(
                (self._delay_tolerance - (max(tat, now) - now))
                / self._emission_interval
            ),
        )
        return RateLimitResult(
            allowed=remaining >= 1,
            limit=self._limit,
            remaining=remaining,
            reset_at=max(tat, now),
            retry_after=None,
        )

    def _evict_stale(self, now: float) -> None:
        stale = [k for k, tat in self._tats.items() if tat <= now]
        for k in stale:
            del self._tats[k]


# ---------------------------------------------------------------------------
# Quota string parsing
# ---------------------------------------------------------------------------

_UNIT_MAP: dict[str, float] = {
    "s": 1.0,
    "sec": 1.0,
    "second": 1.0,
    "m": 60.0,
    "min": 60.0,
    "minute": 60.0,
    "h": 3600.0,
    "hr": 3600.0,
    "hour": 3600.0,
    "d": 86400.0,
    "day": 86400.0,
}

_QUOTA_RE = re.compile(
    r"^\s*(\d+)\s*(?:/|per)\s*([a-z]+)"
    r"(?:\s+burst\s+(\d+))?\s*$",
    re.IGNORECASE,
)


def parse_quota(quota: str) -> dict[str, Any]:
    """Parse a quota string like ``"100/s"`` or ``"10 per minute burst 20"``.

    Returns:
        Dict with keys ``limit`` (int), ``period`` (float in seconds),
        and ``burst`` (int or None).
    """
    m = _QUOTA_RE.match(quota)
    if not m:
        raise ValueError(
            f"invalid quota string: {quota!r}  "
            f"(expected: '<N>/<unit>' or '<N> per <unit> [burst <B>]')"
        )
    limit = int(m.group(1))
    unit = m.group(2).lower()
    # strip trailing "s" for plurals (e.g. "seconds" -> "second") but
    # not for single-char units like "s" itself
    if len(unit) > 1 and unit.endswith("s"):
        unit = unit[:-1]
    if unit not in _UNIT_MAP:
        raise ValueError(f"unknown time unit: {m.group(2)!r}")
    period = _UNIT_MAP[unit]
    burst = int(m.group(3)) if m.group(3) else None
    return {"limit": limit, "period": period, "burst": burst}


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_ALGORITHM_MAP: dict[str, str] = {
    "token_bucket": "token_bucket",
    "fixed_window": "fixed_window",
    "sliding_window": "sliding_window",
    "gcra": "gcra",
}


def create_limiter(
    algorithm: str,
    quota: str,
    *,
    clock: Callable[[], float] | None = None,
) -> RateLimiter:
    """Create a rate limiter from an algorithm name and quota string.

    Args:
        algorithm: One of ``"token_bucket"``, ``"fixed_window"``,
            ``"sliding_window"``, or ``"gcra"``.
        quota: Quota string like ``"100/s"`` or ``"10/m burst 20"``.
        clock: Optional clock override for testing.

    Returns:
        A :class:`RateLimiter` instance.
    """
    algo = algorithm.lower()
    if algo not in _ALGORITHM_MAP:
        raise ValueError(
            f"unknown algorithm: {algorithm!r}  (choices: {', '.join(_ALGORITHM_MAP)})"
        )
    q = parse_quota(quota)
    limit, period, burst = q["limit"], q["period"], q["burst"]

    if algo == "token_bucket":
        rate = limit / period
        cap = burst if burst is not None else limit
        return TokenBucketLimiter(rate=rate, capacity=cap, clock=clock)  # type: ignore[return-value]
    elif algo == "fixed_window":
        return FixedWindowLimiter(limit=limit, window_seconds=period, clock=clock)  # type: ignore[return-value]
    elif algo == "sliding_window":
        return SlidingWindowLimiter(limit=limit, window_seconds=period, clock=clock)  # type: ignore[return-value]
    else:  # gcra
        rate = limit / period
        b = (burst - 1) if burst is not None and burst > 0 else 0
        return GCRALimiter(rate=rate, burst=b, clock=clock)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Decorator / context manager
# ---------------------------------------------------------------------------


class RateLimitExceeded(Exception):
    """Raised when a rate limit is exceeded in decorator/context-manager mode."""

    def __init__(self, result: RateLimitResult) -> None:
        self.result = result
        super().__init__(
            f"rate limit exceeded: remaining={result.remaining}, "
            f"retry_after={result.retry_after}"
        )


class ratelimit:
    """Rate-limit decorator and context manager.

    Can be used as a decorator::

        @ratelimit("10/s")
        def handle(): ...

    Or as a sync/async context manager::

        with ratelimit("5/m", key="user-1"):
            do_work()

        async with ratelimit("5/m", key="user-1"):
            await do_work()

    Args:
        quota: Quota string (e.g. ``"10/s"``, ``"100/m burst 200"``).
        algorithm: Algorithm name (default: ``"token_bucket"``).
        key: Rate-limit key (default: ``"__default__"``).
        timeout: If set, wait up to *timeout* seconds for quota
            instead of raising immediately.
        limiter: Pre-built limiter instance (overrides *quota*
            and *algorithm*).
    """

    def __init__(
        self,
        quota: str | None = None,
        *,
        algorithm: str = "token_bucket",
        key: str = "__default__",
        timeout: float | None = None,
        limiter: RateLimiter | None = None,
    ) -> None:
        if limiter is not None:
            self._limiter = limiter
        elif quota is not None:
            self._limiter = create_limiter(algorithm, quota)
        else:
            raise ValueError("either 'quota' or 'limiter' must be provided")
        self._key = key
        self._timeout = timeout

    def _acquire_or_wait(self, tokens: int = 1) -> RateLimitResult:
        result = self._limiter.acquire(self._key, tokens)
        if result.allowed:
            return result
        if self._timeout is None:
            raise RateLimitExceeded(result)

        deadline = time.monotonic() + self._timeout
        while not result.allowed:
            wait = result.retry_after or 0.1
            remaining_budget = deadline - time.monotonic()
            if remaining_budget <= 0:
                raise RateLimitExceeded(result)
            time.sleep(min(wait, remaining_budget))
            result = self._limiter.acquire(self._key, tokens)

        return result

    async def _acquire_or_wait_async(self, tokens: int = 1) -> RateLimitResult:
        result = self._limiter.acquire(self._key, tokens)
        if result.allowed:
            return result
        if self._timeout is None:
            raise RateLimitExceeded(result)

        deadline = time.monotonic() + self._timeout
        while not result.allowed:
            wait = result.retry_after or 0.1
            remaining_budget = deadline - time.monotonic()
            if remaining_budget <= 0:
                raise RateLimitExceeded(result)
            await asyncio.sleep(min(wait, remaining_budget))
            result = self._limiter.acquire(self._key, tokens)

        return result

    def __call__(self, func: Any) -> Any:
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                await self._acquire_or_wait_async()
                return await func(*args, **kwargs)

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            self._acquire_or_wait()
            return func(*args, **kwargs)

        return sync_wrapper

    def __enter__(self) -> RateLimitResult:
        return self._acquire_or_wait()

    def __exit__(self, *exc: Any) -> None:
        pass

    async def __aenter__(self) -> RateLimitResult:
        return await self._acquire_or_wait_async()

    async def __aexit__(self, *exc: Any) -> None:
        pass


# ---------------------------------------------------------------------------
# Thread-safe wrapper
# ---------------------------------------------------------------------------


class ThreadSafeLimiter:
    """Wraps any :class:`RateLimiter` with a ``threading.Lock``.

    Args:
        limiter: The underlying rate limiter.
    """

    def __init__(self, limiter: RateLimiter) -> None:
        self._limiter = limiter
        self._lock = threading.Lock()

    def acquire(self, key: str, tokens: int = 1) -> RateLimitResult:
        with self._lock:
            return self._limiter.acquire(key, tokens)

    def peek(self, key: str) -> RateLimitResult:
        with self._lock:
            return self._limiter.peek(key)
