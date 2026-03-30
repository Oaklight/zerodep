"""Tests for SSE transport injection API."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import MagicMock


class _FakeSyncResponse:
    """Mock response for sync transport testing."""

    def __init__(self, lines: list[str], status_code: int = 200):
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self._lines = lines
        self._closed = False

    def iter_lines(self):
        yield from self._lines

    def close(self):
        self._closed = True


class _FakeAsyncResponse:
    """Mock response for async transport testing."""

    def __init__(self, lines: list[str], status_code: int = 200):
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self._lines = lines
        self._closed = False

    async def aiter_lines(self):
        for line in self._lines:
            yield line

    async def aclose(self):
        self._closed = True

    def close(self):
        self._closed = True


class TestSSEClientTransportInjection(unittest.TestCase):
    """Test transport injection on SSEClient."""

    def test_custom_transport_receives_events(self):
        """Injected transport should be called and events parsed."""
        from sse import SSEClient

        sse_lines = [
            "event: greeting",
            "data: hello",
            "",
            "event: farewell",
            "data: bye",
            "",
        ]

        call_count = 0

        def _mock_get(url, *, headers=None, stream=False, timeout=None, verify=True):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                # Return 204 on reconnect to stop iteration
                return _FakeSyncResponse([], status_code=204)
            return _FakeSyncResponse(sse_lines)

        client = SSEClient("http://example.com/sse", transport=_mock_get)
        events = list(client)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].event, "greeting")
        self.assertEqual(events[0].data, "hello")
        self.assertEqual(events[1].event, "farewell")
        self.assertEqual(events[1].data, "bye")

    def test_transport_none_raises_value_error(self):
        """transport=None should raise ValueError."""
        from sse import SSEClient

        with self.assertRaises(ValueError) as ctx:
            SSEClient("http://example.com", transport=None)
        self.assertIn("requires a transport", str(ctx.exception))

    def test_custom_transport_reconnect_on_oserror(self):
        """Custom transport should reconnect on OSError."""
        from sse import SSEClient

        call_count = 0

        def _flaky_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise OSError("connection reset")
            # Return 204 to stop
            return _FakeSyncResponse([], status_code=204)

        client = SSEClient(
            "http://example.com/sse",
            transport=_flaky_get,
            retry_interval=1,  # 1ms for fast test
            max_retries=2,
        )
        events = list(client)
        self.assertEqual(events, [])
        self.assertEqual(call_count, 2)

    def test_default_transport_requires_httpclient(self):
        """Without httpclient module, default transport should fail."""
        # This test only checks that _require_httpclient is called,
        # not that it actually imports httpclient (which may or may not
        # be available in the test environment).
        from sse import _HAS_HTTPCLIENT, SSEClient

        if not _HAS_HTTPCLIENT:
            with self.assertRaises(ImportError):
                SSEClient("http://example.com")


class TestAsyncSSEClientTransportInjection(unittest.TestCase):
    """Test transport injection on AsyncSSEClient."""

    def test_custom_async_transport_receives_events(self):
        """Injected async transport should work."""
        from sse import AsyncSSEClient

        sse_lines = [
            "data: async_hello",
            "",
        ]

        call_count = 0

        async def _mock_async_get(
            url, *, headers=None, stream=False, timeout=None, verify=True
        ):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                return _FakeAsyncResponse([], status_code=204)
            return _FakeAsyncResponse(sse_lines)

        async def _run():
            client = AsyncSSEClient("http://example.com/sse", transport=_mock_async_get)
            events = []
            async for event in client:
                events.append(event)
            return events

        events = asyncio.run(_run())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].data, "async_hello")

    def test_async_transport_none_raises(self):
        """transport=None should raise ValueError for async client."""
        from sse import AsyncSSEClient

        with self.assertRaises(ValueError):
            AsyncSSEClient("http://example.com", transport=None)


class TestConvenienceFunctionsForwardTransport(unittest.TestCase):
    """Test that connect() and async_connect() forward transport."""

    def test_connect_forwards_transport(self):
        """connect() should pass transport to SSEClient."""
        from sse import connect

        mock_transport = MagicMock()
        client = connect("http://example.com", transport=mock_transport)
        self.assertIs(client._transport, mock_transport)

    def test_async_connect_forwards_transport(self):
        """async_connect() should pass transport to AsyncSSEClient."""
        from sse import async_connect

        mock_transport = MagicMock()
        client = async_connect("http://example.com", transport=mock_transport)
        self.assertIs(client._transport, mock_transport)


if __name__ == "__main__":
    unittest.main()
