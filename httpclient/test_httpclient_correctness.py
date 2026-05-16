"""Correctness tests: zerodep HTTP client vs httpx."""

import asyncio
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from httpclient import (
    AsyncClient,
    BasicAuth,
    Client,
    DigestAuth,
    HttpConnectionError,
    HTTPError,
    Socks5Error,
    StreamingResponse,
    async_delete,
    async_get,
    async_patch,
    async_post,
    async_put,
    delete,
    get,
    patch,
    post,
    put,
)

httpx = pytest.importorskip("httpx", reason="httpx not installed")


# ── Sync vs httpx: GET ──


class TestSyncGet:
    def test_simple_get(self, httpbin_url):
        ours = get(f"{httpbin_url}/get")
        theirs = httpx.get(f"{httpbin_url}/get")
        assert ours.status_code == theirs.status_code

    def test_get_with_params(self, httpbin_url):
        params = {"key": "value", "num": "42"}
        ours = get(f"{httpbin_url}/get", params=params)
        theirs = httpx.get(f"{httpbin_url}/get", params=params)
        assert ours.json()["args"] == theirs.json()["args"]  # type: ignore

    def test_get_with_headers(self, httpbin_url):
        hdrs = {"X-Custom": "test123"}
        ours = get(f"{httpbin_url}/get", headers=hdrs)
        theirs = httpx.get(f"{httpbin_url}/get", headers=hdrs)
        assert ours.json()["headers"]["X-Custom"] == "test123"  # type: ignore
        assert theirs.json()["headers"]["X-Custom"] == "test123"

    def test_get_json_response(self, httpbin_url):
        ours = get(f"{httpbin_url}/json")
        theirs = httpx.get(f"{httpbin_url}/json")
        assert ours.json() == theirs.json()  # type: ignore

    def test_response_text(self, httpbin_url):
        ours = get(f"{httpbin_url}/html")
        assert "<html>" in ours.text.lower() or "<h1>" in ours.text.lower()  # type: ignore


# ── Sync vs httpx: POST/PUT/PATCH/DELETE ──


class TestSyncMutations:
    def test_post_json(self, httpbin_url):
        payload = {"name": "zerodep", "version": 1}
        ours = post(f"{httpbin_url}/post", json=payload)
        theirs = httpx.post(f"{httpbin_url}/post", json=payload)
        assert ours.json()["json"] == payload  # type: ignore
        assert theirs.json()["json"] == payload

    def test_post_data(self, httpbin_url):
        ours = post(f"{httpbin_url}/post", data="field=value")
        assert ours.status_code == 200
        assert ours.json()["form"]["field"] == "value"  # type: ignore

    def test_put_json(self, httpbin_url):
        payload = {"updated": True}
        ours = put(f"{httpbin_url}/put", json=payload)
        theirs = httpx.put(f"{httpbin_url}/put", json=payload)
        assert ours.json()["json"] == payload  # type: ignore
        assert theirs.json()["json"] == payload

    def test_patch_json(self, httpbin_url):
        payload = {"patched": True}
        ours = patch(f"{httpbin_url}/patch", json=payload)
        theirs = httpx.patch(f"{httpbin_url}/patch", json=payload)
        assert ours.json()["json"] == payload  # type: ignore
        assert theirs.json()["json"] == payload

    def test_delete(self, httpbin_url):
        ours = delete(f"{httpbin_url}/delete")
        theirs = httpx.delete(f"{httpbin_url}/delete")
        assert ours.status_code == theirs.status_code


# ── Sync: redirects ──


class TestSyncRedirects:
    def test_redirect_followed(self, httpbin_url):
        ours = get(f"{httpbin_url}/redirect/3")
        assert ours.status_code == 200

    def test_absolute_redirect(self, httpbin_url):
        ours = get(f"{httpbin_url}/absolute-redirect/1")
        assert ours.status_code == 200


# ── Sync: status codes ──


class TestSyncStatusCodes:
    @pytest.mark.parametrize("code", [200, 201, 204, 400, 401, 403, 404, 500])
    def test_status_code(self, httpbin_url, code: int):
        ours = get(f"{httpbin_url}/status/{code}")
        assert ours.status_code == code

    def test_raise_for_status(self, httpbin_url):
        r = get(f"{httpbin_url}/status/404")
        with pytest.raises(HTTPError):
            r.raise_for_status()

    def test_ok_property(self, httpbin_url):
        r200 = get(f"{httpbin_url}/status/200")
        r404 = get(f"{httpbin_url}/status/404")
        assert r200.ok is True
        assert r404.ok is False


# ── Sync: Client session ──


class TestSyncClient:
    def test_client_get(self, httpbin_url):
        with Client() as c:
            r = c.get(f"{httpbin_url}/get")
            assert r.status_code == 200

    def test_client_base_headers(self, httpbin_url):
        with Client(headers={"X-Session": "abc"}) as c:
            r = c.get(f"{httpbin_url}/get")
            assert r.json()["headers"]["X-Session"] == "abc"  # type: ignore

    def test_client_post_json(self, httpbin_url):
        with Client() as c:
            r = c.post(f"{httpbin_url}/post", json={"client": True})
            assert r.json()["json"] == {"client": True}  # type: ignore


# ── Async vs httpx ──


class TestAsyncGet:
    @pytest.mark.asyncio
    async def test_simple_get(self, httpbin_url):
        ours = await async_get(f"{httpbin_url}/get")
        async with httpx.AsyncClient() as client:
            theirs = await client.get(f"{httpbin_url}/get")
        assert ours.status_code == theirs.status_code

    @pytest.mark.asyncio
    async def test_get_with_params(self, httpbin_url):
        params = {"async_key": "async_val"}
        ours = await async_get(f"{httpbin_url}/get", params=params)
        assert ours.json()["args"]["async_key"] == "async_val"  # type: ignore

    @pytest.mark.asyncio
    async def test_get_json(self, httpbin_url):
        ours = await async_get(f"{httpbin_url}/json")
        async with httpx.AsyncClient() as client:
            theirs = await client.get(f"{httpbin_url}/json")
        assert ours.json() == theirs.json()  # type: ignore


class TestAsyncMutations:
    @pytest.mark.asyncio
    async def test_post_json(self, httpbin_url):
        payload = {"async": True}
        ours = await async_post(f"{httpbin_url}/post", json=payload)
        assert ours.json()["json"] == payload  # type: ignore

    @pytest.mark.asyncio
    async def test_put_json(self, httpbin_url):
        payload = {"async_put": True}
        ours = await async_put(f"{httpbin_url}/put", json=payload)
        assert ours.json()["json"] == payload  # type: ignore

    @pytest.mark.asyncio
    async def test_patch_json(self, httpbin_url):
        payload = {"async_patch": True}
        ours = await async_patch(f"{httpbin_url}/patch", json=payload)
        assert ours.json()["json"] == payload  # type: ignore

    @pytest.mark.asyncio
    async def test_delete(self, httpbin_url):
        ours = await async_delete(f"{httpbin_url}/delete")
        assert ours.status_code == 200


class TestAsyncRedirects:
    @pytest.mark.asyncio
    async def test_redirect_followed(self, httpbin_url):
        ours = await async_get(f"{httpbin_url}/redirect/2")
        assert ours.status_code == 200


class TestAsyncClient:
    @pytest.mark.asyncio
    async def test_client_get(self, httpbin_url):
        async with AsyncClient() as c:
            r = await c.get(f"{httpbin_url}/get")
            assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_client_base_headers(self, httpbin_url):
        async with AsyncClient(headers={"X-Async": "yes"}) as c:
            r = await c.get(f"{httpbin_url}/get")
            assert r.json()["headers"]["X-Async"] == "yes"  # type: ignore


# ── Sync: file upload ──


class TestSyncFileUpload:
    def test_upload_bytes(self, httpbin_url):
        r = post(f"{httpbin_url}/post", files={"file": b"hello world"})
        assert r.status_code == 200
        assert "file" in r.json()["files"]  # type: ignore

    def test_upload_tuple_with_filename(self, httpbin_url):
        r = post(f"{httpbin_url}/post", files={"file": ("test.txt", b"file content")})
        assert r.status_code == 200
        assert r.json()["files"]["file"] == "file content"  # type: ignore

    def test_upload_tuple_with_content_type(self, httpbin_url):
        r = post(
            f"{httpbin_url}/post",
            files={"file": ("data.json", b'{"key": "value"}', "application/json")},
        )
        assert r.status_code == 200
        assert "file" in r.json()["files"]  # type: ignore

    def test_upload_with_data(self, httpbin_url):
        r = post(
            f"{httpbin_url}/post",
            data={"field": "value"},
            files={"file": ("test.txt", b"content")},
        )
        assert r.status_code == 200
        body = r.json()  # type: ignore
        assert body["form"]["field"] == "value"
        assert "file" in body["files"]

    def test_upload_file_object(self, httpbin_url):
        import io

        buf = io.BytesIO(b"file object content")
        buf.name = "buffer.txt"
        r = post(f"{httpbin_url}/post", files={"file": buf})
        assert r.status_code == 200
        assert r.json()["files"]["file"] == "file object content"  # type: ignore

    def test_upload_multiple_files(self, httpbin_url):
        r = post(
            f"{httpbin_url}/post",
            files=[
                ("file1", ("a.txt", b"aaa")),
                ("file2", ("b.txt", b"bbb")),
            ],
        )
        assert r.status_code == 200
        files = r.json()["files"]  # type: ignore
        assert files["file1"] == "aaa"
        assert files["file2"] == "bbb"


# ── Async: file upload ──


class TestAsyncFileUpload:
    @pytest.mark.asyncio
    async def test_upload_bytes(self, httpbin_url):
        r = await async_post(f"{httpbin_url}/post", files={"file": b"async hello"})
        assert r.status_code == 200
        assert "file" in r.json()["files"]  # type: ignore

    @pytest.mark.asyncio
    async def test_upload_with_data(self, httpbin_url):
        r = await async_post(
            f"{httpbin_url}/post",
            data={"field": "async_value"},
            files={"file": ("test.txt", b"async content")},
        )
        assert r.status_code == 200
        body = r.json()  # type: ignore
        assert body["form"]["field"] == "async_value"
        assert "file" in body["files"]

    @pytest.mark.asyncio
    async def test_upload_tuple_with_content_type(self, httpbin_url):
        r = await async_post(
            f"{httpbin_url}/post",
            files={"file": ("data.txt", b"typed content", "text/plain")},
        )
        assert r.status_code == 200
        assert r.json()["files"]["file"] == "typed content"  # type: ignore


# ── Sync: streaming ──


class TestSyncStreaming:
    def test_stream_iter_bytes(self, httpbin_url):
        with get(f"{httpbin_url}/get", stream=True) as r:
            assert isinstance(r, StreamingResponse)
            assert r.status_code == 200
            assert r.ok
            chunks = list(r.iter_bytes())
            assert len(chunks) > 0
            body = b"".join(chunks)
            assert b"headers" in body

    def test_stream_iter_lines(self, httpbin_url):
        with get(f"{httpbin_url}/get", stream=True) as r:
            lines = list(r.iter_lines())  # type: ignore
            assert len(lines) > 0
            # /get returns JSON, should have lines
            text = "\n".join(lines)
            assert "headers" in text

    def test_stream_read(self, httpbin_url):
        with get(f"{httpbin_url}/get", stream=True) as r:
            body = r.read()  # type: ignore
            assert isinstance(body, bytes)
            assert b"headers" in body

    def test_stream_headers_accessible(self, httpbin_url):
        with get(f"{httpbin_url}/get", stream=True) as r:
            assert "content-type" in r.headers
            assert r.url.endswith("/get")

    def test_stream_raise_for_status(self, httpbin_url):
        with get(f"{httpbin_url}/status/404", stream=True) as r:
            assert r.status_code == 404
            assert not r.ok
            with pytest.raises(HTTPError):
                r.raise_for_status()

    def test_stream_redirect(self, httpbin_url):
        with get(f"{httpbin_url}/redirect/2", stream=True) as r:
            assert r.status_code == 200
            body = r.read()  # type: ignore
            assert len(body) > 0

    def test_stream_client_session(self, httpbin_url):
        with Client() as client:
            with client.get(f"{httpbin_url}/get", stream=True) as r:
                assert r.status_code == 200
                body = r.read()  # type: ignore
                assert b"headers" in body


# ── Async: streaming ──


class TestAsyncStreaming:
    @pytest.mark.asyncio
    async def test_stream_aiter_bytes(self, httpbin_url):
        r = await async_get(f"{httpbin_url}/get", stream=True)
        async with r:
            assert isinstance(r, StreamingResponse)
            assert r.status_code == 200
            chunks = []
            async for chunk in r.aiter_bytes():
                chunks.append(chunk)
            assert len(chunks) > 0
            body = b"".join(chunks)
            assert b"headers" in body

    @pytest.mark.asyncio
    async def test_stream_aiter_lines(self, httpbin_url):
        r = await async_get(f"{httpbin_url}/get", stream=True)
        async with r:
            lines = []
            async for line in r.aiter_lines():  # type: ignore
                lines.append(line)
            assert len(lines) > 0
            text = "\n".join(lines)
            assert "headers" in text

    @pytest.mark.asyncio
    async def test_stream_aread(self, httpbin_url):
        r = await async_get(f"{httpbin_url}/get", stream=True)
        async with r:
            body = await r.aread()  # type: ignore
            assert isinstance(body, bytes)
            assert b"headers" in body

    @pytest.mark.asyncio
    async def test_stream_redirect(self, httpbin_url):
        r = await async_get(f"{httpbin_url}/redirect/2", stream=True)
        async with r:
            assert r.status_code == 200
            body = await r.aread()  # type: ignore
            assert len(body) > 0

    @pytest.mark.asyncio
    async def test_stream_client_session(self, httpbin_url):
        async with AsyncClient() as client:
            r = await client.get(f"{httpbin_url}/get", stream=True)
            async with r:
                assert r.status_code == 200
                body = await r.aread()  # type: ignore
                assert b"headers" in body


# ── Response object ──


class TestResponse:
    def test_repr(self, httpbin_url):
        r = get(f"{httpbin_url}/get")
        assert "200" in repr(r)

    def test_content_is_bytes(self, httpbin_url):
        r = get(f"{httpbin_url}/get")
        assert isinstance(r.content, bytes)  # type: ignore

    def test_text_is_str(self, httpbin_url):
        r = get(f"{httpbin_url}/get")
        assert isinstance(r.text, str)  # type: ignore


# ── Sync: decompression ──


class TestSyncDecompression:
    def test_gzip(self, httpbin_url):
        r = get(f"{httpbin_url}/gzip")
        assert r.status_code == 200
        assert r.json()["gzipped"] is True  # type: ignore

    def test_deflate(self, httpbin_url):
        r = get(f"{httpbin_url}/deflate")
        assert r.status_code == 200
        assert r.json()["deflated"] is True  # type: ignore

    def test_gzip_vs_httpx(self, httpbin_url):
        ours = get(f"{httpbin_url}/gzip")
        theirs = httpx.get(f"{httpbin_url}/gzip")
        assert ours.json() == theirs.json()  # type: ignore

    def test_identity_no_decompression(self, httpbin_url):
        """User can opt out by setting Accept-Encoding: identity."""
        r = get(f"{httpbin_url}/get", headers={"Accept-Encoding": "identity"})
        assert r.status_code == 200
        # Server should not compress when identity is requested

    def test_gzip_streaming(self, httpbin_url):
        with get(f"{httpbin_url}/gzip-stream", stream=True) as r:
            assert r.status_code == 200
            body = r.read()
        import json as _json

        data = _json.loads(body)
        assert data["gzipped"] is True


# ── Async: decompression ──


class TestAsyncDecompression:
    @pytest.mark.asyncio
    async def test_gzip(self, httpbin_url):
        r = await async_get(f"{httpbin_url}/gzip")
        assert r.status_code == 200
        assert r.json()["gzipped"] is True  # type: ignore

    @pytest.mark.asyncio
    async def test_deflate(self, httpbin_url):
        r = await async_get(f"{httpbin_url}/deflate")
        assert r.status_code == 200
        assert r.json()["deflated"] is True  # type: ignore

    @pytest.mark.asyncio
    async def test_gzip_streaming(self, httpbin_url):
        r = await async_get(f"{httpbin_url}/gzip-stream", stream=True)
        async with r:
            body = await r.aread()
        import json as _json

        data = _json.loads(body)
        assert data["gzipped"] is True


# ── Sync: basic auth ──


class TestSyncBasicAuth:
    def test_basic_auth_tuple(self, httpbin_url):
        r = get(f"{httpbin_url}/basic-auth/user/pass", auth=("user", "pass"))
        assert r.status_code == 200
        assert r.json()["authenticated"] is True  # type: ignore

    def test_basic_auth_object(self, httpbin_url):
        r = get(f"{httpbin_url}/basic-auth/user/pass", auth=BasicAuth("user", "pass"))
        assert r.status_code == 200
        assert r.json()["authenticated"] is True  # type: ignore

    def test_basic_auth_wrong_credentials(self, httpbin_url):
        r = get(f"{httpbin_url}/basic-auth/user/pass", auth=("wrong", "creds"))
        assert r.status_code == 401

    def test_basic_auth_client_session(self, httpbin_url):
        with Client(auth=("user", "pass")) as c:
            r = c.get(f"{httpbin_url}/basic-auth/user/pass")
            assert r.status_code == 200
            assert r.json()["authenticated"] is True  # type: ignore


# ── Async: basic auth ──


class TestAsyncBasicAuth:
    @pytest.mark.asyncio
    async def test_basic_auth_tuple(self, httpbin_url):
        r = await async_get(
            f"{httpbin_url}/basic-auth/user/pass", auth=("user", "pass")
        )
        assert r.status_code == 200
        assert r.json()["authenticated"] is True  # type: ignore

    @pytest.mark.asyncio
    async def test_basic_auth_object(self, httpbin_url):
        r = await async_get(
            f"{httpbin_url}/basic-auth/user/pass", auth=BasicAuth("user", "pass")
        )
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_basic_auth_client_session(self, httpbin_url):
        async with AsyncClient(auth=("user", "pass")) as c:
            r = await c.get(f"{httpbin_url}/basic-auth/user/pass")
            assert r.status_code == 200


# ── Sync: digest auth ──


class TestSyncDigestAuth:
    def test_digest_auth_success(self, httpbin_url):
        r = get(
            f"{httpbin_url}/digest-auth/auth/user/pass",
            auth=DigestAuth("user", "pass"),
        )
        assert r.status_code == 200
        assert r.json()["authenticated"] is True  # type: ignore

    def test_digest_auth_wrong_credentials(self, httpbin_url):
        r = get(
            f"{httpbin_url}/digest-auth/auth/user/pass",
            auth=DigestAuth("wrong", "creds"),
        )
        assert r.status_code == 401

    def test_digest_auth_client_session(self, httpbin_url):
        with Client(auth=DigestAuth("user", "pass")) as c:
            r = c.get(f"{httpbin_url}/digest-auth/auth/user/pass")
            assert r.status_code == 200
            assert r.json()["user"] == "user"  # type: ignore


# ── Async: digest auth ──


class TestAsyncDigestAuth:
    @pytest.mark.asyncio
    async def test_digest_auth_success(self, httpbin_url):
        r = await async_get(
            f"{httpbin_url}/digest-auth/auth/user/pass",
            auth=DigestAuth("user", "pass"),
        )
        assert r.status_code == 200
        assert r.json()["authenticated"] is True  # type: ignore

    @pytest.mark.asyncio
    async def test_digest_auth_wrong_credentials(self, httpbin_url):
        r = await async_get(
            f"{httpbin_url}/digest-auth/auth/user/pass",
            auth=DigestAuth("wrong", "creds"),
        )
        assert r.status_code == 401


# ── Sync: connection pool ──


class TestSyncConnectionPool:
    def test_pool_basic_reuse(self, httpbin_url):
        with Client() as c:
            for _ in range(5):
                r = c.get(f"{httpbin_url}/get")
                assert r.status_code == 200

    def test_pool_different_paths(self, httpbin_url):
        with Client() as c:
            r1 = c.get(f"{httpbin_url}/get")
            r2 = c.get(f"{httpbin_url}/json")
            assert r1.status_code == 200
            assert r2.status_code == 200

    def test_pool_client_close(self, httpbin_url):
        c = Client()
        c.get(f"{httpbin_url}/get")
        c.close()
        assert len(c._pool._pool) == 0

    def test_pool_size_limit(self, httpbin_url):
        with Client(pool_size=1) as c:
            for _ in range(3):
                r = c.get(f"{httpbin_url}/get")
                assert r.status_code == 200

    def test_pool_vs_no_pool(self, httpbin_url):
        """Stateless functions should still work without pooling."""
        r1 = get(f"{httpbin_url}/get")
        with Client() as c:
            r2 = c.get(f"{httpbin_url}/get")
        assert r1.json()["url"] == r2.json()["url"]  # type: ignore


# ── Async: connection pool ──


class TestAsyncConnectionPool:
    @pytest.mark.asyncio
    async def test_pool_single_request(self, httpbin_url):
        async with AsyncClient() as c:
            r = await c.get(f"{httpbin_url}/get")
            assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_pool_different_hosts(self, httpbin_url):
        """Each request to the same host creates a fresh connection."""
        async with AsyncClient() as c:
            r = await c.get(f"{httpbin_url}/json")
            assert r.status_code == 200
            assert "slideshow" in r.json()  # type: ignore

    @pytest.mark.asyncio
    async def test_pool_client_close(self, httpbin_url):
        c = AsyncClient()
        await c.request("GET", f"{httpbin_url}/get")
        await c.aclose()
        assert len(c._pool._pool) == 0


# ── Sync: proxy ──


class TestSyncProxy:
    def test_http_through_proxy(self, httpbin_url, proxy_url):
        r = get(f"{httpbin_url}/get", proxy=proxy_url)
        assert r.status_code == 200
        assert "url" in r.json()  # type: ignore

    def test_proxy_client_session(self, httpbin_url, proxy_url):
        with Client(proxy=proxy_url) as c:
            r = c.get(f"{httpbin_url}/get")
            assert r.status_code == 200

    def test_proxy_post(self, httpbin_url, proxy_url):
        r = post(f"{httpbin_url}/post", json={"key": "val"}, proxy=proxy_url)
        assert r.status_code == 200
        assert r.json()["json"] == {"key": "val"}  # type: ignore


# ── Async: proxy ──


class TestAsyncProxy:
    @pytest.mark.asyncio
    async def test_http_through_proxy(self, httpbin_url, proxy_url):
        r = await async_get(f"{httpbin_url}/get", proxy=proxy_url)
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_proxy_post(self, httpbin_url, proxy_url):
        r = await async_post(
            f"{httpbin_url}/post", json={"key": "val"}, proxy=proxy_url
        )
        assert r.status_code == 200
        assert r.json()["json"] == {"key": "val"}  # type: ignore


# ── Sync: SOCKS5 proxy ──


class TestSyncSocks5:
    def test_http_through_socks5(self, httpbin_url, socks5_url):
        r = get(f"{httpbin_url}/get", proxy=socks5_url)
        assert r.status_code == 200
        assert "url" in r.json()

    def test_http_through_socks5_auth(self, httpbin_url, socks5_auth_url):
        r = get(f"{httpbin_url}/get", proxy=socks5_auth_url)
        assert r.status_code == 200

    def test_socks5_post(self, httpbin_url, socks5_url):
        r = post(f"{httpbin_url}/post", json={"key": "val"}, proxy=socks5_url)
        assert r.status_code == 200
        assert r.json()["json"] == {"key": "val"}

    def test_socks5_client_session(self, httpbin_url, socks5_url):
        with Client(proxy=socks5_url) as c:
            r = c.get(f"{httpbin_url}/get")
            assert r.status_code == 200

    def test_socks5_streaming(self, httpbin_url, socks5_url):
        r = get(f"{httpbin_url}/stream-bytes/1024", proxy=socks5_url, stream=True)
        assert r.status_code == 200
        data = b"".join(r.iter_bytes())
        assert len(data) == 1024

    def test_socks5_auth_required_but_missing(self, httpbin_url, socks5_auth_url):
        # Strip credentials from URL
        no_auth_url = socks5_auth_url.split("@")[-1]
        no_auth_url = f"socks5://{no_auth_url}"
        with pytest.raises((Socks5Error, HttpConnectionError)):
            get(f"{httpbin_url}/get", proxy=no_auth_url)

    def test_socks5_wrong_credentials(self, httpbin_url, socks5_auth_url):
        parts = socks5_auth_url.split("@")
        wrong_url = f"socks5://wrong:creds@{parts[-1]}"
        with pytest.raises((Socks5Error, HttpConnectionError)):
            get(f"{httpbin_url}/get", proxy=wrong_url)


# ── Async: SOCKS5 proxy ──


class TestAsyncSocks5:
    @pytest.mark.asyncio
    async def test_http_through_socks5(self, httpbin_url, socks5_url):
        r = await async_get(f"{httpbin_url}/get", proxy=socks5_url)
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_http_through_socks5_auth(self, httpbin_url, socks5_auth_url):
        r = await async_get(f"{httpbin_url}/get", proxy=socks5_auth_url)
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_socks5_post(self, httpbin_url, socks5_url):
        r = await async_post(
            f"{httpbin_url}/post", json={"key": "val"}, proxy=socks5_url
        )
        assert r.status_code == 200
        assert r.json()["json"] == {"key": "val"}

    @pytest.mark.asyncio
    async def test_socks5_streaming(self, httpbin_url, socks5_url):
        r = await async_get(
            f"{httpbin_url}/stream-bytes/1024", proxy=socks5_url, stream=True
        )
        assert r.status_code == 200
        data = b""
        async for chunk in r.aiter_bytes():
            data += chunk
        assert len(data) == 1024

    @pytest.mark.asyncio
    async def test_socks5_client_session(self, httpbin_url, socks5_url):
        async with AsyncClient(proxy=socks5_url) as c:
            r = await c.get(f"{httpbin_url}/get")
            assert r.status_code == 200


# ── Concurrency ──


class TestAsyncConcurrency:
    @pytest.mark.asyncio
    async def test_concurrent_requests_not_serialized(self, httpbin_url):
        """Multiple async requests via the same client run concurrently."""
        async with AsyncClient() as c:
            start = time.monotonic()
            results = await asyncio.gather(
                *[c.get(f"{httpbin_url}/delay/0.3") for _ in range(5)]
            )
            elapsed = time.monotonic() - start

        assert all(r.status_code == 200 for r in results)
        # Concurrent: ~0.3s.  Serialized (old behavior): >= 1.5s.
        assert elapsed < 1.0, f"Requests appear serialized: {elapsed:.2f}s"

    @pytest.mark.asyncio
    async def test_no_deadlock_on_concurrent_use(self, httpbin_url):
        """Concurrent requests must not deadlock (regression for #76)."""
        async with AsyncClient() as c:
            results = await asyncio.wait_for(
                asyncio.gather(
                    c.get(f"{httpbin_url}/get"),
                    c.get(f"{httpbin_url}/json"),
                    c.get(f"{httpbin_url}/get"),
                ),
                timeout=5.0,
            )
        assert all(r.status_code == 200 for r in results)


class TestSyncConcurrency:
    def test_concurrent_requests_from_threads(self, httpbin_url):
        """Sync Client handles concurrent requests from multiple threads."""
        client = Client()
        errors = []

        def do_request(i):
            try:
                r = client.get(f"{httpbin_url}/get")
                assert r.status_code == 200
            except Exception as exc:
                errors.append((i, exc))

        with ThreadPoolExecutor(max_workers=5) as pool:
            list(pool.map(do_request, range(10)))

        client.close()
        assert not errors, f"Thread errors: {errors}"
