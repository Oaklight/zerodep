"""Memory benchmarks: zerodep multipart vs python-multipart.

Uses tracemalloc to measure peak heap allocation for parse_multipart
and encode_multipart at three input sizes (S/M/L).  Results are
printed in KB so they are visible in plain ``pytest -s`` output.  No
pytest-benchmark required.

The python-multipart reference library is loaded via site-packages path
inspection to avoid the name collision with our local module (same
technique as the time benchmark).
"""

import importlib
import importlib.util
import os
import sys
import tracemalloc

import pytest

# ── Import python-multipart reference via direct path loading ──

_HAS_REF = False
_ref_mod = None
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

# ── Import our module ──

sys.path.insert(0, os.path.dirname(__file__))

from multipart import encode_multipart, parse_multipart  # noqa: E402

# ── Reference parser adapter ──


def _ref_parse_multipart(body: bytes, content_type: str) -> list:
    """Parse multipart body using python-multipart as reference."""
    if not _HAS_REF:
        pytest.skip("python-multipart not installed")

    from io import BytesIO

    _multipart_mod = _ref_mod

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
        fld = current_part.pop("_header_field", "")
        current_part["headers"][fld.lower()] = data[start:end].decode("latin-1")

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


# ── Test data ──


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
            bytes(range(256)) * 313,  # ~80 KB deterministic, no os.urandom
            "application/octet-stream",
        )
        for i in range(5)
    }
    return encode_multipart(fields=fields, files=files, boundary="benchboundary")


# Pre-build payloads so generation cost is excluded from measurements.
SMALL_BODY, SMALL_CT = _make_small_body()
MEDIUM_BODY, MEDIUM_CT = _make_medium_body()
LARGE_BODY, LARGE_CT = _make_large_body()

SMALL_FIELDS = {"name": "Alice", "age": "30", "city": "Wonderland"}
MEDIUM_FIELDS = {f"field_{i}": f"value_{i} " * 20 for i in range(5)}
MEDIUM_FILES = {
    "file1": ("report.txt", b"x" * 2048, "text/plain"),
    "file2": ("data.bin", b"\x00\xff" * 2048, "application/octet-stream"),
}
LARGE_FIELDS = {f"field_{i}": f"value_{i} " * 100 for i in range(10)}


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


_BODY_SIZES = [
    pytest.param("small", SMALL_BODY, SMALL_CT, id="small"),
    pytest.param("medium", MEDIUM_BODY, MEDIUM_CT, id="medium"),
    pytest.param("large", LARGE_BODY, LARGE_CT, id="large"),
]


# ── Parse memory tests ──


@pytest.mark.parametrize("label,body,ct", _BODY_SIZES)
def test_parse_memory_zerodep(label: str, body: bytes, ct: str) -> None:
    """Measure peak memory for zerodep parse_multipart."""
    peak_kb = _measure_peak_kb(parse_multipart, body, ct)
    print(f"\n[multipart parse zerodep   {label:6s}] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.skipif(not _HAS_REF, reason="python-multipart not installed")
@pytest.mark.parametrize("label,body,ct", _BODY_SIZES)
def test_parse_memory_python_multipart(label: str, body: bytes, ct: str) -> None:
    """Measure peak memory for python-multipart parse."""
    peak_kb = _measure_peak_kb(_ref_parse_multipart, body, ct)
    print(f"\n[multipart parse reference {label:6s}] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.skipif(not _HAS_REF, reason="python-multipart not installed")
@pytest.mark.parametrize("label,body,ct", _BODY_SIZES)
def test_parse_memory_comparison(label: str, body: bytes, ct: str) -> None:
    """Compare zerodep vs python-multipart peak memory for parse."""
    zd_kb = _measure_peak_kb(parse_multipart, body, ct)
    ref_kb = _measure_peak_kb(_ref_parse_multipart, body, ct)
    ratio = zd_kb / ref_kb if ref_kb > 0 else float("inf")
    print(
        f"\n[multipart parse compare   {label:6s}] zerodep={zd_kb:.1f} KB  "
        f"reference={ref_kb:.1f} KB  ratio={ratio:.2f}x"
    )
    assert zd_kb >= 0
    assert ref_kb >= 0


# ── Encode memory tests ──


@pytest.mark.parametrize(
    "label,fields,files",
    [
        pytest.param("small", SMALL_FIELDS, None, id="small"),
        pytest.param("medium", MEDIUM_FIELDS, MEDIUM_FILES, id="medium"),
    ],
)
def test_encode_memory_zerodep(label: str, fields: dict, files) -> None:
    """Measure peak memory for zerodep encode_multipart."""
    kwargs = {"fields": fields, "boundary": "benchboundary"}
    if files is not None:
        kwargs["files"] = files
    peak_kb = _measure_peak_kb(encode_multipart, **kwargs)
    print(f"\n[multipart encode zerodep  {label:6s}] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0
