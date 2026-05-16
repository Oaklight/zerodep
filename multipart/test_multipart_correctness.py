"""Correctness tests for zerodep multipart module."""

import importlib
import os
import sys

import pytest

# Import reference library (python-multipart) via direct path loading
# to avoid name collision with our local multipart module.
_HAS_REF = False
multipart_ref = None  # type: ignore[assignment]
try:
    # Search site-packages for the installed python-multipart package.
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
                multipart_ref = importlib.util.module_from_spec(_spec)
                _spec.loader.exec_module(multipart_ref)
                _HAS_REF = True
            break
except Exception:
    pass

# Now patch sys.path so our local module takes priority.
sys.path.insert(0, os.path.dirname(__file__))

from multipart import (  # noqa: E402
    MultipartEncodeError,
    MultipartParseError,
    encode_multipart,
    extract_boundary,
    parse_multipart,
)

# ── Helpers ──


def _build_body(
    fields: dict[str, str] | None = None,
    files: dict[str, tuple[str, bytes] | tuple[str, bytes, str]] | None = None,
    boundary: str = "testboundary",
) -> tuple[bytes, str]:
    """Build a multipart body from fields and files using our encoder."""
    return encode_multipart(fields=fields, files=files, boundary=boundary)


def _ct(boundary: str = "testboundary") -> str:
    return f"multipart/form-data; boundary={boundary}"


# ── Basic parsing ──


class TestBasicParsing:
    def test_single_text_field(self):
        body, ct = _build_body(fields={"name": "Alice"})
        parts = parse_multipart(body, ct)
        assert len(parts) == 1
        assert parts[0].name == "name"
        assert parts[0].text == "Alice"
        assert parts[0].is_file is False

    def test_multiple_text_fields(self):
        body, ct = _build_body(fields={"a": "1", "b": "2", "c": "3"})
        parts = parse_multipart(body, ct)
        assert len(parts) == 3
        assert [p.name for p in parts] == ["a", "b", "c"]
        assert [p.text for p in parts] == ["1", "2", "3"]

    def test_single_file_upload(self):
        body, ct = _build_body(
            files={"doc": ("hello.txt", b"file content", "text/plain")}
        )
        parts = parse_multipart(body, ct)
        assert len(parts) == 1
        assert parts[0].name == "doc"
        assert parts[0].filename == "hello.txt"
        assert parts[0].data == b"file content"
        assert parts[0].content_type == "text/plain"
        assert parts[0].is_file is True

    def test_multiple_file_uploads(self):
        body, ct = _build_body(
            files={
                "f1": ("a.txt", b"aaa", "text/plain"),
                "f2": ("b.bin", b"\x00\x01\x02", "application/octet-stream"),
            }
        )
        parts = parse_multipart(body, ct)
        assert len(parts) == 2
        assert parts[0].filename == "a.txt"
        assert parts[1].filename == "b.bin"
        assert parts[1].data == b"\x00\x01\x02"

    def test_mixed_fields_and_files(self):
        body, ct = _build_body(
            fields={"user": "bob"},
            files={"avatar": ("pic.png", b"\x89PNG", "image/png")},
        )
        parts = parse_multipart(body, ct)
        assert len(parts) == 2
        names = [p.name for p in parts]
        assert "user" in names
        assert "avatar" in names

    def test_empty_field_value(self):
        body, ct = _build_body(fields={"empty": ""})
        parts = parse_multipart(body, ct)
        assert parts[0].text == ""

    def test_empty_file(self):
        body, ct = _build_body(files={"f": ("empty.bin", b"")})
        parts = parse_multipart(body, ct)
        assert parts[0].data == b""
        assert parts[0].filename == "empty.bin"

    def test_unicode_field_value(self):
        body, ct = _build_body(fields={"msg": "你好世界 🌍"})
        parts = parse_multipart(body, ct)
        assert parts[0].text == "你好世界 🌍"

    def test_binary_file_content(self):
        data = bytes(range(256))
        body, ct = _build_body(files={"bin": ("all.bin", data)})
        parts = parse_multipart(body, ct)
        assert parts[0].data == data

    def test_large_text_field(self):
        large = "x" * 100_000
        body, ct = _build_body(fields={"big": large})
        parts = parse_multipart(body, ct)
        assert parts[0].text == large

    def test_duplicate_field_names(self):
        body, ct = encode_multipart(
            fields=[("tag", "a"), ("tag", "b"), ("tag", "c")],
            boundary="dup",
        )
        parts = parse_multipart(body, "multipart/form-data; boundary=dup")
        assert len(parts) == 3
        assert all(p.name == "tag" for p in parts)
        assert [p.text for p in parts] == ["a", "b", "c"]

    def test_field_order_preserved(self):
        body, ct = encode_multipart(
            fields=[("z", "1"), ("a", "2"), ("m", "3")],
            boundary="order",
        )
        ct = "multipart/form-data; boundary=order"
        parts = parse_multipart(body, ct)
        assert [p.name for p in parts] == ["z", "a", "m"]

    def test_part_is_file_property(self):
        body, ct = _build_body(
            fields={"text": "val"},
            files={"file": ("f.txt", b"data")},
        )
        parts = parse_multipart(body, ct)
        text_part = next(p for p in parts if p.name == "text")
        file_part = next(p for p in parts if p.name == "file")
        assert text_part.is_file is False
        assert file_part.is_file is True

    def test_default_content_type_for_file(self):
        body, ct = _build_body(files={"f": ("x.bin", b"data")})
        parts = parse_multipart(body, ct)
        assert parts[0].content_type == "application/octet-stream"


# ── Boundary handling ──


class TestBoundaryHandling:
    def test_extract_boundary_simple(self):
        b = extract_boundary("multipart/form-data; boundary=abc123")
        assert b == "abc123"

    def test_extract_boundary_quoted(self):
        b = extract_boundary('multipart/form-data; boundary="abc 123"')
        assert b == "abc 123"

    def test_extract_boundary_with_special_chars(self):
        b = extract_boundary("multipart/form-data; boundary=---=Part.123")
        assert b == "---=Part.123"

    def test_extract_boundary_bare_string(self):
        b = extract_boundary("myboundary")
        assert b == "myboundary"

    def test_extract_boundary_missing_raises(self):
        with pytest.raises(MultipartParseError, match="no boundary"):
            extract_boundary("multipart/form-data")

    def test_boundary_like_content(self):
        """Data containing boundary-like strings mid-line is parsed correctly."""
        boundary = "BOUND"
        # The boundary string appears inside the data, but NOT on its own
        # line preceded by CRLF — so it must not be treated as a delimiter.
        trick_data = b"prefix--BOUND\r\nThis is NOT a boundary"
        body, ct = encode_multipart(
            fields={"safe": "ok"},
            files={"tricky": ("t.bin", trick_data)},
            boundary=boundary,
        )
        parts = parse_multipart(body, ct)
        file_part = next(p for p in parts if p.name == "tricky")
        assert file_part.data == trick_data

    def test_auto_boundary_avoids_content_collision(self):
        """Auto-generated boundary should not collide with file content."""
        data = b"--some-boundary\r\nLooks like a boundary"
        body, ct = encode_multipart(files={"f": ("f.bin", data)})
        parts = parse_multipart(body, ct)
        assert len(parts) == 1
        assert parts[0].data == data

    def test_preamble_ignored(self):
        boundary = "bnd"
        inner_body, _ = _build_body(fields={"k": "v"}, boundary=boundary)
        body = b"This is preamble text\r\n" + inner_body
        parts = parse_multipart(body, _ct(boundary))
        assert len(parts) == 1
        assert parts[0].text == "v"

    def test_epilogue_ignored(self):
        boundary = "bnd"
        inner_body, _ = _build_body(fields={"k": "v"}, boundary=boundary)
        body = inner_body + b"\r\nThis is epilogue text"
        parts = parse_multipart(body, _ct(boundary))
        assert len(parts) == 1


# ── Content-Disposition edge cases ──


class TestContentDisposition:
    def test_escaped_quotes_in_filename(self):
        raw = (
            b"--bnd\r\n"
            b'Content-Disposition: form-data; name="f"; '
            b'filename="file\\"name.txt"\r\n'
            b"\r\n"
            b"data\r\n"
            b"--bnd--\r\n"
        )
        parts = parse_multipart(raw, _ct("bnd"))
        assert parts[0].filename == 'file"name.txt'

    def test_rfc5987_filename_star(self):
        raw = (
            b"--bnd\r\n"
            b'Content-Disposition: form-data; name="f"; '
            b"filename*=UTF-8''%C3%A9l%C3%A8ve.txt\r\n"
            b"\r\n"
            b"data\r\n"
            b"--bnd--\r\n"
        )
        parts = parse_multipart(raw, _ct("bnd"))
        assert parts[0].filename == "élève.txt"

    def test_filename_with_path_stripped(self):
        raw = (
            b"--bnd\r\n"
            b'Content-Disposition: form-data; name="f"; '
            b'filename="C:\\Users\\bob\\file.txt"\r\n'
            b"\r\n"
            b"data\r\n"
            b"--bnd--\r\n"
        )
        parts = parse_multipart(raw, _ct("bnd"))
        assert parts[0].filename == "file.txt"

    def test_missing_name_raises(self):
        raw = b"--bnd\r\nContent-Disposition: form-data\r\n\r\ndata\r\n--bnd--\r\n"
        with pytest.raises(MultipartParseError, match="name"):
            parse_multipart(raw, _ct("bnd"))

    def test_missing_content_disposition_raises(self):
        raw = b"--bnd\r\nContent-Type: text/plain\r\n\r\ndata\r\n--bnd--\r\n"
        with pytest.raises(MultipartParseError, match="Content-Disposition"):
            parse_multipart(raw, _ct("bnd"))

    def test_empty_filename(self):
        raw = (
            b"--bnd\r\n"
            b'Content-Disposition: form-data; name="f"; filename=""\r\n'
            b"\r\n"
            b"data\r\n"
            b"--bnd--\r\n"
        )
        parts = parse_multipart(raw, _ct("bnd"))
        assert parts[0].filename == ""
        assert parts[0].is_file is True


# ── Content-Transfer-Encoding ──


class TestTransferEncoding:
    def test_base64_encoded_part(self):
        import base64 as b64

        encoded = b64.b64encode(b"hello world")
        raw = (
            b"--bnd\r\n"
            b'Content-Disposition: form-data; name="f"\r\n'
            b"Content-Transfer-Encoding: base64\r\n"
            b"\r\n" + encoded + b"\r\n"
            b"--bnd--\r\n"
        )
        parts = parse_multipart(raw, _ct("bnd"))
        assert parts[0].data == b"hello world"

    def test_quoted_printable_part(self):
        encoded = b"Hello=20World=0D=0A"
        raw = (
            b"--bnd\r\n"
            b'Content-Disposition: form-data; name="f"\r\n'
            b"Content-Transfer-Encoding: quoted-printable\r\n"
            b"\r\n" + encoded + b"\r\n"
            b"--bnd--\r\n"
        )
        parts = parse_multipart(raw, _ct("bnd"))
        assert parts[0].data == b"Hello World\r\n"

    def test_7bit_passthrough(self):
        raw = (
            b"--bnd\r\n"
            b'Content-Disposition: form-data; name="f"\r\n'
            b"Content-Transfer-Encoding: 7bit\r\n"
            b"\r\n"
            b"plain text\r\n"
            b"--bnd--\r\n"
        )
        parts = parse_multipart(raw, _ct("bnd"))
        assert parts[0].data == b"plain text"


# ── Line ending variations ──


class TestLineEndings:
    def test_lf_only(self):
        raw = b'--bnd\nContent-Disposition: form-data; name="f"\n\ndata\n--bnd--\n'
        parts = parse_multipart(raw, _ct("bnd"))
        assert len(parts) == 1
        assert parts[0].data == b"data"

    def test_crlf_standard(self):
        body, ct = _build_body(fields={"k": "v"})
        parts = parse_multipart(body, ct)
        assert parts[0].text == "v"


# ── Malformed input ──


class TestMalformed:
    def test_empty_body(self):
        parts = parse_multipart(b"", _ct("bnd"))
        assert parts == []

    def test_no_boundary_in_body(self):
        parts = parse_multipart(b"just some random data", _ct("bnd"))
        assert parts == []

    def test_no_parts_only_boundaries(self):
        raw = b"--bnd\r\n--bnd--\r\n"
        parts = parse_multipart(raw, _ct("bnd"))
        assert parts == []

    def test_max_part_size_exceeded(self):
        body, ct = _build_body(fields={"big": "x" * 1000})
        with pytest.raises(MultipartParseError, match="maximum size"):
            parse_multipart(body, ct, max_part_size=100)

    def test_max_parts_exceeded(self):
        body, ct = encode_multipart(
            fields=[("f", str(i)) for i in range(10)],
            boundary="bnd",
        )
        with pytest.raises(MultipartParseError, match="maximum.*parts"):
            parse_multipart(body, _ct("bnd"), max_parts=5)


# ── Encoding ──


class TestEncoding:
    def test_encode_text_field(self):
        body, ct = encode_multipart(fields={"key": "value"})
        assert b"key" in body
        assert b"value" in body
        assert "multipart/form-data; boundary=" in ct

    def test_encode_file(self):
        body, ct = encode_multipart(files={"f": ("test.txt", b"content", "text/plain")})
        assert b"test.txt" in body
        assert b"content" in body
        assert b"text/plain" in body

    def test_encode_mixed(self):
        body, ct = encode_multipart(
            fields={"name": "Alice"},
            files={"doc": ("a.txt", b"data")},
        )
        parts = parse_multipart(body, ct)
        assert len(parts) == 2

    def test_encode_custom_boundary(self):
        body, ct = encode_multipart(fields={"k": "v"}, boundary="CUSTOM")
        assert b"--CUSTOM" in body
        assert "boundary=CUSTOM" in ct

    def test_encode_bytes_field_value(self):
        body, ct = encode_multipart(fields={"bin": b"\x00\x01"})
        parts = parse_multipart(body, ct)
        assert parts[0].data == b"\x00\x01"

    def test_encode_file_bytes_only(self):
        body, ct = encode_multipart(files={"f": b"raw bytes"})
        parts = parse_multipart(body, ct)
        assert parts[0].data == b"raw bytes"
        assert parts[0].is_file is True

    def test_encode_empty(self):
        body, ct = encode_multipart()
        assert b"--" in body

    def test_encode_boundary_too_long_raises(self):
        with pytest.raises(MultipartEncodeError, match="maximum length"):
            encode_multipart(fields={"k": "v"}, boundary="x" * 100)

    def test_encode_list_fields_preserves_order(self):
        body, ct = encode_multipart(fields=[("z", "1"), ("a", "2"), ("m", "3")])
        parts = parse_multipart(body, ct)
        assert [p.name for p in parts] == ["z", "a", "m"]


# ── Round-trip ──


class TestRoundTrip:
    def test_text_fields_roundtrip(self):
        fields = {"name": "Alice", "age": "30", "city": "NYC"}
        body, ct = encode_multipart(fields=fields)
        parts = parse_multipart(body, ct)
        result = {p.name: p.text for p in parts}
        assert result == fields

    def test_file_upload_roundtrip(self):
        data = os.urandom(1024)
        body, ct = encode_multipart(files={"f": ("photo.jpg", data, "image/jpeg")})
        parts = parse_multipart(body, ct)
        assert parts[0].filename == "photo.jpg"
        assert parts[0].data == data
        assert parts[0].content_type == "image/jpeg"

    def test_mixed_roundtrip(self):
        fields = {"user": "bob", "action": "upload"}
        file_data = b"PDF content here"
        body, ct = encode_multipart(
            fields=fields,
            files={"doc": ("report.pdf", file_data, "application/pdf")},
        )
        parts = parse_multipart(body, ct)
        text_parts = {p.name: p.text for p in parts if not p.is_file}
        file_parts = [p for p in parts if p.is_file]
        assert text_parts == fields
        assert len(file_parts) == 1
        assert file_parts[0].data == file_data

    def test_binary_content_roundtrip(self):
        data = bytes(range(256)) * 10
        body, ct = encode_multipart(files={"bin": ("all.bin", data)})
        parts = parse_multipart(body, ct)
        assert parts[0].data == data

    def test_unicode_roundtrip(self):
        fields = {"msg": "こんにちは世界 🎉", "name": "Ñoño"}
        body, ct = encode_multipart(fields=fields)
        parts = parse_multipart(body, ct)
        result = {p.name: p.text for p in parts}
        assert result == fields


# ── Reference comparison vs python-multipart ──


@pytest.mark.skipif(not _HAS_REF, reason="python-multipart not installed")
class TestVsReference:
    """Compare parsed output against python-multipart."""

    @staticmethod
    def _parse_with_reference(body: bytes, boundary: str) -> list[dict]:
        """Parse using python-multipart and return a list of dicts."""
        results: list[dict] = []
        current: dict = {}

        def on_part_begin():
            nonlocal current
            current = {"headers": {}, "data": bytearray()}

        def on_part_data(data: bytes, start: int, end: int):
            current["data"].extend(data[start:end])

        def on_part_end():
            results.append(current)

        def on_header_field(data: bytes, start: int, end: int):
            current["_header_field"] = data[start:end].decode("latin-1")

        def on_header_value(data: bytes, start: int, end: int):
            field = current.pop("_header_field", "")
            current["headers"][field.lower()] = data[start:end].decode("latin-1")

        callbacks = {
            "on_part_begin": on_part_begin,
            "on_part_data": on_part_data,
            "on_part_end": on_part_end,
            "on_header_field": on_header_field,
            "on_header_value": on_header_value,
        }

        parser = multipart_ref.MultipartParser(boundary.encode(), callbacks)
        parser.write(body)
        parser.finalize()
        return results

    def test_text_fields_match_reference(self):
        body, ct = _build_body(fields={"name": "Alice", "age": "30"})
        boundary = extract_boundary(ct)

        ours = parse_multipart(body, ct)
        theirs = self._parse_with_reference(body, boundary)

        assert len(ours) == len(theirs)
        for our_part, ref_part in zip(ours, theirs):
            assert our_part.data == bytes(ref_part["data"])

    def test_file_upload_match_reference(self):
        data = os.urandom(512)
        body, ct = _build_body(
            files={"doc": ("test.bin", data, "application/octet-stream")}
        )
        boundary = extract_boundary(ct)

        ours = parse_multipart(body, ct)
        theirs = self._parse_with_reference(body, boundary)

        assert len(ours) == len(theirs)
        assert ours[0].data == bytes(theirs[0]["data"])

    def test_mixed_match_reference(self):
        body, ct = _build_body(
            fields={"user": "bob"},
            files={"avatar": ("pic.png", b"\x89PNG\r\n", "image/png")},
        )
        boundary = extract_boundary(ct)

        ours = parse_multipart(body, ct)
        theirs = self._parse_with_reference(body, boundary)

        assert len(ours) == len(theirs)
        for our_part, ref_part in zip(ours, theirs):
            assert our_part.data == bytes(ref_part["data"])

    def test_binary_data_match_reference(self):
        data = bytes(range(256))
        body, ct = _build_body(files={"bin": ("all.bin", data)})
        boundary = extract_boundary(ct)

        ours = parse_multipart(body, ct)
        theirs = self._parse_with_reference(body, boundary)

        assert ours[0].data == bytes(theirs[0]["data"])
