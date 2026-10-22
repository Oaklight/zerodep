"""Benchmark: zerodep frontmatter vs python-frontmatter."""

import os
import sys

import pytest

# Every case here takes the ``benchmark`` fixture. Without the plugin
# they would be reported as errors rather than skipped, which reads as a
# broken tree for anyone who installed the module without the extras.
pytest.importorskip("pytest_benchmark")

_this_dir = os.path.dirname(os.path.abspath(__file__))
_repo_root = os.path.dirname(_this_dir)


def _outside_repo(entry: str) -> bool:
    """True for a ``sys.path`` entry that is not inside this repository."""
    path = os.path.abspath(entry or os.curdir)
    return path != _repo_root and not path.startswith(_repo_root + os.sep)


# This module is named like the reference, and pytest's prepend import mode
# puts ``frontmatter/`` on sys.path while collecting, so a plain
# ``import frontmatter`` binds the repo's own file and both sides of the
# benchmark measure the same implementation (#205).  The sibling module
# directories (``yaml/``) are on sys.path the same way and would be picked up
# as python-frontmatter's dependencies, so every entry inside the repository
# is hidden for the duration of the import.  Check where the reference came
# from afterwards: the collision must fail loudly.
_saved_path = sys.path[:]
sys.path = [p for p in sys.path if _outside_repo(p)]
_cached_frontmatter = sys.modules.pop("frontmatter", None)
# python-frontmatter imports PyYAML, which would otherwise stay cached and
# shadow the repo's sibling ``yaml`` module for the zerodep side below.
_cached_yaml = sys.modules.pop("yaml", None)
try:
    import frontmatter as pfm
except ModuleNotFoundError:
    pytest.skip("python-frontmatter not installed", allow_module_level=True)
else:
    _ref_file = os.path.abspath(getattr(pfm, "__file__", "") or "")
    if not _ref_file or _ref_file.startswith(_repo_root + os.sep):
        raise RuntimeError(
            "the benchmark imported the repo's own frontmatter module as the "
            "reference; the comparison would measure one implementation twice"
        )
    if not hasattr(pfm, "loads"):
        raise RuntimeError("Not the real python-frontmatter")
finally:
    sys.path = _saved_path
    sys.modules.pop("frontmatter", None)
    if _cached_frontmatter is not None:
        sys.modules["frontmatter"] = _cached_frontmatter
    sys.modules.pop("yaml", None)
    if _cached_yaml is not None:
        sys.modules["yaml"] = _cached_yaml

sys.path.insert(0, _this_dir)

from frontmatter import dumps as zd_dumps
from frontmatter import loads as zd_loads

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
