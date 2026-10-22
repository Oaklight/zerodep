"""Benchmark: zerodep TOON vs toon_format."""

import json
import os
import sys

import pytest

try:
    import toon_format as _tf
except ImportError:
    pytest.skip("toon_format not installed", allow_module_level=True)

sys.path.insert(0, os.path.dirname(__file__))
from toon import decode, encode  # noqa: E402

# ── Test data ──

SMALL = {"id": 123, "name": "Alice", "active": True}

MEDIUM = {
    "company": "Acme Corp",
    "employees": [
        {"id": i, "name": f"Employee_{i}", "dept": "eng", "active": i % 2 == 0}
        for i in range(20)
    ],
    "config": {
        "debug": False,
        "version": "2.1.0",
        "features": ["auth", "logging", "cache"],
    },
}

LARGE = {
    "metadata": {"version": "3.0", "generated": "2024-01-15"},
    "departments": [
        {
            "name": f"dept_{d}",
            "budget": d * 10000,
            "teams": [
                {
                    "name": f"team_{d}_{t}",
                    "members": [
                        {
                            "id": d * 100 + t * 10 + m,
                            "name": f"person_{d}_{t}_{m}",
                            "role": ["dev", "qa", "pm"][m % 3],
                            "score": 80 + m,
                        }
                        for m in range(5)
                    ],
                }
                for t in range(4)
            ],
        }
        for d in range(5)
    ],
}

# Pre-encode for decode benchmarks
SMALL_TOON = encode(SMALL)
MEDIUM_TOON = encode(MEDIUM)
LARGE_TOON = encode(LARGE)

SMALL_TOON_REF = _tf.encode(SMALL)
MEDIUM_TOON_REF = _tf.encode(MEDIUM)
LARGE_TOON_REF = _tf.encode(LARGE)


# ── Encode benchmarks ──


class TestEncodeBenchmark:
    def test_encode_small_ours(self, benchmark):
        benchmark(encode, SMALL)

    def test_encode_small_ref(self, benchmark):
        benchmark(_tf.encode, SMALL)

    def test_encode_medium_ours(self, benchmark):
        benchmark(encode, MEDIUM)

    def test_encode_medium_ref(self, benchmark):
        benchmark(_tf.encode, MEDIUM)

    def test_encode_large_ours(self, benchmark):
        benchmark(encode, LARGE)

    def test_encode_large_ref(self, benchmark):
        benchmark(_tf.encode, LARGE)


# ── Decode benchmarks ──


class TestDecodeBenchmark:
    def test_decode_small_ours(self, benchmark):
        benchmark(decode, SMALL_TOON)

    def test_decode_small_ref(self, benchmark):
        benchmark(_tf.decode, SMALL_TOON_REF)

    def test_decode_medium_ours(self, benchmark):
        benchmark(decode, MEDIUM_TOON)

    def test_decode_medium_ref(self, benchmark):
        benchmark(_tf.decode, MEDIUM_TOON_REF)

    def test_decode_large_ours(self, benchmark):
        benchmark(decode, LARGE_TOON)

    def test_decode_large_ref(self, benchmark):
        benchmark(_tf.decode, LARGE_TOON_REF)


# ── Token efficiency: TOON vs JSON ──


class TestTokenEfficiency:
    """Show TOON's token savings vs JSON (not a speed benchmark)."""

    @pytest.mark.parametrize(
        "label,data",
        [("small", SMALL), ("medium", MEDIUM), ("large", LARGE)],
    )
    def test_toon_smaller_than_json(self, label, data):
        toon_str = encode(data)
        json_str = json.dumps(data, indent=2)
        toon_chars = len(toon_str)
        json_chars = len(json_str)
        savings = (1 - toon_chars / json_chars) * 100
        print(
            f"\n  {label}: JSON={json_chars} chars, "
            f"TOON={toon_chars} chars, savings={savings:.1f}%"
        )
        assert toon_chars <= json_chars
