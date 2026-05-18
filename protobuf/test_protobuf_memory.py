"""Memory benchmarks: zerodep protobuf encode/decode.

Uses tracemalloc to measure peak heap allocation for encode (serialize)
and decode (parse) at three message sizes (S/M/L).  Results are printed
in KB so they are visible in plain ``pytest -s`` output.  No
pytest-benchmark required.

The google-protobuf reference library is optional.  When absent, only
zerodep measurements are collected and comparison tests are skipped.
"""

import os
import sys
import tracemalloc

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from protobuf import (  # noqa: E402
    bool_,
    double,
    field,
    int32,
    map_field,
    message,
    repeated,
    uint64,
)

# ── Google protobuf reference (optional) ──

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

    file_dp = _dpb2.FileDescriptorProto(
        name="bench_mem.proto",
        package="benchmem",
        syntax="proto3",
    )

    # SmallMessage: name(1)=string, value(2)=int32, flag(3)=bool
    sm = file_dp.message_type.add()
    sm.name = "SmallMessage"
    for fname, fnum, ftype in [
        ("name", 1, _dpb2.FieldDescriptorProto.TYPE_STRING),
        ("value", 2, _dpb2.FieldDescriptorProto.TYPE_INT32),
        ("flag", 3, _dpb2.FieldDescriptorProto.TYPE_BOOL),
    ]:
        f = sm.field.add()
        f.name, f.number, f.type = fname, fnum, ftype
        f.label = _dpb2.FieldDescriptorProto.LABEL_OPTIONAL

    # LargeMessage: id(1)=uint64, name(2)=string, scores(3)=repeated double,
    #               active(4)=bool
    lm = file_dp.message_type.add()
    lm.name = "LargeMessage"
    for fname, fnum, ftype, flabel in [
        (
            "id",
            1,
            _dpb2.FieldDescriptorProto.TYPE_UINT64,
            _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
        ),
        (
            "name",
            2,
            _dpb2.FieldDescriptorProto.TYPE_STRING,
            _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
        ),
        (
            "scores",
            3,
            _dpb2.FieldDescriptorProto.TYPE_DOUBLE,
            _dpb2.FieldDescriptorProto.LABEL_REPEATED,
        ),
        (
            "active",
            4,
            _dpb2.FieldDescriptorProto.TYPE_BOOL,
            _dpb2.FieldDescriptorProto.LABEL_OPTIONAL,
        ),
    ]:
        f = lm.field.add()
        f.name, f.number, f.type, f.label = fname, fnum, ftype, flabel

    fd = pool.Add(file_dp)
    factory = message_factory.MessageFactory(pool=pool)
    classes = {}
    for msg_name in ["SmallMessage", "LargeMessage"]:
        desc = fd.message_types_by_name[msg_name]
        classes[msg_name] = factory.GetPrototype(desc)
    return classes


if HAS_GOOGLE_PB:
    try:
        _goog_classes = _build_google_messages()
        _GoogSmall = _goog_classes["SmallMessage"]
        _GoogLarge = _goog_classes["LargeMessage"]
    except Exception:
        HAS_GOOGLE_PB = False
        _GoogSmall = None
        _GoogLarge = None
else:
    _GoogSmall = None
    _GoogLarge = None

# ── zerodep message definitions ──


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


# ── Pre-built objects ──

_SMALL_OBJ = SmallMessage(name="benchmark", value=42, flag=True)
_MEDIUM_OBJ = MediumMessage(
    id=123456789,
    title="A medium-sized message for benchmarking",
    score=3.14159,
    tags=["alpha", "beta", "gamma", "delta"],
    values=list(range(100)),
)
_LARGE_OBJ = LargeMessage(
    id=987654321,
    name="Large benchmark message",
    items=[InnerMessage(x=i, y=i * 2, label=f"item_{i}") for i in range(50)],
    metadata={f"key_{i}": f"value_{i}" for i in range(20)},
    scores=[float(i) * 0.1 for i in range(100)],
    active=True,
)

_SMALL_BYTES = _SMALL_OBJ.serialize()
_MEDIUM_BYTES = _MEDIUM_OBJ.serialize()
_LARGE_BYTES = _LARGE_OBJ.serialize()


# ── Helpers ──


def _measure_peak_kb(fn, *args, **kwargs) -> float:
    """Run *fn* with *args*/*kwargs* under tracemalloc and return peak KB."""
    tracemalloc.start()
    try:
        fn(*args, **kwargs)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak / 1024


_ENC_SIZES = [
    pytest.param("small", _SMALL_OBJ, id="small"),
    pytest.param("medium", _MEDIUM_OBJ, id="medium"),
    pytest.param("large", _LARGE_OBJ, id="large"),
]

_DEC_SIZES = [
    pytest.param("small", SmallMessage, _SMALL_BYTES, id="small"),
    pytest.param("medium", MediumMessage, _MEDIUM_BYTES, id="medium"),
    pytest.param("large", LargeMessage, _LARGE_BYTES, id="large"),
]

_RT_SIZES = [
    pytest.param("small", _SMALL_OBJ, SmallMessage, id="small"),
    pytest.param("medium", _MEDIUM_OBJ, MediumMessage, id="medium"),
    pytest.param("large", _LARGE_OBJ, LargeMessage, id="large"),
]


# ── Encode memory tests ──


@pytest.mark.parametrize("label,obj", _ENC_SIZES)
def test_encode_memory_zerodep(label: str, obj) -> None:
    """Measure peak memory for zerodep protobuf encode."""
    peak_kb = _measure_peak_kb(obj.serialize)
    print(f"\n[protobuf encode zerodep {label:6s}] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.skipif(not HAS_GOOGLE_PB, reason="google-protobuf not installed")
def test_encode_memory_google_small() -> None:
    """Measure peak memory for google-protobuf encode (small)."""
    obj = _GoogSmall(name="benchmark", value=42, flag=True)

    peak_kb = _measure_peak_kb(obj.SerializeToString)
    print(f"\n[protobuf encode google  small ] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.skipif(not HAS_GOOGLE_PB, reason="google-protobuf not installed")
def test_encode_memory_google_large() -> None:
    """Measure peak memory for google-protobuf encode (large)."""
    obj = _GoogLarge(
        id=987654321,
        name="Large benchmark message",
        scores=[float(i) * 0.1 for i in range(100)],
        active=True,
    )
    peak_kb = _measure_peak_kb(obj.SerializeToString)
    print(f"\n[protobuf encode google  large ] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


# ── Decode memory tests ──


@pytest.mark.parametrize("label,cls,data", _DEC_SIZES)
def test_decode_memory_zerodep(label: str, cls, data: bytes) -> None:
    """Measure peak memory for zerodep protobuf decode."""
    peak_kb = _measure_peak_kb(cls.parse, data)
    print(f"\n[protobuf decode zerodep {label:6s}] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


# ── Roundtrip memory tests ──


@pytest.mark.parametrize("label,obj,cls", _RT_SIZES)
def test_roundtrip_memory_zerodep(label: str, obj, cls) -> None:
    """Measure peak memory for zerodep protobuf roundtrip."""

    def roundtrip():
        return cls.parse(obj.serialize())

    peak_kb = _measure_peak_kb(roundtrip)
    print(f"\n[protobuf roundtrip zerodep {label:6s}] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0
