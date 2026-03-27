# 任务调度器

零依赖的进程内任务调度器，支持 cron 表达式、间隔调度、一次性任务和异步执行。仅依赖标准库，要求 Python 3.10+。

## 概述

`scheduler.py` 是一个单文件任务调度模块，提供后台线程式调度器，支持 5 字段 cron 表达式解析、固定间隔触发器、一次性触发器、per-job 回调、全局事件监听以及同步/异步任务——**无需任何 pip 依赖**。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `scheduler.py` | 纯 Python 实现 | 无（仅标准库：`threading`、`asyncio`、`datetime`、`inspect`、`logging`） |

## 功能特性

- **Cron 表达式** -- 标准 5 字段格式，支持 `*`、范围、步长、列表、命名月份/星期
- **间隔调度** -- 按固定秒/分/时间隔执行
- **一次性任务** -- 在指定时间执行一次
- **同步 + 异步** -- 自动检测协程函数，在专用事件循环中执行
- **Per-job 回调** -- `on_success` / `on_error` 回调
- **事件监听** -- 全局事件系统，监听任务执行、错误、错过等事件
- **任务管理** -- 暂停 / 恢复 / 立即执行 / 删除
- **错过处理** -- 可配置 `misfire_grace_time`，超时跳过
- **上下文管理器** -- `with Scheduler() as sched:` 自动启动和关闭

## 快速开始

### 间隔调度

```python
from scheduler import Scheduler, every

sched = Scheduler()
sched.add_job(lambda: print("tick"), every(10, "seconds"), id="ticker")
sched.start()
```

### Cron 表达式

```python
from scheduler import Scheduler, cron

sched = Scheduler()
sched.add_job(cleanup, cron("0 3 * * *"))       # 每天 03:00
sched.add_job(report, cron("0 9 * * 1-5"))      # 工作日 09:00
sched.add_job(backup, cron("30 2 1 * *"))       # 每月 1 号 02:30
sched.start()
```

标准 5 字段 cron 格式：`分 时 日 月 星期`。支持 `*`、范围（`1-5`）、步长（`*/15`）、列表（`1,15`）、命名值（`jan`、`mon`）。

### 一次性任务

```python
from datetime import datetime, timedelta
from scheduler import Scheduler, once

sched = Scheduler()
run_at = datetime.now() + timedelta(hours=1)
sched.add_job(send_reminder, once(run_at), id="reminder")
sched.start()
```

### 上下文管理器

```python
import time
from scheduler import Scheduler, every

with Scheduler() as sched:
    sched.add_job(heartbeat, every(1, "seconds"))
    time.sleep(10)  # 运行 10 秒后自动关闭
```

### 装饰器用法

```python
from scheduler import Scheduler, every

sched = Scheduler()

@sched.scheduled_job(every(30, "seconds"), id="health")
def health_check():
    print("healthy")

sched.start()
```

### 异步任务

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

异步函数会被自动检测，并在调度器线程的专用事件循环中执行。

### Per-Job 回调

```python
from scheduler import Scheduler, every

def on_ok(result):
    print(f"成功：{result}")

def on_fail(exc):
    print(f"错误：{exc}")

sched = Scheduler()
sched.add_job(
    risky_task,
    every(30, "seconds"),
    on_success=on_ok,
    on_error=on_fail,
)
sched.start()
```

### 事件监听

```python
from scheduler import Scheduler, every, EventType

sched = Scheduler()

def on_event(event):
    if event.event_type == EventType.job_executed:
        print(f"任务 {event.job_id} 在 {event.run_time} 执行")
    elif event.event_type == EventType.job_error:
        print(f"任务 {event.job_id} 失败：{event.exception}")

sched.add_listener(on_event)
sched.add_job(my_task, every(10, "seconds"))
sched.start()
```

### 任务管理

```python
from scheduler import Scheduler, every

sched = Scheduler()
sched.add_job(task_a, every(60, "seconds"), id="a")
sched.add_job(task_b, every(120, "seconds"), id="b")

sched.pause_job("a")          # 暂停任务 "a"
sched.resume_job("a")         # 恢复任务 "a"
sched.run_job("a")            # 立即执行
sched.remove_job("b")         # 删除任务 "b"
print(sched.get_jobs())       # 列出所有任务
```

### 错过处理

```python
from scheduler import Scheduler, every

# 如果任务延迟超过 5 秒，跳过而不执行
sched = Scheduler()
sched.add_job(
    sensitive_task,
    every(10, "seconds"),
    misfire_grace_time=5.0,
)
sched.start()
```

## API 参考

### `Scheduler(tick_interval=0.1)`

主调度器类。运行后台守护线程，定期检查并分发到期任务。

**参数：**

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `tick_interval` | `float` | `0.1` | 调度器检查到期任务的间隔（秒） |

**方法：**

| 方法 | 说明 |
|------|------|
| `add_job(fn, trigger, *, id, name, args, kwargs, misfire_grace_time, on_success, on_error)` | 添加任务，返回 `Job` |
| `remove_job(job_id)` | 按 ID 删除任务，未找到时抛出 `JobNotFound` |
| `get_job(job_id)` | 按 ID 获取任务，返回 `Job` 或 `None` |
| `get_jobs()` | 返回所有任务列表 |
| `pause_job(job_id)` | 暂停任务 |
| `resume_job(job_id)` | 恢复已暂停的任务 |
| `run_job(job_id)` | 立即执行任务，不受调度时间限制 |
| `start()` | 启动后台调度线程 |
| `shutdown(wait=True)` | 停止调度器。`wait=True` 时阻塞直到线程退出 |
| `add_listener(callback)` | 注册 `JobEvent` 事件监听器 |
| `remove_listener(callback)` | 移除事件监听器 |
| `scheduled_job(trigger, **kwargs)` | 装饰器，将函数注册为调度任务 |

---

### 触发器

#### `IntervalTrigger(seconds, start_time=None)`

按固定间隔触发。

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `seconds` | `float` | -- | 间隔秒数 |
| `start_time` | `datetime \| None` | `None` | 最早开始触发的时间 |

#### `CronTrigger(expression)`

按 5 字段 cron 表达式触发。

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `expression` | `str` | 标准 cron 表达式：`分 时 日 月 星期` |

#### `OnceTrigger(run_time)`

在指定时间触发一次，之后不再触发。

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `run_time` | `datetime` | 触发时间 |

---

### 便捷函数

| 函数 | 返回值 | 说明 |
|------|--------|------|
| `every(interval, unit)` | `IntervalTrigger` | 创建间隔触发器。单位：`"seconds"`、`"minutes"`、`"hours"`（支持单数形式） |
| `cron(expression)` | `CronTrigger` | 从 5 字段 cron 表达式创建触发器 |
| `once(dt)` | `OnceTrigger` | 创建一次性触发器 |

---

### `Job`

表示一个调度任务的数据类。

| 属性 | 类型 | 说明 |
|------|------|------|
| `id` | `str` | 唯一任务标识符 |
| `name` | `str` | 可读名称（默认为函数名） |
| `fn` | `Callable` | 要执行的函数 |
| `trigger` | `IntervalTrigger \| CronTrigger \| OnceTrigger` | 触发器 |
| `next_run_time` | `datetime \| None` | 下次调度时间 |
| `status` | `JobStatus` | 当前状态：`pending`、`running` 或 `paused` |
| `args` | `tuple` | 传给 `fn` 的位置参数 |
| `kwargs` | `dict` | 传给 `fn` 的关键字参数 |
| `misfire_grace_time` | `float` | 最大允许延迟（秒），超时则跳过（默认 `1.0`） |
| `on_success` | `Callable \| None` | 成功回调 |
| `on_error` | `Callable \| None` | 异常回调 |

---

### `JobEvent`

发送给事件监听器的数据类。

| 属性 | 类型 | 说明 |
|------|------|------|
| `event_type` | `EventType` | 事件类型：`job_executed`、`job_error`、`job_missed`、`job_added`、`job_removed` |
| `job_id` | `str` | 触发事件的任务 ID |
| `scheduled_time` | `datetime \| None` | 预定执行时间 |
| `run_time` | `datetime \| None` | 实际执行时间 |
| `return_value` | `Any` | 返回值（`job_executed` 事件） |
| `exception` | `BaseException \| None` | 异常（`job_error` 事件） |

---

### 异常

| 异常 | 说明 |
|------|------|
| `SchedulerError` | 调度器基础异常 |
| `SchedulerAlreadyRunning` | 在已运行的调度器上调用 `start()` |
| `SchedulerNotRunning` | 操作需要调度器处于运行状态 |
| `JobNotFound` | 未找到任务 ID。包含 `job_id` 属性 |
| `InvalidCronExpression` | Cron 表达式格式错误。包含 `field` 和 `detail` 属性 |

---

### `parse_cron(expression)`

底层函数，将 5 字段 cron 表达式解析为 `CronSpec` 命名元组。

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `expression` | `str` | 5 字段 cron 表达式 |

**返回值：** `CronSpec(minutes, hours, doms, months, dows, expression)` — 每个字段为 `frozenset[int]`。

## 与 APScheduler / schedule / croniter 的对比

| 特性 | zerodep scheduler | APScheduler | schedule | croniter |
|------|-------------------|-------------|----------|----------|
| 依赖 | 无（仅标准库） | pytz、tzlocal 等 | 无 | 无 |
| Cron 表达式 | 支持（5 字段） | 支持（扩展格式） | 不支持 | 支持（仅解析） |
| 间隔触发器 | 支持 | 支持 | 支持 | 不支持 |
| 一次性触发器 | 支持 | 支持 | 不支持 | 不支持 |
| 异步任务 | 支持（自动检测） | 支持 | 不支持 | 不适用 |
| Per-job 回调 | 支持 | 通过监听器 | 不支持 | 不适用 |
| 事件系统 | 支持 | 支持 | 不支持 | 不适用 |
| 任务管理 | 暂停/恢复/立即执行 | 暂停/恢复/修改 | 取消 | 不适用 |
| 错过处理 | 可配置宽限时间 | 可配置 | 不支持 | 不适用 |
| 持久化 | 不支持 | 支持（多种存储） | 不支持 | 不适用 |
| 实现方式 | 单文件（~1000 行） | 包 | 包 | 包 |
| Cron 解析速度 | ~20 μs | ~74 μs | 不适用 | ~234 μs |

**何时使用 zerodep：** 你需要一个轻量级、零依赖的进程内调度器，覆盖标准的 cron/间隔/一次性调度场景。

**何时使用 APScheduler：** 你需要任务持久化、时区感知调度或高级触发器组合。

## 性能测试

与 `APScheduler`、`croniter` 和 `schedule` 在 cron 解析、下次触发时间计算、任务管理开销三个场景下进行对比。

详见 [调度器性能测试](../benchmarks/scheduler.md)。
