# /// zerodep
# version = "0.1.0"
# deps = []
# ///
"""Structured subprocess execution — zero dependencies, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Run external commands with controlled execution: timeouts with graceful
kill escalation, streaming output, environment isolation, and cross-platform
support.  Designed as a building block (Layer 1) for higher-level execution
frameworks.

Quick start::

    from runner import run

    result = run("echo hello world")
    print(result.stdout)          # "hello world\n"
    print(result.returncode)      # 0
    print(result.duration)        # 0.003  (seconds)

Streaming output::

    from runner import stream

    with stream(["make", "build"]) as proc:
        for line in proc.iter_lines():
            print(f"[build] {line}", end="")

Async execution::

    import asyncio
    from runner import run_async

    result = asyncio.run(run_async("ls -la"))

Requires Python 3.10+.
"""

# ── Imports ──────────────────────────────────────────────────────────

from __future__ import annotations

import asyncio
import dataclasses
import os
import queue
import shlex
import shutil
import subprocess
import threading
import time
from collections.abc import AsyncIterator, Callable, Iterator, Sequence
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import IO

# ── Defaults ──────────────────────────────────────────────────────────

DEFAULT_TIMEOUT: float = 30.0
DEFAULT_KILL_DELAY: float = 5.0
# Pattern 2 convention: encoding default is explicit and used consistently
# across all execution paths (sync, async, streaming).
DEFAULT_ENCODING: str = "utf-8"

_IS_WINDOWS: bool = os.name == "nt"

# ── Exceptions ────────────────────────────────────────────────────────
# Pattern 2 convention: each exception carries domain-relevant context.
# - CommandFailedError: returncode + command + key stderr
# - CommandTimeoutError: command + timeout value (+ partial output)
# - CommandNotFoundError: command name
# - CommandBlockedError: command name + reason


class RunnerError(Exception):
    """Base exception for all runner operations."""


class CommandNotFoundError(RunnerError):
    """Raised when the command binary cannot be located on PATH.

    Attributes:
        name: The command name that was not found.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Command not found: {name}")


class CommandFailedError(RunnerError):
    """Raised when a command exits with a disallowed return code.

    Attributes:
        result: The full RunResult including stdout, stderr, returncode,
            duration.
    """

    def __init__(self, result: RunResult) -> None:
        self.result = result
        cmd_str = " ".join(result.command)
        msg = f"Command failed (rc={result.returncode}): {cmd_str}"
        if result.stderr.strip():
            msg += f"\n{result.stderr.rstrip()}"
        super().__init__(msg)


class CommandTimeoutError(RunnerError):
    """Raised when a command exceeds its timeout.

    Attributes:
        command: The command that timed out.
        timeout: The timeout value in seconds.
        partial_stdout: Any stdout captured before the timeout.
        partial_stderr: Any stderr captured before the timeout.
    """

    def __init__(
        self,
        command: tuple[str, ...],
        timeout: float,
        partial_stdout: str = "",
        partial_stderr: str = "",
    ) -> None:
        self.command = command
        self.timeout = timeout
        self.partial_stdout = partial_stdout
        self.partial_stderr = partial_stderr
        cmd_str = " ".join(command)
        super().__init__(f"Command timed out after {timeout}s: {cmd_str}")


class CommandBlockedError(RunnerError):
    """Raised when a command is rejected by allowlist/blocklist policy.

    Attributes:
        command: The rejected command name.
        reason: Human-readable explanation.
    """

    def __init__(self, command: str, reason: str) -> None:
        self.command = command
        self.reason = reason
        super().__init__(f"Command blocked: {command} ({reason})")


# ── Data Models (RunResult) ───────────────────────────────────────────


@dataclasses.dataclass(frozen=True)
class RunResult:
    """Result of a completed command execution.

    Attributes:
        command: The command and arguments as a tuple.
        returncode: Process exit code.
        stdout: Captured standard output (decoded text).
        stderr: Captured standard error (decoded text).
        duration: Wall-clock execution time in seconds.
        pid: Process ID of the executed command.
    """

    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    duration: float
    pid: int


# ── Internal: Platform ────────────────────────────────────────────────


def _popen_platform_kwargs() -> dict:
    """Return platform-specific kwargs for Popen."""
    if _IS_WINDOWS:
        # CREATE_NO_WINDOW is only available on Windows
        CREATE_NO_WINDOW = 0x08000000
        return {"creationflags": CREATE_NO_WINDOW}
    return {}


def _win_quote(s: str) -> str:
    """Quote a single argument for Windows cmd.exe."""
    if not s:
        return '""'
    if not any(c in s for c in ' \t"&|<>^'):
        return s
    return '"' + s.replace('"', '""') + '"'


# ── Internal: Environment ─────────────────────────────────────────────


def _build_env(
    env: dict[str, str] | None,
    env_extra: dict[str, str] | None,
    env_remove: Sequence[str] | None,
) -> dict[str, str] | None:
    """Build the final environment dict for subprocess.

    Args:
        env: Complete replacement environment. If provided, no
            inheritance from the current process.
        env_extra: Keys to merge into the base environment.
        env_remove: Keys to strip from the base environment.

    Returns:
        The computed environment dict, or None to inherit the current
        environment unchanged.
    """
    if env is None and env_extra is None and env_remove is None:
        return None

    result = dict(env) if env is not None else os.environ.copy()

    if env_remove is not None:
        for key in env_remove:
            result.pop(key, None)

    if env_extra is not None:
        result.update(env_extra)

    return result


# ── Internal: Command Parsing ─────────────────────────────────────────


def _parse_cmd(cmd: str | Sequence[str]) -> tuple[str, ...]:
    """Normalize a command to a tuple of strings.

    Accepts either a pre-split sequence or a shell-style string that
    will be parsed with :func:`shell_split`.

    Args:
        cmd: Command as a string or sequence of strings.

    Returns:
        Tuple of command arguments.

    Raises:
        ValueError: On empty command or unterminated quotes.
    """
    if isinstance(cmd, str):
        parts = shell_split(cmd)
    else:
        parts = list(cmd)

    if not parts:
        raise ValueError("Empty command")

    return tuple(parts)


# ── Policy (allowlist/blocklist) ─────────────────────────────────────


def _check_command_policy(
    cmd_name: str,
    allowed_commands: Sequence[str] | None,
    blocked_commands: Sequence[str] | None,
) -> None:
    """Check a command against allowlist/blocklist policy.

    Args:
        cmd_name: Basename of the command to check.
        allowed_commands: If set, only these commands are permitted.
        blocked_commands: If set, these commands are rejected.

    Raises:
        CommandBlockedError: If the command violates the policy.
    """
    basename = Path(cmd_name).name

    if allowed_commands is not None:
        allowed_basenames = {Path(c).name for c in allowed_commands}
        if basename not in allowed_basenames:
            raise CommandBlockedError(
                basename,
                f"not in allowlist: {', '.join(sorted(allowed_basenames))}",
            )

    if blocked_commands is not None:
        blocked_basenames = {Path(c).name for c in blocked_commands}
        if basename in blocked_basenames:
            raise CommandBlockedError(basename, "in blocklist")


# ── Process Lifecycle Helpers (terminate, escalation) ────────────────
# Pattern 2 convention: timeout handling follows a two-stage escalation:
#   1. SIGTERM with grace period (kill_delay seconds)
#   2. SIGKILL if the process doesn't exit within the grace period
# Both sync and async variants follow this same protocol.


def _terminate_with_escalation(
    proc: subprocess.Popen,  # type: ignore[type-arg]
    kill_delay: float,
) -> None:
    """Terminate a process with SIGTERM -> SIGKILL escalation.

    Args:
        proc: The running Popen process.
        kill_delay: Seconds to wait after SIGTERM before sending SIGKILL.
    """
    proc.terminate()
    try:
        proc.wait(timeout=kill_delay)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


async def _async_terminate_with_escalation(
    proc: asyncio.subprocess.Process,
    kill_delay: float,
) -> None:
    """Async version of terminate with SIGTERM -> SIGKILL escalation.

    Args:
        proc: The running asyncio subprocess.
        kill_delay: Seconds to wait after SIGTERM before sending SIGKILL.
    """
    proc.terminate()
    try:
        await asyncio.wait_for(proc.wait(), timeout=kill_delay)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()


def _read_pipe_lines(
    pipe: IO[str],
    callback: Callable[[str], None] | None,
    buffer: list[str],
) -> None:
    """Read lines from a pipe in a background thread.

    Each line is appended to *buffer* and optionally passed to
    *callback*.

    Args:
        pipe: A readable file-like object (stdout or stderr pipe).
        callback: Optional per-line callback.
        buffer: Accumulator list for captured output.
    """
    try:
        for line in pipe:
            buffer.append(line)
            if callback is not None:
                callback(line)
    except ValueError:
        # Pipe closed
        pass


# ── Sync Execution (run) ─────────────────────────────────────────────


def run(
    cmd: str | Sequence[str],
    *,
    input: str | None = None,  # noqa: A002
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    env_extra: dict[str, str] | None = None,
    env_remove: Sequence[str] | None = None,
    timeout: float | None = DEFAULT_TIMEOUT,
    kill_delay: float = DEFAULT_KILL_DELAY,
    check: bool = True,
    encoding: str = DEFAULT_ENCODING,
    on_stdout: Callable[[str], None] | None = None,
    on_stderr: Callable[[str], None] | None = None,
    allowed_commands: Sequence[str] | None = None,
    blocked_commands: Sequence[str] | None = None,
) -> RunResult:
    """Run a command synchronously and return the result.

    Args:
        cmd: Command as a string (auto-split) or sequence of arguments.
        input: Text to send on stdin.
        cwd: Working directory for the subprocess.
        env: Complete replacement environment (no inheritance).
        env_extra: Extra variables to merge into the inherited environment.
        env_remove: Variables to strip from the inherited environment.
        timeout: Maximum seconds to wait. None means no timeout.
        kill_delay: Seconds to wait between SIGTERM and SIGKILL.
        check: If True, raise CommandFailedError on non-zero exit.
        encoding: Text encoding for stdout/stderr.
        on_stdout: Per-line callback for stdout (output is still captured).
        on_stderr: Per-line callback for stderr (output is still captured).
        allowed_commands: If set, only these command names are permitted.
        blocked_commands: If set, these command names are rejected.

    Returns:
        A RunResult with captured output, exit code, and timing.

    Raises:
        CommandNotFoundError: If the command binary is not found.
        CommandFailedError: If check=True and the exit code is non-zero.
        CommandTimeoutError: If execution exceeds *timeout*.
        CommandBlockedError: If the command violates the policy.
        ValueError: If the command is empty.
    """
    # NOTE: sync/async alignment — phase 1: command normalization
    cmd_tuple = _parse_cmd(cmd)
    # NOTE: sync/async alignment — phase 2: policy validation
    _check_command_policy(cmd_tuple[0], allowed_commands, blocked_commands)

    # NOTE: sync/async alignment — phase 3: environment building
    # (sync-only: popen_kwargs for platform flags; asyncio doesn't use them)
    computed_env = _build_env(env, env_extra, env_remove)
    popen_kwargs = _popen_platform_kwargs()

    # NOTE: sync/async alignment — phase 3b: command existence check
    # Pattern 2 convention: binary lookup via which() before process start.
    if which(cmd_tuple[0]) is None and not Path(cmd_tuple[0]).is_absolute():
        raise CommandNotFoundError(cmd_tuple[0])

    has_callbacks = on_stdout is not None or on_stderr is not None

    t0 = time.monotonic()

    # NOTE: sync/async alignment — phase 4: process startup
    # Sync uses subprocess.Popen with text-mode encoding param;
    # async uses asyncio.create_subprocess_exec with binary pipes.
    try:
        proc = subprocess.Popen(
            cmd_tuple,
            stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=computed_env,
            encoding=encoding,
            **popen_kwargs,
        )
    except FileNotFoundError as exc:
        raise CommandNotFoundError(cmd_tuple[0]) from exc

    pid = proc.pid

    # NOTE: sync/async alignment — phase 5+6: stdout/stderr collection + timeout
    try:
        if has_callbacks:
            stdout_buf: list[str] = []
            stderr_buf: list[str] = []

            stdout_thread = threading.Thread(
                target=_read_pipe_lines,
                args=(proc.stdout, on_stdout, stdout_buf),
                daemon=True,
            )
            stderr_thread = threading.Thread(
                target=_read_pipe_lines,
                args=(proc.stderr, on_stderr, stderr_buf),
                daemon=True,
            )
            stdout_thread.start()
            stderr_thread.start()

            if input is not None and proc.stdin is not None:
                proc.stdin.write(input)
                proc.stdin.close()

            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # NOTE: sync/async alignment — phase 6: timeout handling
                # Pattern 2 convention: terminate → kill escalation,
                # then raise with command + timeout value + partial output.
                _terminate_with_escalation(proc, kill_delay)
                stdout_thread.join(timeout=2)
                stderr_thread.join(timeout=2)
                assert timeout is not None
                raise CommandTimeoutError(
                    cmd_tuple,
                    timeout,
                    "".join(stdout_buf),
                    "".join(stderr_buf),
                )

            stdout_thread.join(timeout=5)
            stderr_thread.join(timeout=5)
            stdout_text = "".join(stdout_buf)
            stderr_text = "".join(stderr_buf)
        else:
            try:
                stdout_text, stderr_text = proc.communicate(
                    input=input, timeout=timeout
                )
            except subprocess.TimeoutExpired as exc:
                # NOTE: sync/async alignment — phase 6: timeout handling
                # Sync captures partial output from the TimeoutExpired
                # exception; async non-callback path does NOT — see
                # TODO(tier2) in run_async().
                _terminate_with_escalation(proc, kill_delay)
                partial_out = (
                    exc.stdout.decode(encoding)
                    if isinstance(exc.stdout, bytes)
                    else (exc.stdout or "")
                )
                partial_err = (
                    exc.stderr.decode(encoding)
                    if isinstance(exc.stderr, bytes)
                    else (exc.stderr or "")
                )
                assert timeout is not None
                raise CommandTimeoutError(
                    cmd_tuple,
                    timeout,
                    partial_out,
                    partial_err,
                )
    except CommandTimeoutError:
        raise
    # Tier 1: must-succeed — process termination on unexpected error
    except Exception:
        if proc.poll() is None:
            _terminate_with_escalation(proc, kill_delay)
        raise

    duration = time.monotonic() - t0

    # NOTE: sync/async alignment — phase 7: result construction
    result = RunResult(
        command=cmd_tuple,
        returncode=proc.returncode,
        stdout=stdout_text,
        stderr=stderr_text,
        duration=duration,
        pid=pid,
    )

    # NOTE: sync/async alignment — phase 8: non-zero exit wrapping
    # Pattern 2 convention: error includes returncode, command, key stderr.
    if check and proc.returncode != 0:
        raise CommandFailedError(result)

    return result


# ── Async Execution (run_async) ──────────────────────────────────────


async def run_async(
    cmd: str | Sequence[str],
    *,
    input: str | None = None,  # noqa: A002
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    env_extra: dict[str, str] | None = None,
    env_remove: Sequence[str] | None = None,
    timeout: float | None = DEFAULT_TIMEOUT,
    kill_delay: float = DEFAULT_KILL_DELAY,
    check: bool = True,
    encoding: str = DEFAULT_ENCODING,
    on_stdout: Callable[[str], None] | None = None,
    on_stderr: Callable[[str], None] | None = None,
    allowed_commands: Sequence[str] | None = None,
    blocked_commands: Sequence[str] | None = None,
) -> RunResult:
    """Run a command asynchronously and return the result.

    Async counterpart of :func:`run`. Uses
    ``asyncio.create_subprocess_exec`` internally.

    Args:
        cmd: Command as a string (auto-split) or sequence of arguments.
        input: Text to send on stdin.
        cwd: Working directory for the subprocess.
        env: Complete replacement environment (no inheritance).
        env_extra: Extra variables to merge into the inherited environment.
        env_remove: Variables to strip from the inherited environment.
        timeout: Maximum seconds to wait. None means no timeout.
        kill_delay: Seconds to wait between SIGTERM and SIGKILL.
        check: If True, raise CommandFailedError on non-zero exit.
        encoding: Text encoding for stdout/stderr.
        on_stdout: Per-line callback for stdout (output is still captured).
        on_stderr: Per-line callback for stderr (output is still captured).
        allowed_commands: If set, only these command names are permitted.
        blocked_commands: If set, these command names are rejected.

    Returns:
        A RunResult with captured output, exit code, and timing.

    Raises:
        CommandNotFoundError: If the command binary is not found.
        CommandFailedError: If check=True and the exit code is non-zero.
        CommandTimeoutError: If execution exceeds *timeout*.
        CommandBlockedError: If the command violates the policy.
        ValueError: If the command is empty.
    """
    # NOTE: sync/async alignment — phase 1: command normalization
    cmd_tuple = _parse_cmd(cmd)
    # NOTE: sync/async alignment — phase 2: policy validation
    _check_command_policy(cmd_tuple[0], allowed_commands, blocked_commands)

    # NOTE: sync/async alignment — phase 3: environment building
    # (no popen_kwargs — asyncio.create_subprocess_exec doesn't support
    # platform-specific creationflags; this is a sync-only concern)
    computed_env = _build_env(env, env_extra, env_remove)

    # NOTE: sync/async alignment — phase 3b: command existence check
    if which(cmd_tuple[0]) is None and not Path(cmd_tuple[0]).is_absolute():
        raise CommandNotFoundError(cmd_tuple[0])

    t0 = time.monotonic()

    # NOTE: sync/async alignment — phase 4: process startup
    # Async uses binary pipes; encoding is applied manually on read.
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd_tuple,
            stdin=(
                asyncio.subprocess.PIPE
                if input is not None
                else asyncio.subprocess.DEVNULL
            ),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=computed_env,
        )
    except FileNotFoundError as exc:
        raise CommandNotFoundError(cmd_tuple[0]) from exc

    pid = proc.pid

    has_callbacks = on_stdout is not None or on_stderr is not None
    input_bytes = input.encode(encoding) if input is not None else None

    # NOTE: sync/async alignment — phase 5+6: stdout/stderr collection + timeout
    try:
        if has_callbacks:
            stdout_buf: list[str] = []
            stderr_buf: list[str] = []

            async def _read_stream(
                stream: asyncio.StreamReader | None,
                callback: Callable[[str], None] | None,
                buf: list[str],
            ) -> None:
                if stream is None:
                    return
                while True:
                    line_bytes = await stream.readline()
                    if not line_bytes:
                        break
                    line = line_bytes.decode(encoding)
                    buf.append(line)
                    if callback is not None:
                        callback(line)

            async def _run_with_streaming() -> None:
                if input_bytes is not None and proc.stdin is not None:
                    proc.stdin.write(input_bytes)
                    await proc.stdin.drain()
                    proc.stdin.close()
                    await proc.stdin.wait_closed()

                await asyncio.gather(
                    _read_stream(proc.stdout, on_stdout, stdout_buf),
                    _read_stream(proc.stderr, on_stderr, stderr_buf),
                )
                await proc.wait()

            try:
                await asyncio.wait_for(_run_with_streaming(), timeout=timeout)
            except asyncio.TimeoutError:
                # NOTE: sync/async alignment — phase 6: timeout handling
                # Callback path captures partial output from buffers —
                # aligned with sync callback path.
                await _async_terminate_with_escalation(proc, kill_delay)
                assert timeout is not None
                raise CommandTimeoutError(
                    cmd_tuple,
                    timeout,
                    "".join(stdout_buf),
                    "".join(stderr_buf),
                )

            stdout_text = "".join(stdout_buf)
            stderr_text = "".join(stderr_buf)
        else:
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(input=input_bytes), timeout=timeout
                )
            except asyncio.TimeoutError:
                # NOTE: sync/async alignment — phase 6: timeout handling
                # asyncio.TimeoutError carries no partial output (unlike
                # subprocess.TimeoutExpired).  After killing the process,
                # drain whatever bytes remain in the pipe buffers so the
                # raised CommandTimeoutError includes partial output —
                # aligned with the sync non-callback path.
                await _async_terminate_with_escalation(proc, kill_delay)
                partial_out = ""
                partial_err = ""
                try:
                    if proc.stdout is not None:
                        raw_out = await proc.stdout.read()
                        partial_out = raw_out.decode(encoding) if raw_out else ""
                except Exception:
                    pass
                try:
                    if proc.stderr is not None:
                        raw_err = await proc.stderr.read()
                        partial_err = raw_err.decode(encoding) if raw_err else ""
                except Exception:
                    pass
                assert timeout is not None
                raise CommandTimeoutError(
                    cmd_tuple,
                    timeout,
                    partial_out,
                    partial_err,
                )

            stdout_text = stdout_bytes.decode(encoding) if stdout_bytes else ""
            stderr_text = stderr_bytes.decode(encoding) if stderr_bytes else ""
    except CommandTimeoutError:
        raise
    # Tier 1: must-succeed — async process termination on unexpected error
    except Exception:
        if proc.returncode is None:
            await _async_terminate_with_escalation(proc, kill_delay)
        raise

    duration = time.monotonic() - t0

    # NOTE: sync/async alignment — phase 7: result construction
    # Defensive fallback: returncode should always be set after communicate(),
    # but asyncio.subprocess.Process.returncode can be None if the process
    # was terminated abnormally. Sync uses proc.returncode directly.
    result = RunResult(
        command=cmd_tuple,
        returncode=proc.returncode if proc.returncode is not None else -1,
        stdout=stdout_text,
        stderr=stderr_text,
        duration=duration,
        pid=pid,
    )

    # NOTE: sync/async alignment — phase 8: non-zero exit wrapping
    if check and result.returncode != 0:
        raise CommandFailedError(result)

    return result


# ── Sync Streaming (StreamHandle, stream) ────────────────────────────


class StreamHandle:
    """Live handle to a running process for streaming output.

    Returned by the :func:`stream` context manager.  Provides iterators
    over stdout and/or stderr lines and process control methods.

    Lifecycle:
        1. **Create** — the :func:`stream` context manager starts the
           subprocess, optionally writes *input* to stdin, then yields
           this handle.  At this point the handle **owns** the process.
        2. **Yield lines** — the caller iterates via :meth:`iter_lines`
           or :meth:`iter_any`.  Lines are yielded as they arrive.
        3. **Cleanup** — when the ``with`` block exits (normally or via
           exception), :meth:`_cleanup` is called automatically.

    Process ownership:
        The handle takes exclusive ownership of the underlying
        :class:`subprocess.Popen` object.  Callers must not interact
        with the ``Popen`` directly.  The handle is responsible for
        ensuring the process is terminated when the context exits.

    Unconsumed output:
        If the caller does not fully consume stdout/stderr (e.g. breaks
        out of the iterator early), the remaining pipe data is
        discarded during cleanup.  The process is still terminated
        cleanly via :meth:`_cleanup`.

    Cleanup semantics:
        :meth:`_cleanup` checks whether the process is still running
        (via ``poll()``).  If so, it calls
        :func:`_terminate_with_escalation` (SIGTERM, then SIGKILL after
        *kill_delay* seconds).  The ``returncode`` attribute is then
        set from the process exit code.  Cleanup is invoked by the
        ``finally`` clause in :func:`stream`, so it always runs even
        if the caller raises an exception.

    Attributes:
        pid: Process ID.
    """

    def __init__(
        self,
        proc: subprocess.Popen,  # type: ignore[type-arg]
        encoding: str,
        timeout: float | None,
        kill_delay: float,
    ) -> None:
        self._proc = proc
        self._encoding = encoding
        self._timeout = timeout
        self._kill_delay = kill_delay
        self.pid: int = proc.pid
        self._returncode: int | None = None

    @property
    def returncode(self) -> int | None:
        """Exit code, available after iteration completes or process exits."""
        if self._returncode is not None:
            return self._returncode
        rc = self._proc.poll()
        if rc is not None:
            self._returncode = rc
        return self._returncode

    def iter_lines(self, *, source: str = "stdout") -> Iterator[str]:
        """Iterate over lines from stdout or stderr.

        Args:
            source: ``"stdout"`` or ``"stderr"``.

        Yields:
            Lines of text (including trailing newline).
        """
        pipe = self._proc.stdout if source == "stdout" else self._proc.stderr
        if pipe is None:
            return
        try:
            for line in pipe:
                yield line
        except ValueError:
            pass
        self._returncode = self._proc.wait()

    def iter_any(self) -> Iterator[tuple[str, str]]:
        """Iterate over interleaved lines from both stdout and stderr.

        Yields:
            Tuples of ``(source, line)`` where source is ``"stdout"``
            or ``"stderr"``.
        """
        q: queue.Queue[tuple[str, str] | None] = queue.Queue()

        def _reader(pipe: IO[str], label: str) -> None:
            try:
                for line in pipe:
                    q.put((label, line))
            except ValueError:
                # Tier 2: best-effort observable — expected on pipe close
                pass
            finally:
                q.put(None)

        threads = []
        for pipe, label in [
            (self._proc.stdout, "stdout"),
            (self._proc.stderr, "stderr"),
        ]:
            if pipe is not None:
                t = threading.Thread(target=_reader, args=(pipe, label), daemon=True)
                t.start()
                threads.append(t)

        finished = 0
        total = len(threads)
        while finished < total:
            item = q.get()
            if item is None:
                finished += 1
            else:
                yield item

        for t in threads:
            t.join(timeout=2)
        self._returncode = self._proc.wait()

    def kill(self) -> None:
        """Forcibly kill the process."""
        self._proc.kill()
        self._proc.wait()

    def _cleanup(self) -> None:
        """Ensure the process is terminated and returncode is captured.

        Called automatically by the :func:`stream` context manager on
        exit.  If the process is still running (``poll()`` returns
        ``None``), escalates through SIGTERM -> SIGKILL.  Always sets
        ``self._returncode`` from the process exit code.
        """
        if self._proc.poll() is None:
            _terminate_with_escalation(self._proc, self._kill_delay)
        self._returncode = self._proc.returncode


@contextmanager
def stream(
    cmd: str | Sequence[str],
    *,
    input: str | None = None,  # noqa: A002
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    env_extra: dict[str, str] | None = None,
    env_remove: Sequence[str] | None = None,
    timeout: float | None = None,
    kill_delay: float = DEFAULT_KILL_DELAY,
    encoding: str = DEFAULT_ENCODING,
    allowed_commands: Sequence[str] | None = None,
    blocked_commands: Sequence[str] | None = None,
) -> Iterator[StreamHandle]:
    """Context manager for streaming subprocess output.

    Yields a :class:`StreamHandle` that provides line iterators over
    stdout and stderr.  The process is automatically cleaned up on
    context exit.

    Args:
        cmd: Command as a string (auto-split) or sequence of arguments.
        input: Text to send on stdin.
        cwd: Working directory for the subprocess.
        env: Complete replacement environment (no inheritance).
        env_extra: Extra variables to merge into the inherited environment.
        env_remove: Variables to strip from the inherited environment.
        timeout: Maximum seconds for the process. None means no timeout.
        kill_delay: Seconds to wait between SIGTERM and SIGKILL.
        encoding: Text encoding for stdout/stderr.
        allowed_commands: If set, only these command names are permitted.
        blocked_commands: If set, these command names are rejected.

    Yields:
        A StreamHandle for reading process output.

    Raises:
        CommandNotFoundError: If the command binary is not found.
        CommandBlockedError: If the command violates the policy.
        ValueError: If the command is empty.
    """
    cmd_tuple = _parse_cmd(cmd)
    _check_command_policy(cmd_tuple[0], allowed_commands, blocked_commands)

    computed_env = _build_env(env, env_extra, env_remove)
    popen_kwargs = _popen_platform_kwargs()

    if which(cmd_tuple[0]) is None and not Path(cmd_tuple[0]).is_absolute():
        raise CommandNotFoundError(cmd_tuple[0])

    try:
        proc = subprocess.Popen(
            cmd_tuple,
            stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=computed_env,
            encoding=encoding,
            **popen_kwargs,
        )
    except FileNotFoundError as exc:
        raise CommandNotFoundError(cmd_tuple[0]) from exc

    if input is not None and proc.stdin is not None:
        proc.stdin.write(input)
        proc.stdin.close()

    handle = StreamHandle(proc, encoding, timeout, kill_delay)
    try:
        yield handle
    finally:
        # Tier 1: must-succeed — process cleanup
        handle._cleanup()


# ── Async Streaming (AsyncStreamHandle, stream_async) ────────────────


class AsyncStreamHandle:
    """Async live handle to a running process for streaming output.

    Returned by the :func:`stream_async` async context manager.

    Lifecycle:
        1. **Create** — :func:`stream_async` starts the subprocess via
           ``asyncio.create_subprocess_exec``, optionally writes *input*
           to stdin, then yields this handle.  The handle **owns** the
           process from this point.
        2. **Yield lines** — the caller iterates via
           :meth:`aiter_lines` or :meth:`aiter_any`.  Lines are yielded
           as they arrive from the async stream readers.
        3. **Cleanup** — when the ``async with`` block exits (normally
           or via exception), :meth:`_cleanup` is awaited automatically.

    Process ownership:
        The handle takes exclusive ownership of the underlying
        ``asyncio.subprocess.Process``.  Callers must not interact with
        the process object directly.

    Unconsumed output:
        If the caller does not fully consume stdout/stderr (e.g. breaks
        out of the async iterator early), remaining pipe data is
        discarded during cleanup.  The process is still terminated
        cleanly via :meth:`_cleanup`.

    Cleanup semantics:
        :meth:`_cleanup` checks ``proc.returncode``.  If ``None`` (the
        process is still running), it awaits
        :func:`_async_terminate_with_escalation` (SIGTERM, then SIGKILL
        after *kill_delay* seconds).  The ``returncode`` attribute is
        then set.  Cleanup is invoked by the ``finally`` clause in
        :func:`stream_async`.

    Attributes:
        pid: Process ID.
    """

    def __init__(
        self,
        proc: asyncio.subprocess.Process,
        encoding: str,
        timeout: float | None,
        kill_delay: float,
    ) -> None:
        self._proc = proc
        self._encoding = encoding
        self._timeout = timeout
        self._kill_delay = kill_delay
        self.pid: int = proc.pid  # type: ignore[assignment]
        self._returncode: int | None = None

    @property
    def returncode(self) -> int | None:
        """Exit code, available after iteration completes or process exits."""
        if self._returncode is not None:
            return self._returncode
        rc = self._proc.returncode
        if rc is not None:
            self._returncode = rc
        return self._returncode

    async def aiter_lines(self, *, source: str = "stdout") -> AsyncIterator[str]:
        """Iterate over lines from stdout or stderr.

        Args:
            source: ``"stdout"`` or ``"stderr"``.

        Yields:
            Lines of text (including trailing newline).
        """
        stream_reader = self._proc.stdout if source == "stdout" else self._proc.stderr
        if stream_reader is None:
            return
        while True:
            line_bytes = await stream_reader.readline()
            if not line_bytes:
                break
            yield line_bytes.decode(self._encoding)
        await self._proc.wait()
        self._returncode = self._proc.returncode

    async def aiter_any(self) -> AsyncIterator[tuple[str, str]]:
        """Iterate over interleaved lines from both stdout and stderr.

        Yields:
            Tuples of ``(source, line)`` where source is ``"stdout"``
            or ``"stderr"``.
        """
        q: asyncio.Queue[tuple[str, str] | None] = asyncio.Queue()

        async def _reader(
            stream_reader: asyncio.StreamReader | None, label: str
        ) -> None:
            if stream_reader is None:
                await q.put(None)
                return
            while True:
                line_bytes = await stream_reader.readline()
                if not line_bytes:
                    break
                await q.put((label, line_bytes.decode(self._encoding)))
            await q.put(None)

        tasks = [
            asyncio.create_task(_reader(self._proc.stdout, "stdout")),
            asyncio.create_task(_reader(self._proc.stderr, "stderr")),
        ]

        finished = 0
        while finished < len(tasks):
            item = await q.get()
            if item is None:
                finished += 1
            else:
                yield item

        await asyncio.gather(*tasks)
        await self._proc.wait()
        self._returncode = self._proc.returncode

    async def kill(self) -> None:
        """Forcibly kill the process."""
        self._proc.kill()
        await self._proc.wait()

    async def _cleanup(self) -> None:
        """Ensure the process is terminated and returncode is captured.

        Called automatically by the :func:`stream_async` context manager
        on exit.  If the process is still running (``returncode is
        None``), escalates through SIGTERM -> SIGKILL.  Always sets
        ``self._returncode`` from the process exit code.
        """
        if self._proc.returncode is None:
            await _async_terminate_with_escalation(self._proc, self._kill_delay)
        self._returncode = self._proc.returncode


@asynccontextmanager
async def stream_async(
    cmd: str | Sequence[str],
    *,
    input: str | None = None,  # noqa: A002
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    env_extra: dict[str, str] | None = None,
    env_remove: Sequence[str] | None = None,
    timeout: float | None = None,
    kill_delay: float = DEFAULT_KILL_DELAY,
    encoding: str = DEFAULT_ENCODING,
    allowed_commands: Sequence[str] | None = None,
    blocked_commands: Sequence[str] | None = None,
) -> AsyncIterator[AsyncStreamHandle]:
    """Async context manager for streaming subprocess output.

    Yields an :class:`AsyncStreamHandle` that provides async line
    iterators over stdout and stderr.  The process is automatically
    cleaned up on context exit.

    Args:
        cmd: Command as a string (auto-split) or sequence of arguments.
        input: Text to send on stdin.
        cwd: Working directory for the subprocess.
        env: Complete replacement environment (no inheritance).
        env_extra: Extra variables to merge into the inherited environment.
        env_remove: Variables to strip from the inherited environment.
        timeout: Maximum seconds for the process. None means no timeout.
        kill_delay: Seconds to wait between SIGTERM and SIGKILL.
        encoding: Text encoding for stdout/stderr.
        allowed_commands: If set, only these command names are permitted.
        blocked_commands: If set, these command names are rejected.

    Yields:
        An AsyncStreamHandle for reading process output.

    Raises:
        CommandNotFoundError: If the command binary is not found.
        CommandBlockedError: If the command violates the policy.
        ValueError: If the command is empty.
    """
    cmd_tuple = _parse_cmd(cmd)
    _check_command_policy(cmd_tuple[0], allowed_commands, blocked_commands)

    computed_env = _build_env(env, env_extra, env_remove)

    if which(cmd_tuple[0]) is None and not Path(cmd_tuple[0]).is_absolute():
        raise CommandNotFoundError(cmd_tuple[0])

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd_tuple,
            stdin=(
                asyncio.subprocess.PIPE
                if input is not None
                else asyncio.subprocess.DEVNULL
            ),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=computed_env,
        )
    except FileNotFoundError as exc:
        raise CommandNotFoundError(cmd_tuple[0]) from exc

    if input is not None and proc.stdin is not None:
        proc.stdin.write(input.encode(encoding))
        await proc.stdin.drain()
        proc.stdin.close()
        await proc.stdin.wait_closed()

    handle = AsyncStreamHandle(proc, encoding, timeout, kill_delay)
    try:
        yield handle
    finally:
        # Tier 1: must-succeed — async process cleanup
        await handle._cleanup()


# ── Shell Utilities ──────────────────────────────────────────────────


def shell_split(s: str) -> list[str]:
    """Split a shell command string into a list of arguments.

    Uses :func:`shlex.split` with POSIX mode on Unix and non-POSIX on
    Windows.

    Args:
        s: Shell command string, e.g. ``'git commit -m "hello world"'``.

    Returns:
        List of arguments.

    Raises:
        ValueError: On unterminated quotes or other parse errors.
    """
    return shlex.split(s, posix=not _IS_WINDOWS)


def shell_quote(*args: str) -> str:
    """Quote arguments for safe shell interpolation.

    On Unix, uses :func:`shlex.quote`.  On Windows, uses ``cmd.exe``-safe
    quoting with double-quote escaping.

    Args:
        *args: Individual arguments to quote.

    Returns:
        Space-joined quoted string.
    """
    if _IS_WINDOWS:
        return " ".join(_win_quote(a) for a in args)
    return " ".join(shlex.quote(a) for a in args)


# ── Command Discovery (which) ───────────────────────────────────────


def which(name: str) -> str | None:
    """Locate a command on the system PATH.

    Cross-platform wrapper around :func:`shutil.which`.

    Binary lookup order (Pattern 2 convention):
      1. Exact path — if *name* is absolute, return it directly if it exists.
      2. PATH search — delegates to :func:`shutil.which`, which walks
         ``os.environ["PATH"]`` entries in order, respecting PATHEXT on
         Windows.

    Args:
        name: Command name (e.g. ``"git"``).

    Returns:
        Absolute path to the binary, or ``None`` if not found.
    """
    return shutil.which(name)


# ── Public API ───────────────────────────────────────────────────────

__all__ = [
    # Data models
    "RunResult",
    # Exceptions
    "RunnerError",
    "CommandNotFoundError",
    "CommandFailedError",
    "CommandTimeoutError",
    "CommandBlockedError",
    # Sync execution
    "run",
    "stream",
    "StreamHandle",
    # Async execution
    "run_async",
    "stream_async",
    "AsyncStreamHandle",
    # Utilities
    "shell_split",
    "shell_quote",
    "which",
    # Defaults (useful for callers to reference)
    "DEFAULT_TIMEOUT",
    "DEFAULT_KILL_DELAY",
    "DEFAULT_ENCODING",
]
