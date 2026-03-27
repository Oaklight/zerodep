"""Benchmark: zerodep SSE EventSource vs httpx-sse SSEDecoder."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from sse import EventSource

httpx_sse = pytest.importorskip("httpx_sse", reason="httpx-sse not installed")
from httpx_sse._decoders import SSEDecoder  # noqa: E402

# ── Test data generators ──


def _make_lines(n_events: int, data_lines: int = 1, data_len: int = 20) -> list[str]:
    """Generate a list of SSE lines (no trailing newlines).

    Args:
        n_events: Number of events to generate.
        data_lines: Number of ``data:`` lines per event.
        data_len: Length of each data value string.
    """
    payload = "x" * data_len
    lines: list[str] = []
    for i in range(n_events):
        lines.append("event: msg")
        lines.append(f"id: {i}")
        for _ in range(data_lines):
            lines.append(f"data: {payload}")
        lines.append("")  # empty line dispatches the event
    return lines


# Pre-build test data at module level
SMALL_LINES = _make_lines(10, data_lines=1, data_len=20)
MEDIUM_LINES = _make_lines(100, data_lines=3, data_len=50)
LARGE_LINES = _make_lines(1000, data_lines=1, data_len=200)


def _zd_parse(lines: list[str]) -> list:
    return list(EventSource(lines))


def _httpx_sse_parse(lines: list[str]) -> list:
    decoder = SSEDecoder()
    events = []
    for line in lines:
        sse = decoder.decode(line)
        if sse is not None:
            events.append(sse)
    return events


# ── Small stream (10 events, 1 data line, 20 chars) ──


class TestSmallStream:
    def test_zerodep(self, benchmark):
        result = benchmark(_zd_parse, SMALL_LINES)
        assert len(result) == 10

    def test_httpx_sse(self, benchmark):
        result = benchmark(_httpx_sse_parse, SMALL_LINES)
        assert len(result) == 10


# ── Medium stream (100 events, 3 data lines, 50 chars each) ──


class TestMediumStream:
    def test_zerodep(self, benchmark):
        result = benchmark(_zd_parse, MEDIUM_LINES)
        assert len(result) == 100

    def test_httpx_sse(self, benchmark):
        result = benchmark(_httpx_sse_parse, MEDIUM_LINES)
        assert len(result) == 100


# ── Large stream (1000 events, 1 data line, 200 chars) ──


class TestLargeStream:
    def test_zerodep(self, benchmark):
        result = benchmark(_zd_parse, LARGE_LINES)
        assert len(result) == 1000

    def test_httpx_sse(self, benchmark):
        result = benchmark(_httpx_sse_parse, LARGE_LINES)
        assert len(result) == 1000
