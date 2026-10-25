"""Tests for the on_request_rejected signal (zerodep#272)."""

from __future__ import annotations

import socket

from test_httpserver_keepalive import _live

from httpserver import App, RejectedRequest


def _app(**kwargs) -> tuple[App, list[RejectedRequest]]:
    app = App(**kwargs)
    events: list[RejectedRequest] = []

    @app.on_request_rejected
    async def record(rejection):
        events.append(rejection)

    @app.post("/echo")
    async def echo(request):
        return {"len": len(request.body)}

    return app, events


def _exchange(app: App, raw: bytes, *, half_close: bool = False) -> bytes:
    """Send *raw*, optionally half-close, and read until the server closes."""
    sock = socket.create_connection((app.host, app.port), timeout=5)
    try:
        sock.sendall(raw)
        if half_close:
            sock.shutdown(socket.SHUT_WR)
        data = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
        return data
    finally:
        sock.close()


def _header(response: bytes, name: str) -> str | None:
    head = response.split(b"\r\n\r\n", 1)[0].decode("latin-1")
    for line in head.split("\r\n")[1:]:
        key, _, value = line.partition(":")
        if key.strip().lower() == name.lower():
            return value.strip()
    return None


class TestRejectionRows:
    def test_bad_request(self):
        app, events = _app()
        with _live(app):
            response = _exchange(app, b"GARBAGE\r\n\r\n")
        assert b" 400 " in response.split(b"\r\n", 1)[0]
        assert len(events) == 1
        rej = events[0]
        assert rej.status_code == 400
        assert rej.reason == "bad_request"
        assert rej.method is None and rej.path is None and rej.headers is None
        assert rej.bytes_received == 0
        assert rej.exception is not None
        assert _header(response, "X-Request-Id") == rej.request_id

    def test_too_large(self):
        app, events = _app(max_body_size=10)
        with _live(app):
            response = _exchange(
                app,
                b"POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: 100\r\n\r\n",
            )
        assert b" 413 " in response.split(b"\r\n", 1)[0]
        assert len(events) == 1
        rej = events[0]
        assert (rej.status_code, rej.reason) == (413, "too_large")
        assert rej.method == "POST"
        assert rej.path == "/echo"
        assert rej.content_length == 100
        assert rej.headers is not None and rej.headers["host"] == "x"
        assert rej.bytes_received == 0
        assert _header(response, "X-Request-Id") == rej.request_id

    def test_timeout(self):
        app, events = _app(read_timeout=0.3)
        with _live(app):
            response = _exchange(
                app,
                b"POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: 5\r\n\r\n",
            )
        assert b" 408 " in response.split(b"\r\n", 1)[0]
        assert len(events) == 1
        rej = events[0]
        assert (rej.status_code, rej.reason) == (408, "timeout")
        assert rej.method == "POST"
        assert rej.content_length == 5
        assert _header(response, "X-Request-Id") == rej.request_id

    def test_incomplete_body(self):
        app, events = _app()
        with _live(app):
            response = _exchange(
                app,
                b"POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: 10\r\n\r\nabc",
                half_close=True,
            )
        assert b" 400 " in response.split(b"\r\n", 1)[0]
        assert len(events) == 1
        rej = events[0]
        assert (rej.status_code, rej.reason) == (400, "incomplete_body")
        assert rej.content_length == 10
        assert rej.bytes_received == 3
        assert _header(response, "X-Request-Id") == rej.request_id

    def test_read_error(self):
        app, events = _app()
        with _live(app):
            response = _exchange(
                app,
                b"POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: abc\r\n\r\n",
            )
        assert b" 500 " in response.split(b"\r\n", 1)[0]
        assert b"Internal Server Error" in response
        assert len(events) == 1
        rej = events[0]
        assert (rej.status_code, rej.reason) == (500, "read_error")
        assert isinstance(rej.exception, ValueError)
        assert rej.method == "POST"
        assert _header(response, "X-Request-Id") == rej.request_id


class TestRequestId:
    def test_client_request_id_is_echoed(self):
        app, events = _app(max_body_size=1)
        with _live(app):
            response = _exchange(
                app,
                b"POST /echo HTTP/1.1\r\nHost: x\r\nX-Request-Id: abc-123\r\n"
                b"Content-Length: 50\r\n\r\n",
            )
        assert _header(response, "X-Request-Id") == "abc-123"
        assert events[0].request_id == "abc-123"

    def test_unusable_client_id_is_replaced(self):
        app, events = _app(max_body_size=1)
        too_long = b"x" * 500
        with _live(app):
            response = _exchange(
                app,
                b"POST /echo HTTP/1.1\r\nHost: x\r\nX-Request-Id: "
                + too_long
                + b"\r\nContent-Length: 50\r\n\r\n",
            )
        generated = _header(response, "X-Request-Id")
        assert generated is not None and generated != too_long.decode()
        assert events[0].request_id == generated

    def test_generated_ids_are_unique(self):
        app, events = _app()
        with _live(app):
            _exchange(app, b"GARBAGE\r\n\r\n")
            _exchange(app, b"GARBAGE\r\n\r\n")
        assert len(events) == 2
        assert events[0].request_id != events[1].request_id


class TestHandlerSemantics:
    def test_failing_handler_does_not_break_response(self):
        app = App()
        calls: list[str] = []

        @app.on_request_rejected
        def boom(rejection):
            calls.append("boom")
            raise RuntimeError("handler failure")

        @app.on_request_rejected
        async def after(rejection):
            calls.append("after")

        with _live(app):
            response = _exchange(app, b"GARBAGE\r\n\r\n")
        assert b" 400 " in response.split(b"\r\n", 1)[0]
        assert _header(response, "X-Request-Id") is not None
        assert calls == ["boom", "after"]

    def test_not_fired_for_dispatched_requests(self):
        app, events = _app()
        with _live(app):
            response = _exchange(
                app,
                b"GET /missing HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n",
            )
        assert b" 404 " in response.split(b"\r\n", 1)[0]
        assert events == []

    def test_not_fired_for_closed_idle_connection(self):
        app, events = _app()
        with _live(app):
            sock = socket.create_connection((app.host, app.port), timeout=5)
            sock.close()
            _exchange(app, b"POST /echo HTTP/1.1\r\nContent-Length: abc\r\n\r\n")
        assert [e.reason for e in events] == ["read_error"]

    def test_no_handler_still_answers_with_request_id(self):
        app = App()
        with _live(app):
            response = _exchange(app, b"GARBAGE\r\n\r\n")
        assert b" 400 " in response.split(b"\r\n", 1)[0]
        assert _header(response, "X-Request-Id")


class TestBodyAccounting:
    def test_timeout_mid_body_reports_bytes_received(self):
        app, events = _app(read_timeout=0.4)
        with _live(app):
            response = _exchange(
                app,
                b"POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: 10\r\n\r\nabc",
            )
        assert b" 408 " in response.split(b"\r\n", 1)[0]
        assert len(events) == 1
        rej = events[0]
        assert (rej.status_code, rej.reason) == (408, "timeout")
        assert rej.content_length == 10
        assert rej.bytes_received == 3

    def test_chunked_overflow_is_too_large(self):
        app, events = _app(max_body_size=10)
        with _live(app):
            response = _exchange(
                app,
                b"POST /echo HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\n\r\n"
                b"6\r\nabcdef\r\n6\r\nghijkl\r\n0\r\n\r\n",
            )
        assert b" 413 " in response.split(b"\r\n", 1)[0]
        assert len(events) == 1
        rej = events[0]
        assert (rej.status_code, rej.reason) == (413, "too_large")
        assert rej.content_length is None
        assert rej.bytes_received == 6
        assert _header(response, "X-Request-Id") == rej.request_id

    def test_chunked_truncated_is_incomplete_body(self):
        app, events = _app()
        with _live(app):
            response = _exchange(
                app,
                b"POST /echo HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\n\r\n"
                b"5\r\nabc",
                half_close=True,
            )
        assert b" 400 " in response.split(b"\r\n", 1)[0]
        assert len(events) == 1
        rej = events[0]
        assert (rej.status_code, rej.reason) == (400, "incomplete_body")
        assert rej.bytes_received == 3


class TestIdleConnection:
    def test_keep_alive_idle_timeout_is_silent(self):
        app, events = _app(keep_alive_timeout=0.3)
        with _live(app):
            sock = socket.create_connection((app.host, app.port), timeout=5)
            try:
                sock.sendall(
                    b"POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: 2\r\n\r\nhi"
                )
                first = sock.recv(4096)
                assert b" 200 " in first.split(b"\r\n", 1)[0]
                # Idle past keep_alive_timeout: the server closes without a
                # response, which is not a rejection.
                assert sock.recv(4096) == b""
            finally:
                sock.close()
        assert events == []


class TestRequestIdValidation:
    def test_comma_separated_client_id_is_replaced(self):
        app, events = _app(max_body_size=1)
        with _live(app):
            response = _exchange(
                app,
                b"POST /echo HTTP/1.1\r\nHost: x\r\nX-Request-Id: a, b\r\n"
                b"Content-Length: 50\r\n\r\n",
            )
        assert "," not in (_header(response, "X-Request-Id") or ",")
        assert events[0].request_id == _header(response, "X-Request-Id")
