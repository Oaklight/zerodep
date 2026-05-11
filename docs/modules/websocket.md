# WebSocket Client

Zero-dependency RFC 6455 WebSocket client with sync + async support -- stdlib only, Python 3.10+.

> **Replaces:** `websocket-client`, `websockets`

## Overview

The websocket module provides synchronous and asynchronous WebSocket clients for `ws://` and `wss://` connections. It implements the core WebSocket protocol including text frames, ping/pong, close handshake, and client-side masking. Designed as a drop-in alternative to the `websockets` library for projects that need WebSocket communication without third-party dependencies.

| File | Description | Dependencies |
|------|-------------|--------------|
| `websocket.py` | Pure Python implementation | None (stdlib only: `asyncio`, `socket`, `ssl`, `hashlib`, `struct`) |

## Features

- **RFC 6455 compliant** -- full WebSocket protocol with upgrade handshake, frame encoding/decoding, and masking
- **Sync + async clients** -- `WebSocketClient` and `AsyncWebSocketClient` with identical APIs
- **TLS support** -- `wss://` connections with configurable certificate verification
- **Ping/pong** -- automatic pong response on receiving ping frames
- **Close handshake** -- proper close frame exchange with status codes and reasons
- **Custom headers** -- pass extra headers in the upgrade request (auth tokens, cookies, etc.)
- **Subprotocol negotiation** -- request and detect accepted subprotocols
- **Timeout control** -- configurable timeouts for connect, send, and receive operations
- **Context manager** -- `with` / `async with` for automatic connect and close

## How to Use in Your Project

Copy the single `.py` file into your project:

```bash
cp websocket/websocket.py your_project/
```

Then import directly:

```python
from websocket import WebSocketClient, AsyncWebSocketClient
```

## Usage Examples

### Basic Sync Client

```python
from websocket import WebSocketClient

with WebSocketClient("ws://localhost:9222/") as ws:
    ws.send("hello")
    response = ws.recv()
    print(response)
```

### Basic Async Client

```python
import asyncio
from websocket import AsyncWebSocketClient

async def main():
    async with AsyncWebSocketClient("wss://example.com/ws") as ws:
        await ws.send('{"type": "subscribe"}')
        data = await ws.recv()
        print(data)

asyncio.run(main())
```

### JSON-RPC over WebSocket

```python
import json
from websocket import WebSocketClient

with WebSocketClient("ws://localhost:9222/devtools/page/123") as ws:
    # Send a CDP command
    ws.send(json.dumps({
        "id": 1,
        "method": "Page.navigate",
        "params": {"url": "https://example.com"}
    }))
    result = json.loads(ws.recv())
    print(result)
```

### Custom Headers

```python
from websocket import WebSocketClient

headers = {
    "Authorization": "Bearer my-token",
    "X-Custom-Header": "value",
}
with WebSocketClient("ws://localhost:8080/ws", headers=headers) as ws:
    ws.send("authenticated message")
    print(ws.recv())
```

### Receive Timeout

```python
from websocket import WebSocketClient, WebSocketTimeoutError

with WebSocketClient("ws://localhost:8080/ws") as ws:
    ws.send("ping")
    try:
        response = ws.recv(timeout=5.0)
    except WebSocketTimeoutError:
        print("No response within 5 seconds")
```

### Manual Connect / Close

```python
from websocket import WebSocketClient

ws = WebSocketClient("ws://localhost:8080/ws")
ws.connect(timeout=10)

ws.send("hello")
print(ws.recv())

ws.close(code=1000, reason="done")
```

### Secure Connection (WSS)

```python
from websocket import WebSocketClient

# With certificate verification (default)
with WebSocketClient("wss://echo.websocket.org") as ws:
    ws.send("secure hello")
    print(ws.recv())

# Without certificate verification (e.g., self-signed certs)
ws = WebSocketClient("wss://localhost:9443/ws")
ws.connect(verify=False)
```

## API Reference

### `WebSocketClient(url, *, headers=None, subprotocols=None)`

Synchronous WebSocket client.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | -- | WebSocket URL (`ws://` or `wss://`) |
| `headers` | `dict[str, str] \| None` | `None` | Extra headers for the upgrade request |
| `subprotocols` | `list[str] \| None` | `None` | Subprotocols to negotiate |

| Method | Description |
|--------|-------------|
| `connect(*, timeout=30.0, verify=True)` | Open the WebSocket connection |
| `send(data: str)` | Send a text message |
| `recv(*, timeout=None) -> str` | Receive a text message |
| `ping(data=b"")` | Send a ping frame |
| `close(code=1000, reason="")` | Close the connection with a close handshake |

| Property | Type | Description |
|----------|------|-------------|
| `connected` | `bool` | Whether the connection is active |
| `accepted_subprotocol` | `str \| None` | The subprotocol accepted by the server |

---

### `AsyncWebSocketClient(url, *, headers=None, subprotocols=None)`

Asynchronous WebSocket client. Same constructor parameters as `WebSocketClient`.

| Method | Description |
|--------|-------------|
| `await connect(*, timeout=30.0, verify=True)` | Open the WebSocket connection |
| `await send(data: str)` | Send a text message |
| `await recv(*, timeout=None) -> str` | Receive a text message |
| `await ping(data=b"")` | Send a ping frame |
| `await close(code=1000, reason="")` | Close the connection |

---

### Exceptions

| Exception | Description |
|-----------|-------------|
| `WebSocketError` | Base exception for all websocket operations |
| `WebSocketConnectionError` | Connection failures (TCP connect, handshake reject, close by server) |
| `WebSocketTimeoutError` | Operation timed out |
| `WebSocketProtocolError` | Protocol violations (bad frame, unsupported opcode) |

---

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `DEFAULT_TIMEOUT` | `30.0` | Default timeout for all operations (seconds) |

## Comparison with websockets

| Feature | zerodep websocket | websockets |
|---------|-------------------|------------|
| Dependencies | None (stdlib only) | None |
| Sync client | `WebSocketClient` | `websockets.sync.client.connect()` |
| Async client | `AsyncWebSocketClient` | `websockets.connect()` |
| Protocol | Text frames only | Text + binary + continuation |
| TLS support | Yes (`wss://`) | Yes (`wss://`) |
| Ping/pong | Auto pong on ping | Auto pong on ping |
| Close handshake | Full close exchange | Full close exchange |
| Server support | No | Yes |
| Compression | No | permessage-deflate |
| File size | ~1000 lines | ~10,000+ lines |
| Install size | Single file copy | pip install |

**When to use zerodep:** You need a lightweight WebSocket client with zero dependencies for CDP communication, JSON-RPC, or simple message exchange.

**When to use websockets:** You need a full-featured WebSocket server/client with binary frames, compression, or advanced protocol extensions.

## Benchmark

Benchmarked against the `websockets` library across JSON-RPC round-trips (~200B), large HTML payload transfer (~50KB), burst messaging (100 messages), and connection setup overhead.

See [WebSocket Benchmark](../benchmarks/websocket.md) for detailed results.
