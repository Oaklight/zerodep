"""Benchmark: zerodep soup vs beautifulsoup4."""

import os
import sys

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


SMALL = _make_html(5)  # ~20 tags
MEDIUM = _make_html(50)  # ~200 tags
LARGE = _make_html(500)  # ~2000 tags


def _zd_parse_and_find(html: str) -> list:
    soup = Soup(html)
    return soup.find_all("div", class_="item")


def _bs4_parse_and_find(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    return soup.find_all("div", class_="item")


# ── Parse + find_all benchmarks ──


class TestSmall:
    def test_zerodep(self, benchmark):
        benchmark(_zd_parse_and_find, SMALL)

    def test_beautifulsoup4(self, benchmark):
        benchmark(_bs4_parse_and_find, SMALL)


class TestMedium:
    def test_zerodep(self, benchmark):
        benchmark(_zd_parse_and_find, MEDIUM)

    def test_beautifulsoup4(self, benchmark):
        benchmark(_bs4_parse_and_find, MEDIUM)


class TestLarge:
    def test_zerodep(self, benchmark):
        benchmark(_zd_parse_and_find, LARGE)

    def test_beautifulsoup4(self, benchmark):
        benchmark(_bs4_parse_and_find, LARGE)
