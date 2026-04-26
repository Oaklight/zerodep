"""Benchmark: zerodep markdown vs mistune."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from markdown import render as zd_render  # noqa: E402

mistune = pytest.importorskip("mistune", reason="mistune not installed")

# ── Test data ──

SMALL = "# Hello **world**\n\nA paragraph with *emphasis* and `code`."

MEDIUM = "\n\n".join(
    [
        "# Document Title",
        "Intro paragraph with **bold**, *italic*, and `inline code`.",
        "## Section 1",
        "Some text with [a link](https://example.com) and ![image](img.png).",
        "```python\ndef hello():\n    print('world')\n```",
        "> A blockquote with **bold** text.\n> Second line.",
        "- item 1\n- item **2**\n- item 3\n  - nested a\n  - nested b",
        "1. first\n2. second\n3. third",
        "| Name | Age |\n| --- | --- |\n| Alice | 30 |\n| Bob | 25 |",
        "---",
        "Final paragraph with `code`, **bold**, and *italic*.",
    ]
)

MEDIUM_GFM = "\n\n".join(
    [
        "# Document with GFM Extensions",
        "Paragraph with ~~strikethrough~~ and **bold**.",
        "Visit https://example.com/docs for more info.",
        "See http://api.example.com/v2?key=abc&format=json here.",
        "- [ ] Write the code\n- [x] Write the tests\n- [ ] Review the PR",
        "1. [x] Step one complete\n2. [ ] Step two pending",
        "| Feature | Status |\n| --- | --- |\n| ~~old~~ | removed |\n| new | active |",
        "> Quote with ~~deleted~~ and https://example.com link.",
        "Mixed: **bold**, *italic*, ~~strike~~, `code`, https://example.com.",
    ]
)

LARGE = "\n\n".join(
    [
        f"{'#' * (i % 6 + 1)} Heading {i}\n\n"
        f"Paragraph {i} with **bold** and *italic* text. "
        f"Also a [link](https://example.com/{i}) here.\n\n"
        f"```\ncode block {i}\n```\n\n"
        f"> Quote {i}\n\n"
        f"- list item {i}a\n- list item {i}b"
        for i in range(50)
    ]
)

LARGE_GFM = "\n\n".join(
    [
        f"{'#' * (i % 6 + 1)} Heading {i}\n\n"
        f"Paragraph {i} with ~~strike {i}~~ and https://example.com/{i} link.\n\n"
        f"- [ ] task {i}a\n- [x] task {i}b\n\n"
        f"| col{i} | ~~old~~ |\n| --- | --- |\n| val | https://example.com |"
        for i in range(50)
    ]
)


def _ref_render(text: str) -> str:
    return mistune.html(text)


_gfm_ref = mistune.create_markdown(
    plugins=["strikethrough", "task_lists", "url", "table"]
)


def _ref_gfm_render(text: str) -> str:
    return _gfm_ref(text)


# ── Render benchmarks (CommonMark) ──


class TestRenderSmall:
    def test_zerodep(self, benchmark):
        benchmark(zd_render, SMALL)

    def test_mistune(self, benchmark):
        benchmark(_ref_render, SMALL)


class TestRenderMedium:
    def test_zerodep(self, benchmark):
        benchmark(zd_render, MEDIUM)

    def test_mistune(self, benchmark):
        benchmark(_ref_render, MEDIUM)


class TestRenderLarge:
    def test_zerodep(self, benchmark):
        benchmark(zd_render, LARGE)

    def test_mistune(self, benchmark):
        benchmark(_ref_render, LARGE)


# ── Render benchmarks (GFM extensions) ──


class TestRenderGFMMedium:
    def test_zerodep(self, benchmark):
        benchmark(zd_render, MEDIUM_GFM)

    def test_mistune(self, benchmark):
        benchmark(_ref_gfm_render, MEDIUM_GFM)


class TestRenderGFMLarge:
    def test_zerodep(self, benchmark):
        benchmark(zd_render, LARGE_GFM)

    def test_mistune(self, benchmark):
        benchmark(_ref_gfm_render, LARGE_GFM)
