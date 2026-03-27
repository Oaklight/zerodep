# httpclient Streaming Response Implementation Plan

## Overview

Add `stream=True` parameter to request functions. When enabled, return `StreamingResponse` instead of `Response`, holding the connection open for incremental body consumption. Prerequisite for SSE support.

## New Components

### `StreamingResponse` class (~150 lines)

Serves both sync and async paths. Created via `_from_sync()` / `_from_async()` class methods.

**Sync iteration:**
- `iter_bytes(chunk_size=4096)` — yields body chunks
- `iter_lines()` — yields decoded lines (for SSE)
- `read()` — consume entire stream into bytes

**Async iteration:**
- `aiter_bytes(chunk_size=4096)` — async yields body chunks
- `aiter_lines()` — async yields decoded lines
- `aread()` — async consume entire stream

**Shared:**
- `status_code`, `headers`, `url`, `ok`, `raise_for_status()`
- Context manager (`with`/`async with`) for cleanup
- `close()` / `aclose()`

### `_async_read_response_headers()` (~25 lines)

Reads HTTP status + headers from `asyncio.StreamReader` without consuming body. Used by async streaming path.

## Changes to Existing Functions

### `_sync_request` — add `stream` parameter

When `stream=True`: follow redirects normally, but on final response don't `resp.read()` or `conn.close()`. Return `StreamingResponse._from_sync(status, headers, url, resp, conn)`.

Restructure `try/finally` to use a `close_conn` flag so connection is NOT closed when StreamingResponse takes ownership.

### `_async_request` — add `stream` parameter

When `stream=True`: use `_async_read_response_headers()` instead of `reader.read(10MB)`. If redirect, drain body and close. If final response, return `StreamingResponse._from_async(...)`.

### `Client.request` / `AsyncClient.request`

Skip lock for streaming requests (StreamingResponse owns an independent connection).

## Async Body Framing (manual)

Async path does raw socket I/O, must handle body framing in `_async_read_body_chunk()`:
1. **Chunked TE**: Read chunk-size line (hex), read chunk data, strip `\r\n`
2. **Content-Length**: Track remaining bytes
3. **Neither**: Read until EOF (connection-close framing)

Sync path: `http.client.HTTPResponse.read(amt)` handles this transparently.

## API Examples

```python
# Sync
with get(url, stream=True) as r:
    for chunk in r.iter_bytes():
        process(chunk)

# Sync lines (SSE-ready)
with get(url, stream=True) as r:
    for line in r.iter_lines():
        handle(line)

# Async
async with await async_get(url, stream=True) as r:
    async for chunk in r.aiter_bytes():
        await process(chunk)
```

## Key Design Decisions

- **Redirects**: Followed eagerly before entering streaming mode
- **Thread safety**: Lock NOT held during streaming; each StreamingResponse has independent connection
- **No context manager**: `__del__` emits `ResourceWarning` as safety net
- **Content-Encoding**: Not handled (consistent with non-streaming behavior)
- **Timeout**: Socket timeout applies per `read()` call (sync); `asyncio.wait_for` per read (async)

## Estimated ~360 lines new/modified code
