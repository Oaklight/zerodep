# HTTP 客户端

零依赖的同步与异步 HTTP/1.1 REST 客户端，完全基于 Python 标准库构建。

## 概述

`httpclient.py` 是一个单文件 HTTP 客户端，支持同步和异步两种工作模式。要求 **Python 3.10+**，**无需任何 pip 依赖**。API 设计沿袭 `requests` / `httpx` 风格——如果你用过其中任何一个，就已经知道怎么使用本模块。

- **熟悉的 API** — `get()`、`post()`、`Response.json()`、`Response.status_code`、`Client` / `AsyncClient` 会话——全部对齐 `requests` 和 `httpx` 的接口风格。
- **同步模式**使用标准库中的 `http.client`。
- **异步模式**使用 `asyncio` 流，手写 HTTP/1.1 协议实现。
- **线程安全**设计：每个请求创建独立连接。会话类内部使用锁机制。

## 两种使用模式

### 函数 API（无状态）

顶层函数如 `get()`、`post()`、`async_get()` 等。每次调用都是独立的，线程安全——调用之间没有共享状态。

```python
from httpclient import get, post

# 简单 GET 请求
response = get("https://httpbin.org/get")
print(response.json())

# 带 JSON 的 POST 请求
response = post("https://httpbin.org/post", json={"key": "value"})
print(response.status_code)
```

### 会话 API（Client / AsyncClient）

`Client` 和 `AsyncClient` 类允许在多个请求之间共享默认请求头、超时时间等设置。

```python
from httpclient import Client

with Client(headers={"Authorization": "Bearer token"}) as client:
    r1 = client.get("https://api.example.com/users")
    r2 = client.post("https://api.example.com/users", json={"name": "Alice"})
```

!!! note "无连接池"
    与 httpx 或 requests 不同，每个请求都会创建一个新的 TCP 连接。这使实现保持简洁且无依赖，代价是对同一主机的重复请求会有一些额外开销。

## 使用示例

### 基本 GET 请求

```python
from httpclient import get

response = get("https://httpbin.org/get")
print(response.status_code)  # 200
print(response.ok)           # True
print(response.json())       # {...}
```

### 带查询参数的 GET

```python
from httpclient import get

response = get(
    "https://httpbin.org/get",
    params={"search": "python", "page": 1},
)
print(response.url)  # https://httpbin.org/get?search=python&page=1
```

### 发送 JSON 的 POST

```python
from httpclient import post

response = post(
    "https://httpbin.org/post",
    json={"username": "alice", "email": "alice@example.com"},
)
data = response.json()
print(data["json"])  # {"username": "alice", "email": "alice@example.com"}
```

### 自定义请求头

```python
from httpclient import get

response = get(
    "https://api.example.com/data",
    headers={
        "Authorization": "Bearer my-token",
        "Accept": "application/json",
    },
)
```

### 错误处理

```python
from httpclient import get, HTTPError

response = get("https://httpbin.org/status/404")
print(response.ok)  # False

try:
    response.raise_for_status()
except HTTPError as e:
    print(f"HTTP {e.status_code} for {e.url}")
```

### 文件上传

```python
from httpclient import post

# 简单文件上传
response = post(
    "https://httpbin.org/post",
    files={"file": ("report.txt", b"file content", "text/plain")},
)

# 同时上传文件和表单字段
response = post(
    "https://httpbin.org/post",
    data={"username": "alice"},
    files={"avatar": open("photo.jpg", "rb")},
)

# 多文件上传
response = post(
    "https://httpbin.org/post",
    files=[
        ("attachment", ("doc1.pdf", pdf_bytes)),
        ("attachment", ("doc2.pdf", pdf_bytes2)),
    ],
)
```

### 会话用法

```python
from httpclient import Client

with Client(
    headers={"Authorization": "Bearer token"},
    timeout=10.0,
) as client:
    users = client.get("https://api.example.com/users").json()
    profile = client.get("https://api.example.com/me").json()
```

### 异步用法

```python
import asyncio
from httpclient import async_get, AsyncClient

async def main():
    # 函数 API
    response = await async_get("https://httpbin.org/get")
    print(response.json())

    # 会话 API
    async with AsyncClient(headers={"X-Api-Key": "secret"}) as client:
        r = await client.get("https://api.example.com/data")
        print(r.json())

asyncio.run(main())
```

### 流式传输

```python
from httpclient import get, async_get

# 同步流式传输
with get("https://httpbin.org/get", stream=True) as r:
    for chunk in r.iter_bytes():
        process(chunk)

# 逐行读取（适用于 SSE）
with get("https://example.com/events", stream=True) as r:
    for line in r.iter_lines():
        print(line)

# 异步流式传输
async with await async_get("https://httpbin.org/get", stream=True) as r:
    async for chunk in r.aiter_bytes():
        await process(chunk)
```

### 禁用 TLS 验证

```python
from httpclient import get

# 不建议在生产环境中使用
response = get("https://self-signed.example.com/api", verify=False)
```

## API 参考

### 同步函数

所有同步函数接受相同的关键字参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `headers` | `dict[str, str]` | `None` | 请求头 |
| `data` | `bytes \| str \| dict[str, str]` | `None` | 原始请求体，或与 `files` 配合使用时的表单字段 |
| `files` | `dict[str, ...] \| list[tuple[str, ...]]` | `None` | 文件上传字段（multipart/form-data） |
| `json` | `Any` | `None` | 可序列化为 JSON 的请求体（自动设置 Content-Type） |
| `params` | `dict[str, Any]` | `None` | URL 查询参数 |
| `timeout` | `float` | `30.0` | 请求超时时间（秒） |
| `max_redirects` | `int` | `10` | 最大重定向次数 |
| `verify` | `bool` | `True` | 是否验证 TLS 证书 |
| `stream` | `bool` | `False` | 返回 `StreamingResponse` 以增量消费响应体 |

```python
get(url, **kwargs) -> Response
post(url, **kwargs) -> Response
put(url, **kwargs) -> Response
patch(url, **kwargs) -> Response
delete(url, **kwargs) -> Response
head(url, **kwargs) -> Response
options(url, **kwargs) -> Response
```

### 异步函数

参数与同步函数相同，但需要使用 `await`：

```python
await async_get(url, **kwargs) -> Response
await async_post(url, **kwargs) -> Response
await async_put(url, **kwargs) -> Response
await async_patch(url, **kwargs) -> Response
await async_delete(url, **kwargs) -> Response
await async_head(url, **kwargs) -> Response
await async_options(url, **kwargs) -> Response
```

### Response 对象

| 属性 / 方法 | 类型 | 说明 |
|-------------|------|------|
| `status_code` | `int` | HTTP 状态码 |
| `headers` | `dict[str, str]` | 响应头（键为小写） |
| `content` | `bytes` | 原始响应体 |
| `url` | `str` | 重定向后的最终 URL |
| `text` | `str`（属性） | 解码后的响应体文本 |
| `ok` | `bool`（属性） | 状态码为 2xx 时返回 `True` |
| `json()` | `Any` | 将响应体解析为 JSON |
| `raise_for_status()` | `None` | 状态码非 2xx 时抛出 `HTTPError` |

### StreamingResponse 对象

当 `stream=True` 时返回。应作为上下文管理器使用以确保资源清理。

| 属性 / 方法 | 类型 | 说明 |
|---|---|---|
| `status_code` | `int` | HTTP 状态码 |
| `headers` | `dict[str, str]` | 响应头（键为小写） |
| `url` | `str` | 重定向后的最终 URL |
| `ok` | `bool`（属性） | 状态码为 2xx 时返回 `True` |
| `raise_for_status()` | `None` | 状态码非 2xx 时抛出 `HTTPError` |
| `iter_bytes(chunk_size)` | `Iterator[bytes]` | 按块生成响应体 |
| `iter_lines()` | `Iterator[str]` | 逐行生成解码后的文本 |
| `read()` | `bytes` | 读取整个流 |
| `aiter_bytes(chunk_size)` | `AsyncIterator[bytes]` | 异步按块生成响应体 |
| `aiter_lines()` | `AsyncIterator[str]` | 异步逐行生成解码后的文本 |
| `aread()` | `bytes` | 异步读取整个流 |
| `close()` / `aclose()` | `None` | 关闭底层连接 |

### Client 类

```python
Client(
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    max_redirects: int = 10,
    verify: bool = True,
)
```

支持上下文管理器（`with` 语句）。方法：`get`、`post`、`put`、`patch`、`delete`、`head`、`options`、`request`。

线程安全：内部使用 `threading.Lock`。

### AsyncClient 类

```python
AsyncClient(
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    max_redirects: int = 10,
    verify: bool = True,
)
```

支持异步上下文管理器（`async with` 语句）。方法：`get`、`post`、`put`、`patch`、`delete`、`head`、`options`、`request`。

内部使用 `asyncio.Lock`，保证同一客户端实例的并发访问安全。

### 异常类

| 异常 | 说明 |
|------|------|
| `HTTPError` | 由 `raise_for_status()` 在非 2xx 状态时抛出。包含 `status_code`、`body` 和 `url` 属性。 |
| `TooManyRedirects` | `HTTPError` 的子类。超出重定向限制时抛出。包含 `max_redirects` 属性。 |
| `ConnectionError` | TCP/TLS 连接失败时抛出。 |
| `TimeoutError` | 请求超时时抛出。 |

## 功能特性

- **自动跟随重定向** -- 处理 301、302、303、307、308，并正确转换请求方法（303 时 POST 转为 GET 等）
- **分块传输编码** -- 异步模式下自动解码
- **TLS 支持** -- 通过 `ssl.create_default_context()` 实现 HTTPS，可选禁用证书验证
- **可配置超时** -- 支持按请求或按会话设置超时
- **JSON 处理** -- 自动序列化/反序列化，自动设置正确的 Content-Type
- **查询参数编码** -- 通过 `params` 参数自动编码
- **Multipart 文件上传** -- 通过 `files` 参数上传文件，支持与 `data` 表单字段混合使用
- **流式响应** -- 通过 `iter_bytes()` / `iter_lines()` 及其异步版本增量消费响应体

## 在项目中使用

将 `httpclient.py` 复制到你的项目中：

```bash
cp httpclient/httpclient.py your_project/
```

然后导入：

```python
from httpclient import get, post, Client, AsyncClient
```

!!! warning "不要重命名为 `http.py`"
    文件名不能是 `http.py`——这会遮蔽标准库的 `http` 模块，而 `httpclient.py` 内部依赖该模块。

## 与 httpx 的对比

| 特性 | zerodep | httpx |
|------|---------|-------|
| 依赖 | 无（仅标准库） | 多个（httpcore、h11 等） |
| HTTP/2 | 不支持 | 支持 |
| 连接池 | 不支持 | 支持 |
| 流式传输 | 支持 | 支持 |
| 同步 + 异步 | 支持 | 支持 |
| 文件上传 | 支持 | 支持 |
| Cookie 管理 | 不支持 | 支持 |
| 线程安全 | 支持 | 支持 |

**何时使用 zerodep：** 你需要一个轻量级、无外部依赖的 HTTP 客户端，使用场景为基本的 REST API 调用。

**何时使用 httpx：** 你需要 HTTP/2、连接池或 Cookie 管理。

## 性能测试

与 `httpx` 进行对比。一次性请求较慢（无连接池），但会话/异步模式下性能基本持平，因为此时受限于网络延迟。

详见 [HTTP 客户端性能测试](../benchmarks/http.md)。
