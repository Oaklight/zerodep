# A2A

Google A2A (Agent-to-Agent) protocol implementation -- zero dependencies, stdlib only, Python 3.10+.

## Overview

The A2A module provides a pure-stdlib implementation of Google's [Agent-to-Agent Protocol](https://github.com/a2aproject/A2A) (v1.0) for agent-to-agent communication. It covers JSON-RPC 2.0 with SSE streaming, an HTTP client, an HTTP server, and an in-memory task store. It can serve as a drop-in alternative to [`a2a-protocol`](https://pypi.org/project/a2a-protocol/).

| File | Description | Dependencies |
|------|-------------|--------------|
| `a2a.py` | Full A2A protocol stack: data types, JSON-RPC, SSE, client, server, task management | None (stdlib only) |

Six layers are provided:

1. **Protocol Data Types** -- dataclass models for the canonical A2A data model
2. **JSON-RPC 2.0 Layer** -- request / response / error / dispatcher
3. **SSE Utilities** -- server-sent events encoder and stream parser
4. **A2A Client** -- `urllib`-based client with SSE streaming support
5. **A2A Server** -- `http.server`-based server with SSE support
6. **Task Management** -- in-memory `TaskStore` and `TaskManager` with state machine

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp a2a/a2a.py your_project/
```

Then import directly:

```python
from a2a import AgentCard, A2AClient, A2AServer, Task, Message
```

## API Reference

### Protocol Data Types

Core data model types for tasks, messages, and artifacts:

| Class | Description |
|-------|-------------|
| `TaskState` | Enum: `SUBMITTED`, `WORKING`, `INPUT_REQUIRED`, `COMPLETED`, `CANCELED`, `FAILED`, `UNKNOWN` |
| `Role` | Enum: `USER`, `AGENT` |
| `Part` | Content part (text, file, or data) |
| `Message` | User/agent message with parts |
| `Artifact` | Output artifact with parts and metadata |
| `TaskStatus` | Current task state + optional message |
| `Task` | Full task with status, artifacts, and history |
| `TaskStatusUpdateEvent` | SSE event for status changes |
| `TaskArtifactUpdateEvent` | SSE event for artifact updates |

All data types support `to_dict()` and `from_dict()` for JSON serialization:

```python
from a2a import Task, TaskStatus, TaskState

task = Task(
    id="task-1",
    status=TaskStatus(state=TaskState.COMPLETED),
    context_id="ctx-1",
)
wire = task.to_dict()       # dict ready for json.dumps()
restored = Task.from_dict(wire)  # reconstruct from dict
```

---

### Agent Card

| Class | Description |
|-------|-------------|
| `AgentCard` | Agent metadata: name, description, URL, capabilities, skills |
| `AgentCapabilities` | Feature flags (streaming, push notifications) |
| `AgentSkill` | Individual skill with name, description, input/output modes |
| `AgentInterface` | Supported protocol interface |
| `AgentProvider` | Organization metadata |
| `AuthenticationInfo` | Authentication schemes |

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

| Class | Description |
|-------|-------------|
| `JSONRPCRequest` | JSON-RPC request with method, params, id |
| `JSONRPCResponse` | JSON-RPC response with result or error |
| `JSONRPCError` | JSON-RPC error with code, message, data |
| `JSONRPCDispatcher` | Method dispatcher for handling requests |

---

### SSE Utilities

| Function | Description |
|----------|-------------|
| `sse_encode(data, *, event, id)` | Encode a dict as an SSE event string |
| `sse_decode_stream(lines)` | Decode an SSE stream from an iterable of lines |

---

### A2A Client

```python
from a2a import A2AClient

client = A2AClient(base_url="http://localhost:8080")

# Send a message and get a task
task = client.send_message("Hello, agent!")

# Send a message with streaming
for event in client.send_message_streaming("Explain Python generators"):
    print(event)

# Get task status
task = client.get_task("task-id")

# Cancel a task
client.cancel_task("task-id")
```

---

### A2A Server

```python
from a2a import A2AServer, A2ARequestHandler

class MyHandler(A2ARequestHandler):
    def handle_send_message(self, request):
        # Process message and return task
        ...

    def handle_send_message_streaming(self, request):
        # Yield SSE events
        ...

server = A2AServer(handler=MyHandler(), host="0.0.0.0", port=8080)
server.start()
```

---

### Task Management

| Class | Description |
|-------|-------------|
| `TaskStore` | Thread-safe in-memory task storage with CRUD operations |
| `TaskManager` | State machine for task lifecycle management |

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

### Error Types

| Class | Description |
|-------|-------------|
| `A2AError` | Base error |
| `TaskNotFoundError` | Task does not exist |
| `TaskNotCancelableError` | Task cannot be canceled |
| `PushNotificationNotSupportedError` | Push notifications not supported |
| `UnsupportedOperationError` | Operation not supported |
| `ContentTypeNotSupportedError` | Content type not supported |
| `InvalidAgentResponseError` | Invalid response from agent |

## Usage Examples

### Simple Client-Server

```python
from a2a import A2AClient

# Connect to an A2A-compatible agent
client = A2AClient(base_url="http://localhost:8080")

# Fetch the agent card
card = client.get_agent_card()
print(f"Agent: {card.name}")
print(f"Skills: {[s.name for s in card.skills]}")

# Send a message
task = client.send_message("What is the capital of France?")
print(f"Status: {task.status.state}")
if task.artifacts:
    for part in task.artifacts[0].parts:
        print(part.text)
```

### Streaming Response

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

### Data Serialization

```python
from a2a import Message, Part, Role
import json

msg = Message(
    message_id="msg-1",
    role=Role.USER,
    parts=[Part(text="Hello!")],
)

# Serialize to JSON
wire = json.dumps(msg.to_dict())

# Deserialize back
restored = Message.from_dict(json.loads(wire))
assert restored.parts[0].text == "Hello!"
```

## Notes and Caveats

!!! info "Protocol Version"
    This implementation targets A2A protocol v1.0 as specified at [a2a-protocol.org](https://a2a-protocol.org/specification).

- **Python version:** Requires Python 3.10+ (uses `X | Y` union type hint syntax).
- **Server:** The built-in server uses `http.server` from stdlib. For production, consider fronting it with a production-grade WSGI/ASGI server.
- **SSE streaming:** Fully supported for both client and server sides.
- **Thread safety:** `TaskStore` is thread-safe via `threading.Lock`.

## Benchmark

Benchmarked against `a2a-protocol` across three input sizes (small, medium, large) for serialization, deserialization, and JSON round-trip operations.

See [A2A Benchmark](../benchmarks/a2a.md) for detailed results.
