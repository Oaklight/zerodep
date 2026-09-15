"""Tests for TLS support in httpserver."""

from __future__ import annotations

import asyncio
import socket as socket_mod
import ssl
import subprocess
import sys

import pytest

from httpserver import App, JSONResponse


def _generate_self_signed_cert(cert_path: str, key_path: str) -> None:
    """Generate a self-signed certificate using openssl CLI."""
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-keyout",
            key_path,
            "-out",
            cert_path,
            "-days",
            "1",
            "-nodes",
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=DNS:localhost,IP:127.0.0.1",
        ],
        check=True,
        capture_output=True,
    )


@pytest.fixture(scope="module")
def tls_certs(tmp_path_factory):
    """Generate a temporary self-signed cert/key pair."""
    d = tmp_path_factory.mktemp("tls")
    cert_path = str(d / "cert.pem")
    key_path = str(d / "key.pem")
    _generate_self_signed_cert(cert_path, key_path)
    return cert_path, key_path


@pytest.fixture(scope="module")
def server_ssl_context(tls_certs):
    """Create a server-side SSLContext."""
    cert_path, key_path = tls_certs
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert_path, key_path)
    return ctx


@pytest.fixture(scope="module")
def client_ssl_context(tls_certs):
    """Create a client-side SSLContext that trusts the self-signed cert."""
    cert_path, _ = tls_certs
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(cert_path)
    return ctx


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


class TestTLSServe:
    """Test TLS server lifecycle and connections."""

    @pytest.mark.asyncio
    async def test_tls_accepts_https_connection(
        self, app, server_ssl_context, client_ssl_context
    ):
        """Server with ssl_context accepts TLS connections."""
        serve_task = asyncio.create_task(
            app._serve("127.0.0.1", 0, ssl_context=server_ssl_context)
        )
        await asyncio.sleep(0.3)

        reader, writer = await asyncio.open_connection(
            "127.0.0.1", app.port, ssl=client_ssl_context
        )
        writer.write(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
        await writer.drain()

        response = await asyncio.wait_for(reader.read(4096), timeout=5)
        assert b"200 OK" in response
        assert b'"status": "ok"' in response

        writer.close()
        await writer.wait_closed()
        app.shutdown()
        await serve_task

    @pytest.mark.asyncio
    async def test_tls_rejects_plaintext(self, app, server_ssl_context):
        """TLS server rejects plain HTTP connections."""
        serve_task = asyncio.create_task(
            app._serve("127.0.0.1", 0, ssl_context=server_ssl_context)
        )
        await asyncio.sleep(0.3)

        reader, writer = await asyncio.open_connection("127.0.0.1", app.port)
        writer.write(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
        await writer.drain()

        response = await asyncio.wait_for(reader.read(4096), timeout=2)
        # Server should close the connection or return empty (TLS handshake fails)
        assert response == b"" or b"200 OK" not in response

        writer.close()
        await writer.wait_closed()
        app.shutdown()
        await serve_task

    @pytest.mark.asyncio
    async def test_tls_post_request(self, app, server_ssl_context, client_ssl_context):
        """POST with JSON body works over TLS."""
        serve_task = asyncio.create_task(
            app._serve("127.0.0.1", 0, ssl_context=server_ssl_context)
        )
        await asyncio.sleep(0.3)

        reader, writer = await asyncio.open_connection(
            "127.0.0.1", app.port, ssl=client_ssl_context
        )
        body = b'{"msg":"hello"}'
        request = (
            b"POST /echo HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n"
            b"\r\n" + body
        )
        writer.write(request)
        await writer.drain()

        response = await asyncio.wait_for(reader.read(4096), timeout=5)
        assert b"200 OK" in response
        assert b'"msg": "hello"' in response

        writer.close()
        await writer.wait_closed()
        app.shutdown()
        await serve_task

    @pytest.mark.asyncio
    async def test_no_ssl_context_serves_plaintext(self, app):
        """Without ssl_context, server accepts plain HTTP (default behavior)."""
        serve_task = asyncio.create_task(app._serve("127.0.0.1", 0))
        await asyncio.sleep(0.3)

        reader, writer = await asyncio.open_connection("127.0.0.1", app.port)
        writer.write(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
        await writer.drain()

        response = await asyncio.wait_for(reader.read(4096), timeout=5)
        assert b"200 OK" in response

        writer.close()
        await writer.wait_closed()
        app.shutdown()
        await serve_task


class TestSocketTuning:
    """Test backlog, reuse_address, reuse_port parameters."""

    @pytest.mark.asyncio
    async def test_custom_backlog(self, app):
        """Server starts with custom backlog value."""
        serve_task = asyncio.create_task(app._serve("127.0.0.1", 0, backlog=2048))
        await asyncio.sleep(0.3)

        reader, writer = await asyncio.open_connection("127.0.0.1", app.port)
        writer.write(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
        await writer.drain()

        response = await asyncio.wait_for(reader.read(4096), timeout=5)
        assert b"200 OK" in response

        writer.close()
        await writer.wait_closed()
        app.shutdown()
        await serve_task

    @pytest.mark.asyncio
    async def test_reuse_address(self, app):
        """Server starts with reuse_address=True."""
        serve_task = asyncio.create_task(app._serve("127.0.0.1", 0, reuse_address=True))
        await asyncio.sleep(0.3)

        reader, writer = await asyncio.open_connection("127.0.0.1", app.port)
        writer.write(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
        await writer.drain()

        response = await asyncio.wait_for(reader.read(4096), timeout=5)
        assert b"200 OK" in response

        writer.close()
        await writer.wait_closed()
        app.shutdown()
        await serve_task

    @pytest.mark.asyncio
    async def test_combined_tls_and_tuning(
        self, app, server_ssl_context, client_ssl_context
    ):
        """TLS and socket tuning parameters work together."""
        serve_task = asyncio.create_task(
            app._serve(
                "127.0.0.1",
                0,
                ssl_context=server_ssl_context,
                backlog=512,
                reuse_address=True,
            )
        )
        await asyncio.sleep(0.3)

        reader, writer = await asyncio.open_connection(
            "127.0.0.1", app.port, ssl=client_ssl_context
        )
        writer.write(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
        await writer.drain()

        response = await asyncio.wait_for(reader.read(4096), timeout=5)
        assert b"200 OK" in response

        writer.close()
        await writer.wait_closed()
        app.shutdown()
        await serve_task


@pytest.fixture
def socket_path(tmp_path):
    """Return a path for a Unix socket in a temp directory."""
    return str(tmp_path / "tls_test.sock")


@pytest.mark.skipif(
    sys.platform == "win32", reason="Unix sockets not available on Windows"
)
class TestTLSUnixSocket:
    """Test TLS over Unix domain sockets."""

    @pytest.mark.asyncio
    async def test_tls_over_unix_socket(
        self, app, socket_path, server_ssl_context, client_ssl_context
    ):
        """TLS works over Unix domain sockets."""
        serve_task = asyncio.create_task(
            app._serve("", 0, socket=socket_path, ssl_context=server_ssl_context)
        )
        await asyncio.sleep(0.3)

        raw_sock = socket_mod.socket(socket_mod.AF_UNIX, socket_mod.SOCK_STREAM)
        raw_sock.connect(socket_path)
        raw_sock.setblocking(False)

        reader, writer = await asyncio.open_connection(
            sock=raw_sock, ssl=client_ssl_context, server_hostname="localhost"
        )
        writer.write(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
        await writer.drain()

        response = await asyncio.wait_for(reader.read(4096), timeout=5)
        assert b"200 OK" in response
        assert b'"status": "ok"' in response

        writer.close()
        await writer.wait_closed()
        app.shutdown()
        await serve_task
