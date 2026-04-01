"""Correctness tests: zerodep jsonrpc."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jsonrpc import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    JSONRPC_VERSION,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    JSONRPCDispatcher,
    JSONRPCError,
    JSONRPCException,
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCTransport,
    next_id,
)

# ── Constants ──


class TestConstants:
    def test_version(self):
        assert JSONRPC_VERSION == "2.0"

    def test_error_codes(self):
        assert PARSE_ERROR == -32700
        assert INVALID_REQUEST == -32600
        assert METHOD_NOT_FOUND == -32601
        assert INVALID_PARAMS == -32602
        assert INTERNAL_ERROR == -32603


# ── JSONRPCError ──


class TestJSONRPCError:
    def test_defaults(self):
        err = JSONRPCError()
        assert err.code == INTERNAL_ERROR
        assert err.message == "Internal error"
        assert err.data is None

    def test_custom(self):
        err = JSONRPCError(code=-32001, message="Not found", data={"id": "t1"})
        assert err.code == -32001
        assert err.message == "Not found"
        assert err.data == {"id": "t1"}

    def test_to_dict_without_data(self):
        err = JSONRPCError(code=-32600, message="Invalid")
        d = err.to_dict()
        assert d == {"code": -32600, "message": "Invalid"}
        assert "data" not in d

    def test_to_dict_with_data(self):
        err = JSONRPCError(code=-32600, message="Invalid", data="details")
        d = err.to_dict()
        assert d == {"code": -32600, "message": "Invalid", "data": "details"}

    def test_from_dict(self):
        raw = {"code": -32700, "message": "Parse error", "data": [1, 2]}
        err = JSONRPCError.from_dict(raw)
        assert err.code == -32700
        assert err.message == "Parse error"
        assert err.data == [1, 2]

    def test_from_dict_no_data(self):
        raw = {"code": -32700, "message": "Parse error"}
        err = JSONRPCError.from_dict(raw)
        assert err.data is None

    def test_round_trip(self):
        err = JSONRPCError(code=-32001, message="Custom", data={"key": "val"})
        restored = JSONRPCError.from_dict(err.to_dict())
        assert restored.code == err.code
        assert restored.message == err.message
        assert restored.data == err.data


# ── JSONRPCRequest ──


class TestJSONRPCRequest:
    def test_defaults(self):
        req = JSONRPCRequest()
        assert req.method == ""
        assert req.params is None
        assert req.id is None
        assert req.jsonrpc == "2.0"

    def test_is_notification(self):
        assert JSONRPCRequest(method="notify").is_notification is True
        assert JSONRPCRequest(method="call", id=1).is_notification is False

    def test_to_dict_minimal(self):
        req = JSONRPCRequest(method="ping")
        d = req.to_dict()
        assert d == {"jsonrpc": "2.0", "method": "ping"}
        assert "id" not in d
        assert "params" not in d

    def test_to_dict_full(self):
        req = JSONRPCRequest(method="add", params={"a": 1}, id=42)
        d = req.to_dict()
        assert d == {"jsonrpc": "2.0", "method": "add", "id": 42, "params": {"a": 1}}

    def test_from_dict(self):
        raw = {"jsonrpc": "2.0", "method": "sub", "id": "abc", "params": {"x": 10}}
        req = JSONRPCRequest.from_dict(raw)
        assert req.method == "sub"
        assert req.id == "abc"
        assert req.params == {"x": 10}

    def test_from_dict_defaults(self):
        req = JSONRPCRequest.from_dict({})
        assert req.method == ""
        assert req.jsonrpc == "2.0"

    def test_round_trip(self):
        req = JSONRPCRequest(method="echo", params={"msg": "hi"}, id=7)
        restored = JSONRPCRequest.from_dict(req.to_dict())
        assert restored.method == req.method
        assert restored.params == req.params
        assert restored.id == req.id


# ── JSONRPCResponse ──


class TestJSONRPCResponse:
    def test_success_factory(self):
        resp = JSONRPCResponse.success(1, {"status": "ok"})
        assert resp.id == 1
        assert resp.result == {"status": "ok"}
        assert resp.error is None

    def test_to_dict_success(self):
        resp = JSONRPCResponse.success(1, "done")
        d = resp.to_dict()
        assert d == {"jsonrpc": "2.0", "id": 1, "result": "done"}
        assert "error" not in d

    def test_to_dict_error(self):
        err = JSONRPCError(code=-32600, message="Bad")
        resp = JSONRPCResponse(id=2, error=err)
        d = resp.to_dict()
        assert d["error"] == {"code": -32600, "message": "Bad"}
        assert "result" not in d

    def test_from_dict_success(self):
        raw = {"jsonrpc": "2.0", "id": 1, "result": [1, 2, 3]}
        resp = JSONRPCResponse.from_dict(raw)
        assert resp.result == [1, 2, 3]
        assert resp.error is None

    def test_from_dict_error(self):
        raw = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32700, "message": "Parse"},
        }
        resp = JSONRPCResponse.from_dict(raw)
        assert resp.error is not None
        assert resp.error.code == -32700

    def test_from_error_with_jsonrpc_error(self):
        err = JSONRPCError(code=-32001, message="Nope")
        resp = JSONRPCResponse.from_error(5, err)
        assert resp.id == 5
        assert resp.error is err

    def test_from_error_with_exception(self):
        exc = JSONRPCException(JSONRPCError(code=-32002, message="Exc"))
        resp = JSONRPCResponse.from_error(6, exc)
        assert resp.id == 6
        assert resp.error.code == -32002

    def test_from_error_with_duck_typed(self):
        class FakeError:
            code = -32010
            rpc_message = "Duck"
            data = {"x": 1}

        resp = JSONRPCResponse.from_error(7, FakeError())
        assert resp.error.code == -32010
        assert resp.error.message == "Duck"
        assert resp.error.data == {"x": 1}

    def test_round_trip_success(self):
        resp = JSONRPCResponse.success(10, {"key": "val"})
        raw = json.dumps(resp.to_dict())
        restored = JSONRPCResponse.from_dict(json.loads(raw))
        assert restored.id == 10
        assert restored.result == {"key": "val"}

    def test_round_trip_error(self):
        resp = JSONRPCResponse(
            id=11, error=JSONRPCError(code=-32600, message="Bad", data="info")
        )
        raw = json.dumps(resp.to_dict())
        restored = JSONRPCResponse.from_dict(json.loads(raw))
        assert restored.error.code == -32600
        assert restored.error.data == "info"


# ── JSONRPCException ──


class TestJSONRPCException:
    def test_wraps_error(self):
        err = JSONRPCError(code=-32001, message="Oops")
        exc = JSONRPCException(err)
        assert exc.error is err
        assert str(exc) == "Oops"

    def test_is_exception(self):
        exc = JSONRPCException(JSONRPCError())
        assert isinstance(exc, Exception)


# ── next_id ──


class TestNextId:
    def test_monotonic(self):
        a = next_id()
        b = next_id()
        c = next_id()
        assert b == a + 1
        assert c == b + 1

    def test_returns_int(self):
        assert isinstance(next_id(), int)


# ── JSONRPCDispatcher ──


class TestJSONRPCDispatcher:
    def test_register_and_dispatch(self):
        d = JSONRPCDispatcher()

        @d.register("echo")
        def handle_echo(params):
            return params

        req = JSONRPCRequest(method="echo", params={"msg": "hi"}, id=1)
        resp = d.dispatch(req)
        assert isinstance(resp, JSONRPCResponse)
        assert resp.result == {"msg": "hi"}

    def test_method_not_found(self):
        d = JSONRPCDispatcher()
        req = JSONRPCRequest(method="missing", id=1)
        resp = d.dispatch(req)
        assert resp.error is not None
        assert resp.error.code == METHOD_NOT_FOUND

    def test_handler_raises_jsonrpc_exception(self):
        d = JSONRPCDispatcher()

        @d.register("fail")
        def handle_fail(params):
            raise JSONRPCException(JSONRPCError(code=-32001, message="Custom"))

        resp = d.dispatch(JSONRPCRequest(method="fail", id=1))
        assert resp.error.code == -32001

    def test_handler_raises_generic_exception(self):
        d = JSONRPCDispatcher()

        @d.register("crash")
        def handle_crash(params):
            raise ValueError("boom")

        resp = d.dispatch(JSONRPCRequest(method="crash", id=1))
        assert resp.error.code == INTERNAL_ERROR
        assert "boom" in resp.error.message

    def test_streaming_dispatch(self):
        d = JSONRPCDispatcher()

        @d.register("stream")
        def handle_stream(params):
            yield {"chunk": 1}
            yield {"chunk": 2}

        req = JSONRPCRequest(method="stream", id=1)
        result = d.dispatch(req)
        responses = list(result)
        assert len(responses) == 2
        assert responses[0].result == {"chunk": 1}
        assert responses[1].result == {"chunk": 2}

    def test_streaming_error(self):
        d = JSONRPCDispatcher()

        @d.register("stream_fail")
        def handle_stream_fail(params):
            yield {"ok": True}
            raise JSONRPCException(JSONRPCError(code=-32099, message="Mid-stream"))

        req = JSONRPCRequest(method="stream_fail", id=1)
        responses = list(d.dispatch(req))
        assert len(responses) == 2
        assert responses[0].result == {"ok": True}
        assert responses[1].error.code == -32099


# ── JSONRPCTransport ──


class TestJSONRPCTransport:
    @pytest.fixture
    def transport_pair(self):
        """Create a transport connected to an in-memory stream pair."""
        loop = asyncio.new_event_loop()
        reader = asyncio.StreamReader()
        # Create a mock writer
        protocol = asyncio.StreamReaderProtocol(reader)
        transport_mock = type("MockTransport", (), {"is_closing": lambda self: False})()
        writer = asyncio.StreamWriter(transport_mock, protocol, reader, loop)
        t = JSONRPCTransport(reader, writer)
        yield t, reader
        loop.close()

    def test_read_message(self):
        async def _test():
            reader = asyncio.StreamReader()
            msg = {"jsonrpc": "2.0", "method": "ping", "id": 1}
            reader.feed_data((json.dumps(msg) + "\n").encode())
            reader.feed_eof()

            asyncio.StreamReaderProtocol(reader)
            t = JSONRPCTransport(reader, None)  # type: ignore[arg-type]
            result = await t.read_message()
            assert result == msg

            eof = await t.read_message()
            assert eof is None

        asyncio.run(_test())

    def test_read_skips_blank_lines(self):
        async def _test():
            reader = asyncio.StreamReader()
            reader.feed_data(b"\n\n")
            reader.feed_data(b'{"method":"x"}\n')
            reader.feed_eof()

            t = JSONRPCTransport(reader, None)  # type: ignore[arg-type]
            result = await t.read_message()
            assert result == {"method": "x"}

        asyncio.run(_test())

    def test_read_skips_malformed_json(self):
        async def _test():
            reader = asyncio.StreamReader()
            reader.feed_data(b"not json\n")
            reader.feed_data(b'{"ok":true}\n')
            reader.feed_eof()

            t = JSONRPCTransport(reader, None)  # type: ignore[arg-type]
            result = await t.read_message()
            assert result == {"ok": True}

        asyncio.run(_test())

    def test_write_message(self):
        async def _test():
            reader = asyncio.StreamReader()
            writer_reader = asyncio.StreamReader()

            class FakeTransport:
                def is_closing(self):
                    return False

                def write(self, data):
                    writer_reader.feed_data(data)

                def get_extra_info(self, *a, **kw):
                    return None

            ft = FakeTransport()
            protocol = asyncio.StreamReaderProtocol(reader)
            writer = asyncio.StreamWriter(
                ft, protocol, reader, asyncio.get_event_loop()
            )

            t = JSONRPCTransport(reader, writer)
            await t.write_message({"jsonrpc": "2.0", "id": 1, "result": "ok"})

            written = writer_reader._buffer  # noqa: SLF001
            lines = bytes(written).decode().strip().split("\n")
            assert len(lines) == 1
            parsed = json.loads(lines[0])
            assert parsed["result"] == "ok"

        asyncio.run(_test())

    def test_close(self):
        async def _test():
            reader = asyncio.StreamReader()

            class FakeTransport:
                closed = False

                def is_closing(self):
                    return self.closed

                def close(self):
                    self.closed = True

                def get_extra_info(self, *a, **kw):
                    return None

            ft = FakeTransport()
            protocol = asyncio.StreamReaderProtocol(reader)
            writer = asyncio.StreamWriter(
                ft, protocol, reader, asyncio.get_event_loop()
            )

            t = JSONRPCTransport(reader, writer)
            assert not t.is_closed
            await t.close()
            assert t.is_closed
            # Idempotent
            await t.close()
            assert t.is_closed

        asyncio.run(_test())
