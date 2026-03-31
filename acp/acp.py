# /// zerodep
# version = "0.2.2"
# deps = ["jsonrpc"]
# tier = "subsystem"
# category = "network"
# ///

"""ACP (Agent Client Protocol) -- Zero-dependency Python implementation.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

The Agent Client Protocol standardizes communication between code editors
(Clients) and AI coding agents (Agents).  It uses JSON-RPC 2.0 over stdio
(newline-delimited JSON), similar to how the Language Server Protocol (LSP)
standardized language-server integration.

This single-file module provides:

* **JSONRPCTransport** -- async read/write of newline-delimited JSON-RPC 2.0
  messages over arbitrary ``asyncio.StreamReader`` / ``asyncio.StreamWriter``
  pairs (typically stdin/stdout of a subprocess).

* **Protocol data types** -- pure-dataclass representations of every message
  and structure defined by the ACP specification (protocol version 1).

* **ACPClient** -- high-level async helper that spawns an agent subprocess,
  performs the ``initialize`` handshake, creates sessions, sends prompts, and
  yields ``session/update`` notifications as an async iterator.

* **ACPAgent** -- abstract base class for implementing an ACP-compatible agent.
  Subclass it and override the ``on_*`` handler methods; call ``agent.run()``
  to start the stdio event loop.

Requires Python >= 3.10.  No third-party packages are needed -- only the
standard library (``asyncio``, ``json``, ``dataclasses``, ``enum``, ``typing``,
``sys``, ``abc``, ``uuid``, ``logging``).

Quickstart -- Client side::

    async def main():
        client = ACPClient(["python", "-m", "my_agent"])
        await client.start()
        init = await client.initialize()
        session = await client.new_session("/home/user/project")
        async for update in client.prompt(session.session_id, "Hello!"):
            print(update)
        await client.stop()

Quickstart -- Agent side::

    class EchoAgent(ACPAgent):
        async def on_initialize(self, params):
            return InitializeResult(protocol_version=1)

        async def on_new_session(self, params):
            return NewSessionResult(session_id="sess_1")

        async def on_prompt(self, params):
            text = ""
            for block in params.prompt:
                if isinstance(block, TextContent):
                    text = block.text
            await self.send_update(params.session_id,
                AgentMessageChunkUpdate(
                    content=TextContent(text=f"Echo: {text}")))
            return PromptResult(stop_reason=StopReason.END_TURN)

    if __name__ == "__main__":
        asyncio.run(EchoAgent().run())
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import sys
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Optional,
    Union,
)


def _ensure_sibling_path(name: str) -> str:
    """Return the sibling module directory and prepend it to ``sys.path``."""
    sibling_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", name)
    if sibling_dir not in sys.path:
        sys.path.insert(0, sibling_dir)
    return sibling_dir


_ensure_sibling_path("jsonrpc")
from jsonrpc import (  # noqa: E402
    INTERNAL_ERROR,
    METHOD_NOT_FOUND,
    JSONRPCError,
    JSONRPCException,
    JSONRPCTransport,
)

__all__ = [
    # JSON-RPC (re-exported from jsonrpc module)
    "JSONRPCTransport",
    "JSONRPCException",
    "JSONRPCError",
    # Enums
    "StopReason",
    "ToolKind",
    "ToolCallStatus",
    "PermissionOptionKind",
    "PlanEntryPriority",
    "PlanEntryStatus",
    # Content blocks
    "TextContent",
    "ImageContent",
    "AudioContent",
    "ResourceContent",
    "ResourceLinkContent",
    # Protocol types
    "ImplementationInfo",
    "FsCapabilities",
    "ClientCapabilities",
    "PromptCapabilities",
    "McpCapabilities",
    "SessionCapabilities",
    "AgentCapabilities",
    "AuthMethod",
    "InitializeParams",
    "InitializeResult",
    "EnvVariable",
    "McpServerStdio",
    "McpServerHttp",
    "HttpHeader",
    "NewSessionParams",
    "NewSessionResult",
    "LoadSessionParams",
    "PromptParams",
    "PromptResult",
    "CancelParams",
    "SessionMode",
    "SessionModeState",
    "SetModeParams",
    "ConfigOptionValue",
    "ConfigOption",
    "SetConfigOptionParams",
    "SetConfigOptionResult",
    "ListSessionsParams",
    "SessionInfo",
    "ListSessionsResult",
    "ToolCallLocation",
    "ToolCallContentItem",
    "DiffContent",
    "TerminalContent",
    "PermissionOption",
    "RequestPermissionParams",
    "RequestPermissionResult",
    "PermissionOutcome",
    "PlanEntry",
    "AvailableCommandInput",
    "AvailableCommand",
    # Session updates
    "AgentMessageChunkUpdate",
    "UserMessageChunkUpdate",
    "ThoughtMessageChunkUpdate",
    "ToolCallUpdate",
    "ToolCallStatusUpdate",
    "PlanUpdate",
    "AvailableCommandsUpdate",
    "CurrentModeUpdate",
    "ConfigOptionUpdate",
    "SessionInfoUpdate",
    # File system
    "ReadTextFileParams",
    "ReadTextFileResult",
    "WriteTextFileParams",
    # Terminal
    "CreateTerminalParams",
    "CreateTerminalResult",
    "TerminalOutputParams",
    "TerminalOutputResult",
    "TerminalExitStatus",
    "WaitForExitParams",
    "KillTerminalParams",
    "ReleaseTerminalParams",
    # Client / Agent
    "ACPClient",
    "ACPAgent",
]

__version__ = "0.2.2"

logger = logging.getLogger("acp")

# ---------------------------------------------------------------------------
# Helper: dataclass <-> dict conversion
# ---------------------------------------------------------------------------

_CAMEL_RE = re.compile(r"(?<=[a-z0-9])([A-Z])")


def _to_camel(name: str) -> str:
    """Convert a snake_case name to camelCase."""
    parts = name.split("_")
    return parts[0] + "".join(w.capitalize() for w in parts[1:])


def _to_snake(name: str) -> str:
    """Convert a camelCase name to snake_case."""
    return _CAMEL_RE.sub(r"_\1", name).lower()


def to_dict(obj: Any) -> Any:
    """Recursively convert a dataclass instance to a JSON-friendly dict.

    * ``None`` values and empty collections are omitted.
    * Snake-case field names are converted to camelCase per the ACP spec.
    * Enum values are serialized as their ``.value``.

    Args:
        obj: A dataclass instance, dict, list, or primitive.

    Returns:
        A JSON-serializable value.
    """
    if obj is None:
        return None
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, (list, tuple)):
        return [to_dict(v) for v in obj]
    if hasattr(obj, "__dataclass_fields__"):
        result: dict[str, Any] = {}
        for f in fields(obj):
            val = getattr(obj, f.name)
            if val is None:
                continue
            if isinstance(val, (list, tuple)) and len(val) == 0:
                continue
            if isinstance(val, dict) and len(val) == 0:
                continue
            result[_to_camel(f.name)] = to_dict(val)
        return result
    return obj


def from_raw(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert camelCase keys in *raw* to snake_case.

    Args:
        raw: A dictionary with camelCase keys.

    Returns:
        A new dictionary with snake_case keys.
    """
    return {_to_snake(k): v for k, v in raw.items()}


def _enum_from_value(enum_cls: type[Enum], value: Any) -> Any:
    """Look up an enum member by its *value* string."""
    if isinstance(value, enum_cls):
        return value
    for member in enum_cls:
        if member.value == value:
            return member
    raise ValueError(f"Unknown {enum_cls.__name__} value: {value!r}")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class StopReason(str, Enum):
    """Reason an agent stopped a prompt turn."""

    END_TURN = "end_turn"
    MAX_TOKENS = "max_tokens"
    MAX_TURN_REQUESTS = "max_turn_requests"
    REFUSAL = "refusal"
    CANCELLED = "cancelled"


class ToolKind(str, Enum):
    """Category of a tool being invoked."""

    READ = "read"
    EDIT = "edit"
    DELETE = "delete"
    MOVE = "move"
    SEARCH = "search"
    EXECUTE = "execute"
    THINK = "think"
    FETCH = "fetch"
    OTHER = "other"


class ToolCallStatus(str, Enum):
    """Execution status of a tool call."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class PermissionOptionKind(str, Enum):
    """Kind of permission option presented to the user."""

    ALLOW_ONCE = "allow_once"
    ALLOW_ALWAYS = "allow_always"
    REJECT_ONCE = "reject_once"
    REJECT_ALWAYS = "reject_always"


class PlanEntryPriority(str, Enum):
    """Priority of a plan entry."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PlanEntryStatus(str, Enum):
    """Execution status of a plan entry."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# ---------------------------------------------------------------------------
# Content blocks (shared with MCP)
# ---------------------------------------------------------------------------


@dataclass
class TextContent:
    """Plain text content block.

    Attributes:
        text: The text payload.
        type: Discriminator (always ``"text"``).
    """

    text: str
    type: str = "text"


@dataclass
class ImageContent:
    """Base64-encoded image content block.

    Attributes:
        data: Base64-encoded image data.
        mime_type: MIME type such as ``"image/png"``.
        type: Discriminator (always ``"image"``).
    """

    data: str
    mime_type: str
    type: str = "image"


@dataclass
class AudioContent:
    """Base64-encoded audio content block.

    Attributes:
        data: Base64-encoded audio data.
        mime_type: MIME type such as ``"audio/wav"``.
        type: Discriminator (always ``"audio"``).
    """

    data: str
    mime_type: str
    type: str = "audio"


@dataclass
class _TextResource:
    """Embedded text resource."""

    uri: str
    text: str
    mime_type: Optional[str] = None


@dataclass
class ResourceContent:
    """Embedded resource content block.

    Attributes:
        resource: The embedded resource (text or blob).
        type: Discriminator (always ``"resource"``).
    """

    resource: _TextResource
    type: str = "resource"


@dataclass
class ResourceLinkContent:
    """Reference to an external resource.

    Attributes:
        uri: URI of the resource.
        name: Human-readable resource name.
        mime_type: Optional MIME type.
        title: Optional display title.
        description: Optional description.
        size: Optional size in bytes.
        type: Discriminator (always ``"resource_link"``).
    """

    uri: str
    name: str
    mime_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    size: Optional[int] = None
    type: str = "resource_link"


ContentBlock = Union[
    TextContent,
    ImageContent,
    AudioContent,
    ResourceContent,
    ResourceLinkContent,
]


def _content_from_dict(raw: dict[str, Any]) -> ContentBlock:
    """Deserialize a content block from a raw dictionary."""
    t = raw.get("type", "text")
    if t == "text":
        return TextContent(text=raw["text"])
    if t == "image":
        return ImageContent(data=raw["data"], mime_type=raw["mimeType"])
    if t == "audio":
        return AudioContent(data=raw["data"], mime_type=raw["mimeType"])
    if t == "resource":
        res = raw["resource"]
        return ResourceContent(
            resource=_TextResource(
                uri=res["uri"],
                text=res.get("text", ""),
                mime_type=res.get("mimeType"),
            )
        )
    if t == "resource_link":
        return ResourceLinkContent(
            uri=raw["uri"],
            name=raw["name"],
            mime_type=raw.get("mimeType"),
            title=raw.get("title"),
            description=raw.get("description"),
            size=raw.get("size"),
        )
    # Fallback -- treat unknown as text
    return TextContent(text=str(raw))


# ---------------------------------------------------------------------------
# Protocol types -- initialization
# ---------------------------------------------------------------------------


@dataclass
class ImplementationInfo:
    """Information about a client or agent implementation.

    Attributes:
        name: Programmatic identifier.
        version: Version string.
        title: Human-readable display name.
    """

    name: str
    version: str = ""
    title: Optional[str] = None


@dataclass
class FsCapabilities:
    """Client file-system capabilities.

    Attributes:
        read_text_file: Whether ``fs/read_text_file`` is available.
        write_text_file: Whether ``fs/write_text_file`` is available.
    """

    read_text_file: bool = False
    write_text_file: bool = False


@dataclass
class ClientCapabilities:
    """Capabilities supported by the client.

    Attributes:
        fs: File-system method availability.
        terminal: Whether all ``terminal/*`` methods are available.
    """

    fs: Optional[FsCapabilities] = None
    terminal: bool = False


@dataclass
class PromptCapabilities:
    """Content types the agent supports in prompts.

    Attributes:
        image: Whether image content is supported.
        audio: Whether audio content is supported.
        embedded_context: Whether embedded resource content is supported.
    """

    image: bool = False
    audio: bool = False
    embedded_context: bool = False


@dataclass
class McpCapabilities:
    """MCP transport capabilities.

    Attributes:
        http: Whether HTTP MCP transport is supported.
        sse: Whether SSE MCP transport is supported.
    """

    http: bool = False
    sse: bool = False


@dataclass
class SessionListCapability:
    """Marker for session/list support."""

    pass


@dataclass
class SessionCapabilities:
    """Session-level capabilities.

    Attributes:
        list: If present, ``session/list`` is supported.
    """

    list: Optional[SessionListCapability] = None


@dataclass
class AgentCapabilities:
    """Capabilities supported by the agent.

    Attributes:
        load_session: Whether ``session/load`` is available.
        prompt_capabilities: Supported content types in prompts.
        mcp_capabilities: Supported MCP transports.
        session_capabilities: Session-level capabilities.
    """

    load_session: bool = False
    prompt_capabilities: Optional[PromptCapabilities] = None
    mcp_capabilities: Optional[McpCapabilities] = None
    session_capabilities: Optional[SessionCapabilities] = None


@dataclass
class AuthMethod:
    """An authentication method advertised by the agent.

    Attributes:
        id: Unique identifier for this auth method.
        name: Human-readable name.
        description: Optional description.
    """

    id: str
    name: str
    description: Optional[str] = None


@dataclass
class InitializeParams:
    """Parameters for the ``initialize`` request.

    Attributes:
        protocol_version: Latest protocol version the client supports.
        client_capabilities: Capabilities the client supports.
        client_info: Information about the client implementation.
    """

    protocol_version: int = 1
    client_capabilities: Optional[ClientCapabilities] = None
    client_info: Optional[ImplementationInfo] = None


@dataclass
class InitializeResult:
    """Result of the ``initialize`` request.

    Attributes:
        protocol_version: Negotiated protocol version.
        agent_capabilities: Capabilities the agent supports.
        agent_info: Information about the agent implementation.
        auth_methods: Available authentication methods.
    """

    protocol_version: int = 1
    agent_capabilities: Optional[AgentCapabilities] = None
    agent_info: Optional[ImplementationInfo] = None
    auth_methods: Optional[list[AuthMethod]] = None


# ---------------------------------------------------------------------------
# Protocol types -- session setup
# ---------------------------------------------------------------------------


@dataclass
class EnvVariable:
    """An environment variable.

    Attributes:
        name: Variable name.
        value: Variable value.
    """

    name: str
    value: str


@dataclass
class McpServerStdio:
    """Stdio MCP server specification.

    Attributes:
        name: Human-readable server name.
        command: Path to the MCP server executable.
        args: Command-line arguments.
        env: Environment variables.
    """

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: Optional[list[EnvVariable]] = None


@dataclass
class HttpHeader:
    """An HTTP header.

    Attributes:
        name: Header name.
        value: Header value.
    """

    name: str
    value: str


@dataclass
class McpServerHttp:
    """HTTP MCP server specification.

    Attributes:
        name: Human-readable server name.
        url: URL of the MCP server.
        headers: HTTP headers.
        type: Transport type (``"http"`` or ``"sse"``).
    """

    name: str
    url: str
    headers: list[HttpHeader] = field(default_factory=list)
    type: str = "http"


McpServer = Union[McpServerStdio, McpServerHttp]


@dataclass
class NewSessionParams:
    """Parameters for ``session/new``.

    Attributes:
        cwd: Absolute path to the working directory.
        mcp_servers: MCP servers to connect to.
    """

    cwd: str
    mcp_servers: Optional[list[dict[str, Any]]] = None


@dataclass
class SessionMode:
    """An operating mode for the agent.

    Attributes:
        id: Unique mode identifier.
        name: Human-readable mode name.
        description: Optional description.
    """

    id: str
    name: str
    description: Optional[str] = None


@dataclass
class SessionModeState:
    """Current mode state for a session.

    Attributes:
        current_mode_id: The currently active mode.
        available_modes: All available modes.
    """

    current_mode_id: str
    available_modes: list[SessionMode] = field(default_factory=list)


@dataclass
class ConfigOptionValue:
    """A possible value for a configuration option.

    Attributes:
        value: Value identifier.
        name: Human-readable name.
        description: Optional description.
    """

    value: str
    name: str
    description: Optional[str] = None


@dataclass
class ConfigOption:
    """A session configuration option.

    Attributes:
        id: Unique option identifier.
        name: Human-readable label.
        type: Input control type (currently only ``"select"``).
        current_value: Currently selected value.
        options: Available values.
        description: Optional description.
        category: Optional semantic category.
    """

    id: str
    name: str
    type: str
    current_value: str
    options: list[ConfigOptionValue] = field(default_factory=list)
    description: Optional[str] = None
    category: Optional[str] = None


@dataclass
class NewSessionResult:
    """Result of ``session/new``.

    Attributes:
        session_id: Unique identifier for the created session.
        modes: Optional mode state.
        config_options: Optional configuration options.
    """

    session_id: str
    modes: Optional[SessionModeState] = None
    config_options: Optional[list[ConfigOption]] = None


@dataclass
class LoadSessionParams:
    """Parameters for ``session/load``.

    Attributes:
        session_id: Session to resume.
        cwd: Working directory.
        mcp_servers: MCP servers to connect to.
    """

    session_id: str
    cwd: str
    mcp_servers: Optional[list[dict[str, Any]]] = None


# ---------------------------------------------------------------------------
# Protocol types -- prompt turn
# ---------------------------------------------------------------------------


@dataclass
class PromptParams:
    """Parameters for ``session/prompt``.

    Attributes:
        session_id: Target session.
        prompt: Content blocks forming the user message.
    """

    session_id: str
    prompt: list[ContentBlock] = field(default_factory=list)


@dataclass
class PromptResult:
    """Result of ``session/prompt``.

    Attributes:
        stop_reason: Why the agent stopped.
    """

    stop_reason: StopReason


@dataclass
class CancelParams:
    """Parameters for ``session/cancel`` notification.

    Attributes:
        session_id: Session to cancel.
    """

    session_id: str


# ---------------------------------------------------------------------------
# Protocol types -- session modes & config
# ---------------------------------------------------------------------------


@dataclass
class SetModeParams:
    """Parameters for ``session/set_mode``.

    Attributes:
        session_id: Target session.
        mode_id: Mode to switch to.
    """

    session_id: str
    mode_id: str


@dataclass
class SetConfigOptionParams:
    """Parameters for ``session/set_config_option``.

    Attributes:
        session_id: Target session.
        config_id: Configuration option id.
        value: New value.
    """

    session_id: str
    config_id: str
    value: str


@dataclass
class SetConfigOptionResult:
    """Result of ``session/set_config_option``.

    Attributes:
        config_options: Complete list of config options with current values.
    """

    config_options: list[ConfigOption] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Protocol types -- session list
# ---------------------------------------------------------------------------


@dataclass
class ListSessionsParams:
    """Parameters for ``session/list``.

    Attributes:
        cwd: Optional directory filter.
        cursor: Optional pagination cursor.
    """

    cwd: Optional[str] = None
    cursor: Optional[str] = None


@dataclass
class SessionInfo:
    """Metadata about an existing session.

    Attributes:
        session_id: Unique session identifier.
        cwd: Working directory.
        title: Optional human-readable title.
        updated_at: Optional ISO 8601 timestamp.
    """

    session_id: str
    cwd: str
    title: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ListSessionsResult:
    """Result of ``session/list``.

    Attributes:
        sessions: List of session metadata.
        next_cursor: Pagination cursor for the next page.
    """

    sessions: list[SessionInfo] = field(default_factory=list)
    next_cursor: Optional[str] = None


# ---------------------------------------------------------------------------
# Protocol types -- tool calls
# ---------------------------------------------------------------------------


@dataclass
class ToolCallLocation:
    """File location affected by a tool call.

    Attributes:
        path: Absolute file path.
        line: Optional line number (1-based).
    """

    path: str
    line: Optional[int] = None


@dataclass
class DiffContent:
    """A file diff produced by a tool call.

    Attributes:
        path: Absolute path of the file being modified.
        new_text: New content after modification.
        old_text: Original content (``None`` for new files).
        type: Discriminator (always ``"diff"``).
    """

    path: str
    new_text: str
    old_text: Optional[str] = None
    type: str = "diff"


@dataclass
class TerminalContent:
    """Reference to terminal output embedded in a tool call.

    Attributes:
        terminal_id: Id of the terminal created with ``terminal/create``.
        type: Discriminator (always ``"terminal"``).
    """

    terminal_id: str
    type: str = "terminal"


@dataclass
class ToolCallContentItem:
    """A content item within a tool call (wraps a ContentBlock).

    Attributes:
        content: The wrapped content block.
        type: Discriminator (always ``"content"``).
    """

    content: ContentBlock
    type: str = "content"


ToolCallContent = Union[ToolCallContentItem, DiffContent, TerminalContent]


@dataclass
class PermissionOption:
    """A permission option presented to the user.

    Attributes:
        option_id: Unique option identifier.
        name: Human-readable label.
        kind: Permission kind hint.
    """

    option_id: str
    name: str
    kind: PermissionOptionKind


@dataclass
class PermissionOutcome:
    """Outcome of a permission request.

    Attributes:
        outcome: ``"selected"`` or ``"cancelled"``.
        option_id: The selected option id (if ``outcome == "selected"``).
    """

    outcome: str
    option_id: Optional[str] = None


@dataclass
class RequestPermissionParams:
    """Parameters for ``session/request_permission`` (agent -> client).

    Attributes:
        session_id: Target session.
        tool_call: Tool call update with details about the operation.
        options: Available permission options.
    """

    session_id: str
    tool_call: dict[str, Any] = field(default_factory=dict)
    options: list[PermissionOption] = field(default_factory=list)


@dataclass
class RequestPermissionResult:
    """Result of ``session/request_permission``.

    Attributes:
        outcome: The user's decision.
    """

    outcome: PermissionOutcome


# ---------------------------------------------------------------------------
# Protocol types -- plans
# ---------------------------------------------------------------------------


@dataclass
class PlanEntry:
    """A single entry in an agent's execution plan.

    Attributes:
        content: Human-readable task description.
        priority: Relative importance.
        status: Current execution status.
    """

    content: str
    priority: PlanEntryPriority
    status: PlanEntryStatus


# ---------------------------------------------------------------------------
# Protocol types -- slash commands
# ---------------------------------------------------------------------------


@dataclass
class AvailableCommandInput:
    """Input specification for a slash command.

    Attributes:
        hint: Placeholder text shown when no input has been provided.
    """

    hint: str


@dataclass
class AvailableCommand:
    """A slash command advertised by the agent.

    Attributes:
        name: Command name (e.g. ``"web"``).
        description: Human-readable description.
        input: Optional input specification.
    """

    name: str
    description: str
    input: Optional[AvailableCommandInput] = None


# ---------------------------------------------------------------------------
# Protocol types -- file system (client methods)
# ---------------------------------------------------------------------------


@dataclass
class ReadTextFileParams:
    """Parameters for ``fs/read_text_file`` (agent -> client).

    Attributes:
        session_id: Target session.
        path: Absolute file path.
        line: Optional start line (1-based).
        limit: Optional max number of lines.
    """

    session_id: str
    path: str
    line: Optional[int] = None
    limit: Optional[int] = None


@dataclass
class ReadTextFileResult:
    """Result of ``fs/read_text_file``.

    Attributes:
        content: File text content.
    """

    content: str


@dataclass
class WriteTextFileParams:
    """Parameters for ``fs/write_text_file`` (agent -> client).

    Attributes:
        session_id: Target session.
        path: Absolute file path.
        content: Text content to write.
    """

    session_id: str
    path: str
    content: str


# ---------------------------------------------------------------------------
# Protocol types -- terminals (client methods)
# ---------------------------------------------------------------------------


@dataclass
class CreateTerminalParams:
    """Parameters for ``terminal/create`` (agent -> client).

    Attributes:
        session_id: Target session.
        command: Command to execute.
        args: Command arguments.
        env: Environment variables.
        cwd: Working directory (absolute path).
        output_byte_limit: Max bytes of output to retain.
    """

    session_id: str
    command: str
    args: Optional[list[str]] = None
    env: Optional[list[EnvVariable]] = None
    cwd: Optional[str] = None
    output_byte_limit: Optional[int] = None


@dataclass
class CreateTerminalResult:
    """Result of ``terminal/create``.

    Attributes:
        terminal_id: Unique terminal identifier.
    """

    terminal_id: str


@dataclass
class TerminalOutputParams:
    """Parameters for ``terminal/output``.

    Attributes:
        session_id: Target session.
        terminal_id: Terminal to query.
    """

    session_id: str
    terminal_id: str


@dataclass
class TerminalExitStatus:
    """Terminal process exit status.

    Attributes:
        exit_code: Process exit code (may be ``None``).
        signal: Termination signal (may be ``None``).
    """

    exit_code: Optional[int] = None
    signal: Optional[str] = None


@dataclass
class TerminalOutputResult:
    """Result of ``terminal/output``.

    Attributes:
        output: Captured terminal output.
        truncated: Whether output was truncated.
        exit_status: Present only if the command has exited.
    """

    output: str = ""
    truncated: bool = False
    exit_status: Optional[TerminalExitStatus] = None


@dataclass
class WaitForExitParams:
    """Parameters for ``terminal/wait_for_exit``.

    Attributes:
        session_id: Target session.
        terminal_id: Terminal to wait on.
    """

    session_id: str
    terminal_id: str


@dataclass
class KillTerminalParams:
    """Parameters for ``terminal/kill``.

    Attributes:
        session_id: Target session.
        terminal_id: Terminal to kill.
    """

    session_id: str
    terminal_id: str


@dataclass
class ReleaseTerminalParams:
    """Parameters for ``terminal/release``.

    Attributes:
        session_id: Target session.
        terminal_id: Terminal to release.
    """

    session_id: str
    terminal_id: str


# ---------------------------------------------------------------------------
# Session update types (agent -> client notifications)
# ---------------------------------------------------------------------------


@dataclass
class AgentMessageChunkUpdate:
    """Agent text output chunk.

    Attributes:
        content: The content block.
        session_update: Discriminator.
    """

    content: ContentBlock
    session_update: str = "agent_message_chunk"


@dataclass
class UserMessageChunkUpdate:
    """Replayed user message chunk (used in ``session/load``).

    Attributes:
        content: The content block.
        session_update: Discriminator.
    """

    content: ContentBlock
    session_update: str = "user_message_chunk"


@dataclass
class ThoughtMessageChunkUpdate:
    """Agent internal reasoning chunk.

    Attributes:
        content: The content block.
        session_update: Discriminator.
    """

    content: ContentBlock
    session_update: str = "thought_message_chunk"


@dataclass
class ToolCallUpdate:
    """Initial tool call notification.

    Attributes:
        tool_call_id: Unique tool call identifier.
        title: Human-readable description.
        kind: Tool category.
        status: Current execution status.
        content: Tool call content items.
        locations: File locations affected.
        raw_input: Raw input parameters.
        raw_output: Raw output.
        session_update: Discriminator.
    """

    tool_call_id: str
    title: str
    kind: ToolKind = ToolKind.OTHER
    status: ToolCallStatus = ToolCallStatus.PENDING
    content: Optional[list[ToolCallContent]] = None
    locations: Optional[list[ToolCallLocation]] = None
    raw_input: Optional[dict[str, Any]] = None
    raw_output: Optional[dict[str, Any]] = None
    session_update: str = "tool_call"


@dataclass
class ToolCallStatusUpdate:
    """Tool call progress/result update.

    Attributes:
        tool_call_id: The tool call being updated.
        status: New status.
        content: Optional new content.
        title: Optional updated title.
        locations: Optional updated locations.
        session_update: Discriminator.
    """

    tool_call_id: str
    status: Optional[ToolCallStatus] = None
    content: Optional[list[ToolCallContent]] = None
    title: Optional[str] = None
    locations: Optional[list[ToolCallLocation]] = None
    session_update: str = "tool_call_update"


@dataclass
class PlanUpdate:
    """Agent execution plan.

    Attributes:
        entries: Plan entries.
        session_update: Discriminator.
    """

    entries: list[PlanEntry] = field(default_factory=list)
    session_update: str = "plan"


@dataclass
class AvailableCommandsUpdate:
    """Update to available slash commands.

    Attributes:
        available_commands: Current list of commands.
        session_update: Discriminator.
    """

    available_commands: list[AvailableCommand] = field(default_factory=list)
    session_update: str = "available_commands_update"


@dataclass
class CurrentModeUpdate:
    """Notification that the agent changed its mode.

    Attributes:
        mode_id: New mode identifier.
        session_update: Discriminator.
    """

    mode_id: str
    session_update: str = "current_mode_update"


@dataclass
class ConfigOptionUpdate:
    """Notification that config options changed.

    Attributes:
        config_options: Complete configuration state.
        session_update: Discriminator.
    """

    config_options: list[ConfigOption] = field(default_factory=list)
    session_update: str = "config_option_update"


@dataclass
class SessionInfoUpdate:
    """Update to session metadata.

    Attributes:
        title: Updated session title.
        updated_at: Updated timestamp.
        session_update: Discriminator.
    """

    title: Optional[str] = None
    updated_at: Optional[str] = None
    session_update: str = "session_info_update"


SessionUpdate = Union[
    AgentMessageChunkUpdate,
    UserMessageChunkUpdate,
    ThoughtMessageChunkUpdate,
    ToolCallUpdate,
    ToolCallStatusUpdate,
    PlanUpdate,
    AvailableCommandsUpdate,
    CurrentModeUpdate,
    ConfigOptionUpdate,
    SessionInfoUpdate,
]


# ---------------------------------------------------------------------------
# ACP Client
# ---------------------------------------------------------------------------


class ACPClient:
    """High-level async client for communicating with an ACP agent subprocess.

    Usage::

        client = ACPClient(["python", "-m", "my_agent"])
        await client.start()
        init = await client.initialize()
        session = await client.new_session("/project")
        async for update in client.prompt(session.session_id, "Hello"):
            print(update)
        await client.stop()

    Args:
        command: Command and arguments to spawn the agent process.
        env: Optional environment variables for the subprocess.
    """

    def __init__(
        self,
        command: list[str],
        env: Optional[dict[str, str]] = None,
    ) -> None:
        self._command = command
        self._env = env
        self._process: Optional[asyncio.subprocess.Process] = None
        self._transport: Optional[JSONRPCTransport] = None
        self._pending: dict[Union[int, str], asyncio.Future[dict[str, Any]]] = {}
        self._notification_handlers: dict[str, Callable[..., Any]] = {}
        self._update_queue: asyncio.Queue[Optional[dict[str, Any]]] = asyncio.Queue()
        self._reader_task: Optional[asyncio.Task[None]] = None
        self._request_handler: Optional[Callable[[str, dict[str, Any]], Any]] = None

    async def start(self) -> None:
        """Launch the agent subprocess and begin reading messages."""
        self._process = await asyncio.create_subprocess_exec(
            *self._command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._env,
        )
        assert self._process.stdin is not None
        assert self._process.stdout is not None
        reader = asyncio.StreamReader()
        reader.set_transport(self._process.stdout._transport)  # type: ignore[union-attr]  # ty: ignore[unresolved-attribute]
        self._transport = JSONRPCTransport(
            reader=self._process.stdout,  # type: ignore[arg-type]
            writer=self._process.stdin,  # type: ignore[arg-type]
        )
        self._reader_task = asyncio.create_task(self._read_loop())

    async def stop(self) -> None:
        """Terminate the agent subprocess and clean up."""
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        if self._transport:
            await self._transport.close()
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()

    def set_request_handler(
        self, handler: Callable[[str, dict[str, Any]], Any]
    ) -> None:
        """Register a handler for incoming requests from the agent.

        This is used for requests like ``session/request_permission``,
        ``fs/read_text_file``, etc.

        Args:
            handler: Async callable ``(method, params) -> result``.
        """
        self._request_handler = handler

    async def _read_loop(self) -> None:
        """Background task that reads and dispatches incoming messages."""
        assert self._transport is not None
        while True:
            msg = await self._transport.read_message()
            if msg is None:
                # EOF -- signal any waiting prompt iterators
                await self._update_queue.put(None)
                break

            # Response to one of our requests
            if "id" in msg and ("result" in msg or "error" in msg):
                req_id = msg["id"]
                fut = self._pending.pop(req_id, None)
                if fut and not fut.done():
                    if "error" in msg:
                        fut.set_exception(
                            JSONRPCException(JSONRPCError.from_dict(msg["error"]))
                        )
                    else:
                        fut.set_result(msg.get("result") or {})

            # Notification from agent
            elif "method" in msg and "id" not in msg:
                method = msg["method"]
                params = msg.get("params", {})
                if method == "session/update":
                    await self._update_queue.put(params)
                handler = self._notification_handlers.get(method)
                if handler:
                    asyncio.create_task(handler(params))

            # Request from agent (e.g. permission, fs, terminal)
            elif "method" in msg and "id" in msg:
                asyncio.create_task(self._handle_agent_request(msg))

    async def _handle_agent_request(self, msg: dict[str, Any]) -> None:
        """Handle an incoming request from the agent side."""
        assert self._transport is not None
        req_id = msg["id"]
        method = msg["method"]
        params = msg.get("params", {})
        if self._request_handler:
            try:
                result = self._request_handler(method, params)
                if asyncio.iscoroutine(result):
                    result = await result
                await self._transport.send_result(req_id, result)
            except Exception as exc:
                await self._transport.send_error(
                    req_id,
                    JSONRPCError(code=INTERNAL_ERROR, message=str(exc)),
                )
        else:
            await self._transport.send_error(
                req_id,
                JSONRPCError(
                    code=METHOD_NOT_FOUND,
                    message=f"No handler for {method}",
                ),
            )

    async def _call(self, method: str, params: Any = None) -> Any:
        """Send a request and wait for its response.

        Args:
            method: JSON-RPC method name.
            params: Method parameters.

        Returns:
            The result payload from the agent.

        Raises:
            JSONRPCException: If the agent returns an error.
        """
        assert self._transport is not None
        sent = await self._transport.send_request(method, params)
        req_id = sent["id"]
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending[req_id] = fut
        return await fut

    # -- Public API ---------------------------------------------------------

    async def initialize(
        self,
        params: Optional[InitializeParams] = None,
    ) -> InitializeResult:
        """Perform the ``initialize`` handshake with the agent.

        Args:
            params: Initialization parameters (defaults provided if ``None``).

        Returns:
            The agent's initialization result.
        """
        if params is None:
            params = InitializeParams()
        raw = await self._call("initialize", to_dict(params))
        raw = raw or {}
        r = from_raw(raw)
        agent_info = None
        if "agent_info" in r:
            ai = r["agent_info"]
            agent_info = ImplementationInfo(
                name=ai.get("name", ""),
                version=ai.get("version", ""),
                title=ai.get("title"),
            )
        return InitializeResult(
            protocol_version=r.get("protocol_version", 1),
            agent_info=agent_info,
        )

    async def new_session(
        self,
        cwd: str,
        mcp_servers: Optional[list[dict[str, Any]]] = None,
    ) -> NewSessionResult:
        """Create a new conversation session.

        Args:
            cwd: Absolute path to the working directory.
            mcp_servers: Optional MCP server configurations.

        Returns:
            The session creation result including the session id.
        """
        p: dict[str, Any] = {"cwd": cwd}
        if mcp_servers:
            p["mcpServers"] = mcp_servers
        raw = await self._call("session/new", p)
        raw = raw or {}
        r = from_raw(raw)
        return NewSessionResult(session_id=r.get("session_id", ""))

    async def load_session(
        self,
        session_id: str,
        cwd: str,
        mcp_servers: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        """Load (resume) an existing session.

        The agent will replay conversation history as ``session/update``
        notifications before responding.

        Args:
            session_id: Session to resume.
            cwd: Working directory.
            mcp_servers: Optional MCP server configurations.
        """
        p: dict[str, Any] = {"sessionId": session_id, "cwd": cwd}
        if mcp_servers:
            p["mcpServers"] = mcp_servers
        await self._call("session/load", p)

    async def prompt(
        self,
        session_id: str,
        text: str,
        extra_content: Optional[list[ContentBlock]] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Send a prompt and yield ``session/update`` notifications.

        This is an async generator.  It yields each raw update dictionary
        until the ``session/prompt`` response is received.

        Args:
            session_id: Target session.
            text: User message text.
            extra_content: Additional content blocks to include.

        Yields:
            Raw ``session/update`` parameter dictionaries.
        """
        blocks: list[dict[str, Any]] = [{"type": "text", "text": text}]
        if extra_content:
            for b in extra_content:
                blocks.append(to_dict(b))

        params = {"sessionId": session_id, "prompt": blocks}

        # Drain any stale updates before sending the prompt
        while not self._update_queue.empty():
            try:
                self._update_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        assert self._transport is not None
        sent = await self._transport.send_request("session/prompt", params)
        req_id = sent["id"]
        loop = asyncio.get_running_loop()
        prompt_fut: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending[req_id] = prompt_fut

        while True:
            # Wait for either an update notification or the prompt response
            update_task = asyncio.create_task(self._update_queue.get())
            done, _ = await asyncio.wait(
                [update_task, prompt_fut],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if update_task in done:
                update = update_task.result()
                if update is None:
                    # EOF
                    return
                yield update
            else:
                update_task.cancel()

            if prompt_fut.done():
                # Drain remaining updates
                while not self._update_queue.empty():
                    update = self._update_queue.get_nowait()
                    if update is not None:
                        yield update
                return

    async def prompt_simple(
        self,
        session_id: str,
        text: str,
    ) -> tuple[list[dict[str, Any]], PromptResult]:
        """Send a prompt and collect all updates, returning them with the result.

        A simpler alternative to the async-generator ``prompt()`` method.

        Args:
            session_id: Target session.
            text: User message text.

        Returns:
            Tuple of (list of update dicts, PromptResult).
        """
        updates: list[dict[str, Any]] = []
        async for u in self.prompt(session_id, text):
            updates.append(u)
        # The prompt future should be resolved by now
        return updates, PromptResult(stop_reason=StopReason.END_TURN)

    async def cancel(self, session_id: str) -> None:
        """Cancel the current prompt turn.

        Args:
            session_id: Session to cancel.
        """
        assert self._transport is not None
        await self._transport.send_notification(
            "session/cancel", {"sessionId": session_id}
        )

    async def set_mode(self, session_id: str, mode_id: str) -> None:
        """Switch the agent operating mode.

        Args:
            session_id: Target session.
            mode_id: Mode to switch to.
        """
        await self._call(
            "session/set_mode",
            {"sessionId": session_id, "modeId": mode_id},
        )

    async def list_sessions(
        self,
        cwd: Optional[str] = None,
        cursor: Optional[str] = None,
    ) -> ListSessionsResult:
        """List sessions known to the agent.

        Args:
            cwd: Optional working-directory filter.
            cursor: Optional pagination cursor.

        Returns:
            List of session metadata.
        """
        p: dict[str, Any] = {}
        if cwd:
            p["cwd"] = cwd
        if cursor:
            p["cursor"] = cursor
        raw = await self._call("session/list", p)
        raw = raw or {}
        sessions: list[SessionInfo] = []
        for s in raw.get("sessions", []):
            sr = from_raw(s)
            sessions.append(
                SessionInfo(
                    session_id=sr.get("session_id", ""),
                    cwd=sr.get("cwd", ""),
                    title=sr.get("title"),
                    updated_at=sr.get("updated_at"),
                )
            )
        return ListSessionsResult(
            sessions=sessions,
            next_cursor=raw.get("nextCursor"),
        )


# ---------------------------------------------------------------------------
# ACP Agent (server-side base class)
# ---------------------------------------------------------------------------


class ACPAgent(ABC):
    """Abstract base class for implementing an ACP-compatible agent.

    Subclass this and override the ``on_*`` methods.  Call ``await agent.run()``
    to start the stdio event loop.

    Example::

        class MyAgent(ACPAgent):
            async def on_initialize(self, params):
                return InitializeResult(protocol_version=1)
            async def on_new_session(self, params):
                return NewSessionResult(session_id=str(uuid.uuid4()))
            async def on_prompt(self, params):
                await self.send_update(params.session_id,
                    AgentMessageChunkUpdate(content=TextContent(text="Hi!")))
                return PromptResult(stop_reason=StopReason.END_TURN)
    """

    def __init__(self) -> None:
        self._transport: Optional[JSONRPCTransport] = None
        self._running = False

    # -- Handler methods (override these) -----------------------------------

    @abstractmethod
    async def on_initialize(self, params: InitializeParams) -> InitializeResult:
        """Handle the ``initialize`` request.

        Args:
            params: Initialization parameters from the client.

        Returns:
            Initialization result with agent capabilities.
        """
        ...

    @abstractmethod
    async def on_new_session(self, params: NewSessionParams) -> NewSessionResult:
        """Handle ``session/new``.

        Args:
            params: Session creation parameters.

        Returns:
            Result containing the new session id.
        """
        ...

    @abstractmethod
    async def on_prompt(self, params: PromptParams) -> PromptResult:
        """Handle ``session/prompt``.

        Use ``self.send_update()`` to stream updates back to the client
        before returning the final result.

        Args:
            params: Prompt parameters including user message.

        Returns:
            Result with the stop reason.
        """
        ...

    async def on_load_session(self, params: LoadSessionParams) -> None:
        """Handle ``session/load``.  Override to support session resumption.

        Args:
            params: Session load parameters.
        """
        raise JSONRPCException(
            JSONRPCError(
                code=METHOD_NOT_FOUND,
                message="session/load not supported",
            )
        )

    async def on_cancel(self, params: CancelParams) -> None:
        """Handle ``session/cancel`` notification.

        Args:
            params: Cancel parameters.
        """

    async def on_set_mode(self, params: SetModeParams) -> None:
        """Handle ``session/set_mode``.

        Args:
            params: Mode change parameters.
        """

    async def on_set_config_option(
        self, params: SetConfigOptionParams
    ) -> SetConfigOptionResult:
        """Handle ``session/set_config_option``.

        Args:
            params: Config option change parameters.

        Returns:
            Complete configuration state.
        """
        return SetConfigOptionResult()

    async def on_list_sessions(self, params: ListSessionsParams) -> ListSessionsResult:
        """Handle ``session/list``.

        Args:
            params: List sessions parameters.

        Returns:
            List of session metadata.
        """
        return ListSessionsResult()

    # -- Outgoing helpers ---------------------------------------------------

    async def send_update(self, session_id: str, update: SessionUpdate) -> None:
        """Send a ``session/update`` notification to the client.

        Args:
            session_id: Target session.
            update: The update payload.
        """
        assert self._transport is not None
        await self._transport.send_notification(
            "session/update",
            {"sessionId": session_id, "update": to_dict(update)},
        )

    async def request_permission(
        self,
        session_id: str,
        tool_call: dict[str, Any],
        options: list[PermissionOption],
    ) -> PermissionOutcome:
        """Request permission from the client for a tool call.

        Args:
            session_id: Target session.
            tool_call: Tool call details.
            options: Available permission options.

        Returns:
            The user's decision.

        Raises:
            JSONRPCException: If the client returns an error.
        """
        assert self._transport is not None
        sent = await self._transport.send_request(
            "session/request_permission",
            {
                "sessionId": session_id,
                "toolCall": tool_call,
                "options": [to_dict(o) for o in options],
            },
        )
        # We need to wait for the response in-line.  Since run() owns the
        # read loop, we store a future that run() will resolve.
        req_id = sent["id"]
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending_requests[req_id] = fut
        raw = await fut
        outcome = raw.get("outcome", {})
        return PermissionOutcome(
            outcome=outcome.get("outcome", "cancelled"),
            option_id=outcome.get("optionId"),
        )

    async def read_text_file(
        self,
        session_id: str,
        path: str,
        *,
        line: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> str:
        """Read a text file via the client's ``fs/read_text_file`` method.

        Args:
            session_id: Target session.
            path: Absolute file path.
            line: Optional start line (1-based).
            limit: Optional max lines.

        Returns:
            File text content.
        """
        assert self._transport is not None
        p: dict[str, Any] = {"sessionId": session_id, "path": path}
        if line is not None:
            p["line"] = line
        if limit is not None:
            p["limit"] = limit
        sent = await self._transport.send_request("fs/read_text_file", p)
        req_id = sent["id"]
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending_requests[req_id] = fut
        raw = await fut
        return raw.get("content", "")

    async def write_text_file(self, session_id: str, path: str, content: str) -> None:
        """Write a text file via the client's ``fs/write_text_file`` method.

        Args:
            session_id: Target session.
            path: Absolute file path.
            content: Text content to write.
        """
        assert self._transport is not None
        sent = await self._transport.send_request(
            "fs/write_text_file",
            {"sessionId": session_id, "path": path, "content": content},
        )
        req_id = sent["id"]
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending_requests[req_id] = fut
        await fut

    async def create_terminal(
        self,
        session_id: str,
        command: str,
        *,
        args: Optional[list[str]] = None,
        cwd: Optional[str] = None,
    ) -> str:
        """Create a terminal via the client's ``terminal/create`` method.

        Args:
            session_id: Target session.
            command: Command to execute.
            args: Command arguments.
            cwd: Working directory.

        Returns:
            Terminal id.
        """
        assert self._transport is not None
        p: dict[str, Any] = {"sessionId": session_id, "command": command}
        if args:
            p["args"] = args
        if cwd:
            p["cwd"] = cwd
        sent = await self._transport.send_request("terminal/create", p)
        req_id = sent["id"]
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending_requests[req_id] = fut
        raw = await fut
        return raw.get("terminalId", "")

    # -- Main event loop ----------------------------------------------------

    async def run(self) -> None:
        """Run the agent, reading from stdin and writing to stdout.

        This blocks until the client closes the connection (EOF on stdin).
        """
        loop = asyncio.get_running_loop()
        reader = asyncio.StreamReader()
        read_transport, _ = await loop.connect_read_pipe(
            lambda: asyncio.StreamReaderProtocol(reader), sys.stdin
        )

        # Build a proper StreamWriter backed by a StreamReaderProtocol so
        # that drain() works correctly on all Python versions.
        write_reader = asyncio.StreamReader()
        write_protocol = asyncio.StreamReaderProtocol(write_reader)
        write_transport, _ = await loop.connect_write_pipe(
            lambda: write_protocol, sys.stdout
        )
        writer = asyncio.StreamWriter(
            write_transport,
            write_protocol,
            write_reader,
            loop,
        )

        self._transport = JSONRPCTransport(reader, writer)
        self._running = True
        self._pending_requests: dict[
            Union[int, str], asyncio.Future[dict[str, Any]]
        ] = {}

        logger.info("Agent started, waiting for messages on stdin...")
        try:
            while self._running:
                msg = await self._transport.read_message()
                if msg is None:
                    break
                asyncio.create_task(self._dispatch(msg))
        except asyncio.CancelledError:
            pass
        finally:
            self._running = False
            await self._transport.close()
            read_transport.close()

    async def _dispatch(self, msg: dict[str, Any]) -> None:
        """Route an incoming JSON-RPC message to the appropriate handler."""
        assert self._transport is not None

        # Response to a request we made (permission, fs, terminal)
        if "id" in msg and ("result" in msg or "error" in msg):
            req_id = msg["id"]
            fut = self._pending_requests.pop(req_id, None)
            if fut and not fut.done():
                if "error" in msg:
                    fut.set_exception(
                        JSONRPCException(JSONRPCError.from_dict(msg["error"]))
                    )
                else:
                    fut.set_result(msg.get("result") or {})
            return

        method = msg.get("method")
        params = msg.get("params", {})
        req_id = msg.get("id")
        is_notification = req_id is None

        try:
            result = await self._handle_method(method, params)
            if not is_notification:
                assert req_id is not None
                result_dict = to_dict(result) if result is not None else None
                await self._transport.send_result(req_id, result_dict)
        except JSONRPCException as exc:
            if not is_notification:
                await self._transport.send_error(req_id, exc.error)
        except Exception as exc:
            logger.exception("Unhandled error in %s", method)
            if not is_notification:
                await self._transport.send_error(
                    req_id,
                    JSONRPCError(code=INTERNAL_ERROR, message=str(exc)),
                )

    async def _handle_method(
        self, method: Optional[str], params: dict[str, Any]
    ) -> Any:
        """Dispatch a method call to the correct handler."""
        if method == "initialize":
            rp = from_raw(params)
            client_info = None
            if "client_info" in rp:
                ci = rp["client_info"]
                client_info = ImplementationInfo(
                    name=ci.get("name", ""),
                    version=ci.get("version", ""),
                    title=ci.get("title"),
                )
            client_caps = None
            if "client_capabilities" in rp:
                cc = rp["client_capabilities"]
                fs = None
                if "fs" in cc:
                    f = cc["fs"]
                    fs = FsCapabilities(
                        read_text_file=f.get("readTextFile", False),
                        write_text_file=f.get("writeTextFile", False),
                    )
                client_caps = ClientCapabilities(
                    fs=fs, terminal=cc.get("terminal", False)
                )
            return await self.on_initialize(
                InitializeParams(
                    protocol_version=rp.get("protocol_version", 1),
                    client_capabilities=client_caps,
                    client_info=client_info,
                )
            )

        if method == "session/new":
            rp = from_raw(params)
            return await self.on_new_session(
                NewSessionParams(
                    cwd=rp.get("cwd", "."),
                    mcp_servers=rp.get("mcp_servers"),
                )
            )

        if method == "session/load":
            rp = from_raw(params)
            return await self.on_load_session(
                LoadSessionParams(
                    session_id=rp.get("session_id", ""),
                    cwd=rp.get("cwd", "."),
                    mcp_servers=rp.get("mcp_servers"),
                )
            )

        if method == "session/prompt":
            rp = from_raw(params)
            prompt_blocks: list[ContentBlock] = []
            for block in rp.get("prompt", []):
                prompt_blocks.append(_content_from_dict(block))
            return await self.on_prompt(
                PromptParams(
                    session_id=rp.get("session_id", ""),
                    prompt=prompt_blocks,
                )
            )

        if method == "session/cancel":
            rp = from_raw(params)
            await self.on_cancel(CancelParams(session_id=rp.get("session_id", "")))
            return None

        if method == "session/set_mode":
            rp = from_raw(params)
            await self.on_set_mode(
                SetModeParams(
                    session_id=rp.get("session_id", ""),
                    mode_id=rp.get("mode_id", ""),
                )
            )
            return None

        if method == "session/set_config_option":
            rp = from_raw(params)
            return await self.on_set_config_option(
                SetConfigOptionParams(
                    session_id=rp.get("session_id", ""),
                    config_id=rp.get("config_id", ""),
                    value=rp.get("value", ""),
                )
            )

        if method == "session/list":
            rp = from_raw(params)
            return await self.on_list_sessions(
                ListSessionsParams(
                    cwd=rp.get("cwd"),
                    cursor=rp.get("cursor"),
                )
            )

        raise JSONRPCException(
            JSONRPCError(
                code=METHOD_NOT_FOUND,
                message=f"Unknown method: {method}",
            )
        )


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------


class _EchoAgent(ACPAgent):
    """Minimal echo agent for demonstration purposes."""

    async def on_initialize(self, params: InitializeParams) -> InitializeResult:
        return InitializeResult(
            protocol_version=params.protocol_version,
            agent_info=ImplementationInfo(
                name="echo-agent", version="0.1.0", title="Echo Agent"
            ),
        )

    async def on_new_session(self, params: NewSessionParams) -> NewSessionResult:
        return NewSessionResult(session_id=f"sess_{uuid.uuid4().hex[:12]}")

    async def on_prompt(self, params: PromptParams) -> PromptResult:
        # Collect text from the prompt
        text_parts: list[str] = []
        for block in params.prompt:
            if isinstance(block, TextContent):
                text_parts.append(block.text)

        user_text = " ".join(text_parts) if text_parts else "(empty)"

        # Echo back as an agent message chunk
        await self.send_update(
            params.session_id,
            AgentMessageChunkUpdate(content=TextContent(text=f"Echo: {user_text}")),
        )
        return PromptResult(stop_reason=StopReason.END_TURN)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    print(
        "Starting echo agent. Send JSON-RPC messages on stdin.",
        file=sys.stderr,
    )
    asyncio.run(_EchoAgent().run())
