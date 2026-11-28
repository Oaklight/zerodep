"""Correctness tests: zerodep sse."""

import asyncio
import http.server
import itertools
import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from sse import (
    AsyncEventSource,
    EventSource,
    SSEConnectionError,
    SSEEvent,
    SSEHTTPError,
    _SSEParser,
    async_connect,
    connect,
    encode_comment,
    encode_event,
)

# ── Helpers ──


def _run_async(coro_fn, *args, **kwargs):
    return asyncio.run(coro_fn(*args, **kwargs))


async def _async_lines(lines):
    """Convert a list of strings to an async iterable."""
    for line in lines:
        yield line


# ── Independent WHATWG model for the line parser ──
#
# Written from the WHATWG event-stream rules, not from sse.py.  Each branch
# corresponds to an assertion that used to be a separate hand-written test;
# the rule-to-assertion mapping is recorded in the PR body.


class _ModelSSEParser:
    """Minimal WHATWG event-stream parser used as an oracle."""

    def __init__(self) -> None:
        self._first_line = True
        self._event_type = ""
        self._data: list[str] = []
        self._last_id = ""
        self._retry: int | None = None

    def feed(self, line: str) -> tuple[str, str, str, int | None] | None:
        if self._first_line:
            self._first_line = False
            if line.startswith("﻿"):
                line = line[1:]

        if line == "":
            if not self._data:
                return None
            event = (
                self._event_type or "message",
                "\n".join(self._data),
                self._last_id,
                self._retry,
            )
            self._event_type = ""
            self._data = []
            return event

        if line.startswith(":"):
            return None

        field, separator, value = line.partition(":")
        if not separator:
            field, value = line, ""
        elif value.startswith(" "):
            value = value[1:]

        if field == "event":
            self._event_type = value
        elif field == "data":
            self._data.append(value)
        elif field == "id":
            if "\0" not in value:
                self._last_id = value
        elif field == "retry":
            if value.isdigit():
                self._retry = int(value)
        return None

    @property
    def last_event_id(self) -> str:
        return self._last_id

    @property
    def retry_interval(self) -> int | None:
        return self._retry


# ── SSEEvent tests ──


class TestSSEEvent:
    def test_defaults(self):
        e = SSEEvent()
        assert e.event == "message"
        assert e.data == ""
        assert e.id == ""
        assert e.retry is None

    def test_frozen(self):
        e = SSEEvent(data="hello")
        with pytest.raises(AttributeError):
            e.data = "world"  # type: ignore

    def test_repr_short(self):
        e = SSEEvent(event="ping", data="hi", id="1")
        r = repr(e)
        assert "ping" in r
        assert "hi" in r
        assert "1" in r

    def test_repr_long_data_truncated(self):
        e = SSEEvent(data="x" * 100)
        r = repr(e)
        assert "..." in r


# ── Encoder tests ──


class TestEncodeEvent:
    def test_basic(self):
        assert encode_event("hello") == "data: hello\n\n"

    def test_multiline_data(self):
        assert encode_event("a\nb") == "data: a\ndata: b\n\n"

    def test_crlf_and_cr_are_normalized(self):
        assert encode_event("a\r\nb\rc") == "data: a\ndata: b\ndata: c\n\n"

    def test_event_id_and_retry(self):
        assert encode_event("x", event="update", id="42", retry=1000) == (
            "event: update\nid: 42\nretry: 1000\ndata: x\n\n"
        )

    def test_empty_data_still_dispatches(self):
        assert encode_event() == "data:\n\n"
        assert list(EventSource(encode_event().split("\n"))) == [SSEEvent(data="")]

    def test_trailing_newline_is_preserved(self):
        assert encode_event("a\n") == "data: a\ndata:\n\n"

    def test_empty_id_resets_and_retry_zero_is_emitted(self):
        assert encode_event("x", id="") == "id:\ndata: x\n\n"
        assert encode_event("x", retry=0) == "retry: 0\ndata: x\n\n"

    def test_data_cannot_inject_fields(self):
        for payload in ("a\nretry: 1", "a\rretry: 1", "a\nevent: x"):
            events = list(EventSource(encode_event(payload).split("\n")))
            assert events == [SSEEvent(data=payload.replace("\r", "\n"))]

    def test_non_str_arguments_raise_type_error(self):
        with pytest.raises(TypeError, match="data must be str"):
            encode_event(None)  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="data must be str"):
            encode_event(b"ab")  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="event must be str"):
            encode_event("x", event=123)  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="id must be str"):
            encode_event("x", id=123)  # type: ignore[arg-type]

    def test_id_with_nul_is_rejected(self):
        with pytest.raises(ValueError, match="NUL"):
            encode_event("x", id="a\0b")

    def test_line_breaks_in_event_or_id_are_rejected(self):
        with pytest.raises(ValueError, match="line break"):
            encode_event("x", event="a\nb")
        with pytest.raises(ValueError, match="line break"):
            encode_event("x", id="a\rb")

    def test_invalid_retry_is_rejected(self):
        with pytest.raises(ValueError, match="non-negative integer"):
            encode_event("x", retry=-1)
        with pytest.raises(ValueError, match="non-negative integer"):
            encode_event("x", retry=True)  # type: ignore[arg-type]

    def test_comment_is_a_heartbeat(self):
        assert encode_comment("ping") == ": ping\n\n"
        assert encode_comment() == ":\n\n"
        assert list(EventSource(encode_comment("ping").split("\n"))) == []

    def test_comment_with_line_break_is_rejected(self):
        with pytest.raises(ValueError, match="line break"):
            encode_comment("a\nb")


_ENCODE_DATA = [
    "",
    "hello",
    "a\nb",
    "a\r\nb\rc",
    "a\n",
    "a" + chr(0x2028) + "b" + chr(0x85) + "c",
    "こんにちは 🎉",
    "x" * 100,
]
_ENCODE_EVENTS = [None, "update", "ping"]
_ENCODE_IDS = [None, "", "42", "abc"]
_ENCODE_RETRIES = [None, 0, 1000]


class TestEncodeRoundTrip:
    def test_generated_events(self):
        failures = []
        for data, event, event_id, retry in itertools.product(
            _ENCODE_DATA, _ENCODE_EVENTS, _ENCODE_IDS, _ENCODE_RETRIES
        ):
            block = encode_event(data, event=event, id=event_id, retry=retry)
            events = list(EventSource(block.split("\n")))
            expected = SSEEvent(
                event=event if event is not None else "message",
                data=data.replace("\r\n", "\n").replace("\r", "\n"),
                id=event_id if event_id is not None else "",
                retry=retry,
            )
            if events != [expected]:
                failures.append((data, event, event_id, retry, events, expected))
        assert not failures, f"encode/parse round-trip failures: {failures!r}"


# ── _SSEParser tests ──


_PARSER_LINES = [
    "data: hello",
    "data:",
    "data:hello",
    "data:  hello",
    "data",
    "event: update",
    "event: ping",
    "id: 42",
    "id: bad" + chr(0) + "id",
    "retry: 5000",
    "retry: abc",
    "retry:",
    "foo: bar",
    ": comment",
    chr(0xFEFF) + "data: hello",
    "data: a" + chr(0x2028) + "b",
]


def _event_tuple(event) -> tuple[str, str, str, int | None] | None:
    if event is None:
        return None
    return (event.event, event.data, event.id, event.retry)


class TestSSEParser:
    def test_last_event_id_property(self):
        p = _SSEParser()
        assert p.last_event_id == ""
        p.feed_line("id: 42")
        p.feed_line("data: x")
        p.feed_line("")
        assert p.last_event_id == "42"

    def test_retry_interval_property(self):
        p = _SSEParser()
        assert p.retry_interval is None
        p.feed_line("retry: 5000")
        p.feed_line("data: x")
        p.feed_line("")
        assert p.retry_interval == 5000

    def test_parser_init_with_restored_state(self):
        """Keyword args restore reconnect state at construction time."""
        p = _SSEParser(last_id="42", retry=5000)
        assert p.last_event_id == "42"
        assert p.retry_interval == 5000

    def test_parser_init_defaults(self):
        """Default construction still gives blank state."""
        p = _SSEParser()
        assert p.last_event_id == ""
        assert p.retry_interval is None

    def test_generated_line_sequences_match_model(self):
        failures = []
        for size in (1, 2, 3):
            for lines in itertools.product(_PARSER_LINES, repeat=size):
                actual = _SSEParser()
                model = _ModelSSEParser()
                for line in lines:
                    got = actual.feed_line(line)
                    expected = model.feed(line)
                    if _event_tuple(got) != expected:
                        failures.append((lines, line, _event_tuple(got), expected))
                        break
                else:
                    got = actual.feed_line("")
                    expected = model.feed("")
                    if _event_tuple(got) != expected:
                        failures.append((lines, "", _event_tuple(got), expected))
                    elif (
                        actual.last_event_id,
                        actual.retry_interval,
                    ) != (model.last_event_id, model.retry_interval):
                        failures.append(
                            (
                                lines,
                                "state",
                                (actual.last_event_id, actual.retry_interval),
                                (model.last_event_id, model.retry_interval),
                            )
                        )
        assert not failures, f"parser model failures: {failures!r}"


# ── EventSource tests ──


class TestEventSource:
    def test_single_event(self):
        lines = ["data: hello", ""]
        events = list(EventSource(lines))
        assert len(events) == 1
        assert events[0].data == "hello"

    def test_multiple_events(self):
        lines = ["data: one", "", "data: two", "", "data: three", ""]
        events = list(EventSource(lines))
        assert len(events) == 3
        assert [e.data for e in events] == ["one", "two", "three"]

    def test_complex_stream(self):
        lines = [
            ": welcome",
            "event: greeting",
            "data: hello",
            "data: world",
            "id: 1",
            "",
            "data: plain message",
            "",
            "event: close",
            "data: bye",
            "id: 2",
            "retry: 5000",
            "",
        ]
        events = list(EventSource(lines))
        assert len(events) == 3

        assert events[0].event == "greeting"
        assert events[0].data == "hello\nworld"
        assert events[0].id == "1"

        assert events[1].event == "message"
        assert events[1].data == "plain message"
        assert events[1].id == "1"  # persists

        assert events[2].event == "close"
        assert events[2].data == "bye"
        assert events[2].id == "2"
        assert events[2].retry == 5000

    def test_empty_input(self):
        events = list(EventSource([]))
        assert events == []

    def test_no_trailing_empty_line(self):
        """Stream ends without dispatching incomplete event."""
        lines = ["data: incomplete"]
        events = list(EventSource(lines))
        assert events == []

    def test_comments_only(self):
        lines = [": comment1", ": comment2", ""]
        events = list(EventSource(lines))
        assert events == []


# ── AsyncEventSource tests ──


class TestAsyncEventSource:
    def test_single_event(self):
        async def _run():
            lines = ["data: hello", ""]
            return [e async for e in AsyncEventSource(_async_lines(lines))]

        events = _run_async(_run)
        assert len(events) == 1
        assert events[0].data == "hello"

    def test_multiple_events(self):
        async def _run():
            lines = ["data: one", "", "data: two", ""]
            return [e async for e in AsyncEventSource(_async_lines(lines))]

        events = _run_async(_run)
        assert len(events) == 2
        assert events[0].data == "one"
        assert events[1].data == "two"

    def test_matches_sync(self):
        """AsyncEventSource produces identical results to EventSource."""
        lines = [
            "event: update",
            "data: line1",
            "data: line2",
            "id: 5",
            "retry: 1000",
            "",
            ": comment",
            "data: simple",
            "",
        ]
        sync_events = list(EventSource(lines))

        async def _run():
            return [e async for e in AsyncEventSource(_async_lines(lines))]

        async_events = _run_async(_run)
        assert sync_events == async_events


# ── Local SSE test server ──


class _SSEHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that serves SSE events configured on the server."""

    def do_GET(self):
        path = self.path

        if path == "/events":
            # Serve events once, then 204 on reconnect (graceful stop)
            count = self.server.request_counts.get(path, 0)  # type: ignore
            self.server.request_counts[path] = count + 1  # type: ignore
            if count == 0:
                self._serve_sse(self.server.sse_lines)  # type: ignore
            else:
                self.send_response(204)
                self.end_headers()
        elif path == "/events-repeat":
            # Always serve events (for retry exhaustion tests)
            self._serve_sse(self.server.sse_lines)  # type: ignore
        elif path == "/events-with-id":
            last_id = self.headers.get("Last-Event-ID", "")
            self.server.received_last_event_ids.append(last_id)  # type: ignore
            count = self.server.request_counts.get(path, 0)  # type: ignore
            self.server.request_counts[path] = count + 1  # type: ignore
            if count == 0:
                self._serve_sse(self.server.sse_lines)  # type: ignore
            else:
                # Record the header but stop — return 204
                self.send_response(204)
                self.end_headers()
        elif path == "/empty-stream":
            # Serve empty SSE stream (no events) — for retry exhaustion testing
            self.close_connection = True
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
        elif path == "/no-content":
            self.send_response(204)
            self.end_headers()
        elif path == "/error":
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Internal Server Error")
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_sse(self, lines):
        self.close_connection = True
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        for line in lines:
            self.wfile.write((line + "\n").encode())
        self.wfile.flush()

    def log_message(self, format, *args):
        pass  # suppress server logs


class _SSETestServer(http.server.HTTPServer):
    sse_lines: list[str] = []
    received_last_event_ids: list[str] = []
    request_counts: dict[str, int] = {}


@pytest.fixture
def sse_server():
    """Start a local SSE test server in a background thread."""
    server = _SSETestServer(("127.0.0.1", 0), _SSEHandler)
    server.sse_lines = [
        "event: greeting",
        "data: hello",
        "id: 1",
        "",
        "data: world",
        "id: 2",
        "",
    ]
    server.received_last_event_ids = []
    server.request_counts = {}
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()


def _server_url(server, path="/events"):
    host, port = server.server_address
    return f"http://{host}:{port}{path}"


# ── SSEClient integration tests ──


class TestSSEClientBasic:
    def test_consume_events(self, sse_server):
        with connect(_server_url(sse_server), retry_interval=100) as client:
            events = list(client)

        assert len(events) == 2
        assert events[0].event == "greeting"
        assert events[0].data == "hello"
        assert events[0].id == "1"
        assert events[1].data == "world"
        assert events[1].id == "2"

    def test_http_204_stops(self, sse_server):
        with connect(_server_url(sse_server, "/no-content"), max_retries=0) as client:
            events = list(client)
        assert events == []

    def test_http_error(self, sse_server):
        with pytest.raises(SSEHTTPError) as exc_info:
            with connect(_server_url(sse_server, "/error"), max_retries=0) as client:
                list(client)
        assert exc_info.value.status_code == 500

    def test_max_retries_exhausted(self, sse_server):
        """Retries exhausted when stream closes without events."""
        with pytest.raises(SSEConnectionError):
            with connect(
                _server_url(sse_server, "/empty-stream"),
                max_retries=1,
                retry_interval=100,
            ) as client:
                list(client)

    def test_last_event_id_sent(self, sse_server):
        """Verify Last-Event-ID is sent on reconnect."""
        sse_server.sse_lines = ["data: msg", "id: 42", ""]
        with connect(
            _server_url(sse_server, "/events-with-id"),
            retry_interval=100,
        ) as client:
            list(client)
        # First request has no ID, second has "42"
        assert sse_server.received_last_event_ids[0] == ""
        assert sse_server.received_last_event_ids[1] == "42"

    def test_initial_last_event_id(self, sse_server):
        """Verify user-provided last_event_id is sent on first request."""
        with connect(
            _server_url(sse_server, "/events-with-id"),
            retry_interval=100,
            last_event_id="100",
        ) as client:
            list(client)
        assert sse_server.received_last_event_ids[0] == "100"

    def test_close_stops_iteration(self, sse_server):
        """Calling close() stops the event loop."""
        sse_server.sse_lines = [
            "data: one",
            "",
            "data: two",
            "",
        ]
        events = []
        with connect(_server_url(sse_server), max_retries=0) as client:
            for event in client:
                events.append(event)
                client.close()
        assert len(events) == 1


# ── AsyncSSEClient integration tests ──


class TestAsyncSSEClientBasic:
    def test_consume_events(self, sse_server):
        async def _run():
            events = []
            async with async_connect(
                _server_url(sse_server), retry_interval=100
            ) as client:
                async for event in client:
                    events.append(event)
            return events

        events = _run_async(_run)
        assert len(events) == 2
        assert events[0].event == "greeting"
        assert events[0].data == "hello"
        assert events[1].data == "world"

    def test_http_204_stops(self, sse_server):
        async def _run():
            async with async_connect(
                _server_url(sse_server, "/no-content"), max_retries=0
            ) as client:
                return [e async for e in client]

        events = _run_async(_run)
        assert events == []

    def test_http_error(self, sse_server):
        async def _run():
            async with async_connect(
                _server_url(sse_server, "/error"), max_retries=0
            ) as client:
                return [e async for e in client]

        with pytest.raises(SSEHTTPError):
            _run_async(_run)

    def test_max_retries_exhausted(self, sse_server):
        async def _run():
            async with async_connect(
                _server_url(sse_server, "/empty-stream"),
                max_retries=1,
                retry_interval=100,
            ) as client:
                return [e async for e in client]

        with pytest.raises(SSEConnectionError):
            _run_async(_run)

    def test_last_event_id_sent(self, sse_server):
        sse_server.sse_lines = ["data: msg", "id: 42", ""]

        async def _run():
            async with async_connect(
                _server_url(sse_server, "/events-with-id"),
                retry_interval=100,
            ) as client:
                return [e async for e in client]

        _run_async(_run)
        assert sse_server.received_last_event_ids[0] == ""
        assert sse_server.received_last_event_ids[1] == "42"

    def test_close_stops_iteration(self, sse_server):
        sse_server.sse_lines = ["data: one", "", "data: two", ""]

        async def _run():
            events = []
            async with async_connect(_server_url(sse_server), max_retries=0) as client:
                async for event in client:
                    events.append(event)
                    await client.close()
            return events

        events = _run_async(_run)
        assert len(events) == 1


# ── Comparison with httpx-sse ──

httpx_sse = None
httpx = None
try:
    import httpx as _httpx
    import httpx_sse as _httpx_sse

    httpx = _httpx
    httpx_sse = _httpx_sse
except ImportError:
    pass


@pytest.mark.skipif(httpx_sse is None, reason="httpx-sse not installed")
class TestCompareWithHttpxSSE:
    """Compare parsing results with httpx-sse reference library."""

    @staticmethod
    def _parse_with_httpx_sse(raw: str) -> list[dict]:
        """Parse raw SSE text using httpx-sse."""
        # httpx-sse expects bytes content

        response = httpx.Response(  # type: ignore
            200,
            headers={"content-type": "text/event-stream"},
            stream=httpx.ByteStream(raw.encode()),  # type: ignore
        )
        response.read()
        source = httpx_sse.EventSource(response)  # type: ignore
        events = []
        for sse in source.iter_sse():
            events.append(
                {"event": sse.event, "data": sse.data, "id": sse.id, "retry": sse.retry}
            )
        return events

    @staticmethod
    def _parse_with_zerodep(raw: str) -> list[dict]:
        """Parse raw SSE text using zerodep EventSource."""
        lines = raw.split("\n")
        # Remove trailing empty string from split if raw ends with \n
        if lines and lines[-1] == "":
            lines.pop()
        events = []
        for event in EventSource(lines):
            events.append(
                {
                    "event": event.event,
                    "data": event.data,
                    "id": event.id,
                    "retry": event.retry,
                }
            )
        return events

    def test_simple_events(self):
        raw = "data: hello\n\ndata: world\n\n"
        assert self._parse_with_zerodep(raw) == self._parse_with_httpx_sse(raw)

    def test_multiline_data(self):
        raw = "data: line1\ndata: line2\ndata: line3\n\n"
        assert self._parse_with_zerodep(raw) == self._parse_with_httpx_sse(raw)

    def test_event_type(self):
        raw = "event: update\ndata: payload\n\n"
        assert self._parse_with_zerodep(raw) == self._parse_with_httpx_sse(raw)

    def test_all_fields(self):
        raw = "event: notification\ndata: payload\nid: 99\nretry: 2000\n\n"
        assert self._parse_with_zerodep(raw) == self._parse_with_httpx_sse(raw)

    def test_comments_ignored(self):
        raw = ": comment\ndata: hello\n\n"
        assert self._parse_with_zerodep(raw) == self._parse_with_httpx_sse(raw)

    def test_mixed_events(self):
        raw = (
            ": stream start\n"
            "event: greeting\n"
            "data: hello\n"
            "data: world\n"
            "id: 1\n"
            "\n"
            "data: simple\n"
            "\n"
            "event: close\n"
            "data: bye\n"
            "id: 2\n"
            "retry: 5000\n"
            "\n"
        )
        assert self._parse_with_zerodep(raw) == self._parse_with_httpx_sse(raw)
