"""Benchmark: zerodep llmstxt parser."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from llmstxt import find_candidates, parse  # noqa: E402

# ── Test data ────────────────────────────────────────────────────────────────

SMALL = """\
# My Project

> A brief description.

## Docs

- [Guide](https://example.com/guide.md): The main guide
- [API](https://example.com/api.md): API reference
- [FAQ](https://example.com/faq.md): Frequently asked questions
"""

MEDIUM = """\
# FastHTML

> FastHTML is a python library which brings together Starlette, Uvicorn, HTMX, and fastcore's FT FastTags into a library for creating server-rendered hypermedia applications.

FastHTML apps are just Starlette apps, so can be deployed to any platform that supports ASGI or WSGI.

The project is documented at https://docs.fastht.ml.

## Docs

- [Quick start](https://docs.fastht.ml/tutorials/quickstart.html.md): Getting started
- [HTMX reference](https://docs.fastht.ml/explains/htmx.html.md): HTMX integration
- [Components](https://docs.fastht.ml/explains/components.html.md): Component system
- [Routes](https://docs.fastht.ml/explains/routes.html.md): Routing overview
- [Forms](https://docs.fastht.ml/explains/forms.html.md): Form handling
- [Sessions](https://docs.fastht.ml/explains/sessions.html.md): Session management

## Tutorials

- [Todo app](https://docs.fastht.ml/tutorials/todo.html.md): A simple todo application
- [Chat app](https://docs.fastht.ml/tutorials/chat.html.md): Real-time chat
- [Blog](https://docs.fastht.ml/tutorials/blog.html.md): Blog engine tutorial
- [Dashboard](https://docs.fastht.ml/tutorials/dashboard.html.md): Data dashboard

## API Reference

- [Core](https://docs.fastht.ml/api/core.html.md): Core module API
- [HTML](https://docs.fastht.ml/api/html.html.md): HTML generation
- [HTTP](https://docs.fastht.ml/api/http.html.md): HTTP utilities
- [CLI](https://docs.fastht.ml/api/cli.html.md): Command line interface

## Optional

- [Advanced deployment](https://docs.fastht.ml/explains/deploy.html.md): Deploy options
- [Middleware](https://docs.fastht.ml/explains/middleware.html.md): Custom middleware
- [Testing](https://docs.fastht.ml/explains/testing.html.md): Testing guide
"""

_LARGE_ENTRIES = "\n".join(
    f"- [Entry {i}](https://example.com/section/entry-{i}.md): Description for entry {i}"
    for i in range(50)
)
_LARGE_SECTIONS = "\n\n".join(f"## Section {s}\n\n{_LARGE_ENTRIES}" for s in range(10))
LARGE = f"""\
# Large Project

> A very large llms.txt file for stress testing the parser.

This is a large project with many sections and entries. It is designed to test
the parser's performance with realistic but large inputs.

{_LARGE_SECTIONS}

## Optional

{_LARGE_ENTRIES}
"""

# ── Benchmarks: parse() ─────────────────────────────────────────────────────


class TestParseSmall:
    def test_zerodep(self, benchmark):
        benchmark(parse, SMALL)


class TestParseMedium:
    def test_zerodep(self, benchmark):
        benchmark(parse, MEDIUM)


class TestParseLarge:
    def test_zerodep(self, benchmark):
        benchmark(parse, LARGE)


# ── Benchmarks: candidate_md_urls() ─────────────────────────────────────────


class TestCandidateUrls:
    def test_zerodep(self, benchmark):
        benchmark(find_candidates, "https://example.com/docs/guide")
