"""Tests for the loads() fast path: plain JSON skips preprocessing.

These tests need no reference library (unlike test_jsonx_correctness.py),
so they run wherever pytest is available.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from jsonx import JSONCDecodeError, loads  # noqa: E402

PLAIN = '{"a": 1, "b": [true, null, 1.5], "c": "has // and # and ,} inside"}'
JSONC = (
    "// leading comment\n"
    "{\n"
    '  "a": 1, # line comment\n'
    '  "b": [true, null,], /* block\n'
    "comment */\n"
    '  "c": "value",\n'
    "}"
)
JSONC_NESTED = '{"a": {"x": 1}, "b": {"y": 2}, // comment\n "c": {"z": 3}}'
MALFORMED = '{"a": 1,,}'


def test_plain_json_parses() -> None:
    assert loads(PLAIN) == json.loads(PLAIN)


def test_jsonc_still_parses() -> None:
    assert loads(JSONC) == {"a": 1, "b": [True, None], "c": "value"}


def test_fast_path_matches_preprocessed_result() -> None:
    """A plain-JSON document must parse identically with and without the
    preprocessing pass (JSON is a subset of JSONC, so the answers agree)."""
    document = json.dumps({"p": {f"k{i}": f"value {i}" for i in range(50)}}, indent=2)
    assert loads(document) == json.loads(document)


def test_malformed_raises_jsonc_decode_error() -> None:
    with pytest.raises(JSONCDecodeError):
        loads(MALFORMED)


def test_non_hook_kwargs_pass_through_on_fast_path() -> None:
    # ``strict`` is forwarded without opting out of the fast path.
    assert loads('{"a": 1}', strict=False) == {"a": 1}


def test_hooks_pass_through_on_plain_json() -> None:
    assert loads('{"a": 1.5}', parse_float=str) == {"a": "1.5"}
    assert loads('{"a": 1}', object_pairs_hook=list) == [("a", 1)]


def test_hooks_pass_through_on_jsonc_path() -> None:
    assert loads('{"a": 1.5, // c\n}', parse_float=str) == {"a": "1.5"}


def test_hooks_are_not_invoked_speculatively() -> None:
    """A JSONC document calls each hook once per decoded value.

    The fast path tries the raw text first; without the opt-out that failed
    attempt would invoke the caller's hooks on the values it had already
    decoded, and the fallback would invoke them again.
    """
    calls: list[object] = []

    def record(value: object) -> object:
        calls.append(value)
        return value

    result = loads(JSONC_NESTED, object_hook=record)
    assert result == {"a": {"x": 1}, "b": {"y": 2}, "c": {"z": 3}}
    assert len(calls) == 4, f"object_hook was called {len(calls)} times"


def test_custom_decoder_sees_preprocessed_text() -> None:
    """A custom decoder opts out of the fast path and gets the cleaned text."""
    seen: list[str] = []

    class RecordingDecoder(json.JSONDecoder):
        def decode(self, s: str, *args: object, **kwargs: object) -> object:
            seen.append(s)
            return super().decode(s, *args, **kwargs)

    assert loads('{"a": 1, // c\n}', cls=RecordingDecoder) == {"a": 1}
    assert len(seen) == 1, f"decoder was called {len(seen)} times"
    assert "// c" not in seen[0]


def test_hook_rejecting_with_decode_error_is_not_retried() -> None:
    """A hook's ``JSONDecodeError`` must not be overridden by the fallback.

    ``json.JSONDecodeError`` is the syntax-error signal, so a hook raising
    it looks like a bad document.  The fast path must not preprocess and
    parse the same text again: the retry would call the hook a second time
    and swallow its refusal.
    """
    calls: list[list[tuple[str, object]]] = []

    def reject(pairs: list[tuple[str, object]]) -> object:
        calls.append(pairs)
        raise json.JSONDecodeError("hook says no", "", 0)

    with pytest.raises(JSONCDecodeError) as excinfo:
        loads('{"a": 1}', object_pairs_hook=reject)

    assert "hook says no" in str(excinfo.value)
    assert len(calls) == 1, f"hook was called {len(calls)} times"


def test_hook_raising_value_error_propagates() -> None:
    def reject(pairs: list[tuple[str, object]]) -> object:
        raise ValueError("hook says no")

    with pytest.raises(ValueError, match="hook says no"):
        loads('{"a": 1}', object_pairs_hook=reject)


def test_bytes_input_is_a_known_limitation() -> None:
    """``loads`` accepts ``str`` only; this documents the current limitation.

    It is not a contract: stdlib ``json.loads`` also takes bytes, and the
    module could decode before the JSONC scanner if that support is wanted.
    """
    with pytest.raises(TypeError):
        loads(b'{"a": 1}')
