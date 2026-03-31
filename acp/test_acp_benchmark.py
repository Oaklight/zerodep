"""Benchmark: zerodep acp vs agent-client-protocol."""

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
    ImplementationInfo,
    InitializeResult,
    PromptCapabilities,
    PromptParams,
    TextContent,
    ToolCallLocation,
    ToolCallStatus,
    ToolCallUpdate,
    ToolKind,
    from_raw,
    to_dict,
)

# ── Test data ──

# -- SMALL: Single TextContent block --

ZD_SMALL = TextContent(text="Hello, world!")
REF_SMALL = acp_ref.TextContent(text="Hello, world!")

# -- MEDIUM: PromptParams with 10 content blocks + InitializeResult with capabilities --

ZD_MEDIUM_PROMPT = PromptParams(
    session_id="sess-medium",
    prompt=[TextContent(text=f"Message block {i}") for i in range(10)],
)
REF_MEDIUM_PROMPT = acp_ref.PromptRequest(
    session_id="sess-medium",
    prompt=[
        acp_ref.TextContentBlock(text=f"Message block {i}", type="text")
        for i in range(10)
    ],
)

ZD_MEDIUM_INIT = InitializeResult(
    protocol_version=1,
    agent_capabilities=AgentCapabilities(
        load_session=True,
        prompt_capabilities=PromptCapabilities(image=True, audio=True),
    ),
    agent_info=ImplementationInfo(name="bench-agent", version="1.0.0"),
)
REF_MEDIUM_INIT = acp_ref.InitializeResponse(
    protocol_version=1,
    agent_capabilities=acp_ref.AgentCapabilities(
        load_session=True,
        prompt_capabilities=acp_ref.PromptCapabilities(image=True, audio=True),
    ),
    agent_info=acp_ref.Implementation(name="bench-agent", version="1.0.0"),
)

# -- LARGE: 20 ToolCallUpdate objects with nested content, locations, and raw data --

ZD_LARGE = [
    ToolCallUpdate(
        tool_call_id=f"tc-{i}",
        title=f"Tool call {i}: "
        f"{'read' if i % 3 == 0 else 'edit' if i % 3 == 1 else 'execute'}",
        kind=[ToolKind.READ, ToolKind.EDIT, ToolKind.EXECUTE][i % 3],
        status=[
            ToolCallStatus.PENDING,
            ToolCallStatus.IN_PROGRESS,
            ToolCallStatus.COMPLETED,
            ToolCallStatus.FAILED,
        ][i % 4],
        locations=[
            ToolCallLocation(path=f"/project/src/file_{i}.py", line=i * 10 + 1),
            ToolCallLocation(path=f"/project/src/file_{i}_test.py", line=i * 5),
        ],
        raw_input={
            "command": f"operation_{i}",
            "args": {"file": f"file_{i}.py", "line": i * 10},
            "nested": {"deep": {"value": i * 42}},
        },
        raw_output={
            "stdout": f"Output line {i}\nSecond line {i}",
            "exit_code": 0 if i % 4 != 3 else 1,
            "duration_ms": i * 100 + 50,
        },
    )
    for i in range(20)
]
REF_LARGE = [
    acp_ref.ToolCallUpdate(
        tool_call_id=f"tc-{i}",
        title=f"Tool call {i}: "
        f"{'read' if i % 3 == 0 else 'edit' if i % 3 == 1 else 'execute'}",
        kind=["read", "edit", "execute"][i % 3],
        status=["pending", "in_progress", "completed", "failed"][i % 4],
        locations=[
            acp_ref.ToolCallLocation(path=f"/project/src/file_{i}.py", line=i * 10 + 1),
            acp_ref.ToolCallLocation(path=f"/project/src/file_{i}_test.py", line=i * 5),
        ],
        raw_input={
            "command": f"operation_{i}",
            "args": {"file": f"file_{i}.py", "line": i * 10},
            "nested": {"deep": {"value": i * 42}},
        },
        raw_output={
            "stdout": f"Output line {i}\nSecond line {i}",
            "exit_code": 0 if i % 4 != 3 else 1,
            "duration_ms": i * 100 + 50,
        },
    )
    for i in range(20)
]


# ── Serialization helpers ──


def _zd_serialize_small():
    return to_dict(ZD_SMALL)


def _ref_serialize_small():
    return REF_SMALL.model_dump(by_alias=True, exclude_none=True)


def _zd_serialize_medium():
    to_dict(ZD_MEDIUM_PROMPT)
    to_dict(ZD_MEDIUM_INIT)


def _ref_serialize_medium():
    REF_MEDIUM_PROMPT.model_dump(by_alias=True, exclude_none=True)
    REF_MEDIUM_INIT.model_dump(by_alias=True, exclude_none=True)


def _zd_serialize_large():
    return [to_dict(tc) for tc in ZD_LARGE]


def _ref_serialize_large():
    return [tc.model_dump(by_alias=True, exclude_none=True) for tc in REF_LARGE]


# ── Deserialization helpers ──

# Pre-compute wire dicts for deserialization benchmarks
_SMALL_WIRE = {"text": "Hello, world!", "type": "text"}
_MEDIUM_PROMPT_WIRE = {
    "sessionId": "sess-medium",
    "prompt": [{"text": f"Message block {i}", "type": "text"} for i in range(10)],
}
_MEDIUM_INIT_WIRE = {
    "protocolVersion": 1,
    "agentCapabilities": {
        "loadSession": True,
        "promptCapabilities": {"image": True, "audio": True},
    },
    "agentInfo": {"name": "bench-agent", "version": "1.0.0"},
}
_LARGE_WIRE = [to_dict(tc) for tc in ZD_LARGE]


def _zd_deserialize_small():
    return from_raw(_SMALL_WIRE)


def _ref_deserialize_small():
    return acp_ref.TextContent.model_validate(_SMALL_WIRE)


def _zd_deserialize_medium():
    from_raw(_MEDIUM_PROMPT_WIRE)
    from_raw(_MEDIUM_INIT_WIRE)


def _ref_deserialize_medium():
    acp_ref.PromptRequest.model_validate(_MEDIUM_PROMPT_WIRE)
    acp_ref.InitializeResponse.model_validate(_MEDIUM_INIT_WIRE)


def _zd_deserialize_large():
    return [from_raw(tc) for tc in _LARGE_WIRE]


def _ref_deserialize_large():
    return [acp_ref.ToolCallUpdate.model_validate(tc) for tc in _LARGE_WIRE]


# ── JSON round-trip helpers ──


def _zd_json_round_trip_small():
    wire = json.dumps(to_dict(ZD_SMALL))
    return from_raw(json.loads(wire))


def _ref_json_round_trip_small():
    wire = json.dumps(REF_SMALL.model_dump(by_alias=True, exclude_none=True))
    return acp_ref.TextContent.model_validate(json.loads(wire))


def _zd_json_round_trip_medium():
    w1 = json.dumps(to_dict(ZD_MEDIUM_PROMPT))
    w2 = json.dumps(to_dict(ZD_MEDIUM_INIT))
    from_raw(json.loads(w1))
    from_raw(json.loads(w2))


def _ref_json_round_trip_medium():
    w1 = json.dumps(REF_MEDIUM_PROMPT.model_dump(by_alias=True, exclude_none=True))
    w2 = json.dumps(REF_MEDIUM_INIT.model_dump(by_alias=True, exclude_none=True))
    acp_ref.PromptRequest.model_validate(json.loads(w1))
    acp_ref.InitializeResponse.model_validate(json.loads(w2))


def _zd_json_round_trip_large():
    wires = [json.dumps(to_dict(tc)) for tc in ZD_LARGE]
    return [from_raw(json.loads(w)) for w in wires]


def _ref_json_round_trip_large():
    wires = [
        json.dumps(tc.model_dump(by_alias=True, exclude_none=True)) for tc in REF_LARGE
    ]
    return [acp_ref.ToolCallUpdate.model_validate(json.loads(w)) for w in wires]


# ── Serialization benchmarks ──


class TestSerializeSmall:
    def test_zerodep(self, benchmark):
        benchmark(_zd_serialize_small)

    def test_acp_ref(self, benchmark):
        benchmark(_ref_serialize_small)


class TestSerializeMedium:
    def test_zerodep(self, benchmark):
        benchmark(_zd_serialize_medium)

    def test_acp_ref(self, benchmark):
        benchmark(_ref_serialize_medium)


class TestSerializeLarge:
    def test_zerodep(self, benchmark):
        benchmark(_zd_serialize_large)

    def test_acp_ref(self, benchmark):
        benchmark(_ref_serialize_large)


# ── Deserialization benchmarks ──


class TestDeserializeSmall:
    def test_zerodep(self, benchmark):
        benchmark(_zd_deserialize_small)

    def test_acp_ref(self, benchmark):
        benchmark(_ref_deserialize_small)


class TestDeserializeMedium:
    def test_zerodep(self, benchmark):
        benchmark(_zd_deserialize_medium)

    def test_acp_ref(self, benchmark):
        benchmark(_ref_deserialize_medium)


class TestDeserializeLarge:
    def test_zerodep(self, benchmark):
        benchmark(_zd_deserialize_large)

    def test_acp_ref(self, benchmark):
        benchmark(_ref_deserialize_large)


# ── JSON round-trip benchmarks ──


class TestJsonRoundTripSmall:
    def test_zerodep(self, benchmark):
        benchmark(_zd_json_round_trip_small)

    def test_acp_ref(self, benchmark):
        benchmark(_ref_json_round_trip_small)


class TestJsonRoundTripMedium:
    def test_zerodep(self, benchmark):
        benchmark(_zd_json_round_trip_medium)

    def test_acp_ref(self, benchmark):
        benchmark(_ref_json_round_trip_medium)


class TestJsonRoundTripLarge:
    def test_zerodep(self, benchmark):
        benchmark(_zd_json_round_trip_large)

    def test_acp_ref(self, benchmark):
        benchmark(_ref_json_round_trip_large)
