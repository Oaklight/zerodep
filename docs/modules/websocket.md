# WebSocket 客户端

零依赖的 RFC 6455 WebSocket 客户端，同步 + 异步支持 -- 仅标准库，Python 3.10+。

> **可替代:** `websocket-client`、`websockets`

## 概览

websocket 模块提供同步和异步 WebSocket 客户端，支持 `ws://` 和 `wss://` 连接。实现了核心 WebSocket 协议，包括文本帧、ping/pong、关闭握手和客户端侧掩码。作为 `websockets` 库的无依赖替代方案，适用于不需要第三方依赖的 WebSocket 通信场景。

| 文件 | 描述 | 依赖 |
|------|------|------|
| `websocket.py` | 纯 Python 实现 | 无（仅标准库：`asyncio`、`socket`、`ssl`、`hashlib`、`struct`） |

## 特性

- **RFC 6455 合规** -- 完整 WebSocket 协议，包含升级握手、帧编解码和掩码
- **同步 + 异步客户端** -- `WebSocketClient` 和 `AsyncWebSocketClient`，API 完全一致
- **TLS 支持** -- `wss://` 连接，可配置证书验证
- **Ping/pong** -- 收到 ping 帧时自动回复 pong
- **关闭握手** -- 完整的关闭帧交换，支持状态码和原因
- **自定义头部** -- 在升级请求中传递额外头部（认证令牌、Cookie 等）
- **子协议协商** -- 请求并检测服务端接受的子协议
- **超时控制** -- 可配置连接、发送和接收操作的超时时间
- **上下文管理器** -- `with` / `async with` 自动连接和关闭

## 在项目中使用

将单个 `.py` 文件复制到你的项目中：

```bash
cp websocket/websocket.py your_project/
```

然后直接导入：

```python
from websocket import WebSocketClient, AsyncWebSocketClient
```

## 使用示例

### 基本同步客户端

```python
from websocket import WebSocketClient

with WebSocketClient("ws://localhost:9222/") as ws:
    ws.send("hello")
    response = ws.recv()
    print(response)
```

### 基本异步客户端

```python
import asyncio
from websocket import AsyncWebSocketClient

async def main():
    async with AsyncWebSocketClient("wss://example.com/ws") as ws:
        await ws.send('{"type": "subscribe"}')
        data = await ws.recv()
        print(data)

asyncio.run(main())
```

### WebSocket 上的 JSON-RPC

```python
import json
from websocket import WebSocketClient

with WebSocketClient("ws://localhost:9222/devtools/page/123") as ws:
    # 发送 CDP 命令
    ws.send(json.dumps({
        "id": 1,
        "method": "Page.navigate",
        "params": {"url": "https://example.com"}
    }))
    result = json.loads(ws.recv())
    print(result)
```

### 自定义头部

```python
from websocket import WebSocketClient

headers = {
    "Authorization": "Bearer my-token",
    "X-Custom-Header": "value",
}
with WebSocketClient("ws://localhost:8080/ws", headers=headers) as ws:
    ws.send("authenticated message")
    print(ws.recv())
```

### 接收超时

```python
from websocket import WebSocketClient, WebSocketTimeoutError

with WebSocketClient("ws://localhost:8080/ws") as ws:
    ws.send("ping")
    try:
        response = ws.recv(timeout=5.0)
    except WebSocketTimeoutError:
        print("5 秒内未收到响应")
```

### 手动连接 / 关闭

```python
from websocket import WebSocketClient

ws = WebSocketClient("ws://localhost:8080/ws")
ws.connect(timeout=10)

ws.send("hello")
print(ws.recv())

ws.close(code=1000, reason="done")
```

### 安全连接 (WSS)

```python
from websocket import WebSocketClient

# 使用证书验证（默认）
with WebSocketClient("wss://echo.websocket.org") as ws:
    ws.send("secure hello")
    print(ws.recv())

# 不验证证书（例如自签名证书）
ws = WebSocketClient("wss://localhost:9443/ws")
ws.connect(verify=False)
```

## API 参考

### `WebSocketClient(url, *, headers=None, subprotocols=None)`

同步 WebSocket 客户端。

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `url` | `str` | -- | WebSocket URL（`ws://` 或 `wss://`） |
| `headers` | `dict[str, str] \| None` | `None` | 升级请求的额外头部 |
| `subprotocols` | `list[str] \| None` | `None` | 要协商的子协议 |

| 方法 | 描述 |
|------|------|
| `connect(*, timeout=30.0, verify=True)` | 打开 WebSocket 连接 |
| `send(data: str)` | 发送文本消息 |
| `recv(*, timeout=None) -> str` | 接收文本消息 |
| `ping(data=b"")` | 发送 ping 帧 |
| `close(code=1000, reason="")` | 通过关闭握手关闭连接 |

| 属性 | 类型 | 描述 |
|------|------|------|
| `connected` | `bool` | 连接是否处于活跃状态 |
| `accepted_subprotocol` | `str \| None` | 服务端接受的子协议 |

---

### `AsyncWebSocketClient(url, *, headers=None, subprotocols=None)`

异步 WebSocket 客户端。构造参数与 `WebSocketClient` 相同。

| 方法 | 描述 |
|------|------|
| `await connect(*, timeout=30.0, verify=True)` | 打开 WebSocket 连接 |
| `await send(data: str)` | 发送文本消息 |
| `await recv(*, timeout=None) -> str` | 接收文本消息 |
| `await ping(data=b"")` | 发送 ping 帧 |
| `await close(code=1000, reason="")` | 关闭连接 |

---

### 异常

| 异常 | 描述 |
|------|------|
| `WebSocketError` | 所有 WebSocket 操作的基础异常 |
| `WebSocketConnectionError` | 连接失败（TCP 连接、握手拒绝、服务端关闭） |
| `WebSocketTimeoutError` | 操作超时 |
| `WebSocketProtocolError` | 协议违规（帧格式错误、不支持的操作码） |

---

### 常量

| 常量 | 值 | 描述 |
|------|------|------|
| `DEFAULT_TIMEOUT` | `30.0` | 所有操作的默认超时时间（秒） |

## 与 websockets 库对比

| 特性 | zerodep websocket | websockets |
|------|-------------------|------------|
| 依赖 | 无（仅标准库） | 无 |
| 同步客户端 | `WebSocketClient` | `websockets.sync.client.connect()` |
| 异步客户端 | `AsyncWebSocketClient` | `websockets.connect()` |
| 协议 | 仅文本帧 | 文本 + 二进制 + 续帧 |
| TLS 支持 | 是（`wss://`） | 是（`wss://`） |
| Ping/pong | 收到 ping 自动回复 pong | 收到 ping 自动回复 pong |
| 关闭握手 | 完整关闭帧交换 | 完整关闭帧交换 |
| 服务端支持 | 否 | 是 |
| 压缩 | 否 | permessage-deflate |
| 代码量 | ~1000 行 | ~10,000+ 行 |
| 安装方式 | 单文件复制 | pip install |

**适用场景 (zerodep)：** 需要轻量级 WebSocket 客户端，用于 CDP 通信、JSON-RPC 或简单消息交换，且不想引入第三方依赖。

**适用场景 (websockets)：** 需要完整功能的 WebSocket 服务端/客户端，支持二进制帧、压缩或高级协议扩展。

## 性能测试

对标 `websockets` 库，测试场景包括 JSON-RPC 往返 (~200B)、大 HTML 负载传输 (~50KB)、突发消息 (100 条) 和连接建立开销。

详见 [WebSocket 性能测试](../benchmarks/websocket.md)。
