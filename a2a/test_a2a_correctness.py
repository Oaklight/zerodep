"""Correctness tests: zerodep a2a vs a2a-protocol."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from a2a import (
    A2AError,
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentProvider,
    AgentSkill,
    Artifact,
    JSONRPCRequest,
    JSONRPCResponse,
    Message,
    Part,
    Role,
    SendMessageConfiguration,
    SendMessageRequest,
    SendMessageResponse,
    StreamResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskManager,
    TaskNotCancelableError,
    TaskNotFoundError,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TaskStore,
    _serialize,
    sse_encode,
)

# Reference library (skip if not installed)
a2a_ref = pytest.importorskip(
    "a2a_protocol.dataclass", reason="a2a-protocol not installed"
)

# ── Helpers ──


def _keys_are_camel(d: dict) -> bool:
    """Return True if all keys in a nested dict are camelCase (no underscores)."""
    for key in d:
        if "_" in key:
            return False
        val = d[key]
        if isinstance(val, dict) and not _keys_are_camel(val):
            return False
        if isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and not _keys_are_camel(item):
                    return False
    return True


# ── Round-trip serialization ──


class TestRoundTripPart:
    """Test Part serialization round-trip."""

    @pytest.mark.parametrize(
        "kwargs",
        [
            pytest.param({"text": "hello"}, id="text"),
            pytest.param({"raw": "base64data"}, id="raw"),
            pytest.param({"url": "https://example.com/file.png"}, id="url"),
            pytest.param({"data": {"key": "value"}}, id="data"),
            pytest.param(
                {"text": "hello", "metadata": {"k": "v"}, "filename": "test.txt"},
                id="text_with_metadata",
            ),
            pytest.param(
                {"text": "hello", "media_type": "text/plain"},
                id="text_with_media_type",
            ),
        ],
    )
    def test_round_trip(self, kwargs):
        part = Part(**kwargs)
        d = part.to_dict()
        restored = Part.from_dict(d)
        assert restored.to_dict() == d


class TestRoundTripMessage:
    """Test Message serialization round-trip."""

    def test_simple(self):
        msg = Message(
            message_id="msg-1",
            role=Role.USER,
            parts=[Part(text="hello")],
        )
        d = msg.to_dict()
        restored = Message.from_dict(d)
        assert restored.message_id == msg.message_id
        assert restored.role == msg.role
        assert len(restored.parts) == 1
        assert restored.parts[0].text == "hello"

    def test_agent_message(self):
        msg = Message(
            message_id="msg-2",
            role=Role.AGENT,
            parts=[Part(text="response")],
            context_id="ctx-1",
            task_id="task-1",
        )
        d = msg.to_dict()
        restored = Message.from_dict(d)
        assert restored.role == Role.AGENT
        assert restored.context_id == "ctx-1"
        assert restored.task_id == "task-1"

    def test_with_extensions(self):
        msg = Message(
            message_id="msg-3",
            role=Role.USER,
            parts=[Part(text="hello")],
            extensions=["urn:ext:custom"],
            reference_task_ids=["task-a", "task-b"],
        )
        d = msg.to_dict()
        restored = Message.from_dict(d)
        assert restored.extensions == ["urn:ext:custom"]
        assert restored.reference_task_ids == ["task-a", "task-b"]


class TestRoundTripArtifact:
    """Test Artifact serialization round-trip."""

    def test_simple(self):
        art = Artifact(
            artifact_id="art-1",
            parts=[Part(text="content")],
            name="result",
        )
        d = art.to_dict()
        restored = Artifact.from_dict(d)
        assert restored.artifact_id == "art-1"
        assert restored.name == "result"
        assert len(restored.parts) == 1

    def test_with_description(self):
        art = Artifact(
            artifact_id="art-2",
            parts=[Part(text="data"), Part(raw="base64")],
            name="output",
            description="Generated output",
        )
        d = art.to_dict()
        restored = Artifact.from_dict(d)
        assert restored.description == "Generated output"
        assert len(restored.parts) == 2


class TestRoundTripTaskStatus:
    """Test TaskStatus serialization round-trip."""

    @pytest.mark.parametrize(
        "state",
        [
            pytest.param(TaskState.SUBMITTED, id="submitted"),
            pytest.param(TaskState.WORKING, id="working"),
            pytest.param(TaskState.COMPLETED, id="completed"),
            pytest.param(TaskState.FAILED, id="failed"),
            pytest.param(TaskState.CANCELED, id="canceled"),
            pytest.param(TaskState.INPUT_REQUIRED, id="input_required"),
            pytest.param(TaskState.REJECTED, id="rejected"),
            pytest.param(TaskState.AUTH_REQUIRED, id="auth_required"),
        ],
    )
    def test_round_trip(self, state):
        ts = TaskStatus(state=state, timestamp="2026-01-01T00:00:00.000Z")
        d = ts.to_dict()
        restored = TaskStatus.from_dict(d)
        assert restored.state == state
        assert restored.timestamp == "2026-01-01T00:00:00.000Z"

    def test_with_message(self):
        ts = TaskStatus(
            state=TaskState.WORKING,
            message=Message(
                message_id="status-msg",
                role=Role.AGENT,
                parts=[Part(text="Processing...")],
            ),
            timestamp="2026-01-01T00:00:00.000Z",
        )
        d = ts.to_dict()
        restored = TaskStatus.from_dict(d)
        assert restored.message is not None
        assert restored.message.parts[0].text == "Processing..."


class TestRoundTripTask:
    """Test Task serialization round-trip."""

    def test_minimal(self):
        task = Task(
            id="task-1",
            status=TaskStatus(
                state=TaskState.SUBMITTED,
                timestamp="2026-01-01T00:00:00.000Z",
            ),
        )
        d = task.to_dict()
        restored = Task.from_dict(d)
        assert restored.id == "task-1"
        assert restored.status.state == TaskState.SUBMITTED

    def test_with_history_and_artifacts(self):
        task = Task(
            id="task-2",
            status=TaskStatus(
                state=TaskState.COMPLETED,
                timestamp="2026-01-01T00:00:00.000Z",
            ),
            context_id="ctx-1",
            history=[
                Message(
                    message_id="m1",
                    role=Role.USER,
                    parts=[Part(text="Do something")],
                ),
                Message(
                    message_id="m2",
                    role=Role.AGENT,
                    parts=[Part(text="Done")],
                ),
            ],
            artifacts=[
                Artifact(
                    artifact_id="a1",
                    parts=[Part(text="result")],
                    name="output",
                ),
            ],
        )
        d = task.to_dict()
        restored = Task.from_dict(d)
        assert restored.context_id == "ctx-1"
        assert len(restored.history) == 2
        assert len(restored.artifacts) == 1
        assert restored.history[0].role == Role.USER
        assert restored.artifacts[0].name == "output"


class TestRoundTripAgentCard:
    """Test AgentCard serialization round-trip."""

    def test_minimal(self):
        card = AgentCard(name="TestAgent", version="1.0.0")
        d = card.to_dict()
        restored = AgentCard.from_dict(d)
        assert restored.name == "TestAgent"
        assert restored.version == "1.0.0"

    def test_full(self):
        card = AgentCard(
            name="FullAgent",
            description="A fully-featured agent",
            version="2.0.0",
            supported_interfaces=[
                AgentInterface(
                    url="http://localhost:8000",
                    protocol_binding="JSONRPC",
                    protocol_version="1.0",
                ),
            ],
            default_input_modes=["text/plain", "application/json"],
            default_output_modes=["text/plain"],
            skills=[
                AgentSkill(
                    id="s1",
                    name="Echo",
                    description="Echoes input",
                    tags=["echo"],
                    examples=["Say hello"],
                ),
            ],
            capabilities=AgentCapabilities(streaming=True, push_notifications=False),
            provider=AgentProvider(organization="TestOrg", url="https://test.org"),
            documentation_url="https://docs.test.org",
        )
        d = card.to_dict()
        restored = AgentCard.from_dict(d)
        assert restored.name == "FullAgent"
        assert restored.description == "A fully-featured agent"
        assert len(restored.supported_interfaces) == 1
        assert restored.supported_interfaces[0].url == "http://localhost:8000"
        assert len(restored.skills) == 1
        assert restored.skills[0].id == "s1"
        assert restored.capabilities.streaming is True
        assert restored.provider.organization == "TestOrg"


# ── Wire format compliance ──


class TestWireFormat:
    """Verify serialized dicts use camelCase keys and correct field names."""

    def test_message_camel_case(self):
        msg = Message(
            message_id="m1",
            role=Role.USER,
            parts=[Part(text="hello")],
            context_id="ctx",
            task_id="t1",
            reference_task_ids=["t0"],
        )
        d = msg.to_dict()
        assert "messageId" in d
        assert "contextId" in d
        assert "taskId" in d
        assert "referenceTaskIds" in d
        assert _keys_are_camel(d)

    def test_task_camel_case(self):
        task = Task(
            id="t1",
            status=TaskStatus(
                state=TaskState.SUBMITTED,
                timestamp="2026-01-01T00:00:00.000Z",
            ),
            context_id="ctx",
        )
        d = task.to_dict()
        assert "contextId" in d
        assert _keys_are_camel(d)

    def test_agent_card_camel_case(self):
        card = AgentCard(
            name="Agent",
            supported_interfaces=[
                AgentInterface(
                    url="http://localhost:8000",
                    protocol_binding="JSONRPC",
                    protocol_version="1.0",
                ),
            ],
            default_input_modes=["text/plain"],
            default_output_modes=["text/plain"],
            capabilities=AgentCapabilities(
                push_notifications=True, extended_agent_card=False
            ),
        )
        d = card.to_dict()
        assert "supportedInterfaces" in d
        assert "defaultInputModes" in d
        assert "defaultOutputModes" in d
        assert _keys_are_camel(d)

    def test_part_media_type_camel(self):
        part = Part(text="hello", media_type="text/plain")
        d = part.to_dict()
        assert "mediaType" in d
        assert "media_type" not in d

    def test_none_fields_omitted(self):
        part = Part(text="hello")
        d = part.to_dict()
        assert "raw" not in d
        assert "url" not in d
        assert "data" not in d
        assert "metadata" not in d

    def test_empty_list_omitted(self):
        msg = Message(message_id="m1", role=Role.USER, parts=[])
        d = msg.to_dict()
        assert "parts" not in d

    def test_json_serializable(self):
        """Verify to_dict() output is JSON-serializable without custom encoder."""
        task = Task(
            id="t1",
            status=TaskStatus(
                state=TaskState.WORKING,
                message=Message(
                    message_id="m1",
                    role=Role.AGENT,
                    parts=[Part(text="working")],
                ),
                timestamp="2026-01-01T00:00:00.000Z",
            ),
            artifacts=[
                Artifact(
                    artifact_id="a1",
                    parts=[Part(text="output"), Part(data={"nested": True})],
                ),
            ],
        )
        d = task.to_dict()
        # Must not raise
        json_str = json.dumps(d)
        # And parse back identically
        assert json.loads(json_str) == d


# ── Enum values ──


class TestEnumValues:
    """Verify our enum values are valid A2A protocol values."""

    def test_role_values(self):
        assert Role.USER.value == "ROLE_USER"
        assert Role.AGENT.value == "ROLE_AGENT"
        assert Role.UNSPECIFIED.value == "ROLE_UNSPECIFIED"

    @pytest.mark.parametrize(
        "state,expected",
        [
            (TaskState.SUBMITTED, "TASK_STATE_SUBMITTED"),
            (TaskState.WORKING, "TASK_STATE_WORKING"),
            (TaskState.COMPLETED, "TASK_STATE_COMPLETED"),
            (TaskState.FAILED, "TASK_STATE_FAILED"),
            (TaskState.CANCELED, "TASK_STATE_CANCELED"),
            (TaskState.INPUT_REQUIRED, "TASK_STATE_INPUT_REQUIRED"),
            (TaskState.REJECTED, "TASK_STATE_REJECTED"),
            (TaskState.AUTH_REQUIRED, "TASK_STATE_AUTH_REQUIRED"),
        ],
    )
    def test_task_state_values(self, state, expected):
        assert state.value == expected

    def test_terminal_states(self):
        terminal = {
            TaskState.COMPLETED,
            TaskState.FAILED,
            TaskState.CANCELED,
            TaskState.REJECTED,
        }
        for state in TaskState:
            if state in terminal:
                assert state.is_terminal()
            else:
                assert not state.is_terminal()

    def test_role_is_str_enum(self):
        """Role values can be used directly as strings."""
        assert f"role={Role.USER}" == "role=ROLE_USER"

    def test_task_state_is_str_enum(self):
        """TaskState values can be used directly as strings."""
        assert f"state={TaskState.SUBMITTED}" == "state=TASK_STATE_SUBMITTED"


# ── Data model completeness ──


class TestDataModelCompleteness:
    """Verify our types have all required fields compared to the reference."""

    def test_message_has_role_and_parts(self):
        """Message must have role and parts fields."""
        msg = Message(role=Role.USER, parts=[Part(text="hello")])
        assert hasattr(msg, "role")
        assert hasattr(msg, "parts")
        assert hasattr(msg, "metadata")

    def test_task_has_required_fields(self):
        """Task must have id and status at minimum."""
        task = Task(id="t1", status=TaskStatus(state=TaskState.SUBMITTED))
        assert hasattr(task, "id")
        assert hasattr(task, "status")
        assert hasattr(task, "artifacts")
        assert hasattr(task, "history")
        assert hasattr(task, "metadata")
        assert hasattr(task, "context_id")

    def test_task_status_has_required_fields(self):
        ts = TaskStatus(state=TaskState.SUBMITTED)
        assert hasattr(ts, "state")
        assert hasattr(ts, "message")
        assert hasattr(ts, "timestamp")

    def test_artifact_has_required_fields(self):
        art = Artifact(parts=[Part(text="content")])
        assert hasattr(art, "artifact_id")
        assert hasattr(art, "parts")
        assert hasattr(art, "name")
        assert hasattr(art, "description")
        assert hasattr(art, "metadata")

    def test_agent_card_has_required_fields(self):
        card = AgentCard(name="Agent", version="1.0")
        assert hasattr(card, "name")
        assert hasattr(card, "version")
        assert hasattr(card, "description")
        assert hasattr(card, "skills")
        assert hasattr(card, "capabilities")
        assert hasattr(card, "supported_interfaces")
        assert hasattr(card, "default_input_modes")
        assert hasattr(card, "default_output_modes")
        assert hasattr(card, "provider")
        assert hasattr(card, "documentation_url")

    def test_agent_skill_has_required_fields(self):
        skill = AgentSkill(id="s1", name="Skill")
        assert hasattr(skill, "id")
        assert hasattr(skill, "name")
        assert hasattr(skill, "description")
        assert hasattr(skill, "tags")
        assert hasattr(skill, "examples")
        assert hasattr(skill, "input_modes")
        assert hasattr(skill, "output_modes")

    def test_ref_message_fields_covered(self):
        """All fields from reference Message are present in our Message."""
        import dataclasses as dc

        ref_fields = {f.name for f in dc.fields(a2a_ref.Message)}
        our_msg = Message(role=Role.USER, parts=[])
        our_fields = {f.name for f in dc.fields(our_msg)}
        # Reference fields (using camelCase like 'metadata')
        # should map to our snake_case
        for rf in ref_fields:
            # The reference uses camelCase field names in some cases
            # Check that we have an equivalent field
            snake = rf.replace("Id", "_id") if rf != "id" else rf
            assert snake in our_fields or rf in our_fields, (
                f"Reference field {rf!r} not found in our Message"
            )

    def test_ref_task_state_coverage(self):
        """Our TaskState covers all reference TaskState values."""
        # Map reference state names to our state names
        ref_states = {s.name for s in a2a_ref.TaskState}
        our_states = {s.name for s in TaskState}
        # We should have at least all the reference states
        # Reference: submitted, working, input_required, completed,
        # canceled, failed, unknown
        expected_mapping = {
            "submitted": "SUBMITTED",
            "working": "WORKING",
            "input_required": "INPUT_REQUIRED",
            "completed": "COMPLETED",
            "canceled": "CANCELED",
            "failed": "FAILED",
        }
        for ref_name, our_name in expected_mapping.items():
            assert ref_name in ref_states, f"Reference missing {ref_name}"
            assert our_name in our_states, f"Our module missing {our_name}"


# ── JSON-RPC layer ──


class TestJSONRPCRequest:
    """Test JSONRPCRequest serialization."""

    def test_basic(self):
        req = JSONRPCRequest(method="SendMessage", params={"key": "value"}, id=1)
        d = req.to_dict()
        assert d["jsonrpc"] == "2.0"
        assert d["method"] == "SendMessage"
        assert d["params"] == {"key": "value"}
        assert d["id"] == 1

    def test_no_params(self):
        req = JSONRPCRequest(method="GetTask", id=2)
        d = req.to_dict()
        assert "params" not in d

    def test_no_id(self):
        req = JSONRPCRequest(method="Notify")
        d = req.to_dict()
        assert "id" not in d

    def test_round_trip(self):
        req = JSONRPCRequest(method="SendMessage", params={"msg": "hi"}, id="abc")
        d = req.to_dict()
        restored = JSONRPCRequest.from_dict(d)
        assert restored.method == req.method
        assert restored.params == req.params
        assert restored.id == req.id
        assert restored.jsonrpc == "2.0"

    def test_string_id(self):
        req = JSONRPCRequest(method="GetTask", id="request-uuid-123")
        d = req.to_dict()
        assert d["id"] == "request-uuid-123"


class TestJSONRPCResponse:
    """Test JSONRPCResponse serialization."""

    def test_success(self):
        resp = JSONRPCResponse.success(1, {"task": {"id": "t1"}})
        d = resp.to_dict()
        assert d["jsonrpc"] == "2.0"
        assert d["id"] == 1
        assert d["result"] == {"task": {"id": "t1"}}
        assert "error" not in d

    def test_error(self):
        err = A2AError("Something went wrong")
        resp = JSONRPCResponse.from_error(1, err)
        d = resp.to_dict()
        assert d["jsonrpc"] == "2.0"
        assert d["id"] == 1
        assert "error" in d
        assert d["error"]["code"] == -32603
        assert d["error"]["message"] == "Something went wrong"
        assert "result" not in d

    def test_task_not_found_error(self):
        err = TaskNotFoundError("Task xyz not found")
        resp = JSONRPCResponse.from_error(42, err)
        d = resp.to_dict()
        assert d["error"]["code"] == -32001
        assert d["error"]["message"] == "Task xyz not found"

    def test_error_with_data(self):
        err = A2AError("bad request", data={"field": "message"})
        resp = JSONRPCResponse.from_error(1, err)
        d = resp.to_dict()
        assert d["error"]["data"] == {"field": "message"}


class TestJSONRPCErrorCodes:
    """Verify error codes match A2A protocol spec."""

    @pytest.mark.parametrize(
        "error_cls,expected_code",
        [
            (A2AError, -32603),
            (TaskNotFoundError, -32001),
            (TaskNotCancelableError, -32002),
        ],
    )
    def test_error_codes(self, error_cls, expected_code):
        err = error_cls()
        assert err.code == expected_code


# ── SSE encode/decode ──


class TestSSE:
    """Test SSE encode and decode round-trip."""

    def test_encode_basic(self):
        data = {"key": "value"}
        encoded = sse_encode(data)
        assert encoded.startswith(b"data: ")
        assert encoded.endswith(b"\n\n")
        # Parse back the JSON
        payload = encoded.decode("utf-8").strip().removeprefix("data: ")
        assert json.loads(payload) == data

    def test_encode_nested(self):
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "task": {
                    "id": "t1",
                    "status": {"state": "TASK_STATE_COMPLETED"},
                }
            },
        }
        encoded = sse_encode(data)
        payload = encoded.decode("utf-8").strip().removeprefix("data: ")
        assert json.loads(payload) == data

    def test_encode_compact(self):
        """SSE encoding uses compact JSON (no spaces after separators)."""
        data = {"a": 1, "b": 2}
        encoded = sse_encode(data)
        payload = encoded.decode("utf-8").strip().removeprefix("data: ")
        # Compact format: no spaces after : or ,
        assert ": " not in payload or payload.count(": ") == 0
        assert ", " not in payload


# ── TaskStore CRUD ──


class TestTaskStore:
    """Test TaskStore basic CRUD operations."""

    def test_save_and_get(self):
        store = TaskStore()
        task = Task(
            id="t1",
            status=TaskStatus(state=TaskState.SUBMITTED),
        )
        store.save(task)
        retrieved = store.get("t1")
        assert retrieved is not None
        assert retrieved.id == "t1"
        assert retrieved.status.state == TaskState.SUBMITTED

    def test_get_returns_copy(self):
        """Store should return deep copies to prevent mutation."""
        store = TaskStore()
        task = Task(id="t1", status=TaskStatus(state=TaskState.SUBMITTED))
        store.save(task)
        retrieved1 = store.get("t1")
        retrieved2 = store.get("t1")
        assert retrieved1 is not retrieved2
        assert retrieved1.id == retrieved2.id

    def test_get_nonexistent(self):
        store = TaskStore()
        assert store.get("nonexistent") is None

    def test_delete(self):
        store = TaskStore()
        task = Task(id="t1", status=TaskStatus(state=TaskState.SUBMITTED))
        store.save(task)
        assert store.delete("t1") is True
        assert store.get("t1") is None

    def test_delete_nonexistent(self):
        store = TaskStore()
        assert store.delete("nonexistent") is False

    def test_update(self):
        store = TaskStore()
        task = Task(id="t1", status=TaskStatus(state=TaskState.SUBMITTED))
        store.save(task)
        task.status = TaskStatus(state=TaskState.WORKING)
        store.save(task)
        retrieved = store.get("t1")
        assert retrieved.status.state == TaskState.WORKING

    def test_list_tasks_empty(self):
        store = TaskStore()
        tasks, token, total = store.list_tasks()
        assert tasks == []
        assert token == ""
        assert total == 0

    def test_list_tasks_basic(self):
        store = TaskStore()
        for i in range(5):
            store.save(
                Task(
                    id=f"t{i}",
                    status=TaskStatus(
                        state=TaskState.SUBMITTED,
                        timestamp=f"2026-01-01T00:00:0{i}.000Z",
                    ),
                )
            )
        tasks, _, total = store.list_tasks()
        assert total == 5
        assert len(tasks) == 5

    def test_list_tasks_filter_by_status(self):
        store = TaskStore()
        store.save(Task(id="t1", status=TaskStatus(state=TaskState.SUBMITTED)))
        store.save(Task(id="t2", status=TaskStatus(state=TaskState.COMPLETED)))
        store.save(Task(id="t3", status=TaskStatus(state=TaskState.SUBMITTED)))
        tasks, _, total = store.list_tasks(status=TaskState.SUBMITTED)
        assert total == 2
        assert all(t.status.state == TaskState.SUBMITTED for t in tasks)

    def test_list_tasks_filter_by_context(self):
        store = TaskStore()
        store.save(
            Task(
                id="t1",
                context_id="ctx-a",
                status=TaskStatus(state=TaskState.SUBMITTED),
            )
        )
        store.save(
            Task(
                id="t2",
                context_id="ctx-b",
                status=TaskStatus(state=TaskState.SUBMITTED),
            )
        )
        store.save(
            Task(
                id="t3",
                context_id="ctx-a",
                status=TaskStatus(state=TaskState.SUBMITTED),
            )
        )
        tasks, _, total = store.list_tasks(context_id="ctx-a")
        assert total == 2

    def test_list_tasks_pagination(self):
        store = TaskStore()
        for i in range(10):
            store.save(
                Task(
                    id=f"t{i}",
                    status=TaskStatus(
                        state=TaskState.SUBMITTED,
                        timestamp=f"2026-01-01T00:00:{i:02d}.000Z",
                    ),
                )
            )
        tasks, next_token, total = store.list_tasks(page_size=3)
        assert total == 10
        assert len(tasks) == 3
        assert next_token != ""


# ── TaskManager state machine ──


class TestTaskManager:
    """Test TaskManager lifecycle and state transitions."""

    def test_create_task(self):
        manager = TaskManager()
        msg = Message(role=Role.USER, parts=[Part(text="hello")])
        task = manager.create_task(msg)
        assert task.id
        assert task.status.state == TaskState.SUBMITTED
        assert task.history is not None
        assert len(task.history) == 1

    def test_get_task(self):
        manager = TaskManager()
        msg = Message(role=Role.USER, parts=[Part(text="hello")])
        created = manager.create_task(msg)
        retrieved = manager.get_task(created.id)
        assert retrieved.id == created.id

    def test_get_task_not_found(self):
        manager = TaskManager()
        with pytest.raises(TaskNotFoundError):
            manager.get_task("nonexistent")

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            (TaskState.SUBMITTED, TaskState.WORKING),
            (TaskState.SUBMITTED, TaskState.COMPLETED),
            (TaskState.SUBMITTED, TaskState.FAILED),
            (TaskState.SUBMITTED, TaskState.CANCELED),
            (TaskState.SUBMITTED, TaskState.REJECTED),
            (TaskState.WORKING, TaskState.COMPLETED),
            (TaskState.WORKING, TaskState.FAILED),
            (TaskState.WORKING, TaskState.CANCELED),
            (TaskState.WORKING, TaskState.INPUT_REQUIRED),
            (TaskState.WORKING, TaskState.AUTH_REQUIRED),
            (TaskState.INPUT_REQUIRED, TaskState.WORKING),
            (TaskState.INPUT_REQUIRED, TaskState.COMPLETED),
            (TaskState.INPUT_REQUIRED, TaskState.CANCELED),
            (TaskState.AUTH_REQUIRED, TaskState.WORKING),
            (TaskState.AUTH_REQUIRED, TaskState.COMPLETED),
            (TaskState.AUTH_REQUIRED, TaskState.CANCELED),
        ],
    )
    def test_valid_transitions(self, from_state, to_state):
        manager = TaskManager()
        msg = Message(role=Role.USER, parts=[Part(text="hello")])
        task = manager.create_task(msg)
        # Transition to from_state first (if not SUBMITTED)
        if from_state != TaskState.SUBMITTED:
            # Need intermediate transitions to reach the target state
            if from_state in (
                TaskState.WORKING,
                TaskState.INPUT_REQUIRED,
                TaskState.AUTH_REQUIRED,
            ):
                manager.update_status(task.id, TaskState.WORKING)
                if from_state in (TaskState.INPUT_REQUIRED, TaskState.AUTH_REQUIRED):
                    manager.update_status(task.id, from_state)
        task = manager.update_status(task.id, to_state)
        assert task.status.state == to_state

    @pytest.mark.parametrize(
        "terminal_state",
        [
            TaskState.COMPLETED,
            TaskState.FAILED,
            TaskState.CANCELED,
            TaskState.REJECTED,
        ],
    )
    def test_terminal_states_reject_transitions(self, terminal_state):
        """Terminal states should not allow any further transitions."""
        manager = TaskManager()
        msg = Message(role=Role.USER, parts=[Part(text="hello")])
        task = manager.create_task(msg)
        # Reach terminal state
        if terminal_state == TaskState.REJECTED:
            manager.update_status(task.id, terminal_state)
        else:
            manager.update_status(task.id, TaskState.WORKING)
            manager.update_status(task.id, terminal_state)
        # Now try to transition from terminal state
        with pytest.raises(ValueError, match="Invalid transition"):
            manager.update_status(task.id, TaskState.WORKING)

    def test_invalid_transition_submitted_to_input_required(self):
        manager = TaskManager()
        msg = Message(role=Role.USER, parts=[Part(text="hello")])
        task = manager.create_task(msg)
        with pytest.raises(ValueError, match="Invalid transition"):
            manager.update_status(task.id, TaskState.INPUT_REQUIRED)

    def test_add_artifact(self):
        manager = TaskManager()
        msg = Message(role=Role.USER, parts=[Part(text="hello")])
        task = manager.create_task(msg)
        manager.update_status(task.id, TaskState.WORKING)
        artifact = Artifact(parts=[Part(text="result")])
        task = manager.add_artifact(task.id, artifact)
        assert task.artifacts is not None
        assert len(task.artifacts) == 1
        assert task.artifacts[0].parts[0].text == "result"

    def test_add_artifact_append(self):
        manager = TaskManager()
        msg = Message(role=Role.USER, parts=[Part(text="hello")])
        task = manager.create_task(msg)
        manager.update_status(task.id, TaskState.WORKING)
        art_id = "art-1"
        artifact1 = Artifact(artifact_id=art_id, parts=[Part(text="chunk1")])
        manager.add_artifact(task.id, artifact1)
        artifact2 = Artifact(artifact_id=art_id, parts=[Part(text="chunk2")])
        task = manager.add_artifact(task.id, artifact2, append=True)
        assert len(task.artifacts) == 1
        assert len(task.artifacts[0].parts) == 2

    def test_cancel_task(self):
        manager = TaskManager()
        msg = Message(role=Role.USER, parts=[Part(text="hello")])
        task = manager.create_task(msg)
        manager.update_status(task.id, TaskState.WORKING)
        task = manager.cancel_task(task.id)
        assert task.status.state == TaskState.CANCELED

    def test_cancel_terminal_task_raises(self):
        manager = TaskManager()
        msg = Message(role=Role.USER, parts=[Part(text="hello")])
        task = manager.create_task(msg)
        manager.update_status(task.id, TaskState.WORKING)
        manager.update_status(task.id, TaskState.COMPLETED)
        with pytest.raises(TaskNotCancelableError):
            manager.cancel_task(task.id)

    def test_subscribe_receives_events(self):
        manager = TaskManager()
        msg = Message(role=Role.USER, parts=[Part(text="hello")])
        task = manager.create_task(msg)
        events = []
        manager.subscribe(task.id, events.append)
        manager.update_status(task.id, TaskState.WORKING)
        assert len(events) == 1
        assert events[0].status_update is not None
        assert events[0].status_update.status.state == TaskState.WORKING

    def test_unsubscribe(self):
        manager = TaskManager()
        msg = Message(role=Role.USER, parts=[Part(text="hello")])
        task = manager.create_task(msg)
        events = []
        unsub = manager.subscribe(task.id, events.append)
        manager.update_status(task.id, TaskState.WORKING)
        unsub()
        manager.update_status(task.id, TaskState.COMPLETED)
        assert len(events) == 1  # only one event before unsubscribe


# ── Streaming event types ──


class TestStreamingEvents:
    """Test streaming event types serialization."""

    def test_task_status_update_event(self):
        event = TaskStatusUpdateEvent(
            task_id="t1",
            context_id="ctx-1",
            status=TaskStatus(
                state=TaskState.WORKING,
                timestamp="2026-01-01T00:00:00.000Z",
            ),
        )
        d = event.to_dict()
        assert d["taskId"] == "t1"
        assert d["contextId"] == "ctx-1"
        assert d["status"]["state"] == "TASK_STATE_WORKING"
        restored = TaskStatusUpdateEvent.from_dict(d)
        assert restored.task_id == "t1"
        assert restored.status.state == TaskState.WORKING

    def test_task_artifact_update_event(self):
        event = TaskArtifactUpdateEvent(
            task_id="t1",
            context_id="ctx-1",
            artifact=Artifact(artifact_id="a1", parts=[Part(text="result")]),
            append=False,
            last_chunk=True,
        )
        d = event.to_dict()
        assert d["taskId"] == "t1"
        assert d["lastChunk"] is True
        restored = TaskArtifactUpdateEvent.from_dict(d)
        assert restored.last_chunk is True
        assert restored.artifact.artifact_id == "a1"

    def test_stream_response_with_task(self):
        task = Task(
            id="t1",
            status=TaskStatus(
                state=TaskState.SUBMITTED,
                timestamp="2026-01-01T00:00:00.000Z",
            ),
        )
        sr = StreamResponse(task=task)
        d = sr.to_dict()
        assert "task" in d
        restored = StreamResponse.from_dict(d)
        assert restored.task is not None
        assert restored.task.id == "t1"

    def test_stream_response_with_status_update(self):
        sr = StreamResponse(
            status_update=TaskStatusUpdateEvent(
                task_id="t1",
                context_id="ctx-1",
                status=TaskStatus(state=TaskState.COMPLETED),
            )
        )
        d = sr.to_dict()
        assert "statusUpdate" in d
        restored = StreamResponse.from_dict(d)
        assert restored.status_update is not None
        assert restored.status_update.status.state == TaskState.COMPLETED


# ── SendMessage request/response ──


class TestSendMessage:
    """Test SendMessage request/response types."""

    def test_send_message_request_round_trip(self):
        req = SendMessageRequest(
            message=Message(
                message_id="m1",
                role=Role.USER,
                parts=[Part(text="hello")],
            ),
            configuration=SendMessageConfiguration(
                accepted_output_modes=["text/plain"],
                history_length=10,
            ),
        )
        d = req.to_dict()
        assert "message" in d
        assert "configuration" in d
        restored = SendMessageRequest.from_dict(d)
        assert restored.message.parts[0].text == "hello"
        assert restored.configuration.history_length == 10

    def test_send_message_response_with_task(self):
        resp = SendMessageResponse(
            task=Task(
                id="t1",
                status=TaskStatus(
                    state=TaskState.COMPLETED,
                    timestamp="2026-01-01T00:00:00.000Z",
                ),
            )
        )
        d = resp.to_dict()
        assert "task" in d
        restored = SendMessageResponse.from_dict(d)
        assert restored.task is not None
        assert restored.task.id == "t1"

    def test_send_message_response_with_message(self):
        resp = SendMessageResponse(
            message=Message(
                message_id="m1",
                role=Role.AGENT,
                parts=[Part(text="response")],
            )
        )
        d = resp.to_dict()
        assert "message" in d
        restored = SendMessageResponse.from_dict(d)
        assert restored.message is not None
        assert restored.message.parts[0].text == "response"


# ── Generic _serialize helper ──


class TestSerializeHelper:
    """Test the _serialize helper function."""

    def test_none(self):
        assert _serialize(None) is None

    def test_primitives(self):
        assert _serialize("hello") == "hello"
        assert _serialize(42) == 42
        assert _serialize(3.14) == 3.14
        assert _serialize(True) is True

    def test_enum(self):
        assert _serialize(Role.USER) == "ROLE_USER"
        assert _serialize(TaskState.COMPLETED) == "TASK_STATE_COMPLETED"

    def test_dict(self):
        result = _serialize({"key": "value", "none_key": None})
        assert result == {"key": "value"}

    def test_list(self):
        result = _serialize([1, "two", None, Role.USER])
        assert result == [1, "two", None, "ROLE_USER"]

    def test_dataclass(self):
        part = Part(text="hello")
        result = _serialize(part)
        assert isinstance(result, dict)
        assert result["text"] == "hello"


# ── Auto-generated IDs ──


class TestAutoGeneratedIds:
    """Test that IDs are auto-generated when not provided."""

    def test_message_id_auto(self):
        msg = Message(role=Role.USER, parts=[])
        assert msg.message_id != ""
        assert len(msg.message_id) > 0

    def test_task_id_auto(self):
        task = Task(status=TaskStatus(state=TaskState.SUBMITTED))
        assert task.id != ""

    def test_artifact_id_auto(self):
        art = Artifact(parts=[])
        assert art.artifact_id != ""

    def test_timestamp_auto(self):
        ts = TaskStatus(state=TaskState.SUBMITTED)
        assert ts.timestamp is not None
        assert "T" in ts.timestamp  # ISO 8601
