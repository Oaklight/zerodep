# /// zerodep
# version = "0.1.0"
# deps = []
# tier = "subsystem"
# category = "terminal"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///
"""Async pseudo-terminal transport — zero dependencies, stdlib only, Python 3.10+.

Spawns a child process on a pseudo-terminal and exposes raw byte I/O.  A PTY
is what makes terminal-only programs (editor TUIs, agent CLIs) behave as they
do for a person: interactive mode, prompt rendering, and terminal queries.

The backend is selected per platform:

- POSIX: ``pty.openpty`` plus ``termios``/``fcntl``; the child runs in its own
  session so teardown can signal the whole process group.  Cursor-position and
  device-attribute queries are answered while reading so the renderer settles.
- Windows: the ConPTY API (``CreatePseudoConsole``) through :mod:`ctypes`.
  The child is created with ``STARTF_USESTDHANDLES`` and NULL standard
  handles; otherwise ``CreateProcessW`` copies the host's standard handles and
  the child writes to the host stdout instead of the pseudoconsole.  ConPTY
  answers terminal queries itself.

Quick start::

    import asyncio
    import sys
    from ptyx import PtyProcess

    async def main():
        proc = await PtyProcess.spawn([sys.executable, "-c", "print('hi')"])
        out = b""
        while chunk := await proc.read():
            out += chunk
        print(out.decode())
        print(await proc.close())

    asyncio.run(main())

Requirements:
    - Python 3.10+
    - POSIX: the ``pty`` module (present on Linux/macOS CPython)
    - Windows: Windows 10 1809 or later (ConPTY)
"""

from __future__ import annotations

import asyncio
import ctypes
import errno
import os
import signal
import struct
import subprocess
import threading
import time
from ctypes import wintypes
from typing import Any

__all__ = ["PtyProcess", "PtyStartupError"]

_IS_WINDOWS = os.name == "nt"

if not _IS_WINDOWS:  # pragma: no branch - platform-specific import
    import fcntl
    import pty as _pty
    import termios


class PtyStartupError(RuntimeError):
    """Raised when a pseudo-terminal cannot be created or the child fails."""


# ---------------------------------------------------------------------------
# Windows ConPTY bindings
# ---------------------------------------------------------------------------

_EXTENDED_STARTUPINFO_PRESENT = 0x00080000
_CREATE_UNICODE_ENVIRONMENT = 0x00000400
_CREATE_NEW_PROCESS_GROUP = 0x00000200
_STARTF_USESTDHANDLES = 0x00000100
_PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE = 0x00020016
_INFINITE = 0xFFFFFFFF
_WAIT_OBJECT_0 = 0
_WAIT_TIMEOUT = 0x00000102


class _COORD(ctypes.Structure):
    _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]


class _STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]


class _STARTUPINFOEXW(ctypes.Structure):
    _fields_ = [
        ("StartupInfo", _STARTUPINFOW),
        ("lpAttributeList", ctypes.c_void_p),
    ]


class _PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]


if _IS_WINDOWS:  # pragma: no cover - exercised on Windows only
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    _CreatePipe = _kernel32.CreatePipe
    _CreatePipe.argtypes = [
        ctypes.POINTER(wintypes.HANDLE),
        ctypes.POINTER(wintypes.HANDLE),
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    _CreatePipe.restype = wintypes.BOOL

    _CreatePseudoConsole = _kernel32.CreatePseudoConsole
    _CreatePseudoConsole.argtypes = [
        _COORD,
        wintypes.HANDLE,
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    ]
    _CreatePseudoConsole.restype = ctypes.c_long

    _ResizePseudoConsole = _kernel32.ResizePseudoConsole
    _ResizePseudoConsole.argtypes = [wintypes.HANDLE, _COORD]
    _ResizePseudoConsole.restype = ctypes.c_long

    _ClosePseudoConsole = _kernel32.ClosePseudoConsole
    _ClosePseudoConsole.argtypes = [wintypes.HANDLE]
    _ClosePseudoConsole.restype = None

    _InitializeProcThreadAttributeList = _kernel32.InitializeProcThreadAttributeList
    _InitializeProcThreadAttributeList.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    _InitializeProcThreadAttributeList.restype = wintypes.BOOL

    _UpdateProcThreadAttribute = _kernel32.UpdateProcThreadAttribute
    _UpdateProcThreadAttribute.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    _UpdateProcThreadAttribute.restype = wintypes.BOOL

    _DeleteProcThreadAttributeList = _kernel32.DeleteProcThreadAttributeList
    _DeleteProcThreadAttributeList.argtypes = [ctypes.c_void_p]
    _DeleteProcThreadAttributeList.restype = None

    _CreateProcessW = _kernel32.CreateProcessW
    _CreateProcessW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.BOOL,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.LPCWSTR,
        ctypes.POINTER(_STARTUPINFOW),
        ctypes.POINTER(_PROCESS_INFORMATION),
    ]
    _CreateProcessW.restype = wintypes.BOOL

    _WaitForSingleObject = _kernel32.WaitForSingleObject
    _WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    _WaitForSingleObject.restype = wintypes.DWORD

    _GetExitCodeProcess = _kernel32.GetExitCodeProcess
    _GetExitCodeProcess.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.DWORD),
    ]
    _GetExitCodeProcess.restype = wintypes.BOOL

    _TerminateProcess = _kernel32.TerminateProcess
    _TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    _TerminateProcess.restype = wintypes.BOOL

    _CloseHandle = _kernel32.CloseHandle
    _CloseHandle.argtypes = [wintypes.HANDLE]
    _CloseHandle.restype = wintypes.BOOL

    _ReadFile = _kernel32.ReadFile
    _ReadFile.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.c_void_p,
    ]
    _ReadFile.restype = wintypes.BOOL

    _WriteFile = _kernel32.WriteFile
    _WriteFile.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.c_void_p,
    ]
    _WriteFile.restype = wintypes.BOOL

    _PeekNamedPipe = _kernel32.PeekNamedPipe
    _PeekNamedPipe.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
    ]
    _PeekNamedPipe.restype = wintypes.BOOL


def _win_error(prefix: str) -> PtyStartupError:
    err = getattr(ctypes, "WinError")()  # noqa: B009 - Windows only
    return PtyStartupError(f"{prefix}: {err}")


def _environment_block(env: dict[str, str]) -> Any:
    """Build a UTF-16 environment block for ``CreateProcessW``."""
    items = [
        f"{key}={value}"
        for key, value in sorted(env.items(), key=lambda item: item[0].upper())
    ]
    return ctypes.create_unicode_buffer("\0".join(items) + "\0\0")


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


class PtyProcess:
    """A child process attached to a pseudo-terminal."""

    @classmethod
    async def spawn(
        cls,
        argv: list[str],
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        rows: int = 50,
        cols: int = 200,
    ) -> PtyProcess:
        """Start *argv* on a new pseudo-terminal.

        Args:
            argv: Command and arguments.
            cwd: Working directory for the child.
            env: Complete environment for the child; ``None`` inherits.
            rows: Initial terminal height in characters.
            cols: Initial terminal width in characters.

        Returns:
            A connected :class:`PtyProcess`.

        Raises:
            PtyStartupError: If the pseudo-terminal or child cannot be
                created.
        """
        if _IS_WINDOWS:
            return await _ConPtyProcess._spawn(
                argv, cwd=cwd, env=env, rows=rows, cols=cols
            )
        return await _PosixPtyProcess._spawn(
            argv, cwd=cwd, env=env, rows=rows, cols=cols
        )

    @property
    def pid(self) -> int:
        """Child process id."""
        raise NotImplementedError

    @property
    def returncode(self) -> int | None:
        """Exit status, or ``None`` while the child runs."""
        raise NotImplementedError

    async def read(self, size: int = 65536) -> bytes:
        """Read one chunk of terminal output; ``b""`` at end of file."""
        raise NotImplementedError

    def write(self, data: bytes) -> None:
        """Write raw bytes to the terminal."""
        raise NotImplementedError

    def resize(self, rows: int, cols: int) -> None:
        """Resize the terminal."""
        raise NotImplementedError

    async def wait(self) -> int:
        """Wait for the child to exit and return its status."""
        raise NotImplementedError

    async def close(self, *, grace: float = 3.0) -> int | None:
        """Terminate the child and release the terminal.

        Asks the child to stop, waits up to *grace* seconds, then forces it.
        Safe to call more than once.

        Returns:
            The child's exit status, if it has exited.
        """
        raise NotImplementedError

    async def __aenter__(self) -> PtyProcess:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()


# ---------------------------------------------------------------------------
# POSIX backend
# ---------------------------------------------------------------------------


class _PosixPtyProcess(PtyProcess):
    def __init__(
        self,
        proc: asyncio.subprocess.Process,
        master_fd: int,
        reader: asyncio.StreamReader,
        transport: asyncio.BaseTransport,
        pipe: Any,
    ) -> None:
        self._proc = proc
        self._master_fd = master_fd
        self._reader = reader
        self._transport = transport
        self._pipe = pipe
        self._closed = False

    @property
    def pid(self) -> int:
        return self._proc.pid

    @property
    def returncode(self) -> int | None:
        return self._proc.returncode

    @classmethod
    async def _spawn(
        cls,
        argv: list[str],
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        rows: int = 50,
        cols: int = 200,
    ) -> _PosixPtyProcess:
        try:
            master_fd, slave_fd = _pty.openpty()
        except OSError as exc:
            raise PtyStartupError(f"cannot open a PTY: {exc}") from exc
        cls._set_winsize(master_fd, rows, cols)
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                cwd=cwd,
                env=env,
                start_new_session=True,
                close_fds=True,
            )
        except BaseException:
            os.close(master_fd)
            os.close(slave_fd)
            raise
        os.close(slave_fd)

        loop = asyncio.get_running_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        pipe = os.fdopen(master_fd, "rb", buffering=0)
        try:
            transport, _ = await loop.connect_read_pipe(lambda: protocol, pipe)
        except BaseException:
            pipe.close()
            proc.kill()
            await proc.wait()
            raise
        return cls(proc, master_fd, reader, transport, pipe)

    async def read(self, size: int = 65536) -> bytes:
        try:
            chunk = await self._reader.read(size)
        except OSError as exc:
            if exc.errno == errno.EIO:
                return b""
            raise
        if chunk:
            self._answer_terminal_queries(chunk)
        return chunk

    def write(self, data: bytes) -> None:
        if self._closed:
            return
        try:
            os.write(self._master_fd, data)
        except OSError:
            pass

    def resize(self, rows: int, cols: int) -> None:
        if not self._closed:
            self._set_winsize(self._master_fd, rows, cols)

    async def wait(self) -> int:
        return await self._proc.wait()

    async def close(self, *, grace: float = 3.0) -> int | None:
        if self._closed:
            return self._proc.returncode
        self._closed = True
        if self._proc.returncode is None:
            try:
                os.killpg(self._proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                await asyncio.wait_for(self._proc.wait(), grace)
            except asyncio.TimeoutError:
                try:
                    os.killpg(self._proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    await asyncio.wait_for(self._proc.wait(), 2.0)
                except asyncio.TimeoutError:
                    pass
        try:
            self._transport.close()
        except Exception:  # noqa: BLE001 - best-effort teardown
            pass
        try:
            self._pipe.close()
        except Exception:  # noqa: BLE001 - best-effort teardown
            pass
        return self._proc.returncode

    def _answer_terminal_queries(self, chunk: bytes) -> None:
        if b"\x1b[6n" in chunk:
            self.write(b"\x1b[1;1R")
        if b"\x1b[c" in chunk or b"\x1b[0c" in chunk:
            self.write(b"\x1b[?62;c")

    @staticmethod
    def _set_winsize(fd: int, rows: int, cols: int) -> None:
        try:
            fcntl.ioctl(
                fd,
                termios.TIOCSWINSZ,
                struct.pack("HHHH", rows, cols, 0, 0),
            )
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Windows ConPTY backend
# ---------------------------------------------------------------------------


class _ConPtyProcess(PtyProcess):
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        process: wintypes.HANDLE,
        pid: int,
        console: wintypes.HANDLE,
        input_handle: wintypes.HANDLE,
        output_handle: wintypes.HANDLE,
    ) -> None:
        self._loop = loop
        self._process = process
        self._pid = pid
        self._console = console
        self._input = input_handle
        self._output = output_handle
        self._queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._buffer = bytearray()
        self._eof = False
        self._closed = False
        self._returncode: int | None = None
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def returncode(self) -> int | None:
        return self._returncode

    @classmethod
    async def _spawn(
        cls,
        argv: list[str],
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        rows: int = 50,
        cols: int = 200,
    ) -> _ConPtyProcess:
        input_read = wintypes.HANDLE()
        input_write = wintypes.HANDLE()
        output_read = wintypes.HANDLE()
        output_write = wintypes.HANDLE()
        if not _CreatePipe(
            ctypes.byref(input_read), ctypes.byref(input_write), None, 0
        ):
            raise _win_error("CreatePipe(input) failed")
        if not _CreatePipe(
            ctypes.byref(output_read), ctypes.byref(output_write), None, 0
        ):
            _CloseHandle(input_read)
            _CloseHandle(input_write)
            raise _win_error("CreatePipe(output) failed")

        console = wintypes.HANDLE()
        hr = _CreatePseudoConsole(
            _COORD(cols, rows),
            input_read,
            output_write,
            0,
            ctypes.byref(console),
        )
        if hr != 0:
            for handle in (input_read, input_write, output_read, output_write):
                _CloseHandle(handle)
            raise PtyStartupError(
                f"CreatePseudoConsole failed: 0x{hr & 0xFFFFFFFF:08X}"
            )

        size = ctypes.c_size_t(0)
        _InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(size))
        attribute_buffer = ctypes.create_string_buffer(size.value)
        attributes = ctypes.cast(attribute_buffer, ctypes.c_void_p)
        if not _InitializeProcThreadAttributeList(attributes, 1, 0, ctypes.byref(size)):
            _cleanup_spawn(console, input_read, input_write, output_read, output_write)
            raise _win_error("InitializeProcThreadAttributeList failed")
        if not _UpdateProcThreadAttribute(
            attributes,
            0,
            _PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE,
            ctypes.cast(console, ctypes.c_void_p),
            ctypes.sizeof(wintypes.HANDLE),
            None,
            None,
        ):
            _DeleteProcThreadAttributeList(attributes)
            _cleanup_spawn(console, input_read, input_write, output_read, output_write)
            raise _win_error("UpdateProcThreadAttribute failed")

        startup = _STARTUPINFOEXW()
        startup.StartupInfo.cb = ctypes.sizeof(_STARTUPINFOEXW)
        startup.StartupInfo.dwFlags = _STARTF_USESTDHANDLES
        startup.lpAttributeList = attributes
        process_info = _PROCESS_INFORMATION()
        command_line = ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
        env_block = _environment_block(env) if env is not None else None
        env_pointer = (
            ctypes.cast(env_block, ctypes.c_void_p) if env_block is not None else None
        )
        created = _CreateProcessW(
            None,
            command_line,
            None,
            None,
            False,
            _EXTENDED_STARTUPINFO_PRESENT
            | _CREATE_UNICODE_ENVIRONMENT
            | _CREATE_NEW_PROCESS_GROUP,
            env_pointer,
            cwd,
            ctypes.cast(ctypes.pointer(startup), ctypes.POINTER(_STARTUPINFOW)),
            ctypes.byref(process_info),
        )
        _DeleteProcThreadAttributeList(attributes)
        # The pseudoconsole owns these ends once the child exists.
        _CloseHandle(input_read)
        _CloseHandle(output_write)
        _CloseHandle(process_info.hThread)
        if not created:
            _CloseHandle(input_write)
            _CloseHandle(output_read)
            _ClosePseudoConsole(console)
            raise _win_error("CreateProcessW failed")

        return cls(
            asyncio.get_running_loop(),
            process_info.hProcess,
            int(process_info.dwProcessId),
            console,
            input_write,
            output_read,
        )

    async def read(self, size: int = 65536) -> bytes:
        if self._buffer:
            return self._take(size)
        if self._eof:
            return b""
        item = await self._queue.get()
        if not item:
            self._eof = True
            return b""
        self._buffer.extend(item)
        return self._take(size)

    def write(self, data: bytes) -> None:
        if self._closed or not data:
            return
        self._write_raw(data)

    def resize(self, rows: int, cols: int) -> None:
        if not self._closed:
            _ResizePseudoConsole(self._console, _COORD(cols, rows))

    async def wait(self) -> int:
        if self._returncode is not None:
            return self._returncode
        self._returncode = await asyncio.to_thread(self._wait_blocking)
        return self._returncode

    async def close(self, *, grace: float = 3.0) -> int | None:
        if self._closed:
            return self._returncode
        self._closed = True
        self._returncode = await asyncio.to_thread(self._close_blocking, grace)
        return self._returncode

    def _take(self, size: int) -> bytes:
        chunk = bytes(self._buffer[:size])
        del self._buffer[:size]
        return chunk

    def _write_raw(self, data: bytes) -> None:
        buffer = ctypes.create_string_buffer(data, len(data))
        written = wintypes.DWORD(0)
        _WriteFile(
            self._input,
            buffer,
            len(data),
            ctypes.byref(written),
            None,
        )

    def _read_loop(self) -> None:
        """Drain the output pipe and report EOF once the child is gone.

        ConPTY keeps the pipe open after the child exits (the console host
        owns the other end until ``ClosePseudoConsole``), so the loop peeks
        instead of blocking in ``ReadFile``: output is drained first, then
        ``b""`` is queued when the process has exited and no bytes remain.
        """
        buffer = ctypes.create_string_buffer(65536)
        exited = False
        while True:
            available = wintypes.DWORD(0)
            if not _PeekNamedPipe(
                self._output,
                None,
                0,
                None,
                ctypes.byref(available),
                None,
            ):
                break
            if available.value:
                read = wintypes.DWORD(0)
                ok = _ReadFile(
                    self._output,
                    buffer,
                    min(available.value, 65536),
                    ctypes.byref(read),
                    None,
                )
                if not ok or read.value == 0:
                    break
                chunk = bytes(buffer.raw[: read.value])
                try:
                    self._loop.call_soon_threadsafe(self._queue.put_nowait, chunk)
                except RuntimeError:
                    return
                continue
            if not exited and _WaitForSingleObject(self._process, 0) == _WAIT_OBJECT_0:
                exited = True
                time.sleep(0.1)
                continue
            if exited:
                break
            time.sleep(0.01)
        try:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, b"")
        except RuntimeError:
            pass

    def _wait_blocking(self) -> int:
        _WaitForSingleObject(self._process, _INFINITE)
        return self._exit_code()

    def _close_blocking(self, grace: float) -> int:
        if self._returncode is None:
            self._write_raw(b"\x03")
            waited = _WaitForSingleObject(self._process, int(grace * 1000))
            if waited == _WAIT_TIMEOUT:
                _TerminateProcess(self._process, 1)
                _WaitForSingleObject(self._process, 5000)
        _ClosePseudoConsole(self._console)
        self._reader.join(timeout=5.0)
        for handle in (self._input, self._output, self._process):
            _CloseHandle(handle)
        return self._exit_code()

    def _exit_code(self) -> int:
        code = wintypes.DWORD(0)
        _GetExitCodeProcess(self._process, ctypes.byref(code))
        return int(code.value)


def _cleanup_spawn(
    console: wintypes.HANDLE,
    input_read: wintypes.HANDLE,
    input_write: wintypes.HANDLE,
    output_read: wintypes.HANDLE,
    output_write: wintypes.HANDLE,
) -> None:
    _ClosePseudoConsole(console)
    for handle in (input_read, input_write, output_read, output_write):
        _CloseHandle(handle)
