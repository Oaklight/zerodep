"""Tests for Unix domain socket support in httpserver."""

from __future__ import annotations

import asyncio
import os
import stat
import sys

import pytest

from httpserver import App, JSONResponse

# Skip all tests on Windows — Unix sockets not available
pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="Unix sockets not available on Windows"
)


@pytest.fixture
def socket_path(tmp_path):
    """Return a path for a Unix socket in a temp directory."""
    return str(tmp_path / "test.sock")


@pytest.fixture
def app():
    """Create a simple test app."""
    app = App()

    @app.route("/health")
    async def health(request):
        return JSONResponse({"status": "ok"})

    @app.route("/echo", methods=["POST"])
    async def echo(request):
        return JSONResponse(request.json())

    return app


class TestUnixSocketServe:
    """Test the Unix socket server lifecycle."""

    @pytest.mark.asyncio
    async def test_socket_created_and_permissions(self, app, socket_path):
        """Socket file is created with 0600 permissions."""
        serve_task = asyncio.create_task(app._serve("", 0, socket=socket_path))
        await asyncio.sleep(0.3)

        assert os.path.exists(socket_path)
        mode = os.stat(socket_path).st_mode
        assert stat.S_ISSOCK(mode)
        # Owner-only: 0o600
        perm = stat.S_IMODE(mode)
        assert perm == 0o600

        app.shutdown()
        await serve_task

    @pytest.mark.asyncio
    async def test_socket_cleaned_up_on_shutdown(self, app, socket_path):
        """Socket file is removed on shutdown."""
        serve_task = asyncio.create_task(app._serve("", 0, socket=socket_path))
        await asyncio.sleep(0.3)
        assert os.path.exists(socket_path)

        app.shutdown()
        await serve_task
        assert not os.path.exists(socket_path)

    @pytest.mark.asyncio
    async def test_stale_socket_removed(self, app, socket_path):
        """A stale socket file is cleaned up before starting."""
        # Create a fake stale socket using a real server
        stale_server = await asyncio.start_unix_server(
            lambda r, w: None, path=socket_path
        )
        stale_server.close()
        await stale_server.wait_closed()
        # Socket file still exists (stale)
        assert os.path.exists(socket_path)

        serve_task = asyncio.create_task(app._serve("", 0, socket=socket_path))
        await asyncio.sleep(0.3)
        assert os.path.exists(socket_path)

        app.shutdown()
        await serve_task

    @pytest.mark.asyncio
    async def test_request_via_unix_socket(self, app, socket_path):
        """HTTP request works over Unix socket."""
        serve_task = asyncio.create_task(app._serve("", 0, socket=socket_path))
        await asyncio.sleep(0.3)

        # Connect via Unix socket
        reader, writer = await asyncio.open_unix_connection(socket_path)
        writer.write(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
        await writer.drain()

        response = await asyncio.wait_for(reader.read(4096), timeout=5)
        response_str = response.decode()
        assert "200" in response_str
        assert '"status"' in response_str
        assert '"ok"' in response_str

        writer.close()
        await writer.wait_closed()

        app.shutdown()
        await serve_task

    @pytest.mark.asyncio
    async def test_post_request_via_unix_socket(self, app, socket_path):
        """POST with JSON body works over Unix socket."""
        serve_task = asyncio.create_task(app._serve("", 0, socket=socket_path))
        await asyncio.sleep(0.3)

        reader, writer = await asyncio.open_unix_connection(socket_path)
        body = b'{"hello": "world"}'
        request = (
            f"POST /echo HTTP/1.1\r\n"
            f"Host: localhost\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"\r\n"
        ).encode() + body
        writer.write(request)
        await writer.drain()

        response = await asyncio.wait_for(reader.read(4096), timeout=5)
        response_str = response.decode()
        assert "200" in response_str
        assert '"hello"' in response_str
        assert '"world"' in response_str

        writer.close()
        await writer.wait_closed()

        app.shutdown()
        await serve_task

    def test_non_socket_file_exits(self, app, tmp_path):
        """Exits if path exists but is not a socket."""
        regular_file = tmp_path / "not_a_socket"
        regular_file.write_text("hello")

        with pytest.raises(SystemExit):
            asyncio.run(app._serve("", 0, socket=str(regular_file)))

    def test_missing_parent_dir_exits(self, app, tmp_path):
        """Exits if parent directory does not exist."""
        bad_path = str(tmp_path / "nonexistent_dir" / "test.sock")
        with pytest.raises(SystemExit):
            asyncio.run(app._serve("", 0, socket=bad_path))

    @pytest.mark.asyncio
    async def test_tcp_still_works(self, app):
        """TCP mode still works when socket is not set."""
        serve_task = asyncio.create_task(app._serve("127.0.0.1", 0))
        await asyncio.sleep(0.3)

        assert app.port is not None
        assert app.port > 0

        reader, writer = await asyncio.open_connection("127.0.0.1", app.port)
        writer.write(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
        await writer.drain()

        response = await asyncio.wait_for(reader.read(4096), timeout=5)
        assert b"200" in response

        writer.close()
        await writer.wait_closed()

        app.shutdown()
        await serve_task
