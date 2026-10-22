"""Tests for default connection pooling on the module-level helpers."""

from __future__ import annotations

import asyncio
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
