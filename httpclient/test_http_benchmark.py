"""Benchmark: zerodep HTTP client vs httpx."""

import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from httpclient import Client, get, post
from httpclient import async_get as zd_async_get
from httpclient import async_post as zd_async_post

httpx = pytest.importorskip("httpx", reason="httpx not installed")

BASE = "https://httpbin.org"


# ── Sync GET ──


class TestSyncGet:
    def test_zerodep(self, benchmark):
        benchmark(get, f"{BASE}/get")

    def test_httpx(self, benchmark):
        benchmark(httpx.get, f"{BASE}/get")


# ── Sync POST JSON ──

PAYLOAD = {"key": "value", "nested": {"a": 1, "b": [1, 2, 3]}}


class TestSyncPostJSON:
    def test_zerodep(self, benchmark):
        benchmark(post, f"{BASE}/post", json=PAYLOAD)

    def test_httpx(self, benchmark):
        benchmark(httpx.post, f"{BASE}/post", json=PAYLOAD)


# ── Sync Client session ──


class TestSyncClientGet:
    def test_zerodep(self, benchmark):
        with Client() as c:
            benchmark(c.get, f"{BASE}/get")

    def test_httpx(self, benchmark):
        with httpx.Client() as c:
            benchmark(c.get, f"{BASE}/get")


# ── Async GET ──


def _run_async(coro_fn, *args, **kwargs):
    return asyncio.run(coro_fn(*args, **kwargs))


class TestAsyncGet:
    def test_zerodep(self, benchmark):
        benchmark(_run_async, zd_async_get, f"{BASE}/get")

    def test_httpx(self, benchmark):
        async def _httpx_get():
            async with httpx.AsyncClient() as c:
                return await c.get(f"{BASE}/get")

        benchmark(_run_async, _httpx_get)


# ── Async POST JSON ──


class TestAsyncPostJSON:
    def test_zerodep(self, benchmark):
        benchmark(_run_async, zd_async_post, f"{BASE}/post", json=PAYLOAD)

    def test_httpx(self, benchmark):
        async def _httpx_post():
            async with httpx.AsyncClient() as c:
                return await c.post(f"{BASE}/post", json=PAYLOAD)

        benchmark(_run_async, _httpx_post)


# ── Sync Streaming ──


class TestSyncStreaming:
    def test_zerodep(self, benchmark):
        def _stream():
            with get(f"{BASE}/stream-bytes/4096", stream=True) as r:
                return r.read()

        benchmark(_stream)

    def test_httpx(self, benchmark):
        def _stream():
            with httpx.stream("GET", f"{BASE}/stream-bytes/4096") as r:
                return r.read()

        benchmark(_stream)


# ── Async Streaming ──


class TestAsyncStreaming:
    def test_zerodep(self, benchmark):
        async def _stream():
            r = await zd_async_get(f"{BASE}/stream-bytes/4096", stream=True)
            async with r:
                return await r.aread()

        benchmark(_run_async, _stream)

    def test_httpx(self, benchmark):
        async def _stream():
            async with httpx.AsyncClient() as c:
                async with c.stream("GET", f"{BASE}/stream-bytes/4096") as r:
                    return await r.aread()

        benchmark(_run_async, _stream)


# ── Sync File Upload ──

UPLOAD_DATA = b"x" * 4096


class TestSyncFileUpload:
    def test_zerodep(self, benchmark):
        benchmark(
            post,
            f"{BASE}/post",
            files={"file": ("bench.bin", UPLOAD_DATA, "application/octet-stream")},
        )

    def test_httpx(self, benchmark):
        benchmark(
            httpx.post,
            f"{BASE}/post",
            files={"file": ("bench.bin", UPLOAD_DATA, "application/octet-stream")},
        )


# ── Async File Upload ──


class TestAsyncFileUpload:
    def test_zerodep(self, benchmark):
        benchmark(
            _run_async,
            zd_async_post,
            f"{BASE}/post",
            files={"file": ("bench.bin", UPLOAD_DATA, "application/octet-stream")},
        )

    def test_httpx(self, benchmark):
        async def _upload():
            async with httpx.AsyncClient() as c:
                return await c.post(
                    f"{BASE}/post",
                    files={
                        "file": (
                            "bench.bin",
                            UPLOAD_DATA,
                            "application/octet-stream",
                        )
                    },
                )

        benchmark(_run_async, _upload)
