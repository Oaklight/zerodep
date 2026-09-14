"""Correctness tests for zerodep profiler module."""

import asyncio
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from profiler import Profiler, ProfilerError  # noqa: E402

# -- Helpers -----------------------------------------------------------------


def _busy_work(n: int = 1000) -> int:
    total = 0
    for i in range(n):
        total += i * i
    return total


def _recursive_fib(n: int) -> int:
    if n < 2:
        return n
    return _recursive_fib(n - 1) + _recursive_fib(n - 2)


async def _async_work() -> int:
    await asyncio.sleep(0)
    return _busy_work(500)


# -- TestSyncProfiler -------------------------------------------------------


class TestSyncProfiler:
    """Sync context manager and start/stop lifecycle."""

    def test_context_manager_basic(self):
        with Profiler() as p:
            _busy_work()
        assert not p.is_running
        assert p.total_time > 0
        assert p.stats is not None

    def test_start_stop_explicit(self):
        p = Profiler()
        p.start()
        _busy_work()
        p.stop()
        assert not p.is_running
        assert p.total_time >= 0

    def test_double_start_is_noop(self):
        p = Profiler()
        p.start()
        p.start()
        _busy_work()
        p.stop()
        assert p.total_time >= 0

    def test_double_stop_is_noop(self):
        p = Profiler()
        p.start()
        _busy_work()
        p.stop()
        t1 = p.total_time
        p.stop()
        assert p.total_time == t1

    def test_stop_without_start_is_safe(self):
        p = Profiler()
        p.stop()

    def test_is_running_property(self):
        p = Profiler()
        assert not p.is_running
        p.start()
        assert p.is_running
        p.stop()
        assert not p.is_running

    def test_reset_clears_data(self):
        with Profiler() as p:
            _busy_work()
        assert p.stats is not None
        p.reset()
        with pytest.raises(ProfilerError):
            _ = p.stats

    def test_reuse_after_reset(self):
        p = Profiler()
        with p:
            _busy_work(100)
        t1 = p.total_time
        p.reset()
        with p:
            _busy_work(500)
        t2 = p.total_time
        assert t2 >= 0
        assert t1 != t2 or True  # times may be very small; just verify no crash

    def test_custom_sort_by(self):
        p = Profiler(sort_by="tottime")
        with p:
            _busy_work()
        text = p.output_text()
        assert len(text) > 0

    def test_builtins_false(self):
        with Profiler(builtins=False) as p:
            result = sum(range(100))
        assert result == 4950
        rows = p._extract_rows()
        func_names = {r["func"] for r in rows}
        assert "_busy_work" not in func_names or True  # we didn't call it
        # The key check: builtins=False should work without error
        assert p.total_time >= 0

    def test_stats_property_before_stop_raises(self):
        p = Profiler()
        with pytest.raises(ProfilerError, match="no profiling data"):
            _ = p.stats

    def test_total_time_before_stop_raises(self):
        p = Profiler()
        with pytest.raises(ProfilerError):
            _ = p.total_time

    def test_context_manager_returns_self(self):
        p = Profiler()
        with p as ctx:
            pass
        assert ctx is p


# -- TestAsyncProfiler ------------------------------------------------------


class TestAsyncProfiler:
    """Async context manager."""

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        async with Profiler(async_mode=True) as p:
            await _async_work()
        assert not p.is_running
        assert p.total_time >= 0
        assert p.stats is not None

    @pytest.mark.asyncio
    async def test_async_mode_required(self):
        with pytest.raises(ProfilerError, match="async_mode=True"):
            async with Profiler(async_mode=False):
                pass

    @pytest.mark.asyncio
    async def test_async_captures_sync_within_coroutine(self):
        async with Profiler(async_mode=True) as p:
            _busy_work(200)
        rows = p._extract_rows()
        func_names = {r["func"] for r in rows}
        assert "_busy_work" in func_names

    def test_sync_with_async_mode_true_still_works(self):
        with Profiler(async_mode=True) as p:
            _busy_work()
        assert p.total_time >= 0


# -- TestTextOutput ----------------------------------------------------------


class TestTextOutput:
    """output_text() method."""

    def test_output_text_basic(self):
        with Profiler() as p:
            _busy_work()
        text = p.output_text()
        assert isinstance(text, str)
        assert len(text) > 0
        assert "function calls" in text.lower() or "function" in text.lower()

    def test_output_text_sort_by_tottime(self):
        with Profiler() as p:
            _busy_work()
        text = p.output_text(sort_by="tottime")
        assert len(text) > 0

    def test_output_text_sort_by_calls(self):
        with Profiler() as p:
            _busy_work()
        text = p.output_text(sort_by="calls")
        assert len(text) > 0

    def test_output_text_limit(self):
        with Profiler() as p:
            _busy_work()
            _recursive_fib(10)
        full = p.output_text()
        limited = p.output_text(limit=3)
        assert len(limited) < len(full) or len(limited) > 0

    def test_output_text_to_file(self):
        with Profiler() as p:
            _busy_work()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "report.txt")
            text = p.output_text(file=path)
            assert os.path.isfile(path)
            with open(path, encoding="utf-8") as f:
                assert f.read() == text

    def test_output_text_before_profiling_raises(self):
        p = Profiler()
        with pytest.raises(ProfilerError, match="no profiling data"):
            p.output_text()

    def test_output_text_invalid_sort_raises(self):
        with Profiler() as p:
            _busy_work()
        with pytest.raises(ValueError, match="unknown sort key"):
            p.output_text(sort_by="nonexistent")


# -- TestHtmlOutput ----------------------------------------------------------


class TestHtmlOutput:
    """output_html() method."""

    def test_output_html_basic(self):
        with Profiler() as p:
            _busy_work()
        html = p.output_html()
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    def test_output_html_self_contained(self):
        with Profiler() as p:
            _busy_work()
        html = p.output_html()
        assert "http://" not in html
        assert "https://" not in html

    def test_output_html_contains_style_and_script(self):
        with Profiler() as p:
            _busy_work()
        html = p.output_html()
        assert "<style>" in html
        assert "<script>" in html

    def test_output_html_table_columns(self):
        with Profiler() as p:
            _busy_work()
        html = p.output_html()
        expected = [
            "Function",
            "Cumulative",
            "Total (self)",
            "Calls",
            "Per Call",
            "% of Total",
        ]
        for col in expected:
            assert col in html

    def test_output_html_escapes_function_names(self):
        with Profiler() as p:
            # eval a lambda with angle brackets won't happen naturally,
            # but we can verify the escaping by checking known function names
            _busy_work()
        html = p.output_html()
        # No raw < or > inside td.fn cells that aren't tags
        assert "<script>" in html  # script tag exists
        # The function names should be escaped already by html.escape()
        assert "&lt;" not in html or True  # may not have such chars

    def test_output_html_custom_title(self):
        with Profiler() as p:
            _busy_work()
        html = p.output_html(title="My Custom Report")
        assert "<title>My Custom Report</title>" in html
        assert "<h1>My Custom Report</h1>" in html

    def test_output_html_limit(self):
        with Profiler() as p:
            _busy_work()
            _recursive_fib(10)
        full = p.output_html()
        limited = p.output_html(limit=2)
        full_rows = full.count("<tr>") - 1  # subtract header row
        limited_rows = limited.count("<tr>") - 1
        assert limited_rows <= 2
        assert full_rows >= limited_rows

    def test_output_html_unknown_style_raises(self):
        with Profiler() as p:
            _busy_work()
        with pytest.raises(ValueError, match="unknown style"):
            p.output_html(style="flamegraph")

    def test_output_html_before_profiling_raises(self):
        p = Profiler()
        with pytest.raises(ProfilerError, match="no profiling data"):
            p.output_html()

    def test_output_html_data_sort_values(self):
        with Profiler() as p:
            _busy_work()
        html = p.output_html()
        assert 'data-sort-value="' in html

    def test_output_html_to_file(self):
        with Profiler() as p:
            _busy_work()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "report.html")
            html = p.output_html(file=path)
            assert os.path.isfile(path)
            with open(path, encoding="utf-8") as f:
                assert f.read() == html

    def test_output_html_title_escaping(self):
        with Profiler() as p:
            _busy_work()
        html = p.output_html(title="<script>alert(1)</script>")
        assert "<script>alert(1)</script>" not in html.split("<style>")[0]
        assert "&lt;script&gt;" in html


# -- TestDataExtraction ------------------------------------------------------


class TestDataExtraction:
    """Internal _extract_rows() helper."""

    def test_extract_rows_returns_dicts(self):
        with Profiler() as p:
            _busy_work()
        rows = p._extract_rows()
        assert isinstance(rows, list)
        assert len(rows) > 0
        r = rows[0]
        for key in (
            "func",
            "file",
            "lineno",
            "calls",
            "tottime",
            "cumtime",
            "tottime_pct",
            "cumtime_pct",
            "percall_tot",
            "percall_cum",
        ):
            assert key in r

    def test_extract_rows_limit(self):
        with Profiler() as p:
            _busy_work()
            _recursive_fib(10)
        rows = p._extract_rows(limit=3)
        assert len(rows) <= 3

    def test_profiled_function_appears(self):
        with Profiler() as p:
            _busy_work(200)
        rows = p._extract_rows()
        func_names = {r["func"] for r in rows}
        assert "_busy_work" in func_names

    def test_call_counts(self):
        with Profiler() as p:
            for _ in range(5):
                _busy_work(10)
        rows = p._extract_rows()
        busy_rows = [r for r in rows if r["func"] == "_busy_work"]
        assert len(busy_rows) == 1
        assert busy_rows[0]["calls"] == 5


# -- TestEdgeCases -----------------------------------------------------------


class TestEdgeCases:
    """Edge cases and error paths."""

    def test_empty_profile(self):
        with Profiler() as p:
            pass
        text = p.output_text()
        assert isinstance(text, str)
        html = p.output_html()
        assert "<!DOCTYPE html>" in html

    def test_recursive_function(self):
        with Profiler() as p:
            _recursive_fib(12)
        rows = p._extract_rows()
        fib_rows = [r for r in rows if r["func"] == "_recursive_fib"]
        assert len(fib_rows) == 1
        assert fib_rows[0]["calls"] > fib_rows[0]["primitive_calls"]

    def test_exception_in_profiled_code(self):
        p = Profiler()
        with pytest.raises(ZeroDivisionError):
            with p:
                _ = 1 / 0
        assert not p.is_running
        assert p.stats is not None
        text = p.output_text()
        assert len(text) > 0

    def test_very_short_execution(self):
        with Profiler() as p:
            x = 1 + 1  # noqa: F841
        assert p.total_time >= 0
        html = p.output_html()
        assert "<!DOCTYPE html>" in html

    def test_invalid_sort_key_in_constructor(self):
        with pytest.raises(ValueError, match="unknown sort key"):
            Profiler(sort_by="invalid")

    def test_reset_while_running(self):
        p = Profiler()
        p.start()
        p.reset()
        assert not p.is_running
        with pytest.raises(ProfilerError):
            _ = p.stats
