"""Client behavior tests for zerodep acp (no reference library required)."""

import os
import sys

import pytest

_this_dir = os.path.dirname(__file__)
sys.path.insert(0, _this_dir)
for _name in list(sys.modules):
    if _name == "acp" or _name.startswith("acp."):
        del sys.modules[_name]

from acp import (  # noqa: E402
    ACP_PROTOCOL_VERSION,
    ACP_SPEC_REVISION,
    SUPPORTED_PROTOCOL_VERSIONS,
    ACPAgent,
    ACPClient,
    ClientCapabilities,
    CompactionSummaryChunkUpdate,
    CompactionUpdate,
    InitializeResult,
    NewSessionResult,
    NoticeUpdate,
    PromptResult,
    SessionClientCapabilities,
    StopReason,
    TextContent,
    UnsupportedProtocolVersion,
    UsageUpdate,
    negotiate_protocol_version,
    supports_update,
    to_dict,
)


def _client_with_response(response):
    """Return an ACPClient whose ``_call`` returns *response*."""

    client = ACPClient(["unused"])

    async def fake_call(method, params=None):
        return response

    client._call = fake_call  # type: ignore[method-assign]
    return client


class _FakeTransport:
    """Minimal transport that records requests and hands out request ids."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, object]] = []
        self._next_id = 0

    async def send_request(self, method, params=None):
        self._next_id += 1
        self.sent.append((method, params))
        return {"jsonrpc": "2.0", "id": self._next_id, "method": method}

    async def send_notification(self, method, params=None):
        self.sent.append((method, params))

    async def send_result(self, req_id, result):
        pass

    async def send_error(self, req_id, error):
        pass

    async def close(self):
        pass


class _ResolvingPending(dict):
    """Pending-request map that resolves a future as soon as it is stored."""

    def __init__(self, result):
        super().__init__()
        self._result = result

    def __setitem__(self, key, fut):
        super().__setitem__(key, fut)
        fut.set_result(self._result)


class TestProtocolVersionCap:
    """The supported ACP version is explicit and testable."""

    def test_constants_are_explicit(self):
        assert ACP_PROTOCOL_VERSION == 1
        assert SUPPORTED_PROTOCOL_VERSIONS == (1,)
        assert ACP_PROTOCOL_VERSION in SUPPORTED_PROTOCOL_VERSIONS
        assert ACP_SPEC_REVISION

    def test_negotiate_supported(self):
        assert negotiate_protocol_version(1) == 1

    def test_negotiate_unknown_clamps_to_cap(self):
        assert negotiate_protocol_version(2) == 1
        assert negotiate_protocol_version(0) == 1

    def test_negotiate_normalizes_non_int_values(self):
        assert negotiate_protocol_version(1.0) == 1
        assert negotiate_protocol_version(1.5) == 1
        assert negotiate_protocol_version("1") == 1
        assert negotiate_protocol_version("latest") == 1
        assert negotiate_protocol_version(None) == 1
        assert isinstance(negotiate_protocol_version(1.0), int)


def test_new_update_types_serialize():
    assert to_dict(UsageUpdate(used=1, size=2))["sessionUpdate"] == "usage_update"
    assert (
        to_dict(NoticeUpdate(severity="warning", title="MCP down"))["sessionUpdate"]
        == "notice"
    )
    assert (
        to_dict(CompactionUpdate(compaction_id="c1", status="completed"))[
            "sessionUpdate"
        ]
        == "compaction_update"
    )
    assert (
        to_dict(
            CompactionSummaryChunkUpdate(
                compaction_id="c1", content=TextContent(text="summary")
            )
        )["sessionUpdate"]
        == "compaction_summary_chunk"
    )


@pytest.mark.asyncio
async def test_initialize_parses_capabilities_and_auth():
    client = _client_with_response(
        {
            "protocolVersion": 1,
            "agentCapabilities": {
                "loadSession": True,
                "promptCapabilities": {
                    "image": True,
                    "audio": False,
                    "embeddedContext": True,
                },
                "mcpCapabilities": {"http": True, "sse": False},
                "sessionCapabilities": {
                    "list": {},
                    "resume": {},
                    "close": {},
                    "delete": {},
                    "additionalDirectories": {},
                },
                "auth": {"logout": {}},
            },
            "agentInfo": {"name": "demo", "version": "1.0", "title": "Demo"},
            "authMethods": [{"id": "login", "name": "Login", "description": "Sign in"}],
        }
    )
    result = await client.initialize()
    assert result.protocol_version == 1
    assert result.agent_info is not None
    assert result.agent_info.name == "demo"
    caps = result.agent_capabilities
    assert caps is not None
    assert caps.load_session is True
    assert caps.prompt_capabilities is not None
    assert caps.prompt_capabilities.image is True
    assert caps.prompt_capabilities.embedded_context is True
    assert caps.mcp_capabilities is not None
    assert caps.mcp_capabilities.http is True
    assert caps.session_capabilities is not None
    assert caps.session_capabilities.resume == {}
    assert caps.session_capabilities.additional_directories == {}
    assert caps.auth == {"logout": {}}
    assert result.auth_methods is not None
    assert result.auth_methods[0].id == "login"


@pytest.mark.asyncio
async def test_initialize_rejects_unsupported_version():
    client = _client_with_response({"protocolVersion": 2})
    with pytest.raises(UnsupportedProtocolVersion):
        await client.initialize()


@pytest.mark.asyncio
async def test_initialize_rejects_non_integer_version():
    client = _client_with_response({"protocolVersion": 1.5})
    with pytest.raises(UnsupportedProtocolVersion):
        await client.initialize()


@pytest.mark.asyncio
async def test_new_session_parses_modes_and_config_options():
    client = _client_with_response(
        {
            "sessionId": "s1",
            "modes": {
                "currentModeId": "code",
                "availableModes": [
                    {"id": "code", "name": "Code"},
                    {"id": "ask", "name": "Ask"},
                ],
            },
            "configOptions": [
                {
                    "id": "model",
                    "name": "Model",
                    "type": "select",
                    "currentValue": "m1",
                    "options": [{"value": "m1", "name": "M1"}],
                    "category": "model",
                }
            ],
        }
    )
    result = await client.new_session("/tmp")
    assert result.session_id == "s1"
    assert result.modes is not None
    assert result.modes.current_mode_id == "code"
    assert [m.id for m in result.modes.available_modes] == ["code", "ask"]
    assert result.config_options is not None
    assert result.config_options[0].id == "model"
    assert result.config_options[0].current_value == "m1"
    assert result.config_options[0].options[0].value == "m1"


@pytest.mark.asyncio
async def test_new_session_sends_additional_directories():
    captured = {}
    client = ACPClient(["unused"])

    async def fake_call(method, params=None):
        captured.update(params or {})
        return {"sessionId": "s1"}

    client._call = fake_call  # type: ignore[method-assign]
    await client.new_session("/tmp", additional_directories=["/a", "/b"])
    assert captured["additionalDirectories"] == ["/a", "/b"]


@pytest.mark.asyncio
async def test_session_lifecycle_methods_send_expected_params():
    captured = []
    client = ACPClient(["unused"])

    async def fake_call(method, params=None):
        captured.append((method, params))
        return {}

    client._call = fake_call  # type: ignore[method-assign]
    await client.resume_session("s1", "/tmp")
    await client.close_session("s1")
    await client.delete_session("s1")
    await client.authenticate("login")
    await client.logout()

    assert captured[0] == (
        "session/resume",
        {"sessionId": "s1", "cwd": "/tmp", "mcpServers": []},
    )
    assert captured[1] == ("session/close", {"sessionId": "s1"})
    assert captured[2] == ("session/delete", {"sessionId": "s1"})
    assert captured[3] == ("authenticate", {"methodId": "login"})
    assert captured[4] == ("logout", {})


@pytest.mark.asyncio
async def test_prompt_uses_real_stop_reason():
    client = ACPClient(["unused"])
    client._transport = _FakeTransport()  # type: ignore[assignment]
    client._pending = _ResolvingPending(  # type: ignore[assignment]
        {"stopReason": "max_tokens"}
    )

    updates = [u async for u in client.prompt("s1", "hi")]
    assert updates == []
    assert client.last_prompt_result is not None
    assert client.last_prompt_result.stop_reason == StopReason.MAX_TOKENS


@pytest.mark.asyncio
async def test_updates_are_routed_by_session_id():
    client = ACPClient(["unused"])
    client._transport = _FakeTransport()  # type: ignore[assignment]
    client._pending = _ResolvingPending({"stopReason": "end_turn"})  # type: ignore[assignment]

    await client._handle_notification(
        {
            "method": "session/update",
            "params": {"sessionId": "s1", "update": {"n": 1}},
        }
    )
    await client._handle_notification(
        {
            "method": "session/update",
            "params": {"sessionId": "s2", "update": {"n": 2}},
        }
    )

    assert [u["update"]["n"] for u in client._drain_remaining_updates("s1")] == [1]
    assert [u["update"]["n"] for u in client._drain_remaining_updates("s2")] == [2]
    assert client._drain_remaining_updates("s1") == []


@pytest.mark.asyncio
async def test_prompt_result_is_per_session():
    client = ACPClient(["unused"])
    client._transport = _FakeTransport()  # type: ignore[assignment]
    client._pending = _ResolvingPending(  # type: ignore[assignment]
        {"stopReason": "max_tokens"}
    )

    await client.prompt_simple("s1", "hi")

    result = client.prompt_result("s1")
    assert result is not None
    assert result.stop_reason == StopReason.MAX_TOKENS
    assert client.prompt_result("s2") is None


@pytest.mark.asyncio
async def test_stale_drain_is_per_session():
    client = ACPClient(["unused"])
    queue = client._queue_for("s1")
    queue.put_nowait({"sessionId": "s1", "update": {"n": 1}})

    client._drain_stale_updates("s2")

    assert not queue.empty()
    assert queue.get_nowait()["update"]["n"] == 1


@pytest.mark.asyncio
async def test_prompt_simple_uses_real_stop_reason():
    client = ACPClient(["unused"])
    client._transport = _FakeTransport()  # type: ignore[assignment]
    client._pending = _ResolvingPending(  # type: ignore[assignment]
        {"stopReason": "refusal"}
    )

    updates, result = await client.prompt_simple("s1", "hi")
    assert updates == []
    assert result.stop_reason == StopReason.REFUSAL


@pytest.mark.asyncio
async def test_unknown_stop_reason_is_not_reported_as_end_turn():
    client = ACPClient(["unused"])
    client._transport = _FakeTransport()  # type: ignore[assignment]
    client._pending = _ResolvingPending(  # type: ignore[assignment]
        {"stopReason": "future_reason"}
    )

    _, result = await client.prompt_simple("s1", "hi")
    assert result.stop_reason == StopReason.UNKNOWN
    assert result.raw_stop_reason == "future_reason"


class _CapturingAgent(ACPAgent):
    """Minimal agent that records the parsed ``initialize`` params."""

    def __init__(self) -> None:
        super().__init__()
        self.init_params = None

    async def on_initialize(self, params):
        self.init_params = params
        return InitializeResult(protocol_version=ACP_PROTOCOL_VERSION)

    async def on_new_session(self, params):
        return NewSessionResult(session_id="s")

    async def on_prompt(self, params):
        return PromptResult(stop_reason=StopReason.END_TURN)


@pytest.mark.asyncio
async def test_agent_parses_extended_client_capabilities():
    agent = _CapturingAgent()
    await agent._handle_method(
        "initialize",
        {
            "protocolVersion": 1,
            "clientCapabilities": {
                "terminal": True,
                "fs": {"readTextFile": True, "writeTextFile": False},
                "session": {
                    "notices": {},
                    "compaction": {},
                    "configOptions": {"boolean": {}},
                },
                "elicitation": {"form": {}, "url": {}},
                "auth": {"terminal": {}},
            },
        },
    )
    caps = agent.init_params.client_capabilities
    assert caps is not None
    assert caps.terminal is True
    assert caps.fs is not None
    assert caps.fs.read_text_file is True
    assert caps.fs.write_text_file is False
    assert caps.session is not None
    assert caps.session.notices == {}
    assert caps.session.compaction == {}
    assert caps.session.config_options == {"boolean": {}}
    assert caps.elicitation is not None
    assert caps.elicitation.form == {}
    assert caps.elicitation.url == {}
    assert caps.auth == {"terminal": {}}


@pytest.mark.asyncio
async def test_agent_tolerates_null_capability_groups():
    agent = _CapturingAgent()
    await agent._handle_method(
        "initialize",
        {"protocolVersion": 1, "clientCapabilities": {"fs": None, "session": None}},
    )
    caps = agent.init_params.client_capabilities
    assert caps is not None
    assert caps.fs is not None
    assert caps.fs.read_text_file is False
    assert caps.session is not None
    assert caps.session.notices is None
    assert caps.elicitation is None
    assert caps.auth is None


def test_supports_update_gates_capability_updates():
    assert supports_update(None, "agent_message_chunk") is True
    assert supports_update(None, "notice") is False
    caps = ClientCapabilities(session=SessionClientCapabilities(notices={}))
    assert supports_update(caps, "notice") is True
    assert supports_update(caps, "compaction_update") is False
    assert supports_update(caps, "compaction_summary_chunk") is False
    caps.session = SessionClientCapabilities(compaction={})
    assert supports_update(caps, "compaction_summary_chunk") is True


@pytest.mark.asyncio
async def test_agent_remembers_client_capabilities_for_update_gating():
    agent = _CapturingAgent()
    await agent._handle_method(
        "initialize",
        {"protocolVersion": 1, "clientCapabilities": {"session": {"notices": {}}}},
    )
    assert agent.supports_update("notice") is True
    assert agent.supports_update("compaction_update") is False


class _MinimalAgent(ACPAgent):
    """Agent relying on the base-class ``on_initialize``."""

    async def on_new_session(self, params):
        return NewSessionResult(session_id="s")

    async def on_prompt(self, params):
        return PromptResult(stop_reason=StopReason.END_TURN)


class _WrongVersionAgent(_MinimalAgent):
    async def on_initialize(self, params):
        return InitializeResult(protocol_version=99)


class _FloatVersionAgent(_MinimalAgent):
    async def on_initialize(self, params):
        return InitializeResult(protocol_version=1.5)


@pytest.mark.asyncio
async def test_agent_default_initialize_negotiates_version():
    agent = _MinimalAgent()
    result = await agent._handle_method("initialize", {"protocolVersion": 2})
    assert result.protocol_version == ACP_PROTOCOL_VERSION


@pytest.mark.asyncio
async def test_agent_rejects_unsupported_result_version():
    agent = _WrongVersionAgent()
    with pytest.raises(UnsupportedProtocolVersion):
        await agent._handle_method("initialize", {"protocolVersion": 1})


@pytest.mark.asyncio
async def test_agent_rejects_non_integer_result_version():
    agent = _FloatVersionAgent()
    with pytest.raises(UnsupportedProtocolVersion):
        await agent._handle_method("initialize", {"protocolVersion": 1})


@pytest.mark.asyncio
async def test_echo_agent_round_trip():
    """Exercise the full client/server loop with the built-in echo agent."""
    module = os.path.join(_this_dir, "acp.py")
    client = ACPClient([sys.executable, module])
    await client.start()
    try:
        init = await client.initialize()
        assert init.protocol_version == ACP_PROTOCOL_VERSION
        session = await client.new_session("/tmp")
        updates = [u async for u in client.prompt(session.session_id, "hello")]
        assert updates
        assert updates[0]["update"]["sessionUpdate"] == "agent_message_chunk"
        assert client.last_prompt_result is not None
        assert client.last_prompt_result.stop_reason == StopReason.END_TURN
    finally:
        await client.stop()
