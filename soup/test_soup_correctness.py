"""Correctness tests: zerodep soup vs beautifulsoup4."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from soup import Soup, Tag

bs4 = pytest.importorskip("bs4", reason="beautifulsoup4 not installed")
BeautifulSoup = bs4.BeautifulSoup

# ── Helpers ──


def _ours(html: str) -> Soup:
    return Soup(html)


def _theirs(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


# ── Test HTML fixtures ──

SIMPLE_HTML = "<html><head><title>Test</title></head><body><p>Hello</p></body></html>"

NESTED_HTML = """
<div class="outer">
    <div class="inner">
        <span>Nested text</span>
    </div>
</div>
"""

MULTI_CLASS_HTML = """
<div class="one two three">Multi</div>
<div class="one">Single</div>
<div class="two three">Pair</div>
"""

ATTRS_HTML = """
<a href="https://example.com" id="link1" class="nav active">Link 1</a>
<a href="https://other.com" class="nav">Link 2</a>
<a class="footer">Link 3</a>
<input type="text" name="q" />
<input type="submit" value="Go" />
"""

SELF_CLOSING_HTML = """
<p>Before<br>After</p>
<img src="pic.jpg" alt="A picture">
<hr>
<input type="text">
<link rel="stylesheet" href="style.css">
<meta charset="utf-8">
"""

MALFORMED_HTML = """
<div><p>Unclosed div
<b>Bold <i>and italic</b> only italic</i>
<span>Missing close
"""

REAL_WORLD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Tool Registry Hub</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <nav class="main-nav">
        <a href="/" class="logo">Hub</a>
        <a href="/tools" class="nav-link">Tools</a>
        <a href="/docs" class="nav-link active">Docs</a>
    </nav>
    <main>
        <div class="tool-card" data-id="1">
            <h2 class="tool-name">Calculator</h2>
            <p class="tool-desc">A simple calculator tool</p>
            <span class="tag">math</span>
            <span class="tag">utility</span>
        </div>
        <div class="tool-card" data-id="2">
            <h2 class="tool-name">Translator</h2>
            <p class="tool-desc">Language translation tool</p>
            <span class="tag">language</span>
        </div>
        <div class="tool-card" data-id="3">
            <h2 class="tool-name">Search</h2>
            <p class="tool-desc">Web search tool</p>
            <span class="tag">web</span>
            <span class="tag">utility</span>
        </div>
    </main>
    <footer>
        <p>&copy; 2024 Tool Registry</p>
    </footer>
    <script>console.log("loaded");</script>
    <style>.hidden { display: none; }</style>
</body>
</html>
"""


# ── TestBasicParsing ──


class TestBasicParsing:
    def test_simple_html(self):
        ours = _ours(SIMPLE_HTML)
        theirs = _theirs(SIMPLE_HTML)
        our_tag = ours.find("title")
        their_tag = theirs.find("title")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.text == their_tag.text

    def test_nested_tags(self):
        ours = _ours(NESTED_HTML)
        theirs = _theirs(NESTED_HTML)
        our_tag = ours.find("span")
        their_tag = theirs.find("span")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.text == their_tag.text

    def test_self_closing_br(self):
        ours = _ours(SELF_CLOSING_HTML)
        theirs = _theirs(SELF_CLOSING_HTML)
        assert len(ours.find_all("br")) == len(theirs.find_all("br"))

    def test_self_closing_img(self):
        ours = _ours(SELF_CLOSING_HTML)
        theirs = _theirs(SELF_CLOSING_HTML)
        our_img = ours.find("img")
        their_img = theirs.find("img")
        assert our_img is not None
        assert their_img is not None
        assert our_img["src"] == their_img["src"]

    def test_self_closing_input(self):
        ours = _ours(SELF_CLOSING_HTML)
        theirs = _theirs(SELF_CLOSING_HTML)
        our_inputs = ours.find_all("input")
        their_inputs = theirs.find_all("input")
        assert len(our_inputs) == len(their_inputs)

    def test_self_closing_meta(self):
        ours = _ours(SELF_CLOSING_HTML)
        theirs = _theirs(SELF_CLOSING_HTML)
        assert len(ours.find_all("meta")) == len(theirs.find_all("meta"))

    def test_self_closing_hr(self):
        ours = _ours(SELF_CLOSING_HTML)
        theirs = _theirs(SELF_CLOSING_HTML)
        assert len(ours.find_all("hr")) == len(theirs.find_all("hr"))

    def test_self_closing_link(self):
        ours = _ours(SELF_CLOSING_HTML)
        theirs = _theirs(SELF_CLOSING_HTML)
        assert len(ours.find_all("link")) == len(theirs.find_all("link"))


# ── TestFind ──


class TestFind:
    def test_by_tag_name(self):
        ours = _ours(SIMPLE_HTML)
        theirs = _theirs(SIMPLE_HTML)
        our_tag = ours.find("p")
        their_tag = theirs.find("p")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.text == their_tag.text

    def test_by_class(self):
        ours = _ours(NESTED_HTML)
        theirs = _theirs(NESTED_HTML)
        our_div = ours.find("div", class_="inner")
        their_div = theirs.find("div", class_="inner")
        assert our_div is not None
        assert their_div is not None
        our_span = our_div.find("span")
        their_span = their_div.find("span")
        assert our_span is not None
        assert their_span is not None
        assert our_span.text == their_span.text

    def test_by_id(self):
        ours = _ours(ATTRS_HTML)
        theirs = _theirs(ATTRS_HTML)
        our_tag = ours.find("a", id="link1")
        their_tag = theirs.find("a", id="link1")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.text == their_tag.text

    def test_by_attribute_value(self):
        ours = _ours(ATTRS_HTML)
        theirs = _theirs(ATTRS_HTML)
        our_input = ours.find("input", {"type": "text"})
        their_input = theirs.find("input", {"type": "text"})
        assert our_input is not None
        assert their_input is not None
        assert our_input["name"] == their_input["name"]

    def test_by_attribute_existence(self):
        ours = _ours(ATTRS_HTML)
        theirs = _theirs(ATTRS_HTML)
        our_result = ours.find("a", href=True)
        their_result = theirs.find("a", href=True)
        assert our_result is not None
        assert their_result is not None
        assert our_result.text == their_result.text

    def test_with_dict_attrs_class(self):
        ours = _ours(MULTI_CLASS_HTML)
        theirs = _theirs(MULTI_CLASS_HTML)
        our_tag = ours.find("div", {"class": "one"})
        their_tag = theirs.find("div", {"class": "one"})
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.text.strip() == their_tag.text.strip()

    def test_find_returns_none(self):
        ours = _ours(SIMPLE_HTML)
        theirs = _theirs(SIMPLE_HTML)
        assert ours.find("table") is None
        assert theirs.find("table") is None

    def test_find_none_name_matches_any(self):
        # find(None, class_=...) should match any tag with that class
        html = '<div class="x">A</div><span class="x">B</span>'
        our_tag = _ours(html).find(None, class_="x")
        their_tag = _theirs(html).find(None, class_="x")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.name == their_tag.name

    def test_find_with_multiple_attrs(self):
        html = '<a href="/a" class="link">A</a><a href="/b" class="link">B</a>'
        ours = _ours(html)
        theirs = _theirs(html)
        our_result = ours.find("a", {"class": "link", "href": "/b"})
        their_result = theirs.find("a", {"class": "link", "href": "/b"})
        assert our_result is not None
        assert their_result is not None
        assert our_result.text == their_result.text


# ── TestFindAll ──


class TestFindAll:
    def test_multiple_results(self):
        ours = _ours(ATTRS_HTML)
        theirs = _theirs(ATTRS_HTML)
        assert len(ours.find_all("a")) == len(theirs.find_all("a"))

    def test_list_of_tag_names(self):
        ours = _ours(ATTRS_HTML)
        theirs = _theirs(ATTRS_HTML)
        our_count = len(ours.find_all(["a", "input"]))
        their_count = len(theirs.find_all(["a", "input"]))
        assert our_count == their_count

    def test_limit(self):
        ours = _ours(ATTRS_HTML)
        theirs = _theirs(ATTRS_HTML)
        assert len(ours.find_all("a", limit=2)) == len(theirs.find_all("a", limit=2))

    def test_find_all_by_class(self):
        ours = _ours(ATTRS_HTML)
        theirs = _theirs(ATTRS_HTML)
        assert len(ours.find_all("a", class_="nav")) == len(
            theirs.find_all("a", class_="nav")
        )

    def test_find_all_empty_result(self):
        ours = _ours(SIMPLE_HTML)
        assert ours.find_all("table") == []

    def test_find_all_no_name(self):
        html = '<span class="x">A</span><div class="x">B</div>'
        ours = _ours(html)
        theirs = _theirs(html)
        assert len(ours.find_all(None, class_="x")) == len(
            theirs.find_all(None, class_="x")
        )


# ── TestSelect ──


class TestSelect:
    def test_by_tag(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        assert len(ours.select("h2")) == len(theirs.select("h2"))

    def test_by_class(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        assert len(ours.select(".tag")) == len(theirs.select(".tag"))

    def test_by_id(self):
        ours = _ours(ATTRS_HTML)
        theirs = _theirs(ATTRS_HTML)
        result_ours = ours.select("#link1")
        result_theirs = theirs.select("#link1")
        assert len(result_ours) == len(result_theirs)
        assert result_ours[0].text == result_theirs[0].text

    def test_tag_dot_class(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        assert len(ours.select("div.tool-card")) == len(theirs.select("div.tool-card"))

    def test_descendant(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        assert len(ours.select("div span")) == len(theirs.select("div span"))

    def test_child(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        assert len(ours.select("div > h2")) == len(theirs.select("div > h2"))

    def test_compound_tag_class_id(self):
        html = '<div class="a" id="x">1</div><div class="a">2</div>'
        ours = _ours(html)
        theirs = _theirs(html)
        assert len(ours.select("div.a#x")) == len(theirs.select("div.a#x"))

    def test_multiple_classes(self):
        ours = _ours(MULTI_CLASS_HTML)
        theirs = _theirs(MULTI_CLASS_HTML)
        assert len(ours.select("div.two.three")) == len(theirs.select("div.two.three"))

    def test_attribute_presence(self):
        ours = _ours(ATTRS_HTML)
        theirs = _theirs(ATTRS_HTML)
        assert len(ours.select("[href]")) == len(theirs.select("[href]"))

    def test_attribute_value(self):
        ours = _ours(ATTRS_HTML)
        theirs = _theirs(ATTRS_HTML)
        assert len(ours.select('[type="text"]')) == len(theirs.select('[type="text"]'))

    def test_nested_descendant(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        assert len(ours.select("nav a")) == len(theirs.select("nav a"))

    def test_class_only(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        assert len(ours.select(".tool-name")) == len(theirs.select(".tool-name"))


# ── TestSelectOne ──


class TestSelectOne:
    def test_select_one_found(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        our_tag = ours.select_one("h2")
        their_tag = theirs.select_one("h2")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.text == their_tag.text

    def test_select_one_not_found(self):
        ours = _ours(SIMPLE_HTML)
        assert ours.select_one("table") is None

    def test_select_one_class(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        our_tag = ours.select_one(".logo")
        their_tag = theirs.select_one(".logo")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.text == their_tag.text

    def test_select_one_descendant(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        our_tag = ours.select_one("nav .logo")
        their_tag = theirs.select_one("nav .logo")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.text == their_tag.text


# ── TestGetText ──


class TestGetText:
    def test_simple(self):
        ours = _ours("<p>Hello <b>world</b></p>")
        theirs = _theirs("<p>Hello <b>world</b></p>")
        our_tag = ours.find("p")
        their_tag = theirs.find("p")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.get_text() == their_tag.get_text()

    def test_with_separator(self):
        ours = _ours("<p>Hello <b>world</b></p>")
        theirs = _theirs("<p>Hello <b>world</b></p>")
        our_tag = ours.find("p")
        their_tag = theirs.find("p")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.get_text(separator="|") == their_tag.get_text(separator="|")

    def test_with_strip(self):
        html = "<p>  Hello  <b>  world  </b>  </p>"
        ours = _ours(html)
        theirs = _theirs(html)
        our_tag = ours.find("p")
        their_tag = theirs.find("p")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.get_text(separator=" ", strip=True) == their_tag.get_text(
            separator=" ", strip=True
        )

    def test_empty_element(self):
        ours = _ours("<div></div>")
        theirs = _theirs("<div></div>")
        our_tag = ours.find("div")
        their_tag = theirs.find("div")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.get_text() == their_tag.get_text()


# ── TestTextProperty ──


class TestTextProperty:
    def test_text(self):
        ours = _ours("<p>Hello</p>")
        theirs = _theirs("<p>Hello</p>")
        our_tag = ours.find("p")
        their_tag = theirs.find("p")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.text == their_tag.text

    def test_nested_text(self):
        ours = _ours("<div><p>Hello</p> <p>World</p></div>")
        theirs = _theirs("<div><p>Hello</p> <p>World</p></div>")
        our_tag = ours.find("div")
        their_tag = theirs.find("div")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.text == their_tag.text

    def test_string_single_child(self):
        ours = _ours("<p>Hello</p>")
        theirs = _theirs("<p>Hello</p>")
        our_tag = ours.find("p")
        their_tag = theirs.find("p")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.string == their_tag.string

    def test_string_nested_single(self):
        ours = _ours("<p><b>Hello</b></p>")
        theirs = _theirs("<p><b>Hello</b></p>")
        our_tag = ours.find("p")
        their_tag = theirs.find("p")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.string == their_tag.string

    def test_string_multiple_children_none(self):
        ours = _ours("<p>Hello <b>World</b></p>")
        theirs = _theirs("<p>Hello <b>World</b></p>")
        our_tag = ours.find("p")
        their_tag = theirs.find("p")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.string is None
        assert their_tag.string is None


# ── TestAttributes ──


class TestAttributes:
    def test_get(self):
        ours = _ours(ATTRS_HTML)
        theirs = _theirs(ATTRS_HTML)
        our_tag = ours.find("a")
        their_tag = theirs.find("a")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag["href"] == their_tag["href"]

    def test_get_default(self):
        ours = _ours(ATTRS_HTML)
        tag = ours.find("a")
        assert tag is not None
        assert tag.get("nonexistent", "default") == "default"

    def test_getitem_raises(self):
        ours = _ours(ATTRS_HTML)
        tag = ours.find("a")
        assert tag is not None
        with pytest.raises(KeyError):
            _ = tag["nonexistent"]

    def test_attrs_dict(self):
        ours = _ours('<div id="test" class="a b">X</div>')
        theirs = _theirs('<div id="test" class="a b">X</div>')
        our_tag = ours.find("div")
        their_tag = theirs.find("div")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.attrs["id"] == their_tag.attrs["id"]

    def test_class_as_list(self):
        ours = _ours('<div class="a b c">X</div>')
        theirs = _theirs('<div class="a b c">X</div>')
        our_tag = ours.find("div")
        their_tag = theirs.find("div")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag["class"] == their_tag["class"]

    def test_contains(self):
        ours = _ours(ATTRS_HTML)
        tag = ours.find("a")
        assert tag is not None
        assert "href" in tag
        assert "nonexistent" not in tag

    def test_empty_attribute(self):
        ours = _ours("<input disabled>")
        tag = ours.find("input")
        assert tag is not None
        assert "disabled" in tag


# ── TestDecompose ──


class TestDecompose:
    def test_remove_element(self):
        html = "<div><p>Keep</p><p>Remove</p></div>"
        ours = _ours(html)
        ps = ours.find_all("p")
        assert len(ps) == 2
        ps[1].decompose()
        assert len(ours.find_all("p")) == 1
        remaining = ours.find("p")
        assert remaining is not None
        assert remaining.text == "Keep"

    def test_decompose_clears_children(self):
        html = "<div><span><b>Deep</b></span></div>"
        ours = _ours(html)
        span = ours.find("span")
        assert span is not None
        span.decompose()
        assert span.children == []
        assert span.parent is None

    def test_decompose_removes_from_parent(self):
        html = "<ul><li>A</li><li>B</li><li>C</li></ul>"
        ours = _ours(html)
        items = ours.find_all("li")
        items[1].decompose()
        remaining = ours.find_all("li")
        assert len(remaining) == 2
        assert remaining[0].text == "A"
        assert remaining[1].text == "C"


# ── TestFindParent ──


class TestFindParent:
    def test_immediate_parent(self):
        ours = _ours(NESTED_HTML)
        span = ours.find("span")
        assert span is not None
        parent = span.find_parent()
        assert parent is not None
        assert parent.name == "div"

    def test_named_parent(self):
        html = "<html><body><div><p><span>X</span></p></div></body></html>"
        ours = _ours(html)
        span = ours.find("span")
        assert span is not None
        div_parent = span.find_parent("div")
        assert div_parent is not None
        assert div_parent.name == "div"

    def test_parent_not_found(self):
        html = "<div><span>X</span></div>"
        ours = _ours(html)
        span = ours.find("span")
        assert span is not None
        assert span.find_parent("table") is None

    def test_find_parent_body(self):
        html = "<html><body><div><p>Text</p></div></body></html>"
        ours = _ours(html)
        p = ours.find("p")
        assert p is not None
        body = p.find_parent("body")
        assert body is not None
        assert body.name == "body"


# ── TestCallable ──


class TestCallable:
    def test_callable_list_of_names(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        our_result = ours(["script", "style"])
        their_result = theirs(["script", "style"])
        assert len(our_result) == len(their_result)

    def test_callable_single_name(self):
        ours = _ours(SIMPLE_HTML)
        theirs = _theirs(SIMPLE_HTML)
        assert len(ours("p")) == len(theirs("p"))

    def test_callable_with_class(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        assert len(ours("a", class_="nav-link")) == len(theirs("a", class_="nav-link"))


# ── TestMalformedHTML ──


class TestMalformedHTML:
    def test_unclosed_tags(self):
        ours = _ours(MALFORMED_HTML)
        # Should not crash
        assert ours.find("div") is not None

    def test_unclosed_bold(self):
        ours = _ours(MALFORMED_HTML)
        tag = ours.find("b")
        assert tag is not None
        assert tag.text is not None

    def test_missing_close_span(self):
        ours = _ours(MALFORMED_HTML)
        assert ours.find("span") is not None

    def test_completely_broken(self):
        html = "<<< not html at all >>>"
        ours = _ours(html)
        # Should not crash, text should still be accessible
        assert isinstance(ours, Soup)

    def test_missing_attribute_quotes(self):
        html = "<div class=foo>Text</div>"
        ours = _ours(html)
        theirs = _theirs(html)
        our_tag = ours.find("div")
        their_tag = theirs.find("div")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.text == their_tag.text


# ── TestEdgeCases ──


class TestEdgeCases:
    def test_empty_html(self):
        ours = _ours("")
        assert ours.find("div") is None
        assert ours.text == ""

    def test_whitespace_only(self):
        ours = _ours("   \n\t  ")
        assert ours.find("div") is None

    def test_entities_amp(self):
        ours = _ours("<p>A &amp; B</p>")
        theirs = _theirs("<p>A &amp; B</p>")
        our_tag = ours.find("p")
        their_tag = theirs.find("p")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.text == their_tag.text

    def test_entities_lt_gt(self):
        ours = _ours("<p>&lt;tag&gt;</p>")
        theirs = _theirs("<p>&lt;tag&gt;</p>")
        our_tag = ours.find("p")
        their_tag = theirs.find("p")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.text == their_tag.text

    def test_numeric_entity(self):
        ours = _ours("<p>&#169; 2024</p>")
        theirs = _theirs("<p>&#169; 2024</p>")
        our_tag = ours.find("p")
        their_tag = theirs.find("p")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.text == their_tag.text

    def test_isinstance_check(self):
        ours = _ours("<div>Text</div>")
        tag = ours.find("div")
        assert isinstance(tag, Tag)

    def test_soup_is_tag(self):
        ours = _ours("<div>Text</div>")
        assert isinstance(ours, Tag)

    def test_repr(self):
        ours = _ours('<a href="/x" class="link">Text</a>')
        tag = ours.find("a")
        assert tag is not None
        r = repr(tag)
        assert "a" in r
        assert "href" in r

    def test_text_only_no_tags(self):
        ours = _ours("Just plain text")
        theirs = _theirs("Just plain text")
        assert ours.text == theirs.text

    def test_comment(self):
        html = "<div><!-- comment -->Text</div>"
        ours = _ours(html)
        theirs = _theirs(html)
        our_tag = ours.find("div")
        their_tag = theirs.find("div")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.text == their_tag.text

    def test_nested_find(self):
        html = "<div><ul><li>1</li><li>2</li></ul></div>"
        ours = _ours(html)
        theirs = _theirs(html)
        our_ul = ours.find("ul")
        their_ul = theirs.find("ul")
        assert our_ul is not None
        assert their_ul is not None
        our_items = our_ul.find_all("li")
        their_items = their_ul.find_all("li")
        assert len(our_items) == len(their_items)
        assert [i.text for i in our_items] == [i.text for i in their_items]


# ── TestRealWorldHTML ──


class TestRealWorldHTML:
    def test_nav_links(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        our_links = ours.select("nav a")
        their_links = theirs.select("nav a")
        assert len(our_links) == len(their_links)
        for o, t in zip(our_links, their_links):
            assert o.text == t.text

    def test_tool_cards(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        our_cards = ours.select("div.tool-card")
        their_cards = theirs.select("div.tool-card")
        assert len(our_cards) == len(their_cards)

    def test_tool_names(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        our_names = [t.text for t in ours.select("h2.tool-name")]
        their_names = [t.text for t in theirs.select("h2.tool-name")]
        assert our_names == their_names

    def test_tags_in_card(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        our_tags = [t.text for t in ours.select("span.tag")]
        their_tags = [t.text for t in theirs.select("span.tag")]
        assert our_tags == their_tags

    def test_data_attributes(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        our_cards = ours.select("[data-id]")
        their_cards = theirs.select("[data-id]")
        assert len(our_cards) == len(their_cards)
        our_ids = [c["data-id"] for c in our_cards]
        their_ids = [c["data-id"] for c in their_cards]
        assert our_ids == their_ids

    def test_decompose_script_style(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        for tag in ours(["script", "style"]):
            tag.decompose()
        for tag in theirs(["script", "style"]):
            tag.decompose()
        # After removing script/style, text should match
        our_text = ours.get_text(separator=" ", strip=True)
        their_text = theirs.get_text(separator=" ", strip=True)
        assert our_text == their_text

    def test_find_active_link(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        our_active = ours.find("a", class_="active")
        their_active = theirs.find("a", class_="active")
        assert our_active is not None
        assert their_active is not None
        assert our_active.text == their_active.text

    def test_child_selector(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        our_result = ours.select("div.tool-card > h2")
        their_result = theirs.select("div.tool-card > h2")
        assert len(our_result) == len(their_result)

    def test_footer_text(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        our_tag = ours.find("footer")
        their_tag = theirs.find("footer")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.get_text(strip=True) == their_tag.get_text(strip=True)

    def test_title(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        our_tag = ours.find("title")
        their_tag = theirs.find("title")
        assert our_tag is not None
        assert their_tag is not None
        assert our_tag.text == their_tag.text


# ── TestAppend ──


class TestAppend:
    def test_append_tag(self):
        ours = _ours("<div></div>")
        theirs = _theirs("<div></div>")
        our_div = ours.find("div")
        their_div = theirs.find("div")
        our_new = Tag("p", {})
        our_new.children.append("Appended")
        their_new = theirs.new_tag("p")
        their_new.string = "Appended"
        our_div.append(our_new)
        their_div.append(their_new)
        assert our_div.find("p").text == their_div.find("p").text

    def test_append_string(self):
        ours = _ours("<div></div>")
        theirs = _theirs("<div></div>")
        our_div = ours.find("div")
        their_div = theirs.find("div")
        our_div.append("hello")
        their_div.append("hello")
        assert our_div.get_text() == their_div.get_text()

    def test_append_detaches_from_old_parent(self):
        ours = _ours("<div><p>Child</p></div><section></section>")
        p = ours.find("p")
        section = ours.find("section")
        section.append(p)
        assert ours.find("div").find("p") is None
        assert section.find("p") is not None
        assert section.find("p").text == "Child"

    def test_append_sets_parent(self):
        ours = _ours("<div></div>")
        div = ours.find("div")
        child = Tag("span", {})
        div.append(child)
        assert child.parent is div

    def test_append_multiple(self):
        ours = _ours("<ul></ul>")
        ul = ours.find("ul")
        for i in range(3):
            li = Tag("li", {})
            li.children.append(f"Item {i}")
            ul.append(li)
        assert len(ul.find_all("li")) == 3


# ── TestInsert ──


class TestInsert:
    def test_insert_at_beginning(self):
        ours = _ours("<div><p>Second</p></div>")
        div = ours.find("div")
        new_p = Tag("p", {})
        new_p.children.append("First")
        div.insert(0, new_p)
        ps = div.find_all("p")
        assert len(ps) == 2
        assert ps[0].text == "First"
        assert ps[1].text == "Second"

    def test_insert_at_end(self):
        ours = _ours("<div><p>First</p></div>")
        div = ours.find("div")
        new_p = Tag("p", {})
        new_p.children.append("Last")
        div.insert(999, new_p)  # beyond end => append
        ps = div.find_all("p")
        assert len(ps) == 2
        assert ps[-1].text == "Last"

    def test_insert_in_middle(self):
        ours = _ours("<div><p>A</p><p>C</p></div>")
        div = ours.find("div")
        new_p = Tag("p", {})
        new_p.children.append("B")
        div.insert(1, new_p)
        ps = div.find_all("p")
        assert [p.text for p in ps] == ["A", "B", "C"]

    def test_insert_string(self):
        ours = _ours("<div><p>After</p></div>")
        div = ours.find("div")
        div.insert(0, "Before text ")
        assert div.get_text().startswith("Before text ")

    def test_insert_detaches_from_old_parent(self):
        ours = _ours("<div><span>X</span></div><section><p>Y</p></section>")
        span = ours.find("span")
        section = ours.find("section")
        section.insert(0, span)
        assert ours.find("div").find("span") is None
        children = [c for c in section.children if isinstance(c, Tag)]
        assert children[0].name == "span"


# ── TestExtractMethod ──


class TestExtractMethod:
    def test_extract_removes_from_parent(self):
        ours = _ours("<div><p>Keep</p><p>Remove</p></div>")
        theirs = _theirs("<div><p>Keep</p><p>Remove</p></div>")
        our_ps = ours.find_all("p")
        their_ps = theirs.find_all("p")
        our_ps[1].extract()
        their_ps[1].extract()
        assert len(ours.find_all("p")) == len(theirs.find_all("p"))
        assert len(ours.find_all("p")) == 1

    def test_extract_keeps_subtree(self):
        ours = _ours("<div><ul><li>A</li><li>B</li></ul></div>")
        ul = ours.find("ul")
        extracted = ul.extract()
        assert extracted.name == "ul"
        assert len(extracted.find_all("li")) == 2
        assert extracted.parent is None

    def test_extract_returns_self(self):
        ours = _ours("<div><span>X</span></div>")
        span = ours.find("span")
        result = span.extract()
        assert result is span

    def test_extract_idempotent(self):
        ours = _ours("<div><span>X</span></div>")
        span = ours.find("span")
        span.extract()
        # Calling again on detached element should not crash.
        result = span.extract()
        assert result is span
        assert span.parent is None


# ── TestReplaceWith ──


class TestReplaceWith:
    def test_replace_tag(self):
        ours = _ours("<div><p>Old</p></div>")
        theirs = _theirs("<div><p>Old</p></div>")
        our_p = ours.find("p")
        their_p = theirs.find("p")
        our_new = Tag("span", {})
        our_new.children.append("New")
        their_new = theirs.new_tag("span")
        their_new.string = "New"
        our_p.replace_with(our_new)
        their_p.replace_with(their_new)
        assert ours.find("span").text == theirs.find("span").text
        assert ours.find("p") is None

    def test_replace_with_string(self):
        ours = _ours("<div><p>Remove me</p></div>")
        p = ours.find("p")
        p.replace_with("Plain text")
        div = ours.find("div")
        assert "Plain text" in div.get_text()
        assert ours.find("p") is None

    def test_replace_detaches_old(self):
        ours = _ours("<div><p>Old</p></div>")
        p = ours.find("p")
        new_tag = Tag("span", {})
        old = p.replace_with(new_tag)
        assert old is p
        assert old.parent is None

    def test_replace_raises_on_detached(self):
        tag = Tag("p", {})
        with pytest.raises(ValueError):
            tag.replace_with(Tag("span", {}))


# ── TestUnwrap ──


class TestUnwrap:
    def test_unwrap_keeps_children(self):
        ours = _ours("<div><b><i>text</i></b></div>")
        b = ours.find("b")
        b.unwrap()
        # <b> should be gone, but <i> should remain inside <div>.
        assert ours.find("b") is None
        i = ours.find("i")
        assert i is not None
        assert i.text == "text"
        assert i.parent.name == "div"

    def test_unwrap_text_children(self):
        ours = _ours("<div><span>hello world</span></div>")
        span = ours.find("span")
        span.unwrap()
        assert ours.find("span") is None
        div = ours.find("div")
        assert "hello world" in div.get_text()

    def test_unwrap_mixed_children(self):
        ours = _ours("<div><span>Text <b>bold</b> more</span></div>")
        span = ours.find("span")
        span.unwrap()
        assert ours.find("span") is None
        div = ours.find("div")
        assert "Text" in div.get_text()
        assert div.find("b") is not None
        assert div.find("b").text == "bold"

    def test_unwrap_detached_noop(self):
        tag = Tag("span", {})
        tag.children.append("text")
        tag.unwrap()  # should not crash
        assert tag.parent is None


# ── TestSetDelItem ──


class TestSetDelItem:
    def test_set_attribute(self):
        ours = _ours("<div></div>")
        theirs = _theirs("<div></div>")
        our_div = ours.find("div")
        their_div = theirs.find("div")
        our_div["id"] = "main"
        their_div["id"] = "main"
        assert our_div["id"] == their_div["id"]

    def test_set_class(self):
        ours = _ours("<div></div>")
        div = ours.find("div")
        div["class"] = ["a", "b"]
        assert div["class"] == ["a", "b"]

    def test_overwrite_attribute(self):
        ours = _ours('<div id="old"></div>')
        div = ours.find("div")
        div["id"] = "new"
        assert div["id"] == "new"

    def test_delete_attribute(self):
        ours = _ours('<div id="test" class="x"></div>')
        theirs = _theirs('<div id="test" class="x"></div>')
        our_div = ours.find("div")
        their_div = theirs.find("div")
        del our_div["id"]
        del their_div["id"]
        assert "id" not in our_div
        assert "id" not in their_div

    def test_delete_missing_raises(self):
        ours = _ours("<div></div>")
        div = ours.find("div")
        with pytest.raises(KeyError):
            del div["nonexistent"]


# ── TestToHtml ──


class TestToHtml:
    def test_simple_tag(self):
        ours = _ours("<p>Hello</p>")
        p = ours.find("p")
        html = p.to_html()
        assert html == "<p>Hello</p>"

    def test_nested_tags(self):
        ours = _ours("<div><p>A</p><p>B</p></div>")
        div = ours.find("div")
        html = div.to_html()
        assert "<div>" in html
        assert "<p>A</p>" in html
        assert "<p>B</p>" in html
        assert html.endswith("</div>")

    def test_self_closing_tags(self):
        ours = _ours("<p>Before<br>After</p>")
        p = ours.find("p")
        html = p.to_html()
        assert "<br>" in html
        # <br> should NOT have a closing tag.
        assert "</br>" not in html

    def test_attributes_preserved(self):
        ours = _ours('<a href="/x" id="link1">Click</a>')
        a = ours.find("a")
        html = a.to_html()
        assert 'href="/x"' in html
        assert 'id="link1"' in html
        assert "Click" in html

    def test_class_list_joined(self):
        ours = _ours('<div class="a b c">X</div>')
        div = ours.find("div")
        html = div.to_html()
        assert 'class="a b c"' in html

    def test_boolean_attribute(self):
        ours = _ours("<input disabled>")
        inp = ours.find("input")
        html = inp.to_html()
        assert "disabled" in html

    def test_str_equals_to_html(self):
        ours = _ours("<div><p>Hello</p></div>")
        div = ours.find("div")
        assert str(div) == div.to_html()

    def test_soup_to_html(self):
        html_str = "<html><body><p>Test</p></body></html>"
        ours = _ours(html_str)
        result = ours.to_html()
        assert "<p>Test</p>" in result
        assert "<html>" in result

    def test_roundtrip_preserves_structure(self):
        """Parse -> to_html -> re-parse should give same text."""
        ours = _ours(REAL_WORLD_HTML)
        html2 = ours.to_html()
        reparsed = _ours(html2)
        # Same tag count
        assert len(ours.find_all("div")) == len(reparsed.find_all("div"))
        assert len(ours.find_all("a")) == len(reparsed.find_all("a"))


# ── TestNewTag ──


class TestNewTag:
    def test_new_tag_basic(self):
        ours = _ours("<div></div>")
        tag = ours.new_tag("span")
        assert tag.name == "span"
        assert tag.parent is None
        assert tag.children == []

    def test_new_tag_with_attrs(self):
        ours = _ours("<div></div>")
        tag = ours.new_tag("a", {"href": "/link", "class": ["nav"]})
        assert tag["href"] == "/link"
        assert tag["class"] == ["nav"]

    def test_new_tag_append_to_tree(self):
        ours = _ours("<div></div>")
        div = ours.find("div")
        span = ours.new_tag("span")
        span.children.append("Added")
        div.append(span)
        assert div.find("span").text == "Added"


# ── TestPseudoSelectors ──

PSEUDO_HTML = """
<ul>
    <li class="a">First</li>
    <li class="b">Second</li>
    <li class="c">Third</li>
</ul>
<div><span class="only">Alone</span></div>
<ol>
    <li class="x">Alpha</li>
</ol>
"""


class TestPseudoSelectors:
    """CSS pseudo-selector tests: compare zerodep soup vs beautifulsoup4."""

    def test_first_child(self):
        ours = _ours(PSEUDO_HTML)
        theirs = _theirs(PSEUDO_HTML)
        assert len(ours.select("li:first-child")) == len(
            theirs.select("li:first-child")
        )
        assert ours.select("li:first-child")[0].text == "First"

    def test_last_child(self):
        ours = _ours(PSEUDO_HTML)
        theirs = _theirs(PSEUDO_HTML)
        assert len(ours.select("li:last-child")) == len(theirs.select("li:last-child"))
        assert ours.select("li:last-child")[0].text == "Third"

    def test_only_child(self):
        ours = _ours(PSEUDO_HTML)
        theirs = _theirs(PSEUDO_HTML)
        our_results = ours.select("span:only-child")
        their_results = theirs.select("span:only-child")
        assert len(our_results) == len(their_results)
        assert our_results[0].text == "Alone"

    def test_only_child_li(self):
        ours = _ours(PSEUDO_HTML)
        theirs = _theirs(PSEUDO_HTML)
        our_results = ours.select("li:only-child")
        their_results = theirs.select("li:only-child")
        assert len(our_results) == len(their_results)
        assert our_results[0].text == "Alpha"

    def test_not_class(self):
        ours = _ours(PSEUDO_HTML)
        theirs = _theirs(PSEUDO_HTML)
        our_results = ours.select("li:not(.a)")
        their_results = theirs.select("li:not(.a)")
        assert len(our_results) == len(their_results)

    def test_not_tag(self):
        html = "<div><span>A</span><em>B</em><span>C</span></div>"
        ours = _ours(html)
        theirs = _theirs(html)
        our_results = ours.select("div > :not(span)")
        their_results = theirs.select("div > :not(span)")
        assert len(our_results) == len(their_results)
        assert our_results[0].text == "B"

    def test_first_child_with_class(self):
        html = '<div><p class="x">1</p><p class="x">2</p></div>'
        ours = _ours(html)
        theirs = _theirs(html)
        our_results = ours.select("p.x:first-child")
        their_results = theirs.select("p.x:first-child")
        assert len(our_results) == len(their_results)
        assert our_results[0].text == "1"

    def test_last_child_descendant(self):
        ours = _ours(PSEUDO_HTML)
        theirs = _theirs(PSEUDO_HTML)
        our_results = ours.select("ul li:last-child")
        their_results = theirs.select("ul li:last-child")
        assert len(our_results) == len(their_results)
        assert our_results[0].text == "Third"

    def test_not_with_id(self):
        html = '<div><p id="a">A</p><p id="b">B</p><p id="c">C</p></div>'
        ours = _ours(html)
        theirs = _theirs(html)
        our_results = ours.select("p:not(#b)")
        their_results = theirs.select("p:not(#b)")
        assert len(our_results) == len(their_results)
        assert [t.text for t in our_results] == ["A", "C"]

    def test_combined_pseudo_selectors(self):
        html = '<ul><li class="a">Only</li></ul>'
        ours = _ours(html)
        theirs = _theirs(html)
        our_results = ours.select("li:first-child:last-child")
        their_results = theirs.select("li:first-child:last-child")
        assert len(our_results) == len(their_results)
        assert our_results[0].text == "Only"

    def test_first_child_no_match(self):
        html = "<div><span>A</span><p>B</p></div>"
        ours = _ours(html)
        theirs = _theirs(html)
        assert len(ours.select("p:first-child")) == len(theirs.select("p:first-child"))
        assert len(ours.select("p:first-child")) == 0

    def test_not_first_child(self):
        ours = _ours(PSEUDO_HTML)
        theirs = _theirs(PSEUDO_HTML)
        our_results = ours.select("li:not(:first-child)")
        their_results = theirs.select("li:not(:first-child)")
        assert len(our_results) == len(their_results)
