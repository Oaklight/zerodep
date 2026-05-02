"""Benchmark: CDP client operations against mock server.

Simulates realistic workloads: full SPA render pipeline, multi-tab management,
JS evaluation throughput, and raw command dispatch overhead.
"""

from __future__ import annotations

from cdp import CDPClient


class TestFullRenderPipeline:
    """Benchmark the core SPA rendering flow: create → navigate → extract text → close."""

    def test_get_rendered_text(self, cdp_mock_url, benchmark):
        client = CDPClient(cdp_mock_url)
        client.connect()

        def render():
            return client.get_rendered_text("https://example.com")

        result = benchmark(render)
        assert "Mock page content" in result
        client.close()

    def test_get_rendered_text_fresh_client(self, cdp_mock_url, benchmark):
        """Full lifecycle including connect/close per call."""

        def render():
            with CDPClient(cdp_mock_url) as client:
                return client.get_rendered_text("https://example.com")

        result = benchmark(render)
        assert "Mock page content" in result


class TestRenderHtml:
    """Benchmark HTML extraction pipeline (outerHTML)."""

    def test_get_rendered_html(self, cdp_mock_url, benchmark):
        client = CDPClient(cdp_mock_url)
        client.connect()

        def render():
            return client.get_rendered_html("https://example.com")

        result = benchmark(render)
        assert "<html>" in result
        client.close()


class TestMultiTarget:
    """Benchmark multi-tab management (5 concurrent targets)."""

    def test_multi_target_pipeline(self, cdp_mock_url, benchmark):
        client = CDPClient(cdp_mock_url)
        client.connect()

        def multi():
            targets = []
            for i in range(5):
                tid = client.create_target(f"https://example.com/page{i}")
                targets.append(tid)
            results = []
            for tid in targets:
                client.navigate(tid, "https://example.com")
                text = client.evaluate(tid, "document.body.innerText")
                results.append(text)
            for tid in targets:
                client.close_target(tid)
            return results

        results = benchmark(multi)
        assert len(results) == 5
        assert all("Mock page content" in r for r in results)
        client.close()


class TestJsEvalThroughput:
    """Benchmark rapid JS evaluation on a single target."""

    def test_evaluate_burst(self, cdp_mock_url, benchmark):
        client = CDPClient(cdp_mock_url)
        client.connect()
        target_id = client.create_target()

        expressions = [
            "document.title",
            "document.body.innerText",
            "window.location.href",
            "document.querySelectorAll('div').length",
            "navigator.userAgent",
            "document.readyState",
            "performance.now()",
            "document.cookie",
            "window.innerWidth",
            "JSON.stringify({ok: true})",
        ]

        def eval_burst():
            results = []
            for expr in expressions:
                results.append(client.evaluate(target_id, expr))
            return results

        results = benchmark(eval_burst)
        assert len(results) == 10
        client.close_target(target_id)
        client.close()


class TestCommandThroughput:
    """Benchmark raw CDP command dispatch overhead."""

    def test_send_command_burst(self, cdp_mock_url, benchmark):
        client = CDPClient(cdp_mock_url)
        client.connect()

        def cmd_burst():
            results = []
            for i in range(20):
                resp = client.send_command(
                    "Target.createTarget",
                    {"url": f"about:blank#{i}"},
                )
                results.append(resp)
            # Clean up created targets
            for resp in results:
                tid = resp.get("targetId", "")
                if tid:
                    client.send_command("Target.closeTarget", {"targetId": tid})
            return results

        results = benchmark(cmd_burst)
        assert len(results) == 20
        client.close()
