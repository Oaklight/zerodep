# CDP 客户端

零依赖的 Chrome DevTools Protocol 客户端，用于无头浏览器自动化 -- 同步 + 异步，仅标准库，Python 3.10+。

> **可替代:** `pychrome`、`pycdp`

## 概览

cdp 模块提供同步和异步 CDP 客户端，通过 WebSocket 与 Chrome/Chromium 内核浏览器通信。支持标签页管理、页面导航、JavaScript 执行和高级渲染内容提取。基于兄弟模块 `websocket` 构建。

| 文件 | 描述 | 依赖 |
|------|------|------|
| `cdp.py` | 纯 Python 实现 | `websocket` 模块（兄弟模块） |

## 特性

- **高级 API** -- `get_rendered_text()` 和 `get_rendered_html()` 一行代码提取渲染内容
- **低级 API** -- `send_command()` 发送任意 CDP 方法调用，自动命令/响应 ID 匹配
- **标签页管理** -- `create_target()`、`close_target()` 支持多标签页工作流
- **页面导航** -- `navigate()` 自动等待 `Page.loadEventFired` 事件
- **JavaScript 执行** -- `evaluate()` 支持浏览器异常错误传播
- **User-Agent 覆盖** -- `set_user_agent()` 按标签页设置
- **自动发现** -- 通过 `/json/version` 自动发现浏览器调试 WebSocket URL
- **事件缓冲** -- 等待命令响应时自动缓冲不匹配的事件
- **同步 + 异步客户端** -- `CDPClient` 和 `AsyncCDPClient`，API 完全一致
- **上下文管理器** -- `with` / `async with` 自动连接和清理

## 在项目中使用

复制两个文件到你的项目（cdp 依赖 websocket）：

```bash
zerodep add cdp
# 或手动：
cp websocket/websocket.py your_project/
cp cdp/cdp.py your_project/
```

然后直接导入：

```python
from cdp import CDPClient, AsyncCDPClient
```

## 使用示例

### 提取渲染文本（一行调用）

```python
from cdp import CDPClient

# 启动 Chrome: chrome --headless --remote-debugging-port=9222
with CDPClient("ws://localhost:9222") as client:
    text = client.get_rendered_text("https://react.dev", timeout=15)
    print(text)
```

### 提取渲染 HTML

```python
from cdp import CDPClient

with CDPClient("ws://localhost:9222") as client:
    html = client.get_rendered_html("https://example.com")
    print(html[:200])
```

### 低级标签页管理

```python
from cdp import CDPClient

with CDPClient("ws://localhost:9222") as client:
    target_id = client.create_target("https://example.com")
    client.navigate(target_id, "https://example.com")

    # 执行 JavaScript
    title = client.evaluate(target_id, "document.title")
    print(f"页面标题: {title}")

    html = client.evaluate(target_id, "document.documentElement.outerHTML")
    print(f"HTML 长度: {len(html)}")

    client.close_target(target_id)
```

### 多标签页工作流

```python
from cdp import CDPClient

with CDPClient("ws://localhost:9222") as client:
    urls = ["https://example.com", "https://httpbin.org", "https://google.com"]
    targets = []

    # 打开多个标签页
    for url in urls:
        tid = client.create_target()
        client.navigate(tid, url)
        targets.append(tid)

    # 从所有标签页提取内容
    for tid in targets:
        text = client.evaluate(tid, "document.body.innerText")
        print(f"标签页 {tid}: {len(text)} 字符")

    # 关闭所有标签页
    for tid in targets:
        client.close_target(tid)
```

### User-Agent 覆盖

```python
from cdp import CDPClient

with CDPClient("ws://localhost:9222") as client:
    target_id = client.create_target()
    client.set_user_agent(target_id, "MyBot/1.0")
    client.navigate(target_id, "https://httpbin.org/user-agent")
    result = client.evaluate(target_id, "document.body.innerText")
    print(result)
    client.close_target(target_id)
```

### 异步客户端

```python
import asyncio
from cdp import AsyncCDPClient

async def main():
    async with AsyncCDPClient("ws://localhost:9222") as client:
        text = await client.get_rendered_text("https://example.com")
        print(text)

asyncio.run(main())
```

### 通过 /json/version 自动发现

```python
from cdp import CDPClient

# 只需提供 host:port — 客户端自动发现 WebSocket URL
with CDPClient("ws://localhost:9222") as client:
    text = client.get_rendered_text("https://example.com")
```

## API 参考

### `CDPClient(url, *, timeout=30.0)`

同步 Chrome DevTools Protocol 客户端。

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `url` | `str` | -- | CDP WebSocket 端点 URL（如 `ws://localhost:9222`） |
| `timeout` | `float` | `30.0` | CDP 命令的默认超时时间 |

**连接方法：**

| 方法 | 描述 |
|------|------|
| `connect(*, timeout=None)` | 打开到 CDP 端点的 WebSocket 连接 |
| `close()` | 关闭所有标签页和 WebSocket 连接 |

**高级方法：**

| 方法 | 描述 |
|------|------|
| `get_rendered_text(url, *, timeout=None) -> str` | 导航并提取 `document.body.innerText` |
| `get_rendered_html(url, *, timeout=None) -> str` | 导航并提取 `document.documentElement.outerHTML` |

**标签页管理：**

| 方法 | 描述 |
|------|------|
| `create_target(url="about:blank") -> str` | 创建并附加到新浏览器标签页，返回 target ID |
| `close_target(target_id)` | 关闭浏览器标签页 |
| `navigate(target_id, url, *, timeout=None)` | 将标签页导航到 URL 并等待页面加载 |
| `wait_for_load(target_id, *, timeout=None)` | 等待标签页页面加载完成 |

**执行与配置：**

| 方法 | 描述 |
|------|------|
| `evaluate(target_id, expression) -> object` | 在标签页中执行 JavaScript |
| `set_user_agent(target_id, user_agent)` | 覆盖标签页的 User-Agent |
| `send_command(method, params=None, *, session_id=None, timeout=None) -> dict` | 发送原始 CDP 命令 |

---

### `AsyncCDPClient(url, *, timeout=30.0)`

异步 Chrome DevTools Protocol 客户端。构造参数与 `CDPClient` 相同。所有方法均为 `async`。

---

### 异常

| 异常 | 描述 |
|------|------|
| `CDPError` | 所有 CDP 操作的基础异常 |
| `CDPConnectionError` | 到 CDP 端点的 WebSocket 连接失败 |
| `CDPTimeoutError` | CDP 操作超时 |
| `CDPProtocolError` | 浏览器返回的 CDP 错误响应 |

---

### 常量

| 常量 | 值 | 描述 |
|------|------|------|
| `DEFAULT_TIMEOUT` | `30.0` | 默认命令超时时间（秒） |
| `DEFAULT_PAGE_LOAD_TIMEOUT` | `30.0` | 默认页面加载超时时间（秒） |

## 与 websockets + 手动 CDP 对比

| 特性 | zerodep cdp | websockets + 手动实现 |
|------|-------------|----------------------|
| 依赖 | 无（仅标准库） | websockets（pip） |
| 高级 API | `get_rendered_text()` | 需手动编排命令序列 |
| 标签页管理 | 内置 `create_target()` / `close_target()` | 需手动发送 Target 域命令 |
| 事件缓冲 | 自动 | 需自行实现 |
| ID 匹配 | 自动命令/响应关联 | 需自行跟踪 ID |
| 自动发现 | `/json/version` 自动探测 | 需手动查找端点 |
| 同步 + 异步 | 两者均内置 | websockets 仅异步（同步包装器） |
| 代码量 | ~900 行 + websocket 模块 | 视情况而定 |

**适用场景 (zerodep cdp)：** 需要从 SPA 提取渲染内容、自动化浏览器任务或与 CDP 兼容浏览器通信，且不想引入 Selenium/Playwright 依赖。

**适用场景 (Playwright/Selenium)：** 需要跨浏览器测试、复杂用户交互模拟或成熟的生态系统。

## 性能测试

对标 mock CDP 服务器，测试场景包括完整渲染管线（创建 → 导航 → 执行 → 关闭）、多标签页场景、JavaScript 执行吞吐和命令吞吐。

详见 [CDP 性能测试](../benchmarks/cdp.md)。
