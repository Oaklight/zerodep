"""Mock CDP server and optional real browser fixtures for testing.

Provides a session-scoped mock CDP server that simulates basic Chrome
DevTools Protocol interactions over WebSocket.
"""

from __future__ import annotations

import asyncio
import json
import threading
import uuid

import pytest


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


@pytest.fixture(scope="session")
def cdp_mock_url():
    """Start a mock CDP server and yield its WebSocket URL."""
    import websockets.server

    handler = _MockCDPHandler()

    async def ws_handler(ws):
        try:
            async for raw in ws:
                responses = handler.handle_message(raw)
                for resp in responses:
                    await ws.send(resp)
        except websockets.exceptions.ConnectionClosedOK:
            pass
        except websockets.exceptions.ConnectionClosedError:
            pass

    loop = asyncio.new_event_loop()
    started = threading.Event()
    port_holder: list[int] = []

    async def run_server():
        async with websockets.server.serve(ws_handler, "127.0.0.1", 0) as server:
            sock = list(server.sockets)[0]
            port_holder.append(sock.getsockname()[1])
            started.set()
            await asyncio.Future()  # run forever

    def thread_target():
        loop.run_until_complete(run_server())

    thread = threading.Thread(target=thread_target, daemon=True)
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
    import http.server

    import websockets.server

    handler = _MockCDPHandler()
    ws_port_holder: list[int] = []

    # Start WS server
    async def ws_handler(ws):
        try:
            async for raw in ws:
                responses = handler.handle_message(raw)
                for resp in responses:
                    await ws.send(resp)
        except websockets.exceptions.ConnectionClosedOK:
            pass
        except websockets.exceptions.ConnectionClosedError:
            pass

    ws_loop = asyncio.new_event_loop()
    ws_started = threading.Event()

    async def run_ws_server():
        async with websockets.server.serve(ws_handler, "127.0.0.1", 0) as server:
            sock = list(server.sockets)[0]
            ws_port_holder.append(sock.getsockname()[1])
            ws_started.set()
            await asyncio.Future()

    def ws_thread_target():
        ws_loop.run_until_complete(run_ws_server())

    ws_thread = threading.Thread(target=ws_thread_target, daemon=True)
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
