"""Correctness tests for the websocket module.

Compares zerodep WebSocket client against the ``websockets`` reference library.
Tests both sync (WebSocketClient) and async (AsyncWebSocketClient) variants.
"""

from __future__ import annotations

import pytest

from websocket import (
    AsyncWebSocketClient,
    WebSocketClient,
    WebSocketConnectionError,
    WebSocketError,
    WebSocketTimeoutError,
)

# ── Sync Tests ─────────────────────────────────────────────────────────────


class TestSyncConnection:
    """Test sync WebSocket connection lifecycle."""

    def test_connect_and_close(self, ws_echo_url):
        ws = WebSocketClient(ws_echo_url)
        ws.connect()
        assert ws.connected
        ws.close()
        assert not ws.connected

    def test_context_manager(self, ws_echo_url):
        with WebSocketClient(ws_echo_url) as ws:
            assert ws.connected
        assert not ws.connected

    def test_double_connect_is_noop(self, ws_echo_url):
        with WebSocketClient(ws_echo_url) as ws:
            ws.connect()  # second call should be a no-op
            assert ws.connected

    def test_double_close_is_noop(self, ws_echo_url):
        ws = WebSocketClient(ws_echo_url)
        ws.connect()
        ws.close()
        ws.close()  # should not raise
        assert not ws.connected

    def test_connection_refused(self):
        ws = WebSocketClient("ws://127.0.0.1:1")
        with pytest.raises(WebSocketConnectionError):
            ws.connect(timeout=2)

    def test_send_without_connect_raises(self):
        ws = WebSocketClient("ws://127.0.0.1:1")
        with pytest.raises(WebSocketError, match="not connected"):
            ws.send("hello")

    def test_recv_without_connect_raises(self):
        ws = WebSocketClient("ws://127.0.0.1:1")
        with pytest.raises(WebSocketError, match="not connected"):
            ws.recv()


class TestSyncEcho:
    """Test sync echo round-trip."""

    def test_short_text(self, ws_echo_url):
        with WebSocketClient(ws_echo_url) as ws:
            ws.send("hello")
            assert ws.recv() == "hello"

    def test_empty_string(self, ws_echo_url):
        with WebSocketClient(ws_echo_url) as ws:
            ws.send("")
            assert ws.recv() == ""

    def test_unicode(self, ws_echo_url):
        with WebSocketClient(ws_echo_url) as ws:
            msg = "Hello 世界 🌍 こんにちは"
            ws.send(msg)
            assert ws.recv() == msg

    def test_long_text(self, ws_echo_url):
        with WebSocketClient(ws_echo_url) as ws:
            msg = "x" * 100_000
            ws.send(msg)
            assert ws.recv() == msg

    def test_multiple_messages(self, ws_echo_url):
        with WebSocketClient(ws_echo_url) as ws:
            for i in range(10):
                ws.send(f"msg-{i}")
                assert ws.recv() == f"msg-{i}"

    def test_json_payload(self, ws_echo_url):
        import json

        with WebSocketClient(ws_echo_url) as ws:
            payload = json.dumps({"key": "value", "num": 42})
            ws.send(payload)
            result = json.loads(ws.recv())
            assert result == {"key": "value", "num": 42}


class TestSyncTimeout:
    """Test sync timeout handling."""

    def test_recv_timeout(self, ws_echo_url):
        with WebSocketClient(ws_echo_url) as ws:
            with pytest.raises(WebSocketTimeoutError):
                ws.recv(timeout=0.1)

    def test_connect_timeout(self):
        # Use a non-routable address to trigger connect timeout
        ws = WebSocketClient("ws://192.0.2.1:9999")
        with pytest.raises((WebSocketTimeoutError, WebSocketConnectionError)):
            ws.connect(timeout=0.5)


class TestSyncCustomServer:
    """Test sync client against server with custom behavior."""

    def test_echo_prefix(self, ws_custom_server_url):
        with WebSocketClient(ws_custom_server_url) as ws:
            ws.send("hello")
            assert ws.recv() == "echo:hello"

    def test_server_initiated_close(self, ws_custom_server_url):
        with WebSocketClient(ws_custom_server_url) as ws:
            ws.send("close-me")
            with pytest.raises(WebSocketConnectionError, match="closed by server"):
                ws.recv()


class TestSyncHeaders:
    """Test sync custom headers."""

    def test_custom_headers(self, ws_echo_url):
        headers = {"X-Custom-Header": "test-value"}
        with WebSocketClient(ws_echo_url, headers=headers) as ws:
            ws.send("hello")
            assert ws.recv() == "hello"


class TestSyncURLParsing:
    """Test URL parsing edge cases."""

    def test_invalid_scheme(self):
        with pytest.raises(ValueError, match="unsupported scheme"):
            WebSocketClient("http://localhost/ws")

    def test_ws_default_port(self, ws_echo_url):
        # Just verify the URL parsing doesn't crash
        ws = WebSocketClient("ws://localhost/path?query=1")
        assert ws._host == "localhost"
        assert ws._port == 80
        assert ws._path == "/path?query=1"
        assert not ws._is_secure

    def test_wss_default_port(self):
        ws = WebSocketClient("wss://example.com/ws")
        assert ws._host == "example.com"
        assert ws._port == 443
        assert ws._is_secure


# ── Async Tests ────────────────────────────────────────────────────────────


class TestAsyncConnection:
    """Test async WebSocket connection lifecycle."""

    @pytest.mark.asyncio
    async def test_connect_and_close(self, ws_echo_url):
        ws = AsyncWebSocketClient(ws_echo_url)
        await ws.connect()
        assert ws.connected
        await ws.close()
        assert not ws.connected

    @pytest.mark.asyncio
    async def test_context_manager(self, ws_echo_url):
        async with AsyncWebSocketClient(ws_echo_url) as ws:
            assert ws.connected
        assert not ws.connected

    @pytest.mark.asyncio
    async def test_double_connect_is_noop(self, ws_echo_url):
        async with AsyncWebSocketClient(ws_echo_url) as ws:
            await ws.connect()  # second call should be a no-op
            assert ws.connected

    @pytest.mark.asyncio
    async def test_double_close_is_noop(self, ws_echo_url):
        ws = AsyncWebSocketClient(ws_echo_url)
        await ws.connect()
        await ws.close()
        await ws.close()  # should not raise
        assert not ws.connected

    @pytest.mark.asyncio
    async def test_connection_refused(self):
        ws = AsyncWebSocketClient("ws://127.0.0.1:1")
        with pytest.raises(WebSocketConnectionError):
            await ws.connect(timeout=2)

    @pytest.mark.asyncio
    async def test_send_without_connect_raises(self):
        ws = AsyncWebSocketClient("ws://127.0.0.1:1")
        with pytest.raises(WebSocketError, match="not connected"):
            await ws.send("hello")

    @pytest.mark.asyncio
    async def test_recv_without_connect_raises(self):
        ws = AsyncWebSocketClient("ws://127.0.0.1:1")
        with pytest.raises(WebSocketError, match="not connected"):
            await ws.recv()


class TestAsyncEcho:
    """Test async echo round-trip."""

    @pytest.mark.asyncio
    async def test_short_text(self, ws_echo_url):
        async with AsyncWebSocketClient(ws_echo_url) as ws:
            await ws.send("hello")
            assert await ws.recv() == "hello"

    @pytest.mark.asyncio
    async def test_empty_string(self, ws_echo_url):
        async with AsyncWebSocketClient(ws_echo_url) as ws:
            await ws.send("")
            assert await ws.recv() == ""

    @pytest.mark.asyncio
    async def test_unicode(self, ws_echo_url):
        async with AsyncWebSocketClient(ws_echo_url) as ws:
            msg = "Hello 世界 🌍 こんにちは"
            await ws.send(msg)
            assert await ws.recv() == msg

    @pytest.mark.asyncio
    async def test_long_text(self, ws_echo_url):
        async with AsyncWebSocketClient(ws_echo_url) as ws:
            msg = "x" * 100_000
            await ws.send(msg)
            assert await ws.recv() == msg

    @pytest.mark.asyncio
    async def test_multiple_messages(self, ws_echo_url):
        async with AsyncWebSocketClient(ws_echo_url) as ws:
            for i in range(10):
                await ws.send(f"msg-{i}")
                assert await ws.recv() == f"msg-{i}"


class TestAsyncTimeout:
    """Test async timeout handling."""

    @pytest.mark.asyncio
    async def test_recv_timeout(self, ws_echo_url):
        async with AsyncWebSocketClient(ws_echo_url) as ws:
            with pytest.raises(WebSocketTimeoutError):
                await ws.recv(timeout=0.1)

    @pytest.mark.asyncio
    async def test_connect_timeout(self):
        ws = AsyncWebSocketClient("ws://192.0.2.1:9999")
        with pytest.raises((WebSocketTimeoutError, WebSocketConnectionError)):
            await ws.connect(timeout=0.5)


class TestAsyncCustomServer:
    """Test async client against server with custom behavior."""

    @pytest.mark.asyncio
    async def test_echo_prefix(self, ws_custom_server_url):
        async with AsyncWebSocketClient(ws_custom_server_url) as ws:
            await ws.send("hello")
            assert await ws.recv() == "echo:hello"

    @pytest.mark.asyncio
    async def test_server_initiated_close(self, ws_custom_server_url):
        async with AsyncWebSocketClient(ws_custom_server_url) as ws:
            await ws.send("close-me")
            with pytest.raises(WebSocketConnectionError, match="closed by server"):
                await ws.recv()


# ── Reference comparison tests ─────────────────────────────────────────────


class TestReferenceComparison:
    """Compare zerodep websocket against the websockets reference library."""

    def test_sync_vs_websockets_echo(self, ws_echo_url):
        """Both clients should get identical echo responses."""
        import websockets.sync.client

        msg = "reference test 日本語"

        # zerodep
        with WebSocketClient(ws_echo_url) as ws:
            ws.send(msg)
            zerodep_result = ws.recv()

        # reference
        with websockets.sync.client.connect(ws_echo_url) as ws:
            ws.send(msg)
            ref_result = ws.recv()

        assert zerodep_result == ref_result == msg

    @pytest.mark.asyncio
    async def test_async_vs_websockets_echo(self, ws_echo_url):
        """Both async clients should get identical echo responses."""
        import websockets

        msg = "async reference test 中文"

        # zerodep
        async with AsyncWebSocketClient(ws_echo_url) as ws:
            await ws.send(msg)
            zerodep_result = await ws.recv()

        # reference
        async with websockets.connect(ws_echo_url) as ws:
            await ws.send(msg)
            ref_result = await ws.recv()

        assert zerodep_result == ref_result == msg
