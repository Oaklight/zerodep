"""Benchmark: zerodep tabulate vs reference tabulate."""

import os
import sys

import pytest

# Our tabulate.py shadows the reference 'tabulate' package.
# Import the reference library first via path manipulation.
_this_dir = os.path.dirname(__file__)

_saved_path = sys.path[:]
sys.path = [
    p
    for p in sys.path
    if os.path.abspath(p)
    not in (
        os.path.abspath(_this_dir),
        os.path.abspath(os.path.join(_this_dir, "..")),
    )
]

_cached_tabulate = sys.modules.pop("tabulate", None)

try:
    import tabulate as _ref_tabulate_mod

    if not hasattr(_ref_tabulate_mod, "tabulate"):
        raise ImportError("Not the real tabulate")
    _ref_tabulate = _ref_tabulate_mod.tabulate
except ImportError:
    pytest.skip("tabulate not installed", allow_module_level=True)
finally:
    sys.path = _saved_path
    sys.modules.pop("tabulate", None)
    if _cached_tabulate is not None:
        sys.modules["tabulate"] = _cached_tabulate

sys.path.insert(0, _this_dir)
from tabulate import tabulate as zd_tabulate  # noqa: E402

# ── Test data ──

SMALL_DATA = [[f"name_{i}", i, i * 1.5] for i in range(5)]
SMALL_HEADERS = ["Name", "Value", "Score"]

MEDIUM_DATA = [[f"item_{i}", i, i * 2.5, f"cat_{i % 5}", i % 2 == 0] for i in range(50)]
MEDIUM_HEADERS = ["Item", "ID", "Price", "Category", "Active"]

LARGE_DATA = [
    [
        f"row_{i}",
        i,
        i * 3.14,
        f"group_{i % 10}",
        i % 2 == 0,
        f"desc_{i}",
        i * 100,
        i / 7.0,
    ]
    for i in range(500)
]
LARGE_HEADERS = ["Row", "ID", "Value", "Group", "Flag", "Desc", "Big", "Ratio"]


# ── Small table (5 rows x 3 cols) ──


class TestSmallTable:
    def test_zerodep(self, benchmark):
        benchmark(zd_tabulate, SMALL_DATA, headers=SMALL_HEADERS, tablefmt="grid")

    def test_reference(self, benchmark):
        benchmark(_ref_tabulate, SMALL_DATA, headers=SMALL_HEADERS, tablefmt="grid")


# ── Medium table (50 rows x 5 cols) ──


class TestMediumTable:
    def test_zerodep(self, benchmark):
        benchmark(zd_tabulate, MEDIUM_DATA, headers=MEDIUM_HEADERS, tablefmt="grid")

    def test_reference(self, benchmark):
        benchmark(_ref_tabulate, MEDIUM_DATA, headers=MEDIUM_HEADERS, tablefmt="grid")


# ── Large table (500 rows x 8 cols) ──


class TestLargeTable:
    def test_zerodep(self, benchmark):
        benchmark(zd_tabulate, LARGE_DATA, headers=LARGE_HEADERS, tablefmt="grid")

    def test_reference(self, benchmark):
        benchmark(_ref_tabulate, LARGE_DATA, headers=LARGE_HEADERS, tablefmt="grid")
