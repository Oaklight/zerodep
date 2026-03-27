"""Benchmark: zerodep structlog vs structlog."""

import os
import sys

import pytest

# Same import pattern as test_structlog_correctness.py to avoid
# name collision between our structlog/ dir and the installed package.
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
_cached = sys.modules.pop("structlog", None)

try:
    import structlog.dev as ref_dev
    import structlog.processors as ref_processors

    import structlog as ref_structlog

    if not hasattr(ref_structlog, "configure"):
        raise ImportError("Not the real structlog")
except ImportError:
    pytest.skip("structlog not installed", allow_module_level=True)
finally:
    sys.path = _saved_path
    for _k in list(sys.modules):
        if _k == "structlog" or _k.startswith("structlog."):
            sys.modules.pop(_k, None)
    if _cached is not None:
        sys.modules["structlog"] = _cached

sys.path.insert(0, _this_dir)
from structlog import (
    BoundLogger,
    ConsoleRenderer,
    JSONRenderer,
    PrintLogger,
    TimeStamper,
    add_log_level,
)

# Sink that discards output
_DEVNULL = open(os.devnull, "w")


def _our_logger(renderer):
    return BoundLogger(
        logger=PrintLogger(file=_DEVNULL),
        processors=[add_log_level, TimeStamper(), renderer],
        context={},
    )


def _ref_logger(renderer):
    ref_structlog.configure(
        processors=[
            ref_structlog.stdlib.add_log_level,
            ref_processors.TimeStamper(fmt="iso", utc=True),
            renderer,
        ],
        wrapper_class=ref_structlog.BoundLogger,
        logger_factory=ref_structlog.PrintLoggerFactory(file=_DEVNULL),
        cache_logger_on_first_use=False,
    )
    return ref_structlog.get_logger()


# ── Simple log call ──────────────────────────────────────────────────────────


class TestSimpleLog:
    def test_zerodep(self, benchmark):
        log = _our_logger(ConsoleRenderer(colors=False))
        benchmark(log.info, "hello world")

    def test_structlog(self, benchmark):
        log = _ref_logger(ref_dev.ConsoleRenderer(colors=False))
        benchmark(log.info, "hello world")


# ── Log with bound context ──────────────────────────────────────────────────


class TestBoundLog:
    def test_zerodep(self, benchmark):
        log = _our_logger(ConsoleRenderer(colors=False)).bind(
            request_id="abc-123", user_id=42
        )
        benchmark(log.info, "request handled", status=200)

    def test_structlog(self, benchmark):
        log = _ref_logger(ref_dev.ConsoleRenderer(colors=False)).bind(
            request_id="abc-123", user_id=42
        )
        benchmark(log.info, "request handled", status=200)


# ── JSON rendering ──────────────────────────────────────────────────────────


class TestJSONRendering:
    def test_zerodep(self, benchmark):
        log = _our_logger(JSONRenderer())
        benchmark(log.info, "event", key="value", count=42)

    def test_structlog(self, benchmark):
        log = _ref_logger(ref_processors.JSONRenderer())
        benchmark(log.info, "event", key="value", count=42)


# ── Bind + log (measures bind overhead) ──────────────────────────────────────


class TestBindAndLog:
    def test_zerodep(self, benchmark):
        base = _our_logger(ConsoleRenderer(colors=False))

        def do():
            log = base.bind(req="abc")
            log.info("handled")

        benchmark(do)

    def test_structlog(self, benchmark):
        base = _ref_logger(ref_dev.ConsoleRenderer(colors=False))

        def do():
            log = base.bind(req="abc")
            log.info("handled")

        benchmark(do)
