"""Correctness tests for zerodep ptyx module."""

from __future__ import annotations

import asyncio
import ctypes
import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.dirname(__file__))

import ptyx as ptyx_module  # noqa: E402
from ptyx import (  # noqa: E402
    PtyProcess,
    PtyReadError,
    PtyStartupError,
    _ConPtyProcess,
    _PosixPtyProcess,
)

IS_WINDOWS = os.name == "nt"


def _clean_env() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("COLUMNS", None)
    env.pop("LINES", None)
    return env


async def _read_all(proc: PtyProcess, limit: int = 65536) -> bytes:
    out = b""
    while len(out) < limit:
        chunk = await proc.read(4096)
        if not chunk:
            break
        out += chunk
    return out


@pytest.mark.asyncio
async def test_spawn_reads_child_output():
    proc = await PtyProcess.spawn(
        [sys.executable, "-c", "print('hello ptyx')"], env=_clean_env()
    )
    out = await _read_all(proc)
    assert b"hello ptyx" in out
    assert await proc.close() == 0


@pytest.mark.asyncio
async def test_write_round_trip():
    code = "import sys\nline = sys.stdin.readline()\nprint('GOT:' + line.strip())\n"
    proc = await PtyProcess.spawn([sys.executable, "-c", code], env=_clean_env())
    await asyncio.sleep(0.3)
    await proc.write(b"ping\r")
    out = await _read_all(proc)
    assert b"GOT:ping" in out
    await proc.close()


@pytest.mark.asyncio
async def test_resize_updates_child_view():
    code = (
        "import shutil, time\n"
        "time.sleep(0.8)\n"
        "size = shutil.get_terminal_size()\n"
        "print(f'columns={size.columns} lines={size.lines}')\n"
    )
    proc = await PtyProcess.spawn(
        [sys.executable, "-c", code], env=_clean_env(), rows=24, cols=80
    )
    proc.resize(30, 100)
    out = await _read_all(proc)
    assert b"columns=100" in out
    assert b"lines=30" in out
    await proc.close()


@pytest.mark.asyncio
async def test_close_terminates_running_child():
    proc = await PtyProcess.spawn(
        [sys.executable, "-c", "import time; time.sleep(60)"], env=_clean_env()
    )
    code = await proc.close(grace=0.5)
    assert code is not None
    assert proc.returncode is not None


@pytest.mark.asyncio
@pytest.mark.skipif(not IS_WINDOWS, reason="ConPTY backend only")
async def test_conpty_reports_same_child_process():
    comspec = os.environ.get("COMSPEC", "cmd.exe")
    proc = await PtyProcess.spawn([comspec, "/c", "echo CONPTY_OK"])
    out = await _read_all(proc)
    assert b"CONPTY_OK" in out
    await proc.close()


@pytest.mark.asyncio
@pytest.mark.skipif(IS_WINDOWS, reason="POSIX pty only")
async def test_posix_child_runs_in_own_session():
    code = (
        "import os, sys\n"
        "print('sid=' + str(os.getsid(0)))\n"
        "print('pid=' + str(os.getpid()))\n"
    )
    proc = await PtyProcess.spawn([sys.executable, "-c", code], env=_clean_env())
    out = await _read_all(proc)
    await proc.close()
    fields = dict(
        line.split("=", 1) for line in out.decode().splitlines() if "=" in line
    )
    assert fields["sid"] == fields["pid"]


@pytest.mark.asyncio
async def test_close_returns_child_exit_status():
    proc = await PtyProcess.spawn(
        [sys.executable, "-c", "raise SystemExit(3)"], env=_clean_env()
    )
    await _read_all(proc)
    assert await proc.close() == 3
    assert proc.returncode == 3


@pytest.mark.asyncio
async def test_spawn_missing_binary_raises_startup_error():
    with pytest.raises(PtyStartupError):
        await PtyProcess.spawn(["definitely-not-a-real-binary-xyz"], env=_clean_env())


@pytest.mark.asyncio
@pytest.mark.skipif(not IS_WINDOWS, reason="ConPTY backend only")
async def test_conpty_eof_when_console_keeps_writing():
    comspec = os.environ.get("COMSPEC", "cmd.exe")
    proc = await PtyProcess.spawn([comspec, "/c", "cls & exit"])
    out = await asyncio.wait_for(_read_all(proc), timeout=15)
    assert isinstance(out, bytes)
    await proc.close()


@pytest.mark.asyncio
async def test_read_after_child_exit_returns_buffered_output():
    proc = await PtyProcess.spawn(
        [sys.executable, "-c", "print('late output')"], env=_clean_env()
    )
    await asyncio.sleep(0.5)
    out = await _read_all(proc)
    assert b"late output" in out
    await proc.close()


@pytest.mark.asyncio
@pytest.mark.skipif(IS_WINDOWS, reason="POSIX pty only")
async def test_large_write_is_not_truncated():
    code = (
        "import os, tty\n"
        "tty.setraw(0)\n"
        "data = b''\n"
        "while len(data) < 32768:\n"
        "    chunk = os.read(0, 32768 - len(data))\n"
        "    if not chunk:\n"
        "        break\n"
        "    data += chunk\n"
        "print('LEN=%d' % len(data))\n"
    )
    proc = await PtyProcess.spawn([sys.executable, "-c", code], env=_clean_env())
    await asyncio.sleep(0.3)
    await proc.write(b"x" * 32768)
    out = await _read_all(proc)
    assert b"LEN=32768" in out
    await proc.close()


@pytest.mark.asyncio
@pytest.mark.skipif(IS_WINDOWS, reason="POSIX terminal-query handling")
async def test_split_terminal_query_is_answered_once():
    # Split the query across chunks and follow it with a marker, so the
    # answerer gets a second chance to match the same query.  The child
    # reads in a non-blocking loop until the marker has been processed,
    # rather than relying on the parent's drain order.
    code = (
        "import os, time, tty\n"
        "tty.setraw(0)\n"
        "os.write(1, b'\\x1b[')\n"
        "time.sleep(0.15)\n"
        "os.write(1, b'6n')\n"
        "time.sleep(0.15)\n"
        "os.write(1, b'MARK')\n"
        "time.sleep(0.15)\n"
        "os.set_blocking(0, False)\n"
        "data = b''\n"
        "for _ in range(40):\n"
        "    try:\n"
        "        part = os.read(0, 64)\n"
        "    except BlockingIOError:\n"
        "        time.sleep(0.02)\n"
        "        continue\n"
        "    if not part:\n"
        "        break\n"
        "    data += part\n"
        "print('REPLIES=%d' % data.count(b'\\x1b[1;1R'))\n"
    )
    proc = await PtyProcess.spawn([sys.executable, "-c", code], env=_clean_env())
    out = await _read_all(proc)
    assert b"REPLIES=1" in out
    await proc.close()


# ── ConPTY backpressure, pipe errors, terminal queries (#311) ──


def _conpty_stub(queue_size: int = 1) -> _ConPtyProcess:
    """Build a ConPTY backend whose reader thread has not started."""
    proc = _ConPtyProcess.__new__(_ConPtyProcess)
    proc._loop = asyncio.get_running_loop()
    proc._process = object()
    proc._pid = 0
    proc._console = object()
    proc._input = object()
    proc._output = object()
    proc._queue = asyncio.Queue(maxsize=queue_size)
    proc._buffer = bytearray()
    proc._read_error = None
    proc._eof = False
    proc._closed = False
    proc._returncode = None
    return proc


def _posix_stub(write_fd: int) -> _PosixPtyProcess:
    proc = _PosixPtyProcess.__new__(_PosixPtyProcess)
    proc._master_fd = write_fd
    proc._query_tail = b""
    return proc


@pytest.mark.asyncio
async def test_conpty_full_queue_does_not_drop_chunks(monkeypatch):
    chunks = [b"chunk-%d" % index for index in range(8)]
    state = {"index": 0}
    proc = _conpty_stub(queue_size=1)

    def fake_wait(handle, timeout):
        if state["index"] < len(chunks):
            return ptyx_module._WAIT_TIMEOUT
        return ptyx_module._WAIT_OBJECT_0

    def fake_peek(handle, buffer, size, read, available, overlapped):
        if state["index"] < len(chunks):
            available._obj.value = len(chunks[state["index"]])
        else:
            available._obj.value = 0
        return 1

    def fake_read(handle, buffer, size, read, overlapped):
        data = chunks[state["index"]]
        ctypes.memmove(buffer, data, len(data))
        read._obj.value = len(data)
        state["index"] += 1
        return 1

    monkeypatch.setattr(ptyx_module, "_WaitForSingleObject", fake_wait, raising=False)
    monkeypatch.setattr(ptyx_module, "_PeekNamedPipe", fake_peek, raising=False)
    monkeypatch.setattr(ptyx_module, "_ReadFile", fake_read, raising=False)

    reader = threading.Thread(target=proc._read_loop, daemon=True)
    reader.start()
    # Let the reader fill the one-slot queue and try to enqueue more.  The
    # old put_nowait handoff dropped these chunks.
    await asyncio.sleep(0.2)

    received: list[bytes] = []
    while True:
        item = await asyncio.wait_for(proc._queue.get(), 2.0)
        if item == b"":
            break
        received.append(item)

    # Join off the event loop: _emit() needs the loop to finish its handoff.
    await asyncio.to_thread(reader.join, 2.0)
    assert received == chunks
    assert not reader.is_alive()


@pytest.mark.asyncio
async def test_conpty_peek_failure_raises_instead_of_eof(monkeypatch):
    proc = _conpty_stub(queue_size=1)

    monkeypatch.setattr(
        ptyx_module,
        "_WaitForSingleObject",
        lambda handle, timeout: ptyx_module._WAIT_TIMEOUT,
        raising=False,
    )
    monkeypatch.setattr(ptyx_module, "_PeekNamedPipe", lambda *args: 0, raising=False)
    monkeypatch.setattr(ptyx_module, "_last_error", lambda: 5, raising=False)

    reader = threading.Thread(target=proc._read_loop, daemon=True)
    reader.start()
    with pytest.raises(PtyReadError, match="PeekNamedPipe.*WinError 5"):
        await asyncio.wait_for(proc.read(), 2.0)

    # Join off the event loop so the reader can finish its queued handoff.
    await asyncio.to_thread(reader.join, 2.0)
    assert not reader.is_alive()


@pytest.mark.asyncio
async def test_conpty_read_failure_raises_instead_of_eof(monkeypatch):
    proc = _conpty_stub(queue_size=1)

    def fake_peek(handle, buffer, size, read, available, overlapped):
        available._obj.value = 4
        return 1

    monkeypatch.setattr(
        ptyx_module,
        "_WaitForSingleObject",
        lambda handle, timeout: ptyx_module._WAIT_TIMEOUT,
        raising=False,
    )
    monkeypatch.setattr(ptyx_module, "_PeekNamedPipe", fake_peek, raising=False)
    monkeypatch.setattr(ptyx_module, "_ReadFile", lambda *args: 0, raising=False)
    # The code must be the one seen at the failing call, not a later one.
    codes = iter([109, 999])
    monkeypatch.setattr(ptyx_module, "_last_error", lambda: next(codes), raising=False)

    reader = threading.Thread(target=proc._read_loop, daemon=True)
    reader.start()
    with pytest.raises(PtyReadError, match="ReadFile.*WinError 109"):
        await asyncio.wait_for(proc.read(), 2.0)

    await asyncio.to_thread(reader.join, 2.0)
    assert not reader.is_alive()


@pytest.mark.asyncio
async def test_conpty_zero_byte_read_is_retried(monkeypatch):
    proc = _conpty_stub(queue_size=1)
    state = {"reads": 0, "done": False}

    def fake_wait(handle, timeout):
        return (
            ptyx_module._WAIT_OBJECT_0 if state["done"] else ptyx_module._WAIT_TIMEOUT
        )

    def fake_peek(handle, buffer, size, read, available, overlapped):
        available._obj.value = 0 if state["done"] else 4
        return 1

    def fake_read(handle, buffer, size, read, overlapped):
        state["reads"] += 1
        if state["reads"] == 1:
            # A zero-byte read before the child exits is not end of stream.
            read._obj.value = 0
            return 1
        ctypes.memmove(buffer, b"late", 4)
        read._obj.value = 4
        state["done"] = True
        return 1

    monkeypatch.setattr(ptyx_module, "_WaitForSingleObject", fake_wait, raising=False)
    monkeypatch.setattr(ptyx_module, "_PeekNamedPipe", fake_peek, raising=False)
    monkeypatch.setattr(ptyx_module, "_ReadFile", fake_read, raising=False)

    reader = threading.Thread(target=proc._read_loop, daemon=True)
    reader.start()
    received: list[bytes] = []
    while True:
        item = await asyncio.wait_for(proc._queue.get(), 2.0)
        if item == b"":
            break
        received.append(item)

    await asyncio.to_thread(reader.join, 2.0)
    assert received == [b"late"]
    assert not reader.is_alive()


@pytest.mark.asyncio
async def test_conpty_queue_timeout_does_not_duplicate_chunks(monkeypatch):
    chunks = [b"one", b"two", b"three"]
    state = {"index": 0}
    proc = _conpty_stub(queue_size=1)

    def fake_wait(handle, timeout):
        if state["index"] < len(chunks):
            return ptyx_module._WAIT_TIMEOUT
        return ptyx_module._WAIT_OBJECT_0

    def fake_peek(handle, buffer, size, read, available, overlapped):
        available._obj.value = (
            len(chunks[state["index"]]) if state["index"] < len(chunks) else 0
        )
        return 1

    def fake_read(handle, buffer, size, read, overlapped):
        data = chunks[state["index"]]
        ctypes.memmove(buffer, data, len(data))
        read._obj.value = len(data)
        state["index"] += 1
        return 1

    monkeypatch.setattr(ptyx_module, "_WaitForSingleObject", fake_wait, raising=False)
    monkeypatch.setattr(ptyx_module, "_PeekNamedPipe", fake_peek, raising=False)
    monkeypatch.setattr(ptyx_module, "_ReadFile", fake_read, raising=False)

    reader = threading.Thread(target=proc._read_loop, daemon=True)
    reader.start()
    # Stay idle past two 0.5 s waits so _emit() times out while blocked.
    await asyncio.sleep(1.1)

    received: list[bytes] = []
    while True:
        item = await asyncio.wait_for(proc._queue.get(), 2.0)
        if item == b"":
            break
        received.append(item)

    await asyncio.to_thread(reader.join, 2.0)
    assert received == chunks
    assert not reader.is_alive()


@pytest.mark.skipif(IS_WINDOWS, reason="POSIX terminal-query handling")
def test_cursor_position_query_gets_a_reply():
    read_fd, write_fd = os.pipe()
    try:
        proc = _posix_stub(write_fd)
        proc._answer_terminal_queries(b"before\x1b[6nafter")
        assert os.read(read_fd, 64) == b"\x1b[1;1R"
    finally:
        os.close(read_fd)
        os.close(write_fd)


@pytest.mark.skipif(IS_WINDOWS, reason="POSIX terminal-query handling")
def test_split_cursor_query_is_answered_once():
    read_fd, write_fd = os.pipe()
    try:
        proc = _posix_stub(write_fd)
        proc._answer_terminal_queries(b"\x1b[")
        proc._answer_terminal_queries(b"6n")
        proc._answer_terminal_queries(b"more")
        assert os.read(read_fd, 64) == b"\x1b[1;1R"
    finally:
        os.close(read_fd)
        os.close(write_fd)


@pytest.mark.skipif(IS_WINDOWS, reason="POSIX terminal-query handling")
def test_other_terminal_queries_get_no_reply():
    read_fd, write_fd = os.pipe()
    os.set_blocking(read_fd, False)
    try:
        proc = _posix_stub(write_fd)
        # DA1, DA2 and the kitty-keyboard query must not receive a fixed
        # reply that claims capabilities the PTY does not have.
        proc._answer_terminal_queries(b"\x1b[?u\x1b[>c\x1b[c\x1b[0c")
        with pytest.raises(BlockingIOError):
            os.read(read_fd, 64)
    finally:
        os.close(read_fd)
        os.close(write_fd)
