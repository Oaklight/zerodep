"""Correctness tests: zerodep YAML vs PyYAML.

The scalar and structural cases are generated from bounded grammars rather
than hand-listed, so every token in the grammar is checked against the same
reference oracle.  Bounded enumeration covers more inputs than the previous
hand-written tables while keeping the suite fast.
"""

import itertools
import os
import sys

import pytest

# Our yaml.py shadows PyYAML. Work around by temporarily manipulating sys.path
# and sys.modules to import the real PyYAML before importing ours.
_this_dir = os.path.dirname(__file__)

# Remove this directory (and project root) from path temporarily
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

# Also remove any cached 'yaml' module (our module from conftest/collection)
_cached_yaml = sys.modules.pop("yaml", None)

try:
    import yaml as _pyyaml

    if not hasattr(_pyyaml, "safe_load"):
        raise ImportError("Not the real PyYAML")
    _safe_load = _pyyaml.safe_load
    _safe_load_all = _pyyaml.safe_load_all
except ImportError:
    pytest.skip("PyYAML not installed", allow_module_level=True)
finally:
    # Restore sys.path and remove PyYAML from modules cache
    sys.path = _saved_path
    sys.modules.pop("yaml", None)
    if _cached_yaml is not None:
        sys.modules["yaml"] = _cached_yaml

sys.path.insert(0, _this_dir)
from yaml import (
    dump,
    load,
    load_all,
)

# ── Helpers ──


def _ours(text: str) -> object:
    return load(text)


def _theirs(text: str) -> object:
    return _safe_load(text)


def _same(ours: object, theirs: object) -> bool:
    """Equality that also treats two NaNs as equal."""
    if isinstance(ours, float) and isinstance(theirs, float):
        if ours != ours and theirs != theirs:
            return True
    return ours == theirs


# ── Generated scalar corpus ──

# Boolean/null words, every case variant accepted by YAML 1.1.
_BOOL_WORDS = ("true", "false", "yes", "no", "on", "off", "null")
_BOOL_TOKENS = sorted(
    {
        variant
        for word in _BOOL_WORDS
        for variant in (word, word.upper(), word.capitalize())
    }
    | {"~", "y", "n", "Y", "N", "Null", "NULL"}
)

# Every numeric form the module claims to support: integers with sign and
# base prefixes, floats, scientific notation, infinities and NaN spellings.
_NUMBER_TOKENS = [
    "0",
    "1",
    "-1",
    "+1",
    "-0",
    "42",
    "-7",
    "0.0",
    "3.14",
    "-2.5",
    ".5",
    "5.",
    "1e3",
    "1.0e+10",
    "1_000",
    "0x1A",
    "0xFF",
    "017",
    "0o17",
    "0b101",
    ".inf",
    "-.inf",
    "+.inf",
    ".nan",
    ".NaN",
    ".NAN",
]

_PLAIN_TOKENS = [
    "hello",
    "hello world",
    "a:b",
    "a#b",
    "a b c",
    "café",
    "- item",
    "#comment",
]

SCALAR_TOKENS = sorted(set(_BOOL_TOKENS) | set(_NUMBER_TOKENS) | set(_PLAIN_TOKENS))


def _block_documents() -> list[str]:
    """Generate valid block-style documents from a bounded grammar."""
    values = ["1", "true", "null", "hello", "3.14"]
    keys = ["a", "b", "c"]
    documents: list[str] = []

    for size in (1, 2):
        for chosen in itertools.combinations(keys, size):
            for combo in itertools.product(values, repeat=size):
                documents.append(
                    "\n".join(f"{key}: {value}" for key, value in zip(chosen, combo))
                )

    for size in (1, 2):
        for combo in itertools.product(values, repeat=size):
            documents.append("\n".join(f"- {value}" for value in combo))

    # Three-element cases are kept explicitly; repeating the grammar at size 3
    # would only re-check the same type-inference branches.
    documents.extend(
        [
            "- 1\n- 2\n- 3",
            "- hello\n- world",
            "- true\n- false\n- null",
            "a: 1\nb: 2\nc: true",
        ]
    )

    for value in values:
        documents.append(f"outer:\n  - {value}\n  - inner")
        documents.append(f"- name: {value}\n  value: {values[0]}")

    for depth in (1, 2, 3):
        lines = ["  " * level + f"k{level}:" for level in range(depth)]
        lines.append("  " * depth + "value")
        documents.append("\n".join(lines))

    return documents


def _flow_documents() -> list[str]:
    """Generate flow-style documents from a bounded grammar."""
    values = ["1", "true", "null", "hello"]
    documents = ["{}", "[]"]

    for size in (1, 2):
        for combo in itertools.product(values, repeat=size):
            documents.append("[" + ", ".join(combo) + "]")
    documents.append("[1, 2, 3]")
    for size in (1, 2):
        for combo in itertools.product(values, repeat=size):
            body = ", ".join(f"k{i}: {value}" for i, value in enumerate(combo))
            documents.append("{" + body + "}")
    documents.extend(["{a: [1, 2], b: {c: 3}}", "[{a: 1}, {b: 2}]"])
    return documents


def _quoted_documents() -> list[str]:
    """Quote every interesting scalar with both quote styles."""
    values = ["true", "42", "a b", "a:b", "#x", "", "line\\nbreak"]
    documents = []
    for value in values:
        documents.append(f"key: '{value}'")
        documents.append(f'key: "{value}"')
    return documents


STRUCTURAL_DOCUMENTS = _block_documents() + _flow_documents() + _quoted_documents()


# ── Test classes ──


class TestScalarTypes:
    def test_scalar_corpus_matches_reference(self):
        mismatches = []
        for text in SCALAR_TOKENS:
            ours = _ours(text)
            theirs = _theirs(text)
            if not _same(ours, theirs):
                mismatches.append((text, ours, theirs))
        assert not mismatches, f"scalar mismatches vs PyYAML: {mismatches!r}"


class TestStructures:
    def test_generated_documents_match_reference(self):
        mismatches = []
        for text in STRUCTURAL_DOCUMENTS:
            ours = _ours(text)
            theirs = _theirs(text)
            if not _same(ours, theirs):
                mismatches.append((text, ours, theirs))
        assert not mismatches, f"structure mismatches vs PyYAML: {mismatches!r}"


class TestMultipleDocuments:
    def test_generated_document_streams(self):
        scalars = ["1", "a: 1", "true"]
        mismatches = []
        for size in (1, 2):
            for combo in itertools.product(scalars, repeat=size):
                text = "---\n" + "\n---\n".join(combo)
                ours = list(load_all(text))
                theirs = list(_safe_load_all(text))
                if ours != theirs:
                    mismatches.append((text, ours, theirs))
        # A three-document stream is preserved explicitly.
        text = "---\n1\n---\n2\n---\n3"
        if list(load_all(text)) != list(_safe_load_all(text)):
            mismatches.append((text, list(load_all(text)), list(_safe_load_all(text))))
        assert not mismatches, f"stream mismatches vs PyYAML: {mismatches!r}"


def _generated_data() -> list[object]:
    """Bounded Python structures for the dump → load round-trip property."""
    scalars = [None, True, False, 0, 1, -1, 3.14, "hello", "true", "a b"]
    data: list[object] = [[value] for value in scalars]
    data += [[left, right] for left, right in itertools.product(scalars[:5], repeat=2)]
    data += [{"k": value} for value in scalars]
    data += [
        {"a": left, "b": right}
        for left, right in itertools.product(scalars[:5], repeat=2)
    ]
    data += [
        {"outer": {"inner": value, "seq": [value, other]}}
        for value in scalars[:5]
        for other in scalars[:3]
    ]
    data.append({"empty_dict": {}, "empty_list": []})
    return data


class TestDump:
    def test_dump_load_round_trip(self):
        mismatches = []
        for data in _generated_data():
            parsed = load(dump(data))
            if parsed != data:
                mismatches.append((data, parsed))
        assert not mismatches, f"dump/load round-trip failures: {mismatches!r}"

    def test_none_value(self):
        data = {"key": None}
        result = dump(data)
        assert "null" in result

    def test_bool_values(self):
        data = {"a": True, "b": False}
        result = dump(data)
        assert "true" in result
        assert "false" in result

    def test_empty_collections(self):
        data = {"empty_dict": {}, "empty_list": []}
        result = dump(data)
        assert "{}" in result
        assert "[]" in result

    def test_special_string_quoting(self):
        data = {"key": "true"}
        result = dump(data)
        # "true" as a string must be quoted
        parsed = load(result)
        assert parsed["key"] == "true"
        assert isinstance(parsed["key"], str)


class TestDumpOptions:
    def test_sort_keys_false(self):
        data = {"z": 1, "a": 2}
        result = dump(data, sort_keys=False)
        z_pos = result.index("z")
        a_pos = result.index("a")
        assert z_pos < a_pos

    def test_flow_style(self):
        data = {"a": 1, "b": 2}
        result = dump(data, default_flow_style=True)
        assert "{" in result

    def test_indent(self):
        data = {"a": {"b": 1}}
        result = dump(data, indent=4)
        lines = result.strip().split("\n")
        # Second line should have 4-space indent
        assert lines[1].startswith("    ")


class TestEdgeCases:
    def test_empty_string(self):
        assert load("") is None

    def test_whitespace_only(self):
        assert load("   \n  \n  ") is None

    def test_comment_only(self):
        assert load("# just a comment") is None

    def test_colon_in_value(self):
        text = "url: http://example.com"
        assert _ours(text) == _theirs(text)

    def test_mapping_inline_flow_list(self):
        text = "tags: [a, b, c]"
        assert _ours(text) == _theirs(text)

    def test_mapping_inline_flow_map(self):
        text = "config: {debug: true, port: 8080}"
        assert _ours(text) == _theirs(text)
