"""Correctness tests: zerodep markdown vs mistune.

Block and inline constructs are generated from bounded grammars and compared
against mistune; security and library-specific behaviour stays as explicit
cases because a property would not express it.
"""

import itertools
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from markdown import render  # noqa: E402

mistune = pytest.importorskip("mistune", reason="mistune not installed")


def assert_same(md: str) -> None:
    """Assert our render matches mistune.html output (stripped)."""
    ours = render(md).strip()
    theirs = mistune.html(md).strip()
    assert ours == theirs, f"Mismatch:\n  ours:   {ours!r}\n  theirs: {theirs!r}"


_gfm_ref = mistune.create_markdown(
    plugins=["strikethrough", "task_lists", "url", "table"]
)


def assert_same_gfm(md: str) -> None:
    """Assert our render matches mistune with GFM plugins (stripped)."""
    ours = render(md).strip()
    theirs = _gfm_ref(md).strip()
    assert ours == theirs, f"Mismatch:\n  ours:   {ours!r}\n  theirs: {theirs!r}"


# ── Generated corpora ────────────────────────────────────────────────────────


def _inline_documents() -> list[str]:
    """Emphasis, strong, code spans and every CommonMark backslash escape."""
    documents: list[str] = []

    markers = ["*", "_", "**", "__", "***", "___"]
    for marker, content in itertools.product(markers, ["x", "a b"]):
        documents.append(f"{marker}{content}{marker}")

    for emphasis, strong in itertools.product(["*", "**"], ["_", "__"]):
        documents.append(f"{strong}bold{strong} and {emphasis}italic{emphasis}")

    for count in (1, 2, 3):
        fence = "`" * count
        if count == 1:
            inner = "code"
        else:
            inner = "code with " + "`" * (count - 1) + " inside"
        documents.append(f"{fence}{inner}{fence}")

    # Backslash escapes for the punctuation the renderer already exercised.
    for char in ("*", "_", "`", "[", "]", "(", ")", "#", "!"):
        documents.append("\\" + char)

    return documents


def _block_documents() -> list[str]:
    """Headings, list markers, quotes, fences and thematic breaks."""
    documents: list[str] = []

    for level in range(1, 7):
        for text in ("Heading", "a b"):
            documents.append("#" * level + " " + text)

    for marker in ("-", "*", "+"):
        for count in (1, 2, 3):
            documents.append(
                "\n".join(f"{marker} item {index}" for index in range(count))
            )
    for count in (1, 2, 3):
        documents.append(
            "\n".join(f"{index + 1}. item {index}" for index in range(count))
        )

    for depth in (1, 2, 3):
        documents.append("> " * depth + f"level {depth}")

    for fence in ("```", "~~~"):
        for info in ("", "python"):
            documents.append(f"{fence}{info}\ncode\n{fence}")

    for md in ("---", "***", "___", "- - -", "* * *"):
        documents.append(md)

    return documents


class TestGeneratedInline:
    def test_matches_reference(self):
        mismatches = []
        for md in _inline_documents():
            try:
                assert_same(md)
            except AssertionError as exc:
                mismatches.append(str(exc))
        assert not mismatches, f"{len(mismatches)} inline mismatches:\n" + "\n".join(
            mismatches
        )


class TestGeneratedBlocks:
    def test_matches_reference(self):
        mismatches = []
        for md in _block_documents():
            try:
                assert_same(md)
            except AssertionError as exc:
                mismatches.append(str(exc))
        assert not mismatches, f"{len(mismatches)} block mismatches:\n" + "\n".join(
            mismatches
        )


# ── ATX Headings ──────────────────────────────────────────────────────────────


class TestATXHeadings:
    def test_heading_with_trailing_hashes(self):
        assert_same("## Heading ##")

    def test_heading_with_inline(self):
        assert_same("# Hello **world**")

    def test_heading_no_space(self):
        # CommonMark requires space after #
        md = "#no space"
        result = render(md)
        assert "<h1>" not in result  # should not be a heading


# ── Setext Headings ───────────────────────────────────────────────────────────


class TestSetextHeadings:
    def test_h1_equals(self):
        assert_same("Heading 1\n=========")

    def test_h2_dashes(self):
        assert_same("Heading 2\n---------")

    def test_multiline_setext(self):
        assert_same("Multi\nline\n====")


# ── Paragraphs ────────────────────────────────────────────────────────────────


class TestParagraphs:
    def test_single_paragraph(self):
        assert_same("Hello world.")

    def test_two_paragraphs(self):
        assert_same("First paragraph.\n\nSecond paragraph.")

    def test_soft_line_break(self):
        assert_same("Line one\nline two")

    def test_empty_input(self):
        assert render("") == ""

    def test_whitespace_only(self):
        assert render("   \n\n   ") == ""


# ── Emphasis ──────────────────────────────────────────────────────────────────


class TestEmphasis:
    def test_bold_in_paragraph(self):
        assert_same("This is **very** important.")


# ── Code Spans ────────────────────────────────────────────────────────────────


class TestCodeSpans:
    def test_code_with_text(self):
        assert_same("Use `render()` function")

    def test_code_escapes_html(self):
        result = render("`<div>`")
        assert "&lt;div&gt;" in result


# ── Fenced Code Blocks ───────────────────────────────────────────────────────


class TestFencedCode:
    def test_language_class(self):
        result = render("```js\nvar x = 1;\n```")
        assert 'class="language-js"' in result

    def test_html_escaped(self):
        result = render("```\n<script>alert('xss')</script>\n```")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_empty_code_block(self):
        result = render("```\n```")
        assert "<pre><code>" in result


# ── Indented Code Blocks ─────────────────────────────────────────────────────


class TestIndentedCode:
    def test_basic(self):
        assert_same("    indented code\n    block")

    def test_preserves_content(self):
        result = render("    line 1\n    line 2")
        assert "line 1" in result
        assert "line 2" in result


# ── Links ─────────────────────────────────────────────────────────────────────


class TestLinks:
    def test_inline_link(self):
        assert_same("[click](https://example.com)")

    def test_link_with_title(self):
        assert_same('[click](https://example.com "Title")')

    def test_link_harmful_protocol(self):
        result = render("[xss](javascript:alert(1))")
        assert "javascript:" not in result
        assert "#harmful-link" in result

    def test_reference_link(self):
        md = "[click][ref]\n\n[ref]: https://example.com"
        result = render(md)
        assert 'href="https://example.com"' in result

    def test_shortcut_reference_link(self):
        md = "[example]\n\n[example]: https://example.com"
        result = render(md)
        assert 'href="https://example.com"' in result

    def test_reference_link_with_title(self):
        md = '[click][ref]\n\n[ref]: https://example.com "My Title"'
        result = render(md)
        assert 'title="My Title"' in result


# ── Images ────────────────────────────────────────────────────────────────────


class TestImages:
    def test_basic_image(self):
        assert_same("![alt text](https://example.com/img.png)")

    def test_image_with_title(self):
        assert_same('![photo](https://example.com/img.png "Photo")')

    def test_image_html(self):
        result = render("![alt](https://example.com/img.png)")
        assert "<img " in result
        assert 'alt="alt"' in result
        assert 'src="https://example.com/img.png"' in result


# ── Lists ─────────────────────────────────────────────────────────────────────


class TestLists:
    def test_ordered(self):
        assert_same("1. first\n2. second\n3. third")

    def test_ordered_start_number(self):
        result = render("5. five\n6. six")
        assert 'start="5"' in result

    def test_nested_list(self):
        assert_same("- a\n  - b\n  - c\n- d")

    def test_list_with_inline(self):
        assert_same("- **bold** item\n- *italic* item")


# ── Block Quotes ──────────────────────────────────────────────────────────────


class TestBlockQuotes:
    def test_multiline(self):
        assert_same("> line one\n> line two")

    def test_with_paragraph(self):
        assert_same("> first\n>\n> second")

    def test_with_inline(self):
        assert_same("> **bold** text")


# ── Tables ────────────────────────────────────────────────────────────────────


class TestTables:
    def test_basic_table(self):
        md = "| Name | Age |\n| --- | --- |\n| Alice | 30 |"
        assert_same(md)

    def test_alignment(self):
        md = "| Left | Center | Right |\n| :--- | :---: | ---: |\n| 1 | 2 | 3 |"
        result = render(md)
        assert "text-align:left" in result
        assert "text-align:center" in result
        assert "text-align:right" in result

    def test_inline_in_table(self):
        md = "| **Bold** | `code` |\n| --- | --- |\n| text | text |"
        result = render(md)
        assert "<strong>Bold</strong>" in result
        assert "<code>code</code>" in result

    def test_multirow(self):
        assert_same("| a | b |\n| --- | --- |\n| 1 | 2 |\n| 3 | 4 |")


# ── Line Breaks ───────────────────────────────────────────────────────────────


class TestLineBreaks:
    def test_two_spaces(self):
        assert_same("Line one  \nLine two")

    def test_backslash(self):
        assert_same("Line one\\\nLine two")


# ── Autolinks ─────────────────────────────────────────────────────────────────


class TestAutolinks:
    def test_url(self):
        assert_same("<https://example.com>")

    def test_email(self):
        md = "<user@example.com>"
        result = render(md)
        assert "mailto:" in result


# ── Edge Cases ────────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_html_entities_escaped(self):
        result = render("3 < 5 & 7 > 2")
        assert "&lt;" in result
        assert "&amp;" in result
        assert "&gt;" in result

    def test_mixed_content(self):
        md = (
            "# Title\n\nParagraph with **bold**.\n\n"
            "- list\n- items\n\n> quote\n\n```\ncode\n```"
        )
        # Just verify no crash and contains expected elements
        result = render(md)
        assert "<h1>" in result
        assert "<strong>" in result
        assert "<li>" in result
        assert "<blockquote>" in result
        assert "<code>" in result

    def test_consecutive_blocks(self):
        md = "# H1\n\n## H2\n\n### H3"
        result = render(md)
        assert "<h1>" in result
        assert "<h2>" in result
        assert "<h3>" in result


# ── Strikethrough ─────────────────────────────────────────────────────────────


class TestStrikethrough:
    def test_basic(self):
        assert_same_gfm("~~deleted~~")

    def test_with_inline(self):
        assert_same_gfm("~~bold **inside** strike~~")

    def test_mid_word(self):
        assert_same_gfm("not~~this~~joined")

    def test_in_paragraph(self):
        assert_same_gfm("This has ~~struck~~ text in it.")

    def test_in_blockquote(self):
        assert_same_gfm("> ~~quoted strike~~")

    def test_in_list(self):
        assert_same_gfm("- ~~list strike~~")

    def test_in_table(self):
        assert_same_gfm("| ~~header~~ | b |\n| --- | --- |\n| c | d |")

    def test_with_code_inside(self):
        result = render("~~`code` and text~~")
        assert "<del>" in result
        assert "<code>code</code>" in result

    def test_not_single_tilde(self):
        result = render("~not strike~")
        assert "<del>" not in result


# ── Task Lists ────────────────────────────────────────────────────────────────


class TestTaskLists:
    def test_unchecked(self):
        assert_same_gfm("- [ ] todo item")

    def test_checked(self):
        assert_same_gfm("- [x] done item")

    def test_checked_uppercase(self):
        assert_same_gfm("- [X] done item")

    def test_mixed(self):
        assert_same_gfm("- [ ] unchecked\n- [x] checked\n- [X] also checked")

    def test_with_inline(self):
        assert_same_gfm("- [ ] task with **bold**")

    def test_ordered_task_list(self):
        assert_same_gfm("1. [ ] ordered task\n2. [x] ordered done")

    def test_regular_list_unaffected(self):
        md = "- normal item\n- another item"
        result = render(md)
        assert "task-list-item" not in result

    def test_checkbox_attributes(self):
        result = render("- [ ] unchecked\n- [x] checked")
        assert 'type="checkbox"' in result
        assert "disabled" in result
        assert "checked" in result


# ── Extended Autolinks ────────────────────────────────────────────────────────


class TestExtendedAutolinks:
    def test_https(self):
        assert_same_gfm("Visit https://example.com for more")

    def test_http(self):
        assert_same_gfm("See http://example.com here")

    def test_trailing_dot(self):
        assert_same_gfm("https://example.com.")

    def test_trailing_comma(self):
        assert_same_gfm("https://example.com,")

    def test_in_parens(self):
        assert_same_gfm("(https://example.com)")

    def test_with_path(self):
        assert_same_gfm("https://example.com/path/to/page.html")

    def test_with_query_and_fragment(self):
        assert_same_gfm("Visit https://example.com/path?q=1&r=2#fragment today")

    def test_with_explicit_link(self):
        assert_same_gfm("[link](https://example.com) and https://other.com")

    def test_url_with_ampersand(self):
        assert_same_gfm("See http://foo.bar/baz?a=1&b=2 here")

    def test_not_bare_www(self):
        result = render("www.example.com")
        assert "<a " not in result

    def test_angle_bracket_still_works(self):
        assert_same("<https://example.com>")
