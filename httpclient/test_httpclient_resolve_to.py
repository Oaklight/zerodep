"""Tests for ``resolve_to`` connect-time address pinning (#305).

The option exists for DNS-rebinding protection: a caller resolves a name,
validates the addresses, and hands them to the client so it connects to a
validated peer without resolving again.  The URL host still provides the
``Host`` header, TLS SNI and certificate verification.

These tests use a local plain-HTTP server and a local TLS server whose
certificate is issued for a fake hostname, so a successful TLS request
proves SNI and verification used the URL host rather than the pinned peer.
"""

from __future__ import annotations

import contextlib
import shutil
import ssl
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from httpclient import AsyncClient, Client, HttpConnectionError, async_get, get

requires_openssl = pytest.mark.skipif(
    shutil.which("openssl") is None, reason="openssl CLI not found"
)


def _make_handler(routes):
    """Build a handler that dispatches on path."""

    class _Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format, *args):  # noqa: A002
            pass

        def do_GET(self):  # noqa: N802
            route = routes.get(self.path.split("?")[0])
            if route is None:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            route(self)

    return _Handler


def _serve(httpd):
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, thread


@contextlib.contextmanager
def _plain_server():
    """Serve /hit, /ok, /jump (cross-host) and /jump-same (relative)."""
    seen: list[tuple[str | None, str]] = []
    state: dict[str, str] = {"jump_to": ""}

    def hit(handler):
        seen.append((handler.headers.get("Host"), handler.path))
        body = b"ok"
        handler.send_response(200)
        handler.send_header("Content-Type", "text/plain")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)

    def jump(handler):
        seen.append((handler.headers.get("Host"), handler.path))
        handler.send_response(302)
        handler.send_header("Location", state["jump_to"])
        handler.send_header("Content-Length", "0")
        handler.end_headers()

    def jump_same(handler):
        seen.append((handler.headers.get("Host"), handler.path))
        handler.send_response(302)
        handler.send_header("Location", "/ok")
        handler.send_header("Content-Length", "0")
        handler.end_headers()

    httpd = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        _make_handler(
            {"/hit": hit, "/ok": hit, "/jump": jump, "/jump-same": jump_same}
        ),
    )
    served, thread = _serve(httpd)
    state["jump_to"] = f"http://other.invalid:{served.server_port}/ok"
    try:
        yield served.server_port, seen, state
    finally:
        served.shutdown()
        served.server_close()
        thread.join(timeout=5)


def _generate_cert(cert_path: str, key_path: str, hostname: str) -> None:
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
            f"/CN={hostname}",
            "-addext",
            f"subjectAltName=DNS:{hostname}",
        ],
        check=True,
        capture_output=True,
    )


@contextlib.contextmanager
def _tls_server(tmp_path, hostname: str):
    """Serve /hit over TLS and record the SNI names the server received."""
    cert_path = str(tmp_path / "cert.pem")
    key_path = str(tmp_path / "key.pem")
    _generate_cert(cert_path, key_path, hostname)

    sni_names: list[str] = []
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert_path, key_path)
    ctx.sni_callback = lambda _sock, name, _ctx: sni_names.append(name)

    def hit(handler):
        body = b"ok"
        handler.send_response(200)
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _make_handler({"/hit": hit}))
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    served, thread = _serve(httpd)
    try:
        yield served.server_port, cert_path, sni_names
    finally:
        served.shutdown()
        served.server_close()
        thread.join(timeout=5)


# ---------------------------------------------------------------------------
# Plain HTTP
# ---------------------------------------------------------------------------


def test_sync_pinned_peer_uses_the_url_host():
    with _plain_server() as (port, seen, _state):
        response = get(f"http://pinned.invalid:{port}/hit", resolve_to="127.0.0.1")

    assert response.status_code == 200
    assert response.text == "ok"
    assert seen == [(f"pinned.invalid:{port}", "/hit")]


def test_sync_unresolvable_host_without_the_pin_fails():
    with _plain_server() as (port, _seen, _state):
        with pytest.raises(HttpConnectionError):
            get(f"http://pinned.invalid:{port}/hit", timeout=2)


def test_sync_addresses_are_tried_in_order():
    """The first address refuses; the second one serves the request."""
    with _plain_server() as (port, seen, _state):
        response = get(
            f"http://pinned.invalid:{port}/hit",
            resolve_to=["127.0.0.2", "127.0.0.1"],
            timeout=2,
        )

    assert response.status_code == 200
    assert seen == [(f"pinned.invalid:{port}", "/hit")]


def test_sync_a_dead_pinned_address_is_reported_without_echoing_it():
    with _plain_server() as (_port, _seen, _state):
        with pytest.raises(HttpConnectionError) as excinfo:
            get(
                "http://pinned.invalid:1/hit",
                resolve_to="127.0.0.10",
                timeout=1,
            )

    message = str(excinfo.value)
    assert "pinned.invalid" in message
    assert "127.0.0.10" not in message


def test_sync_pool_separates_pinned_and_unpinned_connections():
    with _plain_server() as (port, _seen, _state):
        with Client() as client:
            client.get(f"http://127.0.0.1:{port}/hit")
            client.get(f"http://127.0.0.1:{port}/hit", resolve_to="127.0.0.1")

            keys = set(client._pool._pool)

    assert ("127.0.0.1", port, False, True, None) in keys
    assert ("127.0.0.1", port, False, True, ("127.0.0.1",)) in keys


def test_sync_same_origin_redirect_keeps_the_pin():
    with _plain_server() as (port, seen, _state):
        response = get(
            f"http://pinned.invalid:{port}/jump-same", resolve_to="127.0.0.1"
        )

    assert response.status_code == 200
    assert [path for _host, path in seen] == ["/jump-same", "/ok"]


def test_sync_redirect_to_another_host_drops_the_pin():
    """The new host must not be pinned to the address validated for the old."""
    with _plain_server() as (port, seen, _state):
        with pytest.raises(HttpConnectionError):
            get(f"http://pinned.invalid:{port}/jump", resolve_to="127.0.0.1")

    # The redirect was followed, and the second hop resolved normally
    # (``other.invalid``), so it never reached the local server.
    assert [path for _host, path in seen] == ["/jump"]


# ---------------------------------------------------------------------------
# TLS: SNI and certificate verification use the URL host
# ---------------------------------------------------------------------------


@requires_openssl
def test_sync_tls_verifies_the_url_host(tmp_path, monkeypatch):
    with _tls_server(tmp_path, "pinned.test") as (port, cert_path, sni_names):
        monkeypatch.setenv("SSL_CERT_FILE", cert_path)
        response = get(f"https://pinned.test:{port}/hit", resolve_to="127.0.0.1")

    assert response.status_code == 200
    assert response.text == "ok"
    assert sni_names == ["pinned.test"]


# ---------------------------------------------------------------------------
# Async parity
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_pinned_peer_uses_the_url_host():
    with _plain_server() as (port, seen, _state):
        response = await async_get(
            f"http://pinned.invalid:{port}/hit", resolve_to="127.0.0.1"
        )

    assert response.status_code == 200
    assert seen == [("pinned.invalid", "/hit")]


@pytest.mark.asyncio
async def test_async_addresses_are_tried_in_order():
    with _plain_server() as (port, seen, _state):
        response = await async_get(
            f"http://pinned.invalid:{port}/hit",
            resolve_to=["127.0.0.2", "127.0.0.1"],
            timeout=2,
        )

    assert response.status_code == 200
    assert seen == [("pinned.invalid", "/hit")]


@pytest.mark.asyncio
async def test_async_redirect_to_another_host_drops_the_pin():
    with _plain_server() as (port, seen, _state):
        with pytest.raises(HttpConnectionError):
            await async_get(
                f"http://pinned.invalid:{port}/jump", resolve_to="127.0.0.1"
            )

    assert [path for _host, path in seen] == ["/jump"]


@pytest.mark.asyncio
async def test_async_pool_separates_pinned_and_unpinned_connections():
    with _plain_server() as (port, _seen, _state):
        async with AsyncClient() as client:
            await client.get(f"http://127.0.0.1:{port}/hit")
            await client.get(f"http://127.0.0.1:{port}/hit", resolve_to="127.0.0.1")

            keys = set(client._pool._pool)

    assert ("127.0.0.1", port, False, True, None) in keys
    assert ("127.0.0.1", port, False, True, ("127.0.0.1",)) in keys


@requires_openssl
@pytest.mark.asyncio
async def test_async_tls_verifies_the_url_host(tmp_path, monkeypatch):
    with _tls_server(tmp_path, "pinned.test") as (port, cert_path, sni_names):
        monkeypatch.setenv("SSL_CERT_FILE", cert_path)
        response = await async_get(
            f"https://pinned.test:{port}/hit", resolve_to="127.0.0.1"
        )

    assert response.status_code == 200
    assert sni_names == ["pinned.test"]


# ---------------------------------------------------------------------------
# Proxy interaction: fail closed
# ---------------------------------------------------------------------------


def test_client_rejects_resolve_to_with_proxy():
    with pytest.raises(ValueError, match="proxy"):
        Client(proxy="http://127.0.0.1:9", resolve_to="127.0.0.1")


def test_request_rejects_resolve_to_with_proxy():
    with pytest.raises(ValueError, match="proxy"):
        get("http://example.test/", proxy="http://127.0.0.1:9", resolve_to="127.0.0.1")


def test_proxy_check_does_not_depend_on_the_address_list():
    """An empty pin still fails closed when a proxy is set."""
    with pytest.raises(ValueError, match="proxy"):
        get("http://example.test/", proxy="http://127.0.0.1:9", resolve_to=())


def test_empty_resolve_to_is_rejected_without_a_proxy():
    with pytest.raises(ValueError, match="at least one address"):
        Client(resolve_to=())


@pytest.mark.asyncio
async def test_async_client_rejects_resolve_to_with_proxy():
    with pytest.raises(ValueError, match="proxy"):
        AsyncClient(proxy="http://127.0.0.1:9", resolve_to="127.0.0.1")
