"""Benchmark: zerodep profiler vs pyinstrument."""

import cProfile
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from profiler import Profiler, TracingProfiler  # noqa: E402

pyinstrument = pytest.importorskip("pyinstrument", reason="pyinstrument not installed")


def _workload(n: int = 2000) -> int:
    total = 0
    for i in range(n):
        total += i * i
    return total


# -- TestProfilerOverhead ----------------------------------------------------


class TestProfilerOverhead:
    """Measure profiling overhead on a fixed workload."""

    N = 2000

    def test_zerodep(self, benchmark):
        def run():
            with Profiler():
                _workload(self.N)

        benchmark(run)

    def test_raw_cprofile(self, benchmark):
        def run():
            prof = cProfile.Profile()
            prof.enable()
            _workload(self.N)
            prof.disable()

        benchmark(run)

    def test_pyinstrument(self, benchmark):
        def run():
            p = pyinstrument.Profiler()
            p.start()
            _workload(self.N)
            p.stop()

        benchmark(run)


# -- TestOutputGeneration ----------------------------------------------------


class TestOutputGeneration:
    """Measure output generation speed after profiling."""

    def _make_zerodep_profiler(self) -> Profiler:
        with Profiler() as p:
            _workload(5000)
        return p

    def _make_pyinstrument_profiler(self) -> pyinstrument.Profiler:
        p = pyinstrument.Profiler()
        p.start()
        _workload(5000)
        p.stop()
        return p

    def test_zerodep_text(self, benchmark):
        p = self._make_zerodep_profiler()
        benchmark(p.output_text)

    def test_zerodep_html(self, benchmark):
        p = self._make_zerodep_profiler()
        benchmark(p.output_html)

    def test_pyinstrument_text(self, benchmark):
        p = self._make_pyinstrument_profiler()
        benchmark(p.output_text)

    def test_pyinstrument_html(self, benchmark):
        p = self._make_pyinstrument_profiler()
        benchmark(p.output_html)


# -- yappi conditional import ------------------------------------------------

try:
    import yappi as _yappi

    _HAS_YAPPI = True
except ImportError:
    _HAS_YAPPI = False


# -- TestTracingProfilerOverhead ---------------------------------------------


class TestTracingProfilerOverhead:
    """Compare TracingProfiler vs yappi overhead on the same workload."""

    N = 2000

    def test_zerodep_tracing(self, benchmark):
        def run():
            with TracingProfiler() as _p:
                _workload(self.N)

        benchmark(run)

    @pytest.mark.skipif(not _HAS_YAPPI, reason="yappi not installed")
    def test_yappi(self, benchmark):
        def run():
            _yappi.set_clock_type("wall")
            _yappi.start(builtins=False)
            _workload(self.N)
            _yappi.stop()
            _yappi.clear_stats()

        benchmark(run)


# -- TestTracingOutputGeneration ---------------------------------------------


class TestTracingOutputGeneration:
    """Compare tracing profiler output generation speed."""

    def _make_tracing_profiler(self):
        p = TracingProfiler()
        p.start()
        _workload(5000)
        p.stop()
        return p

    def test_zerodep_tracing_text(self, benchmark):
        p = self._make_tracing_profiler()
        benchmark(p.output_text)

    def test_zerodep_tracing_html_table(self, benchmark):
        p = self._make_tracing_profiler()
        benchmark(p.output_html, style="table")

    def test_zerodep_tracing_html_flamegraph(self, benchmark):
        p = self._make_tracing_profiler()
        benchmark(p.output_html, style="flamegraph")


# -- TestMultiThreadOverhead -------------------------------------------------

import threading


class TestMultiThreadOverhead:
    """Compare multi-threaded profiling overhead."""

    N = 1000

    def test_zerodep_tracing_multithread(self, benchmark):
        def run():
            with TracingProfiler() as _p:
                threads = []
                for _ in range(4):
                    t = threading.Thread(target=_workload, args=(self.N,))
                    t.start()
                    threads.append(t)
                for t in threads:
                    t.join()

        benchmark(run)

    @pytest.mark.skipif(not _HAS_YAPPI, reason="yappi not installed")
    def test_yappi_multithread(self, benchmark):
        def run():
            _yappi.set_clock_type("wall")
            _yappi.start(builtins=False)
            threads = []
            for _ in range(4):
                t = threading.Thread(target=_workload, args=(self.N,))
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
            _yappi.stop()
            _yappi.clear_stats()

        benchmark(run)
