"""Benchmark: zerodep persistdict vs shelve vs sqlitedict.

Measures write, read, iterate, and mixed workload throughput for
the JSON and SQLite backends, compared against stdlib shelve and
the popular sqlitedict library.
"""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from persistdict import open as pd_open

# ── Reference implementations ──

import shelve

try:
    from sqlitedict import SqliteDict

    HAS_SQLITEDICT = True
except ImportError:
    HAS_SQLITEDICT = False


# ── Helpers ──

SMALL_N = 50
MEDIUM_N = 500
LARGE_N = 2000


def _small_data():
    return {f"key_{i}": {"index": i, "name": f"item_{i}"} for i in range(SMALL_N)}


def _medium_data():
    return {f"key_{i}": {"index": i, "name": f"item_{i}", "tags": ["a", "b"]} for i in range(MEDIUM_N)}


def _large_data():
    return {
        f"key_{i}": {"index": i, "name": f"item_{i}", "tags": [f"t{j}" for j in range(5)], "active": i % 2 == 0}
        for i in range(LARGE_N)
    }


# ============================================================================
# Write benchmarks
# ============================================================================


class TestWriteSmall:
    def test_zerodep_json(self, benchmark, tmp_path):
        path = str(tmp_path / "bench.json")

        def run():
            d = pd_open(path)
            for k, v in _small_data().items():
                d[k] = v
            d.close()
            os.unlink(path)

        benchmark(run)

    def test_zerodep_sqlite(self, benchmark, tmp_path):
        path = str(tmp_path / "bench.db")

        def run():
            d = pd_open(path)
            for k, v in _small_data().items():
                d[k] = v
            d.close()
            os.unlink(path)

        benchmark(run)

    def test_shelve(self, benchmark, tmp_path):
        path = str(tmp_path / "bench_shelve")

        def run():
            with shelve.open(path) as d:
                for k, v in _small_data().items():
                    d[k] = v
            for ext in (".db", ".dir", ".bak", ".dat"):
                p = path + ext
                if os.path.exists(p):
                    os.unlink(p)

        benchmark(run)

    @pytest.mark.skipif(not HAS_SQLITEDICT, reason="sqlitedict not installed")
    def test_sqlitedict(self, benchmark, tmp_path):
        path = str(tmp_path / "bench_sd.db")

        def run():
            with SqliteDict(path, autocommit=True) as d:
                for k, v in _small_data().items():
                    d[k] = v
            os.unlink(path)

        benchmark(run)


class TestWriteLarge:
    def test_zerodep_json(self, benchmark, tmp_path):
        path = str(tmp_path / "bench.json")

        def run():
            d = pd_open(path)
            for k, v in _large_data().items():
                d[k] = v
            d.close()
            os.unlink(path)

        benchmark(run)

    def test_zerodep_sqlite(self, benchmark, tmp_path):
        path = str(tmp_path / "bench.db")

        def run():
            d = pd_open(path)
            for k, v in _large_data().items():
                d[k] = v
            d.close()
            os.unlink(path)

        benchmark(run)

    def test_shelve(self, benchmark, tmp_path):
        path = str(tmp_path / "bench_shelve")

        def run():
            with shelve.open(path) as d:
                for k, v in _large_data().items():
                    d[k] = v
            for ext in (".db", ".dir", ".bak", ".dat"):
                p = path + ext
                if os.path.exists(p):
                    os.unlink(p)

        benchmark(run)

    @pytest.mark.skipif(not HAS_SQLITEDICT, reason="sqlitedict not installed")
    def test_sqlitedict(self, benchmark, tmp_path):
        path = str(tmp_path / "bench_sd.db")

        def run():
            with SqliteDict(path, autocommit=True) as d:
                for k, v in _large_data().items():
                    d[k] = v
            os.unlink(path)

        benchmark(run)


# ============================================================================
# Read benchmarks (pre-populate, then measure reads)
# ============================================================================


class TestReadSmall:
    def test_zerodep_json(self, benchmark, tmp_path):
        path = str(tmp_path / "bench.json")
        data = _small_data()
        d = pd_open(path)
        d.update(data)
        d.close()

        def run():
            d2 = pd_open(path)
            for k in data:
                _ = d2[k]
            d2.close()

        benchmark(run)

    def test_zerodep_sqlite(self, benchmark, tmp_path):
        path = str(tmp_path / "bench.db")
        data = _small_data()
        d = pd_open(path)
        d.update(data)
        d.close()

        def run():
            d2 = pd_open(path)
            for k in data:
                _ = d2[k]
            d2.close()

        benchmark(run)

    def test_shelve(self, benchmark, tmp_path):
        path = str(tmp_path / "bench_shelve")
        data = _small_data()
        with shelve.open(path) as d:
            d.update(data)

        def run():
            with shelve.open(path) as d:
                for k in data:
                    _ = d[k]

        benchmark(run)

    @pytest.mark.skipif(not HAS_SQLITEDICT, reason="sqlitedict not installed")
    def test_sqlitedict(self, benchmark, tmp_path):
        path = str(tmp_path / "bench_sd.db")
        data = _small_data()
        with SqliteDict(path, autocommit=True) as d:
            d.update(data)

        def run():
            with SqliteDict(path) as d:
                for k in data:
                    _ = d[k]

        benchmark(run)


# ============================================================================
# Iteration benchmark
# ============================================================================


class TestIterateSmall:
    def test_zerodep_json(self, benchmark, tmp_path):
        path = str(tmp_path / "bench.json")
        d = pd_open(path)
        d.update(_small_data())
        d.close()

        def run():
            d2 = pd_open(path)
            for _ in d2.items():
                pass
            d2.close()

        benchmark(run)

    def test_zerodep_sqlite(self, benchmark, tmp_path):
        path = str(tmp_path / "bench.db")
        d = pd_open(path)
        d.update(_small_data())
        d.close()

        def run():
            d2 = pd_open(path)
            for _ in d2.items():
                pass
            d2.close()

        benchmark(run)

    def test_shelve(self, benchmark, tmp_path):
        path = str(tmp_path / "bench_shelve")
        with shelve.open(path) as d:
            d.update(_small_data())

        def run():
            with shelve.open(path) as d:
                for _ in d.items():
                    pass

        benchmark(run)

    @pytest.mark.skipif(not HAS_SQLITEDICT, reason="sqlitedict not installed")
    def test_sqlitedict(self, benchmark, tmp_path):
        path = str(tmp_path / "bench_sd.db")
        with SqliteDict(path, autocommit=True) as d:
            d.update(_small_data())

        def run():
            with SqliteDict(path) as d:
                for _ in d.items():
                    pass

        benchmark(run)
