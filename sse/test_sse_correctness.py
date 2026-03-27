"""Correctness tests for zerodep SSE client."""

import asyncio
import http.server
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
)

# ── Helpers ──


def _run_async(coro_fn, *args, **kwargs):
    return asyncio.run(coro_fn(*args, **kwargs))


async def _async_lines(lines):
    """Convert a list of strings to an async iterable."""
    for line in lines:
        yield line


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
            e.data = "world"

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


# ── _SSEParser tests ──


class TestSSEParser:
    def test_simple_data(self):
        p = _SSEParser()
        assert p.feed_line("data: hello") is None
        event = p.feed_line("")
        assert event is not None
        assert event.data == "hello"
        assert event.event == "message"

    def test_multiline_data(self):
        p = _SSEParser()
        p.feed_line("data: line1")
        p.feed_line("data: line2")
        p.feed_line("data: line3")
        event = p.feed_line("")
        assert event.data == "line1\nline2\nline3"

    def test_event_type(self):
        p = _SSEParser()
        p.feed_line("event: update")
        p.feed_line("data: payload")
        event = p.feed_line("")
        assert event.event == "update"

    def test_event_type_resets_after_dispatch(self):
        p = _SSEParser()
        p.feed_line("event: custom")
        p.feed_line("data: first")
        p.feed_line("")
        p.feed_line("data: second")
        event = p.feed_line("")
        assert event.event == "message"  # reset to default

    def test_id_field(self):
        p = _SSEParser()
        p.feed_line("id: 42")
        p.feed_line("data: payload")
        event = p.feed_line("")
        assert event.id == "42"

    def test_id_persists_across_events(self):
        p = _SSEParser()
        p.feed_line("id: 42")
        p.feed_line("data: first")
        p.feed_line("")
        p.feed_line("data: second")
        event = p.feed_line("")
        assert event.id == "42"  # persists

    def test_id_with_null_ignored(self):
        p = _SSEParser()
        p.feed_line("id: 42")
        p.feed_line("data: first")
        p.feed_line("")
        p.feed_line("id: bad\0id")
        p.feed_line("data: second")
        event = p.feed_line("")
        assert event.id == "42"  # null id ignored

    def test_retry_field(self):
        p = _SSEParser()
        p.feed_line("retry: 5000")
        p.feed_line("data: payload")
        event = p.feed_line("")
        assert event.retry == 5000

    def test_retry_non_digit_ignored(self):
        p = _SSEParser()
        p.feed_line("retry: abc")
        p.feed_line("data: payload")
        event = p.feed_line("")
        assert event.retry is None

    def test_retry_empty_ignored(self):
        p = _SSEParser()
        p.feed_line("retry:")
        p.feed_line("data: payload")
        event = p.feed_line("")
        assert event.retry is None

    def test_retry_persists(self):
        p = _SSEParser()
        p.feed_line("retry: 1000")
        p.feed_line("data: first")
        p.feed_line("")
        p.feed_line("data: second")
        event = p.feed_line("")
        assert event.retry == 1000

    def test_comment_ignored(self):
        p = _SSEParser()
        p.feed_line(": this is a comment")
        p.feed_line("data: hello")
        event = p.feed_line("")
        assert event.data == "hello"

    def test_comment_only_no_dispatch(self):
        p = _SSEParser()
        assert p.feed_line(": comment") is None
        assert p.feed_line("") is None  # no data to dispatch

    def test_empty_data_field(self):
        """data: with no value -> empty string in data buf."""
        p = _SSEParser()
        p.feed_line("data:")
        event = p.feed_line("")
        assert event is not None
        assert event.data == ""

    def test_data_leading_space_stripped(self):
        p = _SSEParser()
        p.feed_line("data: hello")
        event = p.feed_line("")
        assert event.data == "hello"

    def test_data_double_space_preserved(self):
        """Only one leading space is stripped."""
        p = _SSEParser()
        p.feed_line("data:  hello")
        event = p.feed_line("")
        assert event.data == " hello"

    def test_data_no_space(self):
        p = _SSEParser()
        p.feed_line("data:hello")
        event = p.feed_line("")
        assert event.data == "hello"

    def test_field_no_colon(self):
        p = _SSEParser()
        p.feed_line("data")  # field="data", value=""
        event = p.feed_line("")
        assert event is not None
        assert event.data == ""

    def test_unknown_field_ignored(self):
        p = _SSEParser()
        p.feed_line("foo: bar")
        p.feed_line("data: hello")
        event = p.feed_line("")
        assert event.data == "hello"

    def test_bom_stripped_from_first_line(self):
        p = _SSEParser()
        p.feed_line("\ufeffdata: hello")
        event = p.feed_line("")
        assert event.data == "hello"

    def test_bom_only_on_first_line(self):
        """BOM on non-first line is NOT stripped — '\ufeffdata' is unknown field."""
        p = _SSEParser()
        p.feed_line("data: first")
        p.feed_line("")
        # '\ufeffdata' is not recognized as 'data', so nothing appended
        p.feed_line("\ufeffdata: second")
        event = p.feed_line("")
        assert event is None  # no data buffer, nothing to dispatch

    def test_multiple_empty_lines_no_extra_dispatch(self):
        p = _SSEParser()
        p.feed_line("data: hello")
        event1 = p.feed_line("")
        assert event1 is not None
        event2 = p.feed_line("")
        assert event2 is None  # no pending data

    def test_all_fields(self):
        p = _SSEParser()
        p.feed_line("event: notification")
        p.feed_line("data: payload")
        p.feed_line("id: 99")
        p.feed_line("retry: 2000")
        event = p.feed_line("")
        assert event.event == "notification"
        assert event.data == "payload"
        assert event.id == "99"
        assert event.retry == 2000

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
            count = self.server.request_counts.get(path, 0)
            self.server.request_counts[path] = count + 1
            if count == 0:
                self._serve_sse(self.server.sse_lines)
            else:
                self.send_response(204)
                self.end_headers()
        elif path == "/events-repeat":
            # Always serve events (for retry exhaustion tests)
            self._serve_sse(self.server.sse_lines)
        elif path == "/events-with-id":
            last_id = self.headers.get("Last-Event-ID", "")
            self.server.received_last_event_ids.append(last_id)
            count = self.server.request_counts.get(path, 0)
            self.server.request_counts[path] = count + 1
            if count == 0:
                self._serve_sse(self.server.sse_lines)
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

        response = httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            stream=httpx.ByteStream(raw.encode()),
        )
        response.read()
        source = httpx_sse.EventSource(response)
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
