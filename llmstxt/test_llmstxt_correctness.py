"""Correctness tests for zerodep llmstxt parser."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from llmstxt import (  # noqa: E402
    LlmsTxtError,
    find_candidates,
    parse,
)

# ── Test data ────────────────────────────────────────────────────────────────

MINIMAL = "# My Project\n"

SIMPLE = """\
# My Project

> A brief description of the project.

Some extra detail here.

## Docs

- [Guide](https://example.com/guide.md): The main guide
- [API](https://example.com/api.md): API reference
"""

FULL = """\
# FastHTML

> FastHTML is a python library which brings together Starlette, Uvicorn, \
HTMX, and fastcore's `FT` "FastTags" into a library for creating \
server-rendered hypermedia applications.

FastHTML apps are just Starlette apps, so can be deployed to any platform.

The project is documented at https://docs.fastht.ml.

## Docs

- [FastHTML quick start](https://docs.fastht.ml/tutorials/quickstart.html.md): Overview
- [HTMX reference](https://docs.fastht.ml/explains/htmx.html.md): HTMX integration

## Examples

- [Todo app](https://docs.fastht.ml/tutorials/todo.html.md): A simple todo app
- [Chat app](https://docs.fastht.ml/tutorials/chat.html.md)

## Optional

- [Advanced deployment](https://docs.fastht.ml/explains/deploy.html.md): Deploy options
"""

NO_BLOCKQUOTE = """\
# Bare Project

Just some details, no blockquote.

## Links

- [Home](https://example.com/home.md): Homepage
"""

NO_DETAILS = """\
# No Details

> Has a description but no details.

## Links

- [Home](https://example.com/home.md)
"""

MULTI_BLOCKQUOTE = """\
# Multi

> First line of description.
> Second line continues.
> Third line.

## Docs

- [A](https://example.com/a.md)
"""

EMPTY_SECTION = """\
# Empty

> Desc

## Has Entries

- [A](https://example.com/a.md): a note

## Empty Section

## Another

- [B](https://example.com/b.md)
"""


# ── Test: parse() — title ────────────────────────────────────────────────────


class TestParseTitle:
    def test_simple_title(self):
        doc = parse(MINIMAL)
        assert doc.title == "My Project"

    def test_title_with_special_chars(self):
        doc = parse("# My `Project` — v2.0\n")
        assert doc.title == "My `Project` — v2.0"

    def test_missing_title_raises(self):
        with pytest.raises(LlmsTxtError, match="missing required H1"):
            parse("No heading here\n")

    def test_empty_input_raises(self):
        with pytest.raises(LlmsTxtError, match="empty input"):
            parse("")

    def test_whitespace_only_raises(self):
        with pytest.raises(LlmsTxtError, match="empty input"):
            parse("   \n\n  ")

    def test_leading_blank_lines(self):
        doc = parse("\n\n\n# Title\n")
        assert doc.title == "Title"


# ── Test: parse() — description ──────────────────────────────────────────────


class TestParseDescription:
    def test_single_line(self):
        doc = parse(SIMPLE)
        assert doc.description == "A brief description of the project."

    def test_multi_line(self):
        doc = parse(MULTI_BLOCKQUOTE)
        assert doc.description == (
            "First line of description.\nSecond line continues.\nThird line."
        )

    def test_missing_blockquote(self):
        doc = parse(NO_BLOCKQUOTE)
        assert doc.description == ""

    def test_full_description(self):
        doc = parse(FULL)
        assert "FastHTML" in doc.description
        assert "Starlette" in doc.description


# ── Test: parse() — details ──────────────────────────────────────────────────


class TestParseDetails:
    def test_single_paragraph(self):
        doc = parse(SIMPLE)
        assert doc.details == "Some extra detail here."

    def test_multi_paragraph(self):
        doc = parse(FULL)
        assert "documented at" in doc.details
        lines = doc.details.split("\n")
        assert len(lines) >= 2

    def test_missing_details(self):
        doc = parse(NO_DETAILS)
        assert doc.details == ""

    def test_no_blockquote_details_captured(self):
        doc = parse(NO_BLOCKQUOTE)
        assert doc.details == "Just some details, no blockquote."


# ── Test: parse() — sections ─────────────────────────────────────────────────


class TestParseSections:
    def test_single_section(self):
        doc = parse(SIMPLE)
        assert "Docs" in doc.sections
        assert len(doc.sections["Docs"]) == 2

    def test_multiple_sections(self):
        doc = parse(FULL)
        assert "Docs" in doc.sections
        assert "Examples" in doc.sections

    def test_entry_fields(self):
        doc = parse(SIMPLE)
        entry = doc.sections["Docs"][0]
        assert entry.name == "Guide"
        assert entry.url == "https://example.com/guide.md"
        assert entry.notes == "The main guide"

    def test_entry_without_notes(self):
        doc = parse(FULL)
        chat = doc.sections["Examples"][1]
        assert chat.name == "Chat app"
        assert chat.notes == ""

    def test_empty_section(self):
        doc = parse(EMPTY_SECTION)
        assert doc.sections["Empty Section"] == []
        assert len(doc.sections["Has Entries"]) == 1
        assert len(doc.sections["Another"]) == 1

    def test_non_link_lines_skipped(self):
        text = """\
# Test

## Mixed

Some random text here.

- [Valid](https://example.com/a.md): A link
Not a link line
- Another non-link
- [Also valid](https://example.com/b.md)
"""
        doc = parse(text)
        assert len(doc.sections["Mixed"]) == 2


# ── Test: parse() — optional ─────────────────────────────────────────────────


class TestParseOptional:
    def test_optional_populated(self):
        doc = parse(FULL)
        assert len(doc.optional) == 1
        assert doc.optional[0].name == "Advanced deployment"
        assert "Optional" not in doc.sections

    def test_optional_absent(self):
        doc = parse(SIMPLE)
        assert doc.optional == []

    def test_optional_case_sensitive(self):
        text = """\
# Test

## optional

- [A](https://example.com/a.md)
"""
        doc = parse(text)
        # lowercase "optional" is treated as a regular section
        assert "optional" in doc.sections
        assert doc.optional == []


# ── Test: parse() — edge cases ───────────────────────────────────────────────


class TestParseEdgeCases:
    def test_windows_line_endings(self):
        text = (
            "# Title\r\n\r\n> Desc\r\n\r\n## Docs\r\n\r\n- [A](https://a.md): note\r\n"
        )
        doc = parse(text)
        assert doc.title == "Title"
        assert doc.description == "Desc"
        assert len(doc.sections["Docs"]) == 1

    def test_minimal_file(self):
        doc = parse(MINIMAL)
        assert doc.title == "My Project"
        assert doc.description == ""
        assert doc.details == ""
        assert doc.sections == {}
        assert doc.optional == []

    def test_multiple_h1_takes_first(self):
        text = "# First\n\n# Second\n"
        doc = parse(text)
        assert doc.title == "First"

    def test_result_is_frozen(self):
        doc = parse(SIMPLE)
        with pytest.raises(AttributeError):
            doc.title = "new"  # type: ignore[misc]

    def test_entry_is_frozen(self):
        doc = parse(SIMPLE)
        entry = doc.sections["Docs"][0]
        with pytest.raises(AttributeError):
            entry.name = "new"  # type: ignore[misc]

    def test_url_with_query_in_entry(self):
        text = "# T\n\n## S\n\n- [A](https://example.com/a?v=1#frag): note\n"
        doc = parse(text)
        assert doc.sections["S"][0].url == "https://example.com/a?v=1#frag"


# ── Test: find_candidates() — heuristic fallback (no doc) ────────────────────


class TestCandidateMdUrls:
    def test_basic_path(self):
        results = find_candidates("https://example.com/docs/guide")
        urls = [r.url for r in results]
        assert urls == [
            "https://example.com/docs/guide.md",
            "https://example.com/docs/guide/index.md",
            "https://example.com/docs/guide/index.html.md",
        ]

    def test_trailing_slash(self):
        results = find_candidates("https://example.com/docs/")
        urls = [r.url for r in results]
        assert urls == [
            "https://example.com/docs/index.md",
            "https://example.com/docs/index.html.md",
        ]

    def test_root_url(self):
        results = find_candidates("https://example.com/")
        urls = [r.url for r in results]
        assert urls == [
            "https://example.com/index.md",
            "https://example.com/index.html.md",
        ]

    def test_root_no_slash(self):
        results = find_candidates("https://example.com")
        urls = [r.url for r in results]
        assert urls == [
            "https://example.com/index.md",
            "https://example.com/index.html.md",
        ]

    def test_already_md(self):
        results = find_candidates("https://example.com/guide.md")
        assert [r.url for r in results] == ["https://example.com/guide.md"]

    def test_strips_query_and_fragment(self):
        results = find_candidates("https://example.com/docs?q=1#section")
        assert results[0].url == "https://example.com/docs.md"

    def test_html_extension(self):
        results = find_candidates("https://example.com/guide.html")
        urls = [r.url for r in results]
        assert "https://example.com/guide.html.md" in urls

    def test_fallback_entries_have_empty_name(self):
        results = find_candidates("https://example.com/page")
        assert all(r.name == "" for r in results)


# ── Test: find_candidates() — with doc ───────────────────────────────────────


class TestFindCandidates:
    @pytest.fixture()
    def doc(self):
        return parse(FULL)

    def test_exact_match(self, doc):
        results = find_candidates(
            "https://docs.fastht.ml/tutorials/quickstart.html.md", doc=doc
        )
        assert len(results) >= 1
        assert results[0].name == "FastHTML quick start"

    def test_extension_match(self, doc):
        results = find_candidates(
            "https://docs.fastht.ml/tutorials/quickstart.html", doc=doc
        )
        assert len(results) >= 1
        assert results[0].name == "FastHTML quick start"

    def test_no_extension_match(self, doc):
        results = find_candidates(
            "https://docs.fastht.ml/tutorials/quickstart", doc=doc
        )
        assert len(results) >= 1

    def test_prefix_match(self, doc):
        results = find_candidates("https://docs.fastht.ml/tutorials", doc=doc)
        assert len(results) >= 2

    def test_no_match_falls_back_to_heuristic(self, doc):
        results = find_candidates("https://unrelated.example.com/page", doc=doc)
        # No llms.txt match, but heuristic fallback produces candidates
        assert len(results) >= 1
        assert all(r.name == "" for r in results)

    def test_finds_optional_entries(self, doc):
        results = find_candidates(
            "https://docs.fastht.ml/explains/deploy.html.md", doc=doc
        )
        assert len(results) == 1
        assert results[0].name == "Advanced deployment"

    def test_strips_query_fragment(self, doc):
        results = find_candidates(
            "https://docs.fastht.ml/tutorials/todo.html.md?v=1#top", doc=doc
        )
        assert len(results) >= 1
        assert results[0].name == "Todo app"

    def test_no_doc_uses_heuristic(self):
        results = find_candidates("https://example.com/page")
        assert len(results) == 3
        assert results[0].url == "https://example.com/page.md"
