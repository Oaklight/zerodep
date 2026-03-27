"""Correctness tests: zerodep YAML vs PyYAML."""

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
from yaml import dump, load, load_all

# ── Helpers ──


def _ours(text: str) -> object:
    return load(text)


def _theirs(text: str) -> object:
    return _safe_load(text)


# ── Test vectors ──

SCALAR_CASES = [
    pytest.param("null", id="null"),
    pytest.param("~", id="tilde_null"),
    pytest.param("Null", id="null_cap"),
    pytest.param("true", id="true"),
    pytest.param("false", id="false"),
    pytest.param("True", id="true_cap"),
    pytest.param("False", id="false_cap"),
    pytest.param("yes", id="yes"),
    pytest.param("no", id="no"),
    pytest.param("on", id="on"),
    pytest.param("off", id="off"),
    pytest.param("42", id="int"),
    pytest.param("-7", id="negative_int"),
    pytest.param("0", id="zero"),
    pytest.param("3.14", id="float"),
    pytest.param("-2.5", id="negative_float"),
    pytest.param("1.0e+10", id="scientific"),
    pytest.param(".inf", id="inf"),
    pytest.param("-.inf", id="neg_inf"),
    pytest.param(".nan", id="nan_val"),
    pytest.param("0x1A", id="hex_int"),
    pytest.param("017", id="octal_int"),
    pytest.param("hello world", id="plain_string"),
]

MAPPING_CASES = [
    pytest.param("name: Alice", id="simple"),
    pytest.param("name: Alice\nage: 30", id="two_keys"),
    pytest.param("key: true\nother: null", id="bool_and_null"),
    pytest.param("count: 42\nprice: 9.99", id="numeric_values"),
    pytest.param("empty:", id="empty_value"),
]

SEQUENCE_CASES = [
    pytest.param("- 1\n- 2\n- 3", id="int_list"),
    pytest.param("- hello\n- world", id="string_list"),
    pytest.param("- true\n- false\n- null", id="mixed_types"),
]

NESTED_CASES = [
    pytest.param(
        "person:\n  name: Alice\n  age: 30",
        id="nested_mapping",
    ),
    pytest.param(
        "items:\n  - apple\n  - banana\n  - cherry",
        id="mapping_with_list",
    ),
    pytest.param(
        "- name: Alice\n  age: 30\n- name: Bob\n  age: 25",
        id="list_of_mappings",
    ),
    pytest.param(
        "a:\n  b:\n    c: deep",
        id="deeply_nested",
    ),
]

FLOW_CASES = [
    pytest.param("{}", id="empty_mapping"),
    pytest.param("[]", id="empty_sequence"),
    pytest.param("{a: 1, b: 2}", id="flow_mapping"),
    pytest.param("[1, 2, 3]", id="flow_sequence"),
    pytest.param("{a: [1, 2], b: {c: 3}}", id="nested_flow"),
    pytest.param("[{a: 1}, {b: 2}]", id="flow_list_of_maps"),
]

QUOTED_CASES = [
    pytest.param("key: 'single quoted'", id="single_quoted"),
    pytest.param('key: "double quoted"', id="double_quoted"),
    pytest.param("key: 'true'", id="quoted_bool"),
    pytest.param("key: '42'", id="quoted_int"),
    pytest.param('key: "line\\nbreak"', id="escaped_newline"),
    pytest.param("key: ''", id="empty_single_quoted"),
    pytest.param('key: ""', id="empty_double_quoted"),
]


# ── Test classes ──


class TestScalarTypes:
    @pytest.mark.parametrize("text", SCALAR_CASES)
    def test_matches_reference(self, text: str):
        ours = _ours(text)
        theirs = _theirs(text)
        if isinstance(theirs, float) and isinstance(ours, float):
            # Handle NaN comparison
            if theirs != theirs:  # NaN
                assert ours != ours
                return
        assert ours == theirs


class TestBlockMappings:
    @pytest.mark.parametrize("text", MAPPING_CASES)
    def test_matches_reference(self, text: str):
        assert _ours(text) == _theirs(text)


class TestBlockSequences:
    @pytest.mark.parametrize("text", SEQUENCE_CASES)
    def test_matches_reference(self, text: str):
        assert _ours(text) == _theirs(text)


class TestNestedStructures:
    @pytest.mark.parametrize("text", NESTED_CASES)
    def test_matches_reference(self, text: str):
        assert _ours(text) == _theirs(text)


class TestFlowStyle:
    @pytest.mark.parametrize("text", FLOW_CASES)
    def test_matches_reference(self, text: str):
        assert _ours(text) == _theirs(text)


class TestQuotedStrings:
    @pytest.mark.parametrize("text", QUOTED_CASES)
    def test_matches_reference(self, text: str):
        assert _ours(text) == _theirs(text)


class TestMultipleDocuments:
    def test_two_documents(self):
        text = "---\na: 1\n---\nb: 2"
        ours = list(load_all(text))
        theirs = list(_safe_load_all(text))
        assert ours == theirs

    def test_three_documents(self):
        text = "---\n1\n---\n2\n---\n3"
        ours = list(load_all(text))
        theirs = list(_safe_load_all(text))
        assert ours == theirs


class TestDump:
    def test_simple_mapping(self):
        data = {"name": "Alice", "age": 30}
        ours = load(dump(data))
        assert ours == data

    def test_simple_sequence(self):
        data = [1, 2, 3]
        ours = load(dump(data))
        assert ours == data

    def test_nested(self):
        data = {"person": {"name": "Alice", "scores": [95, 87, 91]}}
        ours = load(dump(data))
        assert ours == data

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

    def test_unicode(self):
        text = "name: こんにちは"
        assert _ours(text) == _theirs(text)

    def test_colon_in_value(self):
        text = "url: http://example.com"
        assert _ours(text) == _theirs(text)

    def test_mapping_inline_flow_list(self):
        text = "tags: [a, b, c]"
        assert _ours(text) == _theirs(text)

    def test_mapping_inline_flow_map(self):
        text = "config: {debug: true, port: 8080}"
        assert _ours(text) == _theirs(text)
