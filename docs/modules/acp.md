# ACP

Anthropic ACP（Agent Client Protocol）协议实现 -- 零依赖，仅标准库，Python 3.10+。

> **可替代:** `acp-python`

## 概述

ACP 模块提供了 Anthropic [Agent Client Protocol](https://github.com/anthropics/acp) 的纯标准库实现，用于代码编辑器（Client）和 AI 编程智能体（Agent）之间的通信。使用基于 stdio 的 JSON-RPC 2.0（换行分隔 JSON），类似于 LSP 标准化语言服务器集成的方式。可作为 [`agent-client-protocol`](https://pypi.org/project/agent-client-protocol/) 的替代方案。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `acp.py` | 完整 ACP 协议栈：传输层、数据类型、客户端、智能体框架 | 无（仅标准库） |

提供四层功能：

1. **JsonRpcTransport** -- 基于 `asyncio` 流的异步换行分隔 JSON-RPC 2.0 消息读写
2. **协议数据类型** -- ACP 规范中所有消息和结构的 dataclass 定义（协议版本 1）
3. **ACPClient** -- 高级异步客户端：启动智能体子进程、执行握手、创建会话、流式更新
4. **ACPAgent** -- 抽象基类，用于实现 ACP 兼容的智能体

## 如何在你的项目中使用

只需将 `.py` 文件复制到你的项目中：

```bash
cp acp/acp.py your_project/
```

然后直接导入：

```python
from acp import ACPClient, ACPAgent, TextContent, PromptParams
```

## API 参考

### 传输层

| 类 | 说明 |
|----|------|
| `JsonRpcTransport` | 基于换行分隔 stdio 流的异步 JSON-RPC 2.0 传输 |

```python
from acp import JsonRpcTransport

transport = JsonRpcTransport(reader, writer)
await transport.send_request("initialize", params={...})
message = await transport.read_message()
```

---

### 协议数据类型

内容块：

| 类 | 说明 |
|----|------|
| `TextContent` | 纯文本内容 |
| `ImageContent` | Base64 编码的图片 |
| `AudioContent` | Base64 编码的音频 |
| `ResourceContent` | 带 URI 的文件内容 |
| `ResourceLinkContent` | 资源的 URI 引用 |

会话和初始化：

| 类 | 说明 |
|----|------|
| `InitializeParams` | 握手时的客户端能力和信息 |
| `InitializeResult` | 握手返回的智能体能力和信息 |
| `NewSessionParams` | 创建新会话的参数 |
| `NewSessionResult` | 会话 ID 和元数据 |
| `PromptParams` | 包含内容块的提示 |
| `PromptResult` | 提示完成结果 |

更新事件（通过 `session/update` 流式传输）：

| 类 | 说明 |
|----|------|
| `AgentMessageChunkUpdate` | 智能体的流式文本 |
| `UserMessageChunkUpdate` | 回显的用户内容 |
| `ThoughtMessageChunkUpdate` | 内部推理 / 思维链 |
| `ToolCallUpdate` | 工具调用进度 |
| `ToolCallStatusUpdate` | 工具调用状态变更 |
| `PlanUpdate` | 计划条目更新 |
| `AvailableCommandsUpdate` | 可用斜杠命令 |
| `CurrentModeUpdate` | 会话模式变更 |
| `ConfigOptionUpdate` | 配置选项变更 |
| `SessionInfoUpdate` | 会话元数据更新 |

所有数据类型支持 `to_dict()` / `from_raw()` 进行 JSON 序列化：

```python
from acp import TextContent, to_dict, from_raw

content = TextContent(text="Hello!")
wire = to_dict(content)           # 带 camelCase 键的 dict
restored = from_raw(wire)         # 从 dict 重建对象
```

---

### ACPClient

高级异步客户端，用于驱动 ACP 智能体子进程：

```python
import asyncio
from acp import ACPClient

async def main():
    client = ACPClient(["python", "-m", "my_agent"])
    await client.start()

    # 初始化握手
    init = await client.initialize()
    print(f"Agent: {init.agent_info.name}")

    # 创建会话
    session = await client.new_session("/home/user/project")

    # 发送提示并流式接收更新
    async for update in client.prompt(session.session_id, "Hello!"):
        print(update)

    await client.stop()

asyncio.run(main())
```

---

### ACPAgent

用于实现 ACP 智能体的抽象基类：

```python
from acp import ACPAgent, TextContent

class MyAgent(ACPAgent):
    async def on_initialize(self, params):
        return InitializeResult(
            protocol_version=1,
            agent_capabilities=AgentCapabilities(),
            agent_info=ImplementationInfo(name="my-agent", version="1.0"),
        )

    async def on_new_session(self, params):
        return NewSessionResult(session_id="sess-1")

    async def on_prompt(self, params):
        # 发送流式更新
        await self.emit_update(params.session_id,
            AgentMessageChunkUpdate(message_id="msg-1",
                delta=TextContent(text="Hello back!")))
        return PromptResult()

if __name__ == "__main__":
    MyAgent().run()
```

---

### 枚举

| 枚举 | 值 |
|------|-----|
| `StopReason` | `END_TURN`、`MAX_TOKENS`、`STOP_SEQUENCE`、`TOOL_USE` |
| `ToolKind` | `READ`、`EDIT`、`EXECUTE`、`BROWSER`、`MCP`、`COMPUTER_USE` |
| `ToolCallStatus` | `PENDING`、`IN_PROGRESS`、`COMPLETED`、`FAILED`、`CANCELLED` |
| `SessionMode` | `PLAN`、`AGENT`、`EDIT`（等） |

---

### 错误处理

| 类 | 说明 |
|----|------|
| `JsonRpcError` | JSON-RPC 错误，包含 code 和 data |
| `JsonRpcErrorData` | 结构化错误数据 |

## 用法示例

### 客户端：发送提示

```python
import asyncio
from acp import ACPClient

async def main():
    async with ACPClient(["python", "my_agent.py"]) as client:
        init = await client.initialize()
        session = await client.new_session("/path/to/project")

        async for update in client.prompt(session.session_id,
                "Explain the main function"):
            if hasattr(update, 'delta') and hasattr(update.delta, 'text'):
                print(update.delta.text, end="")

asyncio.run(main())
```

### 智能体：处理提示

```python
from acp import (
    ACPAgent, AgentCapabilities, ImplementationInfo,
    InitializeResult, NewSessionResult, PromptResult,
    AgentMessageChunkUpdate, TextContent,
)

class EchoAgent(ACPAgent):
    async def on_initialize(self, params):
        return InitializeResult(
            protocol_version=1,
            agent_capabilities=AgentCapabilities(),
            agent_info=ImplementationInfo(name="echo", version="0.1"),
        )

    async def on_new_session(self, params):
        return NewSessionResult(session_id="s1")

    async def on_prompt(self, params):
        text = params.prompt[0].text if params.prompt else ""
        await self.emit_update(params.session_id,
            AgentMessageChunkUpdate(
                message_id="m1",
                delta=TextContent(text=f"Echo: {text}"),
            ))
        return PromptResult()

if __name__ == "__main__":
    EchoAgent().run()
```

## 注意事项

!!! info "协议版本"
    本实现面向 ACP 协议版本 1，规范见 [ACP specification](https://github.com/anthropics/acp)。

- **Python 版本：** 需要 Python 3.10+（使用了 `X | Y` 联合类型标注语法）。
- **传输方式：** 使用基于 stdio（stdin/stdout）的换行分隔 JSON，类似 LSP。
- **纯异步：** `ACPClient` 和 `ACPAgent` 均为完全异步（`asyncio`）。
- **线上格式：** 字段名自动在 `snake_case`（Python）和 `camelCase`（线上格式）之间转换。

## 性能测试

与 `agent-client-protocol`（基于 Pydantic）在三种输入大小（小、中、大）下进行序列化、反序列化和 JSON 往返的对比测试。

详见 [ACP 性能测试](../benchmarks/acp.md)。
