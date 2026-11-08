"""Tests for ``follow_redirects=False`` (#306).

The flag returns the first 3xx response instead of following it, so a caller
can read ``Location``, validate the next hop and issue its own request.  The
tests prove the second hop is never contacted by counting requests on a
separate local server.
"""

import contextlib
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote

import pytest

from httpclient import (
    AsyncClient,
    Client,
    DigestAuth,
    StreamingResponse,
    TooManyRedirects,
    async_get,
    get,
)


def _handler(routes):
    """Build a handler that dispatches on path, with a per-server counter."""

    class _Handler(BaseHTTPRequestHandler):
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


@contextlib.contextmanager
def _counter_server():
    """Serve every request with 200 and record the paths it saw."""
    hits = []

    def hit(handler):
        hits.append(handler.path)
        body = b"ok"
        handler.send_response(200)
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)

    httpd = ThreadingHTTPServer(
        ("127.0.0.1", 0), _handler({"/hit": hit, "/elsewhere": hit})
    )
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}/hit", hits
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


@contextlib.contextmanager
def _digest_then_redirect(target_url):
    """Challenge with Digest on the first request, redirect on the retry."""

    def protected(handler):
        if handler.headers.get("Authorization", "").startswith("Digest "):
            handler.send_response(302)
            handler.send_header("Location", target_url)
            handler.send_header("Content-Length", "0")
            handler.end_headers()
            return
        handler.send_response(401)
        handler.send_header(
            "WWW-Authenticate",
            'Digest realm="testrealm@host.com", nonce="testnonce123", '
            'qop="auth", algorithm=MD5',
        )
        handler.send_header("Content-Length", "0")
        handler.end_headers()

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _handler({"/protected": protected}))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}/protected"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


class TestSyncFollowRedirects:
    def test_302_is_returned_without_following(self, httpbin_url):
        with _counter_server() as (target, hits):
            url = f"{httpbin_url}/redirect-to?url={quote(target, safe='')}"
            response = get(url, follow_redirects=False)

            assert response.status_code == 302
            assert response.headers["location"] == target
            assert response.content == b""
        assert hits == []

    def test_default_still_follows(self, httpbin_url):
        response = get(f"{httpbin_url}/redirect/2")
        assert response.status_code == 200

    def test_client_default_and_per_request_override(self, httpbin_url):
        with Client(follow_redirects=False) as client:
            assert client.get(f"{httpbin_url}/redirect/1").status_code == 302
            assert (
                client.get(
                    f"{httpbin_url}/redirect/1", follow_redirects=True
                ).status_code
                == 200
            )

    def test_stream_returns_the_3xx_unread(self, httpbin_url):
        with get(f"{httpbin_url}/redirect/2", stream=True, follow_redirects=False) as r:
            assert isinstance(r, StreamingResponse)
            assert r.status_code == 302

    def test_redirect_loop_and_max_redirects_are_unchanged(self, httpbin_url):
        with pytest.raises(TooManyRedirects):
            get(f"{httpbin_url}/redirect/3", max_redirects=1)

    def test_redirect_after_digest_retry_is_not_followed(self):
        with _counter_server() as (target, hits):
            with _digest_then_redirect(target) as url:
                response = get(
                    url,
                    auth=DigestAuth("user", "pass"),
                    follow_redirects=False,
                )

            assert response.status_code == 302
            assert response.headers["location"] == target
            assert hits == []

    def test_redirect_after_digest_retry_is_followed_by_default(self):
        with _counter_server() as (target, hits):
            with _digest_then_redirect(target) as url:
                response = get(url, auth=DigestAuth("user", "pass"))

            assert response.status_code == 200
            assert hits == ["/hit"]


class TestAsyncFollowRedirects:
    @pytest.mark.asyncio
    async def test_302_is_returned_without_following(self, httpbin_url):
        with _counter_server() as (target, hits):
            url = f"{httpbin_url}/redirect-to?url={quote(target, safe='')}"
            response = await async_get(url, follow_redirects=False)

            assert response.status_code == 302
            assert response.headers["location"] == target
            assert response.content == b""
        assert hits == []

    @pytest.mark.asyncio
    async def test_default_still_follows(self, httpbin_url):
        response = await async_get(f"{httpbin_url}/redirect/2")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_client_default_and_per_request_override(self, httpbin_url):
        async with AsyncClient(follow_redirects=False) as client:
            assert (await client.get(f"{httpbin_url}/redirect/1")).status_code == 302
            assert (
                await client.get(f"{httpbin_url}/redirect/1", follow_redirects=True)
            ).status_code == 200

    @pytest.mark.asyncio
    async def test_stream_returns_the_3xx_unread(self, httpbin_url):
        response = await async_get(
            f"{httpbin_url}/redirect/2", stream=True, follow_redirects=False
        )
        async with response:
            assert isinstance(response, StreamingResponse)
            assert response.status_code == 302

    @pytest.mark.asyncio
    async def test_redirect_loop_and_max_redirects_are_unchanged(self, httpbin_url):
        with pytest.raises(TooManyRedirects):
            await async_get(f"{httpbin_url}/redirect/3", max_redirects=1)

    @pytest.mark.asyncio
    async def test_redirect_after_digest_retry_is_not_followed(self):
        with _counter_server() as (target, hits):
            with _digest_then_redirect(target) as url:
                response = await async_get(
                    url,
                    auth=DigestAuth("user", "pass"),
                    follow_redirects=False,
                )

            assert response.status_code == 302
            assert response.headers["location"] == target
            assert hits == []

    @pytest.mark.asyncio
    async def test_redirect_after_digest_retry_is_followed_by_default(self):
        with _counter_server() as (target, hits):
            with _digest_then_redirect(target) as url:
                response = await async_get(url, auth=DigestAuth("user", "pass"))

            assert response.status_code == 200
            assert hits == ["/hit"]
