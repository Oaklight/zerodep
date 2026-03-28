"""Benchmark: zerodep frontmatter vs python-frontmatter."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from frontmatter import dumps as zd_dumps
from frontmatter import loads as zd_loads

pfm = pytest.importorskip("frontmatter", reason="python-frontmatter not installed")


# ── Test data ──

SMALL = """\
---
title: Hello World
---
A short post.
"""

MEDIUM = """\
---
title: A Medium Post
date: 2026-03-28
author: Alice
tags:
  - python
  - programming
  - zerodep
  - frontmatter
category: tutorial
draft: false
summary: This is a medium-length post with several metadata fields.
---
# Introduction

This is a medium-length document with several paragraphs of content.

## Section One

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam.

## Section Two

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore
eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident.

## Conclusion

Sunt in culpa qui officia deserunt mollit anim id est laborum.
"""

_LARGE_META = "\n".join(f"field_{i}: value_{i}" for i in range(50))
_LARGE_BODY = "\n\n".join(
    f"Paragraph {i}. " + "Lorem ipsum dolor sit amet. " * 10 for i in range(50)
)
LARGE = f"---\ntitle: Large Document\n{_LARGE_META}\n---\n{_LARGE_BODY}\n"


# ── Helpers ──


def _zd_parse(text: str):
    return zd_loads(text)


def _ref_parse(text: str):
    return pfm.loads(text)


def _zd_serialize(text: str):
    doc = zd_loads(text)
    return zd_dumps(doc)


def _ref_serialize(text: str):
    post = pfm.loads(text)
    return pfm.dumps(post)


# ── Parse benchmarks ──


class TestParseSmall:
    def test_zerodep(self, benchmark):
        benchmark(_zd_parse, SMALL)

    def test_python_frontmatter(self, benchmark):
        benchmark(_ref_parse, SMALL)


class TestParseMedium:
    def test_zerodep(self, benchmark):
        benchmark(_zd_parse, MEDIUM)

    def test_python_frontmatter(self, benchmark):
        benchmark(_ref_parse, MEDIUM)


class TestParseLarge:
    def test_zerodep(self, benchmark):
        benchmark(_zd_parse, LARGE)

    def test_python_frontmatter(self, benchmark):
        benchmark(_ref_parse, LARGE)


# ── Serialize benchmarks ──


class TestSerializeSmall:
    def test_zerodep(self, benchmark):
        benchmark(_zd_serialize, SMALL)

    def test_python_frontmatter(self, benchmark):
        benchmark(_ref_serialize, SMALL)


class TestSerializeMedium:
    def test_zerodep(self, benchmark):
        benchmark(_zd_serialize, MEDIUM)

    def test_python_frontmatter(self, benchmark):
        benchmark(_ref_serialize, MEDIUM)


class TestSerializeLarge:
    def test_zerodep(self, benchmark):
        benchmark(_zd_serialize, LARGE)

    def test_python_frontmatter(self, benchmark):
        benchmark(_ref_serialize, LARGE)
