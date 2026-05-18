"""Memory benchmarks: zerodep soup vs beautifulsoup4.

Uses tracemalloc to measure peak heap allocation for parse + find_all
at three input sizes (S/M/L).  Results are printed in KB so they are
visible in plain ``pytest -s`` output.  No pytest-benchmark required.
"""

import os
import sys
import tracemalloc

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from soup import Soup

bs4 = pytest.importorskip("bs4", reason="beautifulsoup4 not installed")
BeautifulSoup = bs4.BeautifulSoup


# ── Test data ──


def _make_html(n_tags: int) -> str:
    """Generate an HTML document with *n_tags* leaf elements."""
    lines = [
        "<!DOCTYPE html>",
        "<html><head><title>Benchmark</title></head><body>",
    ]
    for i in range(n_tags):
        cls = "even" if i % 2 == 0 else "odd"
        lines.append(
            f'<div class="item {cls}" data-id="{i}">'
            f"<h3>Title {i}</h3>"
            f"<p>Description for item {i}</p>"
            f'<a href="/item/{i}">Link</a>'
            f"</div>"
        )
    lines.append("</body></html>")
    return "\n".join(lines)


SMALL = _make_html(5)
MEDIUM = _make_html(50)
LARGE = _make_html(500)


# ── Helpers ──


def _measure_peak_kb(fn, *args) -> float:
    """Run *fn* with *args* under tracemalloc and return peak KB."""
    tracemalloc.start()
    try:
        fn(*args)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak / 1024


def _zd_parse_and_find(html: str) -> list:
    soup = Soup(html)
    return soup.find_all("div", class_="item")


def _bs4_parse_and_find(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    return soup.find_all("div", class_="item")


# ── Memory tests ──


_SIZES = [
    pytest.param("small", SMALL, id="small"),
    pytest.param("medium", MEDIUM, id="medium"),
    pytest.param("large", LARGE, id="large"),
]


@pytest.mark.parametrize("label,html", _SIZES)
def test_memory_zerodep(label: str, html: str) -> None:
    """Measure peak memory for zerodep Soup parse + find_all."""
    peak_kb = _measure_peak_kb(_zd_parse_and_find, html)
    print(f"\n[soup zerodep  {label:6s}] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.parametrize("label,html", _SIZES)
def test_memory_beautifulsoup4(label: str, html: str) -> None:
    """Measure peak memory for BeautifulSoup parse + find_all."""
    peak_kb = _measure_peak_kb(_bs4_parse_and_find, html)
    print(f"\n[soup bs4      {label:6s}] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.parametrize("label,html", _SIZES)
def test_memory_comparison(label: str, html: str) -> None:
    """Compare zerodep vs bs4 peak memory; print ratio."""
    zd_kb = _measure_peak_kb(_zd_parse_and_find, html)
    bs4_kb = _measure_peak_kb(_bs4_parse_and_find, html)
    ratio = zd_kb / bs4_kb if bs4_kb > 0 else float("inf")
    print(
        f"\n[soup compare  {label:6s}] zerodep={zd_kb:.1f} KB  "
        f"bs4={bs4_kb:.1f} KB  ratio={ratio:.2f}x"
    )
    assert zd_kb >= 0
    assert bs4_kb >= 0
