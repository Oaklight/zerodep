"""Regression tests for incremental delivery of streamed bodies.

``HTTPResponse.read(n)`` on a buffered response blocks until ``n`` bytes or
EOF, so yielding from ``read(4096)`` batches small events until the buffer
fills or the stream ends.  For SSE and LLM token streams that turns a live
feed into a stall, which is what these tests pin down.
"""

from __future__ import annotations

import os
import socketserver
import sys
import threading
import time

import pytest

import httpclient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sse"))

from sse import EventSource

# Time the server stalls after each event.  A correct implementation returns
# the first event almost immediately; the old read(4096) loop waited for both
# stalls plus EOF.
EVENT_DELAY = 0.8


class _SseServer(socketserver.ThreadingTCPServer):
    """HTTP/1.1 server that emits two SSE events with a pause between them."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _SseHandler)


class _SseHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        if not self.rfile.readline():
            return
        while True:
            header = self.rfile.readline()
            if header in (b"\r\n", b"\n", b""):
                break
        self.wfile.write(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/event-stream\r\n"
            b"Transfer-Encoding: chunked\r\n"
            b"\r\n"
        )
        for payload in (b"data: 0\n\n", b"data: 1\n\n"):
            self.wfile.write(b"%x\r\n" % len(payload) + payload + b"\r\n")
            self.wfile.flush()
            time.sleep(EVENT_DELAY)
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()


@pytest.fixture
def sse_url():
    server = _SseServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        yield f"http://{host}:{port}/events"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_iter_bytes_yields_each_chunk_as_it_arrives(sse_url):
    with httpclient.get(sse_url, stream=True) as response:
        started = time.monotonic()
        first = next(response.iter_bytes())
        elapsed = time.monotonic() - started

    assert first == b"data: 0\n\n"
    assert elapsed < EVENT_DELAY / 2


def test_event_source_dispatches_without_waiting_for_the_stream_to_end(sse_url):
    with httpclient.get(sse_url, stream=True) as response:
        events = iter(EventSource(response.iter_lines()))
        started = time.monotonic()
        first = next(events)
        elapsed = time.monotonic() - started

    assert first.data == "0"
    assert elapsed < EVENT_DELAY / 2
