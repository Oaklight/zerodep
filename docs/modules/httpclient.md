# HTTP Client

Zero-dependency synchronous and asynchronous HTTP/1.1 REST client built entirely on the Python standard library.

## Overview

`httpclient.py` is a single-file HTTP client that supports both sync and async workflows. It requires **Python 3.10+** and has **no pip dependencies**. The API design follows the `requests` / `httpx` convention — if you've used either, you already know how to use this module.

- **Familiar API** — `get()`, `post()`, `Response.json()`, `Response.status_code`, `Client` / `AsyncClient` sessions — all modeled after `requests` and `httpx`.
- **Sync mode** uses `http.client` from the standard library.
- **Async mode** uses `asyncio` streams with a hand-written HTTP/1.1 protocol implementation.
- **Thread-safe** by design: each request creates its own connection. Session classes use locks internally.
- **Connection pooling** — `Client` and `AsyncClient` automatically pool and reuse TCP connections (stateless functions still create one-off connections).
- **Auto decompression** — transparently decodes gzip/deflate responses.
- **Proxy support** — HTTP proxy, HTTPS proxy with CONNECT tunneling, and SOCKS5 proxy (RFC 1928) with username/password auth.
- **Built-in auth** — Basic and Digest authentication out of the box.

## Two Modes of Operation

### Function API (Stateless)

Top-level functions like `get()`, `post()`, `async_get()`, etc. Each call is independent and thread-safe -- there is no shared state between calls.

```python
from httpclient import get, post

# Simple GET
response = get("https://httpbin.org/get")
print(response.json())

# POST with JSON body
response = post("https://httpbin.org/post", json={"key": "value"})
print(response.status_code)
```

### Session API (Client / AsyncClient)

`Client` and `AsyncClient` classes allow sharing default headers, timeout, and other settings across multiple requests.

```python
from httpclient import Client

with Client(headers={"Authorization": "Bearer token"}) as client:
    r1 = client.get("https://api.example.com/users")
    r2 = client.post("https://api.example.com/users", json={"name": "Alice"})
```

## Usage Examples

### Basic GET Request

```python
from httpclient import get

response = get("https://httpbin.org/get")
print(response.status_code)  # 200
print(response.ok)           # True
print(response.json())       # {...}
```

### GET with Query Parameters

```python
from httpclient import get

response = get(
    "https://httpbin.org/get",
    params={"search": "python", "page": 1},
)
print(response.url)  # https://httpbin.org/get?search=python&page=1
```

### POST with JSON

```python
from httpclient import post

response = post(
    "https://httpbin.org/post",
    json={"username": "alice", "email": "alice@example.com"},
)
data = response.json()
print(data["json"])  # {"username": "alice", "email": "alice@example.com"}
```

### Custom Headers

```python
from httpclient import get

response = get(
    "https://api.example.com/data",
    headers={
        "Authorization": "Bearer my-token",
        "Accept": "application/json",
    },
)
```

### Error Handling

```python
from httpclient import get, HTTPError

response = get("https://httpbin.org/status/404")
print(response.ok)  # False

try:
    response.raise_for_status()
except HTTPError as e:
    print(f"HTTP {e.status_code} for {e.url}")
```

### File Upload

```python
from httpclient import post

# Simple file upload
response = post(
    "https://httpbin.org/post",
    files={"file": ("report.txt", b"file content", "text/plain")},
)

# Upload with form fields
response = post(
    "https://httpbin.org/post",
    data={"username": "alice"},
    files={"avatar": open("photo.jpg", "rb")},
)

# Multiple files
response = post(
    "https://httpbin.org/post",
    files=[
        ("attachment", ("doc1.pdf", pdf_bytes)),
        ("attachment", ("doc2.pdf", pdf_bytes2)),
    ],
)
```

### Session Usage

```python
from httpclient import Client

with Client(
    headers={"Authorization": "Bearer token"},
    timeout=10.0,
) as client:
    users = client.get("https://api.example.com/users").json()
    profile = client.get("https://api.example.com/me").json()
```

### Async Usage

```python
import asyncio
from httpclient import async_get, AsyncClient

async def main():
    # Function API
    response = await async_get("https://httpbin.org/get")
    print(response.json())

    # Session API
    async with AsyncClient(headers={"X-Api-Key": "secret"}) as client:
        r = await client.get("https://api.example.com/data")
        print(r.json())

asyncio.run(main())
```

### Streaming

```python
from httpclient import get, async_get

# Sync streaming
with get("https://httpbin.org/get", stream=True) as r:
    for chunk in r.iter_bytes():
        process(chunk)

# Line-by-line (useful for SSE)
with get("https://example.com/events", stream=True) as r:
    for line in r.iter_lines():
        print(line)

# Async streaming
async with await async_get("https://httpbin.org/get", stream=True) as r:
    async for chunk in r.aiter_bytes():
        await process(chunk)
```

### Disabling TLS Verification

```python
from httpclient import get

# Not recommended for production
response = get("https://self-signed.example.com/api", verify=False)
```

### Connection Pooling

`Client` and `AsyncClient` automatically pool TCP connections per host. Connections are reused across requests, significantly reducing latency for repeated calls to the same API.

```python
from httpclient import Client

# Connections are pooled and reused automatically
with Client() as client:
    for page in range(10):
        r = client.get(f"https://api.example.com/items?page={page}")
        print(r.json())

# Custom pool size
with Client(pool_size=20) as client:
    r = client.get("https://api.example.com/data")
```

!!! note "Stateless Functions"
    Top-level functions like `get()`, `post()` still create a new connection per call. Use `Client` / `AsyncClient` for connection pooling.

### Content Decompression

Responses compressed with gzip or deflate are automatically decompressed. The `Accept-Encoding: gzip, deflate` header is sent by default.

```python
from httpclient import get

# Automatic: response is decompressed transparently
r = get("https://api.example.com/data")
print(r.json())  # Already decompressed

# Opt out of compression
r = get("https://api.example.com/data", headers={"Accept-Encoding": "identity"})
```

Streaming responses are also decompressed incrementally:

```python
with get("https://example.com/large.json.gz", stream=True) as r:
    for chunk in r.iter_bytes():
        process(chunk)  # Already decompressed
```

### Proxy Support

Route requests through an HTTP or SOCKS5 proxy. HTTPS targets use CONNECT tunneling (HTTP proxy) or a transparent TCP tunnel (SOCKS5).

```python
from httpclient import get, Client

# HTTP proxy
r = get("https://api.example.com/data", proxy="http://proxy.corp:8080")

# HTTP proxy with authentication
r = get("https://api.example.com/data", proxy="http://user:pass@proxy.corp:8080")

# SOCKS5 proxy
r = get("https://api.example.com/data", proxy="socks5://proxy.corp:1080")

# SOCKS5 proxy with authentication
r = get("https://api.example.com/data", proxy="socks5://user:pass@proxy.corp:1080")

# Session-level proxy (works with any proxy type)
with Client(proxy="socks5://proxy.corp:1080") as client:
    r = client.get("https://api.example.com/data")
```

### Authentication

Built-in support for HTTP Basic and Digest authentication.

```python
from httpclient import get, Client, BasicAuth, DigestAuth

# Basic auth (tuple shorthand)
r = get("https://api.example.com/data", auth=("user", "pass"))

# Basic auth (explicit)
r = get("https://api.example.com/data", auth=BasicAuth("user", "pass"))

# Digest auth (automatic 401 challenge-response)
r = get("https://api.example.com/data", auth=DigestAuth("user", "pass"))

# Session-level auth
with Client(auth=("user", "pass")) as client:
    r = client.get("https://api.example.com/protected")
```

## API Reference

### Sync Functions

All sync functions accept the same keyword arguments:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `headers` | `dict[str, str]` | `None` | Request headers |
| `data` | `bytes \| str \| dict[str, str]` | `None` | Raw request body, or form fields when used with `files` |
| `files` | `dict[str, ...] \| list[tuple[str, ...]]` | `None` | File fields for multipart/form-data upload |
| `json` | `Any` | `None` | JSON-serializable body (sets Content-Type automatically) |
| `params` | `dict[str, Any]` | `None` | URL query parameters |
| `timeout` | `float` | `30.0` | Request timeout in seconds |
| `max_redirects` | `int` | `10` | Maximum number of redirects to follow |
| `verify` | `bool` | `True` | Verify TLS certificates |
| `stream` | `bool` | `False` | Return a `StreamingResponse` for incremental body consumption |
| `auth` | `tuple[str, str] \| Auth \| None` | `None` | Authentication credentials (tuple for Basic, or `BasicAuth`/`DigestAuth` object) |
| `proxy` | `str \| None` | `None` | Proxy URL (e.g. `"http://proxy:8080"`) |

```python
get(url, **kwargs) -> Response
post(url, **kwargs) -> Response
put(url, **kwargs) -> Response
patch(url, **kwargs) -> Response
delete(url, **kwargs) -> Response
head(url, **kwargs) -> Response
options(url, **kwargs) -> Response
```

### Async Functions

Same parameters as sync functions, but must be awaited:

```python
await async_get(url, **kwargs) -> Response
await async_post(url, **kwargs) -> Response
await async_put(url, **kwargs) -> Response
await async_patch(url, **kwargs) -> Response
await async_delete(url, **kwargs) -> Response
await async_head(url, **kwargs) -> Response
await async_options(url, **kwargs) -> Response
```

### Response Object

| Attribute / Method | Type | Description |
|--------------------|------|-------------|
| `status_code` | `int` | HTTP status code |
| `headers` | `dict[str, str]` | Response headers (lowercase keys) |
| `content` | `bytes` | Raw response body |
| `url` | `str` | Final URL after redirects |
| `text` | `str` (property) | Response body decoded as text |
| `ok` | `bool` (property) | `True` if status code is 2xx |
| `json()` | `Any` | Parse response body as JSON |
| `raise_for_status()` | `None` | Raise `HTTPError` if status is not 2xx |

### StreamingResponse Object

Returned when `stream=True`. Use as a context manager to ensure cleanup.

| Property / Method | Type | Description |
|---|---|---|
| `status_code` | `int` | HTTP status code |
| `headers` | `dict[str, str]` | Response headers (lowercase keys) |
| `url` | `str` | Final URL after redirects |
| `ok` | `bool` (property) | `True` if status is 2xx |
| `raise_for_status()` | `None` | Raise `HTTPError` on non-2xx |
| `iter_bytes(chunk_size)` | `Iterator[bytes]` | Yield body in chunks |
| `iter_lines()` | `Iterator[str]` | Yield decoded lines |
| `read()` | `bytes` | Consume entire stream |
| `aiter_bytes(chunk_size)` | `AsyncIterator[bytes]` | Async yield body in chunks |
| `aiter_lines()` | `AsyncIterator[str]` | Async yield decoded lines |
| `aread()` | `bytes` | Async consume entire stream |
| `close()` / `aclose()` | `None` | Close the underlying connection |

### Client Class

```python
Client(
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    max_redirects: int = 10,
    verify: bool = True,
    auth: tuple[str, str] | Auth | None = None,
    proxy: str | None = None,
    pool_size: int = 10,
)
```

Supports context manager (`with` statement). Methods: `get`, `post`, `put`, `patch`, `delete`, `head`, `options`, `request`.

Thread-safe: uses a `threading.Lock` internally. Connections are pooled and reused automatically. Call `close()` or use as a context manager to release pooled connections.

### AsyncClient Class

```python
AsyncClient(
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    max_redirects: int = 10,
    verify: bool = True,
    auth: tuple[str, str] | Auth | None = None,
    proxy: str | None = None,
    pool_size: int = 10,
)
```

Supports async context manager (`async with` statement). Methods: `get`, `post`, `put`, `patch`, `delete`, `head`, `options`, `request`.

Uses an `asyncio.Lock` internally for safe concurrent access from the same client instance. Connections are pooled and reused automatically. Call `aclose()` or use as an async context manager to release pooled connections.

### Auth Classes

| Class | Description |
|-------|-------------|
| `Auth` | Base class for authentication. Subclass and override `auth_headers(method, url)`. |
| `BasicAuth(username, password)` | HTTP Basic authentication. Sends `Authorization: Basic` header on every request. |
| `DigestAuth(username, password)` | HTTP Digest authentication. On 401 response, computes digest from server challenge and retries. Supports MD5 and SHA-256 algorithms. |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `HTTPError` | Raised by `raise_for_status()` on non-2xx status. Has `status_code`, `body`, and `url` attributes. |
| `TooManyRedirects` | Subclass of `HTTPError`. Raised when redirect limit is exceeded. Has `max_redirects` attribute. |
| `ConnectionError` | Raised on TCP/TLS connection failures. |
| `TimeoutError` | Raised when a request exceeds the timeout. |

## Features

- **Automatic redirect following** -- handles 301, 302, 303, 307, 308 with correct method conversion (POST to GET on 303, etc.)
- **Chunked transfer encoding** -- automatically decoded in async mode
- **TLS support** -- HTTPS via `ssl.create_default_context()`, with option to disable verification
- **Configurable timeouts** -- per-request or per-session timeout
- **JSON handling** -- automatic serialization/deserialization with correct Content-Type
- **Query parameter encoding** -- via the `params` argument
- **Multipart file upload** -- upload files via `files` parameter, with optional form field mixing via `data`
- **Response streaming** -- consume response body incrementally via `iter_bytes()` / `iter_lines()` or their async equivalents
- **Connection pooling** — `Client`/`AsyncClient` pool and reuse TCP connections per host
- **Auto decompression** — transparently decodes gzip/deflate responses
- **HTTP/HTTPS proxy** — route requests through a proxy server, with CONNECT tunneling for HTTPS
- **Basic & Digest auth** — built-in authentication with automatic 401 challenge handling for Digest

## How to Use in Your Project

Copy `httpclient.py` into your project:

```bash
cp httpclient/httpclient.py your_project/
```

Then import it:

```python
from httpclient import get, post, Client, AsyncClient
```

!!! warning "Do Not Rename to `http.py`"
    The file must not be named `http.py` -- that would shadow the standard library `http` module which `httpclient.py` depends on internally.

## Comparison with httpx

| Feature | zerodep | httpx |
|---------|---------|-------|
| Dependencies | None (stdlib only) | Several (httpcore, h11, etc.) |
| HTTP/2 | No | Yes |
| Connection pooling | Yes (Client/AsyncClient) | Yes |
| Auto decompression | Yes (gzip, deflate) | Yes (gzip, deflate, brotli) |
| Proxy support | Yes (HTTP, HTTPS tunnel, SOCKS5) | Yes (HTTP, HTTPS, SOCKS) |
| Authentication | Basic + Digest | Basic + Digest + more |
| Streaming | Yes | Yes |
| Sync + Async | Yes | Yes |
| File upload | Yes | Yes |
| Cookie handling | No | Yes |
| Thread-safe | Yes | Yes |

**When to use zerodep:** You need a lightweight HTTP client with no external dependencies, and your use case involves basic REST API consumption.

**When to use httpx:** You need HTTP/2 or cookie management.

## Benchmark

Benchmarked against `httpx`. Both libraries support connection pooling via session classes. One-off requests and session usage are comparable since both are network-bound.

See [HTTP Client Benchmark](../benchmarks/http.md) for detailed results.
