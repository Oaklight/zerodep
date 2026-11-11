"""Tests for the on_request_rejected signal (zerodep#272)."""

from __future__ import annotations

import socket

import pytest
from test_httpserver_keepalive import _live

import httpserver as server_module
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

    def test_read_error(self, monkeypatch):
        async def failing_read(reader, timeout, max_body_size, *, state=None, **kw):
            await reader.readuntil(b"\r\n\r\n")
            state.method = "POST"
            state.path = "/echo"
            raise RuntimeError("boom")

        monkeypatch.setattr(server_module, "_read_request", failing_read)
        app, events = _app()
        with _live(app):
            response = _exchange(app, b"POST /echo HTTP/1.1\r\nHost: x\r\n\r\n")
        assert b" 500 " in response.split(b"\r\n", 1)[0]
        assert b"Internal Server Error" in response
        assert len(events) == 1
        rej = events[0]
        assert (rej.status_code, rej.reason) == (500, "read_error")
        assert isinstance(rej.exception, RuntimeError)
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
            _exchange(app, b"GARBAGE\r\n\r\n")
        assert [e.reason for e in events] == ["bad_request"]

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

    def test_ids_that_are_not_a_single_token_are_replaced(self):
        for bad in (b"a b", b"a;b", b"a\x01b", b"caf\xe9"):
            app, events = _app(max_body_size=1)
            with _live(app):
                response = _exchange(
                    app,
                    b"POST /echo HTTP/1.1\r\nHost: x\r\nX-Request-Id: "
                    + bad
                    + b"\r\nContent-Length: 50\r\n\r\n",
                )
            sent = _header(response, "X-Request-Id")
            assert sent is not None and sent.isalnum() and len(sent) == 32, bad
            assert events[0].request_id == sent


class TestInvalidFraming:
    def _rejected(self, raw: bytes):
        app, events = _app()
        with _live(app):
            response = _exchange(app, raw)
        assert b" 400 " in response.split(b"\r\n", 1)[0]
        assert len(events) == 1
        rej = events[0]
        assert (rej.status_code, rej.reason) == (400, "bad_request")
        assert rej.method == "POST"
        assert rej.path == "/echo"
        assert rej.content_length is None
        assert _header(response, "X-Request-Id") == rej.request_id
        return response

    def test_non_numeric_content_length(self):
        response = self._rejected(
            b"POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: abc\r\n\r\n"
        )
        assert b"Invalid Content-Length" in response

    def test_negative_content_length(self):
        self._rejected(b"POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: -5\r\n\r\n")

    def test_invalid_chunk_size(self):
        response = self._rejected(
            b"POST /echo HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\n\r\n"
            b"zz\r\nabc\r\n0\r\n\r\n"
        )
        assert b"Invalid chunk size" in response

    def test_negative_chunk_size(self):
        self._rejected(
            b"POST /echo HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\n\r\n"
            b"-1\r\nabc\r\n0\r\n\r\n"
        )

    def test_lenient_int_forms_are_refused(self):
        for value in (b"1_0", b"+5", b"-0", b" ", b"5.0"):
            self._rejected(
                b"POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: "
                + value
                + b"\r\n\r\n"
            )
        for size in (b"0x10", b"+4", b"1_0"):
            self._rejected(
                b"POST /echo HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\n\r\n"
                + size
                + b"\r\nabc\r\n0\r\n\r\n"
            )

    def test_valid_framing_is_still_accepted(self):
        app, events = _app()
        with _live(app):
            plain = _exchange(
                app,
                b"POST /echo HTTP/1.1\r\nHost: x\r\nConnection: close\r\n"
                b"Content-Length: 0010\r\n\r\n0123456789",
            )
            chunked = _exchange(
                app,
                b"POST /echo HTTP/1.1\r\nHost: x\r\nConnection: close\r\n"
                b"Transfer-Encoding: chunked\r\n\r\nA\r\n0123456789\r\n0\r\n\r\n",
            )
        assert b" 200 " in plain.split(b"\r\n", 1)[0]
        assert b" 200 " in chunked.split(b"\r\n", 1)[0]
        assert events == []


class TestHeadersView:
    def test_headers_are_read_only_and_not_shared_between_handlers(self):
        app = App()
        outcomes: list[str] = []

        @app.on_request_rejected
        def first(rejection):
            try:
                rejection.headers["x-tampered"] = "yes"
            except TypeError:
                outcomes.append("read-only")

        @app.on_request_rejected
        def second(rejection):
            outcomes.append(
                "tampered" if "x-tampered" in rejection.headers else "clean"
            )

        with _live(app):
            _exchange(
                app,
                b"POST /x HTTP/1.1\r\nHost: x\r\nContent-Length: -1\r\n\r\n",
            )
        assert outcomes == ["read-only", "clean"]


def _content_length_request(path: str, body: bytes) -> bytes:
    """Build a raw POST with a declared length and *body*."""
    return (
        b"POST %s HTTP/1.1\r\nHost: x\r\nContent-Length: %d\r\n\r\n"
        % (path.encode(), len(body))
    ) + body


def _chunked_request(path: str, body: bytes, frame: int = 64 * 1024) -> bytes:
    """Build a raw chunked POST that carries *body* in ``frame``-sized chunks."""
    frames = [
        b"%x\r\n" % len(part) + part + b"\r\n"
        for part in (
            body[start : start + frame] for start in range(0, len(body), frame)
        )
    ]
    frames.append(b"0\r\n\r\n")
    return (
        b"POST %s HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\n\r\n"
        % path.encode()
    ) + b"".join(frames)


class TestTooLargeClosesCleanly:
    """An over-limit body is drained before close, so the client sees FIN.

    Closing with unread body bytes makes the kernel send RST, which surfaces
    as ``ConnectionResetError`` on the client and can hide the 413.
    """

    LIMIT = 1 << 20

    @pytest.mark.parametrize("multiplier", [1.1, 2, 8])
    def test_content_length_body_is_drained(self, multiplier):
        app, events = _app(max_body_size=self.LIMIT)
        body = b"x" * int(self.LIMIT * multiplier)
        with _live(app):
            response = _exchange(app, _content_length_request("/echo", body))
        assert b" 413 " in response.split(b"\r\n", 1)[0]
        assert len(events) == 1
        assert events[0].reason == "too_large"

    @pytest.mark.parametrize("multiplier", [1.1, 2, 8])
    def test_chunked_body_is_drained(self, multiplier):
        app, events = _app(max_body_size=self.LIMIT)
        body = b"x" * int(self.LIMIT * multiplier)
        with _live(app):
            response = _exchange(app, _chunked_request("/echo", body))
        assert b" 413 " in response.split(b"\r\n", 1)[0]
        assert len(events) == 1
        assert events[0].reason == "too_large"


class _ScriptedReader:
    """StreamReader stand-in: fixed data for ``read``, scripted ``readline``."""

    def __init__(self, data: bytes, lines: list[bytes | Exception]) -> None:
        self._data = data
        self._lines = list(lines)

    async def read(self, n: int) -> bytes:
        part, self._data = self._data[:n], self._data[n:]
        return part

    async def readline(self) -> bytes:
        item = self._lines.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class TestAfterHooks:
    """A rejected read is still a response and passes through after-hooks."""

    @staticmethod
    def _app(**kwargs) -> tuple[App, list[tuple[str, str]]]:
        app = App(**kwargs)
        seen: list[tuple[str, str]] = []

        @app.after_request
        async def mark(request, response):
            seen.append((request.path, request.query_string))
            response.headers["X-Marker"] = "1"
            return response

        @app.post("/echo")
        async def echo(request):
            return {"len": len(request.body)}

        return app, seen

    def test_over_limit_body_gets_the_hook_headers(self):
        app, seen = self._app(max_body_size=10)
        with _live(app):
            response = _exchange(
                app,
                b"POST /echo?x=1 HTTP/1.1\r\nHost: x\r\nContent-Length: 100\r\n\r\n",
            )
        assert b" 413 " in response.split(b"\r\n", 1)[0]
        assert _header(response, "X-Marker") == "1"
        # The parsed request line is available to the hook.
        assert seen == [("/echo", "x=1")]

    def test_malformed_request_line_skips_the_hooks(self):
        app, seen = self._app()
        with _live(app):
            response = _exchange(app, b"GARBAGE\r\n\r\n")
        assert b" 400 " in response.split(b"\r\n", 1)[0]
        assert _header(response, "X-Marker") is None
        assert seen == []

    def test_hook_can_replace_the_rejection_response(self):
        app = App(max_body_size=10)

        @app.after_request
        async def replace(request, response):
            return server_module.JSONResponse({"custom": "rejected"}, status_code=422)

        @app.post("/echo")
        async def echo(request):
            return {"len": len(request.body)}

        with _live(app):
            response = _exchange(
                app,
                b"POST /echo HTTP/1.1\r\nHost: x\r\nContent-Length: 100\r\n\r\n",
            )
        assert b" 422 " in response.split(b"\r\n", 1)[0]
        assert _header(response, "X-Request-Id") is not None


class TestDrainReadErrors:
    """An over-long chunk line ends the drain, not the connection task.

    ``StreamReader.readline()`` raises ``ValueError`` once a line passes the
    64 KiB stream limit.  Draining happens after the 413 is written, so the
    error must be swallowed instead of escaping ``_handle_connection`` and
    logging a traceback for every hostile request.
    """

    @staticmethod
    def _chunked_state() -> server_module._ReadState:
        state = server_module._ReadState()
        state.headers = {"transfer-encoding": "chunked"}
        state.pending_chunk_size = 4
        return state

    @pytest.mark.asyncio
    async def test_over_long_chunk_size_line_is_swallowed(self):
        # Pending chunk data, its CRLF, then an over-limit size line.
        reader = _ScriptedReader(b"xxxx", [b"\r\n", ValueError("line too long")])
        app = App(max_body_size=1024)
        await app._drain_rejected_body(
            reader,
            server_module.HTTPException(413, "Request body too large"),
            self._chunked_state(),
        )

    @pytest.mark.asyncio
    async def test_over_long_trailer_line_is_swallowed(self):
        # Pending chunk data, CRLF, zero chunk, then an over-limit trailer.
        reader = _ScriptedReader(
            b"xxxx", [b"\r\n", b"0\r\n", ValueError("line too long")]
        )
        app = App(max_body_size=1024)
        await app._drain_rejected_body(
            reader,
            server_module.HTTPException(413, "Request body too large"),
            self._chunked_state(),
        )
