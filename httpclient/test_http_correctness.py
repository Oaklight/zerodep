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

BASE = "https://httpbin.org"


# ── Sync vs httpx: GET ──


class TestSyncGet:
    def test_simple_get(self):
        ours = get(f"{BASE}/get")
        theirs = httpx.get(f"{BASE}/get")
        assert ours.status_code == theirs.status_code

    def test_get_with_params(self):
        params = {"key": "value", "num": "42"}
        ours = get(f"{BASE}/get", params=params)
        theirs = httpx.get(f"{BASE}/get", params=params)
        assert ours.json()["args"] == theirs.json()["args"]

    def test_get_with_headers(self):
        hdrs = {"X-Custom": "test123"}
        ours = get(f"{BASE}/get", headers=hdrs)
        theirs = httpx.get(f"{BASE}/get", headers=hdrs)
        assert ours.json()["headers"]["X-Custom"] == "test123"
        assert theirs.json()["headers"]["X-Custom"] == "test123"

    def test_get_json_response(self):
        ours = get(f"{BASE}/json")
        theirs = httpx.get(f"{BASE}/json")
        assert ours.json() == theirs.json()

    def test_response_text(self):
        ours = get(f"{BASE}/html")
        assert "<html>" in ours.text.lower() or "<h1>" in ours.text.lower()


# ── Sync vs httpx: POST/PUT/PATCH/DELETE ──


class TestSyncMutations:
    def test_post_json(self):
        payload = {"name": "zerodep", "version": 1}
        ours = post(f"{BASE}/post", json=payload)
        theirs = httpx.post(f"{BASE}/post", json=payload)
        assert ours.json()["json"] == payload
        assert theirs.json()["json"] == payload

    def test_post_data(self):
        ours = post(f"{BASE}/post", data="field=value")
        assert ours.status_code == 200
        assert ours.json()["form"]["field"] == "value"

    def test_put_json(self):
        payload = {"updated": True}
        ours = put(f"{BASE}/put", json=payload)
        theirs = httpx.put(f"{BASE}/put", json=payload)
        assert ours.json()["json"] == payload
        assert theirs.json()["json"] == payload

    def test_patch_json(self):
        payload = {"patched": True}
        ours = patch(f"{BASE}/patch", json=payload)
        theirs = httpx.patch(f"{BASE}/patch", json=payload)
        assert ours.json()["json"] == payload
        assert theirs.json()["json"] == payload

    def test_delete(self):
        ours = delete(f"{BASE}/delete")
        theirs = httpx.delete(f"{BASE}/delete")
        assert ours.status_code == theirs.status_code


# ── Sync: redirects ──


class TestSyncRedirects:
    def test_redirect_followed(self):
        ours = get(f"{BASE}/redirect/3")
        assert ours.status_code == 200

    def test_absolute_redirect(self):
        ours = get(f"{BASE}/absolute-redirect/1")
        assert ours.status_code == 200


# ── Sync: status codes ──


class TestSyncStatusCodes:
    @pytest.mark.parametrize("code", [200, 201, 204, 400, 401, 403, 404, 500])
    def test_status_code(self, code: int):
        ours = get(f"{BASE}/status/{code}")
        assert ours.status_code == code

    def test_raise_for_status(self):
        r = get(f"{BASE}/status/404")
        with pytest.raises(HTTPError):
            r.raise_for_status()

    def test_ok_property(self):
        r200 = get(f"{BASE}/status/200")
        r404 = get(f"{BASE}/status/404")
        assert r200.ok is True
        assert r404.ok is False


# ── Sync: Client session ──


class TestSyncClient:
    def test_client_get(self):
        with Client() as c:
            r = c.get(f"{BASE}/get")
            assert r.status_code == 200

    def test_client_base_headers(self):
        with Client(headers={"X-Session": "abc"}) as c:
            r = c.get(f"{BASE}/get")
            assert r.json()["headers"]["X-Session"] == "abc"

    def test_client_post_json(self):
        with Client() as c:
            r = c.post(f"{BASE}/post", json={"client": True})
            assert r.json()["json"] == {"client": True}


# ── Async vs httpx ──


class TestAsyncGet:
    @pytest.mark.asyncio
    async def test_simple_get(self):
        ours = await async_get(f"{BASE}/get")
        async with httpx.AsyncClient() as client:
            theirs = await client.get(f"{BASE}/get")
        assert ours.status_code == theirs.status_code

    @pytest.mark.asyncio
    async def test_get_with_params(self):
        params = {"async_key": "async_val"}
        ours = await async_get(f"{BASE}/get", params=params)
        assert ours.json()["args"]["async_key"] == "async_val"

    @pytest.mark.asyncio
    async def test_get_json(self):
        ours = await async_get(f"{BASE}/json")
        async with httpx.AsyncClient() as client:
            theirs = await client.get(f"{BASE}/json")
        assert ours.json() == theirs.json()


class TestAsyncMutations:
    @pytest.mark.asyncio
    async def test_post_json(self):
        payload = {"async": True}
        ours = await async_post(f"{BASE}/post", json=payload)
        assert ours.json()["json"] == payload

    @pytest.mark.asyncio
    async def test_put_json(self):
        payload = {"async_put": True}
        ours = await async_put(f"{BASE}/put", json=payload)
        assert ours.json()["json"] == payload

    @pytest.mark.asyncio
    async def test_patch_json(self):
        payload = {"async_patch": True}
        ours = await async_patch(f"{BASE}/patch", json=payload)
        assert ours.json()["json"] == payload

    @pytest.mark.asyncio
    async def test_delete(self):
        ours = await async_delete(f"{BASE}/delete")
        assert ours.status_code == 200


class TestAsyncRedirects:
    @pytest.mark.asyncio
    async def test_redirect_followed(self):
        ours = await async_get(f"{BASE}/redirect/2")
        assert ours.status_code == 200


class TestAsyncClient:
    @pytest.mark.asyncio
    async def test_client_get(self):
        async with AsyncClient() as c:
            r = await c.get(f"{BASE}/get")
            assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_client_base_headers(self):
        async with AsyncClient(headers={"X-Async": "yes"}) as c:
            r = await c.get(f"{BASE}/get")
            assert r.json()["headers"]["X-Async"] == "yes"


# ── Sync: file upload ──


class TestSyncFileUpload:
    def test_upload_bytes(self):
        r = post(f"{BASE}/post", files={"file": b"hello world"})
        assert r.status_code == 200
        assert "file" in r.json()["files"]

    def test_upload_tuple_with_filename(self):
        r = post(f"{BASE}/post", files={"file": ("test.txt", b"file content")})
        assert r.status_code == 200
        assert r.json()["files"]["file"] == "file content"

    def test_upload_tuple_with_content_type(self):
        r = post(
            f"{BASE}/post",
            files={"file": ("data.json", b'{"key": "value"}', "application/json")},
        )
        assert r.status_code == 200
        assert "file" in r.json()["files"]

    def test_upload_with_data(self):
        r = post(
            f"{BASE}/post",
            data={"field": "value"},
            files={"file": ("test.txt", b"content")},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["form"]["field"] == "value"
        assert "file" in body["files"]

    def test_upload_file_object(self):
        import io

        buf = io.BytesIO(b"file object content")
        buf.name = "buffer.txt"
        r = post(f"{BASE}/post", files={"file": buf})
        assert r.status_code == 200
        assert r.json()["files"]["file"] == "file object content"

    def test_upload_multiple_files(self):
        r = post(
            f"{BASE}/post",
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
    async def test_upload_bytes(self):
        r = await async_post(f"{BASE}/post", files={"file": b"async hello"})
        assert r.status_code == 200
        assert "file" in r.json()["files"]

    @pytest.mark.asyncio
    async def test_upload_with_data(self):
        r = await async_post(
            f"{BASE}/post",
            data={"field": "async_value"},
            files={"file": ("test.txt", b"async content")},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["form"]["field"] == "async_value"
        assert "file" in body["files"]

    @pytest.mark.asyncio
    async def test_upload_tuple_with_content_type(self):
        r = await async_post(
            f"{BASE}/post",
            files={"file": ("data.txt", b"typed content", "text/plain")},
        )
        assert r.status_code == 200
        assert r.json()["files"]["file"] == "typed content"


# ── Sync: streaming ──


class TestSyncStreaming:
    def test_stream_iter_bytes(self):
        with get(f"{BASE}/get", stream=True) as r:
            assert isinstance(r, StreamingResponse)
            assert r.status_code == 200
            assert r.ok
            chunks = list(r.iter_bytes())
            assert len(chunks) > 0
            body = b"".join(chunks)
            assert b"headers" in body

    def test_stream_iter_lines(self):
        with get(f"{BASE}/get", stream=True) as r:
            lines = list(r.iter_lines())
            assert len(lines) > 0
            # httpbin /get returns JSON, should have lines
            text = "\n".join(lines)
            assert "headers" in text

    def test_stream_read(self):
        with get(f"{BASE}/get", stream=True) as r:
            body = r.read()
            assert isinstance(body, bytes)
            assert b"headers" in body

    def test_stream_headers_accessible(self):
        with get(f"{BASE}/get", stream=True) as r:
            assert "content-type" in r.headers
            assert r.url.endswith("/get")

    def test_stream_raise_for_status(self):
        with get(f"{BASE}/status/404", stream=True) as r:
            assert r.status_code == 404
            assert not r.ok
            with pytest.raises(HTTPError):
                r.raise_for_status()

    def test_stream_redirect(self):
        with get(f"{BASE}/redirect/2", stream=True) as r:
            assert r.status_code == 200
            body = r.read()
            assert len(body) > 0

    def test_stream_client_session(self):
        with Client() as client:
            with client.get(f"{BASE}/get", stream=True) as r:
                assert r.status_code == 200
                body = r.read()
                assert b"headers" in body


# ── Async: streaming ──


class TestAsyncStreaming:
    @pytest.mark.asyncio
    async def test_stream_aiter_bytes(self):
        r = await async_get(f"{BASE}/get", stream=True)
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
    async def test_stream_aiter_lines(self):
        r = await async_get(f"{BASE}/get", stream=True)
        async with r:
            lines = []
            async for line in r.aiter_lines():
                lines.append(line)
            assert len(lines) > 0
            text = "\n".join(lines)
            assert "headers" in text

    @pytest.mark.asyncio
    async def test_stream_aread(self):
        r = await async_get(f"{BASE}/get", stream=True)
        async with r:
            body = await r.aread()
            assert isinstance(body, bytes)
            assert b"headers" in body

    @pytest.mark.asyncio
    async def test_stream_redirect(self):
        r = await async_get(f"{BASE}/redirect/2", stream=True)
        async with r:
            assert r.status_code == 200
            body = await r.aread()
            assert len(body) > 0

    @pytest.mark.asyncio
    async def test_stream_client_session(self):
        async with AsyncClient() as client:
            r = await client.get(f"{BASE}/get", stream=True)
            async with r:
                assert r.status_code == 200
                body = await r.aread()
                assert b"headers" in body


# ── Response object ──


class TestResponse:
    def test_repr(self):
        r = get(f"{BASE}/get")
        assert "200" in repr(r)

    def test_content_is_bytes(self):
        r = get(f"{BASE}/get")
        assert isinstance(r.content, bytes)

    def test_text_is_str(self):
        r = get(f"{BASE}/get")
        assert isinstance(r.text, str)
