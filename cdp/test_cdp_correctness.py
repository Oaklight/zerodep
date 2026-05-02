"""Correctness tests for the cdp module.

Tests CDP client against a mock CDP server. Both sync (CDPClient) and
async (AsyncCDPClient) variants are tested.
"""

from __future__ import annotations

import pytest

from cdp import (
    AsyncCDPClient,
    CDPClient,
    CDPConnectionError,
    CDPError,
    CDPProtocolError,
)

# ── Sync Tests ─────────────────────────────────────────────────────────────


class TestSyncConnection:
    """Test sync CDP connection lifecycle."""

    def test_connect_and_close(self, cdp_mock_url):
        client = CDPClient(cdp_mock_url)
        client.connect()
        client.close()

    def test_context_manager(self, cdp_mock_url):
        with CDPClient(cdp_mock_url) as _client:
            pass  # just verify it connects and closes cleanly

    def test_double_connect_is_noop(self, cdp_mock_url):
        with CDPClient(cdp_mock_url) as client:
            client.connect()  # second call should not raise

    def test_double_close_is_noop(self, cdp_mock_url):
        client = CDPClient(cdp_mock_url)
        client.connect()
        client.close()
        client.close()  # should not raise

    def test_connection_refused(self):
        client = CDPClient("ws://127.0.0.1:1/devtools/browser/test")
        with pytest.raises(CDPConnectionError):
            client.connect(timeout=2)

    def test_send_command_without_connect(self):
        client = CDPClient("ws://127.0.0.1:1/devtools/browser/test")
        with pytest.raises(CDPError, match="not connected"):
            client.send_command("Page.enable")


class TestSyncAutoDiscovery:
    """Test sync CDP auto-discovery via /json/version."""

    def test_auto_discover(self, cdp_json_version_url):
        with CDPClient(cdp_json_version_url) as client:
            target_id = client.create_target()
            client.close_target(target_id)


class TestSyncTargetManagement:
    """Test sync target (tab) management."""

    def test_create_and_close_target(self, cdp_mock_url):
        with CDPClient(cdp_mock_url) as client:
            target_id = client.create_target()
            assert target_id
            assert target_id in client._targets
            client.close_target(target_id)
            assert target_id not in client._targets

    def test_create_multiple_targets(self, cdp_mock_url):
        with CDPClient(cdp_mock_url) as client:
            t1 = client.create_target("https://example.com")
            t2 = client.create_target("https://example.org")
            assert t1 != t2
            assert len(client._targets) == 2
            client.close_target(t1)
            client.close_target(t2)

    def test_close_nonexistent_target(self, cdp_mock_url):
        with CDPClient(cdp_mock_url) as client:
            client.close_target("nonexistent-id")  # should not raise

    def test_auto_cleanup_on_close(self, cdp_mock_url):
        client = CDPClient(cdp_mock_url)
        client.connect()
        client.create_target()
        client.create_target()
        assert len(client._targets) == 2
        client.close()
        assert len(client._targets) == 0


class TestSyncNavigation:
    """Test sync page navigation."""

    def test_navigate(self, cdp_mock_url):
        with CDPClient(cdp_mock_url) as client:
            target_id = client.create_target()
            client.navigate(target_id, "https://example.com")
            client.close_target(target_id)

    def test_navigate_unknown_target(self, cdp_mock_url):
        with CDPClient(cdp_mock_url) as client:
            with pytest.raises(CDPError, match="unknown target"):
                client.navigate("bad-id", "https://example.com")


class TestSyncEvaluate:
    """Test sync JavaScript evaluation."""

    def test_evaluate_expression(self, cdp_mock_url):
        with CDPClient(cdp_mock_url) as client:
            target_id = client.create_target()
            result = client.evaluate(target_id, "1 + 1")
            assert result == "eval:1 + 1"
            client.close_target(target_id)

    def test_evaluate_innertext(self, cdp_mock_url):
        with CDPClient(cdp_mock_url) as client:
            target_id = client.create_target()
            result = client.evaluate(target_id, "document.body.innerText")
            assert "Mock page content" in result
            client.close_target(target_id)

    def test_evaluate_error(self, cdp_mock_url):
        with CDPClient(cdp_mock_url) as client:
            target_id = client.create_target()
            with pytest.raises(CDPProtocolError, match="Uncaught Error"):
                client.evaluate(target_id, "throw new Error('test error')")
            client.close_target(target_id)


class TestSyncHighLevel:
    """Test sync high-level API."""

    def test_get_rendered_text(self, cdp_mock_url):
        with CDPClient(cdp_mock_url) as client:
            text = client.get_rendered_text("https://example.com")
            assert isinstance(text, str)
            assert "Mock page content" in text

    def test_get_rendered_html(self, cdp_mock_url):
        with CDPClient(cdp_mock_url) as client:
            html = client.get_rendered_html("https://example.com")
            assert isinstance(html, str)
            assert "<html>" in html
            assert "Mock page content" in html

    def test_get_rendered_text_cleans_up_target(self, cdp_mock_url):
        with CDPClient(cdp_mock_url) as client:
            targets_before = len(client._targets)
            client.get_rendered_text("https://example.com")
            assert len(client._targets) == targets_before


class TestSyncUserAgent:
    """Test sync User-Agent override."""

    def test_set_user_agent(self, cdp_mock_url):
        with CDPClient(cdp_mock_url) as client:
            target_id = client.create_target()
            client.set_user_agent(target_id, "CustomAgent/1.0")
            client.close_target(target_id)


# ── Async Tests ────────────────────────────────────────────────────────────


class TestAsyncConnection:
    """Test async CDP connection lifecycle."""

    @pytest.mark.asyncio
    async def test_connect_and_close(self, cdp_mock_url):
        client = AsyncCDPClient(cdp_mock_url)
        await client.connect()
        await client.close()

    @pytest.mark.asyncio
    async def test_context_manager(self, cdp_mock_url):
        async with AsyncCDPClient(cdp_mock_url) as _client:
            pass

    @pytest.mark.asyncio
    async def test_double_connect_is_noop(self, cdp_mock_url):
        async with AsyncCDPClient(cdp_mock_url) as client:
            await client.connect()

    @pytest.mark.asyncio
    async def test_double_close_is_noop(self, cdp_mock_url):
        client = AsyncCDPClient(cdp_mock_url)
        await client.connect()
        await client.close()
        await client.close()

    @pytest.mark.asyncio
    async def test_connection_refused(self):
        client = AsyncCDPClient("ws://127.0.0.1:1/devtools/browser/test")
        with pytest.raises(CDPConnectionError):
            await client.connect(timeout=2)

    @pytest.mark.asyncio
    async def test_send_command_without_connect(self):
        client = AsyncCDPClient("ws://127.0.0.1:1/devtools/browser/test")
        with pytest.raises(CDPError, match="not connected"):
            await client.send_command("Page.enable")


class TestAsyncTargetManagement:
    """Test async target management."""

    @pytest.mark.asyncio
    async def test_create_and_close_target(self, cdp_mock_url):
        async with AsyncCDPClient(cdp_mock_url) as client:
            target_id = await client.create_target()
            assert target_id
            assert target_id in client._targets
            await client.close_target(target_id)
            assert target_id not in client._targets

    @pytest.mark.asyncio
    async def test_auto_cleanup_on_close(self, cdp_mock_url):
        client = AsyncCDPClient(cdp_mock_url)
        await client.connect()
        await client.create_target()
        await client.create_target()
        assert len(client._targets) == 2
        await client.close()
        assert len(client._targets) == 0


class TestAsyncNavigation:
    """Test async page navigation."""

    @pytest.mark.asyncio
    async def test_navigate(self, cdp_mock_url):
        async with AsyncCDPClient(cdp_mock_url) as client:
            target_id = await client.create_target()
            await client.navigate(target_id, "https://example.com")
            await client.close_target(target_id)


class TestAsyncEvaluate:
    """Test async JavaScript evaluation."""

    @pytest.mark.asyncio
    async def test_evaluate_expression(self, cdp_mock_url):
        async with AsyncCDPClient(cdp_mock_url) as client:
            target_id = await client.create_target()
            result = await client.evaluate(target_id, "1 + 1")
            assert result == "eval:1 + 1"
            await client.close_target(target_id)

    @pytest.mark.asyncio
    async def test_evaluate_error(self, cdp_mock_url):
        async with AsyncCDPClient(cdp_mock_url) as client:
            target_id = await client.create_target()
            with pytest.raises(CDPProtocolError, match="Uncaught Error"):
                await client.evaluate(target_id, "throw new Error('test error')")
            await client.close_target(target_id)


class TestAsyncHighLevel:
    """Test async high-level API."""

    @pytest.mark.asyncio
    async def test_get_rendered_text(self, cdp_mock_url):
        async with AsyncCDPClient(cdp_mock_url) as client:
            text = await client.get_rendered_text("https://example.com")
            assert isinstance(text, str)
            assert "Mock page content" in text

    @pytest.mark.asyncio
    async def test_get_rendered_html(self, cdp_mock_url):
        async with AsyncCDPClient(cdp_mock_url) as client:
            html = await client.get_rendered_html("https://example.com")
            assert isinstance(html, str)
            assert "<html>" in html

    @pytest.mark.asyncio
    async def test_get_rendered_text_cleans_up(self, cdp_mock_url):
        async with AsyncCDPClient(cdp_mock_url) as client:
            targets_before = len(client._targets)
            await client.get_rendered_text("https://example.com")
            assert len(client._targets) == targets_before
