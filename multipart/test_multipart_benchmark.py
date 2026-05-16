"""Benchmark: zerodep multipart vs python-multipart."""

import importlib
import os
import sys

import pytest

# Import reference library (python-multipart) via direct path loading
# to avoid name collision with our local multipart module.
_HAS_REF = False
_ref_parse = None
try:
    for _p in sys.path:
        if "site-packages" not in _p:
            continue
        _pkg_dir = os.path.join(_p, "multipart")
        _ref_file = os.path.join(_pkg_dir, "multipart.py")
        if os.path.isfile(_ref_file):
            _spec = importlib.util.spec_from_file_location(
                "multipart_reference", _ref_file
            )
            if _spec and _spec.loader:
                _ref_mod = importlib.util.module_from_spec(_spec)
                _spec.loader.exec_module(_ref_mod)
                _HAS_REF = True
            break
except Exception:
    pass

# Now import our module.
sys.path.insert(0, os.path.dirname(__file__))

from multipart import encode_multipart, parse_multipart  # noqa: E402


# ── Reference parser adapter ──
def _ref_parse_multipart(body: bytes, content_type: str) -> list:
    """Parse multipart body using python-multipart as reference."""
    if not _HAS_REF:
        pytest.skip("python-multipart not installed")

    from io import BytesIO

    # python-multipart expects headers dict and a callback-based API.
    # Use its high-level multipart.parse_options_header + FormParser.
    _multipart_mod = _ref_mod  # type: ignore[name-defined]

    # Extract boundary
    content_type_bytes = content_type.encode("latin-1")
    _, options = _multipart_mod.parse_options_header(content_type_bytes)
    boundary = options.get(b"boundary", b"")

    parts: list[dict] = []
    current_part: dict = {}
    current_data = BytesIO()

    def on_part_begin():
        nonlocal current_part, current_data
        current_part = {"headers": {}}
        current_data = BytesIO()

    def on_part_data(data: bytes, start: int, end: int):
        current_data.write(data[start:end])

    def on_part_end():
        current_part["data"] = current_data.getvalue()
        parts.append(current_part)

    def on_header_field(data: bytes, start: int, end: int):
        current_part["_header_field"] = data[start:end].decode("latin-1")

    def on_header_value(data: bytes, start: int, end: int):
        field = current_part.pop("_header_field", "")
        current_part["headers"][field.lower()] = data[start:end].decode("latin-1")

    callbacks = {
        "on_part_begin": on_part_begin,
        "on_part_data": on_part_data,
        "on_part_end": on_part_end,
        "on_header_field": on_header_field,
        "on_header_value": on_header_value,
    }

    parser = _multipart_mod.MultipartParser(boundary, callbacks)
    parser.write(body)
    parser.finalize()

    return parts


# ── Test data generators ──


def _make_small_body() -> tuple[bytes, str]:
    """Small payload: 3 text fields (~200 bytes)."""
    return encode_multipart(
        fields={"name": "Alice", "age": "30", "city": "Wonderland"},
        boundary="benchboundary",
    )


def _make_medium_body() -> tuple[bytes, str]:
    """Medium payload: 5 text fields + 2 small files (~10 KB)."""
    fields = {f"field_{i}": f"value_{i} " * 20 for i in range(5)}
    files = {
        "file1": ("report.txt", b"x" * 2048, "text/plain"),
        "file2": ("data.bin", b"\x00\xff" * 2048, "application/octet-stream"),
    }
    return encode_multipart(fields=fields, files=files, boundary="benchboundary")


def _make_large_body() -> tuple[bytes, str]:
    """Large payload: 10 text fields + 5 files (~500 KB)."""
    fields = {f"field_{i}": f"value_{i} " * 100 for i in range(10)}
    files = {
        f"file_{i}": (
            f"upload_{i}.bin",
            os.urandom(80_000),
            "application/octet-stream",
        )
        for i in range(5)
    }
    return encode_multipart(fields=fields, files=files, boundary="benchboundary")


# Pre-build payloads so generation cost is excluded from benchmarks.
SMALL_BODY, SMALL_CT = _make_small_body()
MEDIUM_BODY, MEDIUM_CT = _make_medium_body()
LARGE_BODY, LARGE_CT = _make_large_body()

# Pre-build encode inputs
SMALL_FIELDS = {"name": "Alice", "age": "30", "city": "Wonderland"}
MEDIUM_FIELDS = {f"field_{i}": f"value_{i} " * 20 for i in range(5)}
MEDIUM_FILES = {
    "file1": ("report.txt", b"x" * 2048, "text/plain"),
    "file2": ("data.bin", b"\x00\xff" * 2048, "application/octet-stream"),
}
LARGE_FIELDS = {f"field_{i}": f"value_{i} " * 100 for i in range(10)}
LARGE_FILES = {
    f"file_{i}": (
        f"upload_{i}.bin",
        os.urandom(80_000),
        "application/octet-stream",
    )
    for i in range(5)
}


# ── Parse benchmarks ──


class TestParseSmall:
    def test_zerodep(self, benchmark):
        benchmark(parse_multipart, SMALL_BODY, SMALL_CT)

    @pytest.mark.skipif(not _HAS_REF, reason="python-multipart not installed")
    def test_python_multipart(self, benchmark):
        benchmark(_ref_parse_multipart, SMALL_BODY, SMALL_CT)


class TestParseMedium:
    def test_zerodep(self, benchmark):
        benchmark(parse_multipart, MEDIUM_BODY, MEDIUM_CT)

    @pytest.mark.skipif(not _HAS_REF, reason="python-multipart not installed")
    def test_python_multipart(self, benchmark):
        benchmark(_ref_parse_multipart, MEDIUM_BODY, MEDIUM_CT)


class TestParseLarge:
    def test_zerodep(self, benchmark):
        benchmark(parse_multipart, LARGE_BODY, LARGE_CT)

    @pytest.mark.skipif(not _HAS_REF, reason="python-multipart not installed")
    def test_python_multipart(self, benchmark):
        benchmark(_ref_parse_multipart, LARGE_BODY, LARGE_CT)


# ── Encode benchmarks ──


class TestEncodeSmall:
    def test_zerodep(self, benchmark):
        benchmark(encode_multipart, SMALL_FIELDS)


class TestEncodeMedium:
    def test_zerodep(self, benchmark):
        benchmark(encode_multipart, MEDIUM_FIELDS, MEDIUM_FILES)


class TestEncodeLarge:
    def test_zerodep(self, benchmark):
        benchmark(encode_multipart, LARGE_FIELDS, LARGE_FILES)


# ── Round-trip benchmark ──


class TestRoundTrip:
    def test_small(self, benchmark):
        def roundtrip():
            body, ct = encode_multipart(SMALL_FIELDS, boundary="rt")
            return parse_multipart(body, ct)

        benchmark(roundtrip)

    def test_medium(self, benchmark):
        def roundtrip():
            body, ct = encode_multipart(MEDIUM_FIELDS, MEDIUM_FILES, boundary="rt")
            return parse_multipart(body, ct)

        benchmark(roundtrip)
