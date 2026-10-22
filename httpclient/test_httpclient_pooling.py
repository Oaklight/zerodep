"""Tests for default connection pooling on the module-level helpers."""

from __future__ import annotations

import asyncio
import gc
import socket
import socketserver
import threading
import time

import pytest

import httpclient
from httpclient import _SyncConnectionPool


class _KeepAliveServer(socketserver.ThreadingTCPServer):
    """Minimal HTTP/1.1 server that keeps connections open."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _KeepAliveHandler)
        self.connections = 0
        self._count_lock = threading.Lock()

    def count_connection(self) -> None:
        with self._count_lock:
            self.connections += 1


class _KeepAliveHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        self.server.count_connection()  # type: ignore[attr-defined]
        while True:
            request_line = self.rfile.readline()
            if not request_line:
                return
            while True:
                header = self.rfile.readline()
                if header in (b"\r\n", b"\n", b""):
                    break
            self.wfile.write(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Length: 12\r\n"
                b"Content-Type: application/json\r\n"
                b"\r\n"
                b'{"ok": true}'
            )
            self.wfile.flush()


class _ClosingServer(socketserver.ThreadingTCPServer):
    """HTTP/1.1-ish server that answers once and closes without saying so."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _ClosingHandler)
        self.connections = 0
        self._count_lock = threading.Lock()

    def count_connection(self) -> None:
        with self._count_lock:
            self.connections += 1


class _ClosingHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        self.server.count_connection()  # type: ignore[attr-defined]
        request_line = self.rfile.readline()
        if not request_line:
            return
        while True:
            header = self.rfile.readline()
            if header in (b"\r\n", b"\n", b""):
                break
        self.wfile.write(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Length: 12\r\n"
            b"Content-Type: application/json\r\n"
            b"\r\n"
            b'{"ok": true}'
        )
        self.wfile.flush()
        # No ``Connection: close`` header: the client has to notice the dead
        # socket itself, by peeking or by retrying after EOF.


@pytest.fixture
def keep_alive_url():
    server = _KeepAliveServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        httpclient.close_pools()


class TestDefaultSyncPool:
    def test_module_level_get_reuses_one_connection(self, keep_alive_url):
        url, server = keep_alive_url
        for _ in range(5):
            response = httpclient.get(url)
            assert response.status_code == 200

        assert server.connections == 1

    def test_close_pools_releases_connections(self, keep_alive_url):
        url, server = keep_alive_url
        httpclient.get(url)
        httpclient.close_pools()

        assert sum(len(v) for v in httpclient._DEFAULT_SYNC_POOL._pool.values()) == 0
        assert httpclient.get(url).status_code == 200
        assert server.connections == 2

    def test_stale_pooled_connection_is_retried(self, keep_alive_url, monkeypatch):
        """A connection the server closed under us is retried once."""
        url, server = keep_alive_url
        # Hand out a connection that is already closed, and make the liveness
        # check report it as usable so the request — not the check — fails.
        conn = httpclient.http.client.HTTPConnection(
            server.server_address[0], server.server_address[1], timeout=5
        )
        conn.connect()
        conn.close()
        monkeypatch.setattr(httpclient, "_socket_peer_closed", lambda sock: False)
        with httpclient._DEFAULT_SYNC_POOL._lock:
            httpclient._DEFAULT_SYNC_POOL._pool[
                (server.server_address[0], server.server_address[1], False, True)
            ] = [(conn, time.monotonic())]

        response = httpclient.get(url)
        assert response.status_code == 200
        assert response.json() == {"ok": True}


class TestDefaultAsyncPool:
    def test_module_level_async_get_reuses_one_connection(self, keep_alive_url):
        url, server = keep_alive_url

        async def run():
            for _ in range(5):
                response = await httpclient.async_get(url)
                assert response.status_code == 200
            await httpclient.aclose_pools()

        asyncio.run(run())
        assert server.connections == 1

    def test_each_event_loop_gets_its_own_pool(self, keep_alive_url):
        url, server = keep_alive_url

        async def one():
            assert (await httpclient.async_get(url)).status_code == 200
            await httpclient.aclose_pools()

        asyncio.run(one())
        asyncio.run(one())
        # Pools are per loop, so the second loop opened its own connection.
        assert server.connections == 2


class _StallingHandler(socketserver.StreamRequestHandler):
    """Reads requests and never replies, holding the socket open.

    With ``answer_first`` the first request on each connection is answered
    normally so a connection can be pooled before the stall.
    """

    def handle(self) -> None:
        self.server.count_connection()  # type: ignore[attr-defined]
        first = True
        while True:
            request_line = self.rfile.readline()
            if not request_line:
                return
            while True:
                header = self.rfile.readline()
                if header in (b"\r\n", b"\n", b""):
                    break
            if not first or not self.server.answer_first:  # type: ignore[attr-defined]
                # Hold the connection open without answering so the caller
                # burns its own timeout budget.
                time.sleep(10)
                return
            first = False
            self.wfile.write(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Length: 12\r\n"
                b"Content-Type: application/json\r\n"
                b"\r\n"
                b'{"ok": true}'
            )
            self.wfile.flush()


class _StallingServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, answer_first: bool = False):
        super().__init__(("127.0.0.1", 0), _StallingHandler)
        self.answer_first = answer_first
        self.connections = 0
        self._count_lock = threading.Lock()

    def count_connection(self) -> None:
        with self._count_lock:
            self.connections += 1


def _serve_stalling(answer_first: bool):
    server = _StallingServer(answer_first=answer_first)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        httpclient.close_pools()


@pytest.fixture
def stalling_url():
    yield from _serve_stalling(answer_first=False)


@pytest.fixture
def stall_after_first_url():
    yield from _serve_stalling(answer_first=True)


class _TruncatedBodyHandler(socketserver.StreamRequestHandler):
    """Advertises a body it does not send, then closes."""

    def handle(self) -> None:
        request_line = self.rfile.readline()
        if not request_line:
            return
        while True:
            header = self.rfile.readline()
            if header in (b"\r\n", b"\n", b""):
                break
        self.wfile.write(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Length: 100\r\n"
            b"Content-Type: application/json\r\n"
            b"\r\n"
            b'{"ok":'
        )
        self.wfile.flush()


class _TruncatedBodyServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _TruncatedBodyHandler)


@pytest.fixture
def truncated_url():
    server = _TruncatedBodyServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        httpclient.close_pools()


class TestTimeouts:
    def test_timeout_is_not_retried(self, stalling_url):
        """A timeout must not be retried: it would double the caller's budget."""
        url, server = stalling_url
        started = time.monotonic()
        with pytest.raises(Exception) as excinfo:
            httpclient.get(url, timeout=0.3)
        elapsed = time.monotonic() - started

        assert type(excinfo.value).__name__ == "HttpTimeoutError"
        # One attempt only, and it respected the budget.
        assert server.connections == 1
        assert elapsed < 2.0

    def test_pooled_connection_adopts_the_callers_timeout(self, stall_after_first_url):
        """A reused socket must honour the current call's timeout, not the first."""
        url, server = stall_after_first_url
        assert httpclient.get(url, timeout=5).status_code == 200

        started = time.monotonic()
        with pytest.raises(Exception) as excinfo:
            httpclient.get(url, timeout=0.3)
        elapsed = time.monotonic() - started

        assert type(excinfo.value).__name__ == "HttpTimeoutError"
        assert elapsed < 2.0
        assert server.connections == 1


class TestFailedRead:
    def test_truncated_body_connection_is_not_pooled(self, truncated_url):
        """A connection whose body read failed must not be reused."""
        url, _ = truncated_url
        with pytest.raises(Exception):
            httpclient.get(url)

        assert sum(len(v) for v in httpclient._DEFAULT_SYNC_POOL._pool.values()) == 0

    def test_async_truncated_body_connection_is_not_pooled(self, truncated_url):
        url, _ = truncated_url

        async def run():
            with pytest.raises(Exception):
                await httpclient.async_get(url)
            pool = httpclient._default_async_pool()
            assert sum(len(v) for v in pool._pool.values()) == 0
            await httpclient.aclose_pools()

        asyncio.run(run())


class TestAsyncPoolLifecycle:
    def test_async_pools_are_released_with_their_loop(self, keep_alive_url):
        """A closed loop's pool must not be kept alive by the module."""
        url, _ = keep_alive_url
        before = {id(pool) for pool in httpclient._async_pools}

        async def one():
            assert (await httpclient.async_get(url)).status_code == 200
            # Deliberately not calling aclose_pools().

        asyncio.run(one())
        gc.collect()

        # The pool attached to the finished loop was not pinned by the module
        # registry; only pools from earlier tests may remain.
        assert {id(pool) for pool in httpclient._async_pools} <= before

    def test_async_http_1_0_response_is_not_pooled(self, httpbin_url):
        """HTTP/1.0 without ``Connection: keep-alive`` is not persistent."""

        async def run():
            assert (await httpclient.async_get(f"{httpbin_url}/get")).status_code == 200
            pool = httpclient._default_async_pool()
            assert sum(len(v) for v in pool._pool.values()) == 0
            await httpclient.aclose_pools()

        asyncio.run(run())

    def test_async_timeout_is_not_retried(self, stalling_url):
        url, server = stalling_url
        started = time.monotonic()

        async def run():
            with pytest.raises(Exception):
                await httpclient.async_get(url, timeout=0.3)
            await httpclient.aclose_pools()

        asyncio.run(run())
        assert server.connections == 1
        assert time.monotonic() - started < 2.0


class TestPoolKey:
    def test_verify_is_part_of_the_key(self, keep_alive_url):
        _, server = keep_alive_url
        pool = _SyncConnectionPool(pool_size=2)
        conn = httpclient.http.client.HTTPConnection(
            server.server_address[0], server.server_address[1]
        )
        conn.sock = socket.create_connection(server.server_address)

        pool.release(
            server.server_address[0],
            server.server_address[1],
            False,
            conn,
            verify=False,
        )
        assert (
            pool.acquire(
                server.server_address[0], server.server_address[1], False, 1.0, True
            )
            is None
        )
        assert (
            pool.acquire(
                server.server_address[0], server.server_address[1], False, 1.0, False
            )
            is conn
        )
        conn.close()


@pytest.fixture
def closing_url():
    server = _ClosingServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        httpclient.close_pools()


class TestServerClosesWithoutHeader:
    def test_sync_request_after_close_succeeds(self, closing_url):
        url, server = closing_url
        assert httpclient.get(url).status_code == 200
        # The pooled connection is dead but never advertised itself as such.
        assert httpclient.get(url).status_code == 200
        assert server.connections >= 2

    def test_async_request_after_close_succeeds(self, closing_url):
        url, server = closing_url

        async def run():
            assert (await httpclient.async_get(url)).status_code == 200
            assert (await httpclient.async_get(url)).status_code == 200
            await httpclient.aclose_pools()

        asyncio.run(run())
        assert server.connections >= 2


class _FakeConn:
    """Connection stub that records ``close()``."""

    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class _FakeWriter:
    """Stream-writer stub that records ``close()``."""

    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        return None


class TestGlobalConnectionCap:
    """``pool_size`` is per host, so idle sockets are also capped globally."""

    def test_sync_pool_evicts_oldest_beyond_the_cap(self):
        pool = httpclient._SyncConnectionPool(pool_size=5, max_total=2)
        conns = [_FakeConn() for _ in range(3)]

        for index, conn in enumerate(conns):
            pool.release(f"host-{index}", 80, False, conn, verify=True)

        assert sum(len(v) for v in pool._pool.values()) == 2
        assert conns[0].closed is True
        assert conns[1].closed is False
        assert conns[2].closed is False

    def test_sync_release_sweeps_expired_entries_of_other_hosts(self):
        pool = httpclient._SyncConnectionPool(pool_size=5, max_total=10)
        stale = _FakeConn()
        key = ("stale-host", 80, False, True)
        pool._pool[key] = [(stale, time.monotonic() - 10_000)]

        fresh = _FakeConn()
        pool.release("fresh-host", 80, False, fresh, verify=True)

        assert "stale-host" not in {k[0] for k in pool._pool}
        assert stale.closed is True
        assert sum(len(v) for v in pool._pool.values()) == 1

    def test_async_pool_evicts_oldest_beyond_the_cap(self):
        pool = httpclient._AsyncConnectionPool(pool_size=5, max_total=2)
        writers = [_FakeWriter() for _ in range(3)]

        async def run():
            for index, writer in enumerate(writers):
                await pool.release(
                    f"host-{index}", 80, False, object(), writer, verify=True
                )

        asyncio.run(run())

        assert sum(len(v) for v in pool._pool.values()) == 2
        assert writers[0].closed is True
        assert writers[2].closed is False

    def test_async_release_sweeps_expired_entries_of_other_hosts(self):
        pool = httpclient._AsyncConnectionPool(pool_size=5, max_total=10)
        stale = _FakeWriter()
        pool._pool[("stale-host", 80, False, True)] = [
            (object(), stale, time.monotonic() - 10_000)
        ]

        async def run():
            await pool.release(
                "fresh-host", 80, False, object(), _FakeWriter(), verify=True
            )

        asyncio.run(run())

        assert "stale-host" not in {k[0] for k in pool._pool}
        assert stale.closed is True


class TestIdleTimeoutIsConfigurable:
    """The idle window is per client, not a module constant."""

    def test_sync_pool_uses_its_own_idle_timeout(self):
        pool = httpclient._SyncConnectionPool(pool_size=2, idle_timeout=1.0)
        conn = _FakeConn()
        key = ("host", 80, False, True)
        pool._pool[key] = [(conn, time.monotonic() - 5.0)]

        assert pool.acquire("host", 80, False, 1.0, True) is None
        assert conn.closed is True

    def test_async_pool_uses_its_own_idle_timeout(self):
        pool = httpclient._AsyncConnectionPool(pool_size=2, idle_timeout=1.0)
        writer = _FakeWriter()
        pool._pool[("host", 80, False, True)] = [
            (object(), writer, time.monotonic() - 5.0)
        ]

        async def run():
            return await pool.acquire("host", 80, False, 1.0, True)

        assert asyncio.run(run()) is None
        assert writer.closed is True

    def test_clients_pass_the_timeout_to_the_pool(self):
        sync_client = httpclient.Client(pool_idle_timeout=0.25)
        async_client = httpclient.AsyncClient(pool_idle_timeout=0.5)

        assert sync_client._pool._idle_timeout == 0.25
        assert async_client._pool._idle_timeout == 0.5
