"""Benchmark tests: zerodep protobuf module.

Measures encode/decode throughput for common message shapes.
Optional comparison against google-protobuf if installed.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from protobuf import (
    bool_,
    double,
    field,
    int32,
    map_field,
    message,
    repeated,
    uint64,
)

# ============================================================================
# Google protobuf reference (optional)
# ============================================================================

try:
    from google.protobuf import descriptor_pb2 as _dpb2
    from google.protobuf import descriptor_pool as _pool

    HAS_GOOGLE_PB = True
except ImportError:
    HAS_GOOGLE_PB = False


def _build_google_messages():
    """Dynamically build google-protobuf message classes equivalent to zerodep ones."""
    from google.protobuf import message_factory

    pool = _pool.DescriptorPool()

    # --- SmallMessage: name(1)=string, value(2)=int32, flag(3)=bool ---
    file_dp = _dpb2.FileDescriptorProto(
        name="bench.proto",
        package="bench",
        syntax="proto3",
    )

    # SmallMessage
    small_msg = file_dp.message_type.add()
    small_msg.name = "SmallMessage"
    f = small_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "name",
        1,
        _dpb2.FieldDescriptorProto.TYPE_STRING,
        _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
    )
    f = small_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "value",
        2,
        _dpb2.FieldDescriptorProto.TYPE_INT32,
        _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
    )
    f = small_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "flag",
        3,
        _dpb2.FieldDescriptorProto.TYPE_BOOL,
        _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
    )

    # MediumMessage: id(1)=uint64, title(2)=string, score(3)=double,
    #                tags(4)=repeated string, values(5)=repeated int32
    med_msg = file_dp.message_type.add()
    med_msg.name = "MediumMessage"
    f = med_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "id",
        1,
        _dpb2.FieldDescriptorProto.TYPE_UINT64,
        _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
    )
    f = med_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "title",
        2,
        _dpb2.FieldDescriptorProto.TYPE_STRING,
        _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
    )
    f = med_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "score",
        3,
        _dpb2.FieldDescriptorProto.TYPE_DOUBLE,
        _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
    )
    f = med_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "tags",
        4,
        _dpb2.FieldDescriptorProto.TYPE_STRING,
        _dpb2.FieldDescriptorProto.LABEL_REPEATED,
    )
    f = med_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "values",
        5,
        _dpb2.FieldDescriptorProto.TYPE_INT32,
        _dpb2.FieldDescriptorProto.LABEL_REPEATED,
    )

    # InnerMessage: x(1)=int32, y(2)=int32, label(3)=string
    inner_msg = file_dp.message_type.add()
    inner_msg.name = "InnerMessage"
    f = inner_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "x",
        1,
        _dpb2.FieldDescriptorProto.TYPE_INT32,
        _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
    )
    f = inner_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "y",
        2,
        _dpb2.FieldDescriptorProto.TYPE_INT32,
        _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
    )
    f = inner_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "label",
        3,
        _dpb2.FieldDescriptorProto.TYPE_STRING,
        _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
    )

    # LargeMessage: id(1)=uint64, name(2)=string, items(3)=repeated InnerMessage,
    #               metadata(4)=map<string,string>, scores(5)=repeated double, active(6)=bool
    large_msg = file_dp.message_type.add()
    large_msg.name = "LargeMessage"
    f = large_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "id",
        1,
        _dpb2.FieldDescriptorProto.TYPE_UINT64,
        _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
    )
    f = large_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "name",
        2,
        _dpb2.FieldDescriptorProto.TYPE_STRING,
        _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
    )
    f = large_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "items",
        3,
        _dpb2.FieldDescriptorProto.TYPE_MESSAGE,
        _dpb2.FieldDescriptorProto.LABEL_REPEATED,
    )
    f.type_name = ".bench.InnerMessage"
    # map<string, string> as MapEntry
    map_entry = large_msg.nested_type.add()
    map_entry.name = "MetadataEntry"
    map_entry.options.CopyFrom(_dpb2.MessageOptions(map_entry=True))
    f = map_entry.field.add()
    f.name, f.number, f.type, f.label = (
        "key",
        1,
        _dpb2.FieldDescriptorProto.TYPE_STRING,
        _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
    )
    f = map_entry.field.add()
    f.name, f.number, f.type, f.label = (
        "value",
        2,
        _dpb2.FieldDescriptorProto.TYPE_STRING,
        _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
    )
    f = large_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "metadata",
        4,
        _dpb2.FieldDescriptorProto.TYPE_MESSAGE,
        _dpb2.FieldDescriptorProto.LABEL_REPEATED,
    )
    f.type_name = ".bench.LargeMessage.MetadataEntry"
    f = large_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "scores",
        5,
        _dpb2.FieldDescriptorProto.TYPE_DOUBLE,
        _dpb2.FieldDescriptorProto.LABEL_REPEATED,
    )
    f = large_msg.field.add()
    f.name, f.number, f.type, f.label = (
        "active",
        6,
        _dpb2.FieldDescriptorProto.TYPE_BOOL,
        _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
    )

    pool.Add(file_dp)

    SmallMsg = message_factory.GetMessageClass(
        pool.FindMessageTypeByName("bench.SmallMessage")
    )
    MedMsg = message_factory.GetMessageClass(
        pool.FindMessageTypeByName("bench.MediumMessage")
    )
    InnerMsg = message_factory.GetMessageClass(
        pool.FindMessageTypeByName("bench.InnerMessage")
    )
    LargeMsg = message_factory.GetMessageClass(
        pool.FindMessageTypeByName("bench.LargeMessage")
    )

    return SmallMsg, MedMsg, InnerMsg, LargeMsg


if HAS_GOOGLE_PB:
    GSmall, GMedium, GInner, GLarge = _build_google_messages()

# ============================================================================
# Benchmark message definitions
# ============================================================================


@message
class SmallMessage:
    name: str = field(1)
    value: int32 = field(2)
    flag: bool_ = field(3)


@message
class MediumMessage:
    id: uint64 = field(1)
    title: str = field(2)
    score: double = field(3)
    tags: repeated[str] = field(4)
    values: repeated[int32] = field(5)


@message
class InnerMessage:
    x: int32 = field(1)
    y: int32 = field(2)
    label: str = field(3)


@message
class LargeMessage:
    id: uint64 = field(1)
    name: str = field(2)
    items: repeated[InnerMessage] = field(3)
    metadata: map_field[str, str] = field(4)
    scores: repeated[double] = field(5)
    active: bool_ = field(6)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def small_obj():
    return SmallMessage(name="benchmark", value=42, flag=True)


@pytest.fixture
def medium_obj():
    return MediumMessage(
        id=123456789,
        title="A medium-sized message for benchmarking",
        score=3.14159,
        tags=["alpha", "beta", "gamma", "delta"],
        values=list(range(100)),
    )


@pytest.fixture
def large_obj():
    return LargeMessage(
        id=987654321,
        name="Large benchmark message",
        items=[InnerMessage(x=i, y=i * 2, label=f"item_{i}") for i in range(50)],
        metadata={f"key_{i}": f"value_{i}" for i in range(20)},
        scores=[float(i) * 0.1 for i in range(100)],
        active=True,
    )


# ============================================================================
# Encode benchmarks
# ============================================================================


def test_encode_small(benchmark, small_obj):
    benchmark(small_obj.serialize)


def test_encode_medium(benchmark, medium_obj):
    benchmark(medium_obj.serialize)


def test_encode_large(benchmark, large_obj):
    benchmark(large_obj.serialize)


# ============================================================================
# Decode benchmarks
# ============================================================================


def test_decode_small(benchmark, small_obj):
    data = small_obj.serialize()
    benchmark(SmallMessage.parse, data)


def test_decode_medium(benchmark, medium_obj):
    data = medium_obj.serialize()
    benchmark(MediumMessage.parse, data)


def test_decode_large(benchmark, large_obj):
    data = large_obj.serialize()
    benchmark(LargeMessage.parse, data)


# ============================================================================
# Roundtrip benchmarks
# ============================================================================


def test_roundtrip_small(benchmark, small_obj):
    def roundtrip():
        return SmallMessage.parse(small_obj.serialize())

    benchmark(roundtrip)


def test_roundtrip_medium(benchmark, medium_obj):
    def roundtrip():
        return MediumMessage.parse(medium_obj.serialize())

    benchmark(roundtrip)


def test_roundtrip_large(benchmark, large_obj):
    def roundtrip():
        return LargeMessage.parse(large_obj.serialize())

    benchmark(roundtrip)


# ============================================================================
# Dict conversion benchmarks
# ============================================================================


def test_to_dict_large(benchmark, large_obj):
    benchmark(large_obj.to_dict)


def test_from_dict_large(benchmark, large_obj):
    d = large_obj.to_dict()
    benchmark(LargeMessage.from_dict, d)


# ============================================================================
# Google protobuf comparison benchmarks
# ============================================================================


@pytest.fixture
def g_small_obj():
    return GSmall(name="benchmark", value=42, flag=True)


@pytest.fixture
def g_medium_obj():
    msg = GMedium(
        id=123456789, title="A medium-sized message for benchmarking", score=3.14159
    )
    msg.tags.extend(["alpha", "beta", "gamma", "delta"])
    msg.values.extend(list(range(100)))
    return msg


@pytest.fixture
def g_large_obj():
    msg = GLarge(id=987654321, name="Large benchmark message", active=True)
    for i in range(50):
        msg.items.append(GInner(x=i, y=i * 2, label=f"item_{i}"))
    for i in range(20):
        msg.metadata[f"key_{i}"] = f"value_{i}"
    msg.scores.extend([float(i) * 0.1 for i in range(100)])
    return msg


@pytest.mark.skipif(not HAS_GOOGLE_PB, reason="google-protobuf not installed")
class TestEncodeComparison:
    def test_zerodep_small(self, benchmark, small_obj):
        benchmark(small_obj.serialize)

    def test_google_small(self, benchmark, g_small_obj):
        benchmark(g_small_obj.SerializeToString)

    def test_zerodep_medium(self, benchmark, medium_obj):
        benchmark(medium_obj.serialize)

    def test_google_medium(self, benchmark, g_medium_obj):
        benchmark(g_medium_obj.SerializeToString)

    def test_zerodep_large(self, benchmark, large_obj):
        benchmark(large_obj.serialize)

    def test_google_large(self, benchmark, g_large_obj):
        benchmark(g_large_obj.SerializeToString)


@pytest.mark.skipif(not HAS_GOOGLE_PB, reason="google-protobuf not installed")
class TestDecodeComparison:
    def test_zerodep_small(self, benchmark, small_obj):
        data = small_obj.serialize()
        benchmark(SmallMessage.parse, data)

    def test_google_small(self, benchmark, g_small_obj):
        data = g_small_obj.SerializeToString()

        def parse():
            m = GSmall()
            m.ParseFromString(data)
            return m

        benchmark(parse)

    def test_zerodep_medium(self, benchmark, medium_obj):
        data = medium_obj.serialize()
        benchmark(MediumMessage.parse, data)

    def test_google_medium(self, benchmark, g_medium_obj):
        data = g_medium_obj.SerializeToString()

        def parse():
            m = GMedium()
            m.ParseFromString(data)
            return m

        benchmark(parse)

    def test_zerodep_large(self, benchmark, large_obj):
        data = large_obj.serialize()
        benchmark(LargeMessage.parse, data)

    def test_google_large(self, benchmark, g_large_obj):
        data = g_large_obj.SerializeToString()

        def parse():
            m = GLarge()
            m.ParseFromString(data)
            return m

        benchmark(parse)


@pytest.mark.skipif(not HAS_GOOGLE_PB, reason="google-protobuf not installed")
class TestRoundtripComparison:
    def test_zerodep_small(self, benchmark, small_obj):
        def roundtrip():
            return SmallMessage.parse(small_obj.serialize())

        benchmark(roundtrip)

    def test_google_small(self, benchmark, g_small_obj):
        def roundtrip():
            m = GSmall()
            m.ParseFromString(g_small_obj.SerializeToString())
            return m

        benchmark(roundtrip)

    def test_zerodep_medium(self, benchmark, medium_obj):
        def roundtrip():
            return MediumMessage.parse(medium_obj.serialize())

        benchmark(roundtrip)

    def test_google_medium(self, benchmark, g_medium_obj):
        def roundtrip():
            m = GMedium()
            m.ParseFromString(g_medium_obj.SerializeToString())
            return m

        benchmark(roundtrip)

    def test_zerodep_large(self, benchmark, large_obj):
        def roundtrip():
            return LargeMessage.parse(large_obj.serialize())

        benchmark(roundtrip)

    def test_google_large(self, benchmark, g_large_obj):
        def roundtrip():
            m = GLarge()
            m.ParseFromString(g_large_obj.SerializeToString())
            return m

        benchmark(roundtrip)
