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
        assert ours.find("title").text == theirs.find("title").text

    def test_nested_tags(self):
        ours = _ours(NESTED_HTML)
        theirs = _theirs(NESTED_HTML)
        assert ours.find("span").text == theirs.find("span").text

    def test_self_closing_br(self):
        ours = _ours(SELF_CLOSING_HTML)
        theirs = _theirs(SELF_CLOSING_HTML)
        assert len(ours.find_all("br")) == len(theirs.find_all("br"))

    def test_self_closing_img(self):
        ours = _ours(SELF_CLOSING_HTML)
        theirs = _theirs(SELF_CLOSING_HTML)
        assert ours.find("img")["src"] == theirs.find("img")["src"]

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
        assert ours.find("p").text == theirs.find("p").text

    def test_by_class(self):
        ours = _ours(NESTED_HTML)
        theirs = _theirs(NESTED_HTML)
        assert ours.find("div", class_="inner").find("span").text == (
            theirs.find("div", class_="inner").find("span").text
        )

    def test_by_id(self):
        ours = _ours(ATTRS_HTML)
        theirs = _theirs(ATTRS_HTML)
        assert ours.find("a", id="link1").text == theirs.find("a", id="link1").text

    def test_by_attribute_value(self):
        ours = _ours(ATTRS_HTML)
        theirs = _theirs(ATTRS_HTML)
        assert (
            ours.find("input", {"type": "text"})["name"]
            == (theirs.find("input", {"type": "text"})["name"])
        )

    def test_by_attribute_existence(self):
        ours = _ours(ATTRS_HTML)
        theirs = _theirs(ATTRS_HTML)
        our_result = ours.find("a", href=True)
        their_result = theirs.find("a", href=True)
        assert our_result.text == their_result.text

    def test_with_dict_attrs_class(self):
        ours = _ours(MULTI_CLASS_HTML)
        theirs = _theirs(MULTI_CLASS_HTML)
        assert ours.find("div", {"class": "one"}).text.strip() == (
            theirs.find("div", {"class": "one"}).text.strip()
        )

    def test_find_returns_none(self):
        ours = _ours(SIMPLE_HTML)
        theirs = _theirs(SIMPLE_HTML)
        assert ours.find("table") is None
        assert theirs.find("table") is None

    def test_find_none_name_matches_any(self):
        # find(None, class_=...) should match any tag with that class
        html = '<div class="x">A</div><span class="x">B</span>'
        assert _ours(html).find(None, class_="x").name == (
            _theirs(html).find(None, class_="x").name
        )

    def test_find_with_multiple_attrs(self):
        html = '<a href="/a" class="link">A</a><a href="/b" class="link">B</a>'
        ours = _ours(html)
        theirs = _theirs(html)
        our_result = ours.find("a", {"class": "link", "href": "/b"})
        their_result = theirs.find("a", {"class": "link", "href": "/b"})
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
        assert ours.select_one("h2").text == theirs.select_one("h2").text

    def test_select_one_not_found(self):
        ours = _ours(SIMPLE_HTML)
        assert ours.select_one("table") is None

    def test_select_one_class(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        assert ours.select_one(".logo").text == theirs.select_one(".logo").text

    def test_select_one_descendant(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        assert ours.select_one("nav .logo").text == (
            theirs.select_one("nav .logo").text
        )


# ── TestGetText ──


class TestGetText:
    def test_simple(self):
        ours = _ours("<p>Hello <b>world</b></p>")
        theirs = _theirs("<p>Hello <b>world</b></p>")
        assert ours.find("p").get_text() == theirs.find("p").get_text()

    def test_with_separator(self):
        ours = _ours("<p>Hello <b>world</b></p>")
        theirs = _theirs("<p>Hello <b>world</b></p>")
        assert ours.find("p").get_text(separator="|") == (
            theirs.find("p").get_text(separator="|")
        )

    def test_with_strip(self):
        html = "<p>  Hello  <b>  world  </b>  </p>"
        ours = _ours(html)
        theirs = _theirs(html)
        assert ours.find("p").get_text(separator=" ", strip=True) == (
            theirs.find("p").get_text(separator=" ", strip=True)
        )

    def test_empty_element(self):
        ours = _ours("<div></div>")
        theirs = _theirs("<div></div>")
        assert ours.find("div").get_text() == theirs.find("div").get_text()


# ── TestTextProperty ──


class TestTextProperty:
    def test_text(self):
        ours = _ours("<p>Hello</p>")
        theirs = _theirs("<p>Hello</p>")
        assert ours.find("p").text == theirs.find("p").text

    def test_nested_text(self):
        ours = _ours("<div><p>Hello</p> <p>World</p></div>")
        theirs = _theirs("<div><p>Hello</p> <p>World</p></div>")
        assert ours.find("div").text == theirs.find("div").text

    def test_string_single_child(self):
        ours = _ours("<p>Hello</p>")
        theirs = _theirs("<p>Hello</p>")
        assert ours.find("p").string == theirs.find("p").string

    def test_string_nested_single(self):
        ours = _ours("<p><b>Hello</b></p>")
        theirs = _theirs("<p><b>Hello</b></p>")
        assert ours.find("p").string == theirs.find("p").string

    def test_string_multiple_children_none(self):
        ours = _ours("<p>Hello <b>World</b></p>")
        theirs = _theirs("<p>Hello <b>World</b></p>")
        assert ours.find("p").string is None
        assert theirs.find("p").string is None


# ── TestAttributes ──


class TestAttributes:
    def test_get(self):
        ours = _ours(ATTRS_HTML)
        theirs = _theirs(ATTRS_HTML)
        assert ours.find("a")["href"] == theirs.find("a")["href"]

    def test_get_default(self):
        ours = _ours(ATTRS_HTML)
        assert ours.find("a").get("nonexistent", "default") == "default"

    def test_getitem_raises(self):
        ours = _ours(ATTRS_HTML)
        with pytest.raises(KeyError):
            _ = ours.find("a")["nonexistent"]

    def test_attrs_dict(self):
        ours = _ours('<div id="test" class="a b">X</div>')
        theirs = _theirs('<div id="test" class="a b">X</div>')
        assert ours.find("div").attrs["id"] == theirs.find("div").attrs["id"]

    def test_class_as_list(self):
        ours = _ours('<div class="a b c">X</div>')
        theirs = _theirs('<div class="a b c">X</div>')
        assert ours.find("div")["class"] == theirs.find("div")["class"]

    def test_contains(self):
        ours = _ours(ATTRS_HTML)
        tag = ours.find("a")
        assert "href" in tag
        assert "nonexistent" not in tag

    def test_empty_attribute(self):
        ours = _ours("<input disabled>")
        tag = ours.find("input")
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
        assert ours.find("p").text == "Keep"

    def test_decompose_clears_children(self):
        html = "<div><span><b>Deep</b></span></div>"
        ours = _ours(html)
        span = ours.find("span")
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
        parent = span.find_parent()
        assert parent.name == "div"

    def test_named_parent(self):
        html = "<html><body><div><p><span>X</span></p></div></body></html>"
        ours = _ours(html)
        span = ours.find("span")
        div_parent = span.find_parent("div")
        assert div_parent is not None
        assert div_parent.name == "div"

    def test_parent_not_found(self):
        html = "<div><span>X</span></div>"
        ours = _ours(html)
        span = ours.find("span")
        assert span.find_parent("table") is None

    def test_find_parent_body(self):
        html = "<html><body><div><p>Text</p></div></body></html>"
        ours = _ours(html)
        p = ours.find("p")
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
        assert ours.find("b") is not None
        assert ours.find("b").text is not None

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
        assert ours.find("div").text == theirs.find("div").text


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
        assert ours.find("p").text == theirs.find("p").text

    def test_entities_lt_gt(self):
        ours = _ours("<p>&lt;tag&gt;</p>")
        theirs = _theirs("<p>&lt;tag&gt;</p>")
        assert ours.find("p").text == theirs.find("p").text

    def test_numeric_entity(self):
        ours = _ours("<p>&#169; 2024</p>")
        theirs = _theirs("<p>&#169; 2024</p>")
        assert ours.find("p").text == theirs.find("p").text

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
        assert ours.find("div").text == theirs.find("div").text

    def test_nested_find(self):
        html = "<div><ul><li>1</li><li>2</li></ul></div>"
        ours = _ours(html)
        theirs = _theirs(html)
        our_items = ours.find("ul").find_all("li")
        their_items = theirs.find("ul").find_all("li")
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
        assert ours.find("footer").get_text(strip=True) == (
            theirs.find("footer").get_text(strip=True)
        )

    def test_title(self):
        ours = _ours(REAL_WORLD_HTML)
        theirs = _theirs(REAL_WORLD_HTML)
        assert ours.find("title").text == theirs.find("title").text
