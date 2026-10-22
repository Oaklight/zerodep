"""Tests for decode error types on malformed escape sequences.

Needs no reference library, so it runs wherever pytest is available. The
conformance gate checks the same contract at fixture level; these pin the
module-level behaviour directly.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from toon import ToonDecodeError, decode  # noqa: E402

BAD_ESCAPES = [
    '"a\\b"',  # invalid escape in a top-level string
    'val: "a\\u00b"',  # truncated unicode escape
    'val: "a\\uD800b"',  # lone surrogate code point
    'val: "\\u+0ab"',  # sign before hex digits
    '"a\\x": 1',  # invalid escape in a quoted key
    'k: "a\\x"',  # non-strict mode still validates escapes
]


@pytest.mark.parametrize("text", BAD_ESCAPES)
def test_invalid_escape_raises_toon_decode_error(text: str) -> None:
    with pytest.raises(ToonDecodeError):
        decode(text)


def test_decode_error_is_not_a_value_error() -> None:
    """The documented contract is ToonDecodeError, and it must not subclass
    ValueError: a caller's ``except ValueError`` must not catch decode
    failures, and a caller's ``except ToonDecodeError`` must catch all of
    them."""
    assert not issubclass(ToonDecodeError, ValueError)


def test_trailing_backslash_raises_toon_decode_error() -> None:
    with pytest.raises(ToonDecodeError):
        decode('val: "a\\')
