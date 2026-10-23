"""Tests for request timing milestones (zerodep#172)."""

from __future__ import annotations

import asyncio
import socketserver
import threading
import time

import pytest

import httpclient

HEADER_DELAY = 0.15
BODY_DELAY = 0.15


class _DelayedServer(socketserver.ThreadingTCPServer):
    """HTTP/1.1 server that stalls before the headers and again mid-body."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _DelayedHandler)


class _DelayedHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        while True:
            request_line = self.rfile.readline()
            if not request_line:
                return
            while True:
                header = self.rfile.readline()
                if header in (b"\r\n", b"\n", b""):
                    break
            time.sleep(HEADER_DELAY)
            self.wfile.write(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Length: 2\r\n"
                b"Content-Type: text/plain\r\n"
                b"\r\n"
            )
            self.wfile.flush()
            time.sleep(BODY_DELAY)
            self.wfile.write(b"hi")
            self.wfile.flush()


@pytest.fixture
def delayed_url():
    server = _DelayedServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        yield f"http://{host}:{port}/timing"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_non_streaming_reports_three_milestones(delayed_url):
    events: list[tuple[str, float]] = []
    response = httpclient.get(
        delayed_url, on_timing=lambda event, elapsed: events.append((event, elapsed))
    )

    assert response.status_code == 200
    assert [name for name, _ in events] == [
        "request_started",
        "headers_received",
        "body_complete",
    ]
    names = [elapsed for _, elapsed in events]
    assert names[0] == 0.0
    assert names[1] >= HEADER_DELAY * 0.6
    assert names[2] >= names[1] + BODY_DELAY * 0.6


def test_streaming_body_complete_waits_for_the_read(delayed_url):
    events: list[tuple[str, float]] = []
    response = httpclient.get(
        delayed_url,
        stream=True,
        on_timing=lambda event, elapsed: events.append((event, elapsed)),
    )
    assert [name for name, _ in events] == ["request_started", "headers_received"]

    # The body is still arriving; nothing is reported until it is consumed.
    time.sleep(BODY_DELAY * 2)
    assert [name for name, _ in events] == ["request_started", "headers_received"]

    assert response.read() == b"hi"
    response.close()
    assert [name for name, _ in events] == [
        "request_started",
        "headers_received",
        "body_complete",
    ]


def test_streaming_reports_body_complete_once(delayed_url):
    events: list[str] = []
    response = httpclient.get(
        delayed_url,
        stream=True,
        on_timing=lambda event, _elapsed: events.append(event),
    )
    response.read()
    response.read()
    response.close()
    assert events.count("body_complete") == 1


def test_no_hook_is_allowed(delayed_url):
    response = httpclient.get(delayed_url)
    assert response.status_code == 200
    assert response.content == b"hi"


def test_async_non_streaming_reports_three_milestones(delayed_url):
    events: list[tuple[str, float]] = []

    async def run():
        return await httpclient.async_get(
            delayed_url,
            on_timing=lambda event, elapsed: events.append((event, elapsed)),
        )

    response = asyncio.run(run())
    assert response.status_code == 200
    assert [name for name, _ in events] == [
        "request_started",
        "headers_received",
        "body_complete",
    ]
    assert events[1][1] >= HEADER_DELAY * 0.6
    assert events[2][1] >= events[1][1] + BODY_DELAY * 0.6


def test_async_streaming_body_complete_waits_for_the_read(delayed_url):
    events: list[str] = []

    async def run():
        response = await httpclient.async_get(
            delayed_url,
            stream=True,
            on_timing=lambda event, _elapsed: events.append(event),
        )
        before = list(events)
        body = await response.aread()
        response.close()
        return before, body

    before, body = asyncio.run(run())
    assert before == ["request_started", "headers_received"]
    assert body == b"hi"
    assert events == ["request_started", "headers_received", "body_complete"]
