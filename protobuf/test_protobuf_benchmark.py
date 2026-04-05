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
