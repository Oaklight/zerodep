"""Benchmark: zerodep ptyx vs ptyprocess (POSIX pseudo-terminals).

The ConPTY backend has no row here: the benchmark workflow runs on
ubuntu-latest, and its reference (``pywinpty``) is Windows-only.  The
``bench-ptyx`` extra still pins ``pywinpty`` for a future Windows job.
"""

from __future__ import annotations

import asyncio
import os
import select
import sys
import time

import pytest

# Every case here takes the ``benchmark`` fixture. Without the plugin
# they would be reported as errors rather than skipped, which reads as a
# broken tree for anyone who installed the module without the extras.
pytest.importorskip("pytest_benchmark")

sys.path.insert(0, os.path.dirname(__file__))

from ptyx import PtyProcess  # noqa: E402

ptyprocess = pytest.importorskip("ptyprocess", reason="ptyprocess not installed")

PYTHON = sys.executable

pytestmark = pytest.mark.skipif(
    os.name == "nt", reason="ptyprocess is the POSIX reference"
)


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("COLUMNS", None)
    env.pop("LINES", None)
    return env


ENV = _env()

#: Seconds to wait for one terminal read.  A child that never writes must
#: fail its benchmark row, not stall the whole job.
DRAIN_TIMEOUT = 10.0


async def _drain(proc: PtyProcess, limit: int = 65536) -> bytes:
    """Read *proc* until end of stream or *limit* bytes."""
    out = bytearray()
    while len(out) < limit:
        chunk = await asyncio.wait_for(proc.read(4096), timeout=DRAIN_TIMEOUT)
        if not chunk:
            break
        out += chunk
    return bytes(out)


def _drain_ptyprocess(proc, limit: int = 65536) -> bytes:
    """Blocking twin of :func:`_drain` for a ptyprocess child.

    ``select`` bounds each wait so a child that never writes fails the
    benchmark instead of hanging the job.
    """
    out = bytearray()
    deadline = time.monotonic() + DRAIN_TIMEOUT
    while len(out) < limit:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("ptyprocess child produced no output in time")
        ready, _, _ = select.select([proc.fd], [], [], remaining)
        if not ready:
            raise TimeoutError("ptyprocess child produced no output in time")
        try:
            chunk = proc.read(4096)
        except EOFError:
            break
        if not chunk:
            break
        out += chunk
    return bytes(out)


# ── Spawn a child, drain the terminal, tear it down ──────────────────


class TestSpawnTeardown:
    def test_ptyx(self, benchmark):
        async def run():
            proc = await PtyProcess.spawn([PYTHON, "-c", "pass"], env=ENV)
            await _drain(proc)
            return await proc.close()

        benchmark(lambda: asyncio.run(run()))

    def test_ptyprocess(self, benchmark):
        def run():
            proc = ptyprocess.PtyProcess.spawn([PYTHON, "-c", "pass"], env=ENV)
            try:
                _drain_ptyprocess(proc)
            finally:
                if proc.isalive():
                    proc.close(force=True)

        benchmark(run)


# ── Write a line, read the child's reply, close ──────────────────────


ECHO = (
    "import sys\n"
    "line = sys.stdin.readline()\n"
    "print('GOT:' + line.strip(), flush=True)\n"
)


class TestEchoRoundTrip:
    def test_ptyx(self, benchmark):
        async def run():
            proc = await PtyProcess.spawn([PYTHON, "-c", ECHO], env=ENV)
            try:
                await proc.write(b"ping\r")
                return await _drain(proc)
            finally:
                await proc.close(grace=0.5)

        benchmark(lambda: asyncio.run(run()))

    def test_ptyprocess(self, benchmark):
        def run():
            proc = ptyprocess.PtyProcess.spawn([PYTHON, "-c", ECHO], env=ENV)
            try:
                proc.write(b"ping\r")
                return _drain_ptyprocess(proc)
            finally:
                if proc.isalive():
                    proc.close(force=True)

        benchmark(run)


# ── Move a 32 KiB payload through the terminal ───────────────────────


BULK = "import sys\nsys.stdout.write('x' * 32768)\nsys.stdout.flush()\n"


class TestBulkOutput:
    def test_ptyx(self, benchmark):
        async def run():
            proc = await PtyProcess.spawn([PYTHON, "-c", BULK], env=ENV)
            try:
                return await _drain(proc)
            finally:
                await proc.close(grace=0.5)

        benchmark(lambda: asyncio.run(run()))

    def test_ptyprocess(self, benchmark):
        def run():
            proc = ptyprocess.PtyProcess.spawn([PYTHON, "-c", BULK], env=ENV)
            try:
                return _drain_ptyprocess(proc)
            finally:
                if proc.isalive():
                    proc.close(force=True)

        benchmark(run)
