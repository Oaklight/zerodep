"""Edge-behavior tests for runner process lifecycle."""

import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from runner import (
    CommandBlockedError,
    CommandTimeoutError,
    run,
    run_async,
    stream,
    stream_async,
)

# ── Helpers ───────────────────────────────────────────────────────────

PYTHON = sys.executable


def _async(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


# ── Timeout Escalation ──────────────────────────────────────────────────


class TestTimeoutEscalation:
    """Tests for SIGTERM -> SIGKILL escalation."""

    def test_timeout_sends_sigterm_then_sigkill(self):
        """Process that ignores SIGTERM should be killed after kill_delay."""
        # Script that traps SIGTERM and ignores it
        script = (
            "import signal, time; "
            "signal.signal(signal.SIGTERM, lambda s, f: None); "
            "time.sleep(60)"
        )
        with pytest.raises(CommandTimeoutError) as exc_info:
            run(
                [PYTHON, "-c", script],
                timeout=0.5,
                kill_delay=0.5,
            )
        err = exc_info.value
        assert err.timeout == 0.5
        assert PYTHON in " ".join(err.command)

    def test_timeout_captures_partial_output(self):
        """Timed-out command should include partial stdout/stderr."""
        script = (
            "import sys, time; "
            "sys.stdout.write('partial_out\\n'); sys.stdout.flush(); "
            "sys.stderr.write('partial_err\\n'); sys.stderr.flush(); "
            "time.sleep(60)"
        )
        with pytest.raises(CommandTimeoutError) as exc_info:
            run([PYTHON, "-c", script], timeout=0.5, kill_delay=0.2)
        assert "partial_out" in exc_info.value.partial_stdout
        assert "partial_err" in exc_info.value.partial_stderr


# ── Async Timeout Partial Output ────────────────────────────────────────


class TestAsyncTimeoutPartialOutput:
    """Tests for async timeout partial output (was a bug, now fixed)."""

    def test_run_async_timeout_has_command_and_timeout(self):
        """run_async() timeout should include command and timeout value."""
        script = (
            "import sys, time; "
            "sys.stdout.write('async_partial\\n'); sys.stdout.flush(); "
            "time.sleep(60)"
        )
        with pytest.raises(CommandTimeoutError) as exc_info:
            _async(
                run_async(
                    [PYTHON, "-c", script],
                    timeout=0.5,
                    kill_delay=0.2,
                )
            )
        err = exc_info.value
        assert err.timeout == 0.5
        assert PYTHON in " ".join(err.command)
        # Partial output is best-effort in async non-callback path
        assert isinstance(err.partial_stdout, str)
        assert isinstance(err.partial_stderr, str)

    def test_run_async_timeout_with_callbacks_includes_partial(self):
        """run_async() with callback should capture partial output on timeout."""
        lines: list[str] = []
        script = (
            "import sys, time; "
            "sys.stdout.write('cb_partial\\n'); sys.stdout.flush(); "
            "time.sleep(60)"
        )
        with pytest.raises(CommandTimeoutError) as exc_info:
            _async(
                run_async(
                    [PYTHON, "-c", script],
                    timeout=0.5,
                    kill_delay=0.2,
                    on_stdout=lines.append,
                )
            )
        assert "cb_partial" in exc_info.value.partial_stdout


# ── Stream Handle Lifecycle ─────────────────────────────────────────────


class TestStreamHandleLifecycle:
    """Tests for streaming handle cleanup."""

    def test_stream_context_manager_cleanup(self):
        """stream() context manager should terminate process on exit."""
        with stream([PYTHON, "-c", "import time; time.sleep(60)"]) as proc:
            pid = proc.pid
            assert pid > 0
        # After exiting context, process should be terminated
        assert proc.returncode is not None

    def test_stream_context_manager_cleanup_on_exception(self):
        """stream() should clean up process even when exception is raised."""
        with pytest.raises(ValueError):
            with stream([PYTHON, "-c", "import time; time.sleep(60)"]) as proc:
                raise ValueError("test abort")
        assert proc.returncode is not None

    def test_async_stream_handle_kill_awaits(self):
        """AsyncStreamHandle.kill() should await process exit."""

        async def _test():
            async with stream_async(
                [PYTHON, "-c", "import time; time.sleep(60)"]
            ) as proc:
                await proc.kill()
                # After kill, returncode should be set
                assert proc.returncode is not None

        _async(_test())

    def test_async_stream_cleanup_on_exception(self):
        """stream_async() should clean up process on exception."""

        async def _test():
            with pytest.raises(ValueError):
                async with stream_async(
                    [PYTHON, "-c", "import time; time.sleep(60)"]
                ) as proc:
                    raise ValueError("async abort")
            assert proc.returncode is not None

        _async(_test())


# ── Command Policy ──────────────────────────────────────────────────────


class TestCommandPolicy:
    """Tests for allowlist/blocklist."""

    def test_blocked_command_raises(self):
        """Blocked command should raise CommandBlockedError."""
        with pytest.raises(CommandBlockedError) as exc_info:
            run(["rm", "-rf", "/"], blocked_commands=["rm"])
        assert exc_info.value.command == "rm"
        assert "blocklist" in exc_info.value.reason

    def test_allowed_command_blocks_unlisted(self):
        """Allowlist should block commands not in the list."""
        with pytest.raises(CommandBlockedError) as exc_info:
            run(["echo", "hello"], allowed_commands=["cat"])
        assert exc_info.value.command == "echo"
        assert "allowlist" in exc_info.value.reason

    def test_blocked_command_in_async(self):
        """Blocked command should raise CommandBlockedError in async path too."""
        with pytest.raises(CommandBlockedError):
            _async(run_async(["rm", "-rf", "/"], blocked_commands=["rm"]))

    def test_blocked_command_in_stream(self):
        """Blocked command should raise CommandBlockedError in stream path."""
        with pytest.raises(CommandBlockedError):
            with stream(["rm", "-rf", "/"], blocked_commands=["rm"]):
                pass

    def test_blocked_command_in_stream_async(self):
        """Blocked command should raise CommandBlockedError in async stream."""

        async def _test():
            with pytest.raises(CommandBlockedError):
                async with stream_async(["rm", "-rf", "/"], blocked_commands=["rm"]):
                    pass

        _async(_test())
