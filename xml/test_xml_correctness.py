"""Correctness tests: zerodep XML vs xmltodict."""

import os
import sys

import pytest

# Our xml.py shadows the stdlib xml package AND xmltodict uses stdlib xml
# internally.  We need to import xmltodict *before* our module replaces
# sys.modules["xml"].
_this_dir = os.path.dirname(__file__)

# Import xmltodict with our dir removed from path
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
# Also clear any xml.* sub-module references that might be stale
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
    # Clear xmltodict's cached xml entries
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

from xml import (  # noqa: E402
    XMLError,
    extract_tags,
    parse,
    unparse,
)

# ── Helpers ──


def _ours(xml_str: str, **kwargs) -> dict | None:
    return parse(xml_str, **kwargs)


def _theirs(xml_str: str, **kwargs) -> dict | None:
    return _ref_parse(xml_str, **kwargs)


# ── Test vectors ──

BASIC_CASES = [
    pytest.param("<root/>", id="empty_root"),
    pytest.param("<root></root>", id="empty_root_explicit"),
    pytest.param("<root>hello</root>", id="text_only"),
    pytest.param("<root><a>1</a></root>", id="single_child"),
    pytest.param("<root><a>1</a><b>2</b></root>", id="two_children"),
    pytest.param("<root><a>1</a><b>2</b><c>3</c></root>", id="three_children"),
]

ATTRIBUTE_CASES = [
    pytest.param('<item id="1">hello</item>', id="one_attr"),
    pytest.param('<item id="1" type="test">hello</item>', id="two_attrs"),
    pytest.param('<item id="1"/>', id="attr_empty"),
    pytest.param('<item id="1" class="main">text</item>', id="attr_with_text"),
]

LIST_CASES = [
    pytest.param(
        "<root><item>a</item><item>b</item></root>",
        id="two_same_siblings",
    ),
    pytest.param(
        "<root><item>a</item><item>b</item><item>c</item></root>",
        id="three_same_siblings",
    ),
    pytest.param(
        "<root><x>1</x><y>2</y><x>3</x></root>",
        id="interleaved_siblings",
    ),
]

NESTED_CASES = [
    pytest.param("<root><a><b>deep</b></a></root>", id="two_levels"),
    pytest.param(
        "<root><a><b><c>very deep</c></b></a></root>",
        id="three_levels",
    ),
    pytest.param(
        "<root><person><name>Alice</name><age>30</age></person></root>",
        id="nested_mapping",
    ),
]

WHITESPACE_CASES = [
    pytest.param(
        "<root>\n  <a>1</a>\n  <b>2</b>\n</root>",
        id="indented",
    ),
    pytest.param(
        "<root>  hello  </root>",
        id="padded_text",
    ),
]

CDATA_CASES = [
    pytest.param(
        "<root><![CDATA[hello <world>]]></root>",
        id="cdata_section",
    ),
    pytest.param(
        "<root>prefix<![CDATA[ cdata ]]>suffix</root>",
        id="mixed_cdata",
    ),
]

ENTITY_CASES = [
    pytest.param("<root>&amp;</root>", id="amp_entity"),
    pytest.param("<root>&lt;tag&gt;</root>", id="lt_gt_entities"),
    pytest.param("<root>&quot;quoted&quot;</root>", id="quot_entity"),
]


# ── Test classes ──


class TestParseBasic:
    @pytest.mark.parametrize("xml_str", BASIC_CASES)
    def test_matches_reference(self, xml_str: str):
        assert _ours(xml_str) == _theirs(xml_str)


class TestParseAttributes:
    @pytest.mark.parametrize("xml_str", ATTRIBUTE_CASES)
    def test_matches_reference(self, xml_str: str):
        assert _ours(xml_str) == _theirs(xml_str)

    def test_no_attribs(self):
        xml_str = '<item id="1">hello</item>'
        ours = _ours(xml_str, xml_attribs=False)
        theirs = _theirs(xml_str, xml_attribs=False)
        assert ours == theirs

    def test_custom_prefix(self):
        xml_str = '<item id="1">hello</item>'
        ours = _ours(xml_str, attr_prefix="$")
        theirs = _theirs(xml_str, attr_prefix="$")
        assert ours == theirs


class TestParseLists:
    @pytest.mark.parametrize("xml_str", LIST_CASES)
    def test_matches_reference(self, xml_str: str):
        assert _ours(xml_str) == _theirs(xml_str)

    def test_force_list_tuple(self):
        xml_str = "<root><item>only one</item></root>"
        ours = _ours(xml_str, force_list=("item",))
        theirs = _theirs(xml_str, force_list=("item",))
        assert ours == theirs

    def test_force_list_true(self):
        xml_str = "<root><a>1</a><b>2</b></root>"
        ours = _ours(xml_str, force_list=True)
        theirs = _theirs(xml_str, force_list=True)
        assert ours == theirs


class TestParseNested:
    @pytest.mark.parametrize("xml_str", NESTED_CASES)
    def test_matches_reference(self, xml_str: str):
        assert _ours(xml_str) == _theirs(xml_str)


class TestParseWhitespace:
    @pytest.mark.parametrize("xml_str", WHITESPACE_CASES)
    def test_matches_reference(self, xml_str: str):
        assert _ours(xml_str) == _theirs(xml_str)

    def test_strip_false(self):
        xml_str = "<root>  hello  </root>"
        ours = _ours(xml_str, strip_whitespace=False)
        theirs = _theirs(xml_str, strip_whitespace=False)
        assert ours == theirs


class TestParseCdata:
    @pytest.mark.parametrize("xml_str", CDATA_CASES)
    def test_matches_reference(self, xml_str: str):
        assert _ours(xml_str) == _theirs(xml_str)


class TestParseEntities:
    @pytest.mark.parametrize("xml_str", ENTITY_CASES)
    def test_matches_reference(self, xml_str: str):
        assert _ours(xml_str) == _theirs(xml_str)


class TestParseForceCdata:
    def test_force_cdata(self):
        xml_str = "<root>hello</root>"
        ours = _ours(xml_str, force_cdata=True)
        theirs = _theirs(xml_str, force_cdata=True)
        assert ours == theirs


class TestParsePostprocessor:
    def test_type_cast(self):
        def pp(path, key, value):
            try:
                return key, int(value)
            except (ValueError, TypeError):
                return key, value

        xml_str = "<root><a>1</a><b>hello</b></root>"
        ours = _ours(xml_str, postprocessor=pp)
        theirs = _theirs(xml_str, postprocessor=pp)
        assert ours == theirs

    def test_skip_element(self):
        def pp(path, key, value):
            if key == "skip":
                return None
            return key, value

        xml_str = "<root><keep>1</keep><skip>2</skip></root>"
        ours = _ours(xml_str, postprocessor=pp)
        theirs = _theirs(xml_str, postprocessor=pp)
        assert ours == theirs


class TestParseSecurity:
    def test_entities_disabled_by_default(self):
        xml_str = '<!DOCTYPE foo [<!ENTITY xxe "pwned">]><root>&xxe;</root>'
        with pytest.raises(XMLError):
            parse(xml_str)


class TestParseInputTypes:
    def test_bytes(self):
        xml_bytes = b"<root><a>1</a></root>"
        assert parse(xml_bytes) == {"root": {"a": "1"}}

    def test_file_like(self):
        import io

        xml_str = "<root><a>1</a></root>"
        f = io.BytesIO(xml_str.encode())
        assert parse(f) == {"root": {"a": "1"}}


class TestParseSitemap:
    SITEMAP = """\
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/</loc>
    <lastmod>2024-01-01</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://example.com/about</loc>
    <lastmod>2024-01-02</lastmod>
  </url>
</urlset>"""

    def test_matches_reference(self):
        assert _ours(self.SITEMAP) == _theirs(self.SITEMAP)

    def test_structure(self):
        d = parse(self.SITEMAP)
        urls = d["urlset"]["url"]
        assert isinstance(urls, list)
        assert len(urls) == 2
        assert urls[0]["loc"] == "https://example.com/"


class TestParseRSS:
    RSS = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example Feed</title>
    <link>https://example.com</link>
    <item>
      <title>First Post</title>
      <link>https://example.com/first</link>
      <description>Hello world</description>
    </item>
    <item>
      <title>Second Post</title>
      <link>https://example.com/second</link>
      <description>Another post</description>
    </item>
  </channel>
</rss>"""

    def test_matches_reference(self):
        assert _ours(self.RSS) == _theirs(self.RSS)

    def test_structure(self):
        d = parse(self.RSS)
        items = d["rss"]["channel"]["item"]
        assert isinstance(items, list)
        assert len(items) == 2
        assert items[0]["title"] == "First Post"


class TestUnparseBasic:
    def test_simple(self):
        d = {"root": {"a": "1", "b": "2"}}
        result = unparse(d, full_document=False)
        # Parse it back and verify
        assert parse(result) == d

    def test_with_declaration(self):
        d = {"root": "hello"}
        result = unparse(d)
        assert result.startswith("<?xml")

    def test_without_declaration(self):
        d = {"root": "hello"}
        result = unparse(d, full_document=False)
        assert not result.startswith("<?xml")

    def test_not_dict(self):
        with pytest.raises(XMLError):
            unparse("not a dict")

    def test_multiple_roots(self):
        with pytest.raises(XMLError):
            unparse({"a": "1", "b": "2"})


class TestUnparseAttributes:
    def test_attrs(self):
        d = {"item": {"@id": "1", "#text": "hello"}}
        result = unparse(d, full_document=False)
        parsed = parse(result)
        assert parsed == d

    def test_attrs_only(self):
        d = {"item": {"@id": "1", "@class": "test"}}
        result = unparse(d, full_document=False)
        parsed = parse(result)
        assert parsed["item"]["@id"] == "1"
        assert parsed["item"]["@class"] == "test"


class TestUnparsePretty:
    def test_pretty(self):
        d = {"root": {"a": "1", "b": "2"}}
        result = unparse(d, pretty=True, full_document=False)
        assert "\n" in result
        assert "\t" in result

    def test_custom_indent(self):
        d = {"root": {"a": "1"}}
        result = unparse(d, pretty=True, indent="  ", full_document=False)
        assert "  " in result


class TestUnparsePreprocessor:
    def test_skip_key(self):
        def pp(key, value):
            if key == "skip":
                return None
            return key, value

        d = {"root": {"keep": "1", "skip": "2"}}
        result = unparse(d, full_document=False, preprocessor=pp)
        parsed = parse(result)
        assert "keep" in parsed["root"]
        assert "skip" not in parsed.get("root", {})


class TestRoundTrip:
    """Test that parse(unparse(d)) == d for various structures."""

    ROUND_TRIP_CASES = [
        pytest.param({"root": "hello"}, id="simple_text"),
        pytest.param({"root": {"a": "1", "b": "2"}}, id="two_children"),
        pytest.param({"root": {"a": {"b": "deep"}}}, id="nested"),
        pytest.param({"root": {"item": ["a", "b", "c"]}}, id="list"),
        pytest.param(
            {"root": {"@id": "1", "#text": "hello"}},
            id="attrs_and_text",
        ),
        pytest.param(
            {
                "root": {
                    "person": [
                        {"name": "Alice", "age": "30"},
                        {"name": "Bob", "age": "25"},
                    ]
                }
            },
            id="list_of_dicts",
        ),
    ]

    @pytest.mark.parametrize("data", ROUND_TRIP_CASES)
    def test_round_trip(self, data: dict):
        xml_str = unparse(data, full_document=False)
        result = parse(xml_str)
        assert result == data


class TestUnparseList:
    def test_list_elements(self):
        d = {"root": {"item": ["a", "b", "c"]}}
        result = unparse(d, full_document=False)
        parsed = parse(result)
        assert parsed == d

    def test_list_of_dicts(self):
        d = {
            "root": {
                "item": [
                    {"@id": "1", "#text": "a"},
                    {"@id": "2", "#text": "b"},
                ]
            }
        }
        result = unparse(d, full_document=False)
        parsed = parse(result)
        assert parsed == d


# ── extract_tags tests (standalone, no reference library) ──


class TestExtractTagsBasic:
    def test_simple(self):
        tags = extract_tags("<answer>42</answer>", "answer")
        assert len(tags) == 1
        assert tags[0].tag == "answer"
        assert tags[0].content == "42"
        assert tags[0].is_closed is True
        assert tags[0].attrs == {}

    def test_multiple(self):
        text = "<a>1</a><b>2</b><a>3</a>"
        tags = extract_tags(text, "a")
        assert len(tags) == 2
        assert tags[0].content == "1"
        assert tags[1].content == "3"

    def test_all_tags(self):
        text = "<a>1</a><b>2</b>"
        tags = extract_tags(text)
        assert len(tags) == 2
        assert tags[0].tag == "a"
        assert tags[1].tag == "b"


class TestExtractTagsUnclosed:
    def test_unclosed(self):
        tags = extract_tags("<thinking>let me reason", "thinking")
        assert len(tags) == 1
        assert tags[0].content == "let me reason"
        assert tags[0].is_closed is False

    def test_truncated(self):
        tags = extract_tags("<answer>the answer is 4")
        assert len(tags) == 1
        assert tags[0].is_closed is False

    def test_mixed_closed_unclosed(self):
        text = "<a>closed</a><b>not closed"
        tags = extract_tags(text)
        assert len(tags) == 2
        assert tags[0].is_closed is True
        assert tags[1].is_closed is False


class TestExtractTagsMalformed:
    def test_nested_same_name(self):
        text = "<div><div>inner</div></div>"
        tags = extract_tags(text, "div")
        assert len(tags) == 2
        assert tags[0].content == "<div>inner</div>"
        assert tags[0].is_closed is True

    def test_tags_in_plain_text(self):
        text = "Hello, here is my answer: <answer>42</answer>. Done."
        tags = extract_tags(text, "answer")
        assert len(tags) == 1
        assert tags[0].content == "42"


class TestExtractTagsAttributes:
    def test_with_attrs(self):
        tags = extract_tags('<tag key="value" num="1">content</tag>')
        assert len(tags) == 1
        assert tags[0].attrs == {"key": "value", "num": "1"}
        assert tags[0].content == "content"

    def test_single_quoted_attrs(self):
        tags = extract_tags("<tag key='value'>content</tag>")
        assert len(tags) == 1
        assert tags[0].attrs == {"key": "value"}


class TestExtractTagsSelfClosing:
    def test_self_closing(self):
        tags = extract_tags("<br/>")
        assert len(tags) == 1
        assert tags[0].tag == "br"
        assert tags[0].content == ""
        assert tags[0].is_closed is True

    def test_self_closing_with_attrs(self):
        tags = extract_tags('<img src="test.png"/>')
        assert len(tags) == 1
        assert tags[0].attrs == {"src": "test.png"}
        assert tags[0].is_closed is True


class TestExtractTagsFirstOnly:
    def test_first_only(self):
        text = "<a>1</a><a>2</a><a>3</a>"
        tags = extract_tags(text, "a", first_only=True)
        assert len(tags) == 1
        assert tags[0].content == "1"


class TestExtractTagsLLM:
    """Test patterns commonly seen in LLM output."""

    def test_thinking_answer(self):
        text = """<thinking>
Let me analyze this problem step by step.
The answer should be 42.
</thinking>

<answer>
The answer is 42.
</answer>"""
        thinking = extract_tags(text, "thinking")
        answer = extract_tags(text, "answer")
        assert len(thinking) == 1
        assert "step by step" in thinking[0].content
        assert len(answer) == 1
        assert "42" in answer[0].content

    def test_streaming_truncation(self):
        text = "<response>I'm generating a long response and it gets cut"
        tags = extract_tags(text, "response")
        assert len(tags) == 1
        assert tags[0].is_closed is False
        assert "cut" in tags[0].content

    def test_preamble_before_tag(self):
        text = "Sure, here's my analysis:\n\n<result>Important finding</result>"
        tags = extract_tags(text, "result")
        assert len(tags) == 1
        assert tags[0].content == "Important finding"

    def test_code_in_tags(self):
        text = '<code lang="python">def hello():\n    print("world")</code>'
        tags = extract_tags(text, "code")
        assert len(tags) == 1
        assert 'print("world")' in tags[0].content
        assert tags[0].attrs == {"lang": "python"}


class TestEdgeCases:
    def test_empty_string(self):
        assert extract_tags("") == []

    def test_no_tags(self):
        assert extract_tags("just plain text") == []

    def test_parse_malformed_raises(self):
        with pytest.raises(XMLError):
            parse("<root><unclosed>")

    def test_parse_empty_string(self):
        with pytest.raises(XMLError):
            parse("")

    def test_none_element(self):
        d = parse("<root><empty/></root>")
        assert d == {"root": {"empty": None}}
