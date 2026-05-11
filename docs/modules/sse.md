# SSE Client

Zero-dependency Server-Sent Events (SSE) client with W3C-compliant parsing, auto-reconnection, and sync+async support -- stdlib only, Python 3.10+.

> **Replaces:** `sseclient-py`, `aiohttp-sse-client`, `httpx-sse`

## Overview

The SSE module provides a complete client for consuming [Server-Sent Events](https://html.spec.whatwg.org/multipage/server-sent-events.html) streams. It is designed in three layers so you can use just the parser or the full auto-reconnecting client.

| File | Description | Dependencies |
|------|-------------|--------------|
| `sse.py` | Pure Python implementation | None (stdlib only: `dataclasses`, `asyncio`, `time`, `os`) |

The high-level client (`SSEClient` / `AsyncSSEClient`) additionally uses the sibling `httpclient` module for HTTP transport.

## Features

- **W3C-compliant parsing** -- handles `event`, `data`, `id`, `retry` fields, comments, BOM stripping, and multi-line data
- **Three abstraction layers** -- standalone parser, iterator wrapper, full HTTP client
- **Auto-reconnection** -- configurable retry interval, max retries, and Last-Event-ID tracking
- **Sync + async** -- `EventSource` / `AsyncEventSource` and `SSEClient` / `AsyncSSEClient`
- **204 = stop** -- server returns HTTP 204 to signal graceful stream termination
- **LLM API ready** -- designed for consuming OpenAI, Anthropic, and Google streaming APIs

## How to Use in Your Project

Copy the single `.py` file into your project:

```bash
cp sse/sse.py your_project/
```

For the high-level client, also copy `httpclient/httpclient.py`:

```bash
cp httpclient/httpclient.py your_project/
```

Then import directly:

```python
from sse import connect, EventSource, SSEEvent
```

## Usage Examples

### High-Level Client (Auto-Connect + Reconnect)

```python
from sse import connect

with connect("https://api.example.com/events") as events:
    for event in events:
        print(event.event, event.data)
```

### Async Client

```python
import asyncio
from sse import async_connect

async def main():
    async with async_connect("https://api.example.com/events") as events:
        async for event in events:
            print(event.data)

asyncio.run(main())
```

### With Custom Headers (e.g. LLM API)

```python
from sse import connect

with connect(
    "https://api.openai.com/v1/chat/completions",
    headers={"Authorization": "Bearer sk-..."},
) as events:
    for event in events:
        if event.data == "[DONE]":
            break
        print(event.data)
```

### Low-Level Parser (No HTTP Dependency)

```python
from sse import EventSource

lines = [
    "event: greeting",
    "data: hello",
    "",
    "data: line 1",
    "data: line 2",
    "",
]
for event in EventSource(lines):
    print(event.event, repr(event.data))
    # "greeting" "hello"
    # "message" "line 1\nline 2"
```

### Async Low-Level Parser

```python
from sse import AsyncEventSource

async def parse_stream(async_line_source):
    async for event in AsyncEventSource(async_line_source):
        print(event.data)
```

### With httpclient Streaming Response

```python
from httpclient import get
from sse import EventSource

with get("https://api.example.com/events", stream=True) as r:
    for event in EventSource(r.iter_lines()):
        print(event.data)
```

### Reconnection Configuration

```python
from sse import connect

with connect(
    "https://api.example.com/events",
    retry_interval=5000,     # 5 seconds between reconnects
    max_retries=10,          # give up after 10 retries (-1 = unlimited)
    last_event_id="evt-42",  # resume from a known event ID
) as events:
    for event in events:
        print(event.data)
```

## Auto-Reconnection

The high-level client (`SSEClient` / `AsyncSSEClient`) automatically reconnects when the connection drops:

1. Opens a streaming GET with `Accept: text/event-stream`
2. Sends `Last-Event-ID` header if a previous event had an `id` field
3. Parses the stream; updates `last_event_id` and `retry_interval` from events
4. On connection loss, waits `retry_interval` ms then reconnects
5. Retry counter resets to 0 after each successful event delivery
6. HTTP 204 response means "stop reconnecting" (graceful termination)
7. Non-2xx response raises `SSEHTTPError`
8. Exceeding `max_retries` raises `SSEConnectionError`

## API Reference

### `SSEEvent`

Frozen dataclass representing a single Server-Sent Event.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `event` | `str` | `"message"` | Event type |
| `data` | `str` | `""` | Event payload (multiple `data:` lines joined with `\n`) |
| `id` | `str` | `""` | Last event ID (persists across events until changed) |
| `retry` | `int \| None` | `None` | Reconnection interval in milliseconds |

---

### `EventSource(lines)`

Sync SSE parser wrapping any `Iterable[str]` of lines.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `lines` | `Iterable[str]` | Line source (e.g. list of strings, file object, `response.iter_lines()`) |

**Yields:** `SSEEvent` objects.

---

### `AsyncEventSource(lines)`

Async SSE parser wrapping any `AsyncIterable[str]` of lines.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `lines` | `AsyncIterable[str]` | Async line source |

**Yields:** `SSEEvent` objects.

---

### `SSEClient(url, **kwargs)` / `connect(url, **kwargs)`

Synchronous SSE client with auto-reconnection. Use as a context manager.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `url` | `str` | -- | SSE endpoint URL |
| `headers` | `dict[str, str] \| None` | `None` | Extra HTTP headers |
| `timeout` | `float` | `30.0` | HTTP request timeout in seconds |
| `retry_interval` | `int` | `3000` | Reconnection interval in milliseconds (per W3C spec) |
| `max_retries` | `int` | `-1` | Max reconnection attempts (`-1` = unlimited) |
| `verify` | `bool` | `True` | Verify TLS certificates |
| `last_event_id` | `str` | `""` | Initial Last-Event-ID for resumption |

**Methods:**

| Method | Description |
|--------|-------------|
| `__iter__()` | Iterate over `SSEEvent` objects |
| `close()` | Close the connection |

---

### `AsyncSSEClient(url, **kwargs)` / `async_connect(url, **kwargs)`

Asynchronous SSE client with auto-reconnection. Use as an async context manager.

Same parameters as `SSEClient`. Uses `async for` and `await close()`.

---

### Exceptions

| Exception | Description |
|-----------|-------------|
| `SSEError` | Base exception for all SSE errors |
| `SSEConnectionError` | Raised when `max_retries` is exhausted. Attributes: `url`, `retries`, `last_error` |
| `SSEHTTPError` | Raised on non-2xx HTTP response (other than 204). Attributes: `status_code`, `url` |

## Comparison with httpx-sse

| Feature | zerodep SSE | httpx-sse |
|---------|-------------|-----------|
| Dependencies | None (stdlib only) | httpx |
| Standalone parser | Yes (`EventSource`) | No (requires `httpx.Response`) |
| Auto-reconnection | Yes (built-in) | No |
| Last-Event-ID tracking | Yes | No |
| Sync + async | Yes | Yes |
| 204 graceful stop | Yes | No |
| W3C parsing | Yes | Yes |
| Parsing speed | ~1.5 ms / 1000 events | ~1.4 ms / 1000 events |
| Implementation | Single file (~380 lines) | Package (multiple files) |

**When to use zerodep:** You need a self-contained SSE client with auto-reconnection and zero dependencies, or you want a standalone parser without coupling to any HTTP library.

**When to use httpx-sse:** You are already using httpx and want a thin extension for SSE parsing.

## Benchmark

Benchmarked against `httpx-sse` across small, medium, and large event streams.

See [SSE Client Benchmark](../benchmarks/sse.md) for detailed results.
