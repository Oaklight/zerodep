"""Correctness tests: zerodep retry vs tenacity."""

import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from retry import (
    RetryError,
    RetryState,
    _compute_delay,
    retry,
    retry_call,
    retry_if_exception,
    retry_if_result,
    retry_if_status,
)

tenacity = pytest.importorskip("tenacity", reason="tenacity not installed")


# ── Helpers ──


def _make_failing(fail_times: int, exc: type[BaseException] = RuntimeError):
    """Return a callable that raises *exc* for the first *fail_times* calls."""
    state = {"calls": 0}

    def fn():
        state["calls"] += 1
        if state["calls"] <= fail_times:
            raise exc(f"fail #{state['calls']}")
        return "ok"

    fn.state = state  # type: ignore
    return fn


def _make_async_failing(fail_times: int, exc: type[BaseException] = RuntimeError):
    state = {"calls": 0}

    async def fn():
        state["calls"] += 1
        if state["calls"] <= fail_times:
            raise exc(f"fail #{state['calls']}")
        return "ok"

    fn.state = state  # type: ignore
    return fn


class _FakeHTTPError(Exception):
    """Mimics httpclient.HTTPError for testing retry_if_status."""

    def __init__(self, status_code: int):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}")


# ── Basic Retry ──


class TestBasicRetry:
    @patch("time.sleep")
    def test_succeeds_immediately(self, mock_sleep):
        @retry(jitter="none")
        def fn():
            return 42

        assert fn() == 42
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    def test_succeeds_after_failures(self, mock_sleep):
        f = _make_failing(2)
        result = retry_call(f, max_retries=3, jitter="none")
        assert result == "ok"
        assert f.state["calls"] == 3
        assert mock_sleep.call_count == 2

    @patch("time.sleep")
    def test_exhausted_raises_original(self, mock_sleep):
        f = _make_failing(10)
        with pytest.raises(RuntimeError, match="fail #4"):
            retry_call(f, max_retries=3, jitter="none")
        assert f.state["calls"] == 4

    @patch("time.sleep")
    def test_max_retries_zero(self, mock_sleep):
        f = _make_failing(1)
        with pytest.raises(RuntimeError):
            retry_call(f, max_retries=0, jitter="none")
        assert f.state["calls"] == 1
        mock_sleep.assert_not_called()


# ── Decorator Forms ──


class TestDecoratorForms:
    @patch("time.sleep")
    def test_bare_decorator(self, mock_sleep):
        @retry
        def fn():
            return "bare"

        assert fn() == "bare"

    @patch("time.sleep")
    def test_empty_parens(self, mock_sleep):
        @retry()
        def fn():
            return "parens"

        assert fn() == "parens"

    @patch("time.sleep")
    def test_with_args(self, mock_sleep):
        @retry(max_retries=5)
        def fn():
            return "args"

        assert fn() == "args"

    @patch("time.sleep")
    def test_preserves_function_metadata(self, mock_sleep):
        @retry(max_retries=1)
        def my_function():
            """My docstring."""
            return True

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."


# ── Backoff Strategies ──


class TestBackoffStrategies:
    @patch("time.sleep")
    def test_exponential_delays(self, mock_sleep):
        f = _make_failing(100)  # always fails
        with pytest.raises(RuntimeError):
            retry_call(
                f,
                max_retries=4,
                base_delay=1.0,
                backoff="exponential",
                backoff_factor=2.0,
                jitter="none",
            )
        delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert delays == [1.0, 2.0, 4.0, 8.0]

    @patch("time.sleep")
    def test_linear_delays(self, mock_sleep):
        f = _make_failing(100)
        with pytest.raises(RuntimeError):
            retry_call(
                f,
                max_retries=4,
                base_delay=1.0,
                backoff="linear",
                jitter="none",
            )
        delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert delays == [1.0, 2.0, 3.0, 4.0]

    @patch("time.sleep")
    def test_fixed_delays(self, mock_sleep):
        f = _make_failing(100)
        with pytest.raises(RuntimeError):
            retry_call(
                f,
                max_retries=3,
                base_delay=2.5,
                backoff="fixed",
                jitter="none",
            )
        delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert delays == [2.5, 2.5, 2.5]

    @patch("time.sleep")
    def test_max_delay_caps(self, mock_sleep):
        f = _make_failing(100)
        with pytest.raises(RuntimeError):
            retry_call(
                f,
                max_retries=5,
                base_delay=1.0,
                backoff="exponential",
                backoff_factor=10.0,
                max_delay=5.0,
                jitter="none",
            )
        delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert all(d <= 5.0 for d in delays)

    def test_invalid_backoff_raises(self):
        with pytest.raises(ValueError, match="Unknown backoff"):
            _compute_delay(0, "invalid", 1.0, 2.0, 60.0, "none")

    def test_invalid_jitter_raises(self):
        with pytest.raises(ValueError, match="Unknown jitter"):
            _compute_delay(0, "fixed", 1.0, 2.0, 60.0, "invalid")


# ── Jitter ──


class TestJitter:
    def test_full_jitter_range(self):
        results = [
            _compute_delay(2, "exponential", 1.0, 2.0, 60.0, "full") for _ in range(200)
        ]
        # exponential attempt=2 -> raw=4.0, full jitter -> [0, 4.0]
        assert all(0 <= d <= 4.0 for d in results)
        # Should have some spread (not all the same)
        assert max(results) - min(results) > 0.5

    def test_equal_jitter_range(self):
        results = [
            _compute_delay(2, "exponential", 1.0, 2.0, 60.0, "equal")
            for _ in range(200)
        ]
        # equal jitter -> [2.0, 4.0]
        assert all(2.0 <= d <= 4.0 for d in results)
        assert max(results) - min(results) > 0.3

    def test_no_jitter_deterministic(self):
        results = [
            _compute_delay(2, "exponential", 1.0, 2.0, 60.0, "none") for _ in range(10)
        ]
        assert all(d == 4.0 for d in results)


# ── Exception Filtering ──


class TestRetryOnExceptions:
    @patch("time.sleep")
    def test_retries_matching_exception(self, mock_sleep):
        f = _make_failing(2, ValueError)
        result = retry_call(f, max_retries=3, retry_on=(ValueError,), jitter="none")
        assert result == "ok"

    @patch("time.sleep")
    def test_no_retry_on_unmatched(self, mock_sleep):
        f = _make_failing(1, TypeError)
        with pytest.raises(TypeError):
            retry_call(f, max_retries=3, retry_on=(ValueError,), jitter="none")
        assert f.state["calls"] == 1
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    def test_retry_if_exception_helper(self, mock_sleep):
        pred = retry_if_exception(ValueError, KeyError)
        f = _make_failing(1, KeyError)
        result = retry_call(f, max_retries=2, retry_on=pred, jitter="none")
        assert result == "ok"

    @patch("time.sleep")
    def test_custom_predicate(self, mock_sleep):
        def only_runtime(exc):
            return isinstance(exc, RuntimeError) and "transient" in str(exc)

        calls = {"n": 0}

        def fn():
            calls["n"] += 1
            if calls["n"] <= 2:
                raise RuntimeError("transient error")
            return "ok"

        result = retry_call(fn, max_retries=3, retry_on=only_runtime, jitter="none")
        assert result == "ok"


# ── HTTP Status Filtering ──


class TestRetryIfStatus:
    @patch("time.sleep")
    def test_retries_on_matching_status(self, mock_sleep):
        calls = {"n": 0}

        def fn():
            calls["n"] += 1
            if calls["n"] <= 2:
                raise _FakeHTTPError(429)
            return "ok"

        result = retry_call(
            fn,
            max_retries=3,
            retry_on=retry_if_status(429, 502, 503),
            jitter="none",
        )
        assert result == "ok"
        assert calls["n"] == 3

    @patch("time.sleep")
    def test_no_retry_on_non_matching_status(self, mock_sleep):
        def fn():
            raise _FakeHTTPError(404)

        with pytest.raises(_FakeHTTPError):
            retry_call(
                fn,
                max_retries=3,
                retry_on=retry_if_status(429, 502),
                jitter="none",
            )

    @patch("time.sleep")
    def test_no_retry_on_exception_without_status(self, mock_sleep):
        def fn():
            raise ValueError("no status_code attr")

        with pytest.raises(ValueError):
            retry_call(
                fn,
                max_retries=3,
                retry_on=retry_if_status(429),
                jitter="none",
            )


# ── Result-based Retry ──


class TestRetryOnResult:
    @patch("time.sleep")
    def test_retries_on_bad_result(self, mock_sleep):
        calls = {"n": 0}

        def fn():
            calls["n"] += 1
            return None if calls["n"] <= 2 else "good"

        result = retry_call(
            fn,
            max_retries=3,
            retry_on_result=lambda r: r is None,
            jitter="none",
        )
        assert result == "good"
        assert calls["n"] == 3

    @patch("time.sleep")
    def test_exhausted_result_retry_raises(self, mock_sleep):
        def fn():
            return None

        with pytest.raises(RetryError, match="exhausted"):
            retry_call(
                fn,
                max_retries=2,
                retry_on_result=lambda r: r is None,
                jitter="none",
            )

    @patch("time.sleep")
    def test_retry_if_result_helper(self, mock_sleep):
        calls = {"n": 0}

        def fn():
            calls["n"] += 1
            return -1 if calls["n"] <= 1 else 42

        pred = retry_if_result(lambda r: r < 0)
        result = retry_call(fn, max_retries=2, retry_on_result=pred, jitter="none")
        assert result == 42


# ── on_retry Callback ──


class TestOnRetryCallback:
    @patch("time.sleep")
    def test_callback_invoked(self, mock_sleep):
        states: list[RetryState] = []
        f = _make_failing(2)
        retry_call(f, max_retries=3, on_retry=states.append, jitter="none")
        assert len(states) == 2
        assert states[0].attempt == 1
        assert states[1].attempt == 2
        assert all(isinstance(s.exception, RuntimeError) for s in states)
        assert all(s.result is None for s in states)
        assert all(s.delay >= 0 for s in states)
        assert all(s.elapsed >= 0 for s in states)

    @patch("time.sleep")
    def test_callback_result_retry(self, mock_sleep):
        states: list[RetryState] = []
        calls = {"n": 0}

        def fn():
            calls["n"] += 1
            return None if calls["n"] <= 1 else "ok"

        retry_call(
            fn,
            max_retries=2,
            retry_on_result=lambda r: r is None,
            on_retry=states.append,
            jitter="none",
        )
        assert len(states) == 1
        assert states[0].exception is None
        assert states[0].result is None  # the None return value


# ── Async Retry ──


class TestAsyncRetry:
    @pytest.mark.asyncio
    async def test_async_succeeds(self):
        @retry(jitter="none")
        async def fn():
            return "async_ok"

        assert await fn() == "async_ok"

    @pytest.mark.asyncio
    async def test_async_retries(self):
        f = _make_async_failing(2)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await retry_call(f, max_retries=3, jitter="none", base_delay=0.0)
        assert result == "ok"
        assert f.state["calls"] == 3

    @pytest.mark.asyncio
    async def test_async_exhausted(self):
        f = _make_async_failing(10)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RuntimeError):
                await retry_call(f, max_retries=2, jitter="none", base_delay=0.0)
        assert f.state["calls"] == 3

    @pytest.mark.asyncio
    async def test_async_decorator_forms(self):
        @retry
        async def bare():
            return "bare"

        @retry()
        async def parens():
            return "parens"

        @retry(max_retries=5)
        async def with_args():
            return "args"

        assert await bare() == "bare"
        assert await parens() == "parens"
        assert await with_args() == "args"

    @pytest.mark.asyncio
    async def test_async_on_retry_callback(self):
        states: list[RetryState] = []
        f = _make_async_failing(1)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await retry_call(
                f,
                max_retries=2,
                on_retry=states.append,
                jitter="none",
                base_delay=0.0,
            )
        assert len(states) == 1
        assert states[0].attempt == 1


# ── Cross-validation with tenacity ──


class TestCrossValidation:
    @patch("time.sleep")
    def test_same_retry_count(self, mock_sleep):
        """Both libraries retry the same number of times."""
        ours_calls = {"n": 0}

        def ours_fn():
            ours_calls["n"] += 1
            if ours_calls["n"] <= 3:
                raise ValueError("fail")
            return "ok"

        retry_call(ours_fn, max_retries=5, retry_on=(ValueError,), jitter="none")

        theirs_calls = {"n": 0}

        @tenacity.retry(
            stop=tenacity.stop_after_attempt(6),  # 1 initial + 5 retries
            retry=tenacity.retry_if_exception_type(ValueError),
            wait=tenacity.wait_none(),
        )
        def theirs_fn():
            theirs_calls["n"] += 1
            if theirs_calls["n"] <= 3:
                raise ValueError("fail")
            return "ok"

        theirs_fn()
        assert ours_calls["n"] == theirs_calls["n"]

    @patch("time.sleep")
    def test_both_raise_on_exhaustion(self, mock_sleep):
        """Both libraries raise after exhaustion."""
        with pytest.raises(ValueError):
            retry_call(
                _make_failing(10, ValueError),
                max_retries=2,
                retry_on=(ValueError,),
                jitter="none",
            )

        @tenacity.retry(
            stop=tenacity.stop_after_attempt(3),
            retry=tenacity.retry_if_exception_type(ValueError),
            wait=tenacity.wait_none(),
        )
        def theirs_fn():
            raise ValueError("always fails")

        with pytest.raises(tenacity.RetryError):
            theirs_fn()
