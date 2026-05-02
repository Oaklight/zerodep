"""Mock CDP server and optional real browser fixtures for testing.

Provides a session-scoped mock CDP server that simulates basic Chrome
DevTools Protocol interactions over WebSocket. Uses stdlib-only — no
third-party WebSocket server library needed.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import http.server
import json
import os
import struct
import sys
import threading
import uuid

import pytest

# Reuse protocol helpers from sibling websocket module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "websocket"))
from websocket import _WS_GUID, _make_frame, _mask_payload  # noqa: E402

_OPCODE_TEXT = 0x1
_OPCODE_CLOSE = 0x8
_OPCODE_PING = 0x9
_OPCODE_PONG = 0xA


class _MockCDPHandler:
    """Simulates a minimal CDP server.

    Handles:
    - Target.createTarget / Target.attachToTarget / Target.closeTarget
    - Page.enable / Page.navigate (fires Page.loadEventFired)
    - Runtime.evaluate (returns expression as string value)
    """

    def __init__(self):
        self._targets: dict[str, dict] = {}  # target_id -> info
        self._sessions: dict[str, str] = {}  # session_id -> target_id

    def handle_message(self, raw: str) -> list[str]:
        """Process a CDP message and return response(s).

        Returns a list of JSON strings (response + possible events).
        """
        msg = json.loads(raw)
        cmd_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})
        session_id = msg.get("sessionId")

        responses: list[str] = []

        if method == "Target.createTarget":
            target_id = f"target-{uuid.uuid4().hex[:8]}"
            url = params.get("url", "about:blank")
            self._targets[target_id] = {
                "url": url,
                "loaded": False,
            }
            responses.append(
                json.dumps({"id": cmd_id, "result": {"targetId": target_id}})
            )

        elif method == "Target.attachToTarget":
            target_id = params.get("targetId", "")
            sid = f"session-{uuid.uuid4().hex[:8]}"
            self._sessions[sid] = target_id
            responses.append(json.dumps({"id": cmd_id, "result": {"sessionId": sid}}))
            # Also send Target.attachedToTarget event
            responses.append(
                json.dumps(
                    {
                        "method": "Target.attachedToTarget",
                        "params": {
                            "sessionId": sid,
                            "targetInfo": {
                                "targetId": target_id,
                                "type": "page",
                                "url": self._targets.get(target_id, {}).get("url", ""),
                            },
                        },
                    }
                )
            )

        elif method == "Target.closeTarget":
            target_id = params.get("targetId", "")
            self._targets.pop(target_id, None)
            # Remove associated sessions
            self._sessions = {k: v for k, v in self._sessions.items() if v != target_id}
            responses.append(json.dumps({"id": cmd_id, "result": {"success": True}}))

        elif method == "Page.enable":
            responses.append(json.dumps({"id": cmd_id, "result": {}}))
            if session_id:
                responses[-1] = json.dumps(
                    {"id": cmd_id, "result": {}, "sessionId": session_id}
                )

        elif method == "Page.navigate":
            url = params.get("url", "")
            frame_id = f"frame-{uuid.uuid4().hex[:8]}"
            loader_id = f"loader-{uuid.uuid4().hex[:8]}"

            resp = {
                "id": cmd_id,
                "result": {"frameId": frame_id, "loaderId": loader_id},
            }
            if session_id:
                resp["sessionId"] = session_id
            responses.append(json.dumps(resp))

            # Update target URL
            if session_id and session_id in self._sessions:
                tid = self._sessions[session_id]
                if tid in self._targets:
                    self._targets[tid]["url"] = url
                    self._targets[tid]["loaded"] = True

            # Fire Page.loadEventFired event
            event = {
                "method": "Page.loadEventFired",
                "params": {"timestamp": 12345.678},
            }
            if session_id:
                event["sessionId"] = session_id
            responses.append(json.dumps(event))

        elif method == "Runtime.evaluate":
            expression = params.get("expression", "")

            # Simulate simple evaluations
            if "innerText" in expression:
                value = "Mock page content for testing"
            elif "outerHTML" in expression:
                value = "<html><body>Mock page content for testing</body></html>"
            elif "throw" in expression.lower():
                resp = {
                    "id": cmd_id,
                    "result": {
                        "result": {"type": "object", "subtype": "error"},
                        "exceptionDetails": {
                            "text": "Uncaught Error: test error",
                            "exceptionId": 1,
                        },
                    },
                }
                if session_id:
                    resp["sessionId"] = session_id
                responses.append(json.dumps(resp))
                return responses
            else:
                value = f"eval:{expression}"

            result_obj = {"type": "string", "value": value}
            resp = {"id": cmd_id, "result": {"result": result_obj}}
            if session_id:
                resp["sessionId"] = session_id
            responses.append(json.dumps(resp))

        elif method == "Network.setUserAgentOverride":
            resp = {"id": cmd_id, "result": {}}
            if session_id:
                resp["sessionId"] = session_id
            responses.append(json.dumps(resp))

        else:
            # Unknown method — return empty result
            resp = {"id": cmd_id, "result": {}}
            if session_id:
                resp["sessionId"] = session_id
            responses.append(json.dumps(resp))

        return responses


# ── Stdlib WebSocket server helpers ──────────────────────────────────────


async def _ws_accept(reader, writer):
    """Perform server-side WebSocket handshake."""
    request = b""
    while b"\r\n\r\n" not in request:
        chunk = await reader.read(4096)
        if not chunk:
            writer.close()
            return False
        request += chunk

    key = None
    for line in request.decode(errors="replace").split("\r\n"):
        if line.lower().startswith("sec-websocket-key:"):
            key = line.split(":", 1)[1].strip()
            break

    if not key:
        writer.close()
        return False

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


async def _ws_read_frame(reader) -> tuple[int, bytes] | None:
    """Read one WebSocket frame. Returns (opcode, payload)."""
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


async def _ws_send(writer, opcode: int, payload: bytes):
    """Send a WebSocket frame (server→client, no masking)."""
    writer.write(_make_frame(opcode, payload, mask=False))
    await writer.drain()


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def cdp_mock_url():
    """Start a mock CDP server and yield its WebSocket URL."""
    handler = _MockCDPHandler()

    async def ws_handler(reader, writer):
        if not await _ws_accept(reader, writer):
            return
        try:
            while True:
                result = await _ws_read_frame(reader)
                if result is None:
                    break
                opcode, payload = result

                if opcode == _OPCODE_TEXT:
                    responses = handler.handle_message(payload.decode())
                    for resp in responses:
                        await _ws_send(writer, _OPCODE_TEXT, resp.encode())
                elif opcode == _OPCODE_PING:
                    await _ws_send(writer, _OPCODE_PONG, payload)
                elif opcode == _OPCODE_CLOSE:
                    await _ws_send(writer, _OPCODE_CLOSE, payload)
                    break
        except (asyncio.IncompleteReadError, ConnectionError, OSError):
            pass
        finally:
            writer.close()

    loop = asyncio.new_event_loop()
    started = threading.Event()
    port_holder: list[int] = []

    async def run_server():
        server = await asyncio.start_server(ws_handler, "127.0.0.1", 0)
        port_holder.append(server.sockets[0].getsockname()[1])
        started.set()
        async with server:
            await server.serve_forever()

    thread = threading.Thread(
        target=loop.run_until_complete, args=(run_server(),), daemon=True
    )
    thread.start()
    started.wait(timeout=10)
    yield f"ws://127.0.0.1:{port_holder[0]}/devtools/browser/mock"
    loop.call_soon_threadsafe(loop.stop)


@pytest.fixture(scope="session")
def cdp_json_version_url():
    """Start a mock CDP server with /json/version HTTP endpoint for auto-discovery.

    Returns just the host:port URL without path, so the client must
    auto-discover via /json/version.
    """
    handler = _MockCDPHandler()

    # Start WS server
    async def ws_handler(reader, writer):
        if not await _ws_accept(reader, writer):
            return
        try:
            while True:
                result = await _ws_read_frame(reader)
                if result is None:
                    break
                opcode, payload = result

                if opcode == _OPCODE_TEXT:
                    responses = handler.handle_message(payload.decode())
                    for resp in responses:
                        await _ws_send(writer, _OPCODE_TEXT, resp.encode())
                elif opcode == _OPCODE_PING:
                    await _ws_send(writer, _OPCODE_PONG, payload)
                elif opcode == _OPCODE_CLOSE:
                    await _ws_send(writer, _OPCODE_CLOSE, payload)
                    break
        except (asyncio.IncompleteReadError, ConnectionError, OSError):
            pass
        finally:
            writer.close()

    ws_loop = asyncio.new_event_loop()
    ws_started = threading.Event()
    ws_port_holder: list[int] = []

    async def run_ws_server():
        server = await asyncio.start_server(ws_handler, "127.0.0.1", 0)
        ws_port_holder.append(server.sockets[0].getsockname()[1])
        ws_started.set()
        async with server:
            await server.serve_forever()

    ws_thread = threading.Thread(
        target=ws_loop.run_until_complete,
        args=(run_ws_server(),),
        daemon=True,
    )
    ws_thread.start()
    ws_started.wait(timeout=10)

    # Start HTTP server for /json/version
    class JsonVersionHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # noqa: A002
            pass

        def do_GET(self):
            if self.path == "/json/version":
                ws_url = f"ws://127.0.0.1:{ws_port_holder[0]}/devtools/browser/auto"
                data = json.dumps(
                    {
                        "Browser": "Mock/1.0",
                        "webSocketDebuggerUrl": ws_url,
                    }
                )
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(data.encode())
            else:
                self.send_response(404)
                self.end_headers()

    http_server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), JsonVersionHandler)
    http_port = http_server.server_address[1]
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()

    yield f"ws://127.0.0.1:{http_port}"
    http_server.shutdown()
    ws_loop.call_soon_threadsafe(ws_loop.stop)
