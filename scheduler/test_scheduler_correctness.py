"""Correctness tests: zerodep scheduler."""

import os
import sys
import time
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from scheduler import (
    CronSpec,
    CronTrigger,
    EventType,
    IntervalTrigger,
    InvalidCronExpression,
    Job,
    JobNotFound,
    JobStatus,
    OnceTrigger,
    Scheduler,
    SchedulerAlreadyRunning,
    _cron_next_fire_time,
    cron,
    every,
    once,
    parse_cron,
)

# ── Cron Parser ──


class TestParseCron:
    def test_all_stars(self):
        spec = parse_cron("* * * * *")
        assert spec.minutes == frozenset(range(0, 60))
        assert spec.hours == frozenset(range(0, 24))
        assert spec.days == frozenset(range(1, 32))
        assert spec.months == frozenset(range(1, 13))
        assert spec.weekdays == frozenset(range(0, 7))

    def test_specific_values(self):
        spec = parse_cron("30 9 15 6 3")
        assert spec.minutes == frozenset({30})
        assert spec.hours == frozenset({9})
        assert spec.days == frozenset({15})
        assert spec.months == frozenset({6})
        assert spec.weekdays == frozenset({3})

    def test_ranges(self):
        spec = parse_cron("0-5 9-17 1-15 1-6 1-5")
        assert spec.minutes == frozenset(range(0, 6))
        assert spec.hours == frozenset(range(9, 18))
        assert spec.days == frozenset(range(1, 16))
        assert spec.months == frozenset(range(1, 7))
        assert spec.weekdays == frozenset(range(1, 6))

    def test_step(self):
        spec = parse_cron("*/15 */6 */5 */3 */2")
        assert spec.minutes == frozenset({0, 15, 30, 45})
        assert spec.hours == frozenset({0, 6, 12, 18})
        assert spec.days == frozenset({1, 6, 11, 16, 21, 26, 31})
        assert spec.months == frozenset({1, 4, 7, 10})
        assert spec.weekdays == frozenset({0, 2, 4, 6})

    def test_range_with_step(self):
        spec = parse_cron("1-30/10 0-12/4 * * *")
        assert spec.minutes == frozenset({1, 11, 21})
        assert spec.hours == frozenset({0, 4, 8, 12})

    def test_list(self):
        spec = parse_cron("0,15,30,45 8,12,18 * * *")
        assert spec.minutes == frozenset({0, 15, 30, 45})
        assert spec.hours == frozenset({8, 12, 18})

    def test_month_names(self):
        spec = parse_cron("0 0 1 jan,jun,dec *")
        assert spec.months == frozenset({1, 6, 12})

    def test_dow_names(self):
        spec = parse_cron("0 9 * * mon-fri")
        assert spec.weekdays == frozenset({1, 2, 3, 4, 5})

    def test_expression_preserved(self):
        expr = "30 9 * * 1-5"
        spec = parse_cron(expr)
        assert spec.expression == expr

    def test_repr(self):
        spec = parse_cron("0 9 * * *")
        assert "0 9 * * *" in repr(spec)


class TestParseCronErrors:
    def test_wrong_field_count(self):
        with pytest.raises(InvalidCronExpression, match="expected 5 fields"):
            parse_cron("* * *")

    def test_too_many_fields(self):
        with pytest.raises(InvalidCronExpression, match="expected 5 fields"):
            parse_cron("* * * * * *")

    def test_out_of_range(self):
        with pytest.raises(InvalidCronExpression, match="out of bounds"):
            parse_cron("60 * * * *")

    def test_invalid_range(self):
        with pytest.raises(InvalidCronExpression):
            parse_cron("5-2 * * * *")  # lo > hi

    def test_invalid_step(self):
        with pytest.raises(InvalidCronExpression, match="invalid step"):
            parse_cron("*/abc * * * *")

    def test_zero_step(self):
        with pytest.raises(InvalidCronExpression, match="step must be >= 1"):
            parse_cron("*/0 * * * *")

    def test_invalid_value(self):
        with pytest.raises(InvalidCronExpression, match="invalid value"):
            parse_cron("abc * * * *")

    def test_empty_string(self):
        with pytest.raises(InvalidCronExpression):
            parse_cron("")


# ── Cron Next Fire Time ──


class TestCronNextFireTime:
    def test_simple_every_minute(self):
        spec = parse_cron("* * * * *")
        now = datetime(2026, 3, 27, 10, 30, 15)
        nxt = _cron_next_fire_time(spec, now)
        assert nxt == datetime(2026, 3, 27, 10, 31, 0)

    def test_specific_minute(self):
        spec = parse_cron("45 * * * *")
        now = datetime(2026, 3, 27, 10, 30, 0)
        nxt = _cron_next_fire_time(spec, now)
        assert nxt == datetime(2026, 3, 27, 10, 45, 0)

    def test_minute_rollover_to_next_hour(self):
        spec = parse_cron("15 * * * *")
        now = datetime(2026, 3, 27, 10, 30, 0)
        nxt = _cron_next_fire_time(spec, now)
        assert nxt == datetime(2026, 3, 27, 11, 15, 0)

    def test_specific_hour(self):
        spec = parse_cron("0 9 * * *")
        now = datetime(2026, 3, 27, 10, 0, 0)
        nxt = _cron_next_fire_time(spec, now)
        assert nxt == datetime(2026, 3, 28, 9, 0, 0)

    def test_specific_hour_same_day(self):
        spec = parse_cron("0 15 * * *")
        now = datetime(2026, 3, 27, 10, 0, 0)
        nxt = _cron_next_fire_time(spec, now)
        assert nxt == datetime(2026, 3, 27, 15, 0, 0)

    def test_weekday_filter(self):
        spec = parse_cron("0 9 * * 1")  # Monday (cron: 1=Mon)
        # 2026-03-27 is a Friday
        now = datetime(2026, 3, 27, 10, 0, 0)
        nxt = _cron_next_fire_time(spec, now)
        # Next Monday is 2026-03-30
        assert nxt == datetime(2026, 3, 30, 9, 0, 0)
        assert nxt.weekday() == 0  # Python Monday

    def test_month_rollover(self):
        spec = parse_cron("0 0 1 * *")
        now = datetime(2026, 3, 15, 0, 0, 0)
        nxt = _cron_next_fire_time(spec, now)
        assert nxt == datetime(2026, 4, 1, 0, 0, 0)

    def test_dom_and_dow_or_logic(self):
        # When both dom and dow are restricted, match is OR
        spec = parse_cron("0 0 15 * 1")  # 15th of month OR Monday
        now = datetime(2026, 3, 27, 1, 0, 0)  # Friday
        nxt = _cron_next_fire_time(spec, now)
        # Next Monday (Mar 30) or 15th (Apr 15) — Monday comes first
        assert nxt == datetime(2026, 3, 30, 0, 0, 0)

    def test_year_boundary(self):
        spec = parse_cron("0 0 1 1 *")
        now = datetime(2026, 12, 31, 23, 59, 0)
        nxt = _cron_next_fire_time(spec, now)
        assert nxt == datetime(2027, 1, 1, 0, 0, 0)


# ── IntervalTrigger ──


class TestIntervalTrigger:
    def test_basic(self):
        t = IntervalTrigger(60)
        now = datetime(2026, 3, 27, 10, 0, 0)
        nxt = t.next_fire_time(now)
        assert nxt == now + timedelta(seconds=60)

    def test_with_start_time(self):
        start = datetime(2026, 3, 27, 10, 0, 0)
        t = IntervalTrigger(300, start_time=start)
        now = datetime(2026, 3, 27, 10, 7, 0)  # 420s after start
        nxt = t.next_fire_time(now)
        # 420/300 = 1.4 -> periods=2 -> 600s after start
        assert nxt == start + timedelta(seconds=600)

    def test_before_start_time(self):
        start = datetime(2026, 3, 27, 12, 0, 0)
        t = IntervalTrigger(60, start_time=start)
        now = datetime(2026, 3, 27, 11, 0, 0)
        nxt = t.next_fire_time(now)
        assert nxt == start

    def test_invalid_interval(self):
        with pytest.raises(ValueError, match="positive"):
            IntervalTrigger(0)
        with pytest.raises(ValueError, match="positive"):
            IntervalTrigger(-1)

    def test_repr(self):
        t = IntervalTrigger(30)
        assert "30" in repr(t)


# ── CronTrigger ──


class TestCronTrigger:
    def test_basic(self):
        t = CronTrigger("0 9 * * *")
        now = datetime(2026, 3, 27, 10, 0, 0)
        nxt = t.next_fire_time(now)
        assert nxt == datetime(2026, 3, 28, 9, 0, 0)

    def test_repr(self):
        t = CronTrigger("30 9 * * 1-5")
        assert "30 9 * * 1-5" in repr(t)

    def test_spec_property(self):
        t = CronTrigger("0 0 * * *")
        assert isinstance(t.spec, CronSpec)


# ── OnceTrigger ──


class TestOnceTrigger:
    def test_fires_once(self):
        run_time = datetime(2026, 4, 1, 9, 0, 0)
        t = OnceTrigger(run_time)
        now = datetime(2026, 3, 27, 10, 0, 0)
        assert t.next_fire_time(now) == run_time

    def test_returns_none_after_fired(self):
        run_time = datetime(2026, 4, 1, 9, 0, 0)
        t = OnceTrigger(run_time)
        t.mark_fired()
        assert t.next_fire_time(datetime(2026, 3, 27, 10, 0, 0)) is None

    def test_returns_none_if_past(self):
        run_time = datetime(2026, 3, 1, 9, 0, 0)
        t = OnceTrigger(run_time)
        now = datetime(2026, 3, 27, 10, 0, 0)
        assert t.next_fire_time(now) is None

    def test_repr(self):
        dt = datetime(2026, 4, 1, 9, 0, 0)
        t = OnceTrigger(dt)
        assert "2026" in repr(t)


# ── Convenience constructors ──


class TestConvenience:
    def test_every_seconds(self):
        t = every(30, "seconds")
        assert isinstance(t, IntervalTrigger)
        assert t.seconds == 30

    def test_every_minutes(self):
        t = every(5, "minutes")
        assert t.seconds == 300

    def test_every_hours(self):
        t = every(2, "hours")
        assert t.seconds == 7200

    def test_every_singular_form(self):
        t = every(1, "second")
        assert t.seconds == 1
        t = every(1, "minute")
        assert t.seconds == 60
        t = every(1, "hour")
        assert t.seconds == 3600

    def test_every_invalid_unit(self):
        with pytest.raises(ValueError, match="Unknown unit"):
            every(1, "days")

    def test_cron_function(self):
        t = cron("0 9 * * *")
        assert isinstance(t, CronTrigger)

    def test_once_function(self):
        dt = datetime(2026, 4, 1, 9, 0, 0)
        t = once(dt)
        assert isinstance(t, OnceTrigger)
        assert t.run_time == dt


# ── Job ──


class TestJob:
    def test_defaults(self):
        job = Job(
            id="test",
            name="test_job",
            fn=lambda: None,
            trigger=IntervalTrigger(60),
        )
        assert job.status == JobStatus.pending
        assert job.args == ()
        assert job.kwargs == {}

    def test_repr(self):
        job = Job(
            id="abc",
            name="my_job",
            fn=lambda: None,
            trigger=IntervalTrigger(60),
        )
        r = repr(job)
        assert "abc" in r
        assert "my_job" in r


# ── Scheduler Lifecycle ──


class TestSchedulerLifecycle:
    def test_start_and_shutdown(self):
        sched = Scheduler()
        sched.start()
        assert sched.running
        sched.shutdown()
        assert not sched.running

    def test_context_manager(self):
        with Scheduler() as sched:
            assert sched.running
        assert not sched.running

    def test_double_start_raises(self):
        sched = Scheduler()
        sched.start()
        try:
            with pytest.raises(SchedulerAlreadyRunning):
                sched.start()
        finally:
            sched.shutdown()

    def test_shutdown_without_start(self):
        sched = Scheduler()
        sched.shutdown()  # should not raise


# ── Job Management ──


class TestJobManagement:
    def test_add_job(self):
        sched = Scheduler()
        job = sched.add_job(lambda: None, every(60, "seconds"), id="j1")
        assert job.id == "j1"
        assert sched.get_job("j1") is job

    def test_add_job_auto_id(self):
        sched = Scheduler()
        job = sched.add_job(lambda: None, every(60, "seconds"))
        assert job.id  # non-empty
        assert sched.get_job(job.id) is job

    def test_add_job_auto_name(self):
        def my_func():
            pass

        sched = Scheduler()
        job = sched.add_job(my_func, every(60, "seconds"))
        assert job.name == "my_func"

    def test_remove_job(self):
        sched = Scheduler()
        sched.add_job(lambda: None, every(60, "seconds"), id="j1")
        sched.remove_job("j1")
        assert sched.get_job("j1") is None

    def test_remove_nonexistent_raises(self):
        sched = Scheduler()
        with pytest.raises(JobNotFound):
            sched.remove_job("nonexistent")

    def test_get_jobs(self):
        sched = Scheduler()
        sched.add_job(lambda: None, every(60, "seconds"), id="a")
        sched.add_job(lambda: None, every(30, "seconds"), id="b")
        jobs = sched.get_jobs()
        assert len(jobs) == 2
        ids = {j.id for j in jobs}
        assert ids == {"a", "b"}

    def test_pause_and_resume(self):
        sched = Scheduler()
        sched.add_job(lambda: None, every(60, "seconds"), id="j1")
        sched.pause_job("j1")
        job = sched.get_job("j1")
        assert job is not None
        assert job.status == JobStatus.paused

        sched.resume_job("j1")
        job = sched.get_job("j1")
        assert job is not None
        assert job.status == JobStatus.pending

    def test_pause_nonexistent_raises(self):
        sched = Scheduler()
        with pytest.raises(JobNotFound):
            sched.pause_job("nope")

    def test_resume_nonexistent_raises(self):
        sched = Scheduler()
        with pytest.raises(JobNotFound):
            sched.resume_job("nope")

    def test_scheduled_job_decorator(self):
        sched = Scheduler()

        @sched.scheduled_job(every(10, "seconds"), id="deco")
        def my_task():
            return 42

        assert sched.get_job("deco") is not None
        assert my_task() == 42  # decorator preserves function


# ── Job Execution ──


class TestJobExecution:
    def test_sync_job_runs(self):
        results = []
        sched = Scheduler(tick_interval=0.01)
        sched.add_job(
            lambda: results.append(1),
            every(0.05, "seconds"),
            id="j1",
        )
        sched.start()
        time.sleep(0.2)
        sched.shutdown()
        assert len(results) >= 2

    def test_async_job_runs(self):
        results = []

        async def async_task():
            results.append(1)

        sched = Scheduler(tick_interval=0.01)
        sched.add_job(async_task, every(0.05, "seconds"), id="j1")
        sched.start()
        time.sleep(0.2)
        sched.shutdown()
        assert len(results) >= 2

    def test_run_job_immediate(self):
        calls = []
        sched = Scheduler()
        sched.add_job(lambda: calls.append(1), every(3600, "seconds"), id="j1")
        sched.run_job("j1")
        assert len(calls) == 1

    def test_run_job_nonexistent_raises(self):
        sched = Scheduler()
        with pytest.raises(JobNotFound):
            sched.run_job("nope")

    def test_once_trigger_fires_once(self):
        results = []
        run_at = datetime.now() + timedelta(seconds=0.05)
        sched = Scheduler(tick_interval=0.01)
        sched.add_job(
            lambda: results.append(1),
            once(run_at),
            id="once1",
        )
        sched.start()
        time.sleep(0.3)
        sched.shutdown()
        assert len(results) == 1

    def test_paused_job_does_not_run(self):
        results = []
        sched = Scheduler(tick_interval=0.01)
        sched.add_job(
            lambda: results.append(1),
            every(0.02, "seconds"),
            id="j1",
        )
        sched.pause_job("j1")
        sched.start()
        time.sleep(0.15)
        sched.shutdown()
        assert len(results) == 0


# ── Callbacks ──


class TestCallbacks:
    def test_on_success(self):
        results = []

        def my_task():
            return 42

        sched = Scheduler(tick_interval=0.01)
        sched.add_job(
            my_task,
            every(0.05, "seconds"),
            id="j1",
            on_success=lambda v: results.append(v),
        )
        sched.start()
        time.sleep(0.15)
        sched.shutdown()
        assert 42 in results

    def test_on_error(self):
        errors = []

        def bad_task():
            raise ValueError("boom")

        sched = Scheduler(tick_interval=0.01)
        sched.add_job(
            bad_task,
            every(0.05, "seconds"),
            id="j1",
            on_error=lambda e: errors.append(str(e)),
        )
        sched.start()
        time.sleep(0.15)
        sched.shutdown()
        assert any("boom" in e for e in errors)


# ── Event Listeners ──


class TestEventListeners:
    def test_job_added_event(self):
        events = []
        sched = Scheduler()
        sched.add_listener(lambda e: events.append(e))
        sched.add_job(lambda: None, every(60, "seconds"), id="j1")
        assert any(e.event_type == EventType.job_added for e in events)
        assert events[-1].job_id == "j1"

    def test_job_removed_event(self):
        events = []
        sched = Scheduler()
        sched.add_job(lambda: None, every(60, "seconds"), id="j1")
        sched.add_listener(lambda e: events.append(e))
        sched.remove_job("j1")
        assert any(e.event_type == EventType.job_removed for e in events)

    def test_job_executed_event(self):
        events = []
        sched = Scheduler(tick_interval=0.01)
        sched.add_listener(lambda e: events.append(e))
        sched.add_job(lambda: "ok", every(0.05, "seconds"), id="j1")
        sched.start()
        time.sleep(0.15)
        sched.shutdown()
        exec_events = [e for e in events if e.event_type == EventType.job_executed]
        assert len(exec_events) >= 1
        assert exec_events[0].return_value == "ok"

    def test_job_error_event(self):
        events = []

        def bad():
            raise RuntimeError("fail")

        sched = Scheduler(tick_interval=0.01)
        sched.add_listener(lambda e: events.append(e))
        sched.add_job(bad, every(0.05, "seconds"), id="j1")
        sched.start()
        time.sleep(0.15)
        sched.shutdown()
        err_events = [e for e in events if e.event_type == EventType.job_error]
        assert len(err_events) >= 1
        assert isinstance(err_events[0].exception, RuntimeError)

    def test_remove_listener(self):
        events = []

        def cb(e):
            events.append(e)

        sched = Scheduler()
        sched.add_listener(cb)
        sched.add_job(lambda: None, every(60, "seconds"), id="j1")
        assert len(events) == 1

        sched.remove_listener(cb)
        sched.add_job(lambda: None, every(60, "seconds"), id="j2")
        assert len(events) == 1  # no new events


# ── Misfire Grace Time ──


class TestMisfireGraceTime:
    def test_missed_job_skipped(self):
        events = []
        sched = Scheduler(tick_interval=0.01)
        sched.add_listener(lambda e: events.append(e))

        # Create a job with very tight grace time
        job = sched.add_job(
            lambda: None,
            every(0.02, "seconds"),
            id="j1",
            misfire_grace_time=0.001,  # 1ms grace
        )
        # Artificially set next_run_time far in the past
        job.next_run_time = datetime.now() - timedelta(seconds=5)

        sched.start()
        time.sleep(0.1)
        sched.shutdown()

        missed = [e for e in events if e.event_type == EventType.job_missed]
        assert len(missed) >= 1

    def test_late_but_within_grace(self):
        results = []
        sched = Scheduler(tick_interval=0.01)

        job = sched.add_job(
            lambda: results.append(1),
            every(0.05, "seconds"),
            id="j1",
            misfire_grace_time=10.0,  # generous
        )
        # Set next_run_time slightly in the past
        job.next_run_time = datetime.now() - timedelta(seconds=0.01)

        sched.start()
        time.sleep(0.1)
        sched.shutdown()

        assert len(results) >= 1  # still executed


# ── Job with args/kwargs ──


class TestJobArgs:
    def test_args(self):
        results = []

        def task(a, b):
            results.append(a + b)

        sched = Scheduler(tick_interval=0.01)
        sched.add_job(task, every(0.05, "seconds"), id="j1", args=(3, 4))
        sched.start()
        time.sleep(0.15)
        sched.shutdown()
        assert 7 in results

    def test_kwargs(self):
        results = []

        def task(x=0, y=0):
            results.append(x * y)

        sched = Scheduler(tick_interval=0.01)
        sched.add_job(
            task,
            every(0.05, "seconds"),
            id="j1",
            kwargs={"x": 5, "y": 6},
        )
        sched.start()
        time.sleep(0.15)
        sched.shutdown()
        assert 30 in results
