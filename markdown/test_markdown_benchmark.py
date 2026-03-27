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


def _ref_render(text: str) -> str:
    return mistune.html(text)


# ── Render benchmarks ──


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
