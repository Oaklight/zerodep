"""The PyYAML-compatible ``safe_*`` names.

Needs no PyYAML: the module is loaded by path, so the tests run in a
zero-dependency environment too.
"""

import importlib.util
import io
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parent / "yaml.py"
_spec = importlib.util.spec_from_file_location("zerodep_yaml_safe_names", _PATH)
assert _spec is not None and _spec.loader is not None
zy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(zy)


def test_safe_load_str_bytes_and_streams():
    assert zy.safe_load("a: 1") == {"a": 1}
    assert zy.safe_load(b"a: 1") == {"a": 1}
    assert zy.safe_load(io.StringIO("a: 1")) == {"a": 1}
    assert zy.safe_load(io.BytesIO(b"a: 1")) == {"a": 1}


def test_safe_load_decodes_non_ascii_bytes_as_utf_8():
    assert zy.safe_load("name: caf\u00e9".encode("utf-8")) == {"name": "caf\u00e9"}


def test_safe_load_drops_a_leading_bom():
    assert zy.safe_load(b"\xef\xbb\xbfa: 1") == {"a": 1}
    assert zy.safe_load(io.BytesIO(b"\xef\xbb\xbfa: 1")) == {"a": 1}


def test_safe_load_rejects_undecodable_bytes():
    with pytest.raises(UnicodeDecodeError):
        zy.safe_load("a: 1".encode("utf-16"))


def test_safe_load_all_reads_every_document():
    docs = zy.safe_load_all(io.BytesIO(b"a: 1\n---\nb: 2"))
    assert list(docs) == [{"a": 1}, {"b": 2}]


def test_safe_dump_names_are_the_plain_functions():
    assert zy.safe_dump is zy.dump
    assert zy.safe_dump_all is zy.dump_all
    assert zy.safe_load(zy.safe_dump({"a": [1, 2]})) == {"a": [1, 2]}


def test_star_import_exposes_the_safe_names():
    names = {"safe_load", "safe_load_all", "safe_dump", "safe_dump_all"}
    assert names <= set(zy.__all__)
