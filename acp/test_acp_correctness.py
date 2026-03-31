"""Correctness tests: zerodep acp vs agent-client-protocol."""

import json
import os
import sys

import pytest

# Our acp.py shadows the installed ``acp`` package.  Import the reference
# library *first* with our directory removed from sys.path, then restore
# the path and import our module.
_this_dir = os.path.dirname(__file__)

_saved_path = sys.path[:]
sys.path = [
    p
    for p in sys.path
    if os.path.abspath(p)
    not in (
        os.path.abspath(_this_dir),
        os.path.abspath(os.path.join(_this_dir, "..")),
    )
]
_cached_acp = sys.modules.pop("acp", None)
_cached_acp_sub = {}
for _k in list(sys.modules):
    if _k.startswith("acp."):
        _cached_acp_sub[_k] = sys.modules.pop(_k)

try:
    import acp.schema as acp_ref  # noqa: E402
except ImportError:
    pytest.skip("agent-client-protocol not installed", allow_module_level=True)
finally:
    sys.path = _saved_path
    for _k in list(sys.modules):
        if _k == "acp" or _k.startswith("acp."):
            del sys.modules[_k]
    sys.modules.update(_cached_acp_sub)
    if _cached_acp is not None:
        sys.modules["acp"] = _cached_acp

# Now import our module
sys.path.insert(0, _this_dir)
for _k in list(sys.modules):
    if _k == "acp" or _k.startswith("acp."):
        del sys.modules[_k]

from acp import (  # noqa: E402
    AgentCapabilities,
    AgentMessageChunkUpdate,
    AudioContent,
    AvailableCommand,
    AvailableCommandInput,
    AvailableCommandsUpdate,
    ClientCapabilities,
    ConfigOption,
    ConfigOptionUpdate,
    ConfigOptionValue,
    CurrentModeUpdate,
    DiffContent,
    FsCapabilities,
    ImageContent,
    ImplementationInfo,
    InitializeParams,
    InitializeResult,
    JSONRPCError,
    McpCapabilities,
    NewSessionParams,
    NewSessionResult,
    PlanEntry,
    PlanEntryPriority,
    PlanEntryStatus,
    PlanUpdate,
    PromptCapabilities,
    PromptParams,
    PromptResult,
    SessionInfoUpdate,
    SessionMode,
    SessionModeState,
    StopReason,
    TerminalContent,
    TextContent,
    ThoughtMessageChunkUpdate,
    ToolCallContentItem,
    ToolCallLocation,
    ToolCallStatus,
    ToolCallStatusUpdate,
    ToolCallUpdate,
    ToolKind,
    UserMessageChunkUpdate,
    from_raw,
    to_dict,
)

# ── Helpers ──


def _zd_wire(obj) -> dict:
    """Serialize a zerodep object to wire-format dict."""
    return to_dict(obj)


def _ref_wire(obj) -> dict:
    """Serialize a reference object to wire-format dict (camelCase, no None)."""
    return obj.model_dump(by_alias=True, exclude_none=True)


# ── Round-trip serialization ──


class TestRoundTrip:
    """Verify from_raw(to_dict(obj)) preserves data for all major types."""

    def test_text_content(self):
        obj = TextContent(text="hello world")
        d = to_dict(obj)
        r = from_raw(d)
        assert r["text"] == "hello world"
        assert r["type"] == "text"

    def test_image_content(self):
        obj = ImageContent(data="aGVsbG8=", mime_type="image/png")
        d = to_dict(obj)
        r = from_raw(d)
        assert r["data"] == "aGVsbG8="
        assert r["mime_type"] == "image/png"
        assert r["type"] == "image"

    def test_audio_content(self):
        obj = AudioContent(data="AAAA", mime_type="audio/wav")
        d = to_dict(obj)
        r = from_raw(d)
        assert r["data"] == "AAAA"
        assert r["mime_type"] == "audio/wav"
        assert r["type"] == "audio"

    def test_initialize_params(self):
        obj = InitializeParams(
            protocol_version=1,
            client_info=ImplementationInfo(name="test", version="0.1"),
        )
        d = to_dict(obj)
        r = from_raw(d)
        assert r["protocol_version"] == 1
        assert r["client_info"]["name"] == "test"

    def test_initialize_result(self):
        obj = InitializeResult(
            protocol_version=1,
            agent_capabilities=AgentCapabilities(
                load_session=True,
                prompt_capabilities=PromptCapabilities(image=True),
            ),
            agent_info=ImplementationInfo(name="agent", version="1.0"),
        )
        d = to_dict(obj)
        r = from_raw(d)
        assert r["protocol_version"] == 1
        assert r["agent_info"]["name"] == "agent"
        assert r["agent_capabilities"]["loadSession"] is True

    def test_new_session_params(self):
        obj = NewSessionParams(cwd="/home/user/project")
        d = to_dict(obj)
        r = from_raw(d)
        assert r["cwd"] == "/home/user/project"

    def test_new_session_result(self):
        obj = NewSessionResult(
            session_id="sess-abc",
            modes=SessionModeState(
                current_mode_id="default",
                available_modes=[SessionMode(id="default", name="Default")],
            ),
        )
        d = to_dict(obj)
        r = from_raw(d)
        assert r["session_id"] == "sess-abc"

    def test_prompt_params(self):
        obj = PromptParams(
            session_id="sess-1",
            prompt=[
                TextContent(text="Hello"),
                ImageContent(data="abc", mime_type="image/png"),
            ],
        )
        d = to_dict(obj)
        r = from_raw(d)
        assert r["session_id"] == "sess-1"
        assert len(r["prompt"]) == 2
        assert r["prompt"][0]["text"] == "Hello"

    def test_prompt_result(self):
        obj = PromptResult(stop_reason=StopReason.END_TURN)
        d = to_dict(obj)
        r = from_raw(d)
        assert r["stop_reason"] == "end_turn"

    def test_tool_call_update(self):
        obj = ToolCallUpdate(
            tool_call_id="tc-1",
            title="Read file",
            kind=ToolKind.READ,
            status=ToolCallStatus.COMPLETED,
            locations=[ToolCallLocation(path="/tmp/f.py", line=10)],
            raw_input={"path": "/tmp/f.py"},
        )
        d = to_dict(obj)
        r = from_raw(d)
        assert r["tool_call_id"] == "tc-1"
        assert r["raw_input"] == {"path": "/tmp/f.py"}

    def test_plan_update(self):
        obj = PlanUpdate(
            entries=[
                PlanEntry(
                    content="Step 1",
                    priority=PlanEntryPriority.HIGH,
                    status=PlanEntryStatus.PENDING,
                ),
            ]
        )
        d = to_dict(obj)
        r = from_raw(d)
        assert len(r["entries"]) == 1
        assert r["entries"][0]["content"] == "Step 1"

    def test_json_rpc_error_data(self):
        obj = JSONRPCError(code=-32600, message="Invalid Request", data={"key": 1})
        d = obj.to_dict()
        roundtripped = JSONRPCError.from_dict(d)
        assert roundtripped.code == -32600
        assert roundtripped.message == "Invalid Request"
        assert roundtripped.data == {"key": 1}


# ── Wire format key verification ──


class TestWireFormatKeys:
    """Verify to_dict() produces correct camelCase keys matching ACP spec."""

    def test_text_content_keys(self):
        d = to_dict(TextContent(text="hi"))
        assert set(d.keys()) == {"text", "type"}

    def test_image_content_keys(self):
        d = to_dict(ImageContent(data="x", mime_type="image/png"))
        assert "mimeType" in d
        assert "mime_type" not in d

    def test_audio_content_keys(self):
        d = to_dict(AudioContent(data="x", mime_type="audio/wav"))
        assert "mimeType" in d

    def test_initialize_params_keys(self):
        d = to_dict(
            InitializeParams(
                protocol_version=1,
                client_capabilities=ClientCapabilities(
                    fs=FsCapabilities(read_text_file=True),
                ),
                client_info=ImplementationInfo(name="test", version="0.1"),
            )
        )
        assert "protocolVersion" in d
        assert "clientCapabilities" in d
        assert "clientInfo" in d
        assert "readTextFile" in d["clientCapabilities"]["fs"]

    def test_initialize_result_keys(self):
        d = to_dict(
            InitializeResult(
                protocol_version=1,
                agent_capabilities=AgentCapabilities(load_session=True),
                agent_info=ImplementationInfo(name="a", version="1"),
            )
        )
        assert "protocolVersion" in d
        assert "agentCapabilities" in d
        assert "agentInfo" in d
        assert "loadSession" in d["agentCapabilities"]

    def test_new_session_result_keys(self):
        d = to_dict(NewSessionResult(session_id="s1"))
        assert "sessionId" in d
        assert "session_id" not in d

    def test_prompt_params_keys(self):
        d = to_dict(PromptParams(session_id="s1", prompt=[TextContent(text="hi")]))
        assert "sessionId" in d
        assert "session_id" not in d

    def test_prompt_result_keys(self):
        d = to_dict(PromptResult(stop_reason=StopReason.END_TURN))
        assert "stopReason" in d
        assert d["stopReason"] == "end_turn"

    def test_tool_call_update_keys(self):
        d = to_dict(
            ToolCallUpdate(
                tool_call_id="tc-1",
                title="Read",
                kind=ToolKind.READ,
                status=ToolCallStatus.PENDING,
                raw_input={"x": 1},
                raw_output={"y": 2},
            )
        )
        assert "toolCallId" in d
        assert "rawInput" in d
        assert "rawOutput" in d
        assert "sessionUpdate" in d

    def test_agent_message_chunk_keys(self):
        d = to_dict(AgentMessageChunkUpdate(content=TextContent(text="hi")))
        assert "content" in d
        assert "sessionUpdate" in d
        assert d["sessionUpdate"] == "agent_message_chunk"

    def test_tool_call_location_keys(self):
        d = to_dict(ToolCallLocation(path="/tmp/f.py", line=5))
        assert "path" in d
        assert "line" in d

    def test_plan_entry_keys(self):
        d = to_dict(
            PlanEntry(
                content="task",
                priority=PlanEntryPriority.MEDIUM,
                status=PlanEntryStatus.IN_PROGRESS,
            )
        )
        assert d["priority"] == "medium"
        assert d["status"] == "in_progress"

    def test_session_info_update_keys(self):
        d = to_dict(
            SessionInfoUpdate(
                title="My Session",
                updated_at="2026-01-01T00:00:00Z",
            )
        )
        assert "sessionUpdate" in d
        assert "updatedAt" in d
        assert d["sessionUpdate"] == "session_info_update"

    def test_current_mode_update_keys(self):
        d = to_dict(CurrentModeUpdate(mode_id="plan"))
        assert "modeId" in d
        assert d["sessionUpdate"] == "current_mode_update"

    def test_available_commands_update_keys(self):
        d = to_dict(
            AvailableCommandsUpdate(
                available_commands=[
                    AvailableCommand(
                        name="web",
                        description="Search the web",
                        input=AvailableCommandInput(hint="query"),
                    )
                ]
            )
        )
        assert "availableCommands" in d
        assert d["sessionUpdate"] == "available_commands_update"

    def test_none_values_omitted(self):
        d = to_dict(InitializeResult(protocol_version=1))
        assert "agentCapabilities" not in d
        assert "agentInfo" not in d
        assert "authMethods" not in d


# ── Enum values match ──


class TestEnumValues:
    """Compare enum values between zerodep and reference (Literal types)."""

    @pytest.mark.parametrize(
        "zd_enum,ref_literal",
        [
            (StopReason, acp_ref.StopReason),
            (ToolCallStatus, acp_ref.ToolCallStatus),
            (PlanEntryPriority, acp_ref.PlanEntryPriority),
            (PlanEntryStatus, acp_ref.PlanEntryStatus),
        ],
        ids=["StopReason", "ToolCallStatus", "PlanEntryPriority", "PlanEntryStatus"],
    )
    def test_enum_values_match(self, zd_enum, ref_literal):
        zd_values = {e.value for e in zd_enum}
        ref_values = set(ref_literal.__args__)
        assert zd_values == ref_values

    def test_tool_kind_superset(self):
        """Reference may have extra ToolKind values; ours must be a subset."""
        zd_values = {e.value for e in ToolKind}
        ref_values = set(acp_ref.ToolKind.__args__)
        # Our values should all be valid in the ref spec
        assert zd_values <= ref_values, (
            f"Unexpected zerodep ToolKind values: {zd_values - ref_values}"
        )


# ── Wire format compatibility with reference ──


class TestWireFormatCompatibility:
    """Compare wire-format output between zerodep to_dict and reference model_dump."""

    def test_text_content(self):
        zd = _zd_wire(TextContent(text="hello"))
        # Ref TextContent has no type field; wire format differs here
        ref_tc = acp_ref.TextContent(text="hello")
        ref = _ref_wire(ref_tc)
        # Both should have "text" key
        assert zd["text"] == ref["text"]

    def test_image_content(self):
        zd = _zd_wire(ImageContent(data="aGVsbG8=", mime_type="image/png"))
        ref = _ref_wire(acp_ref.ImageContent(data="aGVsbG8=", mime_type="image/png"))
        assert zd["data"] == ref["data"]
        assert zd["mimeType"] == ref["mimeType"]

    def test_audio_content(self):
        zd = _zd_wire(AudioContent(data="AAAA", mime_type="audio/wav"))
        ref = _ref_wire(acp_ref.AudioContent(data="AAAA", mime_type="audio/wav"))
        assert zd["data"] == ref["data"]
        assert zd["mimeType"] == ref["mimeType"]

    def test_tool_call_update(self):
        zd = _zd_wire(
            ToolCallUpdate(
                tool_call_id="tc-1",
                title="Read file",
                kind=ToolKind.READ,
                status=ToolCallStatus.PENDING,
            )
        )
        ref = _ref_wire(
            acp_ref.ToolCallUpdate(
                tool_call_id="tc-1",
                title="Read file",
                kind="read",
                status="pending",
            )
        )
        assert zd["toolCallId"] == ref["toolCallId"]
        assert zd["title"] == ref["title"]
        assert zd["kind"] == ref["kind"]
        assert zd["status"] == ref["status"]

    def test_tool_call_update_with_locations(self):
        zd = _zd_wire(
            ToolCallUpdate(
                tool_call_id="tc-2",
                title="Edit file",
                kind=ToolKind.EDIT,
                status=ToolCallStatus.COMPLETED,
                locations=[ToolCallLocation(path="/tmp/f.py", line=42)],
            )
        )
        ref = _ref_wire(
            acp_ref.ToolCallUpdate(
                tool_call_id="tc-2",
                title="Edit file",
                kind="edit",
                status="completed",
                locations=[acp_ref.ToolCallLocation(path="/tmp/f.py", line=42)],
            )
        )
        assert zd["locations"] == ref["locations"]

    def test_plan_entry(self):
        zd = _zd_wire(
            PlanEntry(
                content="Do X",
                priority=PlanEntryPriority.HIGH,
                status=PlanEntryStatus.PENDING,
            )
        )
        ref = _ref_wire(
            acp_ref.PlanEntry(content="Do X", priority="high", status="pending")
        )
        assert zd == ref

    def test_prompt_result(self):
        zd = _zd_wire(PromptResult(stop_reason=StopReason.END_TURN))
        ref = _ref_wire(acp_ref.PromptResponse(stop_reason="end_turn"))
        assert zd["stopReason"] == ref["stopReason"]

    def test_new_session_result(self):
        zd = _zd_wire(NewSessionResult(session_id="sess-1"))
        ref = _ref_wire(acp_ref.NewSessionResponse(session_id="sess-1"))
        assert zd["sessionId"] == ref["sessionId"]

    def test_initialize_params(self):
        zd = _zd_wire(InitializeParams(protocol_version=1))
        ref = _ref_wire(acp_ref.InitializeRequest(protocol_version=1))
        assert zd["protocolVersion"] == ref["protocolVersion"]

    def test_implementation_info(self):
        zd = _zd_wire(ImplementationInfo(name="my-agent", version="1.0.0"))
        ref = _ref_wire(acp_ref.Implementation(name="my-agent", version="1.0.0"))
        assert zd["name"] == ref["name"]
        assert zd["version"] == ref["version"]

    def test_available_command(self):
        zd = _zd_wire(
            AvailableCommand(
                name="web",
                description="Search the web",
                input=AvailableCommandInput(hint="query"),
            )
        )
        ref = _ref_wire(
            acp_ref.AvailableCommand(
                name="web",
                description="Search the web",
                input=acp_ref.AvailableCommandInput(hint="query"),
            )
        )
        assert zd["name"] == ref["name"]
        assert zd["description"] == ref["description"]


# ── Content block serialization ──


class TestContentBlockSerialization:
    """Verify content blocks serialize to JSON correctly."""

    def test_text_has_type_field(self):
        d = to_dict(TextContent(text="hello"))
        assert d["type"] == "text"

    def test_image_has_type_field(self):
        d = to_dict(ImageContent(data="abc", mime_type="image/png"))
        assert d["type"] == "image"

    def test_audio_has_type_field(self):
        d = to_dict(AudioContent(data="abc", mime_type="audio/wav"))
        assert d["type"] == "audio"

    def test_diff_content(self):
        d = to_dict(DiffContent(path="/tmp/f.py", new_text="new", old_text="old"))
        assert d["type"] == "diff"
        assert d["path"] == "/tmp/f.py"
        assert "newText" in d
        assert "oldText" in d

    def test_terminal_content(self):
        d = to_dict(TerminalContent(terminal_id="t-1"))
        assert d["type"] == "terminal"
        assert d["terminalId"] == "t-1"

    def test_tool_call_content_item(self):
        d = to_dict(ToolCallContentItem(content=TextContent(text="output")))
        assert d["type"] == "content"
        assert d["content"]["text"] == "output"

    def test_nested_content_in_update(self):
        update = AgentMessageChunkUpdate(content=TextContent(text="hello"))
        d = to_dict(update)
        assert d["content"]["type"] == "text"
        assert d["content"]["text"] == "hello"


# ── Protocol message format ──


class TestProtocolMessageFormat:
    """Verify protocol messages produce correct wire format."""

    def test_initialize_params_full(self):
        obj = InitializeParams(
            protocol_version=1,
            client_capabilities=ClientCapabilities(
                fs=FsCapabilities(read_text_file=True, write_text_file=True),
                terminal=True,
            ),
            client_info=ImplementationInfo(name="test-client", version="0.5.0"),
        )
        d = to_dict(obj)
        assert d["protocolVersion"] == 1
        assert d["clientCapabilities"]["fs"]["readTextFile"] is True
        assert d["clientCapabilities"]["fs"]["writeTextFile"] is True
        assert d["clientCapabilities"]["terminal"] is True
        assert d["clientInfo"]["name"] == "test-client"

    def test_initialize_result_full(self):
        obj = InitializeResult(
            protocol_version=1,
            agent_capabilities=AgentCapabilities(
                load_session=True,
                prompt_capabilities=PromptCapabilities(image=True, audio=True),
                mcp_capabilities=McpCapabilities(http=True, sse=True),
            ),
            agent_info=ImplementationInfo(name="test-agent", version="2.0"),
        )
        d = to_dict(obj)
        caps = d["agentCapabilities"]
        assert caps["loadSession"] is True
        assert caps["promptCapabilities"]["image"] is True
        assert caps["promptCapabilities"]["audio"] is True
        assert caps["mcpCapabilities"]["http"] is True
        assert d["agentInfo"]["name"] == "test-agent"

    def test_prompt_params_multiple_blocks(self):
        obj = PromptParams(
            session_id="sess-1",
            prompt=[
                TextContent(text="Analyze this image:"),
                ImageContent(data="base64data", mime_type="image/png"),
            ],
        )
        d = to_dict(obj)
        assert d["sessionId"] == "sess-1"
        assert len(d["prompt"]) == 2
        assert d["prompt"][0]["type"] == "text"
        assert d["prompt"][1]["type"] == "image"
        assert d["prompt"][1]["mimeType"] == "image/png"

    def test_new_session_with_modes(self):
        obj = NewSessionResult(
            session_id="s1",
            modes=SessionModeState(
                current_mode_id="normal",
                available_modes=[
                    SessionMode(id="normal", name="Normal"),
                    SessionMode(id="plan", name="Plan", description="Planning mode"),
                ],
            ),
        )
        d = to_dict(obj)
        assert d["sessionId"] == "s1"
        assert d["modes"]["currentModeId"] == "normal"
        assert len(d["modes"]["availableModes"]) == 2

    def test_new_session_with_config(self):
        obj = NewSessionResult(
            session_id="s2",
            config_options=[
                ConfigOption(
                    id="model",
                    name="Model",
                    type="select",
                    current_value="gpt-4",
                    options=[
                        ConfigOptionValue(value="gpt-4", name="GPT-4"),
                        ConfigOptionValue(value="gpt-3.5", name="GPT-3.5"),
                    ],
                )
            ],
        )
        d = to_dict(obj)
        opts = d["configOptions"]
        assert len(opts) == 1
        assert opts[0]["currentValue"] == "gpt-4"
        assert len(opts[0]["options"]) == 2


# ── Session update types ──


class TestSessionUpdateTypes:
    """Verify session update serialization."""

    def test_agent_message_chunk(self):
        obj = AgentMessageChunkUpdate(content=TextContent(text="Hello"))
        d = to_dict(obj)
        assert d["sessionUpdate"] == "agent_message_chunk"
        assert d["content"]["text"] == "Hello"

    def test_user_message_chunk(self):
        obj = UserMessageChunkUpdate(content=TextContent(text="Hi"))
        d = to_dict(obj)
        assert d["sessionUpdate"] == "user_message_chunk"

    def test_thought_message_chunk(self):
        obj = ThoughtMessageChunkUpdate(content=TextContent(text="Thinking..."))
        d = to_dict(obj)
        assert d["sessionUpdate"] == "thought_message_chunk"

    def test_tool_call_update_full(self):
        obj = ToolCallUpdate(
            tool_call_id="tc-1",
            title="Read /tmp/f.py",
            kind=ToolKind.READ,
            status=ToolCallStatus.IN_PROGRESS,
            locations=[ToolCallLocation(path="/tmp/f.py", line=1)],
            raw_input={"path": "/tmp/f.py"},
        )
        d = to_dict(obj)
        assert d["sessionUpdate"] == "tool_call"
        assert d["toolCallId"] == "tc-1"
        assert d["kind"] == "read"
        assert d["status"] == "in_progress"
        assert d["locations"][0]["path"] == "/tmp/f.py"

    def test_tool_call_status_update(self):
        obj = ToolCallStatusUpdate(
            tool_call_id="tc-1",
            status=ToolCallStatus.COMPLETED,
            title="Done reading",
        )
        d = to_dict(obj)
        assert d["sessionUpdate"] == "tool_call_update"
        assert d["toolCallId"] == "tc-1"
        assert d["status"] == "completed"

    def test_plan_update(self):
        obj = PlanUpdate(
            entries=[
                PlanEntry(
                    content="Analyze code",
                    priority=PlanEntryPriority.HIGH,
                    status=PlanEntryStatus.COMPLETED,
                ),
                PlanEntry(
                    content="Write tests",
                    priority=PlanEntryPriority.MEDIUM,
                    status=PlanEntryStatus.PENDING,
                ),
            ]
        )
        d = to_dict(obj)
        assert d["sessionUpdate"] == "plan"
        assert len(d["entries"]) == 2
        assert d["entries"][0]["priority"] == "high"
        assert d["entries"][1]["status"] == "pending"

    def test_available_commands_update(self):
        obj = AvailableCommandsUpdate(
            available_commands=[
                AvailableCommand(name="web", description="Web search"),
                AvailableCommand(
                    name="file",
                    description="File ops",
                    input=AvailableCommandInput(hint="path"),
                ),
            ]
        )
        d = to_dict(obj)
        assert d["sessionUpdate"] == "available_commands_update"
        assert len(d["availableCommands"]) == 2
        assert d["availableCommands"][1]["input"]["hint"] == "path"

    def test_current_mode_update(self):
        d = to_dict(CurrentModeUpdate(mode_id="plan"))
        assert d["sessionUpdate"] == "current_mode_update"
        assert d["modeId"] == "plan"

    def test_config_option_update(self):
        obj = ConfigOptionUpdate(
            config_options=[
                ConfigOption(
                    id="model",
                    name="Model",
                    type="select",
                    current_value="gpt-4",
                    options=[ConfigOptionValue(value="gpt-4", name="GPT-4")],
                )
            ]
        )
        d = to_dict(obj)
        assert d["sessionUpdate"] == "config_option_update"
        assert len(d["configOptions"]) == 1

    def test_session_info_update(self):
        obj = SessionInfoUpdate(title="My Chat", updated_at="2026-01-01T00:00:00Z")
        d = to_dict(obj)
        assert d["sessionUpdate"] == "session_info_update"
        assert d["updatedAt"] == "2026-01-01T00:00:00Z"


# ── JSON-RPC transport ──


class TestJSONRPCError:
    """Test JSONRPCError serialization."""

    def test_basic_error(self):
        err = JSONRPCError(code=-32600, message="Invalid Request")
        d = err.to_dict()
        assert d == {"code": -32600, "message": "Invalid Request"}

    def test_error_with_data(self):
        err = JSONRPCError(
            code=-32602, message="Invalid params", data={"expected": "string"}
        )
        d = err.to_dict()
        assert d["data"] == {"expected": "string"}

    def test_from_dict(self):
        d = {"code": -32700, "message": "Parse error", "data": [1, 2, 3]}
        err = JSONRPCError.from_dict(d)
        assert err.code == -32700
        assert err.message == "Parse error"
        assert err.data == [1, 2, 3]

    def test_from_dict_no_data(self):
        d = {"code": -32603, "message": "Internal error"}
        err = JSONRPCError.from_dict(d)
        assert err.data is None

    def test_round_trip(self):
        original = JSONRPCError(
            code=-32601, message="Method not found", data={"m": "foo"}
        )
        restored = JSONRPCError.from_dict(original.to_dict())
        assert restored.code == original.code
        assert restored.message == original.message
        assert restored.data == original.data


# ── from_raw camelCase -> snake_case ──


class TestFromRaw:
    """Verify from_raw converts camelCase keys to snake_case correctly."""

    CAMEL_TO_SNAKE_CASES = [
        pytest.param({"sessionId": "s1"}, {"session_id": "s1"}, id="sessionId"),
        pytest.param(
            {"protocolVersion": 1}, {"protocol_version": 1}, id="protocolVersion"
        ),
        pytest.param(
            {"clientCapabilities": {}},
            {"client_capabilities": {}},
            id="clientCapabilities",
        ),
        pytest.param(
            {"agentCapabilities": {}},
            {"agent_capabilities": {}},
            id="agentCapabilities",
        ),
        pytest.param(
            {"stopReason": "end_turn"}, {"stop_reason": "end_turn"}, id="stopReason"
        ),
        pytest.param({"toolCallId": "tc-1"}, {"tool_call_id": "tc-1"}, id="toolCallId"),
        pytest.param({"rawInput": {}}, {"raw_input": {}}, id="rawInput"),
        pytest.param({"rawOutput": {}}, {"raw_output": {}}, id="rawOutput"),
        pytest.param(
            {"mimeType": "image/png"},
            {"mime_type": "image/png"},
            id="mimeType",
        ),
        pytest.param(
            {"currentModeId": "plan"}, {"current_mode_id": "plan"}, id="currentModeId"
        ),
        pytest.param({"configId": "m"}, {"config_id": "m"}, id="configId"),
        pytest.param(
            {"currentValue": "gpt-4"}, {"current_value": "gpt-4"}, id="currentValue"
        ),
        pytest.param(
            {"availableCommands": []},
            {"available_commands": []},
            id="availableCommands",
        ),
        pytest.param(
            {"sessionUpdate": "plan"}, {"session_update": "plan"}, id="sessionUpdate"
        ),
        pytest.param({"updatedAt": "now"}, {"updated_at": "now"}, id="updatedAt"),
        pytest.param({"nextCursor": "c"}, {"next_cursor": "c"}, id="nextCursor"),
        pytest.param({"terminalId": "t1"}, {"terminal_id": "t1"}, id="terminalId"),
        pytest.param({"exitStatus": {}}, {"exit_status": {}}, id="exitStatus"),
        pytest.param({"exitCode": 0}, {"exit_code": 0}, id="exitCode"),
    ]

    @pytest.mark.parametrize("camel,expected", CAMEL_TO_SNAKE_CASES)
    def test_key_conversion(self, camel: dict, expected: dict):
        assert from_raw(camel) == expected

    def test_unknown_keys_converted(self):
        d = from_raw({"unknownKey": "value", "another": 123})
        assert d == {"unknown_key": "value", "another": 123}

    def test_mixed_known_unknown(self):
        d = from_raw({"sessionId": "s1", "customField": True})
        assert d["session_id"] == "s1"
        assert d["custom_field"] is True


# ── JSON serialization round-trip ──


class TestJsonRoundTrip:
    """Test full JSON serialization round-trip.

    Verifies: to_dict -> json.dumps -> json.loads -> from_raw.
    """

    def test_initialize_result_json_round_trip(self):
        obj = InitializeResult(
            protocol_version=1,
            agent_capabilities=AgentCapabilities(
                load_session=True,
                prompt_capabilities=PromptCapabilities(image=True),
            ),
            agent_info=ImplementationInfo(name="agent", version="1.0"),
        )
        wire = json.loads(json.dumps(to_dict(obj)))
        r = from_raw(wire)
        assert r["protocol_version"] == 1
        assert r["agent_info"]["name"] == "agent"

    def test_tool_call_update_json_round_trip(self):
        obj = ToolCallUpdate(
            tool_call_id="tc-1",
            title="Execute",
            kind=ToolKind.EXECUTE,
            status=ToolCallStatus.COMPLETED,
            locations=[ToolCallLocation(path="/a.py")],
            raw_input={"cmd": "ls"},
            raw_output={"stdout": "file.txt"},
        )
        wire = json.loads(json.dumps(to_dict(obj)))
        r = from_raw(wire)
        assert r["tool_call_id"] == "tc-1"
        assert r["raw_input"]["cmd"] == "ls"
        assert r["raw_output"]["stdout"] == "file.txt"

    def test_prompt_params_json_round_trip(self):
        obj = PromptParams(
            session_id="sess-1",
            prompt=[
                TextContent(text="Hello"),
                ImageContent(data="abc", mime_type="image/png"),
            ],
        )
        wire = json.loads(json.dumps(to_dict(obj)))
        r = from_raw(wire)
        assert r["session_id"] == "sess-1"
        assert len(r["prompt"]) == 2
