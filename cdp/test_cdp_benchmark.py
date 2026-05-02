"""Performance benchmarks for the cdp module.

Benchmarks CDP client operations against the mock server.
Real browser benchmarks require CHROME_PATH to be set.
"""

from __future__ import annotations

from cdp import CDPClient


class TestCDPBenchmarks:
    """Benchmark CDP operations against mock server."""

    def test_create_close_target(self, cdp_mock_url, benchmark):
        """Benchmark target creation and cleanup."""
        client = CDPClient(cdp_mock_url)
        client.connect()

        def create_close():
            tid = client.create_target()
            client.close_target(tid)

        benchmark(create_close)
        client.close()

    def test_navigate_and_evaluate(self, cdp_mock_url, benchmark):
        """Benchmark navigate + evaluate cycle."""
        client = CDPClient(cdp_mock_url)
        client.connect()
        target_id = client.create_target()

        def nav_eval():
            client.navigate(target_id, "https://example.com")
            return client.evaluate(target_id, "document.body.innerText")

        result = benchmark(nav_eval)
        assert "Mock page content" in result
        client.close_target(target_id)
        client.close()

    def test_get_rendered_text(self, cdp_mock_url, benchmark):
        """Benchmark high-level get_rendered_text."""
        client = CDPClient(cdp_mock_url)
        client.connect()

        def get_text():
            return client.get_rendered_text("https://example.com")

        result = benchmark(get_text)
        assert "Mock page content" in result
        client.close()
