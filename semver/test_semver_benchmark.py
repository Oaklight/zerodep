"""Benchmark: zerodep semver vs packaging.version."""

import os
import sys

import pytest

try:
    from packaging.version import Version as PkgVersion
except ImportError:
    pytest.skip("packaging not installed", allow_module_level=True)

sys.path.insert(0, os.path.dirname(__file__))
from semver import Version as ZdVersion  # noqa: E402

# ── Test data ──

SIMPLE_VERSIONS = ["1.0", "2.3.4", "0.1.0", "10.20.30", "1.0.0.0"]

PRERELEASE_VERSIONS = [
    "1.0a1",
    "1.0b2",
    "1.0rc1",
    "2.0.dev3",
    "3.0a1.dev0",
    "1.0.post1",
]

COMPLEX_VERSIONS = [
    "1!2.3.4a1.post2.dev3+local.1",
    "0!1.0.0rc1",
    "2.0.0.post1+build.123",
    "1.0.dev456",
    "3.4.5b2",
]

SORT_LIST = [
    "1.0.dev0",
    "1.0a1",
    "1.0b1",
    "1.0rc1",
    "1.0",
    "1.0.post1",
    "2.0.dev0",
    "2.0a1",
    "2.0",
    "3.0",
]


# ── Parse benchmarks ──


class TestParseSimple:
    def test_zerodep(self, benchmark):
        benchmark(lambda: [ZdVersion(v) for v in SIMPLE_VERSIONS])

    def test_packaging(self, benchmark):
        benchmark(lambda: [PkgVersion(v) for v in SIMPLE_VERSIONS])


class TestParsePrerelease:
    def test_zerodep(self, benchmark):
        benchmark(lambda: [ZdVersion(v) for v in PRERELEASE_VERSIONS])

    def test_packaging(self, benchmark):
        benchmark(lambda: [PkgVersion(v) for v in PRERELEASE_VERSIONS])


class TestParseComplex:
    def test_zerodep(self, benchmark):
        benchmark(lambda: [ZdVersion(v) for v in COMPLEX_VERSIONS])

    def test_packaging(self, benchmark):
        benchmark(lambda: [PkgVersion(v) for v in COMPLEX_VERSIONS])


# ── Comparison benchmarks ──

_zd_parsed = [ZdVersion(v) for v in SORT_LIST]
_pkg_parsed = [PkgVersion(v) for v in SORT_LIST]


class TestSort:
    def test_zerodep(self, benchmark):
        benchmark(sorted, _zd_parsed)

    def test_packaging(self, benchmark):
        benchmark(sorted, _pkg_parsed)


class TestCompare:
    def test_zerodep(self, benchmark):
        def run():
            for i in range(len(_zd_parsed) - 1):
                _ = _zd_parsed[i] < _zd_parsed[i + 1]
                _ = _zd_parsed[i] == _zd_parsed[i + 1]  # noqa: F841

        benchmark(run)

    def test_packaging(self, benchmark):
        def run():
            for i in range(len(_pkg_parsed) - 1):
                _ = _pkg_parsed[i] < _pkg_parsed[i + 1]
                _ = _pkg_parsed[i] == _pkg_parsed[i + 1]  # noqa: F841

        benchmark(run)


# ── Property access benchmarks ──

_zd_pre = [ZdVersion(v) for v in PRERELEASE_VERSIONS]
_pkg_pre = [PkgVersion(v) for v in PRERELEASE_VERSIONS]


class TestPropertyAccess:
    def test_zerodep(self, benchmark):
        def run():
            for v in _zd_pre:
                _ = v.is_prerelease
                _ = v.is_devrelease
                _ = str(v)  # noqa: F841

        benchmark(run)

    def test_packaging(self, benchmark):
        def run():
            for v in _pkg_pre:
                _ = v.is_prerelease
                _ = v.is_devrelease
                _ = str(v)  # noqa: F841

        benchmark(run)
