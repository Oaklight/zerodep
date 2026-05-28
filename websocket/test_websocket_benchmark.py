"""Benchmark: zerodep websocket vs websockets library.

Simulates realistic workloads: JSON-RPC messaging (typical CDP command size),
large HTML payload transfer (SPA outerHTML extraction), burst messaging
(batch CDP commands), and concurrent multi-connection messaging.
"""

from __future__ import annotations

import concurrent.futures
import json

import pytest

from websocket import WebSocketClient

# ── Test data (pre-built at module level) ──────────────────────────────────

# ~200 bytes — typical CDP JSON-RPC command
JSONRPC_MSG = json.dumps(
    {
        "id": 1,
        "method": "Page.navigate",
        "params": {"url": "https://example.com", "transitionType": "typed"},
    }
)

# ~50 KB — simulates document.documentElement.outerHTML extraction
LARGE_HTML = (
    "<html><body>"
    + "<div class='item'><p>content</p></div>\n" * 1000
    + "</body></html>"
)

# 100 JSON-RPC messages — simulates batch CDP commands
BURST_MESSAGES = [
    json.dumps(
        {
            "id": i,
            "method": "Runtime.evaluate",
            "params": {"expression": f"document.querySelectorAll('div')[{i}]"},
        }
    )
    for i in range(100)
]


class TestJsonRpcRoundtrip:
    """Benchmark JSON-RPC message round-trip (~200B, typical CDP command)."""

    def test_zerodep(self, ws_echo_url, benchmark):
        ws = WebSocketClient(ws_echo_url)
        ws.connect()

        def roundtrip():
            ws.send(JSONRPC_MSG)
            return ws.recv()

        result = benchmark(roundtrip)
        assert json.loads(result)["method"] == "Page.navigate"
        ws.close()

    def test_websockets(self, ws_echo_url, benchmark):
        pytest.importorskip("websockets", reason="websockets not installed")
        import websockets.sync.client

        ws = websockets.sync.client.connect(ws_echo_url)

        def roundtrip():
            ws.send(JSONRPC_MSG)
            return ws.recv()

        result = benchmark(roundtrip)
        assert json.loads(result)["method"] == "Page.navigate"
        ws.close()


class TestLargePayload:
    """Benchmark large HTML payload transfer (~50KB, outerHTML extraction)."""

    def test_zerodep(self, ws_echo_url, benchmark):
        ws = WebSocketClient(ws_echo_url)
        ws.connect()

        def roundtrip():
            ws.send(LARGE_HTML)
            return ws.recv()

        result = benchmark(roundtrip)
        assert len(result) == len(LARGE_HTML)
        ws.close()

    def test_websockets(self, ws_echo_url, benchmark):
        pytest.importorskip("websockets", reason="websockets not installed")
        import websockets.sync.client

        ws = websockets.sync.client.connect(ws_echo_url)

        def roundtrip():
            ws.send(LARGE_HTML)
            return ws.recv()

        result = benchmark(roundtrip)
        assert len(result) == len(LARGE_HTML)
        ws.close()


class TestBurstMessages:
    """Benchmark burst messaging (100 JSON-RPC commands, batch CDP scenario)."""

    def test_zerodep(self, ws_echo_url, benchmark):
        ws = WebSocketClient(ws_echo_url)
        ws.connect()

        def burst():
            for msg in BURST_MESSAGES:
                ws.send(msg)
            results = []
            for _ in BURST_MESSAGES:
                results.append(ws.recv())
            return results

        results = benchmark(burst)
        assert len(results) == 100
        ws.close()

    def test_websockets(self, ws_echo_url, benchmark):
        pytest.importorskip("websockets", reason="websockets not installed")
        import websockets.sync.client

        ws = websockets.sync.client.connect(ws_echo_url)

        def burst():
            for msg in BURST_MESSAGES:
                ws.send(msg)
            results = []
            for _ in BURST_MESSAGES:
                results.append(ws.recv())
            return results

        results = benchmark(burst)
        assert len(results) == 100
        ws.close()


class TestConnectionSetup:
    """Benchmark connection establishment + close (handshake overhead)."""

    def test_zerodep(self, ws_echo_url, benchmark):
        def connect_close():
            ws = WebSocketClient(ws_echo_url)
            ws.connect()
            ws.close()

        benchmark(connect_close)

    def test_websockets(self, ws_echo_url, benchmark):
        pytest.importorskip("websockets", reason="websockets not installed")
        import websockets.sync.client

        def connect_close():
            ws = websockets.sync.client.connect(ws_echo_url)
            ws.close()

        benchmark(connect_close)


class TestConcurrentMessages:
    """Benchmark concurrent send/receive across multiple WebSocket connections."""

    CONNECTIONS = 4
    MESSAGES_PER_CONN = 20

    def test_zerodep(self, ws_echo_url, benchmark):
        def run():
            def worker(_):
                ws = WebSocketClient(ws_echo_url)
                ws.connect()
                try:
                    for _ in range(self.MESSAGES_PER_CONN):
                        ws.send(JSONRPC_MSG)
                        ws.recv()
                finally:
                    ws.close()

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.CONNECTIONS
            ) as pool:
                list(pool.map(worker, range(self.CONNECTIONS)))

        benchmark(run)

    def test_websockets(self, ws_echo_url, benchmark):
        pytest.importorskip("websockets", reason="websockets not installed")
        import websockets.sync.client

        def run():
            def worker(_):
                ws = websockets.sync.client.connect(ws_echo_url)
                try:
                    for _ in range(self.MESSAGES_PER_CONN):
                        ws.send(JSONRPC_MSG)
                        ws.recv()
                finally:
                    ws.close()

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.CONNECTIONS
            ) as pool:
                list(pool.map(worker, range(self.CONNECTIONS)))

        benchmark(run)
