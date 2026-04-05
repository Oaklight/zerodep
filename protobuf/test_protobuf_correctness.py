"""Correctness tests: zerodep protobuf module."""

import os
import sys
from enum import IntEnum

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from protobuf import (
    WireType,
    bool_,
    decode_tag,
    decode_varint,
    double,
    encode_varint,
    field,
    fixed32,
    fixed64,
    float32,
    int32,
    int64,
    make_tag,
    map_field,
    message,
    repeated,
    sfixed32,
    sfixed64,
    sint32,
    sint64,
    uint32,
    uint64,
    zigzag_decode,
    zigzag_encode,
)

# ============================================================================
# Wire-format primitives
# ============================================================================


class TestVarint:
    def test_zero(self):
        assert encode_varint(0) == b"\x00"
        val, pos = decode_varint(b"\x00", 0)
        assert val == 0 and pos == 1

    def test_small(self):
        assert encode_varint(1) == b"\x01"
        assert encode_varint(127) == b"\x7f"

    def test_two_bytes(self):
        assert encode_varint(128) == b"\x80\x01"
        assert encode_varint(300) == b"\xac\x02"
        val, pos = decode_varint(b"\xac\x02", 0)
        assert val == 300

    def test_max_uint64(self):
        max_val = (1 << 64) - 1
        encoded = encode_varint(max_val)
        val, pos = decode_varint(encoded, 0)
        assert val == max_val

    def test_negative_twos_complement(self):
        # Proto3 encodes negative int32/int64 as 10-byte two's complement
        encoded = encode_varint(-1)
        val, _ = decode_varint(encoded, 0)
        assert val == 0xFFFFFFFFFFFFFFFF

    def test_decode_offset(self):
        data = b"\x00\x00\xac\x02\x00"
        val, pos = decode_varint(data, 2)
        assert val == 300 and pos == 4

    def test_decode_truncated(self):
        with pytest.raises(ValueError, match="Unexpected end"):
            decode_varint(b"\x80", 0)

    def test_decode_too_long(self):
        # 11 continuation bytes
        data = bytes([0x80] * 11)
        with pytest.raises(ValueError, match="too long"):
            decode_varint(data, 0)


class TestZigZag:
    @pytest.mark.parametrize(
        "signed, unsigned",
        [(0, 0), (-1, 1), (1, 2), (-2, 3), (2, 4), (-2147483648, 4294967295)],
    )
    def test_roundtrip(self, signed, unsigned):
        assert zigzag_encode(signed) == unsigned
        assert zigzag_decode(unsigned) == signed


class TestTags:
    def test_pack_unpack(self):
        tag_bytes = make_tag(1, WireType.VARINT)
        fn, wt, pos = decode_tag(tag_bytes, 0)
        assert fn == 1 and wt == WireType.VARINT

    def test_large_field_number(self):
        tag_bytes = make_tag(536870911, WireType.LEN)
        fn, wt, pos = decode_tag(tag_bytes, 0)
        assert fn == 536870911 and wt == WireType.LEN

    def test_all_wire_types(self):
        for wt in WireType:
            tag_bytes = make_tag(42, wt)
            fn, decoded_wt, _ = decode_tag(tag_bytes, 0)
            assert fn == 42 and decoded_wt == wt


class TestFixedEncodings:
    def test_fixed32_roundtrip(self):
        from protobuf import decode_fixed32, encode_fixed32

        data = encode_fixed32(0xDEADBEEF)
        val, pos = decode_fixed32(data, 0)
        assert val == 0xDEADBEEF and pos == 4

    def test_fixed64_roundtrip(self):
        from protobuf import decode_fixed64, encode_fixed64

        data = encode_fixed64(0xDEADBEEFCAFEBABE)
        val, pos = decode_fixed64(data, 0)
        assert val == 0xDEADBEEFCAFEBABE and pos == 8

    def test_sfixed32_negative(self):
        from protobuf import decode_sfixed32, encode_sfixed32

        data = encode_sfixed32(-42)
        val, pos = decode_sfixed32(data, 0)
        assert val == -42

    def test_sfixed64_negative(self):
        from protobuf import decode_sfixed64, encode_sfixed64

        data = encode_sfixed64(-1234567890123)
        val, pos = decode_sfixed64(data, 0)
        assert val == -1234567890123

    def test_float_roundtrip(self):
        from protobuf import decode_float, encode_float

        data = encode_float(3.14)
        val, _ = decode_float(data, 0)
        assert abs(val - 3.14) < 1e-5

    def test_double_roundtrip(self):
        from protobuf import decode_double, encode_double

        data = encode_double(3.141592653589793)
        val, _ = decode_double(data, 0)
        assert val == 3.141592653589793


# ============================================================================
# Scalar types & message basics
# ============================================================================


class TestSimpleMessage:
    def test_basic_roundtrip(self):
        @message
        class Simple:
            name: str = field(1)
            value: int32 = field(2)

        obj = Simple(name="hello", value=42)
        data = obj.serialize()
        parsed = Simple.parse(data)
        assert parsed.name == "hello"
        assert parsed.value == 42

    def test_empty_message(self):
        @message
        class Empty:
            pass

        obj = Empty()
        data = obj.serialize()
        assert data == b""
        parsed = Empty.parse(data)
        assert isinstance(parsed, Empty)

    def test_default_values_not_serialized(self):
        @message
        class Msg:
            name: str = field(1)
            value: int32 = field(2)

        obj = Msg(name="", value=0)
        data = obj.serialize()
        assert data == b""  # All at proto3 zero-values

    def test_proto3_defaults(self):
        @message
        class Defaults:
            s: str = field(1)
            i: int32 = field(2)
            b: bool_ = field(3)
            f: float32 = field(4)

        obj = Defaults()
        assert obj.s == ""
        assert obj.i == 0
        assert obj.b is False
        assert obj.f == 0.0


class TestAllScalarTypes:
    def test_int32_positive(self):
        @message
        class M:
            v: int32 = field(1)

        obj = M(v=2147483647)
        parsed = M.parse(obj.serialize())
        assert parsed.v == 2147483647

    def test_int32_negative(self):
        @message
        class M:
            v: int32 = field(1)

        obj = M(v=-1)
        parsed = M.parse(obj.serialize())
        assert parsed.v == -1

    def test_int64(self):
        @message
        class M:
            v: int64 = field(1)

        obj = M(v=9223372036854775807)
        parsed = M.parse(obj.serialize())
        assert parsed.v == 9223372036854775807

    def test_int64_negative(self):
        @message
        class M:
            v: int64 = field(1)

        obj = M(v=-9223372036854775808)
        parsed = M.parse(obj.serialize())
        assert parsed.v == -9223372036854775808

    def test_uint32(self):
        @message
        class M:
            v: uint32 = field(1)

        obj = M(v=4294967295)
        parsed = M.parse(obj.serialize())
        assert parsed.v == 4294967295

    def test_uint64(self):
        @message
        class M:
            v: uint64 = field(1)

        obj = M(v=18446744073709551615)
        parsed = M.parse(obj.serialize())
        assert parsed.v == 18446744073709551615

    def test_sint32(self):
        @message
        class M:
            v: sint32 = field(1)

        for val in [0, 1, -1, 2147483647, -2147483648]:
            parsed = M.parse(M(v=val).serialize())
            assert parsed.v == val

    def test_sint64(self):
        @message
        class M:
            v: sint64 = field(1)

        for val in [0, 1, -1, 2**62, -(2**62)]:
            parsed = M.parse(M(v=val).serialize())
            assert parsed.v == val

    def test_fixed32(self):
        @message
        class M:
            v: fixed32 = field(1)

        obj = M(v=0xDEADBEEF)
        parsed = M.parse(obj.serialize())
        assert parsed.v == 0xDEADBEEF

    def test_fixed64(self):
        @message
        class M:
            v: fixed64 = field(1)

        obj = M(v=0xDEADBEEFCAFEBABE)
        parsed = M.parse(obj.serialize())
        assert parsed.v == 0xDEADBEEFCAFEBABE

    def test_sfixed32(self):
        @message
        class M:
            v: sfixed32 = field(1)

        for val in [0, -1, 42, -2147483648, 2147483647]:
            parsed = M.parse(M(v=val).serialize())
            assert parsed.v == val

    def test_sfixed64(self):
        @message
        class M:
            v: sfixed64 = field(1)

        for val in [0, -1, 42, -(2**62)]:
            parsed = M.parse(M(v=val).serialize())
            assert parsed.v == val

    def test_float32(self):
        @message
        class M:
            v: float32 = field(1)

        obj = M(v=3.14)
        parsed = M.parse(obj.serialize())
        assert abs(parsed.v - 3.14) < 1e-5

    def test_double(self):
        @message
        class M:
            v: double = field(1)

        obj = M(v=3.141592653589793)
        parsed = M.parse(obj.serialize())
        assert parsed.v == 3.141592653589793

    def test_bool(self):
        @message
        class M:
            v: bool_ = field(1)

        obj = M(v=True)
        parsed = M.parse(obj.serialize())
        assert parsed.v is True

        # False is zero-value, should roundtrip via default
        obj2 = M(v=False)
        assert obj2.serialize() == b""
        parsed2 = M.parse(b"")
        assert parsed2.v is False

    def test_string(self):
        @message
        class M:
            v: str = field(1)

        obj = M(v="hello world 你好")
        parsed = M.parse(obj.serialize())
        assert parsed.v == "hello world 你好"

    def test_bytes_field(self):
        @message
        class M:
            v: bytes = field(1)

        obj = M(v=b"\x00\x01\xff\xfe")
        parsed = M.parse(obj.serialize())
        assert parsed.v == b"\x00\x01\xff\xfe"


# ============================================================================
# Nested messages
# ============================================================================


class TestNestedMessages:
    def test_simple_nesting(self):
        @message
        class Inner:
            value: int32 = field(1)

        @message
        class Outer:
            inner: Inner = field(1)
            name: str = field(2)

        obj = Outer(inner=Inner(value=42), name="test")
        parsed = Outer.parse(obj.serialize())
        assert parsed.inner.value == 42
        assert parsed.name == "test"

    def test_none_nested(self):
        @message
        class Inner:
            value: int32 = field(1)

        @message
        class Outer:
            inner: Inner = field(1)

        obj = Outer()
        assert obj.inner is None
        data = obj.serialize()
        assert data == b""

    def test_deep_nesting(self):
        @message
        class Level3:
            val: int32 = field(1)

        @message
        class Level2:
            child: Level3 = field(1)

        @message
        class Level1:
            child: Level2 = field(1)

        obj = Level1(child=Level2(child=Level3(val=99)))
        parsed = Level1.parse(obj.serialize())
        assert parsed.child.child.val == 99


# ============================================================================
# Repeated fields
# ============================================================================


class TestRepeated:
    def test_repeated_int32(self):
        @message
        class M:
            values: repeated[int32] = field(1)

        obj = M(values=[1, 2, 3, 4, 5])
        parsed = M.parse(obj.serialize())
        assert parsed.values == [1, 2, 3, 4, 5]

    def test_repeated_empty(self):
        @message
        class M:
            values: repeated[int32] = field(1)

        obj = M(values=[])
        data = obj.serialize()
        assert data == b""
        parsed = M.parse(data)
        assert parsed.values == []

    def test_repeated_string(self):
        @message
        class M:
            names: repeated[str] = field(1)

        obj = M(names=["alice", "bob", "charlie"])
        parsed = M.parse(obj.serialize())
        assert parsed.names == ["alice", "bob", "charlie"]

    def test_repeated_bytes(self):
        @message
        class M:
            data: repeated[bytes] = field(1)

        obj = M(data=[b"\x01\x02", b"\x03\x04"])
        parsed = M.parse(obj.serialize())
        assert parsed.data == [b"\x01\x02", b"\x03\x04"]

    def test_repeated_message(self):
        @message
        class Item:
            id: int32 = field(1)
            name: str = field(2)

        @message
        class Container:
            items: repeated[Item] = field(1)

        items = [Item(id=1, name="a"), Item(id=2, name="b")]
        obj = Container(items=items)
        parsed = Container.parse(obj.serialize())
        assert len(parsed.items) == 2
        assert parsed.items[0].id == 1
        assert parsed.items[0].name == "a"
        assert parsed.items[1].id == 2

    def test_repeated_sint32(self):
        @message
        class M:
            values: repeated[sint32] = field(1)

        obj = M(values=[-3, -2, -1, 0, 1, 2, 3])
        parsed = M.parse(obj.serialize())
        assert parsed.values == [-3, -2, -1, 0, 1, 2, 3]

    def test_repeated_double(self):
        @message
        class M:
            values: repeated[double] = field(1)

        obj = M(values=[1.1, 2.2, 3.3])
        parsed = M.parse(obj.serialize())
        assert parsed.values == [1.1, 2.2, 3.3]

    def test_repeated_bool(self):
        @message
        class M:
            flags: repeated[bool_] = field(1)

        obj = M(flags=[True, False, True, True])
        parsed = M.parse(obj.serialize())
        assert parsed.flags == [True, False, True, True]


# ============================================================================
# Enum fields
# ============================================================================


class TestEnum:
    def test_basic_enum(self):
        class Color(IntEnum):
            RED = 0
            GREEN = 1
            BLUE = 2

        @message
        class M:
            color: Color = field(1)

        obj = M(color=Color.BLUE)
        parsed = M.parse(obj.serialize())
        assert parsed.color == Color.BLUE
        assert parsed.color == 2

    def test_enum_zero_default(self):
        class Status(IntEnum):
            UNKNOWN = 0
            ACTIVE = 1

        @message
        class M:
            status: Status = field(1)

        obj = M()
        data = obj.serialize()
        assert data == b""  # zero-value not serialized

    def test_repeated_enum(self):
        class Color(IntEnum):
            RED = 0
            GREEN = 1
            BLUE = 2

        @message
        class M:
            colors: repeated[Color] = field(1)

        obj = M(colors=[Color.RED, Color.GREEN, Color.BLUE])
        parsed = M.parse(obj.serialize())
        assert parsed.colors == [Color.RED, Color.GREEN, Color.BLUE]

    def test_unknown_enum_value(self):
        class Status(IntEnum):
            OK = 0
            ERROR = 1

        @message
        class M:
            status: Status = field(1)

        # Simulate receiving an unknown enum value (999)
        # Encode manually: tag=0x08 (field 1, varint), value=999
        tag = make_tag(1, WireType.VARINT)
        data = tag + encode_varint(999)
        parsed = M.parse(data)
        assert parsed.status == 999  # preserved as int


# ============================================================================
# Map fields
# ============================================================================


class TestMapField:
    def test_string_to_int32(self):
        @message
        class M:
            attrs: map_field[str, int32] = field(1)

        obj = M(attrs={"a": 1, "b": 2, "c": 3})
        parsed = M.parse(obj.serialize())
        assert parsed.attrs == {"a": 1, "b": 2, "c": 3}

    def test_int32_to_string(self):
        @message
        class M:
            lookup: map_field[int32, str] = field(1)

        obj = M(lookup={1: "one", 2: "two"})
        parsed = M.parse(obj.serialize())
        assert parsed.lookup == {1: "one", 2: "two"}

    def test_string_to_message(self):
        @message
        class Value:
            data: int32 = field(1)

        @message
        class M:
            items: map_field[str, Value] = field(1)

        obj = M(items={"x": Value(data=10), "y": Value(data=20)})
        parsed = M.parse(obj.serialize())
        assert parsed.items["x"].data == 10
        assert parsed.items["y"].data == 20

    def test_empty_map(self):
        @message
        class M:
            attrs: map_field[str, str] = field(1)

        obj = M(attrs={})
        data = obj.serialize()
        assert data == b""

    def test_string_to_string(self):
        @message
        class M:
            env: map_field[str, str] = field(1)

        obj = M(env={"HOME": "/home/user", "PATH": "/usr/bin"})
        parsed = M.parse(obj.serialize())
        assert parsed.env == {"HOME": "/home/user", "PATH": "/usr/bin"}


# ============================================================================
# Oneof fields
# ============================================================================


class TestOneof:
    def test_oneof_serialization(self):
        @message
        class M:
            text: str = field(1, oneof="content")
            image_url: str = field(2, oneof="content")
            value: int32 = field(3)

        # Set only text
        obj = M(text="hello", value=42)
        parsed = M.parse(obj.serialize())
        assert parsed.text == "hello"
        assert parsed.image_url == ""  # default
        assert parsed.value == 42

    def test_oneof_descriptor(self):
        @message
        class M:
            a: str = field(1, oneof="choice")
            b: int32 = field(2, oneof="choice")
            c: str = field(3)

        desc = M._proto_descriptor
        assert "choice" in desc.oneof_groups
        assert len(desc.oneof_groups["choice"]) == 2


# ============================================================================
# Unknown fields
# ============================================================================


class TestUnknownFields:
    def test_preserve_unknown_varint(self):
        @message
        class V1:
            name: str = field(1)
            value: int32 = field(2)

        @message
        class V2:
            name: str = field(1)

        obj = V1(name="test", value=42)
        data = obj.serialize()

        # Parse with V2 (doesn't know about field 2)
        parsed = V2.parse(data)
        assert parsed.name == "test"
        assert len(parsed._unknown_fields) == 1

        # Re-serialize should preserve the unknown field
        redata = parsed.serialize()
        reparsed = V1.parse(redata)
        assert reparsed.name == "test"
        assert reparsed.value == 42

    def test_preserve_unknown_len(self):
        @message
        class Full:
            name: str = field(1)
            extra: str = field(2)

        @message
        class Partial:
            name: str = field(1)

        obj = Full(name="test", extra="hidden")
        data = obj.serialize()

        parsed = Partial.parse(data)
        assert parsed.name == "test"
        assert len(parsed._unknown_fields) == 1


# ============================================================================
# Dict conversion
# ============================================================================


class TestDictConversion:
    def test_to_dict_basic(self):
        @message
        class M:
            name: str = field(1)
            value: int32 = field(2)

        obj = M(name="hello", value=42)
        d = obj.to_dict()
        assert d == {"name": "hello", "value": 42}

    def test_to_dict_omits_defaults(self):
        @message
        class M:
            name: str = field(1)
            value: int32 = field(2)

        obj = M(name="", value=0)
        d = obj.to_dict()
        assert d == {}

    def test_to_dict_nested(self):
        @message
        class Inner:
            x: int32 = field(1)

        @message
        class Outer:
            inner: Inner = field(1)

        obj = Outer(inner=Inner(x=5))
        d = obj.to_dict()
        assert d == {"inner": {"x": 5}}

    def test_to_dict_repeated(self):
        @message
        class M:
            values: repeated[int32] = field(1)

        obj = M(values=[1, 2, 3])
        d = obj.to_dict()
        assert d == {"values": [1, 2, 3]}

    def test_to_dict_bytes_base64(self):
        @message
        class M:
            data: bytes = field(1)

        import base64

        obj = M(data=b"\x01\x02\x03")
        d = obj.to_dict()
        assert d["data"] == base64.b64encode(b"\x01\x02\x03").decode("ascii")

    def test_to_dict_enum(self):
        class Status(IntEnum):
            OK = 0
            ERROR = 1

        @message
        class M:
            status: Status = field(1)

        obj = M(status=Status.ERROR)
        d = obj.to_dict()
        assert d == {"status": 1}

    def test_to_dict_map(self):
        @message
        class M:
            attrs: map_field[str, int32] = field(1)

        obj = M(attrs={"a": 1, "b": 2})
        d = obj.to_dict()
        assert d == {"attrs": {"a": 1, "b": 2}}

    def test_from_dict_basic(self):
        @message
        class M:
            name: str = field(1)
            value: int32 = field(2)

        obj = M.from_dict({"name": "hello", "value": 42})
        assert obj.name == "hello"
        assert obj.value == 42

    def test_from_dict_nested(self):
        @message
        class Inner:
            x: int32 = field(1)

        @message
        class Outer:
            inner: Inner = field(1)

        obj = Outer.from_dict({"inner": {"x": 5}})
        assert obj.inner.x == 5

    def test_from_dict_repeated(self):
        @message
        class M:
            values: repeated[int32] = field(1)

        obj = M.from_dict({"values": [10, 20, 30]})
        assert obj.values == [10, 20, 30]

    def test_from_dict_bytes_base64(self):
        import base64

        @message
        class M:
            data: bytes = field(1)

        b64 = base64.b64encode(b"\xfe\xed").decode("ascii")
        obj = M.from_dict({"data": b64})
        assert obj.data == b"\xfe\xed"

    def test_from_dict_map(self):
        @message
        class M:
            attrs: map_field[str, int32] = field(1)

        obj = M.from_dict({"attrs": {"x": 10, "y": 20}})
        assert obj.attrs == {"x": 10, "y": 20}

    def test_roundtrip_dict(self):
        @message
        class Inner:
            val: int32 = field(1)

        @message
        class M:
            name: str = field(1)
            items: repeated[Inner] = field(2)
            tags: map_field[str, str] = field(3)

        original = M(
            name="test",
            items=[Inner(val=1), Inner(val=2)],
            tags={"env": "prod"},
        )
        d = original.to_dict()
        restored = M.from_dict(d)
        assert restored.name == "test"
        assert len(restored.items) == 2
        assert restored.items[0].val == 1
        assert restored.tags == {"env": "prod"}


# ============================================================================
# Edge cases
# ============================================================================


class TestEdgeCases:
    def test_field_number_validation(self):
        with pytest.raises(ValueError, match="must be >= 1"):
            field(0)

    def test_large_field_number(self):
        @message
        class M:
            value: int32 = field(536870911)  # max valid field number

        obj = M(value=42)
        parsed = M.parse(obj.serialize())
        assert parsed.value == 42

    def test_multiple_fields_ordering(self):
        @message
        class M:
            z: str = field(3)
            a: str = field(1)
            m: str = field(2)

        obj = M(a="first", m="second", z="third")
        parsed = M.parse(obj.serialize())
        assert parsed.a == "first"
        assert parsed.m == "second"
        assert parsed.z == "third"

    def test_bare_int_defaults_to_int64(self):
        @message
        class M:
            value: int = field(1)

        obj = M(value=2**62)
        parsed = M.parse(obj.serialize())
        assert parsed.value == 2**62

    def test_bare_float_defaults_to_double(self):
        @message
        class M:
            value: float = field(1)

        obj = M(value=3.141592653589793)
        parsed = M.parse(obj.serialize())
        assert parsed.value == 3.141592653589793

    def test_memoryview_input(self):
        @message
        class M:
            value: int32 = field(1)

        obj = M(value=42)
        data = obj.serialize()
        mv = memoryview(data)
        parsed = M.parse(mv)
        assert parsed.value == 42

    def test_mixed_fields_complex(self):
        class Priority(IntEnum):
            LOW = 0
            MEDIUM = 1
            HIGH = 2

        @message
        class Tag:
            key: str = field(1)
            value: str = field(2)

        @message
        class Task:
            id: uint64 = field(1)
            title: str = field(2)
            priority: Priority = field(3)
            tags: repeated[Tag] = field(4)
            metadata: map_field[str, str] = field(5)
            completed: bool_ = field(6)

        obj = Task(
            id=12345,
            title="Write tests",
            priority=Priority.HIGH,
            tags=[Tag(key="area", value="testing"), Tag(key="sprint", value="42")],
            metadata={"assignee": "alice", "estimate": "3h"},
            completed=True,
        )
        data = obj.serialize()
        parsed = Task.parse(data)
        assert parsed.id == 12345
        assert parsed.title == "Write tests"
        assert parsed.priority == Priority.HIGH
        assert len(parsed.tags) == 2
        assert parsed.tags[0].key == "area"
        assert parsed.metadata["assignee"] == "alice"
        assert parsed.completed is True

        # Dict roundtrip
        d = obj.to_dict()
        restored = Task.from_dict(d)
        assert restored.id == 12345
        assert restored.priority == Priority.HIGH
        assert len(restored.tags) == 2

    def test_independent_instances(self):
        """Ensure mutable defaults are not shared between instances."""

        @message
        class M:
            items: repeated[int32] = field(1)

        a = M()
        b = M()
        a.items.append(1)
        assert b.items == []  # should not be affected

    def test_independent_parsed_instances(self):
        """Ensure parsed instances have independent mutable fields."""

        @message
        class M:
            items: repeated[int32] = field(1)

        data = M(items=[1, 2]).serialize()
        a = M.parse(data)
        b = M.parse(data)
        a.items.append(99)
        assert 99 not in b.items
