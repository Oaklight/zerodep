"""Benchmark: zerodep dotenv vs python-dotenv."""

import io
import os
import sys

import pytest

_this_dir = os.path.dirname(os.path.abspath(__file__))
_repo_root = os.path.dirname(_this_dir)


def _outside_repo(entry: str) -> bool:
    """True for a ``sys.path`` entry that is not inside this repository."""
    path = os.path.abspath(entry or os.curdir)
    return path != _repo_root and not path.startswith(_repo_root + os.sep)


# This module is named like the reference, and pytest's prepend import mode
# puts ``dotenv/`` on sys.path while collecting, so a plain ``import dotenv``
# binds the repo's own file and both sides of the benchmark measure the same
# implementation (#205).  Every entry inside the repository is hidden for the
# duration of the import, and the bound module is checked afterwards so the
# collision fails loudly.
_saved_path = sys.path[:]
sys.path = [p for p in sys.path if _outside_repo(p)]
_cached_dotenv = sys.modules.pop("dotenv", None)
try:
    import dotenv as ref_dotenv
except ModuleNotFoundError:
    pytest.skip("python-dotenv not installed", allow_module_level=True)
else:
    _ref_file = os.path.abspath(getattr(ref_dotenv, "__file__", "") or "")
    if not _ref_file or _ref_file.startswith(_repo_root + os.sep):
        raise RuntimeError(
            "the benchmark imported the repo's own dotenv module as the "
            "reference; the comparison would measure one implementation twice"
        )
    if not hasattr(ref_dotenv, "dotenv_values"):
        raise RuntimeError("Not the real python-dotenv")
finally:
    sys.path = _saved_path
    sys.modules.pop("dotenv", None)
    if _cached_dotenv is not None:
        sys.modules["dotenv"] = _cached_dotenv

sys.path.insert(0, _this_dir)

from dotenv import dotenv_values as zd_dotenv_values

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
