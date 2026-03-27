# HTTP Client

Zero-dependency synchronous and asynchronous HTTP/1.1 REST client built entirely on the Python standard library.

## Overview

`httpclient.py` is a single-file HTTP client that supports both sync and async workflows. It requires **Python 3.10+** and has **no pip dependencies**.

- **Sync mode** uses `http.client` from the standard library.
- **Async mode** uses `asyncio` streams with a hand-written HTTP/1.1 protocol implementation.
- **Thread-safe** by design: each request creates its own connection. Session classes use locks internally.

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

!!! note "No Connection Pooling"
    Unlike httpx or requests, each request creates a new TCP connection. This keeps the implementation simple and dependency-free, at the cost of some overhead for repeated requests to the same host.

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
)
```

Supports context manager (`with` statement). Methods: `get`, `post`, `put`, `patch`, `delete`, `head`, `options`, `request`.

Thread-safe: uses a `threading.Lock` internally.

### AsyncClient Class

```python
AsyncClient(
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    max_redirects: int = 10,
    verify: bool = True,
)
```

Supports async context manager (`async with` statement). Methods: `get`, `post`, `put`, `patch`, `delete`, `head`, `options`, `request`.

Uses an `asyncio.Lock` internally for safe concurrent access from the same client instance.

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
| Connection pooling | No | Yes |
| Streaming | Yes | Yes |
| Sync + Async | Yes | Yes |
| File upload | Yes | Yes |
| Cookie handling | No | Yes |
| Thread-safe | Yes | Yes |

**When to use zerodep:** You need a lightweight HTTP client with no external dependencies, and your use case involves basic REST API consumption.

**When to use httpx:** You need HTTP/2, connection pooling, or cookie management.

## Benchmark

Benchmarked against `httpx`. One-off requests are slower (no connection pooling), but session/async usage is comparable since both become network-bound.

See [HTTP Client Benchmark](../benchmarks/http.md) for detailed results.
