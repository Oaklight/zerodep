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


# ── to_html serialization benchmarks ──


def _zd_parse_and_serialize(html: str) -> str:
    soup = Soup(html)
    return soup.to_html()


def _bs4_parse_and_serialize(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return str(soup)


class TestSerializeSmall:
    def test_zerodep(self, benchmark):
        benchmark(_zd_parse_and_serialize, SMALL)

    def test_beautifulsoup4(self, benchmark):
        benchmark(_bs4_parse_and_serialize, SMALL)


class TestSerializeMedium:
    def test_zerodep(self, benchmark):
        benchmark(_zd_parse_and_serialize, MEDIUM)

    def test_beautifulsoup4(self, benchmark):
        benchmark(_bs4_parse_and_serialize, MEDIUM)


class TestSerializeLarge:
    def test_zerodep(self, benchmark):
        benchmark(_zd_parse_and_serialize, LARGE)

    def test_beautifulsoup4(self, benchmark):
        benchmark(_bs4_parse_and_serialize, LARGE)


# ── Tree manipulation benchmarks ──

from soup import Tag  # noqa: E402


def _zd_tree_ops(html: str) -> None:
    """Parse, then perform a series of tree manipulation operations."""
    soup = Soup(html)
    divs = soup.find_all("div", class_="item")
    if len(divs) < 2:
        return
    # append new child to first div
    new_tag = Tag("span", {"class": ["added"]})
    new_tag.children.append("new")
    divs[0].append(new_tag)
    # insert at beginning of second div
    ins_tag = Tag("em", {})
    ins_tag.children.append("inserted")
    divs[1].insert(0, ins_tag)
    # extract third div (if exists)
    if len(divs) > 2:
        divs[2].extract()
    # replace_with on first div's <h3>
    h3 = divs[0].find("h3")
    if h3:
        replacement = Tag("h4", {})
        replacement.children.append("Replaced")
        h3.replace_with(replacement)
    # unwrap all <a> tags
    for a in soup.find_all("a"):
        a.unwrap()


def _bs4_tree_ops(html: str) -> None:
    """Parse, then perform a series of tree manipulation operations."""
    soup = BeautifulSoup(html, "html.parser")
    divs = soup.find_all("div", class_="item")
    if len(divs) < 2:
        return
    # append new child to first div
    new_tag = soup.new_tag("span", attrs={"class": ["added"]})
    new_tag.string = "new"
    divs[0].append(new_tag)
    # insert at beginning of second div
    ins_tag = soup.new_tag("em")
    ins_tag.string = "inserted"
    divs[1].insert(0, ins_tag)
    # extract third div (if exists)
    if len(divs) > 2:
        divs[2].extract()
    # replace_with on first div's <h3>
    h3 = divs[0].find("h3")
    if h3:
        replacement = soup.new_tag("h4")
        replacement.string = "Replaced"
        h3.replace_with(replacement)
    # unwrap all <a> tags
    for a in soup.find_all("a"):
        a.unwrap()


class TestTreeOpsSmall:
    def test_zerodep(self, benchmark):
        benchmark(_zd_tree_ops, SMALL)

    def test_beautifulsoup4(self, benchmark):
        benchmark(_bs4_tree_ops, SMALL)


class TestTreeOpsMedium:
    def test_zerodep(self, benchmark):
        benchmark(_zd_tree_ops, MEDIUM)

    def test_beautifulsoup4(self, benchmark):
        benchmark(_bs4_tree_ops, MEDIUM)


class TestTreeOpsLarge:
    def test_zerodep(self, benchmark):
        benchmark(_zd_tree_ops, LARGE)

    def test_beautifulsoup4(self, benchmark):
        benchmark(_bs4_tree_ops, LARGE)


# ── CSS select benchmarks ──

_SELECT_QUERIES = [
    "div.item",
    "div.item > h3",
    "div.even a",
    '[data-id="3"]',
]

_PSEUDO_QUERIES = [
    "div.item :first-child",
    "div.item :last-child",
    "div.item > :not(p)",
    "div.item > :first-child:not(h3)",
]


def _zd_select(html: str, queries: list[str]) -> list:
    soup = Soup(html)
    return [soup.select(q) for q in queries]


def _bs4_select(html: str, queries: list[str]) -> list:
    soup = BeautifulSoup(html, "html.parser")
    return [soup.select(q) for q in queries]


class TestSelectSmall:
    def test_zerodep(self, benchmark):
        benchmark(_zd_select, SMALL, _SELECT_QUERIES)

    def test_beautifulsoup4(self, benchmark):
        benchmark(_bs4_select, SMALL, _SELECT_QUERIES)


class TestSelectMedium:
    def test_zerodep(self, benchmark):
        benchmark(_zd_select, MEDIUM, _SELECT_QUERIES)

    def test_beautifulsoup4(self, benchmark):
        benchmark(_bs4_select, MEDIUM, _SELECT_QUERIES)


class TestSelectLarge:
    def test_zerodep(self, benchmark):
        benchmark(_zd_select, LARGE, _SELECT_QUERIES)

    def test_beautifulsoup4(self, benchmark):
        benchmark(_bs4_select, LARGE, _SELECT_QUERIES)


# ── CSS pseudo-selector benchmarks ──


class TestPseudoSelectSmall:
    def test_zerodep(self, benchmark):
        benchmark(_zd_select, SMALL, _PSEUDO_QUERIES)

    def test_beautifulsoup4(self, benchmark):
        benchmark(_bs4_select, SMALL, _PSEUDO_QUERIES)


class TestPseudoSelectMedium:
    def test_zerodep(self, benchmark):
        benchmark(_zd_select, MEDIUM, _PSEUDO_QUERIES)

    def test_beautifulsoup4(self, benchmark):
        benchmark(_bs4_select, MEDIUM, _PSEUDO_QUERIES)


class TestPseudoSelectLarge:
    def test_zerodep(self, benchmark):
        benchmark(_zd_select, LARGE, _PSEUDO_QUERIES)

    def test_beautifulsoup4(self, benchmark):
        benchmark(_bs4_select, LARGE, _PSEUDO_QUERIES)
