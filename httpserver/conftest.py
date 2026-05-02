"""Fixtures for httpserver tests."""

import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "httpclient"))

from httpserver import App, JSONResponse, Response, StreamingResponse, abort


def _build_test_app(static_dir=None):
    """Create a test app with standard routes."""
    app = App()

    @app.get("/status")
    async def status(request):
        return JSONResponse({"status": "ok"})

    @app.get("/text")
    async def text(request):
        return "Hello, World!"

    @app.get("/bytes")
    async def raw_bytes(request):
        return b"\x00\x01\x02"

    @app.get("/none")
    async def no_content(request):
        return None

    @app.get("/tuple2")
    async def tuple2(request):
        return {"created": True}, 201

    @app.get("/tuple3")
    async def tuple3(request):
        return {"ok": True}, 200, {"X-Custom": "test-value"}

    @app.post("/echo")
    async def echo(request):
        return JSONResponse({"body": request.json(), "method": "POST"})

    @app.put("/echo")
    async def echo_put(request):
        return JSONResponse({"body": request.json(), "method": "PUT"})

    @app.delete("/echo")
    async def echo_delete(request):
        return JSONResponse({"method": "DELETE"})

    @app.patch("/echo")
    async def echo_patch(request):
        return JSONResponse({"body": request.json(), "method": "PATCH"})

    @app.get("/users/<int:id>")
    async def get_user(request, id):
        return JSONResponse({"id": id})

    @app.get("/files/<path:filepath>")
    async def get_file(request, filepath):
        return JSONResponse({"path": filepath})

    @app.get("/query")
    async def query(request):
        return JSONResponse({"params": request.query_params})

    @app.get("/headers")
    async def headers(request):
        ua = request.headers.get("user-agent", "")
        custom = request.headers.get("x-test", "")
        return JSONResponse({"user-agent": ua, "x-test": custom})

    @app.get("/error/404")
    async def not_found_error(request):
        abort(404, "Custom not found")

    @app.get("/error/500")
    async def server_error(request):
        raise RuntimeError("boom")

    @app.post("/form")
    async def form_handler(request):
        return JSONResponse({"form": request.form()})

    @app.get("/sync")
    def sync_handler(request):
        return JSONResponse({"sync": True})

    @app.get("/sse")
    async def sse(request):
        async def generate():
            for i in range(3):
                yield f"data: event-{i}\n\n"

        return StreamingResponse(
            generate(), content_type="text/event-stream"
        )

    @app.get("/stream-chunked")
    async def stream_chunked(request):
        async def generate():
            for i in range(3):
                yield f"chunk-{i}"

        return StreamingResponse(generate(), content_type="text/plain")

    @app.get("/response-obj")
    async def response_obj(request):
        return Response(body="custom", status_code=200, content_type="text/html")

    if static_dir:
        app.static("/static", static_dir)

    return app


@pytest.fixture(scope="session")
def static_dir(tmp_path_factory):
    """Create a temporary directory with static files."""
    d = tmp_path_factory.mktemp("static")
    (d / "hello.txt").write_text("hello world")
    (d / "data.json").write_text('{"key": "value"}')
    sub = d / "sub"
    sub.mkdir()
    (sub / "nested.txt").write_text("nested content")
    return str(d)


@pytest.fixture(scope="session")
def server_url(static_dir):
    """Start the httpserver in a background thread and yield its URL."""
    app = _build_test_app(static_dir=static_dir)

    ready = threading.Event()

    def _run():
        import asyncio

        async def _start():
            app._shutdown_event = asyncio.Event()
            server = await asyncio.start_server(
                app._handle_connection, "127.0.0.1", 0
            )
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
    yield f"http://127.0.0.1:{app.port}"
    app.shutdown()
    thread.join(timeout=2)
