"""Correctness tests: zerodep markdown vs mistune."""

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


# ── ATX Headings ──────────────────────────────────────────────────────────────


class TestATXHeadings:
    @pytest.mark.parametrize("level", [1, 2, 3, 4, 5, 6])
    def test_heading_levels(self, level):
        md = "#" * level + " Heading"
        assert_same(md)

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
    def test_italic_asterisk(self):
        assert_same("*italic*")

    def test_italic_underscore(self):
        assert_same("_italic_")

    def test_bold_asterisk(self):
        assert_same("**bold**")

    def test_bold_underscore(self):
        assert_same("__bold__")

    def test_bold_italic(self):
        assert_same("***bold italic***")

    def test_mixed(self):
        assert_same("**bold** and *italic* and ***both***")

    def test_bold_in_paragraph(self):
        assert_same("This is **very** important.")


# ── Code Spans ────────────────────────────────────────────────────────────────


class TestCodeSpans:
    def test_simple_code(self):
        assert_same("`code`")

    def test_code_with_text(self):
        assert_same("Use `render()` function")

    def test_double_backtick(self):
        assert_same("``code with ` inside``")

    def test_code_escapes_html(self):
        result = render("`<div>`")
        assert "&lt;div&gt;" in result


# ── Fenced Code Blocks ───────────────────────────────────────────────────────


class TestFencedCode:
    def test_basic(self):
        assert_same("```\nhello\n```")

    def test_with_language(self):
        assert_same("```python\ndef foo():\n    pass\n```")

    def test_tilde_fence(self):
        assert_same("~~~\ncode\n~~~")

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
    def test_unordered_dash(self):
        assert_same("- item 1\n- item 2\n- item 3")

    def test_unordered_asterisk(self):
        assert_same("* item 1\n* item 2")

    def test_unordered_plus(self):
        assert_same("+ item 1\n+ item 2")

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
    def test_simple(self):
        assert_same("> blockquote")

    def test_multiline(self):
        assert_same("> line one\n> line two")

    def test_nested(self):
        assert_same("> outer\n> > inner")

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


# ── Thematic Breaks ──────────────────────────────────────────────────────────


class TestThematicBreaks:
    @pytest.mark.parametrize("md", ["---", "***", "___", "- - -", "* * *"])
    def test_variants(self, md):
        result = render(md)
        assert "<hr />" in result


# ── Line Breaks ───────────────────────────────────────────────────────────────


class TestLineBreaks:
    def test_two_spaces(self):
        assert_same("Line one  \nLine two")

    def test_backslash(self):
        assert_same("Line one\\\nLine two")


# ── Backslash Escapes ─────────────────────────────────────────────────────────


class TestBackslashEscapes:
    @pytest.mark.parametrize("char", ["*", "_", "`", "[", "]", "(", ")", "#", "!"])
    def test_escape_chars(self, char):
        md = f"\\{char}"
        result = render(md)
        assert "<em>" not in result or char not in "*_"
        assert char in result or f"&#{ord(char)};" in result


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
