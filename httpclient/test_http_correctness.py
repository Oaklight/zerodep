"""Correctness tests: zerodep HTTP client vs httpx."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from httpclient import (
    AsyncClient,
    Client,
    HTTPError,
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
        assert ours.json()["args"] == theirs.json()["args"]

    def test_get_with_headers(self, httpbin_url):
        hdrs = {"X-Custom": "test123"}
        ours = get(f"{httpbin_url}/get", headers=hdrs)
        theirs = httpx.get(f"{httpbin_url}/get", headers=hdrs)
        assert ours.json()["headers"]["X-Custom"] == "test123"
        assert theirs.json()["headers"]["X-Custom"] == "test123"

    def test_get_json_response(self, httpbin_url):
        ours = get(f"{httpbin_url}/json")
        theirs = httpx.get(f"{httpbin_url}/json")
        assert ours.json() == theirs.json()

    def test_response_text(self, httpbin_url):
        ours = get(f"{httpbin_url}/html")
        assert "<html>" in ours.text.lower() or "<h1>" in ours.text.lower()


# ── Sync vs httpx: POST/PUT/PATCH/DELETE ──


class TestSyncMutations:
    def test_post_json(self, httpbin_url):
        payload = {"name": "zerodep", "version": 1}
        ours = post(f"{httpbin_url}/post", json=payload)
        theirs = httpx.post(f"{httpbin_url}/post", json=payload)
        assert ours.json()["json"] == payload
        assert theirs.json()["json"] == payload

    def test_post_data(self, httpbin_url):
        ours = post(f"{httpbin_url}/post", data="field=value")
        assert ours.status_code == 200
        assert ours.json()["form"]["field"] == "value"

    def test_put_json(self, httpbin_url):
        payload = {"updated": True}
        ours = put(f"{httpbin_url}/put", json=payload)
        theirs = httpx.put(f"{httpbin_url}/put", json=payload)
        assert ours.json()["json"] == payload
        assert theirs.json()["json"] == payload

    def test_patch_json(self, httpbin_url):
        payload = {"patched": True}
        ours = patch(f"{httpbin_url}/patch", json=payload)
        theirs = httpx.patch(f"{httpbin_url}/patch", json=payload)
        assert ours.json()["json"] == payload
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
            assert r.json()["headers"]["X-Session"] == "abc"

    def test_client_post_json(self, httpbin_url):
        with Client() as c:
            r = c.post(f"{httpbin_url}/post", json={"client": True})
            assert r.json()["json"] == {"client": True}


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
        assert ours.json()["args"]["async_key"] == "async_val"

    @pytest.mark.asyncio
    async def test_get_json(self, httpbin_url):
        ours = await async_get(f"{httpbin_url}/json")
        async with httpx.AsyncClient() as client:
            theirs = await client.get(f"{httpbin_url}/json")
        assert ours.json() == theirs.json()


class TestAsyncMutations:
    @pytest.mark.asyncio
    async def test_post_json(self, httpbin_url):
        payload = {"async": True}
        ours = await async_post(f"{httpbin_url}/post", json=payload)
        assert ours.json()["json"] == payload

    @pytest.mark.asyncio
    async def test_put_json(self, httpbin_url):
        payload = {"async_put": True}
        ours = await async_put(f"{httpbin_url}/put", json=payload)
        assert ours.json()["json"] == payload

    @pytest.mark.asyncio
    async def test_patch_json(self, httpbin_url):
        payload = {"async_patch": True}
        ours = await async_patch(f"{httpbin_url}/patch", json=payload)
        assert ours.json()["json"] == payload

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
            assert r.json()["headers"]["X-Async"] == "yes"


# ── Sync: file upload ──


class TestSyncFileUpload:
    def test_upload_bytes(self, httpbin_url):
        r = post(f"{httpbin_url}/post", files={"file": b"hello world"})
        assert r.status_code == 200
        assert "file" in r.json()["files"]

    def test_upload_tuple_with_filename(self, httpbin_url):
        r = post(f"{httpbin_url}/post", files={"file": ("test.txt", b"file content")})
        assert r.status_code == 200
        assert r.json()["files"]["file"] == "file content"

    def test_upload_tuple_with_content_type(self, httpbin_url):
        r = post(
            f"{httpbin_url}/post",
            files={"file": ("data.json", b'{"key": "value"}', "application/json")},
        )
        assert r.status_code == 200
        assert "file" in r.json()["files"]

    def test_upload_with_data(self, httpbin_url):
        r = post(
            f"{httpbin_url}/post",
            data={"field": "value"},
            files={"file": ("test.txt", b"content")},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["form"]["field"] == "value"
        assert "file" in body["files"]

    def test_upload_file_object(self, httpbin_url):
        import io

        buf = io.BytesIO(b"file object content")
        buf.name = "buffer.txt"
        r = post(f"{httpbin_url}/post", files={"file": buf})
        assert r.status_code == 200
        assert r.json()["files"]["file"] == "file object content"

    def test_upload_multiple_files(self, httpbin_url):
        r = post(
            f"{httpbin_url}/post",
            files=[
                ("file1", ("a.txt", b"aaa")),
                ("file2", ("b.txt", b"bbb")),
            ],
        )
        assert r.status_code == 200
        files = r.json()["files"]
        assert files["file1"] == "aaa"
        assert files["file2"] == "bbb"


# ── Async: file upload ──


class TestAsyncFileUpload:
    @pytest.mark.asyncio
    async def test_upload_bytes(self, httpbin_url):
        r = await async_post(f"{httpbin_url}/post", files={"file": b"async hello"})
        assert r.status_code == 200
        assert "file" in r.json()["files"]

    @pytest.mark.asyncio
    async def test_upload_with_data(self, httpbin_url):
        r = await async_post(
            f"{httpbin_url}/post",
            data={"field": "async_value"},
            files={"file": ("test.txt", b"async content")},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["form"]["field"] == "async_value"
        assert "file" in body["files"]

    @pytest.mark.asyncio
    async def test_upload_tuple_with_content_type(self, httpbin_url):
        r = await async_post(
            f"{httpbin_url}/post",
            files={"file": ("data.txt", b"typed content", "text/plain")},
        )
        assert r.status_code == 200
        assert r.json()["files"]["file"] == "typed content"


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
            lines = list(r.iter_lines())
            assert len(lines) > 0
            # /get returns JSON, should have lines
            text = "\n".join(lines)
            assert "headers" in text

    def test_stream_read(self, httpbin_url):
        with get(f"{httpbin_url}/get", stream=True) as r:
            body = r.read()
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
            body = r.read()
            assert len(body) > 0

    def test_stream_client_session(self, httpbin_url):
        with Client() as client:
            with client.get(f"{httpbin_url}/get", stream=True) as r:
                assert r.status_code == 200
                body = r.read()
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
            async for line in r.aiter_lines():
                lines.append(line)
            assert len(lines) > 0
            text = "\n".join(lines)
            assert "headers" in text

    @pytest.mark.asyncio
    async def test_stream_aread(self, httpbin_url):
        r = await async_get(f"{httpbin_url}/get", stream=True)
        async with r:
            body = await r.aread()
            assert isinstance(body, bytes)
            assert b"headers" in body

    @pytest.mark.asyncio
    async def test_stream_redirect(self, httpbin_url):
        r = await async_get(f"{httpbin_url}/redirect/2", stream=True)
        async with r:
            assert r.status_code == 200
            body = await r.aread()
            assert len(body) > 0

    @pytest.mark.asyncio
    async def test_stream_client_session(self, httpbin_url):
        async with AsyncClient() as client:
            r = await client.get(f"{httpbin_url}/get", stream=True)
            async with r:
                assert r.status_code == 200
                body = await r.aread()
                assert b"headers" in body


# ── Response object ──


class TestResponse:
    def test_repr(self, httpbin_url):
        r = get(f"{httpbin_url}/get")
        assert "200" in repr(r)

    def test_content_is_bytes(self, httpbin_url):
        r = get(f"{httpbin_url}/get")
        assert isinstance(r.content, bytes)

    def test_text_is_str(self, httpbin_url):
        r = get(f"{httpbin_url}/get")
        assert isinstance(r.text, str)
