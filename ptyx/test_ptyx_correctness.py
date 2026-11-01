"""Correctness tests for zerodep ptyx module."""

from __future__ import annotations

import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from ptyx import PtyProcess, PtyStartupError  # noqa: E402

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
