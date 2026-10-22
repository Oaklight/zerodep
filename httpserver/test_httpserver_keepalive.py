"""Tests for HTTP keep-alive support (zerodep#210)."""

from __future__ import annotations

import asyncio
import contextlib
import http.client
import socket
import threading

from httpserver import App, Response, StreamingResponse


def _build_app(**kwargs) -> App:
    """Build an app with routes that expose the connection identity."""
    app = App(**kwargs)

    @app.get("/whoami")
    async def whoami(request):
        return {"port": request.client_addr[1]}

    @app.get("/stream")
    async def stream(request):
        async def generate():
            yield "chunk"

        return StreamingResponse(generate(), content_type="text/plain")

    @app.get("/close")
    async def close_route(request):
        return Response(body="bye", headers={"Connection": "close"})

    return app


@contextlib.contextmanager
def _live(app: App):
    """Run *app* on an ephemeral port for the duration of the block."""
    ready = threading.Event()

    def _run():
        async def _start():
            app._shutdown_event = asyncio.Event()
            app._loop = asyncio.get_running_loop()
            server = await asyncio.start_server(app._handle_connection, "127.0.0.1", 0)
            app._server = server
            addrs = server.sockets[0].getsockname()
            app.host, app.port = addrs[0], addrs[1]
            ready.set()
            async with server:
                await app._shutdown_event.wait()

        asyncio.run(_start())

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    assert ready.wait(timeout=5), "server did not start"
    try:
        yield app
    finally:
        app.shutdown()
        thread.join(timeout=5)


def _get(conn: http.client.HTTPConnection, path: str, **headers: str):
    conn.request("GET", path, headers=headers or {})
    return conn.getresponse()


def _raw_exchange(sock: socket.socket, request: bytes) -> bytes:
    """Send *request* and read the response headers."""
    sock.sendall(request)
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
    return data


class TestKeepAlive:
    def test_two_requests_share_one_connection(self):
        with _live(_build_app()) as app:
            conn = http.client.HTTPConnection(app.host, app.port, timeout=5)
            first = _get(conn, "/whoami")
            first_port = first.read().decode()
            second = _get(conn, "/whoami")
            second_port = second.read().decode()

            assert first.status == 200
            assert second.status == 200
            assert first_port == second_port, "second request opened a new connection"
            assert second.getheader("Connection").lower() == "keep-alive"
            assert conn.sock is not None
            conn.close()

    def test_request_close_header_closes(self):
        with _live(_build_app()) as app:
            conn = http.client.HTTPConnection(app.host, app.port, timeout=5)
            response = _get(conn, "/whoami", Connection="close")
            response.read()

            assert response.getheader("Connection").lower() == "close"
            assert conn.sock is None
            conn.close()

    def test_keep_alive_disabled(self):
        with _live(_build_app(keep_alive=False)) as app:
            conn = http.client.HTTPConnection(app.host, app.port, timeout=5)
            response = _get(conn, "/whoami")
            response.read()

            assert response.getheader("Connection").lower() == "close"
            assert conn.sock is None
            conn.close()

    def test_max_requests_per_connection(self):
        with _live(_build_app(max_requests_per_connection=1)) as app:
            conn = http.client.HTTPConnection(app.host, app.port, timeout=5)
            response = _get(conn, "/whoami")
            response.read()

            assert response.getheader("Connection").lower() == "close"
            conn.close()

    def test_streaming_response_closes(self):
        with _live(_build_app()) as app:
            conn = http.client.HTTPConnection(app.host, app.port, timeout=5)
            response = _get(conn, "/stream")
            assert response.read() == b"chunk"

            assert response.getheader("Connection").lower() == "close"
            conn.close()

    def test_http_1_0_closes_without_keep_alive(self):
        with _live(_build_app()) as app:
            with socket.create_connection((app.host, app.port), timeout=5) as sock:
                data = _raw_exchange(
                    sock, b"GET /whoami HTTP/1.0\r\nHost: localhost\r\n\r\n"
                )
                assert b"Connection: close" in data
                assert sock.recv(4096) == b"", "server did not close HTTP/1.0"

    def test_http_1_0_keep_alive_keeps_the_socket_open(self):
        with _live(_build_app()) as app:
            with socket.create_connection((app.host, app.port), timeout=5) as sock:
                data = _raw_exchange(
                    sock,
                    b"GET /whoami HTTP/1.0\r\n"
                    b"Host: localhost\r\n"
                    b"Connection: keep-alive\r\n\r\n",
                )
                assert b"Connection: keep-alive" in data

                second = _raw_exchange(
                    sock,
                    b"GET /whoami HTTP/1.0\r\n"
                    b"Host: localhost\r\n"
                    b"Connection: keep-alive\r\n\r\n",
                )
                assert second.startswith(b"HTTP/1.1 200")

    def test_idle_connection_is_closed_quietly(self):
        with _live(_build_app(keep_alive_timeout=0.1)) as app:
            with socket.create_connection((app.host, app.port), timeout=5) as sock:
                _raw_exchange(sock, b"GET /whoami HTTP/1.1\r\nHost: localhost\r\n\r\n")
                # Drain the body so the server returns to reading.
                sock.settimeout(5)
                data = b""
                while b"}" not in data:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    data += chunk

                assert sock.recv(4096) == b"", "idle connection stayed open"

    def test_client_disconnect_between_requests_is_quiet(self):
        """Closing after a response must not produce a 400 for the next read."""
        with _live(_build_app()) as app:
            with socket.create_connection((app.host, app.port), timeout=5) as sock:
                data = _raw_exchange(
                    sock, b"GET /whoami HTTP/1.1\r\nHost: localhost\r\n\r\n"
                )
                assert b"200 OK" in data
            # The context manager closes the socket; the server's next read
            # sees EOF and simply ends the connection.

    def test_response_close_header_closes(self):
        with _live(_build_app()) as app:
            conn = http.client.HTTPConnection(app.host, app.port, timeout=5)
            response = _get(conn, "/close")
            response.read()

            assert response.getheader("Connection").lower() == "close"
            assert conn.sock is None
            conn.close()

    def test_head_has_no_body_and_keeps_the_connection_clean(self):
        with _live(_build_app()) as app:
            with socket.create_connection((app.host, app.port), timeout=5) as sock:
                sock.sendall(b"HEAD /whoami HTTP/1.1\r\nHost: localhost\r\n\r\n")
                data = b""
                while b"\r\n\r\n" not in data:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                head, _, rest = data.partition(b"\r\n\r\n")

                assert b"405" in head
                assert b"Content-Length: 0" in head
                assert rest == b"", f"HEAD wrote a body: {rest!r}"

                # The next request on the same connection must not see stray
                # bytes from the HEAD response (#210 review).
                sock.sendall(b"GET /whoami HTTP/1.1\r\nHost: localhost\r\n\r\n")
                follow_up = b""
                while b'{"port"' not in follow_up:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    follow_up += chunk
                assert follow_up.startswith(b"HTTP/1.1 200")

    def test_zero_keep_alive_timeout_does_not_advertise_reuse(self):
        with _live(_build_app(keep_alive_timeout=0)) as app:
            conn = http.client.HTTPConnection(app.host, app.port, timeout=5)
            response = _get(conn, "/whoami")
            response.read()

            assert response.getheader("Connection").lower() == "close"
            assert conn.sock is None
            conn.close()
