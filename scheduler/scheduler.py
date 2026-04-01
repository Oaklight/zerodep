# /// zerodep
# version = "0.3.0"
# deps = []
# tier = "subsystem"
# category = "process"
# ///

"""Zero-dependency in-process task scheduler with cron support.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Provides a lightweight, pure-Python task scheduler that runs in a
background daemon thread.  Supports cron expressions, fixed-interval
scheduling, one-shot tasks, per-job callbacks, and async jobs.

Quick start::

    from scheduler import Scheduler, every

    sched = Scheduler()

    @sched.scheduled_job(every(10, "seconds"))
    def heartbeat():
        print("alive")

    sched.start()

Cron usage::

    from scheduler import Scheduler, cron

    sched = Scheduler()
    sched.add_job(cleanup, cron("0 3 * * *"))  # daily at 03:00
    sched.start()

Context-manager usage::

    with Scheduler() as sched:
        sched.add_job(tick, every(1, "seconds"))
        time.sleep(5)

Requires Python 3.10+.
"""

# ── Imports ──

from __future__ import annotations

import asyncio
import dataclasses
import enum
import inspect
import logging
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

__all__ = [
    # Constants
    "DEFAULT_MISFIRE_GRACE_TIME",
    "DEFAULT_TICK_INTERVAL",
    # Exceptions
    "SchedulerError",
    "SchedulerAlreadyRunning",
    "SchedulerNotRunning",
    "JobNotFound",
    "InvalidCronExpression",
    # Cron
    "CronSpec",
    "parse_cron",
    # Triggers
    "IntervalTrigger",
    "CronTrigger",
    "OnceTrigger",
    "every",
    "cron",
    "once",
    # Enums
    "JobStatus",
    "EventType",
    # Data classes
    "JobEvent",
    "Job",
    # Scheduler
    "Scheduler",
]

logger = logging.getLogger(__name__)

# ── Constants ──

DEFAULT_MISFIRE_GRACE_TIME = 1.0  # seconds
DEFAULT_TICK_INTERVAL = 0.1  # seconds — scheduler loop resolution


# ── Exceptions ──
# ── Error Convention ──────────────────────────────────────────────────
# All zerodep subsystem modules follow these error message rules:
# 1. Domain exceptions wrap stdlib exceptions (never expose raw OSError, etc.)
# 2. Error messages include minimal necessary context:
#    - Command execution: command, returncode, stderr
#    - Network: URL, host, timeout, status code
#    - Scheduling: job id, trigger type, scheduled time
#    - Configuration: key, source, expected type
# 3. Exception names reflect domain semantics, not implementation
# 4. Built-in name shadowing (if any) is documented with intent
# ─────────────────────────────────────────────────────────────────────


class SchedulerError(Exception):
    """Base exception for scheduler errors."""


class SchedulerAlreadyRunning(SchedulerError):
    """Raised when start() is called on an already-running scheduler."""


class SchedulerNotRunning(SchedulerError):
    """Raised when an operation requires a running scheduler."""


class JobNotFound(SchedulerError):
    """Raised when a job ID is not found."""

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Job not found: {job_id!r}")


class InvalidCronExpression(SchedulerError):
    """Raised when a cron expression cannot be parsed."""

    def __init__(self, expr: str, reason: str = "") -> None:
        self.expr = expr
        msg = f"Invalid cron expression: {expr!r}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)


# ── Cron Expression Parser ──

# Field ranges: minute(0-59), hour(0-23), day-of-month(1-31),
#               month(1-12), day-of-week(0-6, 0=Sunday)

_CRON_FIELD_RANGES: list[tuple[int, int]] = [
    (0, 59),  # minute
    (0, 23),  # hour
    (1, 31),  # day of month
    (1, 12),  # month
    (0, 6),  # day of week (0=Sun, 6=Sat)
]

_MONTH_NAMES = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

_DOW_NAMES = {
    "sun": 0,
    "mon": 1,
    "tue": 2,
    "wed": 3,
    "thu": 4,
    "fri": 5,
    "sat": 6,
}


def _parse_cron_field(field: str, lo: int, hi: int) -> frozenset[int]:
    """Parse a single cron field into a set of allowed values.

    Supports: ``*``, ranges (``1-5``), steps (``*/2``, ``1-5/2``),
    lists (``1,3,5``), and named values for month/dow fields.

    Args:
        field: The field string to parse.
        lo: Minimum allowed value.
        hi: Maximum allowed value.

    Returns:
        Frozenset of matching integer values.

    Raises:
        InvalidCronExpression: On invalid syntax or out-of-range values.
    """
    result: set[int] = set()

    for part in field.split(","):
        part = part.strip()
        if not part:
            raise InvalidCronExpression(field, "empty part in list")

        # Handle step
        step = 1
        if "/" in part:
            base, step_str = part.split("/", 1)
            try:
                step = int(step_str)
            except ValueError:
                raise InvalidCronExpression(field, f"invalid step: {step_str!r}")
            if step < 1:
                raise InvalidCronExpression(field, f"step must be >= 1, got {step}")
            part = base

        # Resolve named values
        part_lower = part.lower()
        if part_lower in _MONTH_NAMES:
            val = _MONTH_NAMES[part_lower]
            if lo <= val <= hi:
                result.add(val)
                continue
        if part_lower in _DOW_NAMES:
            val = _DOW_NAMES[part_lower]
            if lo <= val <= hi:
                result.add(val)
                continue

        if part == "*":
            result.update(range(lo, hi + 1, step))
        elif "-" in part:
            range_parts = part.split("-", 1)
            try:
                rlo_str, rhi_str = range_parts
                # Resolve names in ranges
                rlo = (
                    _MONTH_NAMES.get(rlo_str.lower())
                    or _DOW_NAMES.get(rlo_str.lower())
                    or int(rlo_str)
                )
                rhi = (
                    _MONTH_NAMES.get(rhi_str.lower())
                    or _DOW_NAMES.get(rhi_str.lower())
                    or int(rhi_str)
                )
            except ValueError:
                raise InvalidCronExpression(field, f"invalid range: {part!r}")
            if rlo < lo or rhi > hi or rlo > rhi:
                raise InvalidCronExpression(
                    field, f"range {rlo}-{rhi} out of bounds [{lo}-{hi}]"
                )
            result.update(range(rlo, rhi + 1, step))
        else:
            try:
                val = int(part)
            except ValueError:
                raise InvalidCronExpression(field, f"invalid value: {part!r}")
            if val < lo or val > hi:
                raise InvalidCronExpression(
                    field, f"value {val} out of bounds [{lo}-{hi}]"
                )
            result.add(val)

    return frozenset(result)


@dataclasses.dataclass(frozen=True, slots=True)
class CronSpec:
    """Parsed 5-field cron specification.

    Attributes:
        minutes: Allowed minute values (0-59).
        hours: Allowed hour values (0-23).
        days: Allowed day-of-month values (1-31).
        months: Allowed month values (1-12).
        weekdays: Allowed day-of-week values (0-6, 0=Sunday).
        expression: The original expression string.
    """

    minutes: frozenset[int]
    hours: frozenset[int]
    days: frozenset[int]
    months: frozenset[int]
    weekdays: frozenset[int]
    expression: str = ""

    def __repr__(self) -> str:
        return f"CronSpec({self.expression!r})"


def parse_cron(expr: str) -> CronSpec:
    """Parse a 5-field cron expression.

    Supports standard cron syntax::

        ┌───────────── minute (0-59)
        │ ┌───────────── hour (0-23)
        │ │ ┌───────────── day of month (1-31)
        │ │ │ ┌───────────── month (1-12 or jan-dec)
        │ │ │ │ ┌───────────── day of week (0-6, Sun=0, or sun-sat)
        │ │ │ │ │
        * * * * *

    Args:
        expr: Cron expression string (5 space-separated fields).

    Returns:
        A ``CronSpec`` with parsed field sets.

    Raises:
        InvalidCronExpression: On invalid syntax.
    """
    fields = expr.strip().split()
    if len(fields) != 5:
        raise InvalidCronExpression(expr, f"expected 5 fields, got {len(fields)}")

    parsed = []
    for field, (lo, hi) in zip(fields, _CRON_FIELD_RANGES):
        parsed.append(_parse_cron_field(field, lo, hi))

    return CronSpec(
        minutes=parsed[0],
        hours=parsed[1],
        days=parsed[2],
        months=parsed[3],
        weekdays=parsed[4],
        expression=expr,
    )


def _cron_next_fire_time(spec: CronSpec, after: datetime) -> datetime:
    """Compute the next fire time for a cron spec after the given time.

    Uses a forward-scanning algorithm: increment minute, then roll over
    to higher fields as needed.  Guarantees termination within 4 years.

    Args:
        spec: Parsed cron specification.
        after: Start time (exclusive — the result will be strictly after this).

    Returns:
        The next datetime matching the cron spec.

    Raises:
        SchedulerError: If no match is found within 4 years (should not happen
            with valid cron specs).
    """
    # Start from the next minute
    dt = after.replace(second=0, microsecond=0) + timedelta(minutes=1)

    # Safety limit: 4 years of minutes (~2.1M iterations max,
    # but the loop advances by large jumps so it's much faster)
    max_dt = after + timedelta(days=366 * 4)

    while dt < max_dt:
        if dt.month not in spec.months:
            # Advance to next valid month
            dt = _advance_month(dt, spec.months)
            continue

        # Day-of-month AND day-of-week check
        # Standard cron: if both dom and dow are restricted (not *),
        # the match is OR (either matches). If only one is restricted,
        # that one must match.
        dom_restricted = spec.days != frozenset(range(1, 32))
        dow_restricted = spec.weekdays != frozenset(range(0, 7))

        dom_match = dt.day in spec.days
        # Python: Monday=0, Sunday=6.  Cron: Sunday=0, Saturday=6.
        py_dow = dt.weekday()  # Mon=0 .. Sun=6
        cron_dow = (py_dow + 1) % 7  # Sun=0 .. Sat=6
        dow_match = cron_dow in spec.weekdays

        if dom_restricted and dow_restricted:
            day_ok = dom_match or dow_match
        elif dom_restricted:
            day_ok = dom_match
        elif dow_restricted:
            day_ok = dow_match
        else:
            day_ok = True

        if not day_ok:
            dt = dt.replace(hour=0, minute=0) + timedelta(days=1)
            continue

        if dt.hour not in spec.hours:
            # Advance to next valid hour
            dt = _advance_hour(dt, spec.hours)
            continue

        if dt.minute not in spec.minutes:
            dt = _advance_minute(dt, spec.minutes)
            continue

        return dt

    raise SchedulerError(f"Could not find next fire time for {spec!r} after {after}")


def _advance_month(dt: datetime, months: frozenset[int]) -> datetime:
    """Advance to the first day of the next valid month."""
    year = dt.year
    month = dt.month
    for _ in range(48):  # max 4 years of months
        month += 1
        if month > 12:
            month = 1
            year += 1
        if month in months:
            return dt.replace(year=year, month=month, day=1, hour=0, minute=0)
    return dt + timedelta(days=366 * 4)  # unreachable with valid spec


def _advance_hour(dt: datetime, hours: frozenset[int]) -> datetime:
    """Advance to the next valid hour on the same or next day."""
    for h in sorted(hours):
        if h > dt.hour:
            return dt.replace(hour=h, minute=0)
    # Roll to next day, hour 0
    return (dt + timedelta(days=1)).replace(hour=0, minute=0)


def _advance_minute(dt: datetime, minutes: frozenset[int]) -> datetime:
    """Advance to the next valid minute in the same or next hour."""
    for m in sorted(minutes):
        if m > dt.minute:
            return dt.replace(minute=m)
    # Roll to next hour
    return dt.replace(minute=0) + timedelta(hours=1)


# ── Trigger Implementations ──


class _BaseTrigger:
    """Abstract base for all triggers."""

    def next_fire_time(self, now: datetime) -> datetime | None:
        """Compute the next fire time after *now*.

        Returns:
            The next datetime to fire, or ``None`` if the trigger
            will never fire again.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class IntervalTrigger(_BaseTrigger):
    """Fire at fixed time intervals.

    Args:
        seconds: Interval in seconds.
        start_time: When to start (default: now).

    Example::

        IntervalTrigger(seconds=60)  # every minute
    """

    __slots__ = ("_seconds", "_start_time")

    def __init__(self, seconds: float, *, start_time: datetime | None = None) -> None:
        if seconds <= 0:
            raise ValueError("Interval must be positive")
        self._seconds = seconds
        self._start_time = start_time

    @property
    def seconds(self) -> float:
        return self._seconds

    def next_fire_time(self, now: datetime) -> datetime:
        if self._start_time is None:
            self._start_time = now
        if now < self._start_time:
            return self._start_time
        elapsed = (now - self._start_time).total_seconds()
        periods = int(elapsed / self._seconds) + 1
        return self._start_time + timedelta(seconds=periods * self._seconds)

    def __repr__(self) -> str:
        return f"IntervalTrigger(seconds={self._seconds})"


class CronTrigger(_BaseTrigger):
    """Fire on a cron schedule.

    Args:
        expression: Standard 5-field cron expression.
        tz: Timezone for evaluation (default: local time via
            ``datetime.now()``).

    Example::

        CronTrigger("30 9 * * 1-5")  # 9:30 AM weekdays
    """

    __slots__ = ("_spec", "_tz")

    def __init__(self, expression: str, *, tz: timezone | None = None) -> None:
        self._spec = parse_cron(expression)
        self._tz = tz

    @property
    def spec(self) -> CronSpec:
        return self._spec

    def next_fire_time(self, now: datetime) -> datetime:
        if self._tz is not None:
            now = now.astimezone(self._tz)
        return _cron_next_fire_time(self._spec, now)

    def __repr__(self) -> str:
        return f"CronTrigger({self._spec.expression!r})"


class OnceTrigger(_BaseTrigger):
    """Fire exactly once at a given time.

    Args:
        run_time: When to fire.

    Example::

        OnceTrigger(datetime(2026, 4, 1, 9, 0))
    """

    __slots__ = ("_run_time", "_fired")

    def __init__(self, run_time: datetime) -> None:
        self._run_time = run_time
        self._fired = False

    @property
    def run_time(self) -> datetime:
        return self._run_time

    def next_fire_time(self, now: datetime) -> datetime | None:
        if self._fired or now >= self._run_time:
            return None
        return self._run_time

    def mark_fired(self) -> None:
        self._fired = True

    def __repr__(self) -> str:
        return f"OnceTrigger({self._run_time!r})"


# ── Convenience Trigger Constructors ──


def every(interval: float, unit: str = "seconds") -> IntervalTrigger:
    """Create an interval trigger with human-friendly units.

    Args:
        interval: Numeric interval value.
        unit: One of ``"seconds"``, ``"minutes"``, ``"hours"``.

    Returns:
        An ``IntervalTrigger``.

    Example::

        every(30, "seconds")
        every(5, "minutes")
        every(1, "hours")
    """
    multipliers = {"seconds": 1, "minutes": 60, "hours": 3600}
    # Also accept singular forms
    multipliers.update({"second": 1, "minute": 60, "hour": 3600})
    unit_lower = unit.lower()
    if unit_lower not in multipliers:
        raise ValueError(
            f"Unknown unit: {unit!r}. Expected one of: {', '.join(sorted(multipliers))}"
        )
    return IntervalTrigger(interval * multipliers[unit_lower])


def cron(expression: str, **kwargs: Any) -> CronTrigger:
    """Create a cron trigger from an expression string.

    Shorthand for ``CronTrigger(expression, **kwargs)``.

    Args:
        expression: 5-field cron expression.
        **kwargs: Passed to ``CronTrigger``.

    Returns:
        A ``CronTrigger``.
    """
    return CronTrigger(expression, **kwargs)


def once(run_time: datetime) -> OnceTrigger:
    """Create a one-shot trigger.

    Shorthand for ``OnceTrigger(run_time)``.

    Args:
        run_time: When to fire.

    Returns:
        An ``OnceTrigger``.
    """
    return OnceTrigger(run_time)


# ── Data Models (Job, JobEvent, JobStatus, EventType) ──


class JobStatus(enum.Enum):
    """Status of a scheduled job."""

    pending = "pending"
    running = "running"
    paused = "paused"


class EventType(enum.Enum):
    """Types of scheduler events."""

    job_executed = "job_executed"
    job_error = "job_error"
    job_missed = "job_missed"
    job_added = "job_added"
    job_removed = "job_removed"


@dataclasses.dataclass
class JobEvent:
    """Event emitted by the scheduler.

    Attributes:
        event_type: What happened.
        job_id: The job that triggered the event.
        scheduled_time: When the job was supposed to run.
        run_time: When the job actually ran (if applicable).
        return_value: Return value of the job function (on success).
        exception: Exception raised (on error).
    """

    event_type: EventType
    job_id: str
    scheduled_time: datetime | None = None
    run_time: datetime | None = None
    return_value: Any = None
    exception: BaseException | None = None


@dataclasses.dataclass
class Job:
    """A scheduled job.

    Attributes:
        id: Unique job identifier.
        name: Human-readable name.
        fn: The callable to invoke.
        trigger: When to invoke the callable.
        args: Positional arguments for *fn*.
        kwargs: Keyword arguments for *fn*.
        next_run_time: Next scheduled execution time.
        status: Current job status.
        misfire_grace_time: Seconds after ``next_run_time`` within which
            a late execution is still accepted.
        on_success: Callback invoked with the return value on success.
        on_error: Callback invoked with the exception on failure.
    """

    id: str
    name: str
    fn: Callable[..., Any]
    trigger: _BaseTrigger
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = dataclasses.field(default_factory=dict)
    next_run_time: datetime | None = None
    status: JobStatus = JobStatus.pending
    misfire_grace_time: float = DEFAULT_MISFIRE_GRACE_TIME
    on_success: Callable[[Any], None] | None = None
    on_error: Callable[[BaseException], None] | None = None

    def __repr__(self) -> str:
        return (
            f"<Job id={self.id!r} name={self.name!r} "
            f"trigger={self.trigger!r} status={self.status.value!r}>"
        )


# ── Scheduler Core ──


class Scheduler:
    """In-process task scheduler with background thread execution.

    Jobs are checked and dispatched by a daemon thread that wakes
    at ``tick_interval`` resolution.  Supports sync and async callables.

    Concurrency Model:
        The scheduler runs a single background daemon thread that
        periodically checks for due jobs via ``_run_loop``.

        - **Sync jobs**: executed directly in the scheduler thread.
          This means long-running sync jobs block the scheduler tick.
        - **Async jobs**: executed via a temporary ``asyncio`` event loop
          created per invocation (``asyncio.new_event_loop()``), then
          closed in a ``finally`` block.  The scheduler thread blocks
          until the coroutine completes.

        Threading guarantees:
        - ``self._jobs`` dict access is protected by ``self._lock``.
        - ``_get_due_jobs()`` snapshots due jobs under the lock.
        - Job execution (``_execute_job``) runs **outside** the lock.
        - Job status transitions (``pending → running → pending``)
          are performed under the lock.  ``_execute_job`` atomically
          checks and sets ``status = running``, preventing concurrent
          double-execution of the same job.
        - ``_reschedule`` mutates ``next_run_time`` under the lock.
        - ``_process_job`` reads ``next_run_time`` under the lock.
        - Listener dispatch (``_emit``) runs outside the lock, so
          listeners may observe intermediate job states.

        Shutdown semantics:
        - ``self._running`` set to ``False``; ``self._event`` signaled.
        - Background thread finishes its current tick iteration
          (including any in-flight job) before exiting the loop.
        - ``_thread.join()`` blocks the caller until the thread exits
          (unless ``wait=False``).
        - There is no pre-emption: a running sync job will complete;
          a running async job's event loop will run to completion.
        - Listeners receive events for jobs that complete during the
          final tick, but no synthetic "shutdown" event is emitted.

    Args:
        tick_interval: How often (seconds) the scheduler checks for
            due jobs.  Lower values give better timing accuracy at the
            cost of CPU.
        daemon: If ``True`` (default), the background thread is a daemon
            and will not prevent process exit.

    Example::

        sched = Scheduler()
        sched.add_job(my_func, every(10, "seconds"))
        sched.start()
        # ... later ...
        sched.shutdown()
    """

    def __init__(
        self,
        *,
        tick_interval: float = DEFAULT_TICK_INTERVAL,
        daemon: bool = True,
    ) -> None:
        self._tick_interval = tick_interval
        self._daemon = daemon
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._event = threading.Event()  # for shutdown signaling
        self._thread: threading.Thread | None = None
        self._running = False
        self._listeners: list[Callable[[JobEvent], None]] = []

    # ── Context manager ──

    def __enter__(self) -> Scheduler:
        self.start()
        return self

    def __exit__(self, *args: Any) -> None:
        self.shutdown()

    # ── Job management ──

    def add_job(
        self,
        fn: Callable[..., Any],
        trigger: _BaseTrigger,
        *,
        id: str | None = None,
        name: str | None = None,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
        misfire_grace_time: float = DEFAULT_MISFIRE_GRACE_TIME,
        on_success: Callable[[Any], None] | None = None,
        on_error: Callable[[BaseException], None] | None = None,
    ) -> Job:
        """Add a job to the scheduler.

        Args:
            fn: Callable to invoke.
            trigger: Trigger that determines when the job fires.
            id: Unique ID (auto-generated if omitted).
            name: Human-readable name (defaults to ``fn.__name__``).
            args: Positional arguments for *fn*.
            kwargs: Keyword arguments for *fn*.
            misfire_grace_time: Seconds of late execution tolerance.
            on_success: Called with the return value on success.
            on_error: Called with the exception on failure.

        Returns:
            The created ``Job``.
        """
        job_id = id or str(uuid.uuid4())[:8]
        job_name = name or getattr(fn, "__name__", repr(fn))
        now = datetime.now()

        job = Job(
            id=job_id,
            name=job_name,
            fn=fn,
            trigger=trigger,
            args=args,
            kwargs=kwargs if kwargs is not None else {},
            next_run_time=trigger.next_fire_time(now),
            misfire_grace_time=misfire_grace_time,
            on_success=on_success,
            on_error=on_error,
        )

        with self._lock:
            self._jobs[job_id] = job

        self._emit(JobEvent(EventType.job_added, job_id))
        return job

    def scheduled_job(
        self,
        trigger: _BaseTrigger,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to register a function as a scheduled job.

        Args:
            trigger: Trigger for the job.
            **kwargs: Passed to ``add_job``.

        Returns:
            Decorator that registers the function and returns it unchanged.

        Example::

            @sched.scheduled_job(every(60, "seconds"))
            def periodic_task():
                ...
        """

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.add_job(fn, trigger, **kwargs)
            return fn

        return decorator

    def remove_job(self, job_id: str) -> None:
        """Remove a job by ID.

        Args:
            job_id: The job to remove.

        Raises:
            JobNotFound: If *job_id* doesn't exist.
        """
        with self._lock:
            if job_id not in self._jobs:
                raise JobNotFound(job_id)
            del self._jobs[job_id]
        self._emit(JobEvent(EventType.job_removed, job_id))

    def get_job(self, job_id: str) -> Job | None:
        """Get a job by ID, or ``None`` if not found."""
        with self._lock:
            return self._jobs.get(job_id)

    def get_jobs(self) -> list[Job]:
        """Return a list of all jobs."""
        with self._lock:
            return list(self._jobs.values())

    def pause_job(self, job_id: str) -> None:
        """Pause a job so it won't fire until resumed.

        Args:
            job_id: The job to pause.

        Raises:
            JobNotFound: If *job_id* doesn't exist.
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise JobNotFound(job_id)
            job.status = JobStatus.paused

    def resume_job(self, job_id: str) -> None:
        """Resume a paused job.

        Args:
            job_id: The job to resume.

        Raises:
            JobNotFound: If *job_id* doesn't exist.
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise JobNotFound(job_id)
            job.status = JobStatus.pending
            job.next_run_time = job.trigger.next_fire_time(datetime.now())

    def run_job(self, job_id: str) -> Any:
        """Execute a job immediately, bypassing its trigger.

        This does **not** update ``next_run_time`` — the trigger's
        schedule continues independently.

        Double-execution is prevented by the status guard in
        ``_execute_job``, which atomically checks and sets
        ``job.status = running`` under the lock.

        Args:
            job_id: The job to run.

        Returns:
            The return value of the job function, or ``None`` if the
            job is already running.

        Raises:
            JobNotFound: If *job_id* doesn't exist.
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise JobNotFound(job_id)

        return self._execute_job(job, datetime.now())

    # ── Event system (listeners, emission) ──

    def add_listener(self, callback: Callable[[JobEvent], None]) -> None:
        """Register a global event listener.

        Args:
            callback: Called with a ``JobEvent`` whenever an event occurs.
        """
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[JobEvent], None]) -> None:
        """Unregister a global event listener."""
        self._listeners.remove(callback)

    def _emit(self, event: JobEvent) -> None:
        """Dispatch an event to all listeners.

        Runs outside the lock, so listeners may observe intermediate
        job states (e.g., ``status=running``).
        """
        # Note: self._listeners is a plain list; add_listener/
        # remove_listener mutate it without locking.  This is safe
        # under CPython's GIL (list.append is atomic), but not
        # guaranteed by the language spec.
        for listener in self._listeners:
            # Tier 2: best-effort observable — listener errors logged
            try:
                listener(event)
            except Exception:
                logger.exception("Error in event listener")

    # ── Lifecycle (start, main loop, shutdown) ──

    @property
    def running(self) -> bool:
        """Whether the scheduler is currently running."""
        return self._running

    def start(self) -> None:
        """Start the background scheduler thread.

        Raises:
            SchedulerAlreadyRunning: If already started.
        """
        if self._running:
            raise SchedulerAlreadyRunning("Scheduler is already running")
        self._running = True
        self._event.clear()
        self._thread = threading.Thread(
            target=self._run_loop, name="zerodep-scheduler", daemon=self._daemon
        )
        self._thread.start()

    def shutdown(self, wait: bool = True) -> None:
        """Stop the scheduler.

        Args:
            wait: If ``True``, block until the background thread exits.

        Shutdown behavior:
        - Currently running jobs: the scheduler thread finishes the
          current ``_process_job`` call (including ``_execute_job``)
          before checking ``self._running`` again.  There is no
          pre-emption — sync jobs run to completion, and async jobs'
          event loops run to completion.
        - Listener events: listeners receive ``job_executed`` /
          ``job_error`` events for any job that completes during the
          final tick.  No synthetic "scheduler_stopped" event is emitted.
        - Async job cleanup: the per-invocation event loop is always
          closed in ``_run_async_job``'s ``finally`` block, regardless
          of shutdown timing.
        """
        # Signal the run loop to stop after its current iteration
        self._running = False
        # Wake the thread from Event.wait() so it exits promptly
        self._event.set()
        if wait and self._thread is not None and self._thread.is_alive():
            self._thread.join()
        self._thread = None

    def _run_loop(self) -> None:
        """Background thread main loop.

        Note: ``self._running`` is read without a lock.  This is safe
        because it is a simple boolean flag written by the main thread
        (in ``shutdown``) and read here — worst case is one extra tick.
        """
        while self._running:
            now = datetime.now()
            due_jobs = self._get_due_jobs(now)
            for job in due_jobs:
                self._process_job(job, now)
            self._event.wait(timeout=self._tick_interval)

    def _get_due_jobs(self, now: datetime) -> list[Job]:
        """Return jobs whose next_run_time <= now and are not paused."""
        with self._lock:
            return [
                job
                for job in self._jobs.values()
                if (
                    job.status == JobStatus.pending
                    and job.next_run_time is not None
                    and job.next_run_time <= now
                )
            ]

    def _process_job(self, job: Job, now: datetime) -> None:
        """Check misfire and execute or skip a due job.

        Note: *job* was snapshotted from ``_get_due_jobs`` under lock,
        but is processed here without the lock held.  This is intentional
        to avoid holding the lock during potentially long job execution.
        """
        with self._lock:
            scheduled = job.next_run_time
        if scheduled is None:
            return

        late = (now - scheduled).total_seconds()
        if late > job.misfire_grace_time:
            # Missed — skip and reschedule
            self._emit(JobEvent(EventType.job_missed, job.id, scheduled_time=scheduled))
            logger.debug(
                "Job %r missed (late by %.1fs > grace %.1fs)",
                job.id,
                late,
                job.misfire_grace_time,
            )
        else:
            try:
                self._execute_job(job, now)
            except Exception:
                pass  # already handled via on_error / event emission

        # Reschedule
        self._reschedule(job, now)

    def _execute_job(self, job: Job, now: datetime) -> Any:
        """Run a job function, handling sync and async callables.

        Acquires the lock to atomically check and set job status to
        ``running``.  If the job is already running (concurrent
        ``run_job`` or scheduler execution), the call is skipped.
        The lock is released before job execution and re-acquired
        briefly to reset the status in the ``finally`` block.
        """
        with self._lock:
            if job.status == JobStatus.running:
                logger.debug("Job %r already running, skipping", job.id)
                return None
            job.status = JobStatus.running
            scheduled = job.next_run_time

        try:
            if inspect.iscoroutinefunction(job.fn):
                result = self._run_async_job(job)
            else:
                result = job.fn(*job.args, **job.kwargs)

            self._emit(
                JobEvent(
                    EventType.job_executed,
                    job.id,
                    scheduled_time=scheduled,
                    run_time=now,
                    return_value=result,
                )
            )
            if job.on_success is not None:
                # Tier 2: best-effort observable — callback error logged
                try:
                    job.on_success(result)
                except Exception:
                    logger.exception("Error in on_success callback for job %r", job.id)

            return result

        except Exception as exc:
            self._emit(
                JobEvent(
                    EventType.job_error,
                    job.id,
                    scheduled_time=scheduled,
                    run_time=now,
                    exception=exc,
                )
            )
            if job.on_error is not None:
                # Tier 2: best-effort observable — callback error logged
                try:
                    job.on_error(exc)
                except Exception:
                    logger.exception("Error in on_error callback for job %r", job.id)
            raise

        finally:
            # Tier 1: must-succeed — job status must reset
            with self._lock:
                if job.status == JobStatus.running:
                    job.status = JobStatus.pending

    def _run_async_job(self, job: Job) -> Any:
        """Execute an async job function in a new event loop.

        A fresh event loop is created per invocation so that the
        scheduler thread (which has no running loop) can drive async
        jobs.  The loop is always closed in the ``finally`` block,
        ensuring no resource leak even on exception.
        """
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(job.fn(*job.args, **job.kwargs))
        finally:
            # Tier 1: must-succeed — event loop must close
            loop.close()

    def _reschedule(self, job: Job, now: datetime) -> None:
        """Update a job's next_run_time from its trigger.

        Called from the scheduler thread after job execution.
        Trigger computation runs outside the lock; only the state
        mutation is protected.
        """
        if isinstance(job.trigger, OnceTrigger):
            with self._lock:
                job.trigger.mark_fired()
                job.next_run_time = None
            return

        nxt = job.trigger.next_fire_time(now)
        with self._lock:
            job.next_run_time = nxt

    # ── Wakeup on job add ──

    def wakeup(self) -> None:
        """Signal the scheduler thread to check for due jobs immediately."""
        self._event.set()
