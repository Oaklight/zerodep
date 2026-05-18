"""Memory benchmarks: zerodep xml vs xmltodict.

Uses tracemalloc to measure peak heap allocation for parse and unparse
at three input sizes (S/M/L).  Results are printed in KB so they are
visible in plain ``pytest -s`` output.  No pytest-benchmark required.

Note: our ``xml.py`` shadows stdlib ``xml`` on sys.path, so xmltodict
must be imported with path manipulation (same technique as the time
benchmark).
"""

import os
import sys
import tracemalloc

import pytest

# ── Import xmltodict before our module shadows stdlib xml ──

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
_cached_xml = sys.modules.pop("xml", None)
_cached_xml_sub = {}
for _k in list(sys.modules):
    if _k.startswith("xml."):
        _cached_xml_sub[_k] = sys.modules.pop(_k)

try:
    import xmltodict as _xmltodict

    if not hasattr(_xmltodict, "parse"):
        raise ImportError("Not the real xmltodict")
    _ref_parse = _xmltodict.parse
    _ref_unparse = _xmltodict.unparse
except ImportError:
    pytest.skip("xmltodict not installed", allow_module_level=True)
finally:
    sys.path = _saved_path
    for _k in list(sys.modules):
        if _k == "xml" or _k.startswith("xml."):
            del sys.modules[_k]
    sys.modules.update(_cached_xml_sub)
    if _cached_xml is not None:
        sys.modules["xml"] = _cached_xml

# Now import our module.
sys.path.insert(0, _this_dir)
for _k in list(sys.modules):
    if _k == "xml" or _k.startswith("xml."):
        del sys.modules[_k]

from xml import parse as zd_parse  # noqa: E402
from xml import unparse as zd_unparse  # noqa: E402

# ── Test data (same as time benchmark) ──

SMALL_XML = "<root><name>Alice</name><age>30</age><active>true</active></root>"

MEDIUM_XML = (
    """\
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""
    + "".join(
        f"  <url>\n"
        f"    <loc>https://example.com/page-{i}</loc>\n"
        f"    <lastmod>2024-{(i % 12) + 1:02d}-01</lastmod>\n"
        f"    <changefreq>weekly</changefreq>\n"
        f"    <priority>{0.5 + (i % 5) * 0.1:.1f}</priority>\n"
        f"  </url>\n"
        for i in range(25)
    )
    + "</urlset>"
)

LARGE_XML = (
    "<catalog>\n"
    + "".join(
        f'  <product id="{i}" category="cat-{i % 10}">\n'
        f"    <name>Product {i}</name>\n"
        f"    <price>{9.99 + i * 0.5:.2f}</price>\n"
        f"    <description>Description for product {i}</description>\n"
        f"    <tags>\n"
        f"      <tag>tag-{i % 5}</tag>\n"
        f"      <tag>tag-{(i + 1) % 5}</tag>\n"
        f"    </tags>\n"
        f"    <in_stock>{'true' if i % 3 != 0 else 'false'}</in_stock>\n"
        f"  </product>\n"
        for i in range(200)
    )
    + "</catalog>"
)

# Pre-parsed dicts for unparse benchmarks.
SMALL_DATA = _ref_parse(SMALL_XML)
MEDIUM_DATA = _ref_parse(MEDIUM_XML)
LARGE_DATA = _ref_parse(LARGE_XML)


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


_DOC_SIZES = [
    pytest.param("small", SMALL_XML, id="small"),
    pytest.param("medium", MEDIUM_XML, id="medium"),
    pytest.param("large", LARGE_XML, id="large"),
]

_DATA_SIZES = [
    pytest.param("small", SMALL_DATA, id="small"),
    pytest.param("medium", MEDIUM_DATA, id="medium"),
    pytest.param("large", LARGE_DATA, id="large"),
]


# ── Parse memory tests ──


@pytest.mark.parametrize("label,doc", _DOC_SIZES)
def test_parse_memory_zerodep(label: str, doc: str) -> None:
    """Measure peak memory for zerodep xml.parse."""
    peak_kb = _measure_peak_kb(zd_parse, doc)
    print(f"\n[xml parse zerodep   {label:6s}] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.parametrize("label,doc", _DOC_SIZES)
def test_parse_memory_xmltodict(label: str, doc: str) -> None:
    """Measure peak memory for xmltodict.parse."""
    peak_kb = _measure_peak_kb(_ref_parse, doc)
    print(f"\n[xml parse xmltodict {label:6s}] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.parametrize("label,doc", _DOC_SIZES)
def test_parse_memory_comparison(label: str, doc: str) -> None:
    """Compare zerodep vs xmltodict peak memory for parse."""
    zd_kb = _measure_peak_kb(zd_parse, doc)
    ref_kb = _measure_peak_kb(_ref_parse, doc)
    ratio = zd_kb / ref_kb if ref_kb > 0 else float("inf")
    print(
        f"\n[xml parse compare   {label:6s}] zerodep={zd_kb:.1f} KB  "
        f"xmltodict={ref_kb:.1f} KB  ratio={ratio:.2f}x"
    )
    assert zd_kb >= 0
    assert ref_kb >= 0


# ── Unparse memory tests ──


@pytest.mark.parametrize("label,data", _DATA_SIZES)
def test_unparse_memory_zerodep(label: str, data) -> None:
    """Measure peak memory for zerodep xml.unparse."""
    peak_kb = _measure_peak_kb(zd_unparse, data, full_document=False)
    print(f"\n[xml unparse zerodep   {label:6s}] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.parametrize("label,data", _DATA_SIZES)
def test_unparse_memory_xmltodict(label: str, data) -> None:
    """Measure peak memory for xmltodict.unparse."""
    peak_kb = _measure_peak_kb(_ref_unparse, data, full_document=False)
    print(f"\n[xml unparse xmltodict {label:6s}] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.parametrize("label,data", _DATA_SIZES)
def test_unparse_memory_comparison(label: str, data) -> None:
    """Compare zerodep vs xmltodict peak memory for unparse."""
    zd_kb = _measure_peak_kb(zd_unparse, data, full_document=False)
    ref_kb = _measure_peak_kb(_ref_unparse, data, full_document=False)
    ratio = zd_kb / ref_kb if ref_kb > 0 else float("inf")
    print(
        f"\n[xml unparse compare   {label:6s}] zerodep={zd_kb:.1f} KB  "
        f"xmltodict={ref_kb:.1f} KB  ratio={ratio:.2f}x"
    )
    assert zd_kb >= 0
    assert ref_kb >= 0
