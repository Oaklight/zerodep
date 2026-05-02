"""Benchmark: zerodep httpserver vs microdot vs bottle."""

import json
import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "httpclient"))

from httpclient import get, post

# ── zerodep httpserver setup ──
from httpserver import App, JSONResponse

microdot = pytest.importorskip("microdot", reason="microdot not installed")
bottle = pytest.importorskip("bottle", reason="bottle not installed")


def _make_zerodep_app():
    app = App()

    @app.get("/ping")
    async def ping(request):
        return JSONResponse({"pong": True})

    @app.post("/echo")
    async def echo(request):
        return JSONResponse(request.json())

    @app.get("/text")
    async def text(request):
        return "Hello, World!"

    return app


def _start_zerodep(app):
    import asyncio

    ready = threading.Event()

    def _run():
        async def _start():
            app._shutdown_event = asyncio.Event()
            server = await asyncio.start_server(app._handle_connection, "127.0.0.1", 0)
            app._server = server
            addrs = server.sockets[0].getsockname()
            app.host = addrs[0]
            app.port = addrs[1]
            ready.set()
            async with server:
                await app._shutdown_event.wait()

        asyncio.run(_start())

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    ready.wait(timeout=5)
    return f"http://127.0.0.1:{app.port}"


# ── microdot setup ──


def _make_microdot_app():
    app = microdot.Microdot()

    @app.get("/ping")
    async def ping(request):
        return {"pong": True}

    @app.post("/echo")
    async def echo(request):
        return request.json

    @app.get("/text")
    async def text(request):
        return "Hello, World!"

    return app


def _start_microdot(app):
    import asyncio

    ready = threading.Event()

    def _run():
        async def _start():
            server = await app.start_server(
                host="127.0.0.1", port=0, start_serving=False
            )
            addrs = server.sockets[0].getsockname()
            app._port = addrs[1]
            ready.set()
            await server.serve_forever()

        try:
            asyncio.run(_start())
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    ready.wait(timeout=5)
    return f"http://127.0.0.1:{app._port}"


# ── bottle setup ──


def _make_bottle_app():
    app = bottle.Bottle()

    @app.get("/ping")
    def ping():
        bottle.response.content_type = "application/json"
        return json.dumps({"pong": True})

    @app.post("/echo")
    def echo():
        body = json.loads(bottle.request.body.read())
        bottle.response.content_type = "application/json"
        return json.dumps(body)

    @app.get("/text")
    def text():
        return "Hello, World!"

    return app


def _start_bottle(app):
    from wsgiref.simple_server import make_server

    server = make_server("127.0.0.1", 0, app)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return f"http://127.0.0.1:{port}"


# ── fixtures ──


@pytest.fixture(scope="module")
def zerodep_url():
    app = _make_zerodep_app()
    return _start_zerodep(app)


@pytest.fixture(scope="module")
def microdot_url():
    app = _make_microdot_app()
    return _start_microdot(app)


@pytest.fixture(scope="module")
def bottle_url():
    app = _make_bottle_app()
    return _start_bottle(app)


# ── Benchmarks ──

PAYLOAD = {"key": "value", "nested": {"a": 1, "b": [1, 2, 3]}}


class TestGetJSON:
    def test_zerodep(self, benchmark, zerodep_url):
        benchmark(get, f"{zerodep_url}/ping")

    def test_microdot(self, benchmark, microdot_url):
        benchmark(get, f"{microdot_url}/ping")

    def test_bottle(self, benchmark, bottle_url):
        benchmark(get, f"{bottle_url}/ping")


class TestPostJSON:
    def test_zerodep(self, benchmark, zerodep_url):
        benchmark(post, f"{zerodep_url}/echo", json=PAYLOAD)

    def test_microdot(self, benchmark, microdot_url):
        benchmark(post, f"{microdot_url}/echo", json=PAYLOAD)

    def test_bottle(self, benchmark, bottle_url):
        benchmark(post, f"{bottle_url}/echo", json=PAYLOAD)


class TestGetText:
    def test_zerodep(self, benchmark, zerodep_url):
        benchmark(get, f"{zerodep_url}/text")

    def test_microdot(self, benchmark, microdot_url):
        benchmark(get, f"{microdot_url}/text")

    def test_bottle(self, benchmark, bottle_url):
        benchmark(get, f"{bottle_url}/text")
