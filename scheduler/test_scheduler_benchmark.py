"""Benchmark: zerodep scheduler vs APScheduler / schedule / croniter."""

import os
import sys
from datetime import datetime

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from scheduler import (
    Scheduler,
    _cron_next_fire_time,
    every,
    parse_cron,
)

croniter_mod = pytest.importorskip("croniter", reason="croniter not installed")
from croniter import croniter  # noqa: E402

apscheduler = pytest.importorskip("apscheduler", reason="APScheduler not installed")
from apscheduler.triggers.cron import CronTrigger as APCronTrigger  # noqa: E402

schedule_mod = pytest.importorskip("schedule", reason="schedule not installed")


# ── Cron Parsing ──


_CRON_EXPRESSIONS = [
    "* * * * *",
    "0 9 * * 1-5",
    "*/15 */6 1,15 * *",
    "30 3 1-7 1,4,7,10 *",
    "0 0 * * 0",
]


class TestCronParsing:
    def test_zerodep(self, benchmark):
        def run():
            for expr in _CRON_EXPRESSIONS:
                parse_cron(expr)

        benchmark(run)

    def test_croniter(self, benchmark):
        now = datetime.now()

        def run():
            for expr in _CRON_EXPRESSIONS:
                croniter(expr, now)

        benchmark(run)

    def test_apscheduler(self, benchmark):
        def run():
            for expr in _CRON_EXPRESSIONS:
                APCronTrigger.from_crontab(expr)

        benchmark(run)


# ── Next Fire Time Calculation ──


_SPECS = [parse_cron(e) for e in _CRON_EXPRESSIONS]
_NOW = datetime(2026, 3, 27, 10, 30, 0)


class TestNextFireTime:
    def test_zerodep(self, benchmark):
        def run():
            for spec in _SPECS:
                _cron_next_fire_time(spec, _NOW)

        benchmark(run)

    def test_croniter(self, benchmark):
        def run():
            for expr in _CRON_EXPRESSIONS:
                c = croniter(expr, _NOW)
                c.get_next(datetime)

        benchmark(run)

    def test_apscheduler(self, benchmark):
        triggers = [APCronTrigger.from_crontab(e) for e in _CRON_EXPRESSIONS]

        def run():
            for t in triggers:
                t.get_next_fire_time(None, _NOW)

        benchmark(run)


# ── Batch Next Fire Time (100 iterations) ──


class TestBatchNextFireTime:
    def test_zerodep(self, benchmark):
        spec = parse_cron("*/5 9-17 * * 1-5")

        def run():
            dt = _NOW
            for _ in range(100):
                dt = _cron_next_fire_time(spec, dt)

        benchmark(run)

    def test_croniter(self, benchmark):
        def run():
            c = croniter("*/5 9-17 * * 1-5", _NOW)
            for _ in range(100):
                c.get_next(datetime)

        benchmark(run)

    def test_apscheduler(self, benchmark):
        trigger = APCronTrigger.from_crontab("*/5 9-17 * * 1-5")

        def run():
            dt = _NOW
            for _ in range(100):
                dt = trigger.get_next_fire_time(None, dt)

        benchmark(run)


# ── Job Add Overhead ──


class TestJobAddOverhead:
    def test_zerodep(self, benchmark):
        def run():
            sched = Scheduler()
            for i in range(100):
                sched.add_job(lambda: None, every(60, "seconds"), id=f"j{i}")

        benchmark(run)

    def test_schedule(self, benchmark):
        def run():
            s = schedule_mod.Scheduler()
            for i in range(100):
                s.every(60).seconds.do(lambda: None)

        benchmark(run)
