"""WebSocket echo server fixture for testing.

Provides session-scoped fixtures that start a threaded WebSocket echo server
using the ``websockets`` library. The server echoes back any text message and
supports ping/pong and close handshakes.
"""

from __future__ import annotations

import asyncio
import threading

import pytest


@pytest.fixture(scope="session")
def ws_echo_url():
    """Start a WebSocket echo server and yield its URL."""
    import websockets.server

    async def echo_handler(ws):
        try:
            async for msg in ws:
                await ws.send(msg)
        except websockets.exceptions.ConnectionClosedOK:
            pass
        except websockets.exceptions.ConnectionClosedError:
            pass

    loop = asyncio.new_event_loop()
    started = threading.Event()
    port_holder: list[int] = []

    async def run_server():
        async with websockets.server.serve(echo_handler, "127.0.0.1", 0) as server:
            sock = list(server.sockets)[0]
            port_holder.append(sock.getsockname()[1])
            started.set()
            await asyncio.Future()  # run forever

    def thread_target():
        loop.run_until_complete(run_server())

    thread = threading.Thread(target=thread_target, daemon=True)
    thread.start()
    started.wait(timeout=10)
    yield f"ws://127.0.0.1:{port_holder[0]}"
    loop.call_soon_threadsafe(loop.stop)


@pytest.fixture(scope="session")
def ws_custom_server_url():
    """Start a WebSocket server with custom behavior for testing.

    This server:
    - Echoes text messages prefixed with "echo:"
    - Responds to "ping-me" by sending a ping frame
    - Responds to "close-me" by initiating a close
    """
    import websockets.server

    async def handler(ws):
        try:
            async for msg in ws:
                if msg == "ping-me":
                    await ws.ping(b"server-ping")
                    await ws.send("ping-sent")
                elif msg == "close-me":
                    await ws.close(1000, "server closing")
                    return
                else:
                    await ws.send(f"echo:{msg}")
        except websockets.exceptions.ConnectionClosedOK:
            pass
        except websockets.exceptions.ConnectionClosedError:
            pass

    loop = asyncio.new_event_loop()
    started = threading.Event()
    port_holder: list[int] = []

    async def run_server():
        async with websockets.server.serve(handler, "127.0.0.1", 0) as server:
            sock = list(server.sockets)[0]
            port_holder.append(sock.getsockname()[1])
            started.set()
            await asyncio.Future()

    def thread_target():
        loop.run_until_complete(run_server())

    thread = threading.Thread(target=thread_target, daemon=True)
    thread.start()
    started.wait(timeout=10)
    yield f"ws://127.0.0.1:{port_holder[0]}"
    loop.call_soon_threadsafe(loop.stop)
