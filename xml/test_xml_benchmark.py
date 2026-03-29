"""Benchmark: zerodep XML vs xmltodict."""

import os
import sys

import pytest

# Import xmltodict before our module replaces sys.modules["xml"].
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

# Now import our module
sys.path.insert(0, _this_dir)
for _k in list(sys.modules):
    if _k == "xml" or _k.startswith("xml."):
        del sys.modules[_k]

from xml import extract_tags as zd_extract  # noqa: E402
from xml import parse as zd_parse  # noqa: E402
from xml import unparse as zd_unparse  # noqa: E402

# ── Test data ──

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

# Pre-parsed data for unparse benchmarks
SMALL_DATA = _ref_parse(SMALL_XML)
MEDIUM_DATA = _ref_parse(MEDIUM_XML)
LARGE_DATA = _ref_parse(LARGE_XML)

# LLM-style text for extract_tags benchmark
LLM_TEXT = "\n".join(
    f"<thinking>Let me analyze item {i} carefully. "
    f"This requires considering factors A, B, and C.</thinking>\n"
    f'<answer confidence="{0.5 + (i % 5) * 0.1:.1f}">'
    f"The result for item {i} is {i * 42}.</answer>"
    for i in range(50)
)


# ── Parse benchmarks ──


class TestParseSmall:
    def test_zerodep(self, benchmark):
        benchmark(zd_parse, SMALL_XML)

    def test_xmltodict(self, benchmark):
        benchmark(_ref_parse, SMALL_XML)


class TestParseMedium:
    def test_zerodep(self, benchmark):
        benchmark(zd_parse, MEDIUM_XML)

    def test_xmltodict(self, benchmark):
        benchmark(_ref_parse, MEDIUM_XML)


class TestParseLarge:
    def test_zerodep(self, benchmark):
        benchmark(zd_parse, LARGE_XML)

    def test_xmltodict(self, benchmark):
        benchmark(_ref_parse, LARGE_XML)


# ── Unparse benchmarks ──


class TestUnparseSmall:
    def test_zerodep(self, benchmark):
        benchmark(zd_unparse, SMALL_DATA, full_document=False)

    def test_xmltodict(self, benchmark):
        benchmark(_ref_unparse, SMALL_DATA, full_document=False)


class TestUnparseMedium:
    def test_zerodep(self, benchmark):
        benchmark(zd_unparse, MEDIUM_DATA, full_document=False)

    def test_xmltodict(self, benchmark):
        benchmark(_ref_unparse, MEDIUM_DATA, full_document=False)


class TestUnparseLarge:
    def test_zerodep(self, benchmark):
        benchmark(zd_unparse, LARGE_DATA, full_document=False)

    def test_xmltodict(self, benchmark):
        benchmark(_ref_unparse, LARGE_DATA, full_document=False)


# ── extract_tags benchmark (no reference) ──


class TestExtractTags:
    def test_extract_all(self, benchmark):
        benchmark(zd_extract, LLM_TEXT)

    def test_extract_filtered(self, benchmark):
        benchmark(zd_extract, LLM_TEXT, "answer")

    def test_extract_first_only(self, benchmark):
        benchmark(zd_extract, LLM_TEXT, "answer", first_only=True)
