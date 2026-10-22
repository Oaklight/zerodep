"""Benchmark: zerodep runner vs sh vs raw subprocess."""

import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from runner import run, stream

sh = pytest.importorskip("sh", reason="sh not installed")

PYTHON = sys.executable


# ── Simple command execution (echo) ──────────────────────────────────


class TestSimpleCommand:
    def test_zerodep(self, benchmark):
        def fn():
            return run(["echo", "hello"], check=False)

        benchmark(fn)

    def test_sh(self, benchmark):
        def fn():
            return sh.echo("hello")

        benchmark(fn)

    def test_subprocess(self, benchmark):
        def fn():
            return subprocess.run(
                ["echo", "hello"],
                capture_output=True,
                text=True,
            )

        benchmark(fn)


# ── Command with output capture ──────────────────────────────────────


class TestOutputCapture:
    def test_zerodep(self, benchmark):
        def fn():
            return run(
                [PYTHON, "-c", "print('line ' + str(i)) for i in range(10)"],
                check=False,
            )

        benchmark(fn)

    def test_sh(self, benchmark):
        def fn():
            return sh.Command(PYTHON)(
                "-c", "for i in range(10): print('line ' + str(i))"
            )

        benchmark(fn)

    def test_subprocess(self, benchmark):
        def fn():
            return subprocess.run(
                [PYTHON, "-c", "for i in range(10): print('line ' + str(i))"],
                capture_output=True,
                text=True,
            )

        benchmark(fn)


# ── Command with stdin ───────────────────────────────────────────────


class TestStdinInput:
    def test_zerodep(self, benchmark):
        def fn():
            return run(
                [PYTHON, "-c", "import sys; print(sys.stdin.read().upper())"],
                input="hello world",
                check=False,
            )

        benchmark(fn)

    def test_sh(self, benchmark):
        def fn():
            return sh.Command(PYTHON)(
                "-c",
                "import sys; print(sys.stdin.read().upper())",
                _in="hello world",
            )

        benchmark(fn)

    def test_subprocess(self, benchmark):
        def fn():
            return subprocess.run(
                [
                    PYTHON,
                    "-c",
                    "import sys; print(sys.stdin.read().upper())",
                ],
                input="hello world",
                capture_output=True,
                text=True,
            )

        benchmark(fn)


# ── Streaming line iteration ─────────────────────────────────────────


class TestStreamingLines:
    def test_zerodep(self, benchmark):
        def fn():
            lines = []
            with stream([PYTHON, "-c", "for i in range(20): print(i)"]) as proc:
                for line in proc.iter_lines():
                    lines.append(line)
            return lines

        benchmark(fn)

    def test_sh(self, benchmark):
        def fn():
            lines = []
            for line in sh.Command(PYTHON)(
                "-c",
                "for i in range(20): print(i)",
                _iter=True,
            ):
                lines.append(line)
            return lines

        benchmark(fn)

    def test_subprocess(self, benchmark):
        def fn():
            proc = subprocess.Popen(
                [PYTHON, "-c", "for i in range(20): print(i)"],
                stdout=subprocess.PIPE,
                text=True,
            )
            lines = []
            for line in proc.stdout:
                lines.append(line)
            proc.wait()
            return lines

        benchmark(fn)


# ── Environment variable passing ─────────────────────────────────────


class TestEnvPassing:
    def test_zerodep(self, benchmark):
        def fn():
            return run(
                [PYTHON, "-c", "import os; print(os.environ['BENCH_VAR'])"],
                env_extra={"BENCH_VAR": "test_value"},
                check=False,
            )

        benchmark(fn)

    def test_sh(self, benchmark):
        def fn():
            return sh.Command(PYTHON)(
                "-c",
                "import os; print(os.environ['BENCH_VAR'])",
                _env={**os.environ, "BENCH_VAR": "test_value"},
            )

        benchmark(fn)

    def test_subprocess(self, benchmark):
        env = {**os.environ, "BENCH_VAR": "test_value"}

        def fn():
            return subprocess.run(
                [PYTHON, "-c", "import os; print(os.environ['BENCH_VAR'])"],
                capture_output=True,
                text=True,
                env=env,
            )

        benchmark(fn)
