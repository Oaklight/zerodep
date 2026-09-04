"""Correctness tests for zerodep httpserver module."""

import asyncio
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "httpclient"))

from httpclient import delete, get, patch, post, put
from httpserver import (
    App,
    HTTPException,
    JSONResponse,
    Request,
    Response,
    State,
    StreamingResponse,
    _coerce_response,
    _compile_route,
    abort,
)

# ── Unit Tests ───────────────────────────────────────────────────────────────


class TestRequest:
    """Request parsing and accessors."""

    def test_json(self):
        req = Request("POST", "/", "", {}, b'{"key": "val"}', ("127.0.0.1", 0))
        assert req.json() == {"key": "val"}
        # cached
        assert req.json() is req.json()

    def test_text(self):
        req = Request("GET", "/", "", {}, b"hello", ("127.0.0.1", 0))
        assert req.text() == "hello"

    def test_form(self):
        req = Request("POST", "/", "", {}, b"a=1&b=2&b=3", ("127.0.0.1", 0))
        form = req.form()
        assert form["a"] == ["1"]
        assert form["b"] == ["2", "3"]

    def test_query_params(self):
        req = Request("GET", "/", "x=1&y=2&y=3", {}, b"", ("127.0.0.1", 0))
        assert req.query_params["x"] == ["1"]
        assert req.query_params["y"] == ["2", "3"]


class TestResponse:
    """Response construction."""

    def test_str_body(self):
        r = Response(body="hello")
        assert r.body == b"hello"

    def test_bytes_body(self):
        r = Response(body=b"\x00\x01")
        assert r.body == b"\x00\x01"

    def test_content_type(self):
        r = Response(body="x", content_type="text/html")
        assert r.headers["Content-Type"] == "text/html"

    def test_json_response(self):
        r = JSONResponse({"a": 1})
        data = json.loads(r.body)
        assert data == {"a": 1}
        assert "application/json" in r.headers["Content-Type"]

    def test_json_response_unicode(self):
        r = JSONResponse({"msg": "你好"})
        assert "你好" in r.body.decode("utf-8")


class TestCoerceResponse:
    """Handler return value coercion."""

    def test_none(self):
        r = _coerce_response(None)
        assert r.status_code == 204

    def test_dict(self):
        r = _coerce_response({"a": 1})
        assert isinstance(r, JSONResponse)
        assert json.loads(r.body) == {"a": 1}

    def test_str(self):
        r = _coerce_response("hello")
        assert r.body == b"hello"

    def test_bytes(self):
        r = _coerce_response(b"\x00")
        assert r.body == b"\x00"

    def test_tuple2(self):
        r = _coerce_response(({"ok": True}, 201))
        assert r.status_code == 201

    def test_tuple3(self):
        r = _coerce_response(("ok", 200, {"X-Custom": "val"}))
        assert r.headers["X-Custom"] == "val"

    def test_response_passthrough(self):
        orig = Response(body="x")
        assert _coerce_response(orig) is orig

    def test_invalid_type(self):
        with pytest.raises(TypeError):
            _coerce_response(12345)


class TestRouteCompilation:
    """Path pattern to regex compilation."""

    def test_static_path(self):
        pattern, names, _ = _compile_route("/hello")
        assert names == []
        assert pattern.match("/hello")
        assert not pattern.match("/other")

    def test_str_param(self):
        pattern, names, converters = _compile_route("/users/<name>")
        assert names == ["name"]
        m = pattern.match("/users/alice")
        assert m
        assert converters[0](m.group(1)) == "alice"

    def test_int_param(self):
        pattern, names, converters = _compile_route("/users/<int:id>")
        assert names == ["id"]
        m = pattern.match("/users/42")
        assert m
        assert converters[0](m.group(1)) == 42

    def test_float_param(self):
        pattern, names, converters = _compile_route("/price/<float:amount>")
        m = pattern.match("/price/3.14")
        assert m
        assert converters[0](m.group(1)) == pytest.approx(3.14)

    def test_path_param(self):
        pattern, names, converters = _compile_route("/files/<path:filepath>")
        m = pattern.match("/files/a/b/c.txt")
        assert m
        assert converters[0](m.group(1)) == "a/b/c.txt"

    def test_multiple_params(self):
        pattern, names, _ = _compile_route("/users/<int:uid>/posts/<int:pid>")
        assert names == ["uid", "pid"]
        m = pattern.match("/users/1/posts/99")
        assert m
        assert m.groups() == ("1", "99")

    def test_unknown_type(self):
        with pytest.raises(ValueError, match="Unknown"):
            _compile_route("/x/<badtype:y>")


class TestHTTPException:
    """Exception and abort helper."""

    def test_exception_message(self):
        exc = HTTPException(404)
        assert exc.status_code == 404
        assert exc.message == "Not Found"

    def test_custom_message(self):
        exc = HTTPException(400, "Invalid input")
        assert exc.message == "Invalid input"

    def test_abort(self):
        with pytest.raises(HTTPException) as exc_info:
            abort(403, "Forbidden")
        assert exc_info.value.status_code == 403


# ── Integration Tests (require running server) ──────────────────────────────


class TestBasicRouting:
    """Basic GET/POST/PUT/DELETE/PATCH routing."""

    def test_get_json(self, server_url):
        r = get(f"{server_url}/status")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_get_text(self, server_url):
        r = get(f"{server_url}/text")
        assert r.status_code == 200
        assert r.text == "Hello, World!"

    def test_get_bytes(self, server_url):
        r = get(f"{server_url}/bytes")
        assert r.status_code == 200
        assert r.content == b"\x00\x01\x02"

    def test_none_204(self, server_url):
        r = get(f"{server_url}/none")
        assert r.status_code == 204

    def test_tuple2_status(self, server_url):
        r = get(f"{server_url}/tuple2")
        assert r.status_code == 201
        assert r.json()["created"] is True

    def test_tuple3_headers(self, server_url):
        r = get(f"{server_url}/tuple3")
        assert r.status_code == 200
        assert r.headers.get("x-custom") == "test-value"

    def test_post_json(self, server_url):
        r = post(f"{server_url}/echo", json={"msg": "hi"})
        assert r.status_code == 200
        data = r.json()
        assert data["body"] == {"msg": "hi"}
        assert data["method"] == "POST"

    def test_put_json(self, server_url):
        r = put(f"{server_url}/echo", json={"msg": "updated"})
        assert r.status_code == 200
        assert r.json()["method"] == "PUT"

    def test_delete(self, server_url):
        r = delete(f"{server_url}/echo")
        assert r.status_code == 200
        assert r.json()["method"] == "DELETE"

    def test_patch_json(self, server_url):
        r = patch(f"{server_url}/echo", json={"field": "val"})
        assert r.status_code == 200
        assert r.json()["method"] == "PATCH"

    def test_response_obj(self, server_url):
        r = get(f"{server_url}/response-obj")
        assert r.status_code == 200
        assert r.text == "custom"
        assert "text/html" in r.headers.get("content-type", "")


class TestPathParams:
    """Dynamic path parameter extraction."""

    def test_int_param(self, server_url):
        r = get(f"{server_url}/users/42")
        assert r.json() == {"id": 42}

    def test_path_param(self, server_url):
        r = get(f"{server_url}/files/a/b/c.txt")
        assert r.json() == {"path": "a/b/c.txt"}


class TestQueryParams:
    """Query string parsing."""

    def test_query(self, server_url):
        r = get(f"{server_url}/query?x=1&y=2&y=3")
        params = r.json()["params"]
        assert params["x"] == ["1"]
        assert params["y"] == ["2", "3"]


class TestHeaders:
    """Request header handling."""

    def test_custom_header(self, server_url):
        r = get(f"{server_url}/headers", headers={"X-Test": "hello"})
        assert r.json()["x-test"] == "hello"


class TestFormData:
    """URL-encoded form body."""

    def test_form(self, server_url):
        r = post(
            f"{server_url}/form",
            data="a=1&b=2",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        form = r.json()["form"]
        assert form["a"] == ["1"]
        assert form["b"] == ["2"]


class TestSyncHandler:
    """Sync (non-async) handler support."""

    def test_sync(self, server_url):
        r = get(f"{server_url}/sync")
        assert r.json() == {"sync": True}


class TestErrorHandling:
    """Error responses."""

    def test_404(self, server_url):
        r = get(f"{server_url}/nonexistent")
        assert r.status_code == 404

    def test_405(self, server_url):
        r = post(f"{server_url}/status")
        assert r.status_code == 405
        assert "Allow" in r.headers or "allow" in r.headers

    def test_abort_404(self, server_url):
        r = get(f"{server_url}/error/404")
        assert r.status_code == 404
        assert r.json()["error"] == "Custom not found"

    def test_500(self, server_url):
        r = get(f"{server_url}/error/500")
        assert r.status_code == 500
        assert "error" in r.json()


class TestStaticFiles:
    """Static file serving."""

    def test_text_file(self, server_url):
        r = get(f"{server_url}/static/hello.txt")
        assert r.status_code == 200
        assert r.text == "hello world"
        assert "text/plain" in r.headers.get("content-type", "")

    def test_json_file(self, server_url):
        r = get(f"{server_url}/static/data.json")
        assert r.status_code == 200
        assert r.json() == {"key": "value"}

    def test_nested_file(self, server_url):
        r = get(f"{server_url}/static/sub/nested.txt")
        assert r.status_code == 200
        assert r.text == "nested content"

    def test_missing_file(self, server_url):
        r = get(f"{server_url}/static/nope.txt")
        assert r.status_code == 404

    def test_traversal(self, server_url):
        r = get(f"{server_url}/static/../../../etc/passwd")
        assert r.status_code == 404


class TestStreaming:
    """Streaming responses (SSE and chunked)."""

    def test_sse_stream(self, server_url):
        r = get(f"{server_url}/sse")
        assert r.status_code == 200
        assert "text/event-stream" in r.headers.get("content-type", "")
        text = r.text
        for i in range(3):
            assert f"data: event-{i}" in text

    def test_chunked_stream(self, server_url):
        r = get(f"{server_url}/stream-chunked")
        assert r.status_code == 200
        text = r.text
        for i in range(3):
            assert f"chunk-{i}" in text


class _MockWriter:
    """Minimal writer stub for StreamingResponse tests."""

    def write(self, data):
        pass

    async def drain(self):
        pass


class TestStreamingBackground:
    """StreamingResponse background callback."""

    def test_sync_background_called(self):
        called = []

        async def gen():
            yield "hello"

        resp = StreamingResponse(gen(), background=lambda: called.append("done"))

        async def _run():
            await resp._write(_MockWriter())
            assert called == ["done"]

        asyncio.run(_run())

    def test_async_background_called(self):
        called = []

        async def gen():
            yield "hello"

        async def on_complete():
            called.append("async_done")

        resp = StreamingResponse(gen(), background=on_complete)

        async def _run():
            await resp._write(_MockWriter())
            assert called == ["async_done"]

        asyncio.run(_run())

    def test_background_called_after_generator_completes(self):
        order = []

        async def gen():
            for i in range(3):
                order.append(f"chunk-{i}")
                yield f"data-{i}"

        def on_complete():
            order.append("background")

        resp = StreamingResponse(gen(), background=on_complete)

        async def _run():
            await resp._write(_MockWriter())
            assert order == ["chunk-0", "chunk-1", "chunk-2", "background"]

        asyncio.run(_run())

    def test_background_not_called_when_none(self):
        async def gen():
            yield "hello"

        resp = StreamingResponse(gen())
        assert resp.background is None

        async def _run():
            await resp._write(_MockWriter())

        asyncio.run(_run())

    def test_background_exception_suppressed(self):
        async def gen():
            yield "hello"

        def bad_callback():
            raise ValueError("boom")

        resp = StreamingResponse(gen(), background=bad_callback)

        async def _run():
            await resp._write(_MockWriter())

        asyncio.run(_run())

    def test_background_called_after_generator_error(self):
        called = []

        async def gen():
            yield "ok"
            raise RuntimeError("generator error")

        resp = StreamingResponse(gen(), background=lambda: called.append("done"))

        async def _run():
            with pytest.raises(RuntimeError, match="generator error"):
                await resp._write(_MockWriter())
            assert called == ["done"]

        asyncio.run(_run())


class TestMiddleware:
    """Before/after request middleware hooks."""

    def test_before_after_request(self):
        """Test middleware hooks with a fresh app."""
        app = App()
        log = []

        @app.before_request
        async def before(request):
            log.append("before")

        @app.get("/mid")
        async def handler(request):
            log.append("handler")
            return {"ok": True}

        @app.after_request
        async def after(request, response):
            log.append("after")
            if isinstance(response, Response):
                response.headers["X-After"] = "yes"
            return response

        async def _test():
            req = Request("GET", "/mid", "", {}, b"", ("127.0.0.1", 0), app=app)
            resp = await app._dispatch(req)
            assert log == ["before", "handler", "after"]
            assert isinstance(resp, Response)
            assert resp.headers["X-After"] == "yes"

        asyncio.run(_test())

    def test_before_request_shortcircuit(self):
        """before_request returning a Response skips the handler."""
        app = App()

        @app.before_request
        async def auth_check(request):
            return JSONResponse({"error": "unauthorized"}, status_code=401)

        @app.get("/protected")
        async def protected(request):
            return {"secret": True}

        async def _test():
            req = Request("GET", "/protected", "", {}, b"", ("127.0.0.1", 0), app=app)
            resp = await app._dispatch(req)
            assert resp.status_code == 401

        asyncio.run(_test())

    def test_errorhandler(self):
        """Custom error handler."""
        app = App()

        @app.errorhandler(404)
        async def custom_404(request, exc):
            return JSONResponse({"custom": "not found"}, status_code=404)

        async def _test():
            req = Request("GET", "/nope", "", {}, b"", ("127.0.0.1", 0), app=app)
            resp = await app._dispatch(req)
            assert resp.status_code == 404
            assert json.loads(resp.body)["custom"] == "not found"

        asyncio.run(_test())


class TestRequestState:
    """Per-request State namespace."""

    def test_set_and_get_attribute(self):
        """State allows arbitrary attribute set/get."""
        state = State()
        state.foo = "bar"
        state.count = 42
        assert state.foo == "bar"
        assert state.count == 42

    def test_missing_attribute_raises(self):
        """Accessing an unset attribute raises AttributeError."""
        state = State()
        with pytest.raises(AttributeError):
            _ = state.no_such_attr

    def test_repr_empty(self):
        """Empty State has a clean repr."""
        state = State()
        assert repr(state) == "State()"

    def test_repr_with_attrs(self):
        """State repr shows stored attributes."""
        state = State()
        state.x = 1
        r = repr(state)
        assert r.startswith("State(")
        assert "x=1" in r

    def test_equality(self):
        """Two State objects with the same attributes are equal."""
        a = State()
        a.x = 1
        a.y = "hello"
        b = State()
        b.x = 1
        b.y = "hello"
        assert a == b

    def test_inequality(self):
        """State objects with different attributes are not equal."""
        a = State()
        a.x = 1
        b = State()
        b.x = 2
        assert a != b

    def test_equality_not_implemented_for_other_types(self):
        """State.__eq__ returns NotImplemented for non-State objects."""
        state = State()
        assert state != "not a state"
        assert state.__eq__("not a state") is NotImplemented

    def test_request_has_fresh_state(self):
        """Each Request gets its own fresh State instance."""
        req = Request("GET", "/", "", {}, b"", ("127.0.0.1", 0))
        assert isinstance(req.state, State)
        assert repr(req.state) == "State()"

    def test_each_request_gets_independent_state(self):
        """Two requests do not share state."""
        req1 = Request("GET", "/", "", {}, b"", ("127.0.0.1", 0))
        req2 = Request("GET", "/", "", {}, b"", ("127.0.0.1", 0))
        req1.state.marker = "req1"
        assert not hasattr(req2.state, "marker")

    def test_state_in_before_request_middleware(self):
        """State set in before_request is visible in the handler."""
        app = App()
        observed = {}

        @app.before_request
        async def inject(request):
            request.state.injected = "hello"

        @app.get("/check")
        async def handler(request):
            observed["value"] = request.state.injected
            return {"ok": True}

        async def _test():
            req = Request("GET", "/check", "", {}, b"", ("127.0.0.1", 0), app=app)
            await app._dispatch(req)
            assert observed["value"] == "hello"

        asyncio.run(_test())

    def test_state_persists_across_middleware_and_handler(self):
        """State survives from before_request through handler to after_request."""
        app = App()
        log = []

        @app.before_request
        async def before(request):
            request.state.trace = ["before"]

        @app.get("/traced")
        async def handler(request):
            request.state.trace.append("handler")
            return {"ok": True}

        @app.after_request
        async def after(request, response):
            request.state.trace.append("after")
            log.extend(request.state.trace)
            return response

        async def _test():
            req = Request("GET", "/traced", "", {}, b"", ("127.0.0.1", 0), app=app)
            await app._dispatch(req)
            assert log == ["before", "handler", "after"]

        asyncio.run(_test())


class TestLifespan:
    """Lifespan event hooks (on_startup / on_shutdown)."""

    def test_sync_startup(self):
        """Sync startup hook is called."""
        app = App()
        called = []

        @app.on_startup
        def init():
            called.append("started")

        asyncio.run(app._run_startup_hooks())
        assert called == ["started"]

    def test_async_startup(self):
        """Async startup hook is called."""
        app = App()
        called = []

        @app.on_startup
        async def init():
            called.append("async_started")

        asyncio.run(app._run_startup_hooks())
        assert called == ["async_started"]

    def test_sync_shutdown(self):
        """Sync shutdown hook is called."""
        app = App()
        called = []

        @app.on_shutdown
        def cleanup():
            called.append("stopped")

        asyncio.run(app._run_shutdown_hooks())
        assert called == ["stopped"]

    def test_async_shutdown(self):
        """Async shutdown hook is called."""
        app = App()
        called = []

        @app.on_shutdown
        async def cleanup():
            called.append("async_stopped")

        asyncio.run(app._run_shutdown_hooks())
        assert called == ["async_stopped"]

    def test_startup_order(self):
        """Startup hooks run in registration order."""
        app = App()
        order = []

        @app.on_startup
        def first():
            order.append(1)

        @app.on_startup
        async def second():
            order.append(2)

        @app.on_startup
        def third():
            order.append(3)

        asyncio.run(app._run_startup_hooks())
        assert order == [1, 2, 3]

    def test_shutdown_reverse_order(self):
        """Shutdown hooks run in reverse registration order (LIFO)."""
        app = App()
        order = []

        @app.on_shutdown
        def first():
            order.append(1)

        @app.on_shutdown
        async def second():
            order.append(2)

        @app.on_shutdown
        def third():
            order.append(3)

        asyncio.run(app._run_shutdown_hooks())
        assert order == [3, 2, 1]

    def test_startup_failure_reraises(self):
        """Startup hook failure is re-raised to prevent server start."""
        app = App()
        called = []

        @app.on_startup
        def good():
            called.append("good")

        @app.on_startup
        async def bad():
            raise RuntimeError("init failed")

        @app.on_startup
        def after_bad():
            called.append("should_not_run")

        with pytest.raises(RuntimeError, match="init failed"):
            asyncio.run(app._run_startup_hooks())

        # First hook ran, third did not
        assert called == ["good"]

    def test_shutdown_failure_continues(self):
        """Shutdown hook failure does not prevent remaining hooks."""
        app = App()
        called = []

        @app.on_shutdown
        def first():
            called.append("first")

        @app.on_shutdown
        async def bad():
            raise RuntimeError("cleanup failed")

        @app.on_shutdown
        def third():
            called.append("third")

        # No exception raised despite the failing hook
        asyncio.run(app._run_shutdown_hooks())

        # Reverse order: third, bad (fails), first — both non-failing hooks ran
        assert called == ["third", "first"]

    def test_decorators_return_original(self):
        """on_startup / on_shutdown return the original callable."""
        app = App()

        @app.on_startup
        def my_startup():
            pass

        @app.on_shutdown
        async def my_shutdown():
            pass

        assert my_startup.__name__ == "my_startup"
        assert my_shutdown.__name__ == "my_shutdown"

    def test_lifespan_integration_with_serve(self):
        """Startup and shutdown hooks fire during a full server lifecycle."""
        import threading

        app = App()
        events = []

        @app.on_startup
        async def on_start():
            events.append("startup")

        @app.on_shutdown
        async def on_stop():
            events.append("shutdown")

        @app.get("/ping")
        async def ping(request):
            return {"pong": True}

        ready = threading.Event()

        def _run():
            async def _start():
                app._shutdown_event = asyncio.Event()
                app._loop = asyncio.get_running_loop()
                await app._run_startup_hooks()
                server = await asyncio.start_server(
                    app._handle_connection, "127.0.0.1", 0
                )
                app._server = server
                addrs = server.sockets[0].getsockname()
                app.host = addrs[0]
                app.port = addrs[1]
                ready.set()
                try:
                    async with server:
                        await app._shutdown_event.wait()
                finally:
                    await app._run_shutdown_hooks()

            asyncio.run(_start())

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        ready.wait(timeout=5)

        from httpclient import get as http_get

        r = http_get(f"http://127.0.0.1:{app.port}/ping")
        assert r.status_code == 200

        app.shutdown()
        thread.join(timeout=5)
        assert not thread.is_alive(), "Server thread did not exit in time"

        assert events == ["startup", "shutdown"]

    def test_no_hooks_is_noop(self):
        """Server works fine with no lifespan hooks registered."""
        app = App()

        async def _test():
            await app._run_startup_hooks()
            await app._run_shutdown_hooks()

        asyncio.run(_test())  # Should not raise
