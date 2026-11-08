"""Tests for the buffered-response size limit.

Each test talks to a raw socket server so the wire shape (declared length,
chunked frames, EOF-delimited body, compressed bomb) is under test control.
"""

import gzip
import os
import socketserver
import sys
import threading
import time

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from httpclient import (  # noqa: E402
    AsyncClient,
    Client,
    DecompressionError,
    HttpClientError,
    ResponseTooLargeError,
)

# ── Raw response server ─────────────────────────────────────────────────────


class _RawHandler(socketserver.BaseRequestHandler):
    """Answer every request with a fixed, pre-built response.

    After writing the response the handler waits for the peer to close, so a
    test can tell a closed connection from one that is merely unpooled.
    """

    payload: bytes = b""
    connections: int = 0
    peer_closed: list[bool] = []

    def handle(self) -> None:
        state = type(self)
        state.connections += 1
        try:
            self.request.recv(65536)
            self.request.sendall(state.payload)
            self.request.settimeout(5)
            tail = self.request.recv(1)
            # b"" is a clean FIN; a reset means the peer closed with unread
            # bytes still in its receive buffer.
            state.peer_closed.append(tail == b"")
        except TimeoutError:
            state.peer_closed.append(False)
        except OSError:
            state.peer_closed.append(True)


class _RawServer:
    """A threaded TCP server that always writes ``payload``."""

    def __init__(self, payload: bytes) -> None:
        handler = type("_Handler", (_RawHandler,), {"payload": payload})
        self._handler = handler
        self._server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
        self._server.daemon_threads = True
        self.url = f"http://127.0.0.1:{self._server.server_address[1]}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    @property
    def connections(self) -> int:
        return self._handler.connections

    def wait_peer_closed(self, timeout: float = 5.0) -> bool:
        """Wait until the client closes its side of the connection."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._handler.peer_closed:
                return self._handler.peer_closed[0]
            time.sleep(0.01)
        return False

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()


@pytest.fixture
def raw_server():
    """Return a factory that serves *payload* and cleans up afterwards."""
    servers: list[_RawServer] = []

    def _make(payload: bytes) -> _RawServer:
        server = _RawServer(payload)
        servers.append(server)
        return server

    yield _make
    for server in servers:
        server.close()


# ── Wire payloads ───────────────────────────────────────────────────────────


def _declared_over(limit: int) -> bytes:
    """Declare a body ``10 * limit`` bytes long, send only a fragment."""
    return (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: application/octet-stream\r\n"
        + f"Content-Length: {limit * 10}\r\n".encode()
        + b"\r\n"
        + b"x" * 16
    )


def _chunked_over(limit: int) -> bytes:
    """Send two chunks of *limit* bytes each; the second crosses the cap."""
    size_line = f"{limit:x}\r\n".encode()
    body = (
        size_line
        + b"a" * limit
        + b"\r\n"
        + size_line
        + b"b" * limit
        + b"\r\n"
        + b"0\r\n\r\n"
    )
    return b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n" + body


def _eof_over(limit: int) -> bytes:
    """Send ``4 * limit`` bytes with no length header, then close."""
    return b"HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n" + b"c" * (limit * 4)


def _bodyless(status: int, reason: str) -> bytes:
    """A bodyless response that still carries a Content-Encoding header."""
    return (
        f"HTTP/1.1 {status} {reason}\r\n"
        "Content-Encoding: gzip\r\n"
        "Content-Length: 0\r\n"
        "\r\n"
    ).encode()


def _gzip_truncated(limit: int) -> bytes:
    """Send a gzip stream whose 8-byte trailer was cut off."""
    compressed = gzip.compress(b"d" * limit, 9)[:-8]
    return (
        b"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\n"
        + f"Content-Length: {len(compressed)}\r\n".encode()
        + b"\r\n"
        + compressed
    )


def _gzip_bomb(limit: int) -> bytes:
    """Compress ``100 * limit`` zero bytes; the wire body stays tiny."""
    compressed = gzip.compress(b"\x00" * (limit * 100), 9)
    return (
        b"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\n"
        + f"Content-Length: {len(compressed)}\r\n".encode()
        + b"\r\n"
        + compressed
    )


def _gzip_members(parts: list[bytes], *, truncate_last: bool = False) -> bytes:
    """Send one gzip member per part, concatenated into one stream."""
    compressed = b"".join(gzip.compress(part, 9) for part in parts)
    if truncate_last:
        # Cut the last member's 8-byte trailer.
        compressed = compressed[:-8]
    return (
        b"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\n"
        + f"Content-Length: {len(compressed)}\r\n".encode()
        + b"\r\n"
        + compressed
    )


def _chunked_gzip_frames(frames: list[bytes]) -> bytes:
    """Send each frame as one HTTP chunk of a chunked response.

    The chunked readers (`HTTPResponse.read1()` and `_aiter_chunked()`)
    never read past the HTTP chunk they are in, so every frame reaches the
    decompressor as exactly one read.  Framing the compressed stream this
    way pins a member boundary to the end of a read.
    """
    body = b"".join(
        f"{len(frame):x}\r\n".encode() + frame + b"\r\n" for frame in frames
    )
    return (
        b"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\n"
        b"Transfer-Encoding: chunked\r\n\r\n" + body + b"0\r\n\r\n"
    )


def _pool_entries(client: Client) -> int:
    return sum(len(entries) for entries in client._pool._pool.values())


# ── Option validation ───────────────────────────────────────────────────────


class TestOptionValidation:
    """A non-positive cap is refused before any request is sent."""

    @pytest.mark.parametrize("bad", [0, -1])
    def test_client_constructor_rejects_non_positive(self, bad):
        with pytest.raises(ValueError, match="positive integer"):
            Client(max_response_size=bad)

    @pytest.mark.parametrize("bad", [0, -1])
    def test_async_client_constructor_rejects_non_positive(self, bad):
        with pytest.raises(ValueError, match="positive integer"):
            AsyncClient(max_response_size=bad)

    @pytest.mark.parametrize("bad", [0, -1])
    def test_per_request_cap_is_validated_before_io(self, raw_server, bad):
        server = raw_server(_eof_over(1024))
        with Client() as client:
            with pytest.raises(ValueError, match="positive integer"):
                client.get(server.url, max_response_size=bad)
        assert server.connections == 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize("bad", [0, -1])
    async def test_async_per_request_cap_is_validated_before_io(self, raw_server, bad):
        server = raw_server(_eof_over(1024))
        async with AsyncClient() as client:
            with pytest.raises(ValueError, match="positive integer"):
                await client.get(server.url, max_response_size=bad)
        assert server.connections == 0


# ── Sync client ─────────────────────────────────────────────────────────────


class TestSyncResponseLimit:
    """Buffered sync reads refuse a body above ``max_response_size``."""

    def test_declared_length_is_refused_before_reading(self, raw_server):
        limit = 64
        server = raw_server(_declared_over(limit))
        with Client() as client:
            with pytest.raises(ResponseTooLargeError) as excinfo:
                client.get(server.url, max_response_size=limit)
            # The exception still references its traceback, so the
            # connection cannot have been freed by the collector: this
            # asserts an explicit close, not just "not pooled".
            assert server.wait_peer_closed()
            assert _pool_entries(client) == 0
        error = excinfo.value
        assert error.url == server.url
        assert error.max_size == limit
        assert error.declared == limit * 10
        assert error.received == 0
        assert isinstance(error, HttpClientError)

    def test_chunked_body_is_refused_at_the_limit(self, raw_server):
        limit = 64
        server = raw_server(_chunked_over(limit))
        with Client() as client:
            with pytest.raises(ResponseTooLargeError) as excinfo:
                client.get(server.url, max_response_size=limit)
            assert server.wait_peer_closed()
            assert _pool_entries(client) == 0
        assert excinfo.value.declared is None
        # http.client's chunked reader fills the requested amount across
        # chunk boundaries, so the read stops one byte past the cap rather
        # than at the frame that would cross it.
        assert excinfo.value.received == limit + 1

    def test_eof_body_is_refused_at_the_limit(self, raw_server):
        limit = 64
        server = raw_server(_eof_over(limit))
        with Client() as client:
            with pytest.raises(ResponseTooLargeError) as excinfo:
                client.get(server.url, max_response_size=limit)
            assert server.wait_peer_closed()
            assert _pool_entries(client) == 0
        assert excinfo.value.declared is None
        assert excinfo.value.received == limit + 1

    def test_gzip_bomb_is_refused(self, raw_server):
        limit = 1024
        server = raw_server(_gzip_bomb(limit))
        with Client() as client:
            with pytest.raises(ResponseTooLargeError) as excinfo:
                client.get(server.url, max_response_size=limit)
        # The decompressed size is what crossed the limit.
        assert excinfo.value.received == limit + 1

    def test_truncated_gzip_is_refused(self, raw_server):
        """A truncated stream must fail, not decode to a prefix."""
        server = raw_server(_gzip_truncated(256))
        with Client() as client:
            with pytest.raises(DecompressionError) as excinfo:
                client.get(server.url)
        assert isinstance(excinfo.value, HttpClientError)
        # The message names the problem, never the body.
        assert "d" * 32 not in str(excinfo.value)

    def test_every_gzip_member_is_decoded(self, raw_server):
        """Concatenated gzip members are one stream, not just the first."""
        server = raw_server(_gzip_members([b"first|", b"second|", b"third"]))
        with Client() as client:
            response = client.get(server.url)
        assert response.content == b"first|second|third"

    def test_truncated_second_gzip_member_is_refused(self, raw_server):
        """A member that ends mid-stream still fails the whole body."""
        server = raw_server(_gzip_members([b"first|", b"second|"], truncate_last=True))
        with Client() as client:
            with pytest.raises(DecompressionError):
                client.get(server.url)

    def test_gzip_members_share_one_size_budget(self, raw_server):
        """Several members cannot combine past ``max_response_size``."""
        limit = 256
        server = raw_server(_gzip_members([b"a" * 200, b"b" * 200]))
        with Client() as client:
            with pytest.raises(ResponseTooLargeError) as excinfo:
                client.get(server.url, max_response_size=limit)
        assert excinfo.value.received == limit + 1

    def test_streaming_decodes_every_gzip_member(self, raw_server):
        """The streaming decompressor crosses member boundaries too."""
        server = raw_server(_gzip_members([b"first|", b"second|", b"third"]))
        with Client() as client:
            response = client.get(server.url, stream=True)
            try:
                body = b"".join(response.iter_bytes())
            finally:
                response.close()
        assert body == b"first|second|third"

    @pytest.mark.parametrize(
        ("status", "reason", "method"),
        [
            (200, "OK", "HEAD"),
            (204, "No Content", "GET"),
            (304, "Not Modified", "GET"),
        ],
        ids=["head", "no-content", "not-modified"],
    )
    def test_bodyless_response_skips_decompression(
        self, raw_server, status, reason, method
    ):
        """HEAD/204/304 carry no body; Content-Encoding must not be decoded."""
        server = raw_server(_bodyless(status, reason))
        with Client() as client:
            response = client.request(method, server.url)
        assert response.content == b""

    def test_no_limit_by_default(self, raw_server):
        limit = 1024
        server = raw_server(_eof_over(limit))
        with Client() as client:
            response = client.get(server.url)
        assert len(response.content) == limit * 4

    def test_client_default_and_per_request_override(self, raw_server):
        limit = 1024
        server = raw_server(_eof_over(limit))
        with Client(max_response_size=64) as client:
            with pytest.raises(ResponseTooLargeError):
                client.get(server.url)
            response = client.get(server.url, max_response_size=8192)
        assert len(response.content) == limit * 4

    def test_streaming_is_not_limited(self, raw_server):
        limit = 1024
        server = raw_server(_eof_over(limit))
        with Client(max_response_size=64) as client:
            response = client.get(server.url, stream=True)
            try:
                body = b"".join(response.iter_bytes())
            finally:
                response.close()
        assert len(body) == limit * 4


# ── Async client ────────────────────────────────────────────────────────────


class TestAsyncResponseLimit:
    """Buffered async reads apply the same limit and error."""

    @pytest.mark.asyncio
    async def test_declared_length_is_refused_before_reading(self, raw_server):
        limit = 64
        server = raw_server(_declared_over(limit))
        async with AsyncClient() as client:
            with pytest.raises(ResponseTooLargeError) as excinfo:
                await client.get(server.url, max_response_size=limit)
            assert server.wait_peer_closed()
        error = excinfo.value
        assert error.url == server.url
        assert error.declared == limit * 10
        assert error.received == 0

    @pytest.mark.asyncio
    async def test_chunked_body_is_refused_at_the_limit(self, raw_server):
        limit = 64
        server = raw_server(_chunked_over(limit))
        async with AsyncClient() as client:
            with pytest.raises(ResponseTooLargeError) as excinfo:
                await client.get(server.url, max_response_size=limit)
            assert server.wait_peer_closed()
        assert excinfo.value.declared is None
        assert excinfo.value.received == limit * 2

    @pytest.mark.asyncio
    async def test_eof_body_is_refused_at_the_limit(self, raw_server):
        limit = 64
        server = raw_server(_eof_over(limit))
        async with AsyncClient() as client:
            with pytest.raises(ResponseTooLargeError) as excinfo:
                await client.get(server.url, max_response_size=limit)
            assert server.wait_peer_closed()
        assert excinfo.value.declared is None
        assert excinfo.value.received == limit + 1

    @pytest.mark.asyncio
    async def test_gzip_bomb_is_refused(self, raw_server):
        limit = 1024
        server = raw_server(_gzip_bomb(limit))
        async with AsyncClient() as client:
            with pytest.raises(ResponseTooLargeError) as excinfo:
                await client.get(server.url, max_response_size=limit)
        assert excinfo.value.received == limit + 1

    @pytest.mark.asyncio
    async def test_truncated_gzip_is_refused(self, raw_server):
        """A truncated stream must fail, not decode to a prefix."""
        server = raw_server(_gzip_truncated(256))
        async with AsyncClient() as client:
            with pytest.raises(DecompressionError):
                await client.get(server.url)

    @pytest.mark.asyncio
    async def test_every_gzip_member_is_decoded(self, raw_server):
        """Concatenated gzip members are one stream, not just the first."""
        server = raw_server(_gzip_members([b"first|", b"second|", b"third"]))
        async with AsyncClient() as client:
            response = await client.get(server.url)
        assert response.content == b"first|second|third"

    @pytest.mark.asyncio
    async def test_truncated_second_gzip_member_is_refused(self, raw_server):
        """A member that ends mid-stream still fails the whole body."""
        server = raw_server(_gzip_members([b"first|", b"second|"], truncate_last=True))
        async with AsyncClient() as client:
            with pytest.raises(DecompressionError):
                await client.get(server.url)

    @pytest.mark.asyncio
    async def test_gzip_members_share_one_size_budget(self, raw_server):
        """Several members cannot combine past ``max_response_size``."""
        limit = 256
        server = raw_server(_gzip_members([b"a" * 200, b"b" * 200]))
        async with AsyncClient() as client:
            with pytest.raises(ResponseTooLargeError) as excinfo:
                await client.get(server.url, max_response_size=limit)
        assert excinfo.value.received == limit + 1

    @pytest.mark.asyncio
    async def test_streaming_decodes_every_gzip_member(self, raw_server):
        """The async streaming decompressor crosses member boundaries too."""
        server = raw_server(_gzip_members([b"first|", b"second|", b"third"]))
        async with AsyncClient() as client:
            response = await client.get(server.url, stream=True)
            try:
                body = b"".join([chunk async for chunk in response.aiter_bytes()])
            finally:
                await response.aclose()
        assert body == b"first|second|third"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("status", "reason", "method"),
        [
            (200, "OK", "HEAD"),
            (204, "No Content", "GET"),
            (304, "Not Modified", "GET"),
        ],
        ids=["head", "no-content", "not-modified"],
    )
    async def test_bodyless_response_skips_decompression(
        self, raw_server, status, reason, method
    ):
        """HEAD/204/304 carry no body; Content-Encoding must not be decoded."""
        server = raw_server(_bodyless(status, reason))
        async with AsyncClient() as client:
            response = await client.request(method, server.url)
        assert response.content == b""

    @pytest.mark.asyncio
    async def test_no_limit_by_default(self, raw_server):
        limit = 1024
        server = raw_server(_eof_over(limit))
        async with AsyncClient() as client:
            response = await client.get(server.url)
        assert len(response.content) == limit * 4

    @pytest.mark.asyncio
    async def test_client_default_and_per_request_override(self, raw_server):
        limit = 1024
        server = raw_server(_eof_over(limit))
        async with AsyncClient(max_response_size=64) as client:
            with pytest.raises(ResponseTooLargeError):
                await client.get(server.url)
            response = await client.get(server.url, max_response_size=8192)
        assert len(response.content) == limit * 4


# ── Gzip member boundaries on read chunks ───────────────────────────────────


class TestGzipMemberBoundaries:
    """Member boundaries that fall on a read-chunk boundary (#303).

    ``StreamingResponse`` decompresses one read at a time, so a
    ``decompressobj`` can end a member at the last byte of a chunk and
    leave ``unused_data`` empty; the next member then starts in the next
    chunk, handed to a decompressor that already reported ``eof``.  The
    chunked framing below puts one gzip member in each HTTP chunk, which
    makes that the read alignment, and the sync/async readers never cross
    an HTTP chunk boundary.
    """

    @staticmethod
    def _frames(*members: bytes) -> bytes:
        return _chunked_gzip_frames([gzip.compress(member, 9) for member in members])

    def test_sync_every_member_ends_at_a_chunk_boundary(self, raw_server):
        server = raw_server(self._frames(b"first|", b"second|", b"third"))
        with Client() as client:
            response = client.get(server.url, stream=True)
            try:
                body = b"".join(response.iter_bytes())
            finally:
                response.close()
        assert body == b"first|second|third"

    @pytest.mark.asyncio
    async def test_async_every_member_ends_at_a_chunk_boundary(self, raw_server):
        server = raw_server(self._frames(b"first|", b"second|", b"third"))
        async with AsyncClient() as client:
            response = await client.get(server.url, stream=True)
            try:
                body = b"".join([chunk async for chunk in response.aiter_bytes()])
            finally:
                await response.aclose()
        assert body == b"first|second|third"

    @staticmethod
    def _split_frames(first: bytes, second: bytes) -> bytes:
        """Split the first member across two chunks, then start the second."""
        compressed = gzip.compress(first, 9)
        midpoint = len(compressed) // 2
        return _chunked_gzip_frames(
            [compressed[:midpoint], compressed[midpoint:], gzip.compress(second, 9)]
        )

    def test_sync_member_spans_two_chunks(self, raw_server):
        server = raw_server(self._split_frames(b"first|", b"second"))
        with Client() as client:
            response = client.get(server.url, stream=True)
            try:
                body = b"".join(response.iter_bytes())
            finally:
                response.close()
        assert body == b"first|second"

    @pytest.mark.asyncio
    async def test_async_member_spans_two_chunks(self, raw_server):
        server = raw_server(self._split_frames(b"first|", b"second"))
        async with AsyncClient() as client:
            response = await client.get(server.url, stream=True)
            try:
                body = b"".join([chunk async for chunk in response.aiter_bytes()])
            finally:
                await response.aclose()
        assert body == b"first|second"
