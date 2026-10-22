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


# ── Fixture data: real-world multipart payloads ──

_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
_FIXTURE_CACHE: dict[str, tuple[bytes, str]] = {}

_FIXTURE_FILES = {
    "form-with-file": ("form-with-file.bin", "form-with-file.content-type"),
    "mixed-charsets": ("mixed-charsets.bin", "mixed-charsets.content-type"),
    "large-binary": ("large-binary.bin", "large-binary.content-type"),
}


def _fixture_available(name: str) -> bool:
    if name not in _FIXTURE_FILES:
        return False
    bin_file, ct_file = _FIXTURE_FILES[name]
    return os.path.isfile(os.path.join(_FIXTURES_DIR, bin_file)) and os.path.isfile(
        os.path.join(_FIXTURES_DIR, ct_file)
    )


def _get_fixture(name: str) -> tuple[bytes, str]:
    if name not in _FIXTURE_CACHE:
        bin_file, ct_file = _FIXTURE_FILES[name]
        with open(os.path.join(_FIXTURES_DIR, bin_file), "rb") as f:
            body = f.read()
        with open(os.path.join(_FIXTURES_DIR, ct_file), encoding="utf-8") as f:
            ct = f.read().strip()
        _FIXTURE_CACHE[name] = (body, ct)
    return _FIXTURE_CACHE[name]


# ── Fixture parse benchmarks ──


@pytest.mark.skipif(not _fixture_available("form-with-file"), reason="fixture missing")
class TestFixtureParseFormWithFile:
    def test_zerodep(self, benchmark):
        body, ct = _get_fixture("form-with-file")
        benchmark(parse_multipart, body, ct)

    @pytest.mark.skipif(not _HAS_REF, reason="python-multipart not installed")
    def test_python_multipart(self, benchmark):
        body, ct = _get_fixture("form-with-file")
        benchmark(_ref_parse_multipart, body, ct)


@pytest.mark.skipif(not _fixture_available("mixed-charsets"), reason="fixture missing")
class TestFixtureParseMixedCharsets:
    def test_zerodep(self, benchmark):
        body, ct = _get_fixture("mixed-charsets")
        benchmark(parse_multipart, body, ct)

    @pytest.mark.skipif(not _HAS_REF, reason="python-multipart not installed")
    def test_python_multipart(self, benchmark):
        body, ct = _get_fixture("mixed-charsets")
        benchmark(_ref_parse_multipart, body, ct)


@pytest.mark.skipif(not _fixture_available("large-binary"), reason="fixture missing")
class TestFixtureParseLargeBinary:
    def test_zerodep(self, benchmark):
        body, ct = _get_fixture("large-binary")
        benchmark(parse_multipart, body, ct)

    @pytest.mark.skipif(not _HAS_REF, reason="python-multipart not installed")
    def test_python_multipart(self, benchmark):
        body, ct = _get_fixture("large-binary")
        benchmark(_ref_parse_multipart, body, ct)


# ── Scale curve: vary number of parts / total payload size geometrically ──


def _make_scale_body(n_parts: int, part_size: int) -> tuple[bytes, str]:
    """Build a multipart body with *n_parts* binary parts of *part_size* bytes each."""
    files = {
        f"file_{i}": (f"data_{i}.bin", bytes(range(256)) * (part_size // 256 + 1))[
            :part_size
        ]
        for i in range(n_parts)
    }
    return encode_multipart(fields={}, files=files, boundary="scalebench")


# Scale by total payload size: (n_parts, part_size_bytes) → ~target payload.
# Total ≈ n_parts * part_size (plus multipart framing overhead).
_SCALE_PARAMS = [
    (1, 100, "100B"),
    (1, 500, "500B"),
    (2, 512, "1KB"),
    (5, 1_024, "5KB"),
    (5, 2_048, "10KB"),
    (10, 5_120, "50KB"),
    (10, 10_240, "100KB"),
    (20, 25_000, "500KB"),
]

# Pre-build all payloads so construction cost is excluded from benchmarks.
_SCALE_BODIES: dict[str, tuple[bytes, str]] = {
    label: _make_scale_body(n_parts, part_size)
    for n_parts, part_size, label in _SCALE_PARAMS
}


class TestScaleCurve:
    """Scale curves: vary total payload size to reveal parse/encode complexity.

    Each parametrized ID encodes the approximate total payload size so
    results can be plotted against input scale.
    """

    @pytest.mark.parametrize("label", [lbl for _, _, lbl in _SCALE_PARAMS])
    def test_parse_zerodep(self, benchmark, label):
        """zerodep parse_multipart: scale with payload size."""
        body, ct = _SCALE_BODIES[label]
        benchmark(parse_multipart, body, ct)

    @pytest.mark.skipif(not _HAS_REF, reason="python-multipart not installed")
    @pytest.mark.parametrize("label", [lbl for _, _, lbl in _SCALE_PARAMS])
    def test_parse_python_multipart(self, benchmark, label):
        """python-multipart parse: scale with payload size."""
        body, ct = _SCALE_BODIES[label]
        benchmark(_ref_parse_multipart, body, ct)

    @pytest.mark.parametrize("label", [lbl for _, _, lbl in _SCALE_PARAMS])
    def test_encode_zerodep(self, benchmark, label):
        """zerodep encode_multipart: scale with payload size."""
        n_parts, part_size, _lbl = next(
            (n, p, lb) for n, p, lb in _SCALE_PARAMS if lb == label
        )
        files = {
            f"file_{i}": (
                f"data_{i}.bin",
                (bytes(range(256)) * (part_size // 256 + 1))[:part_size],
            )
            for i in range(n_parts)
        }
        benchmark(encode_multipart, {}, files, boundary="scalebench")

    @pytest.mark.parametrize("label", [lbl for _, _, lbl in _SCALE_PARAMS])
    def test_roundtrip_zerodep(self, benchmark, label):
        """zerodep encode + parse roundtrip: scale with payload size."""
        n_parts, part_size, _lbl = next(
            (n, p, lb) for n, p, lb in _SCALE_PARAMS if lb == label
        )
        files = {
            f"file_{i}": (
                f"data_{i}.bin",
                (bytes(range(256)) * (part_size // 256 + 1))[:part_size],
            )
            for i in range(n_parts)
        }

        def roundtrip():
            body, ct = encode_multipart({}, files, boundary="scalebench")
            return parse_multipart(body, ct)

        benchmark(roundtrip)
