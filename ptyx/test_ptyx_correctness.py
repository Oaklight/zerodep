"""Correctness tests for zerodep ptyx module."""

from __future__ import annotations

import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from ptyx import PtyProcess  # noqa: E402

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
    proc.write(b"ping\r")
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
