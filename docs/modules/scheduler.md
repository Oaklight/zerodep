# Scheduler

Zero-dependency in-process task scheduler with cron expressions, interval scheduling, one-shot tasks, and async support -- stdlib only, Python 3.10+.

## Overview

The Scheduler module provides a lightweight, background-thread task scheduler with 5-field cron expression parsing, fixed-interval triggers, one-shot triggers, per-job callbacks, global event listeners, and sync+async job support -- all without any third-party dependencies.

| File | Description | Dependencies |
|------|-------------|--------------|
| `scheduler.py` | Pure Python implementation | None (stdlib only: `threading`, `asyncio`, `datetime`, `inspect`, `logging`) |

The module supports misfire grace time, job pause/resume, immediate job execution, a decorator API, and context manager usage.

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp scheduler/scheduler.py your_project/
```

Then import directly:

```python
from scheduler import Scheduler, every, cron, once
```

## Usage Examples

### Basic Interval Scheduling

```python
from scheduler import Scheduler, every

sched = Scheduler()
sched.add_job(lambda: print("tick"), every(10, "seconds"), id="ticker")
sched.start()
```

### Cron Expression

```python
from scheduler import Scheduler, cron

sched = Scheduler()
sched.add_job(cleanup, cron("0 3 * * *"))       # daily at 03:00
sched.add_job(report, cron("0 9 * * 1-5"))      # weekdays at 09:00
sched.add_job(backup, cron("30 2 1 * *"))       # 1st of month at 02:30
sched.start()
```

Standard 5-field cron format: `minute hour day-of-month month day-of-week`. Supports `*`, ranges (`1-5`), steps (`*/15`), lists (`1,15`), and named months/days (`jan`, `mon`).

### One-Shot Task

```python
from datetime import datetime, timedelta
from scheduler import Scheduler, once

sched = Scheduler()
run_at = datetime.now() + timedelta(hours=1)
sched.add_job(send_reminder, once(run_at), id="reminder")
sched.start()
```

### Context Manager

```python
import time
from scheduler import Scheduler, every

with Scheduler() as sched:
    sched.add_job(heartbeat, every(1, "seconds"))
    time.sleep(10)  # runs for 10 seconds, then auto-shuts down
```

### Decorator API

```python
from scheduler import Scheduler, every

sched = Scheduler()

@sched.scheduled_job(every(30, "seconds"), id="health")
def health_check():
    print("healthy")

sched.start()
```

### Async Jobs

```python
import asyncio
from scheduler import Scheduler, every

sched = Scheduler()

async def fetch_data():
    await asyncio.sleep(0.1)
    print("fetched")

sched.add_job(fetch_data, every(60, "seconds"))
sched.start()
```

Async functions are automatically detected and executed in a dedicated event loop within the scheduler thread.

### Per-Job Callbacks

```python
from scheduler import Scheduler, every

def on_ok(result):
    print(f"Success: {result}")

def on_fail(exc):
    print(f"Error: {exc}")

sched = Scheduler()
sched.add_job(
    risky_task,
    every(30, "seconds"),
    on_success=on_ok,
    on_error=on_fail,
)
sched.start()
```

### Event Listeners

```python
from scheduler import Scheduler, every, EventType

sched = Scheduler()

def on_event(event):
    if event.event_type == EventType.job_executed:
        print(f"Job {event.job_id} executed at {event.run_time}")
    elif event.event_type == EventType.job_error:
        print(f"Job {event.job_id} failed: {event.exception}")

sched.add_listener(on_event)
sched.add_job(my_task, every(10, "seconds"))
sched.start()
```

### Job Management

```python
from scheduler import Scheduler, every

sched = Scheduler()
sched.add_job(task_a, every(60, "seconds"), id="a")
sched.add_job(task_b, every(120, "seconds"), id="b")

sched.pause_job("a")          # pause job "a"
sched.resume_job("a")         # resume job "a"
sched.run_job("a")            # execute immediately
sched.remove_job("b")         # remove job "b"
print(sched.get_jobs())       # list all jobs
```

### Misfire Grace Time

```python
from scheduler import Scheduler, every

# If a job is late by more than 5 seconds, skip it instead of running
sched = Scheduler()
sched.add_job(
    sensitive_task,
    every(10, "seconds"),
    misfire_grace_time=5.0,
)
sched.start()
```

## API Reference

### `Scheduler(tick_interval=0.1)`

The main scheduler class. Runs a background daemon thread that checks and dispatches due jobs.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `tick_interval` | `float` | `0.1` | How often (seconds) the scheduler checks for due jobs. |

**Methods:**

| Method | Description |
|--------|-------------|
| `add_job(fn, trigger, *, id, name, args, kwargs, misfire_grace_time, on_success, on_error)` | Add a job to the scheduler. Returns `Job`. |
| `remove_job(job_id)` | Remove a job by ID. Raises `JobNotFound` if not found. |
| `get_job(job_id)` | Get a job by ID. Returns `Job` or `None`. |
| `get_jobs()` | Return a list of all jobs. |
| `pause_job(job_id)` | Pause a job (it will not fire until resumed). |
| `resume_job(job_id)` | Resume a paused job. |
| `run_job(job_id)` | Execute a job immediately, regardless of schedule. |
| `start()` | Start the background scheduler thread. |
| `shutdown(wait=True)` | Stop the scheduler. If `wait=True`, block until the thread exits. |
| `add_listener(callback)` | Register a `JobEvent` listener. |
| `remove_listener(callback)` | Unregister a listener. |
| `scheduled_job(trigger, **kwargs)` | Decorator to register a function as a scheduled job. |

---

### Triggers

#### `IntervalTrigger(seconds, start_time=None)`

Fires at a fixed interval.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `seconds` | `float` | -- | Interval in seconds. |
| `start_time` | `datetime \| None` | `None` | Earliest time to start firing. |

#### `CronTrigger(expression)`

Fires according to a 5-field cron expression.

| Name | Type | Description |
|------|------|-------------|
| `expression` | `str` | Standard cron: `minute hour dom month dow`. |

#### `OnceTrigger(run_time)`

Fires once at a specific datetime, then never again.

| Name | Type | Description |
|------|------|-------------|
| `run_time` | `datetime` | When to fire. |

---

### Convenience Functions

| Function | Returns | Description |
|----------|---------|-------------|
| `every(interval, unit)` | `IntervalTrigger` | Create an interval trigger. Units: `"seconds"`, `"minutes"`, `"hours"` (or singular forms). |
| `cron(expression)` | `CronTrigger` | Create a cron trigger from a 5-field expression. |
| `once(dt)` | `OnceTrigger` | Create a one-shot trigger. |

---

### `Job`

Dataclass representing a scheduled job.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique job identifier. |
| `name` | `str` | Human-readable name (defaults to function name). |
| `fn` | `Callable` | The function to execute. |
| `trigger` | `IntervalTrigger \| CronTrigger \| OnceTrigger` | When to fire. |
| `next_run_time` | `datetime \| None` | Next scheduled fire time. |
| `status` | `JobStatus` | Current status: `pending`, `running`, or `paused`. |
| `args` | `tuple` | Positional arguments passed to `fn`. |
| `kwargs` | `dict` | Keyword arguments passed to `fn`. |
| `misfire_grace_time` | `float` | Max seconds late before skipping (default `1.0`). |
| `on_success` | `Callable \| None` | Callback on successful execution. |
| `on_error` | `Callable \| None` | Callback on exception. |

---

### `JobEvent`

Dataclass emitted to event listeners.

| Field | Type | Description |
|-------|------|-------------|
| `event_type` | `EventType` | One of: `job_executed`, `job_error`, `job_missed`, `job_added`, `job_removed`. |
| `job_id` | `str` | The job that triggered this event. |
| `scheduled_time` | `datetime \| None` | When the job was supposed to run. |
| `run_time` | `datetime \| None` | When the job actually ran. |
| `return_value` | `Any` | Return value (for `job_executed`). |
| `exception` | `BaseException \| None` | Exception (for `job_error`). |

---

### Exceptions

| Exception | Description |
|-----------|-------------|
| `SchedulerError` | Base exception for all scheduler errors. |
| `SchedulerAlreadyRunning` | `start()` called on an already-running scheduler. |
| `SchedulerNotRunning` | Operation requires a running scheduler. |
| `JobNotFound` | Job ID not found. Has `job_id` attribute. |
| `InvalidCronExpression` | Malformed cron expression. Has `field` and `detail` attributes. |

---

### `parse_cron(expression)`

Low-level function to parse a 5-field cron expression into a `CronSpec` namedtuple.

| Name | Type | Description |
|------|------|-------------|
| `expression` | `str` | 5-field cron expression. |

**Returns:** `CronSpec(minutes, hours, doms, months, dows, expression)` — each field is a `frozenset[int]`.

## Comparison with APScheduler / schedule / croniter

| Feature | zerodep scheduler | APScheduler | schedule | croniter |
|---------|------------------|-------------|----------|----------|
| Dependencies | None (stdlib only) | pytz, tzlocal, etc. | None | None |
| Cron expressions | Yes (5-field) | Yes (extended) | No | Yes (parsing only) |
| Interval triggers | Yes | Yes | Yes | No |
| One-shot triggers | Yes | Yes | No | No |
| Async jobs | Yes (auto-detected) | Yes | No | N/A |
| Per-job callbacks | Yes | Via listeners | No | N/A |
| Event system | Yes | Yes | No | N/A |
| Job management | pause/resume/run | pause/resume/modify | cancel | N/A |
| Misfire handling | Skip with grace time | Configurable | No | N/A |
| Persistence | No | Yes (multiple stores) | No | N/A |
| Implementation | Single file (~1000 lines) | Package | Package | Package |
| Cron parsing speed | ~20 us | ~74 us | N/A | ~234 us |

**When to use zerodep:** You need a lightweight in-process scheduler with zero dependencies and standard cron/interval/one-shot scheduling.

**When to use APScheduler:** You need job persistence, timezone-aware scheduling, or advanced trigger composition.

## Benchmark

Benchmarked against `APScheduler`, `croniter`, and `schedule` across cron parsing, next fire time calculation, and job management overhead.

See [Scheduler Benchmark](../benchmarks/scheduler.md) for detailed results.
