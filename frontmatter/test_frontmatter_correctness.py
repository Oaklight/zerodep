"""Correctness tests: zerodep frontmatter vs python-frontmatter."""

import io
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from frontmatter import (
    Document,
    FrontmatterError,
    HandlerError,
    check,
    detect_handler,
    dump,
    dumps,
    load,
    loads,
)

pfm = pytest.importorskip("frontmatter", reason="python-frontmatter not installed")


# ── Test vectors ──

YAML_SIMPLE = """\
---
title: Hello World
date: 2026-01-15
---
This is the content.
"""

YAML_LISTS = """\
---
title: Post
tags:
  - python
  - zerodep
  - frontmatter
---
Body text here.
"""

YAML_NESTED = """\
---
title: Nested
author:
  name: Alice
  email: alice@example.com
---
Content.
"""

YAML_EMPTY_META = """\
---
---
Just content.
"""

YAML_MULTILINE_CONTENT = """\
---
title: Multi
---
Line one.

Line two.

Line three.
"""

NO_FRONTMATTER = """\
# Just a Markdown file

No frontmatter here.
"""

JSON_SIMPLE = """\
{"title": "Hello", "count": 42}
Some content after JSON.
"""


# ── Detection tests ──


class TestDetection:
    def test_yaml_detected(self):
        assert detect_handler(YAML_SIMPLE) == "yaml"

    def test_json_detected(self):
        assert detect_handler(JSON_SIMPLE) == "json"

    def test_none_detected(self):
        assert detect_handler(NO_FRONTMATTER) is None

    def test_check_true(self):
        assert check(YAML_SIMPLE) is True

    def test_check_false(self):
        assert check(NO_FRONTMATTER) is False

    def test_bom_handling(self):
        assert detect_handler("\ufeff---\ntitle: BOM\n---\n") == "yaml"


# ── YAML parsing tests ──


class TestYAMLParsing:
    def test_simple(self):
        doc = loads(YAML_SIMPLE)
        assert doc.metadata["title"] == "Hello World"
        assert doc.metadata["date"] == "2026-01-15"
        assert "content" in doc.content.lower() or "This is" in doc.content

    def test_lists(self):
        doc = loads(YAML_LISTS)
        assert doc.metadata["title"] == "Post"
        assert doc.metadata["tags"] == ["python", "zerodep", "frontmatter"]

    def test_nested(self):
        doc = loads(YAML_NESTED)
        assert doc.metadata["author"]["name"] == "Alice"
        assert doc.metadata["author"]["email"] == "alice@example.com"

    def test_empty_metadata(self):
        doc = loads(YAML_EMPTY_META)
        assert doc.metadata == {}
        assert "Just content" in doc.content

    def test_no_frontmatter(self):
        doc = loads(NO_FRONTMATTER)
        assert doc.metadata == {}
        assert doc.content == NO_FRONTMATTER

    def test_multiline_content(self):
        doc = loads(YAML_MULTILINE_CONTENT)
        assert doc.metadata["title"] == "Multi"
        assert "Line one" in doc.content
        assert "Line three" in doc.content


# ── Comparison with python-frontmatter ──


COMPARISON_CASES = [
    pytest.param(YAML_SIMPLE, id="simple"),
    pytest.param(YAML_LISTS, id="lists"),
    pytest.param(YAML_NESTED, id="nested"),
    pytest.param(YAML_MULTILINE_CONTENT, id="multiline"),
    pytest.param(NO_FRONTMATTER, id="no_frontmatter"),
]


class TestCompareWithReference:
    @pytest.mark.parametrize("text", COMPARISON_CASES)
    def test_metadata_matches(self, text: str):
        ours = loads(text)
        theirs = pfm.loads(text)
        assert ours.metadata == theirs.metadata

    @pytest.mark.parametrize("text", COMPARISON_CASES)
    def test_content_matches(self, text: str):
        ours = loads(text)
        theirs = pfm.loads(text)
        # Normalize whitespace for comparison
        assert ours.content.strip() == theirs.content.strip()


# ── JSON parsing tests ──


class TestJSONParsing:
    def test_simple(self):
        doc = loads(JSON_SIMPLE)
        assert doc.metadata["title"] == "Hello"
        assert doc.metadata["count"] == 42
        assert "content after JSON" in doc.content

    def test_nested_json(self):
        text = '{"a": {"b": 1}}\nBody.'
        doc = loads(text)
        assert doc.metadata["a"]["b"] == 1
        assert doc.content == "Body."

    def test_json_with_array(self):
        text = '{"tags": ["a", "b"]}\nContent.'
        doc = loads(text)
        assert doc.metadata["tags"] == ["a", "b"]


# ── Document dataclass tests ──


class TestDocument:
    def test_get(self):
        doc = Document({"title": "Hi"}, "Body")
        assert doc.get("title") == "Hi"
        assert doc.get("missing", "default") == "default"

    def test_getitem(self):
        doc = Document({"title": "Hi"}, "Body")
        assert doc["title"] == "Hi"
        with pytest.raises(KeyError):
            _ = doc["missing"]

    def test_setitem(self):
        doc = Document({}, "Body")
        doc["title"] = "New"
        assert doc.metadata["title"] == "New"

    def test_contains(self):
        doc = Document({"title": "Hi"}, "Body")
        assert "title" in doc
        assert "missing" not in doc

    def test_bool(self):
        assert bool(Document({"a": 1}, "")) is True
        assert bool(Document({}, "text")) is True
        assert bool(Document({}, "")) is False

    def test_keys_values_items(self):
        doc = Document({"a": 1, "b": 2}, "")
        assert set(doc.keys()) == {"a", "b"}
        assert set(doc.values()) == {1, 2}
        assert set(doc.items()) == {("a", 1), ("b", 2)}


# ── Serialization tests ──


class TestDumps:
    def test_yaml_roundtrip(self):
        original = loads(YAML_SIMPLE)
        text = dumps(original)
        restored = loads(text)
        assert restored.metadata == original.metadata
        assert restored.content.strip() == original.content.strip()

    def test_yaml_lists_roundtrip(self):
        original = loads(YAML_LISTS)
        text = dumps(original)
        restored = loads(text)
        assert restored.metadata == original.metadata

    def test_json_roundtrip(self):
        doc = Document({"title": "Test", "count": 5}, "Body.\n")
        text = dumps(doc, handler="json")
        restored = loads(text, handler="json")
        assert restored.metadata == doc.metadata

    def test_empty_metadata(self):
        doc = Document({}, "Just text.")
        text = dumps(doc)
        assert "---" in text
        restored = loads(text)
        assert restored.metadata == {}

    def test_unknown_handler(self):
        doc = Document({"a": 1}, "")
        with pytest.raises(HandlerError):
            dumps(doc, handler="xml")


# ── File I/O tests ──


class TestFileIO:
    def test_load_from_path(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text(YAML_SIMPLE, encoding="utf-8")
        doc = load(str(p))
        assert doc.metadata["title"] == "Hello World"

    def test_load_from_path_object(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text(YAML_SIMPLE, encoding="utf-8")
        doc = load(p)
        assert doc.metadata["title"] == "Hello World"

    def test_load_from_stream(self):
        doc = load(io.StringIO(YAML_SIMPLE))
        assert doc.metadata["title"] == "Hello World"

    def test_dump_to_path(self, tmp_path):
        p = tmp_path / "out.md"
        doc = Document({"title": "Written"}, "Content.\n")
        dump(doc, p)
        restored = load(p)
        assert restored.metadata["title"] == "Written"

    def test_dump_to_stream(self):
        buf = io.StringIO()
        doc = Document({"title": "Stream"}, "Content.\n")
        dump(doc, buf)
        buf.seek(0)
        restored = load(buf)
        assert restored.metadata["title"] == "Stream"


# ── Edge cases ──


class TestEdgeCases:
    def test_unclosed_fence(self):
        text = "---\ntitle: Broken\nNo closing fence."
        doc = loads(text)
        # Should treat as no frontmatter
        assert doc.metadata == {}

    def test_force_handler(self):
        doc = loads(YAML_SIMPLE, handler="yaml")
        assert doc.metadata["title"] == "Hello World"

    def test_non_dict_yaml_raises(self):
        text = "---\n- item1\n- item2\n---\nBody."
        with pytest.raises(FrontmatterError, match="mapping"):
            loads(text)

    def test_windows_line_endings(self):
        text = "---\r\ntitle: CRLF\r\n---\r\nBody.\r\n"
        doc = loads(text)
        assert doc.metadata["title"] == "CRLF"

    def test_only_frontmatter_no_body(self):
        text = "---\ntitle: Only Meta\n---\n"
        doc = loads(text)
        assert doc.metadata["title"] == "Only Meta"
        assert doc.content == ""

    def test_content_with_yaml_separator(self):
        text = "---\ntitle: Test\n---\nSome text\n---\nMore text after separator.\n"
        doc = loads(text)
        assert doc.metadata["title"] == "Test"
        assert "---" in doc.content
