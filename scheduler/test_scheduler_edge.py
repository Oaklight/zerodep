"""Edge-behavior tests for scheduler concurrency and shutdown."""

import os
import sys
import threading
import time

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from scheduler import (
    EventType,
    JobStatus,
    Scheduler,
    every,
)

# ── Shutdown Behavior ───────────────────────────────────────────────────


class TestShutdownBehavior:
    """Tests for clean shutdown."""

    def test_shutdown_stops_scheduling(self):
        """After shutdown(), no new jobs should fire."""
        results = []
        sched = Scheduler(tick_interval=0.01)
        sched.add_job(
            lambda: results.append(1),
            every(0.02, "seconds"),
            id="j1",
        )
        sched.start()
        time.sleep(0.1)
        sched.shutdown()
        count_at_shutdown = len(results)
        assert count_at_shutdown >= 1

        # After shutdown, no more jobs should fire
        time.sleep(0.1)
        assert len(results) == count_at_shutdown

    def test_shutdown_with_running_job(self):
        """Shutdown during job execution should not deadlock."""
        started = threading.Event()
        results = []

        def slow_job():
            started.set()
            time.sleep(0.2)
            results.append(1)

        sched = Scheduler(tick_interval=0.01)
        sched.add_job(slow_job, every(0.02, "seconds"), id="j1")
        sched.start()

        # Wait for the job to actually start executing
        started.wait(timeout=2.0)
        assert started.is_set(), "Job did not start"

        # Shutdown while job is running -- should not deadlock
        # Use a timeout to detect deadlock
        shutdown_done = threading.Event()

        def do_shutdown():
            sched.shutdown(wait=True)
            shutdown_done.set()

        t = threading.Thread(target=do_shutdown)
        t.start()
        t.join(timeout=5.0)
        assert shutdown_done.is_set(), "Shutdown deadlocked"

    def test_shutdown_without_start_is_safe(self):
        """Calling shutdown() without start() should not raise."""
        sched = Scheduler()
        sched.shutdown()  # should be a no-op

    def test_shutdown_wait_false_returns_immediately(self):
        """shutdown(wait=False) should return without blocking."""
        sched = Scheduler(tick_interval=0.01)
        sched.add_job(lambda: time.sleep(0.5), every(0.02, "seconds"), id="j1")
        sched.start()
        time.sleep(0.05)

        t0 = time.monotonic()
        sched.shutdown(wait=False)
        elapsed = time.monotonic() - t0
        # Should return quickly (not wait for running job)
        assert elapsed < 1.0
        # Clean up: wait for thread to finish
        time.sleep(0.6)


# ── Job State Safety ────────────────────────────────────────────────────


class TestJobStateSafety:
    """Tests for thread-safe job state transitions."""

    def test_concurrent_run_job_does_not_double_execute(self):
        """Manual run_job() should skip if job is already running."""
        call_count = 0
        started = threading.Event()
        proceed = threading.Event()

        def blocking_job():
            nonlocal call_count
            call_count += 1
            started.set()
            proceed.wait(timeout=5.0)

        sched = Scheduler()
        sched.add_job(blocking_job, every(3600, "seconds"), id="j1")

        # Start the job in a thread
        t = threading.Thread(target=sched.run_job, args=("j1",))
        t.start()
        started.wait(timeout=2.0)

        # Job is running; concurrent run_job should skip
        result = sched.run_job("j1")
        assert result is None  # skipped

        # Let the first job finish
        proceed.set()
        t.join(timeout=2.0)
        assert call_count == 1

    def test_job_status_reset_after_execution(self):
        """Job status should return to pending after execution completes."""
        sched = Scheduler()
        sched.add_job(lambda: 42, every(3600, "seconds"), id="j1")

        # Run immediately
        sched.run_job("j1")

        job = sched.get_job("j1")
        assert job is not None
        assert job.status == JobStatus.pending

    def test_job_status_reset_after_error(self):
        """Job status should return to pending even after an exception."""
        sched = Scheduler()
        sched.add_job(
            lambda: 1 / 0,
            every(3600, "seconds"),
            id="j1",
        )

        # run_job re-raises exceptions, but status should still reset
        with pytest.raises(ZeroDivisionError):
            sched.run_job("j1")

        job = sched.get_job("j1")
        assert job is not None
        assert job.status == JobStatus.pending


# ── Event System ────────────────────────────────────────────────────────


class TestEventSystem:
    """Tests for listener behavior."""

    def test_listener_exception_does_not_crash_scheduler(self):
        """A failing listener should not prevent job execution."""
        results = []

        def bad_listener(event):
            raise RuntimeError("listener boom")

        sched = Scheduler(tick_interval=0.01)
        sched.add_listener(bad_listener)
        sched.add_job(
            lambda: results.append(1),
            every(0.05, "seconds"),
            id="j1",
        )
        sched.start()
        time.sleep(0.2)
        sched.shutdown()

        # Jobs should still have executed despite the failing listener
        assert len(results) >= 1

    def test_listener_receives_correct_event_types(self):
        """Listeners should receive matching event types for lifecycle."""
        events = []
        sched = Scheduler()
        sched.add_listener(lambda e: events.append(e))

        sched.add_job(lambda: None, every(3600, "seconds"), id="j1")
        sched.remove_job("j1")

        types = [e.event_type for e in events]
        assert EventType.job_added in types
        assert EventType.job_removed in types

    def test_multiple_listeners_all_called(self):
        """All registered listeners should be called for each event."""
        results_a = []
        results_b = []

        sched = Scheduler()
        sched.add_listener(lambda e: results_a.append(e))
        sched.add_listener(lambda e: results_b.append(e))

        sched.add_job(lambda: None, every(3600, "seconds"), id="j1")

        assert len(results_a) == 1
        assert len(results_b) == 1
        assert results_a[0].job_id == "j1"
        assert results_b[0].job_id == "j1"
