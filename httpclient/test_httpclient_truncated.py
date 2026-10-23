"""A streamed body shorter than its Content-Length is an error (#236)."""

from __future__ import annotations

import asyncio
import socketserver
import threading

import pytest

import httpclient


class _ShortServer(socketserver.ThreadingTCPServer):
    """Declares 128 bytes, sends 32, closes."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _ShortHandler)


class _ShortHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        self.rfile.readline()
        while True:
            header = self.rfile.readline()
            if header in (b"\r\n", b"\n", b""):
                break
        self.wfile.write(
            b"HTTP/1.1 200 OK\r\nContent-Length: 128\r\n"
            b"Content-Type: application/octet-stream\r\n"
            b"Connection: close\r\n\r\n" + b"x" * 32
        )
        self.wfile.flush()


class _FullServer(socketserver.ThreadingTCPServer):
    """Declares 2 bytes and sends them all."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _FullHandler)


class _FullHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        self.rfile.readline()
        while True:
            header = self.rfile.readline()
            if header in (b"\r\n", b"\n", b""):
                break
        self.wfile.write(
            b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n"
            b"Content-Type: text/plain\r\nConnection: close\r\n\r\nhi"
        )
        self.wfile.flush()


class _NoBodyServer(socketserver.ThreadingTCPServer):
    """Declares 128 bytes but never sends a body (HEAD / 304)."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _NoBodyHandler)


class _NoBodyHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        request_line = self.rfile.readline()
        while True:
            header = self.rfile.readline()
            if header in (b"\r\n", b"\n", b""):
                break
        if b" /not-modified " in request_line:
            self.wfile.write(
                b"HTTP/1.1 304 Not Modified\r\nContent-Length: 128\r\n\r\n"
            )
        else:
            self.wfile.write(b"HTTP/1.1 200 OK\r\nContent-Length: 128\r\n\r\n")
        self.wfile.flush()


@pytest.fixture
def short_url():
    server = _ShortServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        yield f"http://{host}:{port}/short"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_buffered_read_rejects_a_short_body(short_url):
    with pytest.raises(httpclient.HttpConnectionError):
        httpclient.get(short_url)


def test_stream_read_rejects_a_short_body(short_url):
    response = httpclient.get(short_url, stream=True)
    try:
        with pytest.raises(httpclient.HttpConnectionError):
            response.read()
    finally:
        response.close()


def test_stream_iter_bytes_rejects_a_short_body(short_url):
    response = httpclient.get(short_url, stream=True)
    seen = b""
    try:
        with pytest.raises(httpclient.HttpConnectionError):
            for chunk in response.iter_bytes(8):
                seen += chunk
    finally:
        response.close()
    assert seen == b"x" * 32


def test_stream_body_complete_does_not_fire_for_a_short_body(short_url):
    events: list[str] = []
    response = httpclient.get(
        short_url,
        stream=True,
        on_timing=lambda event, _elapsed: events.append(event),
    )
    try:
        with pytest.raises(httpclient.HttpConnectionError):
            response.read()
    finally:
        response.close()
    assert events == ["request_started", "headers_received"]


def test_repeated_read_after_a_complete_body_stays_clean():
    server = _FullServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    response = httpclient.get(f"http://{host}:{port}/full", stream=True)
    try:
        assert response.read() == b"hi"
        assert response.read() == b""
    finally:
        response.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_head_and_304_tolerate_a_declared_length():
    server = _NoBodyServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    base = f"http://{host}:{port}"
    try:
        response = httpclient.head(f"{base}/head", stream=True)
        try:
            assert response.read() == b""
        finally:
            response.close()

        response = httpclient.get(f"{base}/not-modified", stream=True)
        try:
            assert response.status_code == 304
            assert response.read() == b""
        finally:
            response.close()

        async def run():
            response = await httpclient.async_head(f"{base}/head", stream=True)
            try:
                return await response.aread()
            finally:
                response.close()

        assert asyncio.run(run()) == b""
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_async_stream_read_rejects_a_short_body(short_url):
    async def run():
        response = await httpclient.async_get(short_url, stream=True)
        try:
            return await response.aread()
        finally:
            response.close()

    with pytest.raises(httpclient.HttpConnectionError):
        asyncio.run(run())
