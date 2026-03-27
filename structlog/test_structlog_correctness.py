"""Correctness tests: zerodep structlog vs structlog."""

import io
import json
import logging
import os
import sys
import threading

import pytest

# Our structlog.py shadows the installed structlog package.
# Import the reference library first with path manipulation
# (same pattern as yaml/test_yaml_correctness.py).
_this_dir = os.path.dirname(__file__)

_saved_path = sys.path[:]
sys.path = [
    p
    for p in sys.path
    if os.path.abspath(p)
    not in (
        os.path.abspath(_this_dir),
        os.path.abspath(os.path.join(_this_dir, "..")),
    )
]
_cached_structlog = sys.modules.pop("structlog", None)

try:
    import structlog as _ref

    if not hasattr(_ref, "configure"):
        raise ImportError("Not the real structlog")
    ref_structlog = _ref
    import structlog.processors as ref_processors
    import structlog.stdlib as ref_stdlib
except ImportError:
    pytest.skip("structlog not installed", allow_module_level=True)
finally:
    sys.path = _saved_path
    # Remove ref structlog from modules cache so our local one can load.
    for _k in list(sys.modules):
        if _k == "structlog" or _k.startswith("structlog."):
            sys.modules.pop(_k, None)
    if _cached_structlog is not None:
        sys.modules["structlog"] = _cached_structlog

sys.path.insert(0, _this_dir)
from structlog import (
    BoundLogger,
    ConsoleRenderer,
    DropEvent,
    JSONRenderer,
    KeyValueRenderer,
    PrintLogger,
    PrintLoggerFactory,
    TimeStamper,
    add_log_level,
    add_logger_name,
    configure,
    format_exc_info,
    get_logger,
    reset_defaults,
    setup_logging,
    truncate_base64,
    truncate_string,
    wrap_logger,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _capture_ours(**kw: object) -> str:
    """Return a single log line captured from our library."""
    buf = io.StringIO()
    logger = _make_ours_logger(buf)
    logger.info("test event", **kw)
    return buf.getvalue().strip()


def _make_ours_logger(buf: io.StringIO) -> BoundLogger:
    """Create a our BoundLogger that writes to *buf*."""
    return BoundLogger(
        logger=PrintLogger(file=buf),
        processors=[add_log_level, TimeStamper(), ConsoleRenderer(colors=False)],
        context={},
    )


def _make_json_logger(buf: io.StringIO) -> BoundLogger:
    """Create a our BoundLogger with JSON output."""
    return BoundLogger(
        logger=PrintLogger(file=buf),
        processors=[add_log_level, TimeStamper(), JSONRenderer()],
        context={},
    )


@pytest.fixture(autouse=True)
def _reset():
    """Reset global config between tests."""
    reset_defaults()
    yield
    reset_defaults()


# ── BoundLogger ──────────────────────────────────────────────────────────────


class TestBoundLogger:
    def test_bind_creates_new_instance(self):
        buf = io.StringIO()
        log1 = _make_ours_logger(buf)
        log2 = log1.bind(user_id=42)
        assert log1 is not log2

    def test_bind_preserves_original_context(self):
        buf = io.StringIO()
        log1 = _make_ours_logger(buf).bind(a=1)
        log1.bind(b=2)
        # Original should not have 'b'
        assert "b" not in log1._context

    def test_bind_merges_context(self):
        buf = io.StringIO()
        log = _make_ours_logger(buf).bind(a=1).bind(b=2)
        assert log._context == {"a": 1, "b": 2}

    def test_bind_overwrites_key(self):
        buf = io.StringIO()
        log = _make_ours_logger(buf).bind(a=1).bind(a=99)
        assert log._context == {"a": 99}

    def test_unbind_removes_keys(self):
        buf = io.StringIO()
        log = _make_ours_logger(buf).bind(a=1, b=2).unbind("a")
        assert log._context == {"b": 2}

    def test_unbind_missing_key_is_noop(self):
        buf = io.StringIO()
        log = _make_ours_logger(buf).bind(a=1).unbind("nonexistent")
        assert log._context == {"a": 1}

    def test_new_replaces_context(self):
        buf = io.StringIO()
        log = _make_ours_logger(buf).bind(a=1, b=2).new(c=3)
        assert log._context == {"c": 3}

    def test_all_log_methods_produce_output(self):
        for method in ("debug", "info", "warning", "error", "critical"):
            buf = io.StringIO()
            log = _make_ours_logger(buf)
            getattr(log, method)("test")
            assert buf.getvalue().strip(), f"{method} produced no output"

    def test_exception_adds_exc_info(self):
        buf = io.StringIO()
        log = BoundLogger(
            logger=PrintLogger(file=buf),
            processors=[add_log_level, format_exc_info, ConsoleRenderer(colors=False)],
            context={},
        )
        try:
            raise ValueError("boom")
        except ValueError:
            log.exception("caught it")
        output = buf.getvalue()
        assert "ValueError" in output
        assert "boom" in output

    def test_bound_context_appears_in_output(self):
        buf = io.StringIO()
        log = _make_ours_logger(buf).bind(request_id="abc-123")
        log.info("handling")
        output = buf.getvalue()
        assert "request_id=abc-123" in output


# ── Processor Pipeline ───────────────────────────────────────────────────────


class TestProcessorPipeline:
    def test_processors_run_in_order(self):
        order = []

        def proc_a(logger, method, ed):
            order.append("a")
            return ed

        def proc_b(logger, method, ed):
            order.append("b")
            return ed

        def final(logger, method, ed):
            order.append("final")
            return str(ed)

        buf = io.StringIO()
        log = BoundLogger(
            logger=PrintLogger(file=buf),
            processors=[proc_a, proc_b, final],
            context={},
        )
        log.info("test")
        assert order == ["a", "b", "final"]

    def test_drop_event(self):
        def dropper(logger, method, ed):
            raise DropEvent()

        buf = io.StringIO()
        log = BoundLogger(
            logger=PrintLogger(file=buf),
            processors=[dropper, ConsoleRenderer(colors=False)],
            context={},
        )
        log.info("should not appear")
        assert buf.getvalue() == ""

    def test_processor_receives_event_and_kwargs(self):
        received = {}

        def capture(logger, method, ed):
            received.update(ed)
            return str(ed)

        buf = io.StringIO()
        log = BoundLogger(
            logger=PrintLogger(file=buf),
            processors=[capture],
            context={},
        )
        log.info("hello", foo="bar")
        assert received["event"] == "hello"
        assert received["foo"] == "bar"


# ── Built-in Processors ─────────────────────────────────────────────────────


class TestAddLogLevel:
    def test_adds_level_key(self):
        ed = add_log_level(None, "info", {"event": "test"})
        assert ed["level"] == "info"

    def test_level_matches_method(self):
        for method in ("debug", "info", "warning", "error", "critical"):
            ed = add_log_level(None, method, {"event": "test"})
            assert ed["level"] == method

    def test_matches_reference(self):
        our_ed = add_log_level(None, "warning", {"event": "x"})
        ref_ed = ref_stdlib.add_log_level(None, "warning", {"event": "x"})
        assert our_ed["level"] == ref_ed["level"]


class TestAddLoggerName:
    def test_adds_name_from_stdlib_logger(self):
        stdlib_logger = logging.getLogger("test.module")
        ed = add_logger_name(stdlib_logger, "info", {"event": "test"})
        assert ed["logger"] == "test.module"

    def test_empty_for_print_logger(self):
        ed = add_logger_name(PrintLogger(), "info", {"event": "test"})
        assert ed["logger"] == ""


class TestTimeStamper:
    def test_iso_format(self):
        ts = TimeStamper(fmt="iso", utc=True)
        ed = ts(None, "info", {"event": "test"})
        assert "timestamp" in ed
        assert "T" in ed["timestamp"]

    def test_unix_timestamp(self):
        ts = TimeStamper(fmt=None, utc=True)
        ed = ts(None, "info", {"event": "test"})
        assert isinstance(ed["timestamp"], float)

    def test_custom_format(self):
        ts = TimeStamper(fmt="%Y-%m-%d", utc=True)
        ed = ts(None, "info", {"event": "test"})
        # Should be a date string like "2026-03-27"
        assert len(ed["timestamp"]) == 10
        assert "-" in ed["timestamp"]

    def test_custom_key(self):
        ts = TimeStamper(key="ts")
        ed = ts(None, "info", {"event": "test"})
        assert "ts" in ed
        assert "timestamp" not in ed


class TestFormatExcInfo:
    def test_formats_exception_tuple(self):
        try:
            raise RuntimeError("test error")
        except RuntimeError:
            exc_info = sys.exc_info()

        ed = format_exc_info(None, "error", {"event": "fail", "exc_info": exc_info})
        assert "exc_info" not in ed
        assert "RuntimeError" in ed["exception"]
        assert "test error" in ed["exception"]

    def test_exc_info_true_captures_current(self):
        try:
            raise ValueError("caught")
        except ValueError:
            ed = format_exc_info(None, "error", {"event": "fail", "exc_info": True})
        assert "ValueError" in ed["exception"]

    def test_no_exc_info_is_noop(self):
        ed = format_exc_info(None, "info", {"event": "ok"})
        assert "exception" not in ed
        assert "exc_info" not in ed

    def test_exc_info_false_is_noop(self):
        ed = format_exc_info(None, "info", {"event": "ok", "exc_info": False})
        assert "exception" not in ed

    def test_exc_info_exception_instance(self):
        err = TypeError("bad type")
        ed = format_exc_info(None, "error", {"event": "fail", "exc_info": err})
        assert "TypeError" in ed["exception"]


# ── Renderers ────────────────────────────────────────────────────────────────


class TestJSONRenderer:
    def test_basic_output(self):
        renderer = JSONRenderer()
        result = renderer(None, "info", {"event": "hello", "key": "val"})
        parsed = json.loads(result)
        assert parsed["event"] == "hello"
        assert parsed["key"] == "val"

    def test_non_serializable_fallback(self):
        renderer = JSONRenderer()
        result = renderer(None, "info", {"event": "test", "data": {1, 2, 3}})
        parsed = json.loads(result)
        assert isinstance(parsed["data"], list)

    def test_datetime_serialization(self):
        import datetime

        renderer = JSONRenderer()
        now = datetime.datetime(2026, 3, 27, 14, 30, 0)
        result = renderer(None, "info", {"event": "test", "ts": now})
        parsed = json.loads(result)
        assert "2026-03-27" in parsed["ts"]

    def test_matches_reference_fields(self):
        """Both renderers should produce the same JSON keys."""
        ed = {"event": "test", "level": "info", "x": 1}
        ours = json.loads(JSONRenderer()(None, "info", dict(ed)))
        theirs = json.loads(ref_processors.JSONRenderer()(None, "info", dict(ed)))
        assert set(ours.keys()) == set(theirs.keys())


class TestKeyValueRenderer:
    def test_basic_output(self):
        renderer = KeyValueRenderer()
        result = renderer(None, "info", {"event": "hello", "n": 42})
        assert "event=hello" in result
        assert "n=42" in result

    def test_key_order(self):
        renderer = KeyValueRenderer(key_order=["event", "level"])
        result = renderer(None, "info", {"level": "info", "event": "test", "x": 1})
        # event and level should come before x
        event_pos = result.index("event=")
        level_pos = result.index("level=")
        x_pos = result.index("x=")
        assert event_pos < level_pos < x_pos

    def test_sort_keys(self):
        renderer = KeyValueRenderer(sort_keys=True)
        result = renderer(None, "info", {"z": 1, "a": 2, "m": 3})
        a_pos = result.index("a=")
        m_pos = result.index("m=")
        z_pos = result.index("z=")
        assert a_pos < m_pos < z_pos


class TestConsoleRenderer:
    def test_no_color_output_format(self):
        renderer = ConsoleRenderer(colors=False)
        ts = "2026-03-27T14:30:00+00:00"
        ed = {"event": "started", "level": "info", "timestamp": ts}
        result = renderer(None, "info", ed)
        assert "INFO" in result
        assert "started" in result
        assert "2026-03-27" in result

    def test_colored_output_contains_ansi(self):
        renderer = ConsoleRenderer(colors=True)
        ts = "2026-03-27T14:30:00+00:00"
        ed = {"event": "test", "level": "info", "timestamp": ts}
        result = renderer(None, "info", ed)
        assert "\033[" in result

    def test_context_kv_in_output(self):
        renderer = ConsoleRenderer(colors=False)
        ed = {
            "event": "request",
            "level": "info",
            "timestamp": "2026-03-27T14:30:00+00:00",
            "user_id": 42,
        }
        result = renderer(None, "info", ed)
        assert "user_id=42" in result

    def test_exception_in_output(self):
        renderer = ConsoleRenderer(colors=False)
        ed = {
            "event": "error",
            "level": "error",
            "exception": "Traceback ...\nValueError: boom",
        }
        result = renderer(None, "error", ed)
        assert "ValueError: boom" in result

    def test_fallback_timestamp(self):
        """When no timestamp in event_dict, renderer generates one."""
        renderer = ConsoleRenderer(colors=False)
        result = renderer(None, "info", {"event": "test", "level": "info"})
        # Should still have a timestamp-like pattern
        assert "20" in result  # year prefix


# ── Configuration ────────────────────────────────────────────────────────────


class TestConfigure:
    def test_configure_changes_processors(self):
        configure(processors=[add_log_level, JSONRenderer()])
        buf = io.StringIO()
        log = wrap_logger(PrintLogger(file=buf))
        log.info("test")
        output = buf.getvalue().strip()
        parsed = json.loads(output)
        assert parsed["event"] == "test"
        assert parsed["level"] == "info"

    def test_reset_defaults_restores(self):
        configure(processors=[JSONRenderer()])
        reset_defaults()
        buf = io.StringIO()
        log = wrap_logger(PrintLogger(file=buf))
        log.info("test")
        # Default uses ConsoleRenderer, not JSON
        output = buf.getvalue().strip()
        with pytest.raises(json.JSONDecodeError):
            json.loads(output)

    def test_configure_changes_factory(self):
        buf = io.StringIO()
        configure(logger_factory=PrintLoggerFactory(file=buf))
        log = get_logger()
        log.info("hello")
        assert "hello" in buf.getvalue()


# ── get_logger / wrap_logger ─────────────────────────────────────────────────


class TestGetLogger:
    def test_returns_bound_logger(self):
        log = get_logger()
        assert isinstance(log, BoundLogger)

    def test_initial_values_bound(self):
        log = get_logger(service="web")
        assert log._context == {"service": "web"}

    def test_caching(self):
        log1 = get_logger("mylogger")
        log2 = get_logger("mylogger")
        assert log1 is log2

    def test_no_cache_with_initial_values(self):
        log1 = get_logger(a=1)
        log2 = get_logger(a=1)
        # With initial values, caching is disabled
        assert log1 is not log2


class TestWrapLogger:
    def test_wraps_stdlib_logger(self):
        stdlib_logger = logging.getLogger("test_wrap")
        stdlib_logger.handlers.clear()
        buf = io.StringIO()
        handler = logging.StreamHandler(buf)
        handler.setFormatter(logging.Formatter("%(message)s"))
        stdlib_logger.addHandler(handler)
        stdlib_logger.setLevel(logging.DEBUG)

        log = wrap_logger(
            stdlib_logger,
            processors=[add_log_level, ConsoleRenderer(colors=False)],
        )
        log.info("via stdlib")
        assert "via stdlib" in buf.getvalue()


# ── setup_logging ────────────────────────────────────────────────────────────


class TestSetupLogging:
    def test_console_mode(self):
        buf = io.StringIO()
        log = setup_logging(renderer="console", colors=False, stream=buf)
        log.info("console test")
        output = buf.getvalue()
        assert "INFO" in output
        assert "console test" in output

    def test_json_mode(self):
        buf = io.StringIO()
        log = setup_logging(renderer="json", stream=buf)
        log.info("json test", key="val")
        output = buf.getvalue().strip()
        parsed = json.loads(output)
        assert parsed["event"] == "json test"
        assert parsed["key"] == "val"

    def test_kv_mode(self):
        buf = io.StringIO()
        log = setup_logging(renderer="kv", stream=buf)
        log.info("kv test", n=1)
        output = buf.getvalue()
        assert "event=kv test" in output
        assert "n=1" in output

    def test_custom_level(self):
        buf = io.StringIO()
        log = setup_logging(
            level="WARNING", renderer="console", colors=False, stream=buf
        )
        log.info("should not appear")
        log.warning("should appear")
        output = buf.getvalue()
        assert "should not appear" not in output
        assert "should appear" in output

    def test_returns_bound_logger(self):
        log = setup_logging(stream=io.StringIO())
        assert isinstance(log, BoundLogger)


# ── Utilities ────────────────────────────────────────────────────────────────


class TestTruncateString:
    def test_short_string_unchanged(self):
        assert truncate_string("hello", 10) == "hello"

    def test_long_string_truncated(self):
        result = truncate_string("a" * 100, 10)
        assert result.startswith("a" * 10)
        assert "[90 more chars]" in result

    def test_exact_length_unchanged(self):
        assert truncate_string("12345", 5) == "12345"

    def test_custom_suffix(self):
        result = truncate_string("abcdef", 3, suffix="~~")
        assert result == "abc~~[3 more chars]"


class TestTruncateBase64:
    def test_non_data_url_unchanged(self):
        assert truncate_base64("https://example.com") == "https://example.com"

    def test_short_data_url_unchanged(self):
        url = "data:image/png;base64,abc"
        assert truncate_base64(url, max_length=100) == url

    def test_long_data_url_truncated(self):
        payload = "x" * 200
        url = f"data:image/png;base64,{payload}"
        result = truncate_base64(url, max_length=50)
        assert result.startswith("data:image/png;base64,")
        assert "[150 more chars]" in result


# ── Thread Safety ────────────────────────────────────────────────────────────


class TestThreadSafety:
    def test_concurrent_bind_and_log(self):
        """Multiple threads binding and logging should not raise."""
        buf = io.StringIO()
        base_log = _make_ours_logger(buf)
        errors: list[Exception] = []

        def worker(i: int) -> None:
            try:
                log = base_log.bind(thread=i)
                for j in range(50):
                    log.info("msg", iteration=j)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"

    def test_concurrent_get_logger(self):
        """Concurrent get_logger calls should not raise."""
        errors: list[Exception] = []

        def worker(i: int) -> None:
            try:
                log = get_logger(f"thread-{i}")
                log.info("hello")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(16)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors


# ── Cross-validation with structlog ──────────────────────────────────────────


class TestCrossValidation:
    """Verify our output is structurally compatible with structlog."""

    def test_json_output_same_keys(self):
        """Our JSON renderer and structlog's should produce identical key sets."""
        ed_ours = {"event": "test", "level": "info", "x": 1}
        ed_theirs = dict(ed_ours)

        ours = json.loads(JSONRenderer()(None, "info", ed_ours))
        theirs = json.loads(ref_processors.JSONRenderer()(None, "info", ed_theirs))
        assert set(ours.keys()) == set(theirs.keys())

    def test_add_log_level_same_output(self):
        ed_ours = add_log_level(None, "error", {"event": "x"})
        ed_theirs = ref_stdlib.add_log_level(None, "error", {"event": "x"})
        assert ed_ours["level"] == ed_theirs["level"]

    def test_timestamper_iso_format_compatible(self):
        """Both should produce an ISO 8601 timestamp under the same key."""
        our_ts = TimeStamper(fmt="iso", utc=True)
        ref_ts = ref_processors.TimeStamper(fmt="iso", utc=True)

        ed_ours = our_ts(None, "info", {"event": "x"})
        ed_theirs = ref_ts(None, "info", {"event": "x"})

        assert "timestamp" in ed_ours
        assert "timestamp" in ed_theirs
        # Both should be ISO format strings containing 'T'
        assert "T" in ed_ours["timestamp"]
        assert "T" in ed_theirs["timestamp"]

    def test_bound_logger_bind_semantics(self):
        """bind() should be non-mutating (copy-on-write) like structlog."""
        # Ours
        buf = io.StringIO()
        our_log = _make_ours_logger(buf)
        our_log1 = our_log.bind(a=1)
        our_log2 = our_log1.bind(b=2)
        assert "a" in our_log1._context
        assert "b" not in our_log1._context
        assert "a" in our_log2._context
        assert "b" in our_log2._context

        # Structlog
        ref_log = ref_structlog.get_logger()
        ref_log1 = ref_log.bind(a=1)
        ref_log2 = ref_log1.bind(b=2)
        # Both should follow the same copy-on-write pattern
        assert ref_log1 is not ref_log2
