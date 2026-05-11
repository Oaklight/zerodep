# JSON-RPC

JSON-RPC 2.0 协议实现 -- 零依赖，仅标准库，Python 3.10+。

> **可替代:** `jsonrpclib`、`jsonrpcserver`、`python-jsonrpc`

## 概述

JSON-RPC 模块提供完整的 [JSON-RPC 2.0](https://www.jsonrpc.org/specification) 实现，包括核心数据类型、异常层次结构、支持流式的方法分发器，以及基于换行分隔 JSON 流的异步传输层。它是 [A2A](a2a.md) 和 [ACP](acp.md) 智能体协议模块的共享协议基础。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `jsonrpc.py` | 纯 Python JSON-RPC 2.0 实现 | 无（仅标准库） |

提供五层功能：

- **核心类型：** `JSONRPCError`、`JSONRPCRequest`、`JSONRPCResponse` 数据类，支持序列化
- **异常：** `JSONRPCException` 包装 `JSONRPCError` 用于控制流
- **ID 生成：** 线程安全的自增请求 ID 计数器
- **分发器：** 方法路由，支持自动错误处理和流式响应
- **异步传输：** 基于 `asyncio` 流的换行分隔 JSON-RPC

## 如何在你的项目中使用

只需将 `.py` 文件复制到你的项目中：

```bash
cp jsonrpc/jsonrpc.py your_project/
```

然后直接导入：

```python
from jsonrpc import JSONRPCDispatcher, JSONRPCRequest, JSONRPCResponse
```

## API 参考

### 常量

| 常量 | 值 | 说明 |
|------|------|------|
| `JSONRPC_VERSION` | `"2.0"` | 协议版本字符串。 |
| `PARSE_ERROR` | `-32700` | 接收到无效 JSON。 |
| `INVALID_REQUEST` | `-32600` | JSON 不是有效的请求。 |
| `METHOD_NOT_FOUND` | `-32601` | 方法不存在。 |
| `INVALID_PARAMS` | `-32602` | 方法参数无效。 |
| `INTERNAL_ERROR` | `-32603` | 内部 JSON-RPC 错误。 |

---

### `class JSONRPCError`

JSON-RPC 2.0 错误对象（数据类）。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `code` | `int` | `-32603` | 数字错误码。 |
| `message` | `str` | `"Internal error"` | 可读的错误信息。 |
| `data` | `Any` | `None` | 可选的附加错误数据。 |

**方法：**

- `to_dict() -> dict` -- 序列化为字典。`data` 为 `None` 时省略。
- `from_dict(raw) -> JSONRPCError` -- 从字典反序列化（类方法）。

---

### `class JSONRPCRequest`

JSON-RPC 2.0 请求对象（数据类）。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `method` | `str` | `""` | RPC 方法名。 |
| `params` | `dict[str, Any] \| None` | `None` | 方法参数。 |
| `id` | `str \| int \| None` | `None` | 请求标识符（通知请求为 `None`）。 |
| `jsonrpc` | `str` | `"2.0"` | 协议版本。 |

**属性：**

- `is_notification -> bool` -- `id` 为 `None` 时返回 `True`。

**方法：**

- `to_dict() -> dict` -- 序列化为字典。`id` 和 `params` 为 `None` 时省略。
- `from_dict(d) -> JSONRPCRequest` -- 从字典反序列化（类方法）。

---

### `class JSONRPCResponse`

JSON-RPC 2.0 响应对象（数据类）。`result` 和 `error` 应恰好设置其中一个。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `id` | `str \| int \| None` | `None` | 对应的请求标识符。 |
| `result` | `Any` | `None` | 成功时的结果载荷。 |
| `error` | `JSONRPCError \| None` | `None` | 失败时的错误详情。 |
| `jsonrpc` | `str` | `"2.0"` | 协议版本。 |

**方法：**

- `to_dict() -> dict` -- 序列化为字典。
- `from_dict(d) -> JSONRPCResponse` -- 从字典反序列化（类方法）。
- `success(request_id, result) -> JSONRPCResponse` -- 创建成功响应（类方法）。
- `from_error(request_id, error) -> JSONRPCResponse` -- 从 `JSONRPCError`、`JSONRPCException` 或鸭子类型错误对象创建错误响应（类方法）。

---

### `class JSONRPCException`

包装 `JSONRPCError` 的异常类。

| 属性 | 类型 | 说明 |
|------|------|------|
| `error` | `JSONRPCError` | 底层错误对象。 |

字符串表示为错误信息。

---

### `next_id() -> int`

返回下一个自增请求 ID。线程安全（基于 `itertools.count`）。

---

### `class JSONRPCDispatcher`

将 JSON-RPC 方法调用路由到注册的处理函数。支持普通和流式（生成器）处理函数。

**方法：**

#### `register(method) -> decorator`

注册方法处理函数的装饰器。

```python
@dispatcher.register("echo")
def handle_echo(params):
    return params
```

#### `dispatch(request) -> JSONRPCResponse | Iterator[JSONRPCResponse]`

将解析后的请求分发到对应的处理函数。返回单个响应或（对于生成器处理函数）响应迭代器。

- 处理函数抛出的 `JSONRPCException` 会被捕获并转换为错误响应。
- 其他异常产生 `INTERNAL_ERROR` 响应。

---

### `class JSONRPCTransport`

基于换行分隔 JSON 流的异步 JSON-RPC 2.0 传输层。

```python
transport = JSONRPCTransport(reader, writer)
```

**方法：**

| 方法 | 说明 |
|------|------|
| `await read_message()` | 读取下一个 JSON 对象。EOF 时返回 `None`。跳过空行和格式错误的 JSON。 |
| `await write_message(msg)` | 写入 JSON 对象并追加 `\n`。 |
| `await send_request(method, params, req_id)` | 构建并发送请求（未提供时自动生成 `id`）。 |
| `await send_notification(method, params)` | 发送通知（无 `id`）。 |
| `await send_result(req_id, result)` | 发送成功响应。 |
| `await send_error(req_id, error)` | 发送错误响应。 |
| `await close()` | 关闭写入流（幂等）。 |

**属性：**

- `is_closed -> bool` -- 传输是否已关闭。

## 用法示例

### 基本分发

```python
from jsonrpc import JSONRPCDispatcher, JSONRPCRequest

dispatcher = JSONRPCDispatcher()

@dispatcher.register("add")
def handle_add(params):
    return params["a"] + params["b"]

req = JSONRPCRequest(method="add", params={"a": 2, "b": 3}, id=1)
resp = dispatcher.dispatch(req)
print(resp.result)  # 5
```

### 流式处理

```python
from jsonrpc import JSONRPCDispatcher, JSONRPCRequest

dispatcher = JSONRPCDispatcher()

@dispatcher.register("count")
def handle_count(params):
    for i in range(params["n"]):
        yield {"index": i}

req = JSONRPCRequest(method="count", params={"n": 3}, id=1)
for resp in dispatcher.dispatch(req):
    print(resp.result)
# {"index": 0}
# {"index": 1}
# {"index": 2}
```

### 错误处理

```python
from jsonrpc import (
    JSONRPCDispatcher,
    JSONRPCError,
    JSONRPCException,
    JSONRPCRequest,
)

dispatcher = JSONRPCDispatcher()

@dispatcher.register("fail")
def handle_fail(params):
    raise JSONRPCException(
        JSONRPCError(code=-32001, message="Custom error", data={"reason": "demo"})
    )

resp = dispatcher.dispatch(JSONRPCRequest(method="fail", id=1))
print(resp.error.code)     # -32001
print(resp.error.message)  # "Custom error"
```

### 异步传输

```python
import asyncio
from jsonrpc import JSONRPCTransport

async def main():
    reader, writer = await asyncio.open_connection("localhost", 8080)
    transport = JSONRPCTransport(reader, writer)

    # 发送请求
    await transport.send_request("ping", {"timestamp": 12345})

    # 读取响应
    response = await transport.read_message()
    print(response)

    await transport.close()
```

### 序列化往返

```python
import json
from jsonrpc import JSONRPCRequest

req = JSONRPCRequest(method="echo", params={"msg": "hi"}, id=7)
wire = json.dumps(req.to_dict())
restored = JSONRPCRequest.from_dict(json.loads(wire))
assert restored.method == "echo"
assert restored.params == {"msg": "hi"}
```

## 注意事项

!!! info "共享基础"
    本模块通过 zerodep 的兄弟导入机制被 [A2A](a2a.md) 和 [ACP](acp.md) 协议模块内部使用。复制依赖 `jsonrpc` 的模块时，使用 `zerodep` CLI 工具可自动解析依赖关系。

- **Python 版本：** 需要 Python 3.10+（使用了 `X | Y` 联合类型标注语法）。
- **线程安全：** `next_id()` 线程安全（使用 `itertools.count`）。分发器本身在并发注册时不是线程安全的，但设置完成后可安全并发分发。
- **流式：** 生成器处理函数会被包装，每个 yield 值成为独立的 `JSONRPCResponse`。流式中途的异常会产生最终的错误响应。
- **传输：** 使用换行分隔 JSON（`\n` 分隔）。每条消息必须是单行。

## 性能测试

与 `jsonrpcserver` 进行端到端分发性能对比（JSON 字符串输入，JSON 字符串输出）。

详见 [JSON-RPC 性能测试](../benchmarks/jsonrpc.md)。
