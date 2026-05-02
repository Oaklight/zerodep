"""Performance benchmarks for the websocket module.

Compares zerodep WebSocket client against the ``websockets`` reference library.

Note: ``websocket-client`` benchmarks are excluded because its import name
(``websocket``) collides with this module.
"""

from __future__ import annotations

from websocket import WebSocketClient


class TestSyncBenchmarks:
    """Benchmark sync WebSocket operations."""

    def test_echo_roundtrip(self, ws_echo_url, benchmark):
        """Measure echo round-trip latency."""
        ws = WebSocketClient(ws_echo_url)
        ws.connect()

        def roundtrip():
            ws.send("benchmark")
            return ws.recv()

        result = benchmark(roundtrip)
        assert result == "benchmark"
        ws.close()

    def test_echo_roundtrip_long(self, ws_echo_url, benchmark):
        """Measure echo round-trip latency for large messages."""
        ws = WebSocketClient(ws_echo_url)
        ws.connect()
        msg = "x" * 10_000

        def roundtrip():
            ws.send(msg)
            return ws.recv()

        result = benchmark(roundtrip)
        assert len(result) == 10_000
        ws.close()


class TestReferenceBenchmarks:
    """Benchmark against websockets reference library."""

    def test_websockets_echo_roundtrip(self, ws_echo_url, benchmark):
        """Measure websockets library echo round-trip latency."""
        import websockets.sync.client

        ws = websockets.sync.client.connect(ws_echo_url)

        def roundtrip():
            ws.send("benchmark")
            return ws.recv()

        result = benchmark(roundtrip)
        assert result == "benchmark"
        ws.close()

    def test_connection_setup(self, ws_echo_url, benchmark):
        """Benchmark connection establishment time (zerodep)."""

        def connect_disconnect():
            ws = WebSocketClient(ws_echo_url)
            ws.connect()
            ws.close()

        benchmark(connect_disconnect)

    def test_connection_setup_websockets(self, ws_echo_url, benchmark):
        """Benchmark connection establishment time (websockets)."""
        import websockets.sync.client

        def connect_disconnect():
            ws = websockets.sync.client.connect(ws_echo_url)
            ws.close()

        benchmark(connect_disconnect)
