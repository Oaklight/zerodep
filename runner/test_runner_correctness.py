"""Correctness tests: zerodep runner."""

import asyncio
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from runner import (
    CommandBlockedError,
    CommandFailedError,
    CommandNotFoundError,
    CommandTimeoutError,
    RunnerError,
    RunResult,
    run,
    run_async,
    shell_quote,
    shell_split,
    stream,
    stream_async,
    which,
)

# ── Helpers ───────────────────────────────────────────────────────────

PYTHON = sys.executable


def _async(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


# ── Exception Hierarchy ──────────────────────────────────────────────


class TestExceptionHierarchy:
    def test_base_exception(self):
        assert issubclass(RunnerError, Exception)

    def test_command_not_found_is_runner_error(self):
        assert issubclass(CommandNotFoundError, RunnerError)

    def test_command_failed_is_runner_error(self):
        assert issubclass(CommandFailedError, RunnerError)

    def test_command_timeout_is_runner_error(self):
        assert issubclass(CommandTimeoutError, RunnerError)

    def test_command_blocked_is_runner_error(self):
        assert issubclass(CommandBlockedError, RunnerError)


# ── RunResult ─────────────────────────────────────────────────────────


class TestRunResult:
    def test_frozen(self):
        result = RunResult(
            command=("echo", "hi"),
            returncode=0,
            stdout="hi\n",
            stderr="",
            duration=0.01,
            pid=12345,
        )
        with pytest.raises(AttributeError):
            result.returncode = 1  # type: ignore[misc]

    def test_fields(self):
        result = RunResult(
            command=("ls",),
            returncode=0,
            stdout="",
            stderr="",
            duration=0.5,
            pid=999,
        )
        assert result.command == ("ls",)
        assert result.returncode == 0
        assert result.pid == 999
        assert result.duration == 0.5


# ── Basic run() ───────────────────────────────────────────────────────


class TestRunBasic:
    def test_echo(self):
        result = run(["echo", "hello", "world"])
        assert result.stdout.strip() == "hello world"
        assert result.returncode == 0
        assert result.duration > 0
        assert result.pid > 0

    def test_string_command(self):
        result = run("echo hello")
        assert result.stdout.strip() == "hello"

    def test_string_command_with_quotes(self):
        result = run(f'{PYTHON} -c "print(42)"')
        assert result.stdout.strip() == "42"

    def test_stdin_input(self):
        script = "import sys; print(sys.stdin.read().upper())"
        result = run([PYTHON, "-c", script], input="hello")
        assert result.stdout.strip() == "HELLO"

    def test_stderr_captured(self):
        result = run(
            [PYTHON, "-c", "import sys; sys.stderr.write('err\\n')"],
            check=False,
        )
        assert "err" in result.stderr

    def test_returncode_zero(self):
        result = run(["true"])
        assert result.returncode == 0

    def test_empty_command_raises(self):
        with pytest.raises(ValueError, match="Empty command"):
            run([])

    def test_empty_string_command_raises(self):
        with pytest.raises(ValueError, match="Empty command"):
            run("")

    def test_command_tuple_in_result(self):
        result = run(["echo", "a", "b"])
        assert result.command == ("echo", "a", "b")

    def test_cwd(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run(["pwd"], cwd=tmpdir)
            assert os.path.realpath(result.stdout.strip()) == os.path.realpath(tmpdir)


# ── check mode ────────────────────────────────────────────────────────


class TestRunCheck:
    def test_check_true_raises_on_failure(self):
        with pytest.raises(CommandFailedError) as exc_info:
            run(["false"], check=True)
        assert exc_info.value.result.returncode != 0

    def test_check_false_no_raise(self):
        result = run(["false"], check=False)
        assert result.returncode != 0

    def test_check_true_by_default(self):
        with pytest.raises(CommandFailedError):
            run(["false"])

    def test_failed_error_has_result(self):
        with pytest.raises(CommandFailedError) as exc_info:
            run([PYTHON, "-c", "import sys; sys.stderr.write('oops\\n'); sys.exit(1)"])
        err = exc_info.value
        assert err.result.returncode == 1
        assert "oops" in err.result.stderr


# ── Command Not Found ─────────────────────────────────────────────────


class TestCommandNotFound:
    def test_missing_command(self):
        with pytest.raises(CommandNotFoundError) as exc_info:
            run(["__nonexistent_command_xyz__"])
        assert exc_info.value.name == "__nonexistent_command_xyz__"

    def test_missing_command_is_runner_error(self):
        with pytest.raises(RunnerError):
            run(["__nonexistent_command_xyz__"])


# ── Timeout ───────────────────────────────────────────────────────────


class TestRunTimeout:
    def test_timeout_raises(self):
        with pytest.raises(CommandTimeoutError) as exc_info:
            run(
                [PYTHON, "-c", "import time; time.sleep(60)"],
                timeout=0.3,
                kill_delay=0.2,
            )
        err = exc_info.value
        assert err.timeout == 0.3
        assert PYTHON in " ".join(err.command)

    def test_no_timeout(self):
        result = run(["echo", "fast"], timeout=None)
        assert result.stdout.strip() == "fast"

    def test_timeout_partial_output(self):
        script = (
            "import sys, time; "
            "sys.stdout.write('partial\\n'); "
            "sys.stdout.flush(); time.sleep(60)"
        )
        with pytest.raises(CommandTimeoutError) as exc_info:
            run([PYTHON, "-c", script], timeout=0.5, kill_delay=0.2)
        assert "partial" in exc_info.value.partial_stdout


# ── Environment ───────────────────────────────────────────────────────


class TestRunEnvironment:
    def test_env_replacement(self):
        script = "import os; print(os.environ.get('ZERODEP_TEST', 'missing'))"
        result = run(
            [PYTHON, "-c", script],
            env={
                "ZERODEP_TEST": "found",
                "PATH": os.environ.get("PATH", ""),
            },
        )
        assert result.stdout.strip() == "found"

    def test_env_extra(self):
        script = "import os; print(os.environ.get('ZERODEP_EXTRA', 'missing'))"
        result = run(
            [PYTHON, "-c", script],
            env_extra={"ZERODEP_EXTRA": "added"},
        )
        assert result.stdout.strip() == "added"

    def test_env_remove(self):
        os.environ["ZERODEP_REMOVE_TEST"] = "secret"
        try:
            script = "import os; print(os.environ.get('ZERODEP_REMOVE_TEST', 'gone'))"
            result = run(
                [PYTHON, "-c", script],
                env_remove=["ZERODEP_REMOVE_TEST"],
            )
            assert result.stdout.strip() == "gone"
        finally:
            os.environ.pop("ZERODEP_REMOVE_TEST", None)

    def test_env_extra_and_remove_compose(self):
        os.environ["ZERODEP_COMPOSE_A"] = "old"
        try:
            script = (
                "import os; "
                "a = os.environ.get('ZERODEP_COMPOSE_A', 'gone'); "
                "b = os.environ.get('ZERODEP_COMPOSE_B', 'missing'); "
                "print(a, b)"
            )
            result = run(
                [PYTHON, "-c", script],
                env_remove=["ZERODEP_COMPOSE_A"],
                env_extra={"ZERODEP_COMPOSE_B": "new"},
            )
            output = result.stdout.strip()
            assert "gone" in output
            assert "new" in output
        finally:
            os.environ.pop("ZERODEP_COMPOSE_A", None)


# ── Streaming Callbacks ──────────────────────────────────────────────


class TestRunCallbacks:
    def test_on_stdout(self):
        lines: list[str] = []
        result = run(
            [PYTHON, "-c", "print('line1'); print('line2')"],
            on_stdout=lines.append,
        )
        assert len(lines) == 2
        assert "line1" in lines[0]
        assert "line2" in lines[1]
        # Output is still fully captured
        assert "line1" in result.stdout
        assert "line2" in result.stdout

    def test_on_stderr(self):
        lines: list[str] = []
        result = run(
            [PYTHON, "-c", "import sys; sys.stderr.write('err1\\nerr2\\n')"],
            on_stderr=lines.append,
        )
        assert len(lines) == 2
        assert "err1" in lines[0]
        assert result.stderr.count("err") == 2


# ── Command Policy ───────────────────────────────────────────────────


class TestCommandPolicy:
    def test_allowed_pass(self):
        result = run(["echo", "ok"], allowed_commands=["echo"])
        assert result.stdout.strip() == "ok"

    def test_allowed_block(self):
        with pytest.raises(CommandBlockedError) as exc_info:
            run(["echo", "no"], allowed_commands=["cat"])
        assert exc_info.value.command == "echo"
        assert "allowlist" in exc_info.value.reason

    def test_blocked_reject(self):
        with pytest.raises(CommandBlockedError) as exc_info:
            run(["rm", "-rf", "/"], blocked_commands=["rm"])
        assert exc_info.value.command == "rm"

    def test_blocked_pass(self):
        result = run(["echo", "ok"], blocked_commands=["rm"])
        assert result.stdout.strip() == "ok"


# ── stream() Context Manager ─────────────────────────────────────────


class TestStream:
    def test_iter_lines_stdout(self):
        lines = []
        with stream([PYTHON, "-c", "print('a'); print('b'); print('c')"]) as proc:
            for line in proc.iter_lines():
                lines.append(line.strip())
        assert lines == ["a", "b", "c"]
        assert proc.returncode == 0

    def test_iter_lines_stderr(self):
        script = "import sys; sys.stderr.write('e1\\ne2\\n')"
        lines = []
        with stream([PYTHON, "-c", script]) as proc:
            for line in proc.iter_lines(source="stderr"):
                lines.append(line.strip())
        assert lines == ["e1", "e2"]

    def test_iter_any(self):
        script = (
            "import sys; "
            "sys.stdout.write('out\\n'); sys.stdout.flush(); "
            "sys.stderr.write('err\\n'); sys.stderr.flush()"
        )
        items = []
        with stream([PYTHON, "-c", script]) as proc:
            for source, line in proc.iter_any():
                items.append((source, line.strip()))
        sources = {s for s, _ in items}
        assert "stdout" in sources
        assert "stderr" in sources
        assert proc.returncode == 0

    def test_pid_available(self):
        with stream(["echo", "hi"]) as proc:
            assert proc.pid > 0

    def test_cleanup_on_exception(self):
        with pytest.raises(RuntimeError):
            with stream([PYTHON, "-c", "import time; time.sleep(60)"]) as proc:
                raise RuntimeError("abort")
        # Process should be cleaned up
        assert proc.returncode is not None

    def test_command_not_found(self):
        with pytest.raises(CommandNotFoundError):
            with stream(["__nonexistent_xyz__"]):
                pass

    def test_stdin_input(self):
        lines = []
        with stream(
            [PYTHON, "-c", "import sys; print(sys.stdin.read().upper())"],
            input="hello",
        ) as proc:
            for line in proc.iter_lines():
                lines.append(line.strip())
        assert lines == ["HELLO"]


# ── run_async() ───────────────────────────────────────────────────────


class TestRunAsync:
    def test_basic(self):
        result = _async(run_async(["echo", "async_hello"]))
        assert result.stdout.strip() == "async_hello"
        assert result.returncode == 0

    def test_string_command(self):
        result = _async(run_async("echo async_str"))
        assert result.stdout.strip() == "async_str"

    def test_check_raises(self):
        with pytest.raises(CommandFailedError):
            _async(run_async(["false"]))

    def test_check_false(self):
        result = _async(run_async(["false"], check=False))
        assert result.returncode != 0

    def test_timeout(self):
        with pytest.raises(CommandTimeoutError):
            _async(
                run_async(
                    [PYTHON, "-c", "import time; time.sleep(60)"],
                    timeout=0.3,
                    kill_delay=0.2,
                )
            )

    def test_stdin_input(self):
        result = _async(
            run_async(
                [PYTHON, "-c", "import sys; print(sys.stdin.read().upper())"],
                input="async",
            )
        )
        assert result.stdout.strip() == "ASYNC"

    def test_on_stdout_callback(self):
        lines: list[str] = []
        result = _async(
            run_async(
                [PYTHON, "-c", "print('x'); print('y')"],
                on_stdout=lines.append,
            )
        )
        assert len(lines) == 2
        assert "x" in result.stdout

    def test_command_not_found(self):
        with pytest.raises(CommandNotFoundError):
            _async(run_async(["__nonexistent_async_xyz__"]))

    def test_env_extra(self):
        result = _async(
            run_async(
                [PYTHON, "-c", "import os; print(os.environ.get('ASYNC_TEST', 'no'))"],
                env_extra={"ASYNC_TEST": "yes"},
            )
        )
        assert result.stdout.strip() == "yes"


# ── stream_async() ───────────────────────────────────────────────────


class TestStreamAsync:
    def test_aiter_lines(self):
        async def _test():
            lines = []
            async with stream_async([PYTHON, "-c", "print('a1'); print('a2')"]) as proc:
                async for line in proc.aiter_lines():
                    lines.append(line.strip())
            assert lines == ["a1", "a2"]
            assert proc.returncode == 0

        _async(_test())

    def test_aiter_any(self):
        async def _test():
            script = (
                "import sys; "
                "sys.stdout.write('out\\n'); sys.stdout.flush(); "
                "sys.stderr.write('err\\n'); sys.stderr.flush()"
            )
            items = []
            async with stream_async([PYTHON, "-c", script]) as proc:
                async for source, line in proc.aiter_any():
                    items.append((source, line.strip()))
            sources = {s for s, _ in items}
            assert "stdout" in sources
            assert "stderr" in sources

        _async(_test())

    def test_cleanup_on_exception(self):
        async def _test():
            with pytest.raises(RuntimeError):
                async with stream_async(
                    [PYTHON, "-c", "import time; time.sleep(60)"]
                ) as proc:
                    raise RuntimeError("abort")
            assert proc.returncode is not None

        _async(_test())

    def test_pid_available(self):
        async def _test():
            async with stream_async(["echo", "hi"]) as proc:
                assert proc.pid > 0

        _async(_test())


# ── Utilities ─────────────────────────────────────────────────────────


class TestShellSplit:
    def test_simple(self):
        assert shell_split("echo hello world") == ["echo", "hello", "world"]

    def test_quoted(self):
        assert shell_split('echo "hello world"') == ["echo", "hello world"]

    def test_single_quoted(self):
        assert shell_split("echo 'hello world'") == ["echo", "hello world"]

    def test_empty(self):
        assert shell_split("") == []

    def test_unterminated_quote(self):
        with pytest.raises(ValueError):
            shell_split('echo "unterminated')


class TestShellQuote:
    def test_simple(self):
        quoted = shell_quote("hello")
        assert "hello" in quoted

    def test_spaces(self):
        quoted = shell_quote("hello world")
        # Should be quoted in some form
        assert len(quoted) > len("hello world")

    def test_multiple_args(self):
        quoted = shell_quote("a", "b c", "d")
        parts = quoted.split()
        assert len(parts) >= 3


class TestWhich:
    def test_existing_command(self):
        # echo might be a shell builtin, so test with python
        py_path = which("python3") or which("python")
        assert py_path is not None

    def test_missing_command(self):
        assert which("__nonexistent_command_xyz__") is None
