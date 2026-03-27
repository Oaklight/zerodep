# SSE 客户端

零依赖的 Server-Sent Events (SSE) 客户端，W3C 标准解析、自动重连、同步 + 异步双模式，仅标准库，Python 3.10+。

## 概述

SSE 模块提供完整的 [Server-Sent Events](https://html.spec.whatwg.org/multipage/server-sent-events.html) 流消费客户端。采用三层架构设计，你可以只使用解析器，也可以使用完整的自动重连客户端。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `sse.py` | 纯 Python 实现 | 无（仅标准库：`dataclasses`、`asyncio`、`time`、`os`） |

高级客户端（`SSEClient` / `AsyncSSEClient`）另需同项目的 `httpclient` 模块提供 HTTP 传输。

## 功能特性

- **W3C 标准解析** —— 支持 `event`、`data`、`id`、`retry` 字段，注释忽略，BOM 剥离，多行 data 合并
- **三层抽象** —— 独立解析器、迭代器包装、完整 HTTP 客户端
- **自动重连** —— 可配置重试间隔、最大重试次数和 Last-Event-ID 跟踪
- **同步 + 异步** —— `EventSource` / `AsyncEventSource` 和 `SSEClient` / `AsyncSSEClient`
- **204 = 停止** —— 服务器返回 HTTP 204 表示优雅终止流
- **LLM API 就绪** —— 专为 OpenAI、Anthropic、Google 等流式 API 设计

## 快速开始

### 复制文件

```bash
cp sse/sse.py your_project/
```

如需高级客户端，同时复制 `httpclient`：

```bash
cp httpclient/httpclient.py your_project/
```

然后直接导入：

```python
from sse import connect, EventSource, SSEEvent
```

## 使用示例

### 高级客户端（自动连接 + 重连）

```python
from sse import connect

with connect("https://api.example.com/events") as events:
    for event in events:
        print(event.event, event.data)
```

### 异步客户端

```python
import asyncio
from sse import async_connect

async def main():
    async with async_connect("https://api.example.com/events") as events:
        async for event in events:
            print(event.data)

asyncio.run(main())
```

### 自定义请求头（如 LLM API）

```python
from sse import connect

with connect(
    "https://api.openai.com/v1/chat/completions",
    headers={"Authorization": "Bearer sk-..."},
) as events:
    for event in events:
        if event.data == "[DONE]":
            break
        print(event.data)
```

### 低级解析器（无需 HTTP 依赖）

```python
from sse import EventSource

lines = [
    "event: greeting",
    "data: hello",
    "",
    "data: line 1",
    "data: line 2",
    "",
]
for event in EventSource(lines):
    print(event.event, repr(event.data))
    # "greeting" "hello"
    # "message" "line 1\nline 2"
```

### 异步低级解析器

```python
from sse import AsyncEventSource

async def parse_stream(async_line_source):
    async for event in AsyncEventSource(async_line_source):
        print(event.data)
```

### 配合 httpclient 流式响应

```python
from httpclient import get
from sse import EventSource

with get("https://api.example.com/events", stream=True) as r:
    for event in EventSource(r.iter_lines()):
        print(event.data)
```

### 重连配置

```python
from sse import connect

with connect(
    "https://api.example.com/events",
    retry_interval=5000,     # 重连间隔 5 秒
    max_retries=10,          # 最多重试 10 次（-1 = 无限）
    last_event_id="evt-42",  # 从指定事件 ID 恢复
) as events:
    for event in events:
        print(event.data)
```

## 自动重连机制

高级客户端（`SSEClient` / `AsyncSSEClient`）在连接断开时自动重连：

1. 发送 GET 请求，设置 `Accept: text/event-stream`
2. 如有上次事件 ID，附带 `Last-Event-ID` 请求头
3. 解析事件流，实时更新 `last_event_id` 和 `retry_interval`
4. 连接断开后，等待 `retry_interval` 毫秒然后重连
5. 每成功接收一个事件后重置重试计数器
6. 服务器返回 HTTP 204 表示"停止重连"（优雅终止）
7. 非 2xx 响应抛出 `SSEHTTPError`
8. 超过 `max_retries` 抛出 `SSEConnectionError`

## API 参考

### `SSEEvent`

冻结数据类，表示单个 Server-Sent Event。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `event` | `str` | `"message"` | 事件类型 |
| `data` | `str` | `""` | 事件载荷（多行 `data:` 用 `\n` 连接） |
| `id` | `str` | `""` | 最后事件 ID（跨事件持久化，直到服务器更改） |
| `retry` | `int \| None` | `None` | 重连间隔（毫秒） |

---

### `EventSource(lines)`

同步 SSE 解析器，包装任意 `Iterable[str]` 行源。

**参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `lines` | `Iterable[str]` | 行源（如字符串列表、文件对象、`response.iter_lines()`） |

**产出：** `SSEEvent` 对象。

---

### `AsyncEventSource(lines)`

异步 SSE 解析器，包装任意 `AsyncIterable[str]` 行源。

**参数：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `lines` | `AsyncIterable[str]` | 异步行源 |

**产出：** `SSEEvent` 对象。

---

### `SSEClient(url, **kwargs)` / `connect(url, **kwargs)`

同步 SSE 客户端，支持自动重连。用作上下文管理器。

**参数：**

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `url` | `str` | -- | SSE 端点 URL |
| `headers` | `dict[str, str] \| None` | `None` | 额外 HTTP 请求头 |
| `timeout` | `float` | `30.0` | HTTP 请求超时（秒） |
| `retry_interval` | `int` | `3000` | 重连间隔（毫秒，W3C 规范默认值） |
| `max_retries` | `int` | `-1` | 最大重连次数（`-1` = 无限） |
| `verify` | `bool` | `True` | 是否验证 TLS 证书 |
| `last_event_id` | `str` | `""` | 初始 Last-Event-ID，用于断点续传 |

**方法：**

| 方法 | 说明 |
|------|------|
| `__iter__()` | 迭代产出 `SSEEvent` 对象 |
| `close()` | 关闭连接 |

---

### `AsyncSSEClient(url, **kwargs)` / `async_connect(url, **kwargs)`

异步 SSE 客户端，支持自动重连。用作异步上下文管理器。

参数与 `SSEClient` 相同。使用 `async for` 和 `await close()`。

---

### 异常类

| 异常 | 说明 |
|------|------|
| `SSEError` | 所有 SSE 错误的基类 |
| `SSEConnectionError` | `max_retries` 耗尽时抛出。属性：`url`、`retries`、`last_error` |
| `SSEHTTPError` | 收到非 2xx HTTP 响应（204 除外）时抛出。属性：`status_code`、`url` |

## 与 httpx-sse 的对比

| 特性 | zerodep SSE | httpx-sse |
|------|-------------|-----------|
| 依赖 | 无（仅标准库） | httpx |
| 独立解析器 | 有（`EventSource`） | 无（需要 `httpx.Response`） |
| 自动重连 | 有 | 无 |
| Last-Event-ID 跟踪 | 有 | 无 |
| 同步 + 异步 | 有 | 有 |
| 204 优雅停止 | 有 | 无 |
| W3C 解析 | 有 | 有 |
| 解析速度 | ~1.5 ms / 1000 事件 | ~1.4 ms / 1000 事件 |
| 实现 | 单文件（~380 行） | 包（多文件） |

**何时使用 zerodep：** 你需要一个自包含的 SSE 客户端，具备自动重连和零依赖，或者需要一个不与任何 HTTP 库耦合的独立解析器。

**何时使用 httpx-sse：** 你已经在使用 httpx，只需一个轻量的 SSE 解析扩展。

## 性能测试

与 `httpx-sse` 在小、中、大三种事件流规模下进行对比。

详见 [SSE 客户端性能测试](../benchmarks/sse.md)。
