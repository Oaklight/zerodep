"""Correctness tests: zerodep TOON vs toon_format."""

import os
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path, PurePosixPath

import pytest

# ── Import toon_format for comparison ──

try:
    import toon_format as _tf
except ImportError:
    pytest.skip("toon_format not installed", allow_module_level=True)

# Import our implementation
sys.path.insert(0, os.path.dirname(__file__))
from toon import (  # noqa: E402
    DecodeOptions,
    EncodeOptions,
    ToonDecodeError,
    decode,
    encode,
)

# ── Helpers ──


def assert_encode_same(data):
    """Assert our encode matches toon_format.encode."""
    ours = encode(data)
    theirs = _tf.encode(data)
    assert ours == theirs, f"Encode mismatch:\n  ours:   {ours!r}\n  theirs: {theirs!r}"


def assert_roundtrip(data, options=None):
    """Assert encode → decode roundtrip."""
    encoded = encode(data, options)
    dec_opts = None
    if options and "indent" in options:
        dec_opts = DecodeOptions(indent=options["indent"])
    decoded = decode(encoded, dec_opts)
    assert decoded == data, (
        f"Roundtrip mismatch:\n"
        f"  original: {data!r}\n"
        f"  encoded:  {encoded!r}\n"
        f"  decoded:  {decoded!r}"
    )


# ── Test: encode primitives ──


class TestEncodePrimitives:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (42, "42"),
            (0, "0"),
            (-7, "-7"),
            (3.14, "3.14"),
            (True, "true"),
            (False, "false"),
            (None, "null"),
            ("hello", "hello"),
        ],
        ids=["int", "zero", "negative", "float", "true", "false", "null", "string"],
    )
    def test_primitive_encoding(self, value, expected):
        assert encode(value) == expected
        assert_encode_same(value)

    def test_empty_string(self):
        assert encode("") == '""'
        assert_encode_same("")

    def test_string_with_colon(self):
        result = encode("has:colon")
        assert result.startswith('"')
        assert_encode_same("has:colon")

    def test_string_with_quotes(self):
        assert_encode_same('say "hi"')

    def test_string_with_newline(self):
        assert_encode_same("line1\nline2")


# ── Test: encode objects ──


class TestEncodeObjects:
    def test_empty_object(self):
        assert encode({}) == ""
        assert_encode_same({})

    def test_simple_object(self):
        data = {"name": "Alice", "age": 30}
        assert_encode_same(data)

    def test_bool_null_values(self):
        data = {"flag": True, "empty": None, "val": False}
        assert_encode_same(data)

    def test_nested_object(self):
        data = {"user": {"name": "Alice", "profile": {"city": "NYC"}}}
        assert_encode_same(data)

    def test_key_order_preserved(self):
        data = OrderedDict([("z", 1), ("a", 2), ("m", 3)])
        result = encode(data)
        lines = result.strip().split("\n")
        keys = [ln.split(":")[0].strip() for ln in lines]
        assert keys == ["z", "a", "m"]


# ── Test: encode arrays ──


class TestEncodeArrays:
    def test_empty_array(self):
        assert encode([]) == "[0]:"
        assert_encode_same([])

    def test_primitive_array(self):
        assert_encode_same([1, 2, 3])

    def test_string_array(self):
        assert_encode_same(["a", "b", "c"])

    def test_mixed_primitives(self):
        assert_encode_same([1, "hello", True, None])

    def test_tabular(self):
        data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        assert_encode_same(data)

    def test_non_tabular_objects(self):
        data = [{"name": "A", "age": 1}, {"name": "B", "extra": 2}]
        assert_encode_same(data)

    def test_array_of_arrays(self):
        assert_encode_same([[1, 2], [3, 4]])

    def test_nested_with_arrays(self):
        data = {"user": {"name": "Alice", "tags": ["a", "b"]}}
        assert_encode_same(data)


# ── Test: normalization ──


class TestNormalization:
    def test_none_to_null(self):
        assert encode(None) == "null"

    def test_tuple_to_list(self):
        data = {"items": (1, 2, 3)}
        encoded = encode(data)
        decoded = decode(encoded)
        assert decoded["items"] == [1, 2, 3]

    def test_set_to_sorted_list(self):
        data = {"tags": {3, 1, 2}}
        encoded = encode(data)
        decoded = decode(encoded)
        assert decoded["tags"] == [1, 2, 3]

    def test_frozenset_to_sorted_list(self):
        data = {"items": frozenset([3, 1, 2])}
        encoded = encode(data)
        decoded = decode(encoded)
        assert decoded["items"] == [1, 2, 3]

    def test_decimal(self):
        data = {"price": Decimal("19.99")}
        encoded = encode(data)
        assert "19.99" in encoded
        assert_encode_same(data)

    def test_path(self):
        data = {"file": Path("/tmp/test.txt")}
        encoded = encode(data)
        assert "/tmp/test.txt" in encoded
        assert_encode_same(data)

    def test_posix_path(self):
        data = {"p": PurePosixPath("/usr/bin/python")}
        assert_encode_same(data)

    def test_inf_to_null(self):
        assert encode(float("inf")) == "null"
        assert_encode_same(float("inf"))

    def test_neg_inf_to_null(self):
        assert encode(float("-inf")) == "null"
        assert_encode_same(float("-inf"))

    def test_nan_to_null(self):
        assert encode(float("nan")) == "null"

    def test_negative_zero(self):
        result = encode({"val": -0.0})
        assert "-0" not in result
        assert "val: 0" in result

    def test_callable_to_null(self):
        result = encode(lambda x: x)
        assert result == "null"

    def test_empty_set(self):
        data = {"empty": set()}
        encoded = encode(data)
        decoded = decode(encoded)
        assert decoded["empty"] == []

    def test_empty_tuple(self):
        data = {"empty": ()}
        encoded = encode(data)
        decoded = decode(encoded)
        assert decoded["empty"] == []

    def test_non_finite_in_array(self):
        data = [1, float("nan"), 3]
        result = encode(data)
        assert "null" in result

    def test_datetime_iso(self):
        from datetime import datetime

        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = encode({"ts": dt})
        assert "2024-01-15T10:30:00" in result

    def test_date_iso(self):
        from datetime import date

        d = date(2024, 1, 15)
        result = encode({"d": d})
        assert "2024-01-15" in result


# ── Test: number precision ──


class TestNumberPrecision:
    def test_no_scientific_notation(self):
        data = {"big": 1000000, "small": 0.000001}
        result = encode(data)
        assert "e" not in result.lower()

    def test_large_int_roundtrip(self):
        n = 2**60
        assert_roundtrip({"val": n})

    @pytest.mark.parametrize(
        "value",
        [42, -123, 0, 3.14, 0.0001, -0.00001, 999999999999999],
        ids=["int", "neg", "zero", "float", "small", "negsmall", "large"],
    )
    def test_numeric_roundtrip(self, value):
        assert_roundtrip({"v": value})


# ── Test: decode primitives ──


class TestDecodePrimitives:
    @pytest.mark.parametrize(
        "toon,expected",
        [
            ("42", 42),
            ("3.14", 3.14),
            ("true", True),
            ("false", False),
            ("null", None),
            ("hello world", "hello world"),
            ('"quoted string"', "quoted string"),
        ],
        ids=["int", "float", "true", "false", "null", "unquoted", "quoted"],
    )
    def test_primitive_decode(self, toon, expected):
        assert decode(toon) == expected

    def test_leading_zero_is_string(self):
        result = decode("code: 05")
        assert result == {"code": "05"}
        assert isinstance(result["code"], str)

    def test_leading_zero_array(self):
        result = decode("codes[3]: 01,02,03")
        assert result == {"codes": ["01", "02", "03"]}

    def test_zero_is_number(self):
        result = decode("value: 0")
        assert result["value"] == 0
        assert isinstance(result["value"], int)

    def test_exponent_notation(self):
        result = decode("a: 1e-6")
        assert abs(result["a"] - 1e-6) < 1e-12

    def test_exponent_in_array(self):
        result = decode("values[3]: 1e2,2e-1,3E+4")
        assert result == {"values": [100.0, 0.2, 30000.0]}


# ── Test: decode objects ──


class TestDecodeObjects:
    def test_empty_input(self):
        assert decode("") == {}

    def test_whitespace_input(self):
        assert decode("   \n  \n   ") == {}

    def test_simple_object(self):
        toon = "name: Alice\nage: 30"
        assert decode(toon) == {"name": "Alice", "age": 30}

    def test_nested_object(self):
        toon = "user:\n  name: Alice\n  age: 30"
        assert decode(toon) == {"user": {"name": "Alice", "age": 30}}

    def test_key_order_preserved(self):
        toon = "z: 1\na: 2\nm: 3\nb: 4"
        result = decode(toon)
        assert list(result.keys()) == ["z", "a", "m", "b"]

    def test_indent_4(self):
        toon = "parent:\n    child:\n        value: 42"
        result = decode(toon, DecodeOptions(indent=4))
        assert result == {"parent": {"child": {"value": 42}}}


# ── Test: decode arrays ──


class TestDecodeArrays:
    def test_inline_array(self):
        assert decode("[3]: 1,2,3") == [1, 2, 3]

    def test_inline_string_array(self):
        assert decode("[3]: a,b,c") == ["a", "b", "c"]

    def test_empty_array(self):
        assert decode("[0]:") == []

    def test_tabular(self):
        toon = "[2]{id,name}:\n  1,Alice\n  2,Bob"
        assert decode(toon) == [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]

    def test_list_items(self):
        toon = "[2]:\n  - name: A\n    age: 1\n  - name: B\n    age: 2"
        assert decode(toon) == [
            {"name": "A", "age": 1},
            {"name": "B", "age": 2},
        ]

    def test_array_of_arrays(self):
        toon = "[2]:\n  - [2]: 1,2\n  - [2]: 3,4"
        assert decode(toon) == [[1, 2], [3, 4]]

    def test_order_preserved(self):
        result = decode("items[5]: 5,1,9,2,7")
        assert result["items"] == [5, 1, 9, 2, 7]


# ── Test: encode options ──


class TestEncodeOptions:
    def test_tab_delimiter(self):
        result = encode([1, 2, 3], EncodeOptions(delimiter="\t"))
        ref = _tf.encode([1, 2, 3], {"delimiter": "\t"})
        assert result == ref

    def test_pipe_delimiter(self):
        result = encode([1, 2, 3], EncodeOptions(delimiter="|"))
        ref = _tf.encode([1, 2, 3], {"delimiter": "|"})
        assert result == ref

    def test_length_marker(self):
        result = encode([1, 2, 3], EncodeOptions(lengthMarker="#"))
        assert "[#3]:" in result

    def test_custom_indent(self):
        data = {"parent": {"child": 1}}
        result = encode(data, EncodeOptions(indent=4))
        lines = result.split("\n")
        assert lines[1].startswith("    ")


# ── Test: decode options ──


class TestDecodeOptions:
    def test_strict_length_mismatch(self):
        with pytest.raises(ToonDecodeError):
            decode("items[5]: a,b,c", DecodeOptions(strict=True))

    def test_non_strict_length_mismatch(self):
        result = decode("items[5]: a,b,c", DecodeOptions(strict=False))
        assert result == {"items": ["a", "b", "c"]}

    def test_custom_indent_decode(self):
        toon = "user:\n   id: 1"
        result = decode(toon, DecodeOptions(indent=3))
        assert result == {"user": {"id": 1}}


# ── Test: roundtrip ──


class TestRoundtrip:
    @pytest.mark.parametrize(
        "data",
        [
            {"name": "Alice", "age": 30},
            [1, 2, 3],
            [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}],
            {"user": {"name": "Alice", "tags": ["a", "b"]}},
            {"flag": True, "empty": None, "val": False},
            [[1, 2], [3, 4]],
            [1, "hello", True, None],
        ],
        ids=[
            "object",
            "int-array",
            "tabular",
            "nested",
            "boolnull",
            "array-of-arrays",
            "mixed-primitives",
        ],
    )
    def test_encode_decode_roundtrip(self, data):
        assert_roundtrip(data)

    @pytest.mark.parametrize(
        "data",
        [
            {"items": [1, 2, 3]},
            {"items": [1, 2, 3]},
            {"parent": {"child": {"value": 42}}},
        ],
        ids=["comma", "default", "nested"],
    )
    def test_roundtrip_with_ref(self, data):
        """Verify our roundtrip matches toon_format roundtrip."""
        ref_encoded = _tf.encode(data)
        our_encoded = encode(data)
        assert our_encoded == ref_encoded

        ref_decoded = _tf.decode(ref_encoded)
        our_decoded = decode(our_encoded)
        assert our_decoded == ref_decoded


# ── Test: error handling ──


class TestErrors:
    def test_unterminated_string(self):
        with pytest.raises(ToonDecodeError, match="[Uu]nterminated"):
            decode('text: "unterminated')

    def test_invalid_escape(self):
        with pytest.raises((ToonDecodeError, ValueError)):
            decode(r'text: "invalid\x"')

    def test_tabs_in_indentation_strict(self):
        with pytest.raises(ToonDecodeError, match="[Tt]ab"):
            decode("key:\n\tvalue: 1", DecodeOptions(strict=True))


# ── Test: strings that look like other types ──


class TestStringEdgeCases:
    def test_numeric_string_quoted(self):
        data = {"code": "42"}
        encoded = encode(data)
        assert '"42"' in encoded
        assert_roundtrip(data)

    def test_bool_string_quoted(self):
        data = {"val": "true"}
        encoded = encode(data)
        assert '"true"' in encoded
        assert_roundtrip(data)

    def test_null_string_quoted(self):
        data = {"val": "null"}
        encoded = encode(data)
        assert '"null"' in encoded
        assert_roundtrip(data)

    def test_octal_like_string_quoted(self):
        data = {"code": "0123"}
        encoded = encode(data)
        assert '"0123"' in encoded
        assert_roundtrip(data)


# ── Test: complex structures ──


class TestComplexStructures:
    def test_object_with_multiple_array_types(self):
        data = {
            "name": "test",
            "items": [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}],
            "nested": {"x": [1, 2, 3]},
            "flag": True,
        }
        assert_encode_same(data)
        assert_roundtrip(data)

    def test_deeply_nested(self):
        data = {"a": {"b": {"c": {"d": 1}}}}
        assert_encode_same(data)
        assert_roundtrip(data)

    def test_object_with_array_fields(self):
        data = {"tags": ["a", "b", "c"], "nums": [1, 2]}
        assert_encode_same(data)
        assert_roundtrip(data)

    def test_three_level_tabular(self):
        data = {
            "employees": [
                {"id": 1, "name": "Alice", "active": True},
                {"id": 2, "name": "Bob", "active": False},
                {"id": 3, "name": "Charlie", "active": True},
            ]
        }
        assert_encode_same(data)
        assert_roundtrip(data)

    def test_mixed_nested_arrays(self):
        data = [
            {"name": "A", "data": {"x": 1}},
            {"name": "B", "data": {"x": 2}},
        ]
        assert_encode_same(data)
        assert_roundtrip(data)


# ── Test: cross-implementation decode ──


class TestCrossImplementation:
    """Decode text produced by toon_format with our decoder and vice versa."""

    @pytest.mark.parametrize(
        "data",
        [
            {"name": "Alice", "age": 30},
            [1, 2, 3],
            [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}],
            {"a": {"b": [1, 2]}},
            [],
            [True, False, None],
            [[1], [2, 3]],
        ],
        ids=[
            "object",
            "int-array",
            "tabular",
            "nested",
            "empty-array",
            "bool-array",
            "array-of-arrays",
        ],
    )
    def test_decode_ref_encoded(self, data):
        """Our decode on toon_format's encode."""
        ref = _tf.encode(data)
        if not ref.strip():
            return
        ours = decode(ref)
        expected = _tf.decode(ref)
        assert ours == expected

    @pytest.mark.parametrize(
        "data",
        [
            {"name": "Alice", "age": 30},
            [1, 2, 3],
            [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}],
        ],
        ids=["object", "array", "tabular"],
    )
    def test_ref_decode_our_encoded(self, data):
        """toon_format decode on our encode."""
        ours = encode(data)
        result = _tf.decode(ours)
        assert result == data
