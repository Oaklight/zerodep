# A2A

Google A2A（Agent-to-Agent）协议实现 -- 零依赖，仅标准库，Python 3.10+。

## 概述

A2A 模块提供了 Google [Agent-to-Agent 协议](https://github.com/a2aproject/A2A)（v1.0）的纯标准库实现，用于智能体之间的通信。涵盖基于 SSE 流的 JSON-RPC 2.0、HTTP 客户端、HTTP 服务端和内存任务存储。可作为 [`a2a-protocol`](https://pypi.org/project/a2a-protocol/) 的替代方案。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `a2a.py` | 完整 A2A 协议栈：数据类型、JSON-RPC、SSE、客户端、服务端、任务管理 | 无（仅标准库） |

提供六层功能：

1. **协议数据类型** -- A2A 规范数据模型的 dataclass 定义
2. **JSON-RPC 2.0 层** -- 请求 / 响应 / 错误 / 分发器
3. **SSE 工具** -- 服务端推送事件编码器和流解析器
4. **A2A 客户端** -- 基于 `urllib` 的客户端，支持 SSE 流
5. **A2A 服务端** -- 基于 `http.server` 的服务端，支持 SSE
6. **任务管理** -- 内存 `TaskStore` 和 `TaskManager`，含状态机

## 如何在你的项目中使用

只需将 `.py` 文件复制到你的项目中：

```bash
cp a2a/a2a.py your_project/
```

然后直接导入：

```python
from a2a import AgentCard, A2AClient, A2AServer, Task, Message
```

## API 参考

### 协议数据类型

任务、消息和产物的核心数据模型：

| 类 | 说明 |
|----|------|
| `TaskState` | 枚举：`SUBMITTED`、`WORKING`、`INPUT_REQUIRED`、`COMPLETED`、`CANCELED`、`FAILED`、`UNKNOWN` |
| `Role` | 枚举：`USER`、`AGENT` |
| `Part` | 内容部分（文本、文件或数据） |
| `Message` | 用户/智能体消息，包含多个 Part |
| `Artifact` | 输出产物，包含 Part 和元数据 |
| `TaskStatus` | 当前任务状态 + 可选消息 |
| `Task` | 完整任务，包含状态、产物和历史记录 |
| `TaskStatusUpdateEvent` | 状态变更的 SSE 事件 |
| `TaskArtifactUpdateEvent` | 产物更新的 SSE 事件 |

所有数据类型支持 `to_dict()` 和 `from_dict()` 进行 JSON 序列化：

```python
from a2a import Task, TaskStatus, TaskState

task = Task(
    id="task-1",
    status=TaskStatus(state=TaskState.COMPLETED),
    context_id="ctx-1",
)
wire = task.to_dict()       # 可直接用于 json.dumps() 的 dict
restored = Task.from_dict(wire)  # 从 dict 重建对象
```

---

### 智能体卡片

| 类 | 说明 |
|----|------|
| `AgentCard` | 智能体元数据：名称、描述、URL、能力、技能 |
| `AgentCapabilities` | 功能标志（流式、推送通知） |
| `AgentSkill` | 单个技能：名称、描述、输入/输出模式 |
| `AgentInterface` | 支持的协议接口 |
| `AgentProvider` | 组织元数据 |
| `AuthenticationInfo` | 认证方案 |

```python
from a2a import AgentCard, AgentCapabilities, AgentSkill

card = AgentCard(
    name="My Agent",
    description="A helpful agent",
    url="http://localhost:8080",
    version="1.0",
    capabilities=AgentCapabilities(streaming=True),
    skills=[AgentSkill(id="chat", name="Chat", description="General chat")],
)
```

---

### JSON-RPC 2.0

| 类 | 说明 |
|----|------|
| `JSONRPCRequest` | JSON-RPC 请求，包含 method、params、id |
| `JSONRPCResponse` | JSON-RPC 响应，包含 result 或 error |
| `JSONRPCError` | JSON-RPC 错误，包含 code、message、data |
| `JSONRPCDispatcher` | 方法分发器 |

---

### SSE 工具

| 函数 | 说明 |
|------|------|
| `sse_encode(data, *, event, id)` | 将 dict 编码为 SSE 事件字符串 |
| `sse_decode_stream(lines)` | 从行迭代器解码 SSE 流 |

---

### A2A 客户端

```python
from a2a import A2AClient

client = A2AClient(base_url="http://localhost:8080")

# 发送消息并获取任务
task = client.send_message("Hello, agent!")

# 流式发送消息
for event in client.send_message_streaming("Explain Python generators"):
    print(event)

# 获取任务状态
task = client.get_task("task-id")

# 取消任务
client.cancel_task("task-id")
```

---

### A2A 服务端

```python
from a2a import A2AServer, A2ARequestHandler

class MyHandler(A2ARequestHandler):
    def handle_send_message(self, request):
        # 处理消息并返回任务
        ...

    def handle_send_message_streaming(self, request):
        # 生成 SSE 事件
        ...

server = A2AServer(handler=MyHandler(), host="0.0.0.0", port=8080)
server.start()
```

---

### 任务管理

| 类 | 说明 |
|----|------|
| `TaskStore` | 线程安全的内存任务存储，支持 CRUD 操作 |
| `TaskManager` | 任务生命周期状态机 |

```python
from a2a import TaskStore, TaskManager

store = TaskStore()
manager = TaskManager(store)

task = manager.create_task(context_id="ctx-1")
manager.update_status(task.id, TaskState.WORKING, message="Processing...")
manager.add_artifact(task.id, artifact)
manager.complete(task.id)
```

---

### 错误类型

| 类 | 说明 |
|----|------|
| `A2AError` | 基础错误 |
| `TaskNotFoundError` | 任务不存在 |
| `TaskNotCancelableError` | 任务无法取消 |
| `PushNotificationNotSupportedError` | 不支持推送通知 |
| `UnsupportedOperationError` | 不支持的操作 |
| `ContentTypeNotSupportedError` | 不支持的内容类型 |
| `InvalidAgentResponseError` | 智能体响应无效 |

## 用法示例

### 简单客户端-服务端

```python
from a2a import A2AClient

# 连接到 A2A 兼容的智能体
client = A2AClient(base_url="http://localhost:8080")

# 获取智能体卡片
card = client.get_agent_card()
print(f"Agent: {card.name}")
print(f"Skills: {[s.name for s in card.skills]}")

# 发送消息
task = client.send_message("What is the capital of France?")
print(f"Status: {task.status.state}")
if task.artifacts:
    for part in task.artifacts[0].parts:
        print(part.text)
```

### 流式响应

```python
from a2a import A2AClient, TaskStatusUpdateEvent, TaskArtifactUpdateEvent

client = A2AClient(base_url="http://localhost:8080")

for event in client.send_message_streaming("Write a haiku about Python"):
    if isinstance(event, TaskStatusUpdateEvent):
        print(f"Status: {event.status.state}")
    elif isinstance(event, TaskArtifactUpdateEvent):
        for part in event.artifact.parts:
            print(part.text, end="")
```

### 数据序列化

```python
from a2a import Message, Part, Role
import json

msg = Message(
    message_id="msg-1",
    role=Role.USER,
    parts=[Part(text="Hello!")],
)

# 序列化为 JSON
wire = json.dumps(msg.to_dict())

# 反序列化
restored = Message.from_dict(json.loads(wire))
assert restored.parts[0].text == "Hello!"
```

## 注意事项

!!! info "协议版本"
    本实现面向 A2A 协议 v1.0，规范见 [a2a-protocol.org](https://a2a-protocol.org/specification)。

- **Python 版本：** 需要 Python 3.10+（使用了 `X | Y` 联合类型标注语法）。
- **服务端：** 内置服务端使用标准库的 `http.server`。生产环境建议使用专业的 WSGI/ASGI 服务器。
- **SSE 流：** 客户端和服务端均完整支持。
- **线程安全：** `TaskStore` 通过 `threading.Lock` 保证线程安全。

## 性能测试

与 `a2a-protocol` 在三种输入大小（小、中、大）下进行序列化、反序列化和 JSON 往返的对比测试。

详见 [A2A 性能测试](../benchmarks/a2a.md)。
