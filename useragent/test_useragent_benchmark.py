"""Benchmark: zerodep useragent vs ua-generator."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from useragent import generate

ua_generator = pytest.importorskip("ua_generator", reason="ua-generator not installed")


# ── Generate (default, random browser + platform) ──


class TestGenerateDefault:
    def test_zerodep(self, benchmark):
        benchmark(generate)

    def test_ua_generator(self, benchmark):
        benchmark(ua_generator.generate)


# ── Generate Chrome desktop ──


class TestGenerateChromeDesktop:
    def test_zerodep(self, benchmark):
        benchmark(generate, browser="chrome", device="desktop")

    def test_ua_generator(self, benchmark):
        benchmark(ua_generator.generate, browser=("chrome",), device="desktop")


# ── Generate Edge mobile ──


class TestGenerateEdgeMobile:
    def test_zerodep(self, benchmark):
        benchmark(generate, browser="edge", device="mobile")

    def test_ua_generator(self, benchmark):
        benchmark(ua_generator.generate, browser=("edge",), device="mobile")


# ── Headers generation ──


class TestHeadersGet:
    def test_zerodep(self, benchmark):
        def run():
            ua = generate(browser="chrome", device="desktop")
            return ua.headers.get()

        benchmark(run)

    def test_ua_generator(self, benchmark):
        def run():
            ua = ua_generator.generate(browser=("chrome",), device="desktop")
            return ua.headers.get()

        benchmark(run)
