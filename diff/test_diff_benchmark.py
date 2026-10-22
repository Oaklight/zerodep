"""Benchmark: zerodep diff vs unidiff."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from diff import apply_patch, make_diff, parse_patch

unidiff = pytest.importorskip("unidiff", reason="unidiff not installed")


# ── Test Data ────────────────────────────────────────────────────────

_SMALL_A = "line1\nline2\nline3\nline4\nline5\n"
_SMALL_B = "line1\nchanged\nline3\nline4\nline5\n"
SMALL_DIFF = make_diff(_SMALL_A, _SMALL_B)

_MED_A = "".join(f"line{i}\n" for i in range(50))
_med_b = list(f"line{i}\n" for i in range(50))
_med_b[10] = "CHANGED10\n"
_med_b[25] = "CHANGED25\n"
_med_b[40] = "CHANGED40\n"
_MED_B = "".join(_med_b)
MEDIUM_DIFF = make_diff(_MED_A, _MED_B)

_LARGE_A = "".join(f"line{i}\n" for i in range(1000))
_large_b = list(f"line{i}\n" for i in range(1000))
for i in range(0, 1000, 100):
    _large_b[i] = f"CHANGED{i}\n"
_LARGE_B = "".join(_large_b)
LARGE_DIFF = make_diff(_LARGE_A, _LARGE_B)


# ── Parse Benchmarks ─────────────────────────────────────────────────


class TestParseSmall:
    def test_zerodep(self, benchmark):
        benchmark(parse_patch, SMALL_DIFF)

    def test_unidiff(self, benchmark):
        benchmark(unidiff.PatchSet, SMALL_DIFF)


class TestParseMedium:
    def test_zerodep(self, benchmark):
        benchmark(parse_patch, MEDIUM_DIFF)

    def test_unidiff(self, benchmark):
        benchmark(unidiff.PatchSet, MEDIUM_DIFF)


class TestParseLarge:
    def test_zerodep(self, benchmark):
        benchmark(parse_patch, LARGE_DIFF)

    def test_unidiff(self, benchmark):
        benchmark(unidiff.PatchSet, LARGE_DIFF)


# ── Apply Benchmarks (zerodep only) ─────────────────────────────────


class TestApplySmall:
    def test_zerodep(self, benchmark):
        patch = parse_patch(SMALL_DIFF)
        benchmark(apply_patch, _SMALL_A, patch)


class TestApplyMedium:
    def test_zerodep(self, benchmark):
        patch = parse_patch(MEDIUM_DIFF)
        benchmark(apply_patch, _MED_A, patch)


class TestApplyLarge:
    def test_zerodep(self, benchmark):
        patch = parse_patch(LARGE_DIFF)
        benchmark(apply_patch, _LARGE_A, patch)
