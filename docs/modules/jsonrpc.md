# JSON-RPC

JSON-RPC 2.0 protocol implementation -- zero dependencies, stdlib only, Python 3.10+.

> **Replaces:** `jsonrpclib`, `jsonrpcserver`, `python-jsonrpc`

## Overview

The JSON-RPC module provides a complete [JSON-RPC 2.0](https://www.jsonrpc.org/specification) implementation including core data types, an exception hierarchy, a method dispatcher with streaming support, and an async transport layer for newline-delimited JSON streams. It serves as the shared protocol foundation for the [A2A](a2a.md) and [ACP](acp.md) agent protocol modules.

| File | Description | Dependencies |
|------|-------------|--------------|
| `jsonrpc.py` | Pure Python JSON-RPC 2.0 implementation | None (stdlib only) |

Five layers are provided:

- **Core types:** `JSONRPCError`, `JSONRPCRequest`, `JSONRPCResponse` dataclasses with serialization
- **Exception:** `JSONRPCException` wrapping `JSONRPCError` for control flow
- **ID generation:** Thread-safe auto-incrementing request ID counter
- **Dispatcher:** Method routing with automatic error handling and streaming support
- **Async transport:** Newline-delimited JSON-RPC over `asyncio` streams

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp jsonrpc/jsonrpc.py your_project/
```

Then import directly:

```python
from jsonrpc import JSONRPCDispatcher, JSONRPCRequest, JSONRPCResponse
```

## API Reference

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `JSONRPC_VERSION` | `"2.0"` | Protocol version string. |
| `PARSE_ERROR` | `-32700` | Invalid JSON was received. |
| `INVALID_REQUEST` | `-32600` | The JSON is not a valid request. |
| `METHOD_NOT_FOUND` | `-32601` | The method does not exist. |
| `INVALID_PARAMS` | `-32602` | Invalid method parameters. |
| `INTERNAL_ERROR` | `-32603` | Internal JSON-RPC error. |

---

### `class JSONRPCError`

A JSON-RPC 2.0 error object (dataclass).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `code` | `int` | `-32603` | Numeric error code. |
| `message` | `str` | `"Internal error"` | Human-readable error message. |
| `data` | `Any` | `None` | Optional additional error data. |

**Methods:**

- `to_dict() -> dict` -- Serialize to a dictionary. Omits `data` when `None`.
- `from_dict(raw) -> JSONRPCError` -- Deserialize from a dictionary (classmethod).

---

### `class JSONRPCRequest`

A JSON-RPC 2.0 request object (dataclass).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `method` | `str` | `""` | The RPC method name. |
| `params` | `dict[str, Any] \| None` | `None` | Method parameters. |
| `id` | `str \| int \| None` | `None` | Request identifier (`None` for notifications). |
| `jsonrpc` | `str` | `"2.0"` | Protocol version. |

**Properties:**

- `is_notification -> bool` -- `True` if `id` is `None`.

**Methods:**

- `to_dict() -> dict` -- Serialize to a dictionary. Omits `id` and `params` when `None`.
- `from_dict(d) -> JSONRPCRequest` -- Deserialize from a dictionary (classmethod).

---

### `class JSONRPCResponse`

A JSON-RPC 2.0 response object (dataclass). Exactly one of `result` or `error` should be set.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `str \| int \| None` | `None` | Matching request identifier. |
| `result` | `Any` | `None` | Successful result payload. |
| `error` | `JSONRPCError \| None` | `None` | Error details on failure. |
| `jsonrpc` | `str` | `"2.0"` | Protocol version. |

**Methods:**

- `to_dict() -> dict` -- Serialize to a dictionary.
- `from_dict(d) -> JSONRPCResponse` -- Deserialize from a dictionary (classmethod).
- `success(request_id, result) -> JSONRPCResponse` -- Create a successful response (classmethod).
- `from_error(request_id, error) -> JSONRPCResponse` -- Create an error response from a `JSONRPCError`, `JSONRPCException`, or duck-typed error object (classmethod).

---

### `class JSONRPCException`

Exception wrapper around a `JSONRPCError`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `error` | `JSONRPCError` | The underlying error object. |

The string representation is the error message.

---

### `next_id() -> int`

Return the next auto-incrementing request id. Thread-safe (backed by `itertools.count`).

---

### `class JSONRPCDispatcher`

Routes JSON-RPC method calls to registered handler functions. Supports both regular and streaming (generator) handlers.

**Methods:**

#### `register(method) -> decorator`

Decorator to register a handler for the given method name.

```python
@dispatcher.register("echo")
def handle_echo(params):
    return params
```

#### `dispatch(request) -> JSONRPCResponse | Iterator[JSONRPCResponse]`

Dispatch a parsed request to its handler. Returns a single response or, for generator handlers, an iterator of responses.

- `JSONRPCException` raised by handlers is caught and converted to an error response.
- Other exceptions produce an `INTERNAL_ERROR` response.

---

### `class JSONRPCTransport`

Async JSON-RPC 2.0 transport over newline-delimited JSON streams.

```python
transport = JSONRPCTransport(reader, writer)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `await read_message()` | Read the next JSON object. Returns `None` on EOF. Skips blank lines and malformed JSON. |
| `await write_message(msg)` | Write a JSON object followed by `\n`. |
| `await send_request(method, params, req_id)` | Build and send a request (auto-generates `id` if not provided). |
| `await send_notification(method, params)` | Send a notification (no `id`). |
| `await send_result(req_id, result)` | Send a success response. |
| `await send_error(req_id, error)` | Send an error response. |
| `await close()` | Close the writer stream (idempotent). |

**Properties:**

- `is_closed -> bool` -- Whether the transport has been closed.

## Usage Examples

### Basic Dispatcher

```python
from jsonrpc import JSONRPCDispatcher, JSONRPCRequest

dispatcher = JSONRPCDispatcher()

@dispatcher.register("add")
def handle_add(params):
    return params["a"] + params["b"]

req = JSONRPCRequest(method="add", params={"a": 2, "b": 3}, id=1)
resp = dispatcher.dispatch(req)
print(resp.result)  # 5
```

### Streaming Handler

```python
from jsonrpc import JSONRPCDispatcher, JSONRPCRequest

dispatcher = JSONRPCDispatcher()

@dispatcher.register("count")
def handle_count(params):
    for i in range(params["n"]):
        yield {"index": i}

req = JSONRPCRequest(method="count", params={"n": 3}, id=1)
for resp in dispatcher.dispatch(req):
    print(resp.result)
# {"index": 0}
# {"index": 1}
# {"index": 2}
```

### Error Handling

```python
from jsonrpc import (
    JSONRPCDispatcher,
    JSONRPCError,
    JSONRPCException,
    JSONRPCRequest,
)

dispatcher = JSONRPCDispatcher()

@dispatcher.register("fail")
def handle_fail(params):
    raise JSONRPCException(
        JSONRPCError(code=-32001, message="Custom error", data={"reason": "demo"})
    )

resp = dispatcher.dispatch(JSONRPCRequest(method="fail", id=1))
print(resp.error.code)     # -32001
print(resp.error.message)  # "Custom error"
```

### Async Transport

```python
import asyncio
from jsonrpc import JSONRPCTransport

async def main():
    reader, writer = await asyncio.open_connection("localhost", 8080)
    transport = JSONRPCTransport(reader, writer)

    # Send a request
    await transport.send_request("ping", {"timestamp": 12345})

    # Read the response
    response = await transport.read_message()
    print(response)

    await transport.close()
```

### Serialization Round-Trip

```python
import json
from jsonrpc import JSONRPCRequest

req = JSONRPCRequest(method="echo", params={"msg": "hi"}, id=7)
wire = json.dumps(req.to_dict())
restored = JSONRPCRequest.from_dict(json.loads(wire))
assert restored.method == "echo"
assert restored.params == {"msg": "hi"}
```

## Notes and Caveats

!!! info "Shared Foundation"
    This module is used internally by the [A2A](a2a.md) and [ACP](acp.md) protocol modules via zerodep's sibling import mechanism. When copying modules that depend on `jsonrpc`, use the `zerodep` CLI tool to automatically resolve dependencies.

- **Python version:** Requires Python 3.10+ (uses `X | Y` union type hint syntax).
- **Thread safety:** `next_id()` is thread-safe (uses `itertools.count`). The dispatcher itself is not thread-safe for concurrent registration, but concurrent dispatching is safe after setup.
- **Streaming:** Generator handlers are wrapped so each yielded value becomes a separate `JSONRPCResponse`. Exceptions mid-stream produce a final error response.
- **Transport:** Uses newline-delimited JSON (`\n`-separated). Each message must be a single line.

## Benchmark

Benchmarked against `jsonrpcserver` for end-to-end dispatch performance (JSON string in, JSON string out).

See [JSON-RPC Benchmark](../benchmarks/jsonrpc.md) for detailed results.
