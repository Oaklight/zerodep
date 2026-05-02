"""Benchmark: zerodep httpserver vs flask vs microdot vs bottle."""

import asyncio
import json
import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "httpclient"))

from httpclient import async_get, async_post, get, post

# ── zerodep httpserver setup ──
from httpserver import App, JSONResponse

microdot = pytest.importorskip("microdot", reason="microdot not installed")
bottle = pytest.importorskip("bottle", reason="bottle not installed")
flask = pytest.importorskip("flask", reason="flask not installed")

# ── Payloads ──

PAYLOAD = {"key": "value", "nested": {"a": 1, "b": [1, 2, 3]}}
LARGE_PAYLOAD = {
    "items": [{"id": i, "name": f"item_{i}", "data": "x" * 100} for i in range(100)]
}

CONCURRENCY = 10


# ── Helpers ──


def _run_concurrent_get(url, n=CONCURRENCY):
    async def _gather():
        await asyncio.gather(*[async_get(url) for _ in range(n)])

    asyncio.run(_gather())


def _run_concurrent_post(url, payload, n=CONCURRENCY):
    async def _gather():
        await asyncio.gather(*[async_post(url, json=payload) for _ in range(n)])

    asyncio.run(_gather())


# ── zerodep httpserver setup ──


def _make_zerodep_app():
    app = App()

    @app.get("/ping")
    async def ping(request):
        return JSONResponse({"pong": True})

    @app.get("/sync-ping")
    def sync_ping(request):
        return JSONResponse({"pong": True})

    @app.post("/echo")
    async def echo(request):
        return JSONResponse(request.json())

    @app.get("/text")
    async def text(request):
        return "Hello, World!"

    return app


def _start_zerodep(app):
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


# ── flask setup ──


def _make_flask_app():
    app = flask.Flask(__name__)

    @app.get("/ping")
    def ping():
        return flask.jsonify({"pong": True})

    @app.post("/echo")
    def echo():
        return flask.jsonify(flask.request.get_json())

    @app.get("/text")
    def text():
        return "Hello, World!"

    return app


def _start_flask(app):
    from werkzeug.serving import make_server as werkzeug_make_server

    server = werkzeug_make_server("127.0.0.1", 0, app)
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


@pytest.fixture(scope="module")
def flask_url():
    app = _make_flask_app()
    return _start_flask(app)


# ── Serial Benchmarks ──


class TestGetJSON:
    def test_zerodep(self, benchmark, zerodep_url):
        benchmark(get, f"{zerodep_url}/ping")

    def test_flask(self, benchmark, flask_url):
        benchmark(get, f"{flask_url}/ping")

    def test_microdot(self, benchmark, microdot_url):
        benchmark(get, f"{microdot_url}/ping")

    def test_bottle(self, benchmark, bottle_url):
        benchmark(get, f"{bottle_url}/ping")


class TestPostJSON:
    def test_zerodep(self, benchmark, zerodep_url):
        benchmark(post, f"{zerodep_url}/echo", json=PAYLOAD)

    def test_flask(self, benchmark, flask_url):
        benchmark(post, f"{flask_url}/echo", json=PAYLOAD)

    def test_microdot(self, benchmark, microdot_url):
        benchmark(post, f"{microdot_url}/echo", json=PAYLOAD)

    def test_bottle(self, benchmark, bottle_url):
        benchmark(post, f"{bottle_url}/echo", json=PAYLOAD)


class TestGetText:
    def test_zerodep(self, benchmark, zerodep_url):
        benchmark(get, f"{zerodep_url}/text")

    def test_flask(self, benchmark, flask_url):
        benchmark(get, f"{flask_url}/text")

    def test_microdot(self, benchmark, microdot_url):
        benchmark(get, f"{microdot_url}/text")

    def test_bottle(self, benchmark, bottle_url):
        benchmark(get, f"{bottle_url}/text")


# ── Sync vs Async Handler (zerodep only) ──


class TestSyncVsAsyncHandler:
    def test_async_handler(self, benchmark, zerodep_url):
        benchmark(get, f"{zerodep_url}/ping")

    def test_sync_handler(self, benchmark, zerodep_url):
        benchmark(get, f"{zerodep_url}/sync-ping")


# ── Concurrent Benchmarks ──


class TestConcurrentGet:
    def test_zerodep(self, benchmark, zerodep_url):
        benchmark(_run_concurrent_get, f"{zerodep_url}/ping")

    def test_flask(self, benchmark, flask_url):
        benchmark(_run_concurrent_get, f"{flask_url}/ping")

    def test_microdot(self, benchmark, microdot_url):
        benchmark(_run_concurrent_get, f"{microdot_url}/ping")

    def test_bottle(self, benchmark, bottle_url):
        benchmark(_run_concurrent_get, f"{bottle_url}/ping")


class TestConcurrentPost:
    def test_zerodep(self, benchmark, zerodep_url):
        benchmark(_run_concurrent_post, f"{zerodep_url}/echo", PAYLOAD)

    def test_flask(self, benchmark, flask_url):
        benchmark(_run_concurrent_post, f"{flask_url}/echo", PAYLOAD)

    def test_microdot(self, benchmark, microdot_url):
        benchmark(_run_concurrent_post, f"{microdot_url}/echo", PAYLOAD)

    def test_bottle(self, benchmark, bottle_url):
        benchmark(_run_concurrent_post, f"{bottle_url}/echo", PAYLOAD)


# ── Large Payload ──


class TestLargePayload:
    def test_zerodep(self, benchmark, zerodep_url):
        benchmark(post, f"{zerodep_url}/echo", json=LARGE_PAYLOAD)

    def test_flask(self, benchmark, flask_url):
        benchmark(post, f"{flask_url}/echo", json=LARGE_PAYLOAD)

    def test_microdot(self, benchmark, microdot_url):
        benchmark(post, f"{microdot_url}/echo", json=LARGE_PAYLOAD)

    def test_bottle(self, benchmark, bottle_url):
        benchmark(post, f"{bottle_url}/echo", json=LARGE_PAYLOAD)
