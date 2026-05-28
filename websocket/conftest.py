"""WebSocket echo server fixture for testing.

Provides session-scoped fixtures with a stdlib-only WebSocket echo server.
No third-party dependencies — uses asyncio.start_server and the protocol
helpers from our own websocket module.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import struct
import threading

import pytest

# Reuse protocol constants/helpers from our module
from websocket import _WS_GUID, _make_frame, _mask_payload

_OPCODE_TEXT = 0x1
_OPCODE_CLOSE = 0x8
_OPCODE_PING = 0x9
_OPCODE_PONG = 0xA


async def _ws_accept(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Perform WebSocket server-side handshake."""
    request = b""
    while b"\r\n\r\n" not in request:
        chunk = await reader.read(4096)
        if not chunk:
            writer.close()
            return None
        request += chunk

    # Extract Sec-WebSocket-Key
    key = None
    for line in request.decode(errors="replace").split("\r\n"):
        if line.lower().startswith("sec-websocket-key:"):
            key = line.split(":", 1)[1].strip()
            break

    if not key:
        writer.close()
        return None

    accept = base64.b64encode(hashlib.sha1((key + _WS_GUID).encode()).digest()).decode()
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n"
        "\r\n"
    )
    writer.write(response.encode())
    await writer.drain()
    return True


async def _ws_read_frame(
    reader: asyncio.StreamReader,
) -> tuple[int, bytes] | None:
    """Read one WebSocket frame from the client. Returns (opcode, payload)."""
    header = await reader.readexactly(2)
    opcode = header[0] & 0x0F
    is_masked = bool(header[1] & 0x80)
    length = header[1] & 0x7F

    if length == 126:
        length = struct.unpack(">H", await reader.readexactly(2))[0]
    elif length == 127:
        length = struct.unpack(">Q", await reader.readexactly(8))[0]

    if is_masked:
        mask_key = await reader.readexactly(4)
        raw = await reader.readexactly(length)
        payload = _mask_payload(mask_key, raw)
    else:
        payload = await reader.readexactly(length)

    return opcode, payload


async def _ws_send(writer: asyncio.StreamWriter, opcode: int, payload: bytes):
    """Send a WebSocket frame (server→client, no masking)."""
    writer.write(_make_frame(opcode, payload, mask=False))
    await writer.drain()


async def _echo_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Handle a single WebSocket connection: echo all text messages."""
    if not await _ws_accept(reader, writer):
        return
    try:
        while True:
            result = await _ws_read_frame(reader)
            if result is None:
                break
            opcode, payload = result

            if opcode == _OPCODE_TEXT:
                await _ws_send(writer, _OPCODE_TEXT, payload)
            elif opcode == _OPCODE_PING:
                await _ws_send(writer, _OPCODE_PONG, payload)
            elif opcode == _OPCODE_CLOSE:
                # Echo the close frame back
                await _ws_send(writer, _OPCODE_CLOSE, payload)
                break
    except (asyncio.IncompleteReadError, ConnectionError, OSError):
        pass
    finally:
        writer.close()


async def _custom_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Handle a single WebSocket connection with custom behavior.

    - Echoes text with "echo:" prefix
    - "ping-me" → sends a ping frame + "ping-sent" text
    - "close-me" → initiates server-side close
    """
    if not await _ws_accept(reader, writer):
        return
    try:
        while True:
            result = await _ws_read_frame(reader)
            if result is None:
                break
            opcode, payload = result

            if opcode == _OPCODE_TEXT:
                text = payload.decode()
                if text == "ping-me":
                    await _ws_send(writer, _OPCODE_PING, b"server-ping")
                    await _ws_send(writer, _OPCODE_TEXT, b"ping-sent")
                elif text == "close-me":
                    close_payload = struct.pack(">H", 1000) + b"server closing"
                    await _ws_send(writer, _OPCODE_CLOSE, close_payload)
                    break
                else:
                    await _ws_send(writer, _OPCODE_TEXT, f"echo:{text}".encode())
            elif opcode == _OPCODE_PING:
                await _ws_send(writer, _OPCODE_PONG, payload)
            elif opcode == _OPCODE_CLOSE:
                await _ws_send(writer, _OPCODE_CLOSE, payload)
                break
    except (asyncio.IncompleteReadError, ConnectionError, OSError):
        pass
    finally:
        writer.close()


def _start_ws_server(handler):
    """Start an async WebSocket server in a background thread, return its URL."""
    loop = asyncio.new_event_loop()
    started = threading.Event()
    server_holder = {}

    async def start():
        server = await asyncio.start_server(handler, "127.0.0.1", 0)
        server_holder["server"] = server
        server_holder["port"] = server.sockets[0].getsockname()[1]
        started.set()

    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start())
        loop.run_forever()
        loop.close()

    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    started.wait(timeout=10)
    return (
        f"ws://127.0.0.1:{server_holder['port']}",
        loop,
        server_holder["server"],
        thread,
    )


def _stop_ws_server(loop, server, thread):
    """Stop the background WebSocket server cleanly."""

    async def shutdown():
        server.close()
        await server.wait_closed()

    future = asyncio.run_coroutine_threadsafe(shutdown(), loop)
    future.result(timeout=10)
    loop.call_soon_threadsafe(loop.stop)
    thread.join(timeout=10)


@pytest.fixture(scope="session")
def ws_echo_url():
    """Start a stdlib WebSocket echo server and yield its URL."""
    url, loop, server, thread = _start_ws_server(_echo_handler)
    yield url
    _stop_ws_server(loop, server, thread)


@pytest.fixture(scope="session")
def ws_custom_server_url():
    """Start a WebSocket server with custom behavior for testing."""
    url, loop, server, thread = _start_ws_server(_custom_handler)
    yield url
    _stop_ws_server(loop, server, thread)
