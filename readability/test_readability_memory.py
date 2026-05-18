"""Memory benchmarks: zerodep readability vs readability-lxml.

Uses tracemalloc to measure peak heap allocation for HTML content
extraction at three fixture size tiers (S/M/L from Mozilla test pages).
Results are printed in KB so they are visible in plain ``pytest -s``
output.  No pytest-benchmark required.
"""

import importlib
import os
import sys
import tracemalloc

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from readability import extract  # noqa: E402

# ── readability-lxml reference ──

try:
    from importlib.metadata import version as _pkg_version

    _pkg_version("readability-lxml")
    _HAS_REFERENCE = True
except Exception:
    _HAS_REFERENCE = False


def _load_reference_document_class():
    """Load readability-lxml's Document class, working around name clash."""
    saved_path = sys.path[:]
    saved_modules = {
        k: sys.modules.pop(k)
        for k in list(sys.modules)
        if k == "readability" or k.startswith("readability.")
    }
    try:
        this_dir = os.path.dirname(__file__)
        this_abs = os.path.abspath(this_dir)
        sys.path = [p for p in sys.path if os.path.abspath(p) != this_abs]
        mod = importlib.import_module("readability")
        return mod.Document
    finally:
        sys.path = saved_path
        for k in list(sys.modules):
            if k == "readability" or k.startswith("readability."):
                del sys.modules[k]
        sys.modules.update(saved_modules)


if _HAS_REFERENCE:
    _RefDocument = _load_reference_document_class()
else:
    _RefDocument = None


# ── Test fixtures: Mozilla Readability test pages ──

_TEST_PAGES_DIR = os.path.join(os.path.dirname(__file__), "test-pages")

_SMALL_FIXTURES = ["rtl-1", "basic-tags-cleaning", "003-metadata-preferred"]
_MEDIUM_FIXTURES = ["001", "ars-1"]
_LARGE_FIXTURES = ["cnn", "bbc-1", "guardian-1"]


def _fixture_path(name: str) -> str:
    return os.path.join(_TEST_PAGES_DIR, name, "source.html")


def _pick_available(names: list) -> str | None:
    """Return the first available fixture name, or None."""
    for name in names:
        if os.path.isfile(_fixture_path(name)):
            return name
    return None


_FIXTURE_CACHE: dict[str, str] = {}


def _get_fixture(name: str) -> str:
    """Get cached fixture HTML."""
    if name not in _FIXTURE_CACHE:
        with open(_fixture_path(name), encoding="utf-8") as f:
            _FIXTURE_CACHE[name] = f.read()
    return _FIXTURE_CACHE[name]


# Resolve one fixture per size tier (skip entire tier if none available).
_SMALL = _pick_available(_SMALL_FIXTURES)
_MEDIUM = _pick_available(_MEDIUM_FIXTURES)
_LARGE = _pick_available(_LARGE_FIXTURES)


# ── Helpers ──


def _measure_peak_kb(fn, *args, **kwargs) -> float:
    """Run *fn* with *args*/*kwargs* under tracemalloc and return peak KB."""
    tracemalloc.start()
    try:
        fn(*args, **kwargs)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak / 1024


def _zd_extract(html: str) -> None:
    extract(html)


def _ref_extract(html: str) -> None:
    doc = _RefDocument(html)
    doc.summary()


# ── Memory tests ──


@pytest.mark.skipif(_SMALL is None, reason="no small fixture available")
def test_extract_memory_zerodep_small() -> None:
    """Measure peak memory for zerodep extract on a small fixture."""
    html = _get_fixture(_SMALL)
    peak_kb = _measure_peak_kb(_zd_extract, html)
    print(f"\n[readability zerodep  small ] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.skipif(_MEDIUM is None, reason="no medium fixture available")
def test_extract_memory_zerodep_medium() -> None:
    """Measure peak memory for zerodep extract on a medium fixture."""
    html = _get_fixture(_MEDIUM)
    peak_kb = _measure_peak_kb(_zd_extract, html)
    print(f"\n[readability zerodep  medium] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.skipif(_LARGE is None, reason="no large fixture available")
def test_extract_memory_zerodep_large() -> None:
    """Measure peak memory for zerodep extract on a large fixture."""
    html = _get_fixture(_LARGE)
    peak_kb = _measure_peak_kb(_zd_extract, html)
    print(f"\n[readability zerodep  large ] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.skipif(not _HAS_REFERENCE, reason="readability-lxml not installed")
@pytest.mark.skipif(_SMALL is None, reason="no small fixture available")
def test_extract_memory_reference_small() -> None:
    """Measure peak memory for readability-lxml on a small fixture."""
    html = _get_fixture(_SMALL)
    peak_kb = _measure_peak_kb(_ref_extract, html)
    print(f"\n[readability lxml     small ] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.skipif(not _HAS_REFERENCE, reason="readability-lxml not installed")
@pytest.mark.skipif(_MEDIUM is None, reason="no medium fixture available")
def test_extract_memory_reference_medium() -> None:
    """Measure peak memory for readability-lxml on a medium fixture."""
    html = _get_fixture(_MEDIUM)
    peak_kb = _measure_peak_kb(_ref_extract, html)
    print(f"\n[readability lxml     medium] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.skipif(not _HAS_REFERENCE, reason="readability-lxml not installed")
@pytest.mark.skipif(_LARGE is None, reason="no large fixture available")
def test_extract_memory_reference_large() -> None:
    """Measure peak memory for readability-lxml on a large fixture."""
    html = _get_fixture(_LARGE)
    peak_kb = _measure_peak_kb(_ref_extract, html)
    print(f"\n[readability lxml     large ] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.skipif(not _HAS_REFERENCE, reason="readability-lxml not installed")
@pytest.mark.skipif(_SMALL is None, reason="no small fixture available")
def test_extract_memory_comparison_small() -> None:
    """Compare zerodep vs readability-lxml peak memory on small fixture."""
    html = _get_fixture(_SMALL)
    zd_kb = _measure_peak_kb(_zd_extract, html)
    ref_kb = _measure_peak_kb(_ref_extract, html)
    ratio = zd_kb / ref_kb if ref_kb > 0 else float("inf")
    print(
        f"\n[readability compare  small ] zerodep={zd_kb:.1f} KB  "
        f"lxml={ref_kb:.1f} KB  ratio={ratio:.2f}x"
    )
    assert zd_kb >= 0
    assert ref_kb >= 0


@pytest.mark.skipif(not _HAS_REFERENCE, reason="readability-lxml not installed")
@pytest.mark.skipif(_MEDIUM is None, reason="no medium fixture available")
def test_extract_memory_comparison_medium() -> None:
    """Compare zerodep vs readability-lxml peak memory on medium fixture."""
    html = _get_fixture(_MEDIUM)
    zd_kb = _measure_peak_kb(_zd_extract, html)
    ref_kb = _measure_peak_kb(_ref_extract, html)
    ratio = zd_kb / ref_kb if ref_kb > 0 else float("inf")
    print(
        f"\n[readability compare  medium] zerodep={zd_kb:.1f} KB  "
        f"lxml={ref_kb:.1f} KB  ratio={ratio:.2f}x"
    )
    assert zd_kb >= 0
    assert ref_kb >= 0


@pytest.mark.skipif(not _HAS_REFERENCE, reason="readability-lxml not installed")
@pytest.mark.skipif(_LARGE is None, reason="no large fixture available")
def test_extract_memory_comparison_large() -> None:
    """Compare zerodep vs readability-lxml peak memory on large fixture."""
    html = _get_fixture(_LARGE)
    zd_kb = _measure_peak_kb(_zd_extract, html)
    ref_kb = _measure_peak_kb(_ref_extract, html)
    ratio = zd_kb / ref_kb if ref_kb > 0 else float("inf")
    print(
        f"\n[readability compare  large ] zerodep={zd_kb:.1f} KB  "
        f"lxml={ref_kb:.1f} KB  ratio={ratio:.2f}x"
    )
    assert zd_kb >= 0
    assert ref_kb >= 0
