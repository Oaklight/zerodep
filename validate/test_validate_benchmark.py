"""Benchmark: zerodep validate vs pydantic."""

import os
import sys
from typing import Annotated

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from validate import Ge, Gt, Le, MaxLen, MinLen, json_schema, validate

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

pydantic = pytest.importorskip("pydantic", reason="pydantic not installed")


# ── Shared test data ──


class SimpleUserTD(TypedDict):
    name: str
    age: int
    email: str


class SimpleUserPydantic(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(strict=True)
    name: str
    age: int
    email: str


SIMPLE_DATA = {"name": "Alice", "age": 30, "email": "alice@example.com"}


class AddressTD(TypedDict):
    street: str
    city: str
    zip_code: str


class UserWithAddrTD(TypedDict):
    name: str
    age: int
    address: AddressTD


class AddressPydantic(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(strict=True)
    street: str
    city: str
    zip_code: str


class UserWithAddrPydantic(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(strict=True)
    name: str
    age: int
    address: AddressPydantic


NESTED_DATA = {
    "name": "Alice",
    "age": 30,
    "address": {"street": "123 Main St", "city": "NYC", "zip_code": "10001"},
}


class ConstrainedTD(TypedDict):
    name: Annotated[str, MinLen(1), MaxLen(100)]
    price: Annotated[float, Gt(0)]
    quantity: Annotated[int, Ge(0), Le(1000)]


class ConstrainedPydantic(pydantic.BaseModel):
    name: Annotated[str, pydantic.Field(min_length=1, max_length=100)]
    price: Annotated[float, pydantic.Field(gt=0)]
    quantity: Annotated[int, pydantic.Field(ge=0, le=1000)]


CONSTRAINED_DATA = {"name": "Widget", "price": 9.99, "quantity": 100}


class ItemTD(TypedDict):
    name: str
    price: float


ITEMS_DATA = [{"name": f"item_{i}", "price": float(i)} for i in range(50)]


# ── Benchmarks ──


class TestBenchmarkSimple:
    def test_ours(self, benchmark):
        benchmark(validate, SIMPLE_DATA, SimpleUserTD)

    def test_pydantic(self, benchmark):
        benchmark(SimpleUserPydantic.model_validate, SIMPLE_DATA)


class TestBenchmarkNested:
    def test_ours(self, benchmark):
        benchmark(validate, NESTED_DATA, UserWithAddrTD)

    def test_pydantic(self, benchmark):
        benchmark(UserWithAddrPydantic.model_validate, NESTED_DATA)


class TestBenchmarkConstrained:
    def test_ours(self, benchmark):
        benchmark(validate, CONSTRAINED_DATA, ConstrainedTD)

    def test_pydantic(self, benchmark):
        benchmark(ConstrainedPydantic.model_validate, CONSTRAINED_DATA)


class TestBenchmarkListOfDicts:
    def test_ours(self, benchmark):
        benchmark(validate, ITEMS_DATA, list[ItemTD])

    def test_pydantic(self, benchmark):
        class ItemPydantic(pydantic.BaseModel):
            model_config = pydantic.ConfigDict(strict=True)
            name: str
            price: float

        ta = pydantic.TypeAdapter(list[ItemPydantic])
        benchmark(ta.validate_python, ITEMS_DATA)


class TestBenchmarkJsonSchema:
    def test_ours(self, benchmark):
        benchmark(json_schema, ConstrainedTD)

    def test_pydantic(self, benchmark):
        benchmark(ConstrainedPydantic.model_json_schema)


# ── Discriminated union benchmarks (LLM payload simulation) ──
#
# Real LLM agent conversations contain:
# - Hundreds to thousands of messages
# - Each message has mixed content parts (text, tool_call, tool_result, etc.)
# - Dozens to hundreds of tool definitions
# - Deeply nested structures (messages > content parts > tool args)

from typing import Literal, Union


class _TextPart(TypedDict):
    type: Literal["text"]
    text: str


class _ImagePart(TypedDict):
    type: Literal["image"]
    url: str


class _ToolCallPart(TypedDict):
    type: Literal["tool_call"]
    tool_call_id: str
    name: str
    arguments: str


class _ToolResultPart(TypedDict):
    type: Literal["tool_result"]
    tool_call_id: str
    output: str


class _ReasoningPart(TypedDict):
    type: Literal["reasoning"]
    content: str


class _RefusalPart(TypedDict):
    type: Literal["refusal"]
    reason: str


class _CitationPart(TypedDict):
    type: Literal["citation"]
    source: str
    quote: str


class _AudioPart(TypedDict):
    type: Literal["audio"]
    data: str


class _FilePart(TypedDict):
    type: Literal["file"]
    path: str
    mime: str


class _MetaPart(TypedDict):
    type: Literal["meta"]
    key: str
    value: str


_ContentPart = Union[
    _TextPart,
    _ImagePart,
    _ToolCallPart,
    _ToolResultPart,
    _ReasoningPart,
    _RefusalPart,
    _CitationPart,
    _AudioPart,
    _FilePart,
    _MetaPart,
]

# Cycle through representative content parts
_PART_TEMPLATES = [
    {"type": "text", "text": "Hello, how can I help?"},
    {
        "type": "tool_call",
        "tool_call_id": "tc_1",
        "name": "read_file",
        "arguments": '{"path": "/tmp/x"}',
    },
    {"type": "tool_result", "tool_call_id": "tc_1", "output": "file contents here"},
    {"type": "reasoning", "content": "I need to think about this carefully..."},
    {"type": "text", "text": "Based on my analysis, here is the answer."},
]


def _build_flat_payload(n: int) -> list[dict]:
    """N content parts in a flat list."""
    return [_PART_TEMPLATES[i % len(_PART_TEMPLATES)] for i in range(n)]


class _Message(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: list[_ContentPart]


def _build_conversation(n_messages: int, parts_per_msg: int) -> list[dict]:
    """N messages, each with M content parts."""
    roles = ["user", "assistant"]
    return [
        {
            "role": roles[i % 2],
            "content": [
                _PART_TEMPLATES[j % len(_PART_TEMPLATES)] for j in range(parts_per_msg)
            ],
        }
        for i in range(n_messages)
    ]


class _ToolParam(TypedDict):
    name: str
    type: Literal["string", "integer", "boolean", "array", "object"]
    description: str
    required: bool


class _ToolDef(TypedDict):
    name: str
    description: str
    parameters: list[_ToolParam]


def _build_tools(n_tools: int, params_per_tool: int) -> list[dict]:
    """N tool definitions, each with M parameters."""
    return [
        {
            "name": f"tool_{i}",
            "description": f"Tool number {i} does something useful",
            "parameters": [
                {
                    "name": f"param_{j}",
                    "type": ["string", "integer", "boolean", "array", "object"][j % 5],
                    "description": f"Parameter {j} for tool {i}",
                    "required": j < 2,
                }
                for j in range(params_per_tool)
            ],
        }
        for i in range(n_tools)
    ]


# --- Flat union list: scaling content part count ---

# Small: 50 parts (simple request)
_FLAT_50 = _build_flat_payload(50)

# Medium: 500 parts (multi-turn agent conversation)
_FLAT_500 = _build_flat_payload(500)

# Large: 2000 parts (long agent session)
_FLAT_2000 = _build_flat_payload(2000)


class TestBenchmarkDiscUnionFlat50:
    def test_ours(self, benchmark):
        benchmark(validate, _FLAT_50, list[_ContentPart])


class TestBenchmarkDiscUnionFlat500:
    def test_ours(self, benchmark):
        benchmark(validate, _FLAT_500, list[_ContentPart])


class TestBenchmarkDiscUnionFlat2000:
    def test_ours(self, benchmark):
        benchmark(validate, _FLAT_2000, list[_ContentPart])


# --- Nested: messages with content parts ---

# 20 messages x 3 parts = 60 union validations + 20 message unions
_CONV_SMALL = _build_conversation(20, 3)

# 200 messages x 5 parts = 1000 union validations
_CONV_MEDIUM = _build_conversation(200, 5)

# 1000 messages x 5 parts = 5000 union validations (heavy agent session)
_CONV_LARGE = _build_conversation(1000, 5)


class TestBenchmarkConversationSmall:
    """20 messages x 3 parts."""

    def test_ours(self, benchmark):
        benchmark(validate, _CONV_SMALL, list[_Message])


class TestBenchmarkConversationMedium:
    """200 messages x 5 parts."""

    def test_ours(self, benchmark):
        benchmark(validate, _CONV_MEDIUM, list[_Message])


class TestBenchmarkConversationLarge:
    """1000 messages x 5 parts."""

    def test_ours(self, benchmark):
        benchmark(validate, _CONV_LARGE, list[_Message])


# --- Tool definitions: scaling tool count ---

# 10 tools x 5 params
_TOOLS_10 = _build_tools(10, 5)

# 50 tools x 8 params (agent with many tools)
_TOOLS_50 = _build_tools(50, 8)

# 200 tools x 10 params (heavy tool-use agent like Claude Code)
_TOOLS_200 = _build_tools(200, 10)


class TestBenchmarkTools10:
    def test_ours(self, benchmark):
        benchmark(validate, _TOOLS_10, list[_ToolDef])


class TestBenchmarkTools50:
    def test_ours(self, benchmark):
        benchmark(validate, _TOOLS_50, list[_ToolDef])


class TestBenchmarkTools200:
    def test_ours(self, benchmark):
        benchmark(validate, _TOOLS_200, list[_ToolDef])
