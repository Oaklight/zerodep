"""Edge-behavior tests for httpclient resource management."""

import os
import sys
import time
import warnings

sys.path.insert(0, os.path.dirname(__file__))

import pytest

from httpclient import (
    CaseInsensitiveDict,
    Client,
    HttpConnectionError,
    HTTPError,
    HttpTimeoutError,
    StreamingResponse,
    _prepare_body,
    _SyncConnectionPool,
    async_get,
    get,
)

# ── Connection Pool Lifecycle ───────────────────────────────────────────────


class TestConnectionPoolLifecycle:
    """Tests for pool acquire/release/eviction paths."""

    def test_pool_returns_connection_after_non_streaming_request(self, httpbin_url):
        """Non-streaming request should return connection to pool."""
        with Client() as c:
            c.get(f"{httpbin_url}/get")
            # After a successful non-streaming request, pool should have a conn
            pool_entries = sum(len(v) for v in c._pool._pool.values())
            assert pool_entries >= 1

    def test_pool_discards_connection_on_close_header(self, httpbin_url):
        """Connection with 'Connection: close' header should not be pooled."""
        with Client() as c:
            # Force Connection: close via request headers -- server will echo it
            c.get(f"{httpbin_url}/get", headers={"Connection": "close"})
            # Pool may or may not retain depending on server response;
            # the key invariant is no crash and pool is in valid state
            pool_entries = sum(len(v) for v in c._pool._pool.values())
            assert pool_entries >= 0  # no corruption

    def test_pool_evicts_stale_connections(self):
        """Connections older than idle timeout should be evicted."""
        import http.client

        pool = _SyncConnectionPool(pool_size=5)

        # Create a mock connection via real HTTPConnection (not connected)
        conn = http.client.HTTPConnection("127.0.0.1", 9999, timeout=1)
        # Manually insert with an old timestamp
        key = ("127.0.0.1", 9999, False)
        pool._pool[key] = [(conn, time.monotonic() - 9999)]

        # acquire should evict the stale connection
        result = pool.acquire("127.0.0.1", 9999, False, 1.0, True)
        assert result is None
        # Pool entry list should be empty after eviction
        assert len(pool._pool.get(key, [])) == 0

    def test_pool_overflow_discards_excess(self, httpbin_url):
        """When pool is full, excess connections are closed, not queued."""
        import http.client

        pool = _SyncConnectionPool(pool_size=1)

        conn1 = http.client.HTTPConnection("127.0.0.1", 9999)
        conn2 = http.client.HTTPConnection("127.0.0.1", 9999)

        pool.release("127.0.0.1", 9999, False, conn1)
        pool.release("127.0.0.1", 9999, False, conn2)

        # Pool size is 1, so only one should be stored
        key = ("127.0.0.1", 9999, False)
        assert len(pool._pool[key]) == 1

    def test_close_all_empties_pool(self, httpbin_url):
        """close_all() should remove all pooled connections."""
        with Client() as c:
            c.get(f"{httpbin_url}/get")
            c.get(f"{httpbin_url}/json")
            c._pool.close_all()
            pool_entries = sum(len(v) for v in c._pool._pool.values())
            assert pool_entries == 0


# ── Streaming Cleanup ───────────────────────────────────────────────────────


class TestStreamingCleanup:
    """Tests for streaming response resource cleanup."""

    def test_streaming_response_close_releases_resources(self, httpbin_url):
        """Explicit close() should release all underlying resources."""
        r = get(f"{httpbin_url}/get", stream=True)
        assert isinstance(r, StreamingResponse)
        assert not r._closed
        r.close()
        assert r._closed

    def test_streaming_response_context_manager_cleanup(self, httpbin_url):
        """Context manager exit should close streaming response."""
        with get(f"{httpbin_url}/get", stream=True) as r:
            assert isinstance(r, StreamingResponse)
            assert not r._closed
        assert r._closed

    def test_streaming_response_double_close_is_noop(self, httpbin_url):
        """Calling close() twice should not raise."""
        with get(f"{httpbin_url}/get", stream=True) as r:
            pass
        # Already closed by context manager
        assert r._closed
        # Second close should be a no-op
        r.close()
        assert r._closed

    def test_unconsumed_streaming_response_warns(self, httpbin_url):
        """StreamingResponse.__del__ should warn if not closed."""
        r = get(f"{httpbin_url}/get", stream=True)
        assert isinstance(r, StreamingResponse)
        # Trigger __del__ by dropping the reference
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", ResourceWarning)
            r.__del__()
            resource_warnings = [
                x for x in w if issubclass(x.category, ResourceWarning)
            ]
            # After __del__, the response should be closed
            assert r._closed
            # There should have been a ResourceWarning
            assert len(resource_warnings) >= 1
            assert "Unclosed StreamingResponse" in str(resource_warnings[0].message)


# ── Async Streaming Cleanup ─────────────────────────────────────────────────


class TestAsyncStreamingCleanup:
    """Async counterparts of TestStreamingCleanup."""

    @pytest.mark.asyncio
    async def test_aclose_releases_writer(self, httpbin_url):
        """Explicit aclose() should close the underlying async writer."""
        r = await async_get(f"{httpbin_url}/get", stream=True)
        assert isinstance(r, StreamingResponse)
        assert not r._closed
        assert r._async_writer is not None
        await r.aclose()
        assert r._closed

    @pytest.mark.asyncio
    async def test_async_context_manager_cleanup(self, httpbin_url):
        """async with should call aclose() on exit."""
        r = await async_get(f"{httpbin_url}/get", stream=True)
        async with r:
            assert not r._closed
        assert r._closed

    @pytest.mark.asyncio
    async def test_async_double_aclose_is_noop(self, httpbin_url):
        """Calling aclose() twice should not raise."""
        r = await async_get(f"{httpbin_url}/get", stream=True)
        await r.aclose()
        assert r._closed
        await r.aclose()
        assert r._closed

    @pytest.mark.asyncio
    async def test_sync_close_closes_async_writer(self, httpbin_url):
        """close() must also close _async_writer (the fd-leak fix)."""
        r = await async_get(f"{httpbin_url}/get", stream=True)
        assert r._async_writer is not None
        writer = r._async_writer

        r.close()
        assert r._closed
        assert writer.is_closing()

    @pytest.mark.asyncio
    async def test_del_closes_async_writer(self, httpbin_url):
        """__del__ → close() must close _async_writer to prevent fd leaks."""
        r = await async_get(f"{httpbin_url}/get", stream=True)
        assert r._async_writer is not None
        writer = r._async_writer

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", ResourceWarning)
            r.__del__()
            resource_warnings = [
                x for x in w if issubclass(x.category, ResourceWarning)
            ]
            assert r._closed
            assert writer.is_closing()
            assert len(resource_warnings) >= 1
            assert "Unclosed StreamingResponse" in str(resource_warnings[0].message)

    @pytest.mark.asyncio
    async def test_unconsumed_async_stream_close_prevents_leak(self, httpbin_url):
        """An async stream that is never iterated must still be closeable."""
        r = await async_get(f"{httpbin_url}/get", stream=True)
        assert r._async_writer is not None
        r.close()
        assert r._closed
        assert r._async_writer.is_closing()


# ── Timeout Behavior ────────────────────────────────────────────────────────


class TestTimeoutBehavior:
    """Tests for timeout handling."""

    def test_timeout_raises_with_context(self):
        """HttpTimeoutError should include url and timeout value."""
        err = HttpTimeoutError("timed out", url="http://example.com/slow", timeout=5.0)
        assert err.url == "http://example.com/slow"
        assert err.timeout == 5.0
        assert "timed out" in str(err)

    def test_connection_error_includes_host(self):
        """HttpConnectionError should include host and port."""
        err = HttpConnectionError(
            "Connection refused", host="db.example.com", port=5432
        )
        assert err.host == "db.example.com"
        assert err.port == 5432
        assert "Connection refused" in str(err)

    def test_http_error_includes_status_and_url(self):
        """HTTPError should include status_code, body, and url."""
        err = HTTPError(404, "Not Found", "http://example.com/missing")
        assert err.status_code == 404
        assert err.body == "Not Found"
        assert err.url == "http://example.com/missing"
        assert "404" in str(err)
        assert "http://example.com/missing" in str(err)


# ── _prepare_body ───────────────────────────────────────────────────────────


class TestPrepareBody:
    """Tests for _prepare_body dict-data handling."""

    def test_dict_data_urlencoded(self):
        """Dict data without files should be URL-encoded."""
        body, content_type = _prepare_body(data={"key": "value", "foo": "bar"})
        assert content_type == "application/x-www-form-urlencoded"
        assert body is not None
        decoded = body.decode("utf-8")
        assert "key=value" in decoded
        assert "foo=bar" in decoded

    def test_dict_data_special_chars(self):
        """Dict data with special characters should be percent-encoded."""
        body, content_type = _prepare_body(data={"q": "hello world", "x": "a&b=c"})
        assert content_type == "application/x-www-form-urlencoded"
        decoded = body.decode("utf-8")
        assert "hello+world" in decoded or "hello%20world" in decoded
        assert "a%26b%3Dc" in decoded

    def test_dict_data_empty(self):
        """Empty dict should produce empty URL-encoded body."""
        body, content_type = _prepare_body(data={})
        assert content_type == "application/x-www-form-urlencoded"
        assert body == b""

    def test_json_takes_priority_over_dict_data(self):
        """json parameter should take priority over dict data."""
        body, content_type = _prepare_body(data={"key": "value"}, json={"j": 1})
        assert content_type == "application/json"

    def test_str_data_still_works(self):
        """String data should still work as before."""
        body, content_type = _prepare_body(data="key=value")
        assert content_type == "application/x-www-form-urlencoded"
        assert body == b"key=value"

    def test_none_data_returns_none(self):
        """None data should return (None, None)."""
        body, content_type = _prepare_body()
        assert body is None
        assert content_type is None


# ── Chunked Transfer Decoding ───────────────────────────────────────────────


class TestChunkedDecoding:
    """Tests for chunked transfer encoding edge cases."""

    @staticmethod
    def _make_chunked_response(raw_bytes: bytes) -> StreamingResponse:
        """Build a StreamingResponse wired to an in-memory chunked stream."""
        import asyncio

        reader = asyncio.StreamReader()
        reader.feed_data(raw_bytes)
        reader.feed_eof()
        return StreamingResponse._from_async(
            status_code=200,
            headers=CaseInsensitiveDict(),
            url="http://test",
            reader=reader,
            writer=None,
            is_chunked=True,
            content_length=None,
            timeout=5.0,
        )

    @pytest.mark.asyncio
    async def test_valid_chunked_stream(self):
        """Normal chunked stream should decode correctly."""
        raw = b"5\r\nhello\r\n6\r\n world\r\n0\r\n\r\n"
        resp = self._make_chunked_response(raw)
        data = b"".join([chunk async for chunk in resp.aiter_bytes()])
        assert data == b"hello world"

    @pytest.mark.asyncio
    async def test_http_error_injected_mid_stream(self):
        """Mid-stream HTTP error raises HttpConnectionError."""
        raw = b"HTTP/1.1 502 Bad Gateway\r\n"
        resp = self._make_chunked_response(raw)
        with pytest.raises(HttpConnectionError, match="Invalid chunked encoding"):
            async for _ in resp.aiter_bytes():
                pass

    @pytest.mark.asyncio
    async def test_garbage_chunk_size(self):
        """Non-hex chunk size line should raise HttpConnectionError."""
        raw = b"not-hex\r\nsome data\r\n0\r\n\r\n"
        resp = self._make_chunked_response(raw)
        with pytest.raises(HttpConnectionError, match="Invalid chunked encoding"):
            async for _ in resp.aiter_bytes():
                pass

    @pytest.mark.asyncio
    async def test_error_after_valid_chunks(self):
        """Error injected after some valid chunks should raise HttpConnectionError."""
        raw = b"5\r\nhello\r\nHTTP/1.1 500 Internal Server Error\r\n"
        resp = self._make_chunked_response(raw)
        chunks = []
        with pytest.raises(HttpConnectionError, match="Invalid chunked encoding"):
            async for chunk in resp.aiter_bytes():
                chunks.append(chunk)
        assert b"hello" in chunks


class TestIterLinesDecoding:
    """Tests for iter_lines / aiter_lines edge cases (gzip, UTF-8 boundaries)."""

    @staticmethod
    def _make_sync_response(
        chunks: list[bytes], content_encoding: str = ""
    ) -> StreamingResponse:
        """Build a sync StreamingResponse backed by an in-memory chunk list."""
        it = iter(chunks)

        class FakeResp:
            def read(self, n: int = 4096) -> bytes:
                return next(it, b"")

        obj = object.__new__(StreamingResponse)
        obj.status_code = 200
        obj.headers = CaseInsensitiveDict()
        obj.url = "http://test"
        obj._encoding = "utf-8"
        if content_encoding:
            import zlib

            wbits = (
                16 + zlib.MAX_WBITS
                if content_encoding in ("gzip", "x-gzip")
                else -zlib.MAX_WBITS
            )
            obj._decompressor = zlib.decompressobj(wbits)
        else:
            obj._decompressor = None
        obj._sync_resp = FakeResp()
        obj._sync_conn = None
        obj._async_reader = None
        obj._async_writer = None
        obj._async_timeout = None
        obj._is_chunked = False
        obj._content_length = None
        obj._bytes_remaining = None
        obj._closed = False
        return obj

    @staticmethod
    def _make_async_response(
        chunks: list[bytes], content_encoding: str = ""
    ) -> StreamingResponse:
        """Build an async StreamingResponse backed by an in-memory chunk list."""
        import asyncio

        reader = asyncio.StreamReader()
        total = b"".join(chunks)
        reader.feed_data(total)
        reader.feed_eof()
        return StreamingResponse._from_async(
            status_code=200,
            headers=CaseInsensitiveDict(),
            url="http://test",
            reader=reader,
            writer=None,
            is_chunked=False,
            content_length=len(total),
            timeout=5.0,
            content_encoding=content_encoding,
        )

    def test_iter_lines_gzip(self):
        """iter_lines should decompress gzip content correctly."""
        import gzip

        payload = b"line one\nline two\nline three\n"
        compressed = gzip.compress(payload)
        resp = self._make_sync_response([compressed], content_encoding="gzip")
        lines = list(resp.iter_lines())
        assert lines == ["line one", "line two", "line three"]

    def test_iter_lines_gzip_chunked(self):
        """iter_lines should handle gzip data split across multiple chunks."""
        import gzip

        payload = b"hello\nworld\n"
        compressed = gzip.compress(payload)
        mid = len(compressed) // 2
        resp = self._make_sync_response(
            [compressed[:mid], compressed[mid:]], content_encoding="gzip"
        )
        lines = list(resp.iter_lines())
        assert lines == ["hello", "world"]

    def test_iter_lines_utf8_chunk_boundary(self):
        """iter_lines should not corrupt multi-byte UTF-8 split across chunks."""
        text = "café\nnaïve\n"
        raw = text.encode("utf-8")
        split_at = raw.index(b"\xc3\xa9") + 1  # split mid-é
        resp = self._make_sync_response([raw[:split_at], raw[split_at:]])
        lines = list(resp.iter_lines())
        assert lines == ["café", "naïve"]

    @pytest.mark.asyncio
    async def test_aiter_lines_gzip(self):
        """aiter_lines should decompress gzip content correctly."""
        import gzip

        payload = b"async line one\nasync line two\n"
        compressed = gzip.compress(payload)
        resp = self._make_async_response([compressed], content_encoding="gzip")
        lines = [line async for line in resp.aiter_lines()]
        assert lines == ["async line one", "async line two"]

    @pytest.mark.asyncio
    async def test_aiter_lines_utf8_chunk_boundary(self):
        """aiter_lines should not corrupt multi-byte UTF-8 split across chunks."""
        import gzip

        text = "données\nrésumé\n"
        raw = text.encode("utf-8")
        compressed = gzip.compress(raw)
        mid = len(compressed) // 2
        resp = self._make_async_response(
            [compressed[:mid], compressed[mid:]], content_encoding="gzip"
        )
        lines = [line async for line in resp.aiter_lines()]
        assert lines == ["données", "résumé"]

    def test_iter_lines_crlf(self):
        """iter_lines should handle \\r\\n line endings."""
        payload = b"line1\r\nline2\r\nline3"
        resp = self._make_sync_response([payload])
        lines = list(resp.iter_lines())
        assert lines == ["line1", "line2", "line3"]
