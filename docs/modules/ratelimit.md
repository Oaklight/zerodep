# 限流器

零依赖多算法限流器，支持同步 + 异步 — 仅标准库，Python 3.10+。

> **可替代：** `limits`、`pyrate-limiter`、`aiolimiter`、`limiter`

## 概述

ratelimit 模块提供 4 种内存限流算法，统一于 `RateLimiter` Protocol，并附带便捷包装器（装饰器、上下文管理器、字符串配额表示法）。

| 文件 | 描述 | 依赖 |
|------|------|------|
| `ratelimit.py` | 4 种算法 + 便捷 API | 无（仅标准库） |

## 算法

| 算法 | 类名 | 适用场景 |
|------|------|----------|
| 令牌桶 | `TokenBucketLimiter` | Per-IP 限流，平滑速率 + burst 容忍 |
| 固定窗口 | `FixedWindowLimiter` | 简单计数器，最低开销 |
| 滑动窗口计数器 | `SlidingWindowLimiter` | 无边界突发，精确限流 |
| GCRA | `GCRALimiter` | 恒定速率整形，单 TAT 时间戳 |

## 特性

- **4 种算法** 统一于 `RateLimiter` Protocol
- **同步 + 异步** — 所有类均提供 `acquire()`/`peek()` 和 `aacquire()`/`apeek()`
- **装饰器 + 上下文管理器** — `@ratelimit("10/s")` 或 `with ratelimit("5/m")`
- **字符串配额表示法** — 解析 `"100/s"`、`"10 per minute burst 20"`
- **线程安全包装器** — `ThreadSafeLimiter`，per-key 锁
- **等待重试** — 阻塞等待最多 `timeout` 秒获取配额
- **可注入时钟** — 通过 `clock` 参数实现确定性测试
- **摊销清理** — 每 128 次 acquire 清理过期 key

## 使用方式

```bash
zerodep add ratelimit
# 或直接复制 ratelimit/ratelimit.py 到你的项目
```

## 快速开始

### 直接使用

```python
from ratelimit import TokenBucketLimiter

limiter = TokenBucketLimiter(rate=10.0, capacity=20)
result = limiter.acquire("client-ip")
if not result.allowed:
    return 429, {"Retry-After": str(result.retry_after)}
```

### 工厂函数 + 字符串配额

```python
from ratelimit import create_limiter

limiter = create_limiter("sliding_window", "100/m burst 200")
result = limiter.acquire("user-123")
```

### 装饰器

```python
from ratelimit import ratelimit

@ratelimit("10/s", algorithm="token_bucket")
def handle_request():
    ...

@ratelimit("5/s")
async def async_handler():
    ...
```

### 上下文管理器

```python
from ratelimit import ratelimit

with ratelimit("5/m", key="user-1") as result:
    print(f"剩余配额: {result.remaining}")

async with ratelimit("5/m", key="user-1") as result:
    await do_work()
```

### 等待重试

```python
from ratelimit import ratelimit

# 最多阻塞 5 秒等待配额
with ratelimit("10/s", timeout=5.0):
    do_work()
```

### 线程安全

```python
from ratelimit import TokenBucketLimiter, ThreadSafeLimiter

limiter = ThreadSafeLimiter(TokenBucketLimiter(rate=100.0, capacity=100))
# 多线程安全调用 — per-key 锁
result = limiter.acquire("client-ip")
```

### 异步 API

```python
from ratelimit import TokenBucketLimiter

limiter = TokenBucketLimiter(rate=10.0, capacity=20)
result = await limiter.aacquire("client-ip")
state = await limiter.apeek("client-ip")
```

## RateLimitResult

每次 `acquire()` / `peek()` 调用返回一个 `RateLimitResult`：

| 字段 | 类型 | 描述 |
|------|------|------|
| `allowed` | `bool` | 请求是否被允许 |
| `limit` | `int \| float` | 总配额（容量或窗口限制） |
| `remaining` | `int \| float` | 剩余配额（分数令牌时为 float） |
| `reset_at` | `float` | 配额恢复的单调时钟时间戳 |
| `retry_after` | `float \| None` | 重试等待秒数（allowed 时为 `None`） |

## 配额字符串格式

| 模式 | 示例 |
|------|------|
| `N/unit` | `"100/s"`、`"10/m"`、`"5/h"`、`"1/d"` |
| `N per unit` | `"10 per minute"` |
| `N/unit burst B` | `"100/s burst 200"` |
| `N per unit burst B` | `"10 per minute burst 20"` |

支持的时间单位：`s`/`sec`/`second`、`m`/`min`/`minute`、`h`/`hr`/`hour`、`d`/`day`（接受复数形式）。

## 性能

全部 4 种算法的 `acquire()` 调用均在 1μs 以内，比 `limits` 库在可比算法上**快 6-7 倍**，FixedWindow 与 `token-bucket` C 扩展差距仅 5%。

详见[完整性能测试结果](../benchmarks/ratelimit.md)，包含详细对比、多线程吞吐量和优化历程。
