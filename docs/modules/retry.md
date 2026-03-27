# 重试

零依赖的装饰器式自动重试，支持可配置的退避策略、抖动模式、异常/结果/HTTP 状态码过滤，兼容同步与异步函数。

## 概述

`retry.py` 是一个单文件重试模块，提供装饰器和命令式两种使用方式。要求 **Python 3.10+**，**无需任何 pip 依赖**。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `retry.py` | 纯 Python 实现 | 无（仅标准库：`time`、`functools`、`random`、`asyncio`、`inspect`） |

## 功能特性

- **三种退避策略** -- `exponential`（指数）、`linear`（线性）、`fixed`（固定）
- **三种抖动模式** -- `full`（完全随机）、`equal`（半随机）、`none`（无抖动）
- **异常过滤** -- 按异常类型或自定义谓词决定是否重试
- **结果过滤** -- 根据返回值决定是否重试
- **HTTP 状态码过滤** -- 针对特定 HTTP 状态码（如 429、502、503）自动重试
- **同步 + 异步** -- 自动检测被装饰函数是否为协程，使用对应的 sleep
- **on_retry 回调** -- 每次重试前调用，接收 `RetryState` 实例
- **命令式用法** -- `retry_call()` 无需装饰器即可使用重试逻辑

## 快速开始

### 装饰器用法

```python
from retry import retry

@retry
def call_api():
    return get("https://api.example.com/data")

@retry(max_retries=5, backoff="linear")
def call_api_linear():
    return get("https://api.example.com/data")
```

### 异步用法

```python
import asyncio
from retry import retry

@retry(max_retries=3, retry_on=(ConnectionError, TimeoutError))
async def call_api():
    return await async_get("https://api.example.com/data")

asyncio.run(call_api())
```

### 异常过滤

```python
from retry import retry, retry_if_exception

# 仅对特定异常类型重试
@retry(retry_on=retry_if_exception(ConnectionError, TimeoutError))
def call_api():
    return get("https://api.example.com/data")

# 使用元组形式（等效写法）
@retry(retry_on=(ConnectionError, TimeoutError))
def call_api():
    return get("https://api.example.com/data")
```

### HTTP 状态码重试

```python
from retry import retry, retry_if_status

@retry(retry_on=retry_if_status(429, 502, 503))
def call_api():
    resp = get("https://api.example.com/data")
    resp.raise_for_status()
    return resp
```

### 返回值重试

```python
from retry import retry, retry_if_result

# 当返回值为 None 时重试
@retry(retry_on_result=retry_if_result(lambda r: r is None))
def poll_task():
    resp = get("https://api.example.com/task/123")
    return resp.json().get("result")
```

### on_retry 回调

```python
from retry import retry, RetryState

def log_retry(state: RetryState):
    print(
        f"Retry #{state.attempt}, delay={state.delay:.2f}s, "
        f"elapsed={state.elapsed:.2f}s, exception={state.exception}"
    )

@retry(max_retries=5, on_retry=log_retry)
def call_api():
    return get("https://api.example.com/data")
```

### 命令式用法

```python
from retry import retry_call

result = retry_call(
    call_api,
    args=("https://api.example.com/data",),
    max_retries=5,
    backoff="exponential",
)
```

### 错误处理

```python
from retry import retry, RetryError

@retry(max_retries=3, retry_on_result=lambda r: r is None)
def always_none():
    return None

try:
    always_none()
except RetryError as e:
    print(f"重试耗尽：{e.attempts} 次尝试")
    print(f"最后异常：{e.last_exception}")
```

## API 参考

### `retry(fn=None, *, ...)`

装饰器，在函数失败时使用可配置的退避策略自动重试。支持 `@retry`、`@retry()` 和 `@retry(...)` 三种用法。

**参数：**

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `fn` | `Callable \| None` | `None` | 被装饰的函数（无括号使用时自动传入） |
| `max_retries` | `int` | `3` | 最大重试次数（不含首次调用） |
| `base_delay` | `float` | `1.0` | 首次重试前的基础延迟（秒） |
| `max_delay` | `float` | `60.0` | 延迟时间上限（秒） |
| `backoff` | `str` | `"exponential"` | 退避策略：`"exponential"`、`"linear"` 或 `"fixed"` |
| `backoff_factor` | `float` | `2.0` | 指数退避的乘数因子 |
| `jitter` | `str` | `"full"` | 抖动模式：`"full"`（[0, delay] 均匀分布）、`"equal"`（delay/2 + [0, delay/2]）或 `"none"` |
| `retry_on` | `tuple[type[BaseException], ...] \| Callable` | `(Exception,)` | 触发重试的异常类型元组或谓词函数 |
| `retry_on_result` | `Callable[[Any], bool] \| None` | `None` | 返回值谓词，返回 `True` 时触发重试 |
| `on_retry` | `Callable[[RetryState], None] \| None` | `None` | 每次重试前调用的回调 |

**返回值：** 装饰后的函数（同步或异步，与原函数一致）。

**异常：**

- 异常触发的重试耗尽后，抛出原始异常。
- 返回值触发的重试耗尽后，抛出 `RetryError`。

---

### `retry_call(fn, args=(), kwargs=None, **retry_kwargs)`

命令式重试调用，无需装饰器。

**参数：**

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `fn` | `Callable` | -- | 要调用的函数 |
| `args` | `tuple` | `()` | 位置参数 |
| `kwargs` | `dict \| None` | `None` | 关键字参数 |
| `**retry_kwargs` | `Any` | -- | 与 `retry` 装饰器相同的关键字参数 |

**返回值：** 成功时返回 `fn` 的返回值。

---

### `retry_if_exception(*exc_types)`

构建一个异常过滤谓词。

**参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `*exc_types` | `type[BaseException]` | 需要重试的异常类型 |

**返回值：** `Callable[[BaseException], bool]` -- 异常匹配时返回 `True`。

---

### `retry_if_result(predicate)`

标记一个结果过滤谓词（恒等辅助函数）。

**参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `predicate` | `Callable[[Any], bool]` | 返回值谓词，返回 `True` 时触发重试 |

**返回值：** 同一个 callable。

---

### `retry_if_status(*status_codes)`

构建一个 HTTP 状态码过滤谓词。适用于任何携带 `status_code` 属性的异常（如 `httpclient.HTTPError`）。

**参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `*status_codes` | `int` | 需要重试的 HTTP 状态码（如 429、502、503） |

**返回值：** `Callable[[BaseException], bool]` -- 状态码匹配时返回 `True`。

---

### `RetryError`

所有重试耗尽后抛出的异常（仅在由 `retry_on_result` 触发时）。继承自 `Exception`。

| 属性 | 类型 | 说明 |
|------|------|------|
| `last_exception` | `BaseException \| None` | 最后一次尝试的异常，结果谓词触发时为 `None` |
| `attempts` | `int` | 总尝试次数（首次调用 + 重试次数） |

---

### `RetryState`

传递给 `on_retry` 回调的数据类，包含当前重试的状态信息。

| 属性 | 类型 | 说明 |
|------|------|------|
| `attempt` | `int` | 重试编号（从 1 开始，1 = 第一次重试，不含首次调用） |
| `exception` | `BaseException \| None` | 触发本次重试的异常，结果谓词触发时为 `None` |
| `result` | `Any` | 触发本次重试的返回值，异常触发时为 `None` |
| `delay` | `float` | 本次重试前等待的秒数 |
| `elapsed` | `float` | 自首次调用以来经过的秒数 |

## 退避策略说明

| 策略 | 公式 | 说明 |
|------|------|------|
| `exponential` | `base_delay * backoff_factor ^ attempt` | 指数增长，适合大多数场景 |
| `linear` | `base_delay * (attempt + 1)` | 线性增长，延迟增长较为平缓 |
| `fixed` | `base_delay` | 固定延迟，每次重试等待相同时间 |

所有策略的延迟均受 `max_delay` 上限和 `jitter` 抖动的影响。

## 与 tenacity / backoff 的对比

| 特性 | zerodep retry | tenacity | backoff |
|------|---------------|----------|---------|
| 依赖 | 无（仅标准库） | `attrs` 等 | 无 |
| 退避策略 | 3 种（指数、线性、固定） | 多种 | 多种 |
| 抖动模式 | 3 种 | 多种 | 2 种 |
| 异常过滤 | 支持 | 支持 | 支持 |
| 结果过滤 | 支持 | 支持 | 不支持 |
| HTTP 状态码过滤 | 支持 | 需自定义 | 不支持 |
| 同步 + 异步 | 支持 | 支持 | 支持 |
| on_retry 回调 | 支持 | 支持 | 支持 |
| 命令式 API | 支持 | 支持 | 不支持 |
| 单文件 | 是 | 否 | 否 |

**何时使用 zerodep：** 你需要一个轻量级、零依赖的重试方案，覆盖常见的退避与过滤场景。

**何时使用 tenacity：** 你需要更丰富的退避策略组合、等待条件或与其他框架的深度集成。

## 性能测试

与 `tenacity` 在装饰器开销、重试执行、退避计算三个场景下进行对比。

详见 [重试性能测试](../benchmarks/retry.md)。
