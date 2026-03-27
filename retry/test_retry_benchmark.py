"""Benchmark: zerodep retry vs tenacity."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from retry import _compute_delay, retry, retry_call

tenacity = pytest.importorskip("tenacity", reason="tenacity not installed")


# ── Decorator overhead (function succeeds immediately) ──


class TestDecoratorOverhead:
    def test_zerodep(self, benchmark):
        @retry(jitter="none")
        def fn():
            return 1

        benchmark(fn)

    def test_tenacity(self, benchmark):
        @tenacity.retry(
            stop=tenacity.stop_after_attempt(4),
            wait=tenacity.wait_none(),
        )
        def fn():
            return 1

        benchmark(fn)


# ── Retry loop with failures (base_delay=0) ──


class TestRetryWithFailures:
    def _make_failing(self, n):
        state = {"calls": 0}

        def fn():
            state["calls"] += 1
            if state["calls"] <= n:
                raise RuntimeError("fail")
            return "ok"

        fn.reset = lambda: state.update(calls=0)
        return fn

    def test_zerodep(self, benchmark):
        f = self._make_failing(2)

        def run():
            f.reset()
            return retry_call(f, max_retries=3, base_delay=0, jitter="none")

        benchmark(run)

    def test_tenacity(self, benchmark):
        f = self._make_failing(2)

        @tenacity.retry(
            stop=tenacity.stop_after_attempt(4),
            wait=tenacity.wait_none(),
        )
        def wrapped():
            return f()

        def run():
            f.reset()
            return wrapped()

        benchmark(run)


# ── Backoff calculation ──


class TestBackoffCalculation:
    def test_zerodep(self, benchmark):
        def run():
            for attempt in range(10):
                _compute_delay(attempt, "exponential", 1.0, 2.0, 60.0, "full")

        benchmark(run)

    def test_tenacity(self, benchmark):
        wait = tenacity.wait_exponential(multiplier=1, max=60)

        def run():
            for attempt in range(10):
                rs = tenacity.RetryCallState(
                    retry_object=None, fn=None, args=None, kwargs=None
                )
                rs.attempt_number = attempt + 1
                wait(rs)

        benchmark(run)
