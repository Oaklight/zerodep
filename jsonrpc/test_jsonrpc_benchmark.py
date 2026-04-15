"""Benchmark: zerodep jsonrpc vs jsonrpcserver.

Compares end-to-end dispatch performance (JSON string in → JSON string out)
since jsonrpcserver only operates on serialized JSON strings.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jsonrpc import (
    JSONRPCDispatcher,
    JSONRPCError,
    JSONRPCException,
    JSONRPCRequest,
    JSONRPCResponse,
    next_id,
)

# Reference library (skip if not installed)
jrpc_ref = pytest.importorskip("jsonrpcserver", reason="jsonrpcserver not installed")

# ── Setup: zerodep dispatcher ──

zd_dispatcher = JSONRPCDispatcher()


@zd_dispatcher.register("echo")
def _zd_echo(params):
    return params


@zd_dispatcher.register("fail")
def _zd_fail(params):
    raise JSONRPCException(JSONRPCError(code=-32001, message="Custom error"))


# ── Setup: jsonrpcserver dispatcher ──

from jsonrpcserver import Error, Result, Success, method  # noqa: E402
from jsonrpcserver import dispatch as ref_dispatch


@method
def echo(msg="") -> Result:
    return Success(msg)


@method
def fail() -> Result:
    return Error(-32001, "Custom error")


# ── Test data: JSON strings for end-to-end comparison ──

ECHO_JSON = json.dumps(
    {"jsonrpc": "2.0", "method": "echo", "params": {"msg": "hello"}, "id": 1}
)
FAIL_JSON = json.dumps({"jsonrpc": "2.0", "method": "fail", "params": {}, "id": 2})
NOT_FOUND_JSON = json.dumps({"jsonrpc": "2.0", "method": "missing", "id": 3})

# Pre-parsed for zerodep (it works with dicts, not JSON strings)
ECHO_DICT = json.loads(ECHO_JSON)
FAIL_DICT = json.loads(FAIL_JSON)
NOT_FOUND_DICT = json.loads(NOT_FOUND_JSON)

# Batch: 20 requests
BATCH_JSONS = [
    json.dumps(
        {"jsonrpc": "2.0", "method": "echo", "params": {"msg": f"item-{i}"}, "id": i}
    )
    for i in range(20)
]
BATCH_DICTS = [json.loads(j) for j in BATCH_JSONS]


# ── Helpers ──


def _zd_end_to_end(json_str: str) -> str:
    """zerodep: JSON string -> parse -> dispatch -> serialize -> JSON string."""
    req_dict = json.loads(json_str)
    req = JSONRPCRequest.from_dict(req_dict)
    resp = zd_dispatcher.dispatch(req)
    return json.dumps(resp.to_dict())


def _ref_end_to_end(json_str: str) -> str:
    """jsonrpcserver: JSON string -> dispatch -> JSON string."""
    return ref_dispatch(json_str)


# ── Dispatch benchmarks ──


class TestDispatchSuccess:
    def test_zerodep(self, benchmark):
        benchmark(_zd_end_to_end, ECHO_JSON)

    def test_jsonrpcserver(self, benchmark):
        benchmark(_ref_end_to_end, ECHO_JSON)


class TestDispatchError:
    def test_zerodep(self, benchmark):
        benchmark(_zd_end_to_end, FAIL_JSON)

    def test_jsonrpcserver(self, benchmark):
        benchmark(_ref_end_to_end, FAIL_JSON)


class TestDispatchNotFound:
    def test_zerodep(self, benchmark):
        benchmark(_zd_end_to_end, NOT_FOUND_JSON)

    def test_jsonrpcserver(self, benchmark):
        benchmark(_ref_end_to_end, NOT_FOUND_JSON)


class TestDispatchBatch:
    def test_zerodep(self, benchmark):
        def _run():
            return [_zd_end_to_end(j) for j in BATCH_JSONS]

        benchmark(_run)

    def test_jsonrpcserver(self, benchmark):
        def _run():
            return [_ref_end_to_end(j) for j in BATCH_JSONS]

        benchmark(_run)


# ── Serialization (zerodep only — jsonrpcserver has no model objects) ──

SMALL_REQ = JSONRPCRequest(method="echo", params={"msg": "hello"}, id=1)
SMALL_REQ_WIRE = SMALL_REQ.to_dict()

SMALL_ERR = JSONRPCError(code=-32001, message="Not found", data={"id": "t1"})
SMALL_ERR_WIRE = SMALL_ERR.to_dict()

MEDIUM_RESP = JSONRPCResponse.success(
    1,
    {
        "tasks": [
            {"id": f"task-{i}", "status": "completed", "result": {"value": i * 10}}
            for i in range(10)
        ]
    },
)
MEDIUM_RESP_WIRE = MEDIUM_RESP.to_dict()

LARGE_BATCH_REQS = [
    JSONRPCRequest(method=f"method_{i}", params={"index": i, "data": "x" * 100}, id=i)
    for i in range(50)
]
LARGE_BATCH_WIRE = [r.to_dict() for r in LARGE_BATCH_REQS]


class TestSerializeToDict:
    def test_request_to_dict(self, benchmark):
        benchmark(SMALL_REQ.to_dict)

    def test_response_to_dict(self, benchmark):
        benchmark(MEDIUM_RESP.to_dict)


class TestDeserializeFromDict:
    def test_request_from_dict(self, benchmark):
        benchmark(JSONRPCRequest.from_dict, SMALL_REQ_WIRE)

    def test_response_from_dict(self, benchmark):
        benchmark(JSONRPCResponse.from_dict, MEDIUM_RESP_WIRE)


class TestJsonRoundTrip:
    def test_json_round_trip(self, benchmark):
        def _run():
            wire = json.dumps(SMALL_REQ.to_dict())
            return JSONRPCRequest.from_dict(json.loads(wire))

        benchmark(_run)


class TestIdGeneration:
    def test_next_id(self, benchmark):
        benchmark(next_id)
