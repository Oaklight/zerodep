"""Benchmark: zerodep dotenv vs python-dotenv."""

import io
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import dotenv_values as zd_dotenv_values

ref_dotenv = pytest.importorskip("dotenv", reason="python-dotenv not installed")

# ── Test data ──

SMALL = "\n".join(f"KEY_{i}=value_{i}" for i in range(10))

MEDIUM_LINES = []
for i in range(50):
    if i % 5 == 0:
        MEDIUM_LINES.append(f"# comment block {i}")
    if i % 3 == 0:
        MEDIUM_LINES.append(f'KEY_{i}="quoted value {i}"')
    elif i % 3 == 1:
        MEDIUM_LINES.append(f"KEY_{i}='single {i}'")
    else:
        MEDIUM_LINES.append(f"KEY_{i}=plain_{i}")
MEDIUM = "\n".join(MEDIUM_LINES)

LARGE = "\n".join(f"KEY_{i}=value_{i}" for i in range(500))


def _zd_parse(content: str) -> dict:
    return zd_dotenv_values(stream=io.StringIO(content))


def _ref_parse(content: str) -> dict:
    return ref_dotenv.dotenv_values(stream=io.StringIO(content))


# ── Parse benchmarks ──


class TestParseSmall:
    def test_zerodep(self, benchmark):
        benchmark(_zd_parse, SMALL)

    def test_python_dotenv(self, benchmark):
        benchmark(_ref_parse, SMALL)


class TestParseMedium:
    def test_zerodep(self, benchmark):
        benchmark(_zd_parse, MEDIUM)

    def test_python_dotenv(self, benchmark):
        benchmark(_ref_parse, MEDIUM)


class TestParseLarge:
    def test_zerodep(self, benchmark):
        benchmark(_zd_parse, LARGE)

    def test_python_dotenv(self, benchmark):
        benchmark(_ref_parse, LARGE)
