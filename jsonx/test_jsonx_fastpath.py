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
    '{\n'
    '  "a": 1, # line comment\n'
    '  "b": [true, null,], /* block\n'
    "comment */\n"
    '  "c": "value",\n'
    "}"
)
MALFORMED = '{"a": 1,,}'


def test_plain_json_parses() -> None:
    assert loads(PLAIN) == json.loads(PLAIN)


def test_jsonc_still_parses() -> None:
    assert loads(JSONC) == {"a": 1, "b": [True, None], "c": "value"}


def test_fast_path_matches_preprocessed_result() -> None:
    """A plain-JSON document must parse identically with and without the
    preprocessing pass (JSON is a subset of JSONC, so the answers agree)."""
    document = json.dumps(
        {"p": {f"k{i}": f"value {i}" for i in range(50)}}, indent=2
    )
    assert loads(document) == json.loads(document)


def test_malformed_raises_jsonc_decode_error() -> None:
    with pytest.raises(JSONCDecodeError):
        loads(MALFORMED)


def test_kwargs_pass_through_on_fast_path() -> None:
    assert loads('{"a": 1.5}', parse_float=str) == {"a": "1.5"}
    assert loads('{"a": 1}', object_pairs_hook=list) == [("a", 1)]


def test_kwargs_pass_through_on_jsonc_path() -> None:
    assert loads('{"a": 1.5, // c\n}', parse_float=str) == {"a": "1.5"}


def test_bytes_input_behaviour_unchanged() -> None:
    """Pre-existing behaviour: bytes documents were never supported by the
    preprocessing pass, and the fast path must not change that."""
    with pytest.raises(TypeError):
        loads(b'{"a": 1}')


def test_fast_path_perf_regression_guard() -> None:
    """The preprocessing regex passes cost ~14x the underlying parse on
    comment-free documents; the fast path should stay close to json.loads."""
    import timeit

    document = json.dumps(
        {"p": {f"k{i}": f"value {i}" for i in range(500)}}, indent=2
    )
    jsonx_time = min(timeit.repeat(lambda: loads(document), number=10, repeat=3))
    stdlib_time = min(
        timeit.repeat(lambda: json.loads(document), number=10, repeat=3)
    )
    # Allow generous headroom for CI noise; without the fast path this is >10.
    assert jsonx_time < stdlib_time * 3
