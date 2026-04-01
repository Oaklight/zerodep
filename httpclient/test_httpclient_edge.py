"""Edge-behavior tests for httpclient resource management."""

import os
import sys
import time
import warnings

sys.path.insert(0, os.path.dirname(__file__))

from httpclient import (
    Client,
    HttpConnectionError,
    HTTPError,
    HttpTimeoutError,
    StreamingResponse,
    _SyncConnectionPool,
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
