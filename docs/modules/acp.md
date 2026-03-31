# ACP

Anthropic ACP (Agent Client Protocol) implementation -- zero dependencies, stdlib only, Python 3.10+.

## Overview

The ACP module provides a pure-stdlib implementation of Anthropic's [Agent Client Protocol](https://github.com/anthropics/acp) for communication between code editors (Clients) and AI coding agents (Agents). It uses JSON-RPC 2.0 over stdio, similar to how LSP standardized language-server integration. It can serve as a drop-in alternative to [`agent-client-protocol`](https://pypi.org/project/agent-client-protocol/).

| File | Description | Dependencies |
|------|-------------|--------------|
| `acp.py` | Full ACP protocol stack: transport, data types, client, agent framework | None (stdlib only) |

Four layers are provided:

1. **JsonRpcTransport** -- async read/write of newline-delimited JSON-RPC 2.0 messages over `asyncio` streams
2. **Protocol Data Types** -- dataclass representations of every ACP message and structure (protocol version 1)
3. **ACPClient** -- high-level async client that spawns an agent subprocess, performs handshake, and streams updates
4. **ACPAgent** -- abstract base class for implementing ACP-compatible agents

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp acp/acp.py your_project/
```

Then import directly:

```python
from acp import ACPClient, ACPAgent, TextContent, PromptParams
```

## API Reference

### Transport

| Class | Description |
|-------|-------------|
| `JsonRpcTransport` | Async JSON-RPC 2.0 over newline-delimited stdio streams |

```python
from acp import JsonRpcTransport

transport = JsonRpcTransport(reader, writer)
await transport.send_request("initialize", params={...})
message = await transport.read_message()
```

---

### Protocol Data Types

Content blocks:

| Class | Description |
|-------|-------------|
| `TextContent` | Plain text content |
| `ImageContent` | Base64-encoded image |
| `AudioContent` | Base64-encoded audio |
| `ResourceContent` | File content with URI |
| `ResourceLinkContent` | URI reference to a resource |

Session and initialization:

| Class | Description |
|-------|-------------|
| `InitializeParams` | Client capabilities and info for handshake |
| `InitializeResult` | Agent capabilities and info from handshake |
| `NewSessionParams` | Parameters for creating a new session |
| `NewSessionResult` | Session ID and metadata |
| `PromptParams` | Prompt with content blocks |
| `PromptResult` | Prompt completion result |

Update events (streamed via `session/update`):

| Class | Description |
|-------|-------------|
| `AgentMessageChunkUpdate` | Streaming text from agent |
| `UserMessageChunkUpdate` | Echoed user content |
| `ThoughtMessageChunkUpdate` | Internal reasoning / chain-of-thought |
| `ToolCallUpdate` | Tool invocation progress |
| `ToolCallStatusUpdate` | Tool call status changes |
| `PlanUpdate` | Plan entries update |
| `AvailableCommandsUpdate` | Available slash commands |
| `CurrentModeUpdate` | Session mode change |
| `ConfigOptionUpdate` | Configuration option change |
| `SessionInfoUpdate` | Session metadata update |

All data types support `to_dict()` / `from_raw()` for JSON serialization:

```python
from acp import TextContent, to_dict, from_raw

content = TextContent(text="Hello!")
wire = to_dict(content)           # dict with camelCase keys
restored = from_raw(wire)         # reconstruct from dict
```

---

### ACPClient

High-level async client for driving an ACP agent subprocess:

```python
import asyncio
from acp import ACPClient

async def main():
    client = ACPClient(["python", "-m", "my_agent"])
    await client.start()

    # Initialize handshake
    init = await client.initialize()
    print(f"Agent: {init.agent_info.name}")

    # Create a session
    session = await client.new_session("/home/user/project")

    # Send a prompt and stream updates
    async for update in client.prompt(session.session_id, "Hello!"):
        print(update)

    await client.stop()

asyncio.run(main())
```

---

### ACPAgent

Abstract base class for implementing an ACP agent:

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
        # Emit streaming updates
        await self.emit_update(params.session_id,
            AgentMessageChunkUpdate(message_id="msg-1",
                delta=TextContent(text="Hello back!")))
        return PromptResult()

if __name__ == "__main__":
    MyAgent().run()
```

---

### Enums

| Enum | Values |
|------|--------|
| `StopReason` | `END_TURN`, `MAX_TOKENS`, `STOP_SEQUENCE`, `TOOL_USE` |
| `ToolKind` | `READ`, `EDIT`, `EXECUTE`, `BROWSER`, `MCP`, `COMPUTER_USE` |
| `ToolCallStatus` | `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, `CANCELLED` |
| `SessionMode` | `PLAN`, `AGENT`, `EDIT` (and more) |

---

### Error Handling

| Class | Description |
|-------|-------------|
| `JsonRpcError` | JSON-RPC error with code and data |
| `JsonRpcErrorData` | Structured error data |

## Usage Examples

### Client: Send a Prompt

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

### Agent: Handle Prompts

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

## Notes and Caveats

!!! info "Protocol Version"
    This implementation targets ACP protocol version 1, as specified in the [ACP specification](https://github.com/anthropics/acp).

- **Python version:** Requires Python 3.10+ (uses `X | Y` union type hint syntax).
- **Transport:** Uses newline-delimited JSON over stdio (stdin/stdout), like LSP.
- **Async only:** Both `ACPClient` and `ACPAgent` are fully async (`asyncio`).
- **Wire format:** All field names are automatically converted between `snake_case` (Python) and `camelCase` (wire format).

## Benchmark

Benchmarked against `agent-client-protocol` (Pydantic-based) across three input sizes (small, medium, large) for serialization, deserialization, and JSON round-trip operations.

See [ACP Benchmark](../benchmarks/acp.md) for detailed results.
