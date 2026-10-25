# HTTP Server

Zero-dependency async HTTP server with Flask-style decorator routing, streaming responses (SSE), static file serving, and graceful shutdown -- stdlib only, Python 3.10+.

> **Replaces:** `flask` (lightweight), `microdot`, `bottle`, `starlette` (basic), `aiohttp` (server)

## Overview

The httpserver module provides a lightweight async HTTP/1.1 server built on `asyncio.start_server()`. It is designed as a drop-in alternative to Flask/microdot for projects that need HTTP serving without third-party dependencies.

| File | Description | Dependencies |
|------|-------------|--------------|
| `httpserver.py` | Pure Python implementation | None (stdlib only: `asyncio`, `json`, `re`, `signal`, `mimetypes`) |

## Features

- **Flask/microdot-compatible API** -- `@app.route()`, `@app.get()`, `@app.post()` with identical signatures
- **Path parameters** -- `<name>`, `<int:id>`, `<float:price>`, `<path:filepath>` with automatic type conversion
- **Return value coercion** -- `dict` → JSON, `str` → text, `bytes` → binary, `tuple` → (body, status, headers), `None` → 204
- **Streaming responses** -- chunked transfer encoding for async generators, SSE-compatible
- **Static file serving** -- `app.static()` with directory traversal prevention
- **Middleware** -- `before_request`, `after_request`, `errorhandler` hooks
- **Sync + async handlers** -- sync handlers auto-wrapped with `asyncio.to_thread()`
- **Graceful shutdown** -- SIGINT/SIGTERM handling, `app.shutdown()` callable from handlers

## How to Use in Your Project

Copy the single `.py` file into your project:

```bash
cp httpserver/httpserver.py your_project/
```

Then import directly:

```python
from httpserver import App, JSONResponse
```

## Usage Examples

### Basic App

```python
from httpserver import App, JSONResponse

app = App()

@app.get("/hello")
async def hello(request):
    return {"message": "Hello, World!"}

@app.post("/echo")
async def echo(request):
    return JSONResponse(request.json())

app.run(host="127.0.0.1", port=8000)
```

### Path Parameters

```python
@app.get("/users/<int:id>")
async def get_user(request, id):
    return {"user_id": id}

@app.get("/files/<path:filepath>")
async def get_file(request, filepath):
    return {"path": filepath}
```

### Multi-Method Route

```python
@app.route("/items", methods=["GET", "POST"])
async def items(request):
    if request.method == "GET":
        return {"items": []}
    data = request.json()
    return JSONResponse({"created": data}, status_code=201)
```

### Query Parameters and Headers

```python
@app.get("/search")
async def search(request):
    q = request.query_params.get("q", [""])[0]
    auth = request.headers.get("authorization", "")
    return {"query": q, "auth_present": bool(auth)}
```

### Sync Handlers

Sync functions are automatically wrapped with `asyncio.to_thread()`:

```python
@app.get("/sync")
def sync_handler(request):
    import time
    time.sleep(0.01)  # blocking I/O is fine
    return {"sync": True}
```

### Streaming Response (SSE)

```python
from httpserver import StreamingResponse
from sse import encode_comment, encode_event

@app.get("/events")
async def events(request):
    async def generate():
        yield encode_event("hello", event="greeting", id="1")
        yield encode_comment("heartbeat")
        yield encode_event("bye", id="2")

    return StreamingResponse(
        generate(),
        content_type="text/event-stream",
        disconnect_on_eof=True,
    )
```

`encode_event()` produces one complete block — multi-line payloads become one `data:` field per line, and the terminating blank line that dispatches the event is included. Writing `f"data: {value}\n\n"` by hand works only while the value has no line breaks: the first one ends the event, so the client dispatches the prefix and silently drops the rest. `encode_comment()` emits heartbeat comments that clients ignore. Both live in [`sse`](sse.md), which also provides the client side (`EventSource`, `connect`).

A client disconnect is noticed at three points: a failed write (`BrokenPipeError`, for example after a reset) ends the stream; between yields the loop also checks `writer.is_closing()`, which can stay false for a peer FIN until a write fails; and while the generator is blocked, `disconnect_check_interval` (default 30 s) checks it too. `disconnect_on_eof=True` adds read-side EOF to those checks, which is also what a legitimate half-close looks like, so it stays off unless the client never half-closes (browsers and common HTTP clients do not). The generator's `finally` then runs.

### Static Files

```python
app.static("/assets", "./public")
# GET /assets/style.css → serves ./public/style.css
```

### Middleware

```python
@app.before_request
async def auth_check(request):
    if not request.headers.get("authorization"):
        return JSONResponse({"error": "unauthorized"}, status_code=401)

@app.after_request
async def add_cors(request, response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.errorhandler(404)
async def not_found(request, exc):
    return JSONResponse({"error": "not found"}, status_code=404)

@app.errorhandler(ValueError)
async def bad_value(request, exc):
    return JSONResponse({"error": str(exc)}, status_code=400)
```

### File Response

```python
from httpserver import FileResponse

@app.get("/download")
async def download(request):
    return FileResponse("report.pdf")
```

### Return Value Coercion

Handlers can return various types, automatically coerced to responses:

```python
@app.get("/dict")
async def as_dict(request):
    return {"key": "value"}           # → JSONResponse

@app.get("/text")
async def as_text(request):
    return "Hello"                     # → Response (text/plain)

@app.get("/bytes")
async def as_bytes(request):
    return b"\x89PNG..."               # → Response (application/octet-stream)

@app.get("/tuple")
async def as_tuple(request):
    return {"ok": True}, 201           # → JSONResponse with status 201

@app.get("/empty")
async def as_none(request):
    return None                        # → 204 No Content
```

### Graceful Shutdown

```python
@app.post("/shutdown")
async def trigger_shutdown(request):
    request.app.shutdown()
    return {"status": "shutting down"}
```

## API Reference

### `App(*, max_body_size=1048576, read_timeout=30.0, keep_alive=True, keep_alive_timeout=5.0, max_requests_per_connection=100, shutdown_grace_timeout=5.0)`

Main application class.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_body_size` | `int` | `1048576` (1 MB) | Maximum request body size in bytes |
| `read_timeout` | `float` | `30.0` | Timeout for reading a single request |
| `keep_alive` | `bool` | `True` | Serve multiple requests per connection |
| `keep_alive_timeout` | `float` | `5.0` | Idle seconds before a kept-alive connection is closed |
| `max_requests_per_connection` | `int` | `100` | Close a connection after this many requests |
| `shutdown_grace_timeout` | `float` | `5.0` | Seconds a shutdown waits for in-flight requests before cancelling them; a request that has sent its request line and then stalls is also in flight, so this is its budget too |

**Connections:** HTTP/1.1 connections are kept alive unless the request sends `Connection: close` or the response sets it (the response header is matched case-insensitively); HTTP/1.0 stays open only when the request asks with `Connection: keep-alive`, and an unrecognised protocol version closes. Streaming responses (`StreamingResponse`) always close. `keep_alive_timeout` bounds only the wait for the *next request line*; once a request has started, its headers and body are read under `read_timeout`, so a slow upload is not cut off. An idle connection therefore closes quietly — no `408` — while a request that stalls after its request line still receives `408`. `HEAD` is served by the matching `GET` route (RFC 9110 §9.3.2) with the same headers, `Content-Length` included, and no body. On shutdown, a connection that has not sent a complete request line — a brand-new one that has sent nothing, a half-sent line, or a reused one waiting for its next request — is closed immediately — otherwise `Server.wait_closed()` (which waits for open connections on Python 3.12+) would hold shutdown for the whole idle window. Once a request line has arrived the connection is no longer idle, so a request whose body is still uploading is drained rather than cut off. Requests already being handled are allowed to finish on every supported Python version: connection handlers are tracked and awaited for up to `shutdown_grace_timeout` (default 5 s, `App(shutdown_grace_timeout=...)`) before being cancelled, since `wait_closed()` returns immediately on 3.10/3.11. A request that completes after shutdown began is answered with `Connection: close`.

**Routing Methods:**

| Method | Description |
|--------|-------------|
| `route(url_pattern, methods=None)` | Register a handler for a URL pattern. Default: `["GET"]` |
| `get(path)` | Shorthand for `route(path, methods=["GET"])` |
| `post(path)` | Shorthand for `route(path, methods=["POST"])` |
| `put(path)` | Shorthand for `route(path, methods=["PUT"])` |
| `delete(path)` | Shorthand for `route(path, methods=["DELETE"])` |
| `patch(path)` | Shorthand for `route(path, methods=["PATCH"])` |
| `static(url_prefix, directory)` | Serve static files from a directory |

**Middleware Methods:**

| Method | Description |
|--------|-------------|
| `before_request(handler)` | Register a pre-request hook. Return `Response` to short-circuit |
| `after_request(handler)` | Register a post-request hook. Receives `(request, response)` |
| `errorhandler(code_or_exc)` | Register an error handler for HTTP status code or exception class |

**Lifecycle Methods:**

| Method | Description |
|--------|-------------|
| `run(host="127.0.0.1", port=8000)` | Start the server (blocking) |
| `shutdown()` | Request graceful shutdown (safe to call from handlers) |

---

### `Request`

Parsed HTTP request object, passed as the first argument to all handlers.

| Attribute | Type | Description |
|-----------|------|-------------|
| `method` | `str` | Uppercase HTTP method (GET, POST, ...) |
| `path` | `str` | URL path, percent-decoded |
| `query_string` | `str` | Raw query string (without `?`) |
| `query_params` | `dict[str, list[str]]` | Parsed query string |
| `headers` | `dict[str, str]` | Headers (keys stored lowercase) |
| `body` | `bytes` | Raw request body |
| `path_params` | `dict[str, Any]` | Parameters extracted from route pattern |
| `client_addr` | `tuple[str, int]` | Client `(host, port)` |
| `app` | `App` | Reference to the application instance |

| Method | Return Type | Description |
|--------|-------------|-------------|
| `json()` | `Any` | Parse body as JSON (cached) |
| `text()` | `str` | Decode body as UTF-8 |
| `form()` | `dict[str, list[str]]` | Parse URL-encoded form body |

---

### `Response(body="", status_code=200, headers=None, content_type=None)`

HTTP response with a fixed body.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `body` | `bytes \| str` | `b""` | Response body |
| `status_code` | `int` | `200` | HTTP status code |
| `headers` | `dict[str, str] \| None` | `None` | Extra response headers |
| `content_type` | `str \| None` | `None` | Shorthand for Content-Type header |

---

### `JSONResponse(data, status_code=200, headers=None, *, allow_nan=False)`

Convenience response that serializes `data` to JSON.

Non-finite floats (`NaN`, `Infinity`, `-Infinity`) are refused with
`ValueError` rather than written, because they are not valid JSON and a
client's `JSON.parse` would fail on the body. Starlette's `JSONResponse`
makes the same choice. Pass `allow_nan=True` to emit them anyway; a handler
that wants `null` for non-finite values should sanitize the payload itself.

A handler that returns a `dict` always goes through `JSONResponse` with the
default, so the opt-out is reachable only by constructing the response
explicitly. When serialization fails inside a handler, a `before_request` or
`after_request` hook, or an error handler, the server answers `500` — the
connection stays usable rather than being closed without a response.

---

### `StreamingResponse(generator, status_code=200, headers=None, content_type=None, disconnect_check_interval=None, disconnect_on_eof=False)`

Streaming response using chunked transfer encoding.

| Parameter | Type | Description |
|-----------|------|-------------|
| `generator` | `AsyncIterator[str \| bytes]` | Async generator yielding response chunks |
| `content_type` | `str \| None` | For SSE, use `"text/event-stream"` |
| `disconnect_check_interval` | `float \| None` | Seconds between disconnect checks while the generator is blocked (default 30) |
| `disconnect_on_eof` | `bool` | Treat read-side EOF as a disconnect while blocked. Off by default because a half-closing client is still reading |

---

### `FileResponse(path, status_code=200, headers=None, content_type=None)`

Serve a file from disk. Content type is auto-detected via `mimetypes.guess_type()`.

---

### `HTTPException(status_code, message=None)`

Exception that maps to an HTTP status code. Raise directly or via `abort()`.

### `abort(status_code, message=None)`

Shorthand to raise `HTTPException`.

## Comparison with Flask / microdot / bottle

| Feature | zerodep httpserver | Flask | microdot | bottle |
|---------|-------------------|-------|----------|--------|
| Dependencies | None (stdlib only) | werkzeug, jinja2, ... | None | None |
| Async native | Yes (`asyncio`) | No (WSGI) | Yes (`asyncio`) | No (WSGI) |
| Handler first arg | `request` (explicit) | global `flask.request` | `request` (explicit) | global `bottle.request` |
| Route API | `@app.route(path, methods=)` | Same | Same | Same |
| Return coercion | dict/str/bytes/tuple/None | dict/str/tuple | dict/str/tuple | str/dict |
| Streaming | `StreamingResponse` | `stream_with_context` | `Response(async_gen)` | Generators |
| Static files | `app.static()` | `send_from_directory` | `send_file` | `static_file` |
| File size | ~1000 lines | ~2000 lines + deps | ~1400 lines | ~4700 lines |
| Concurrent handling | Async (many connections) | 1 req/thread | Async (many connections) | 1 req/thread |

**When to use zerodep:** You need a lightweight async server with zero dependencies and Flask-compatible API for embedding in tools, daemons, or microservices.

**When to use Flask:** You need the full ecosystem (Jinja templates, extensions, production WSGI servers like gunicorn).

**When to use microdot:** You need async serving on MicroPython or want a minimal Flask alternative with more features than zerodep.

## Benchmark

Benchmarked against Flask, microdot, and bottle across serial requests, concurrent load, sync vs async handlers, and large payloads.

See [HTTP Server Benchmark](../benchmarks/httpserver.md) for detailed results.
