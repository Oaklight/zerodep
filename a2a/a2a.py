# /// zerodep
# version = "0.3.0"
# deps = ["jsonrpc"]
# tier = "subsystem"
# category = "network"
# note = "Install/update via zerodep CLI (https://zerodep.readthedocs.io/en/latest/guide/cli/). Manual copy may miss deps."
# ///

"""A2A (Agent-to-Agent Protocol) - Zero-dependency Python implementation.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

A pure-stdlib implementation of Google's A2A protocol (v1.0) for agent-to-agent
communication.  Covers the JSON-RPC 2.0 binding with SSE streaming, an HTTP
client, an HTTP server, and an in-memory task store.

Protocol reference:
    https://github.com/a2aproject/A2A
    https://a2a-protocol.org/specification

Requires:
    Python >= 3.10, no external packages.

Sections:
    1. Protocol Data Types   - dataclass models for the canonical A2A data model
    2. JSON-RPC 2.0 Layer    - request / response / error / dispatcher
    3. SSE Utilities         - server-sent events writer and parser
    4. A2A Client            - urllib-based client with SSE streaming
    5. A2A Server            - http.server-based server with SSE support
    6. Task Management       - in-memory TaskStore and TaskManager

Example usage is provided in the ``if __name__ == "__main__"`` block at the
bottom of this file.
"""

from __future__ import annotations

import copy
import datetime
import enum
import http.client
import http.server
import json
import logging
import os
import re
import socketserver
import sys
import threading
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field, fields
from typing import (
    Any,
    Callable,
    Iterator,
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
    PARSE_ERROR,
    JSONRPCDispatcher,
    JSONRPCError,
    JSONRPCException,
    JSONRPCRequest,
    JSONRPCResponse,
)

__all__ = [
    # enums
    "TaskState",
    "Role",
    # data types
    "Part",
    "Message",
    "Artifact",
    "TaskStatus",
    "Task",
    "TaskStatusUpdateEvent",
    "TaskArtifactUpdateEvent",
    "StreamResponse",
    "SendMessageConfiguration",
    "SendMessageRequest",
    "SendMessageResponse",
    "AuthenticationInfo",
    "PushNotificationConfig",
    "AgentProvider",
    "AgentCapabilities",
    "AgentExtension",
    "AgentSkill",
    "AgentInterface",
    "AgentCard",
    # json-rpc
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCError",
    "JSONRPCDispatcher",
    # errors
    "A2AError",
    "TaskNotFoundError",
    "TaskNotCancelableError",
    "PushNotificationNotSupportedError",
    "UnsupportedOperationError",
    "ContentTypeNotSupportedError",
    "InvalidAgentResponseError",
    # sse
    "sse_encode",
    "sse_decode_stream",
    # client
    "A2AClient",
    # server
    "A2AServer",
    "A2ARequestHandler",
    # task management
    "TaskStore",
    "TaskManager",
]

__version__ = "0.3.0"

logger = logging.getLogger("a2a")

# ── Helpers: camelCase <-> snake_case ──────────────────────────────────────

_CAMEL_RE = re.compile(r"(?<=[a-z0-9])([A-Z])")


def _to_camel(name: str) -> str:
    """Convert a snake_case name to camelCase."""
    parts = name.split("_")
    return parts[0] + "".join(w.capitalize() for w in parts[1:])


def _to_snake(name: str) -> str:
    """Convert a camelCase name to snake_case."""
    return _CAMEL_RE.sub(r"_\1", name).lower()


def _now_iso() -> str:
    """Return the current UTC time in ISO 8601 format."""
    return (
        datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[
            :-3
        ]
        + "Z"
    )


# ── 1. Protocol Data Types ─────────────────────────────────────────────────


class TaskState(str, enum.Enum):
    """Lifecycle states of a Task (mirrors ``TaskState`` proto enum)."""

    UNSPECIFIED = "TASK_STATE_UNSPECIFIED"
    SUBMITTED = "TASK_STATE_SUBMITTED"
    WORKING = "TASK_STATE_WORKING"
    COMPLETED = "TASK_STATE_COMPLETED"
    FAILED = "TASK_STATE_FAILED"
    CANCELED = "TASK_STATE_CANCELED"
    INPUT_REQUIRED = "TASK_STATE_INPUT_REQUIRED"
    REJECTED = "TASK_STATE_REJECTED"
    AUTH_REQUIRED = "TASK_STATE_AUTH_REQUIRED"

    def is_terminal(self) -> bool:
        """Return True if the state is terminal (no further transitions)."""
        return self in (
            TaskState.COMPLETED,
            TaskState.FAILED,
            TaskState.CANCELED,
            TaskState.REJECTED,
        )


class Role(str, enum.Enum):
    """Sender role for a Message."""

    UNSPECIFIED = "ROLE_UNSPECIFIED"
    USER = "ROLE_USER"
    AGENT = "ROLE_AGENT"


# --- Serialization helpers for dataclasses ---


def _serialize(obj: Any) -> Any:
    """Recursively convert a dataclass / enum / dict / list to JSON-safe dicts.

    Field names are emitted in camelCase.  ``None`` values and empty
    collections are omitted for a compact wire format.
    """
    if obj is None:
        return None
    if isinstance(obj, enum.Enum):
        return obj.value
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, (list, tuple)):
        return [_serialize(v) for v in obj]
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
            result[_to_camel(f.name)] = _serialize(val)
        return result
    return obj


def _enum_from_value(enum_cls: type[enum.Enum], value: Any) -> Any:
    """Look up an enum member by its *value* string."""
    if isinstance(value, enum_cls):
        return value
    for member in enum_cls:
        if member.value == value:
            return member
    raise ValueError(f"Unknown {enum_cls.__name__} value: {value!r}")


# --- Core Part type ---


@dataclass
class Part:
    """The smallest unit of content inside a Message or Artifact.

    Exactly one of ``text``, ``raw``, ``url``, or ``data`` should be set,
    corresponding to the ``oneof content`` in the proto definition.

    Attributes:
        text: Plain-text content.
        raw: Base64-encoded binary content.
        url: URL pointing to file content.
        data: Arbitrary structured data (JSON value).
        metadata: Optional key-value metadata.
        filename: Optional filename hint.
        media_type: MIME type of the content.
    """

    text: str | None = None
    raw: str | None = None
    url: str | None = None
    data: Any | None = None
    metadata: dict[str, Any] | None = None
    filename: str | None = None
    media_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Part":
        """Deserialize from a camelCase dictionary."""
        return cls(
            text=d.get("text"),
            raw=d.get("raw"),
            url=d.get("url"),
            data=d.get("data"),
            metadata=d.get("metadata"),
            filename=d.get("filename"),
            media_type=d.get("mediaType"),
        )


# --- Message ---


@dataclass
class Message:
    """A single communication turn between client and agent.

    Attributes:
        message_id: Unique identifier for this message.
        role: The sender role (user or agent).
        parts: Content parts of the message.
        context_id: Optional context grouping identifier.
        task_id: Optional associated task identifier.
        metadata: Optional key-value metadata.
        extensions: Extension URIs active for this message.
        reference_task_ids: Task IDs referenced for additional context.
    """

    message_id: str = ""
    role: Role = Role.USER
    parts: list[Part] = field(default_factory=list)
    context_id: str | None = None
    task_id: str | None = None
    metadata: dict[str, Any] | None = None
    extensions: list[str] | None = None
    reference_task_ids: list[str] | None = None

    def __post_init__(self) -> None:
        if not self.message_id:
            self.message_id = str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Message":
        """Deserialize from a camelCase dictionary."""
        role_val = d.get("role", "ROLE_USER")
        return cls(
            message_id=d.get("messageId", ""),
            role=_enum_from_value(Role, role_val),
            parts=[Part.from_dict(p) for p in d.get("parts", [])],
            context_id=d.get("contextId"),
            task_id=d.get("taskId"),
            metadata=d.get("metadata"),
            extensions=d.get("extensions"),
            reference_task_ids=d.get("referenceTaskIds"),
        )


# --- Artifact ---


@dataclass
class Artifact:
    """An output produced by the agent as a result of task processing.

    Attributes:
        artifact_id: Unique identifier within a task.
        parts: Content parts of the artifact.
        name: Human-readable name.
        description: Human-readable description.
        metadata: Optional key-value metadata.
        extensions: Extension URIs relevant to this artifact.
    """

    artifact_id: str = ""
    parts: list[Part] = field(default_factory=list)
    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None
    extensions: list[str] | None = None

    def __post_init__(self) -> None:
        if not self.artifact_id:
            self.artifact_id = str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Artifact":
        """Deserialize from a camelCase dictionary."""
        return cls(
            artifact_id=d.get("artifactId", ""),
            parts=[Part.from_dict(p) for p in d.get("parts", [])],
            name=d.get("name"),
            description=d.get("description"),
            metadata=d.get("metadata"),
            extensions=d.get("extensions"),
        )


# --- TaskStatus ---


@dataclass
class TaskStatus:
    """Current status of a Task.

    Attributes:
        state: The lifecycle state.
        message: An optional message associated with the status.
        timestamp: ISO 8601 timestamp when the status was recorded.
    """

    state: TaskState = TaskState.SUBMITTED
    message: Message | None = None
    timestamp: str | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = _now_iso()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TaskStatus":
        """Deserialize from a camelCase dictionary."""
        msg = d.get("message")
        return cls(
            state=_enum_from_value(TaskState, d.get("state", "TASK_STATE_UNSPECIFIED")),
            message=Message.from_dict(msg) if msg else None,
            timestamp=d.get("timestamp"),
        )


# --- Task ---


@dataclass
class Task:
    """The fundamental unit of work managed by A2A.

    Attributes:
        id: Server-generated unique identifier.
        status: Current task status.
        context_id: Optional context grouping identifier.
        artifacts: Output artifacts produced so far.
        history: Message history for the task.
        metadata: Optional key-value metadata.
    """

    id: str = ""
    status: TaskStatus = field(default_factory=TaskStatus)
    context_id: str | None = None
    artifacts: list[Artifact] | None = None
    history: list[Message] | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Task":
        """Deserialize from a camelCase dictionary."""
        artifacts_raw = d.get("artifacts")
        history_raw = d.get("history")
        return cls(
            id=d.get("id", ""),
            status=TaskStatus.from_dict(d.get("status", {})),
            context_id=d.get("contextId"),
            artifacts=(
                [Artifact.from_dict(a) for a in artifacts_raw]
                if artifacts_raw is not None
                else None
            ),
            history=(
                [Message.from_dict(m) for m in history_raw]
                if history_raw is not None
                else None
            ),
            metadata=d.get("metadata"),
        )


# --- Streaming event types ---


@dataclass
class TaskStatusUpdateEvent:
    """Event indicating a change in task status.

    Attributes:
        task_id: The task that changed.
        context_id: The context the task belongs to.
        status: The new status.
        metadata: Optional metadata.
    """

    task_id: str = ""
    context_id: str = ""
    status: TaskStatus = field(default_factory=TaskStatus)
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TaskStatusUpdateEvent":
        """Deserialize from a camelCase dictionary."""
        return cls(
            task_id=d.get("taskId", ""),
            context_id=d.get("contextId", ""),
            status=TaskStatus.from_dict(d.get("status", {})),
            metadata=d.get("metadata"),
        )


@dataclass
class TaskArtifactUpdateEvent:
    """Event indicating an artifact update on a task.

    Attributes:
        task_id: The task for this artifact.
        context_id: The context the task belongs to.
        artifact: The artifact that was generated or updated.
        append: If True, content appends to a previous artifact with the same ID.
        last_chunk: If True, this is the final chunk of the artifact.
        metadata: Optional metadata.
    """

    task_id: str = ""
    context_id: str = ""
    artifact: Artifact = field(default_factory=Artifact)
    append: bool = False
    last_chunk: bool = False
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TaskArtifactUpdateEvent":
        """Deserialize from a camelCase dictionary."""
        return cls(
            task_id=d.get("taskId", ""),
            context_id=d.get("contextId", ""),
            artifact=Artifact.from_dict(d.get("artifact", {})),
            append=d.get("append", False),
            last_chunk=d.get("lastChunk", False),
            metadata=d.get("metadata"),
        )


@dataclass
class StreamResponse:
    """Wrapper for streaming responses (oneof semantics).

    Exactly one of the four fields should be set.

    Attributes:
        task: A Task object with current state.
        message: A Message object.
        status_update: A TaskStatusUpdateEvent.
        artifact_update: A TaskArtifactUpdateEvent.
    """

    task: Task | None = None
    message: Message | None = None
    status_update: TaskStatusUpdateEvent | None = None
    artifact_update: TaskArtifactUpdateEvent | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        if self.task is not None:
            return {"task": self.task.to_dict()}
        if self.message is not None:
            return {"message": self.message.to_dict()}
        if self.status_update is not None:
            return {"statusUpdate": self.status_update.to_dict()}
        if self.artifact_update is not None:
            return {"artifactUpdate": self.artifact_update.to_dict()}
        return {}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "StreamResponse":
        """Deserialize from a camelCase dictionary."""
        task_d = d.get("task")
        msg_d = d.get("message")
        su_d = d.get("statusUpdate")
        au_d = d.get("artifactUpdate")
        return cls(
            task=Task.from_dict(task_d) if task_d else None,
            message=Message.from_dict(msg_d) if msg_d else None,
            status_update=(TaskStatusUpdateEvent.from_dict(su_d) if su_d else None),
            artifact_update=(TaskArtifactUpdateEvent.from_dict(au_d) if au_d else None),
        )


# --- Request / Configuration types ---


@dataclass
class AuthenticationInfo:
    """Authentication details for push notifications.

    Attributes:
        scheme: HTTP authentication scheme (e.g. "Bearer").
        credentials: The credential string.
    """

    scheme: str = "Bearer"
    credentials: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AuthenticationInfo":
        """Deserialize from a camelCase dictionary."""
        return cls(
            scheme=d.get("scheme", "Bearer"),
            credentials=d.get("credentials"),
        )


@dataclass
class PushNotificationConfig:
    """Configuration for push notification delivery.

    Attributes:
        url: Webhook URL where notifications are sent.
        id: Unique configuration identifier.
        task_id: The associated task ID.
        token: A client-provided token for verification.
        authentication: Authentication info for the webhook.
    """

    url: str = ""
    id: str | None = None
    task_id: str | None = None
    token: str | None = None
    authentication: AuthenticationInfo | None = None

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PushNotificationConfig":
        """Deserialize from a camelCase dictionary."""
        auth = d.get("authentication")
        return cls(
            url=d.get("url", ""),
            id=d.get("id"),
            task_id=d.get("taskId"),
            token=d.get("token"),
            authentication=AuthenticationInfo.from_dict(auth) if auth else None,
        )


@dataclass
class SendMessageConfiguration:
    """Configuration accompanying a SendMessage request.

    Attributes:
        accepted_output_modes: Media types the client can accept.
        push_notification_config: Optional push notification setup.
        history_length: Max number of history messages to return.
        return_immediately: If True, return without waiting for completion.
    """

    accepted_output_modes: list[str] | None = None
    push_notification_config: PushNotificationConfig | None = None
    history_length: int | None = None
    return_immediately: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SendMessageConfiguration":
        """Deserialize from a camelCase dictionary."""
        pnc = d.get("pushNotificationConfig") or d.get("taskPushNotificationConfig")
        return cls(
            accepted_output_modes=d.get("acceptedOutputModes"),
            push_notification_config=(
                PushNotificationConfig.from_dict(pnc) if pnc else None
            ),
            history_length=d.get("historyLength"),
            return_immediately=d.get("returnImmediately", False),
        )


@dataclass
class SendMessageRequest:
    """Request object for the SendMessage / SendStreamingMessage operations.

    Attributes:
        message: The message to send.
        configuration: Optional send configuration.
        metadata: Optional key-value metadata.
    """

    message: Message = field(default_factory=Message)
    configuration: SendMessageConfiguration | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SendMessageRequest":
        """Deserialize from a camelCase dictionary."""
        cfg = d.get("configuration")
        return cls(
            message=Message.from_dict(d.get("message", {})),
            configuration=(SendMessageConfiguration.from_dict(cfg) if cfg else None),
            metadata=d.get("metadata"),
        )


@dataclass
class SendMessageResponse:
    """Response for SendMessage (oneof task | message).

    Attributes:
        task: The task created or updated.
        message: A direct response message.
    """

    task: Task | None = None
    message: Message | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        if self.task is not None:
            return {"task": self.task.to_dict()}
        if self.message is not None:
            return {"message": self.message.to_dict()}
        return {}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SendMessageResponse":
        """Deserialize from a camelCase dictionary."""
        task_d = d.get("task")
        msg_d = d.get("message")
        return cls(
            task=Task.from_dict(task_d) if task_d else None,
            message=Message.from_dict(msg_d) if msg_d else None,
        )


# --- Agent discovery types ---


@dataclass
class AgentProvider:
    """Service provider information for an agent.

    Attributes:
        organization: Provider organization name.
        url: Provider URL.
    """

    organization: str = ""
    url: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AgentProvider":
        """Deserialize from a camelCase dictionary."""
        return cls(
            organization=d.get("organization", ""),
            url=d.get("url", ""),
        )


@dataclass
class AgentExtension:
    """Declaration of a protocol extension supported by an agent.

    Attributes:
        uri: Unique URI identifying the extension.
        description: Human-readable description.
        required: Whether the client must support this extension.
        params: Extension-specific configuration.
    """

    uri: str = ""
    description: str | None = None
    required: bool = False
    params: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AgentExtension":
        """Deserialize from a camelCase dictionary."""
        return cls(
            uri=d.get("uri", ""),
            description=d.get("description"),
            required=d.get("required", False),
            params=d.get("params"),
        )


@dataclass
class AgentCapabilities:
    """Optional capabilities supported by an agent.

    Attributes:
        streaming: Whether the agent supports streaming.
        push_notifications: Whether the agent supports push notifications.
        extensions: List of supported protocol extensions.
        extended_agent_card: Whether an authenticated extended card is available.
    """

    streaming: bool | None = None
    push_notifications: bool | None = None
    extensions: list[AgentExtension] | None = None
    extended_agent_card: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AgentCapabilities":
        """Deserialize from a camelCase dictionary."""
        exts = d.get("extensions")
        return cls(
            streaming=d.get("streaming"),
            push_notifications=d.get("pushNotifications"),
            extensions=([AgentExtension.from_dict(e) for e in exts] if exts else None),
            extended_agent_card=d.get("extendedAgentCard"),
        )


@dataclass
class AgentSkill:
    """A distinct capability that an agent can perform.

    Attributes:
        id: Unique skill identifier.
        name: Human-readable name.
        description: Detailed description.
        tags: Keywords describing the skill.
        examples: Example prompts or scenarios.
        input_modes: Supported input media types (overrides agent defaults).
        output_modes: Supported output media types (overrides agent defaults).
    """

    id: str = ""
    name: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    examples: list[str] | None = None
    input_modes: list[str] | None = None
    output_modes: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AgentSkill":
        """Deserialize from a camelCase dictionary."""
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            description=d.get("description", ""),
            tags=d.get("tags", []),
            examples=d.get("examples"),
            input_modes=d.get("inputModes"),
            output_modes=d.get("outputModes"),
        )


@dataclass
class AgentInterface:
    """A supported protocol interface for an agent.

    Attributes:
        url: The URL where the interface is available.
        protocol_binding: Protocol binding type (JSONRPC, GRPC, HTTP+JSON).
        protocol_version: A2A protocol version (e.g. "1.0").
        tenant: Optional tenant identifier.
    """

    url: str = ""
    protocol_binding: str = "JSONRPC"
    protocol_version: str = "1.0"
    tenant: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AgentInterface":
        """Deserialize from a camelCase dictionary."""
        return cls(
            url=d.get("url", ""),
            protocol_binding=d.get("protocolBinding", "JSONRPC"),
            protocol_version=d.get("protocolVersion", "1.0"),
            tenant=d.get("tenant"),
        )


@dataclass
class AgentCard:
    """Self-describing manifest for an A2A agent.

    Attributes:
        name: Human-readable agent name.
        description: Agent purpose description.
        version: Agent version string.
        supported_interfaces: Ordered list of supported protocol interfaces.
        default_input_modes: Supported input media types.
        default_output_modes: Supported output media types.
        skills: Agent capabilities / skills.
        capabilities: Optional capability flags.
        provider: Service provider info.
        documentation_url: Link to additional docs.
        security_schemes: Security scheme definitions.
        security_requirements: Security requirements.
        icon_url: URL to an agent icon.
    """

    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    supported_interfaces: list[AgentInterface] = field(default_factory=list)
    default_input_modes: list[str] = field(default_factory=lambda: ["text/plain"])
    default_output_modes: list[str] = field(default_factory=lambda: ["text/plain"])
    skills: list[AgentSkill] = field(default_factory=list)
    capabilities: AgentCapabilities | None = None
    provider: AgentProvider | None = None
    documentation_url: str | None = None
    security_schemes: dict[str, Any] | None = None
    security_requirements: list[dict[str, Any]] | None = None
    icon_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a camelCase dictionary."""
        return _serialize(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AgentCard":
        """Deserialize from a camelCase dictionary."""
        interfaces = d.get("supportedInterfaces", [])
        skills = d.get("skills", [])
        caps = d.get("capabilities")
        provider = d.get("provider")
        return cls(
            name=d.get("name", ""),
            description=d.get("description", ""),
            version=d.get("version", "1.0.0"),
            supported_interfaces=[AgentInterface.from_dict(i) for i in interfaces],
            default_input_modes=d.get("defaultInputModes", ["text/plain"]),
            default_output_modes=d.get("defaultOutputModes", ["text/plain"]),
            skills=[AgentSkill.from_dict(s) for s in skills],
            capabilities=(AgentCapabilities.from_dict(caps) if caps else None),
            provider=AgentProvider.from_dict(provider) if provider else None,
            documentation_url=d.get("documentationUrl"),
            security_schemes=d.get("securitySchemes"),
            security_requirements=d.get("securityRequirements"),
            icon_url=d.get("iconUrl"),
        )


# ── 2. JSON-RPC 2.0 Layer ──────────────────────────────────────────────────


class A2AError(JSONRPCException):
    """Base class for A2A protocol errors."""

    code: int = INTERNAL_ERROR
    default_message: str = "Internal error"

    def __init__(self, message: str | None = None, data: Any = None):
        self.rpc_message = message or self.default_message
        self.data = data
        super().__init__(
            JSONRPCError(code=self.code, message=self.rpc_message, data=self.data)
        )


class TaskNotFoundError(A2AError):
    """The specified task ID does not exist or is not accessible."""

    code = -32001
    default_message = "Task not found"


class TaskNotCancelableError(A2AError):
    """The task is not in a cancelable state."""

    code = -32002
    default_message = "Task not cancelable"


class PushNotificationNotSupportedError(A2AError):
    """Push notification features are not supported by this agent."""

    code = -32003
    default_message = "Push notifications not supported"


class UnsupportedOperationError(A2AError):
    """The requested operation is not supported."""

    code = -32004
    default_message = "Unsupported operation"


class ContentTypeNotSupportedError(A2AError):
    """A media type in the request is not supported."""

    code = -32005
    default_message = "Content type not supported"


class InvalidAgentResponseError(A2AError):
    """The agent returned a response that does not conform to the spec."""

    code = -32006
    default_message = "Invalid agent response"


# ── 3. SSE (Server-Sent Events) Utilities ──────────────────────────────────


def sse_encode(data: Any) -> bytes:
    """Encode *data* as a single SSE ``data:`` frame.

    Args:
        data: JSON-serializable object.

    Returns:
        UTF-8 encoded SSE frame bytes (``data: ...\\n\\n``).
    """
    payload = json.dumps(data, separators=(",", ":"))
    return f"data: {payload}\n\n".encode("utf-8")


def sse_decode_stream(
    response: http.client.HTTPResponse,
) -> Iterator[dict[str, Any]]:
    """Parse an SSE stream from an ``http.client.HTTPResponse``.

    Reads lines from the response, extracts ``data:`` fields, and yields
    parsed JSON objects.  Handles chunked transfer encoding transparently
    because ``http.client`` decodes it for us.

    Args:
        response: An open HTTP response with ``Content-Type: text/event-stream``.

    Yields:
        Parsed JSON dictionaries for each SSE ``data:`` event.
    """
    buf = b""
    while True:
        chunk = response.read(4096)
        if not chunk:
            break
        buf += chunk
        while b"\n" in buf:
            line_bytes, buf = buf.split(b"\n", 1)
            line = line_bytes.decode("utf-8", errors="replace").rstrip("\r")
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str.strip():
                    try:
                        yield json.loads(data_str)
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse SSE data: %s", data_str)
            # Ignore comments (lines starting with ':'), event/id/retry fields.
    # Handle any remaining data in buffer
    if buf:
        line = buf.decode("utf-8", errors="replace").rstrip("\r\n")
        if line.startswith("data: ") and line[6:].strip():
            try:
                yield json.loads(line[6:])
            except json.JSONDecodeError:
                pass


# ── 4. A2A Client ──────────────────────────────────────────────────────────


class A2AClient:
    """HTTP client for the A2A JSON-RPC protocol binding.

    Uses only ``urllib.request`` and ``http.client`` from the standard library.

    Args:
        agent_card_url: Full URL to the agent card JSON endpoint.  If not
            provided, it is derived from *base_url*.
        base_url: The base JSON-RPC endpoint URL.  If not provided, it is
            derived from the agent card once fetched.
        headers: Extra HTTP headers to include in every request.

    Example::

        client = A2AClient(base_url="http://localhost:8000")
        card = client.get_agent_card()
        resp = client.send_message("Hello, agent!")
    """

    def __init__(
        self,
        agent_card_url: str | None = None,
        base_url: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        self._base_url = base_url.rstrip("/") if base_url else None
        self._agent_card_url = agent_card_url
        self._headers = headers or {}
        self._agent_card: AgentCard | None = None

    # --- Agent Card ---

    def get_agent_card(self) -> AgentCard:
        """Fetch and cache the agent card.

        Returns:
            The ``AgentCard`` published by the remote agent.

        Raises:
            urllib.error.URLError: On network failure.
        """
        if self._agent_card is not None:
            return self._agent_card

        url = self._agent_card_url
        if url is None:
            if self._base_url is None:
                raise ValueError("Either agent_card_url or base_url must be provided")
            parsed = urllib.parse.urlparse(self._base_url)
            url = f"{parsed.scheme}://{parsed.netloc}/.well-known/agent-card.json"

        req = urllib.request.Request(url, headers=self._headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        self._agent_card = AgentCard.from_dict(data)

        # Derive base_url from card if not set
        if self._base_url is None and self._agent_card.supported_interfaces:
            self._base_url = self._agent_card.supported_interfaces[0].url
        return self._agent_card

    # --- Low-level RPC ---

    def _rpc_url(self) -> str:
        """Return the JSON-RPC endpoint URL."""
        if self._base_url is None:
            raise ValueError("base_url is not configured")
        return self._base_url

    def _make_rpc_request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        request_id: Union[str, int, None] = None,
    ) -> JSONRPCResponse:
        """Send a JSON-RPC request and return the parsed response.

        Args:
            method: JSON-RPC method name.
            params: Method parameters.
            request_id: Optional request ID (defaults to auto-generated int).

        Returns:
            Parsed ``JSONRPCResponse``.
        """
        if request_id is None:
            request_id = id(params) & 0xFFFFFF
        rpc_req = JSONRPCRequest(method=method, params=params, id=request_id)
        body = json.dumps(rpc_req.to_dict()).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self._headers,
        }
        req = urllib.request.Request(
            self._rpc_url(), data=body, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
        rpc_resp = JSONRPCResponse(
            id=resp_data.get("id"),
            jsonrpc=resp_data.get("jsonrpc", "2.0"),
        )
        if "error" in resp_data and resp_data["error"] is not None:
            err = resp_data["error"]
            rpc_resp.error = JSONRPCError(
                code=err.get("code", -32603),
                message=err.get("message", "Unknown error"),
                data=err.get("data"),
            )
        else:
            rpc_resp.result = resp_data.get("result")
        return rpc_resp

    def _make_sse_request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        request_id: Union[str, int, None] = None,
    ) -> Iterator[dict[str, Any]]:
        """Send a JSON-RPC request and stream SSE responses.

        Uses ``http.client`` for chunked/streaming reads.

        Args:
            method: JSON-RPC method name.
            params: Method parameters.
            request_id: Optional request ID.

        Yields:
            Parsed JSON dictionaries from each SSE ``data:`` event.
        """
        if request_id is None:
            request_id = id(params) & 0xFFFFFF
        rpc_req = JSONRPCRequest(method=method, params=params, id=request_id)
        body = json.dumps(rpc_req.to_dict()).encode("utf-8")
        parsed = urllib.parse.urlparse(self._rpc_url())
        host = parsed.hostname or "localhost"

        if parsed.scheme == "https":
            conn = http.client.HTTPSConnection(host, parsed.port)
        else:
            conn = http.client.HTTPConnection(host, parsed.port)

        path = parsed.path or "/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            **self._headers,
        }
        try:
            conn.request("POST", path, body=body, headers=headers)
            response = conn.getresponse()
            yield from sse_decode_stream(response)
        finally:
            conn.close()

    # --- High-level API ---

    def send_message(
        self,
        text: str,
        *,
        task_id: str | None = None,
        context_id: str | None = None,
        configuration: SendMessageConfiguration | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SendMessageResponse:
        """Send a text message to the agent (blocking).

        Args:
            text: The message text.
            task_id: Optional task to continue.
            context_id: Optional context to associate with.
            configuration: Optional send configuration.
            metadata: Optional request metadata.

        Returns:
            A ``SendMessageResponse`` containing either a Task or Message.
        """
        msg = Message(
            role=Role.USER,
            parts=[Part(text=text)],
            task_id=task_id,
            context_id=context_id,
        )
        req = SendMessageRequest(
            message=msg,
            configuration=configuration,
            metadata=metadata,
        )
        rpc_resp = self._make_rpc_request("SendMessage", req.to_dict())
        if rpc_resp.error:
            raise A2AError(rpc_resp.error.message, rpc_resp.error.data)
        return SendMessageResponse.from_dict(rpc_resp.result or {})

    def send_message_streaming(
        self,
        text: str,
        *,
        task_id: str | None = None,
        context_id: str | None = None,
        configuration: SendMessageConfiguration | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Iterator[StreamResponse]:
        """Send a text message and stream responses via SSE.

        Args:
            text: The message text.
            task_id: Optional task to continue.
            context_id: Optional context to associate with.
            configuration: Optional send configuration.
            metadata: Optional request metadata.

        Yields:
            ``StreamResponse`` objects as they arrive.
        """
        msg = Message(
            role=Role.USER,
            parts=[Part(text=text)],
            task_id=task_id,
            context_id=context_id,
        )
        req = SendMessageRequest(
            message=msg,
            configuration=configuration,
            metadata=metadata,
        )
        for event in self._make_sse_request("SendStreamingMessage", req.to_dict()):
            result = event.get("result")
            if result:
                yield StreamResponse.from_dict(result)

    def get_task(
        self,
        task_id: str,
        *,
        history_length: int | None = None,
    ) -> Task:
        """Retrieve the current state of a task.

        Args:
            task_id: The task identifier.
            history_length: Optional max number of history messages to return.

        Returns:
            The current ``Task`` object.
        """
        params: dict[str, Any] = {"id": task_id}
        if history_length is not None:
            params["historyLength"] = history_length
        rpc_resp = self._make_rpc_request("GetTask", params)
        if rpc_resp.error:
            raise A2AError(rpc_resp.error.message, rpc_resp.error.data)
        return Task.from_dict(rpc_resp.result or {})

    def list_tasks(
        self,
        *,
        context_id: str | None = None,
        status: TaskState | None = None,
        page_size: int | None = None,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """List tasks with optional filtering.

        Args:
            context_id: Filter by context.
            status: Filter by task state.
            page_size: Maximum results per page.
            page_token: Cursor for pagination.

        Returns:
            Raw result dictionary with ``tasks``, ``nextPageToken``, etc.
        """
        params: dict[str, Any] = {}
        if context_id:
            params["contextId"] = context_id
        if status:
            params["status"] = status.value
        if page_size is not None:
            params["pageSize"] = page_size
        if page_token:
            params["pageToken"] = page_token
        rpc_resp = self._make_rpc_request("ListTasks", params)
        if rpc_resp.error:
            raise A2AError(rpc_resp.error.message, rpc_resp.error.data)
        return rpc_resp.result or {}

    def cancel_task(self, task_id: str) -> Task:
        """Request cancellation of a task.

        Args:
            task_id: The task identifier.

        Returns:
            The updated ``Task`` with cancellation status.
        """
        rpc_resp = self._make_rpc_request("CancelTask", {"id": task_id})
        if rpc_resp.error:
            raise A2AError(rpc_resp.error.message, rpc_resp.error.data)
        return Task.from_dict(rpc_resp.result or {})


# ── 5. A2A Server ──────────────────────────────────────────────────────────


class A2ARequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for the A2A JSON-RPC protocol binding.

    Subclass this and assign ``dispatcher`` and ``agent_card`` on the server
    to customise behavior, or use ``A2AServer`` which wires everything up.
    """

    # Suppress default stderr logging from BaseHTTPRequestHandler
    def log_message(self, format: str, *args: Any) -> None:
        logger.debug(format, *args)

    @property
    def _dispatcher(self) -> JSONRPCDispatcher:
        return self.server.dispatcher  # type: ignore[attr-defined]  # ty: ignore[unresolved-attribute]

    @property
    def _agent_card(self) -> AgentCard:
        return self.server.agent_card  # type: ignore[attr-defined]  # ty: ignore[unresolved-attribute]

    # --- GET handlers ---

    def do_GET(self) -> None:
        """Handle GET requests (agent card endpoint)."""
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/.well-known/agent-card.json":
            self._serve_agent_card()
        else:
            self.send_error(404, "Not Found")

    def _serve_agent_card(self) -> None:
        """Respond with the agent card JSON."""
        body = json.dumps(self._agent_card.to_dict(), indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    # --- POST handlers ---

    def do_POST(self) -> None:
        """Handle POST requests (JSON-RPC endpoint)."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._send_json_error(400, "Empty request body")
            return

        raw = self.rfile.read(content_length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            self._send_jsonrpc_error(
                None,
                JSONRPCError(code=PARSE_ERROR, message=f"Parse error: {exc}"),
            )
            return

        rpc_req = JSONRPCRequest.from_dict(data)

        # Determine if the client wants SSE
        accept = self.headers.get("Accept", "")
        wants_sse = "text/event-stream" in accept

        result = self._dispatcher.dispatch(rpc_req)

        if hasattr(result, "__next__"):
            # Streaming response — result is an Iterator here
            stream: Iterator[JSONRPCResponse] = result  # type: ignore[assignment]  # ty: ignore[invalid-assignment]
            if wants_sse:
                self._send_sse_stream(stream)
            else:
                # Collect all into a list and return as a single JSON-RPC
                # response with the last item.
                last: JSONRPCResponse | None = None
                for item in stream:
                    last = item
                if last is not None:
                    self._send_jsonrpc_response(last)
                else:
                    self._send_jsonrpc_response(
                        JSONRPCResponse.success(rpc_req.id, None)
                    )
        else:
            self._send_jsonrpc_response(result)

    def _send_jsonrpc_response(self, response: JSONRPCResponse) -> None:
        """Write a single JSON-RPC response."""
        body = json.dumps(response.to_dict()).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_jsonrpc_error(self, request_id: Any, error: JSONRPCError) -> None:
        """Write a JSON-RPC error response."""
        resp = JSONRPCResponse(id=request_id, error=error)
        self._send_jsonrpc_response(resp)

    def _send_sse_stream(self, responses: Iterator[JSONRPCResponse]) -> None:
        """Write a stream of JSON-RPC responses as SSE events."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            for resp in responses:
                frame = sse_encode(resp.to_dict())
                self.wfile.write(frame)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            logger.debug("SSE client disconnected")

    def _send_json_error(self, status: int, message: str) -> None:
        """Send a plain JSON error (non-RPC)."""
        body = json.dumps({"error": message}).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # --- OPTIONS (CORS preflight) ---

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization, Accept, A2A-Version, A2A-Extensions",
        )
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()


class A2AServer:
    """A2A protocol server using the JSON-RPC binding over HTTP.

    This wraps Python's ``http.server.HTTPServer`` with threading support
    and provides a ``JSONRPCDispatcher`` for registering method handlers.

    Args:
        host: Bind address (default ``"0.0.0.0"``).
        port: Bind port (default ``8000``).
        agent_card: The ``AgentCard`` to serve.

    Example::

        card = AgentCard(name="Echo Agent", description="Echoes messages")
        server = A2AServer(port=9000, agent_card=card)

        @server.dispatcher.register("SendMessage")
        def handle_send(params):
            req = SendMessageRequest.from_dict(params)
            text = req.message.parts[0].text or ""
            task = Task(
                status=TaskStatus(state=TaskState.COMPLETED),
                artifacts=[Artifact(parts=[Part(text=f"Echo: {text}")])],
            )
            return SendMessageResponse(task=task).to_dict()

        server.start()
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        agent_card: AgentCard | None = None,
    ):
        self.host = host
        self.port = port
        self.dispatcher = JSONRPCDispatcher()
        self.agent_card = agent_card or AgentCard()
        self._httpd: http.server.HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def _create_server(self) -> http.server.HTTPServer:
        """Create and configure the HTTP server instance."""

        class _ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
            daemon_threads = True

        server = _ThreadedHTTPServer((self.host, self.port), A2ARequestHandler)
        server.dispatcher = self.dispatcher  # type: ignore[attr-defined]  # ty: ignore[unresolved-attribute]
        server.agent_card = self.agent_card  # type: ignore[attr-defined]  # ty: ignore[unresolved-attribute]
        return server

    def start(self, blocking: bool = True) -> None:
        """Start serving requests.

        Args:
            blocking: If True, block the calling thread. If False, serve in
                a background daemon thread.
        """
        self._httpd = self._create_server()
        logger.info("A2A server starting on %s:%d", self.host, self.port)
        if blocking:
            try:
                self._httpd.serve_forever()
            except KeyboardInterrupt:
                self.stop()
        else:
            self._thread = threading.Thread(
                target=self._httpd.serve_forever, daemon=True
            )
            self._thread.start()

    def stop(self) -> None:
        """Shut down the server."""
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            logger.info("A2A server stopped")

    @property
    def url(self) -> str:
        """Return the base URL of the running server."""
        return f"http://{self.host}:{self.port}"


# ── 6. Task Management ─────────────────────────────────────────────────────


class TaskStore:
    """Thread-safe in-memory task store backed by a dictionary.

    Provides CRUD operations for ``Task`` objects keyed by their ``id``.

    Example::

        store = TaskStore()
        task = Task(status=TaskStatus(state=TaskState.SUBMITTED))
        store.save(task)
        retrieved = store.get(task.id)
    """

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._lock = threading.Lock()

    def save(self, task: Task) -> None:
        """Save or update a task in the store.

        Args:
            task: The task to save.
        """
        with self._lock:
            self._tasks[task.id] = copy.deepcopy(task)

    def get(self, task_id: str) -> Task | None:
        """Retrieve a task by ID.

        Args:
            task_id: The task identifier.

        Returns:
            A deep copy of the task, or ``None`` if not found.
        """
        with self._lock:
            task = self._tasks.get(task_id)
            return copy.deepcopy(task) if task else None

    def delete(self, task_id: str) -> bool:
        """Remove a task from the store.

        Args:
            task_id: The task identifier.

        Returns:
            True if the task was deleted, False if it was not found.
        """
        with self._lock:
            return self._tasks.pop(task_id, None) is not None

    def list_tasks(
        self,
        *,
        context_id: str | None = None,
        status: TaskState | None = None,
        page_size: int = 50,
        page_token: str | None = None,
    ) -> tuple[list[Task], str, int]:
        """List tasks with optional filtering and pagination.

        Args:
            context_id: Filter by context ID.
            status: Filter by task state.
            page_size: Maximum number of tasks to return.
            page_token: Opaque cursor (task ID) for pagination.

        Returns:
            Tuple of (tasks, next_page_token, total_count).
        """
        with self._lock:
            all_tasks = list(self._tasks.values())

        # Filter
        if context_id:
            all_tasks = [t for t in all_tasks if t.context_id == context_id]
        if status:
            all_tasks = [t for t in all_tasks if t.status.state == status]

        # Sort by timestamp descending
        all_tasks.sort(
            key=lambda t: t.status.timestamp or "",
            reverse=True,
        )

        total = len(all_tasks)

        # Pagination
        start_idx = 0
        if page_token:
            for i, t in enumerate(all_tasks):
                if t.id == page_token:
                    start_idx = i + 1
                    break

        page = all_tasks[start_idx : start_idx + page_size]
        next_token = ""
        if start_idx + page_size < total:
            next_token = page[-1].id if page else ""

        return [copy.deepcopy(t) for t in page], next_token, total


class TaskManager:
    """High-level task lifecycle manager built on top of ``TaskStore``.

    Manages task creation, state transitions, artifact generation, and
    provides event callbacks for streaming.

    Args:
        store: The ``TaskStore`` to use. Creates one if not provided.

    Example::

        manager = TaskManager()
        task = manager.create_task(message)
        manager.update_status(task.id, TaskState.WORKING)
        manager.add_artifact(task.id, Artifact(parts=[Part(text="result")]))
        manager.update_status(task.id, TaskState.COMPLETED)
    """

    # Valid state transitions (from -> set of allowed to-states)
    _TRANSITIONS: dict[TaskState, set] = {
        TaskState.UNSPECIFIED: {TaskState.SUBMITTED},
        TaskState.SUBMITTED: {
            TaskState.WORKING,
            TaskState.COMPLETED,
            TaskState.FAILED,
            TaskState.CANCELED,
            TaskState.REJECTED,
        },
        TaskState.WORKING: {
            TaskState.COMPLETED,
            TaskState.FAILED,
            TaskState.CANCELED,
            TaskState.INPUT_REQUIRED,
            TaskState.AUTH_REQUIRED,
        },
        TaskState.INPUT_REQUIRED: {
            TaskState.WORKING,
            TaskState.COMPLETED,
            TaskState.FAILED,
            TaskState.CANCELED,
        },
        TaskState.AUTH_REQUIRED: {
            TaskState.WORKING,
            TaskState.COMPLETED,
            TaskState.FAILED,
            TaskState.CANCELED,
        },
        # Terminal states allow no transitions
        TaskState.COMPLETED: set(),
        TaskState.FAILED: set(),
        TaskState.CANCELED: set(),
        TaskState.REJECTED: set(),
    }

    def __init__(self, store: TaskStore | None = None):
        self.store = store or TaskStore()
        self._listeners: dict[str, list[Callable[[StreamResponse], None]]] = {}
        self._lock = threading.Lock()

    def create_task(
        self,
        message: Message,
        *,
        context_id: str | None = None,
    ) -> Task:
        """Create a new task from an incoming message.

        Args:
            message: The initiating message.
            context_id: Optional context to associate the task with.

        Returns:
            The newly created ``Task`` in SUBMITTED state.
        """
        task = Task(
            id=str(uuid.uuid4()),
            context_id=context_id or str(uuid.uuid4()),
            status=TaskStatus(state=TaskState.SUBMITTED),
            history=[message],
        )
        self.store.save(task)
        return task

    def get_task(self, task_id: str) -> Task:
        """Retrieve a task, raising ``TaskNotFoundError`` if absent.

        Args:
            task_id: The task identifier.

        Returns:
            The ``Task`` object.

        Raises:
            TaskNotFoundError: If the task does not exist.
        """
        task = self.store.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task {task_id!r} not found")
        return task

    def update_status(
        self,
        task_id: str,
        state: TaskState,
        *,
        status_message: Message | None = None,
    ) -> Task:
        """Transition a task to a new state.

        Args:
            task_id: The task identifier.
            state: The target state.
            status_message: Optional message to attach to the status.

        Returns:
            The updated ``Task``.

        Raises:
            TaskNotFoundError: If the task does not exist.
            ValueError: If the state transition is not valid.
        """
        task = self.get_task(task_id)
        current = task.status.state
        allowed = self._TRANSITIONS.get(current, set())
        if state not in allowed:
            raise ValueError(
                f"Invalid transition from {current.value} to {state.value}"
            )
        task.status = TaskStatus(
            state=state, message=status_message, timestamp=_now_iso()
        )
        self.store.save(task)

        # Notify listeners
        event = StreamResponse(
            status_update=TaskStatusUpdateEvent(
                task_id=task.id,
                context_id=task.context_id or "",
                status=task.status,
            )
        )
        self._notify(task_id, event)
        return task

    def add_artifact(
        self,
        task_id: str,
        artifact: Artifact,
        *,
        append: bool = False,
        last_chunk: bool = True,
    ) -> Task:
        """Add an artifact to a task.

        Args:
            task_id: The task identifier.
            artifact: The artifact to add.
            append: If True, append to an existing artifact with the same ID.
            last_chunk: If True, this is the final chunk of the artifact.

        Returns:
            The updated ``Task``.

        Raises:
            TaskNotFoundError: If the task does not exist.
        """
        task = self.get_task(task_id)
        if task.artifacts is None:
            task.artifacts = []

        if append:
            # Find and extend existing artifact
            for existing in task.artifacts:
                if existing.artifact_id == artifact.artifact_id:
                    existing.parts.extend(artifact.parts)
                    break
            else:
                task.artifacts.append(artifact)
        else:
            task.artifacts.append(artifact)

        self.store.save(task)

        # Notify listeners
        event = StreamResponse(
            artifact_update=TaskArtifactUpdateEvent(
                task_id=task.id,
                context_id=task.context_id or "",
                artifact=artifact,
                append=append,
                last_chunk=last_chunk,
            )
        )
        self._notify(task_id, event)
        return task

    def cancel_task(self, task_id: str) -> Task:
        """Cancel a task.

        Args:
            task_id: The task identifier.

        Returns:
            The updated ``Task`` with CANCELED state.

        Raises:
            TaskNotFoundError: If the task does not exist.
            TaskNotCancelableError: If the task is in a terminal state.
        """
        task = self.get_task(task_id)
        if task.status.state.is_terminal():
            raise TaskNotCancelableError(
                f"Task {task_id!r} is in terminal state {task.status.state.value}"
            )
        return self.update_status(task_id, TaskState.CANCELED)

    def subscribe(
        self, task_id: str, callback: Callable[[StreamResponse], None]
    ) -> Callable[[], None]:
        """Subscribe to streaming events for a task.

        Args:
            task_id: The task identifier.
            callback: Function called with each ``StreamResponse`` event.

        Returns:
            An unsubscribe function that removes the callback.
        """
        with self._lock:
            if task_id not in self._listeners:
                self._listeners[task_id] = []
            self._listeners[task_id].append(callback)

        def unsubscribe() -> None:
            with self._lock:
                listeners = self._listeners.get(task_id, [])
                if callback in listeners:
                    listeners.remove(callback)

        return unsubscribe

    def _notify(self, task_id: str, event: StreamResponse) -> None:
        """Notify all subscribers of an event for a task."""
        with self._lock:
            listeners = list(self._listeners.get(task_id, []))
        for cb in listeners:
            try:
                cb(event)
            except Exception:
                logger.exception("Error in task listener for %s", task_id)


# ── Main: Usage Example ────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # -- Build an example agent card --
    card = AgentCard(
        name="Echo Agent",
        description="A simple agent that echoes messages back.",
        version="1.0.0",
        supported_interfaces=[
            AgentInterface(
                url="http://localhost:8000",
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            ),
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="echo",
                name="Echo",
                description="Echoes back the user message.",
                tags=["echo", "test"],
                examples=["Say hello"],
            ),
        ],
    )

    # -- Set up the server --
    server = A2AServer(host="127.0.0.1", port=8000, agent_card=card)
    task_manager = TaskManager()

    @server.dispatcher.register("SendMessage")
    def handle_send_message(params: dict[str, Any]) -> dict[str, Any]:
        """Handle a SendMessage request by echoing the input."""
        req = SendMessageRequest.from_dict(params)
        text = ""
        for part in req.message.parts:
            if part.text:
                text += part.text

        task = task_manager.create_task(req.message, context_id=req.message.context_id)
        task_manager.update_status(task.id, TaskState.WORKING)
        task_manager.add_artifact(
            task.id,
            Artifact(
                name="echo-response",
                parts=[Part(text=f"Echo: {text}")],
            ),
        )
        task = task_manager.update_status(task.id, TaskState.COMPLETED)
        return SendMessageResponse(task=task).to_dict()

    @server.dispatcher.register("SendStreamingMessage")
    def handle_stream_message(
        params: dict[str, Any],
    ) -> Iterator[dict[str, Any]]:
        """Handle a SendStreamingMessage by streaming token-by-token."""
        req = SendMessageRequest.from_dict(params)
        text = ""
        for part in req.message.parts:
            if part.text:
                text += part.text

        task = task_manager.create_task(req.message, context_id=req.message.context_id)
        # Yield initial task
        yield StreamResponse(task=task).to_dict()

        task_manager.update_status(task.id, TaskState.WORKING)
        yield StreamResponse(
            status_update=TaskStatusUpdateEvent(
                task_id=task.id,
                context_id=task.context_id or "",
                status=TaskStatus(state=TaskState.WORKING),
            )
        ).to_dict()

        # Yield artifact
        artifact = Artifact(
            name="echo-response",
            parts=[Part(text=f"Echo: {text}")],
        )
        task_manager.add_artifact(task.id, artifact)
        yield StreamResponse(
            artifact_update=TaskArtifactUpdateEvent(
                task_id=task.id,
                context_id=task.context_id or "",
                artifact=artifact,
                last_chunk=True,
            )
        ).to_dict()

        # Complete
        task_manager.update_status(task.id, TaskState.COMPLETED)
        yield StreamResponse(
            status_update=TaskStatusUpdateEvent(
                task_id=task.id,
                context_id=task.context_id or "",
                status=TaskStatus(state=TaskState.COMPLETED),
            )
        ).to_dict()

    @server.dispatcher.register("GetTask")
    def handle_get_task(params: dict[str, Any]) -> dict[str, Any]:
        """Handle a GetTask request."""
        task_id = params.get("id", "")
        task = task_manager.get_task(task_id)
        return task.to_dict()

    @server.dispatcher.register("CancelTask")
    def handle_cancel_task(params: dict[str, Any]) -> dict[str, Any]:
        """Handle a CancelTask request."""
        task_id = params.get("id", "")
        task = task_manager.cancel_task(task_id)
        return task.to_dict()

    # -- Run --
    if len(sys.argv) > 1 and sys.argv[1] == "client":
        # Client mode: connect to an already-running server
        print("=== A2A Client Demo ===\n")
        client = A2AClient(base_url="http://127.0.0.1:8000")

        # Fetch agent card
        agent_card = client.get_agent_card()
        print(f"Agent: {agent_card.name}")
        print(f"Description: {agent_card.description}\n")

        # Send a blocking message
        print("--- Blocking SendMessage ---")
        resp = client.send_message("Hello, A2A world!")
        if resp.task:
            print(f"Task ID: {resp.task.id}")
            print(f"State: {resp.task.status.state.value}")
            if resp.task.artifacts:
                for art in resp.task.artifacts:
                    for p in art.parts:
                        if p.text:
                            print(f"Artifact: {p.text}")

        # Send a streaming message
        print("\n--- Streaming SendStreamingMessage ---")
        for event in client.send_message_streaming("Stream this message!"):
            if event.task:
                print(f"[stream] Task: {event.task.id}")
            if event.status_update:
                print(f"[stream] Status: {event.status_update.status.state.value}")
            if event.artifact_update:
                for p in event.artifact_update.artifact.parts:
                    if p.text:
                        print(f"[stream] Artifact: {p.text}")
    else:
        # Server mode
        print("=== A2A Echo Server ===")
        print("Listening on http://127.0.0.1:8000")
        print("Agent card at http://127.0.0.1:8000/.well-known/agent-card.json")
        print("Run with 'client' argument to test the client.\n")
        server.start(blocking=True)
