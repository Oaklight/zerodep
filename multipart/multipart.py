# /// zerodep
# version = "0.1.0"
# deps = []
# tier = "medium"
# category = "serialization"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///
"""Zero-dependency multipart/form-data parser and encoder.

Parses and encodes ``multipart/form-data`` bodies per RFC 7578 / RFC 2046.
Designed for HTTP file upload handling without any third-party dependencies.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.
"""

from __future__ import annotations

import base64
import dataclasses
import os
import quopri
import re
import urllib.parse
from collections.abc import Iterator
from typing import Any

__all__ = [
    "MultipartError",
    "MultipartParseError",
    "MultipartEncodeError",
    "Part",
    "parse_multipart",
    "encode_multipart",
    "extract_boundary",
]

# ── Constants ──

_DEFAULT_MAX_PART_SIZE = 10 * 1024 * 1024  # 10 MB
_DEFAULT_MAX_PARTS = 1000
_MAX_HEADER_SIZE = 16 * 1024  # 16 KB
_MAX_BOUNDARY_LEN = 70  # RFC 2046 §5.1.1

# Regex for parsing header parameters (e.g. name="value" or name=token)
_PARAM_RE = re.compile(
    r";\s*"
    r"([a-zA-Z_][\w*-]*)"  # parameter name (allows trailing *)
    r"\s*=\s*"
    r'(?:"((?:[^"\\]|\\.)*)"|'  # quoted value (with backslash escapes)
    r"([^\s;]*))",  # or unquoted token
)


# ── Exceptions ──


class MultipartError(Exception):
    """Base exception for the multipart module."""


class MultipartParseError(MultipartError):
    """Raised when parsing fails (malformed input, missing boundary, etc.)."""


class MultipartEncodeError(MultipartError):
    """Raised when encoding fails (invalid arguments)."""


# ── Data classes ──


@dataclasses.dataclass(frozen=True, slots=True)
class Part:
    """A single part from a multipart/form-data body.

    Attributes:
        name: Form field name from Content-Disposition.
        data: Raw bytes content of this part.
        filename: Original filename for file uploads, or None for text fields.
        content_type: MIME type of this part.
        headers: All MIME headers of this part (keys lowercased).
    """

    name: str
    data: bytes
    filename: str | None = None
    content_type: str = "text/plain"
    headers: dict[str, str] = dataclasses.field(default_factory=dict)

    @property
    def text(self) -> str:
        """Decode data as text using charset from content_type, or UTF-8."""
        charset = _extract_charset(self.content_type)
        return self.data.decode(charset)

    @property
    def is_file(self) -> bool:
        """True if this part has a filename (i.e., is a file upload)."""
        return self.filename is not None


# ── Public API ──


def extract_boundary(content_type: str) -> str:
    """Extract the boundary string from a Content-Type header.

    Handles both quoted and unquoted boundaries.  If the string contains
    no ``boundary=``, it is returned as-is (assumed to be a bare boundary).

    Args:
        content_type: Full Content-Type header value or bare boundary string.

    Returns:
        The boundary string.

    Raises:
        MultipartParseError: If Content-Type is multipart/* but has no boundary.
    """
    # Try to find boundary= in the header
    match = re.search(
        r"boundary\s*=\s*(?:\"([^\"]*)\"|([^\s;]+))",
        content_type,
        re.IGNORECASE,
    )
    if match:
        return match.group(1) if match.group(1) is not None else match.group(2)

    # If it looks like a Content-Type header but has no boundary, error
    if "multipart/" in content_type.lower():
        raise MultipartParseError(
            "Content-Type is multipart/* but contains no boundary parameter"
        )

    # Treat the whole string as a bare boundary value
    return content_type.strip()


def parse_multipart(
    body: bytes,
    content_type: str,
    *,
    max_part_size: int = _DEFAULT_MAX_PART_SIZE,
    max_parts: int = _DEFAULT_MAX_PARTS,
) -> list[Part]:
    """Parse a multipart/form-data request body into a list of parts.

    Args:
        body: The raw request body bytes.
        content_type: Full Content-Type header value
            (e.g. ``"multipart/form-data; boundary=abc123"``), or just the
            boundary string itself.
        max_part_size: Maximum size in bytes for any single part.
            Set to 0 to disable.
        max_parts: Maximum number of parts allowed.
            Set to 0 to disable.

    Returns:
        List of Part objects in the order they appeared.

    Raises:
        MultipartParseError: If the body is malformed or limits are exceeded.
    """
    boundary = extract_boundary(content_type)
    return list(_iter_parts(body, boundary, max_part_size, max_parts))


def encode_multipart(
    fields: dict[str, str | bytes] | list[tuple[str, str | bytes]] | None = None,
    files: (
        dict[str, bytes | tuple[str, bytes] | tuple[str, bytes, str]]
        | list[tuple[str, bytes | tuple[str, bytes] | tuple[str, bytes, str]]]
        | None
    ) = None,
    *,
    boundary: str | None = None,
) -> tuple[bytes, str]:
    """Encode form fields and files as a multipart/form-data body.

    Args:
        fields: Text form fields as ``{name: value}`` dict or
            ``[(name, value)]`` list.  Values can be str or bytes.
        files: File uploads as dict or list of tuples.  Each value can be:

            - ``bytes`` -- raw content (auto filename, octet-stream)
            - ``(filename, bytes)`` -- named file
            - ``(filename, bytes, content_type)`` -- named file with MIME type
        boundary: Optional boundary string.  If None, a random one is
            generated.

    Returns:
        ``(body_bytes, content_type_header)`` where content_type_header is
        the full ``"multipart/form-data; boundary=..."`` string.

    Raises:
        MultipartEncodeError: If arguments are invalid.
    """
    if boundary is None:
        boundary = os.urandom(16).hex()

    if len(boundary) > _MAX_BOUNDARY_LEN:
        raise MultipartEncodeError(
            f"Boundary exceeds maximum length of {_MAX_BOUNDARY_LEN}"
        )

    buf = bytearray()
    delim = f"--{boundary}\r\n".encode()

    # Encode text fields
    field_items: list[tuple[str, str | bytes]] = []
    if isinstance(fields, dict):
        field_items = list(fields.items())
    elif fields is not None:
        field_items = list(fields)

    for name, value in field_items:
        buf += delim
        cd = f'Content-Disposition: form-data; name="{_quote_name(name)}"\r\n'
        buf += cd.encode()
        buf += b"\r\n"
        if isinstance(value, bytes):
            buf += value
        else:
            buf += str(value).encode()
        buf += b"\r\n"

    # Encode file uploads
    file_items: list[tuple[str, Any]] = []
    if isinstance(files, dict):
        file_items = list(files.items())
    elif files is not None:
        file_items = list(files)

    for name, file_val in file_items:
        buf += delim
        filename: str
        data: bytes
        ct: str

        if isinstance(file_val, bytes):
            filename = name
            data = file_val
            ct = "application/octet-stream"
        elif isinstance(file_val, tuple):
            if len(file_val) == 2:
                filename, data = file_val  # type: ignore[misc]
                ct = "application/octet-stream"
            elif len(file_val) == 3:
                filename, data, ct = file_val  # type: ignore[misc]
            else:
                raise MultipartEncodeError(
                    f"File tuple for '{name}' must have 2 or 3 elements, "
                    f"got {len(file_val)}"
                )
        else:
            raise MultipartEncodeError(
                f"File value for '{name}' must be bytes or tuple, "
                f"got {type(file_val).__name__}"
            )

        buf += (
            f'Content-Disposition: form-data; name="{_quote_name(name)}"; '
            f'filename="{_quote_name(filename)}"\r\n'
        ).encode()
        buf += f"Content-Type: {ct}\r\n".encode()
        buf += b"\r\n"
        buf += data
        buf += b"\r\n"

    buf += f"--{boundary}--\r\n".encode()

    content_type_header = f"multipart/form-data; boundary={boundary}"
    return bytes(buf), content_type_header


# ── Internal helpers ──


def _iter_parts(
    body: bytes,
    boundary: str,
    max_part_size: int,
    max_parts: int,
) -> Iterator[Part]:
    """Iterate over parts in a multipart body using boundary-split algorithm."""
    delimiter = f"--{boundary}".encode()
    delim_len = len(delimiter)

    # Find the first boundary (skip preamble)
    first = body.find(delimiter)
    if first == -1:
        return  # no boundary found → no parts

    # Advance past the first delimiter
    pos = first + delim_len

    # Check if immediately followed by -- (empty body, only closing boundary)
    if body[pos : pos + 2] == b"--":
        return

    # Skip past the CRLF or LF after the first delimiter
    if body[pos : pos + 2] == b"\r\n":
        pos += 2
    elif body[pos : pos + 1] == b"\n":
        pos += 1

    part_count = 0

    while pos < len(body):
        # Find the next real boundary delimiter.  A real boundary must be
        # preceded by CRLF or LF AND followed by CRLF, LF, or "--".
        # This prevents false matches when the boundary string appears
        # inside part data.
        delim_pos = _find_next_boundary(body, delimiter, delim_len, pos)

        if delim_pos == -1:
            # No more delimiters — treat the rest as the last part
            raw_part = body[pos:]
            end_pos = len(body)
        else:
            # Trim the preceding line ending from the part data
            part_end = delim_pos
            if part_end >= 2 and body[part_end - 2 : part_end] == b"\r\n":
                part_end -= 2
            elif part_end >= 1 and body[part_end - 1 : part_end] == b"\n":
                part_end -= 1
            raw_part = body[pos:part_end]
            end_pos = delim_pos + delim_len

        # Check limits
        if max_parts and part_count >= max_parts:
            raise MultipartParseError(f"Exceeded maximum of {max_parts} parts")
        if max_part_size and len(raw_part) > max_part_size:
            raise MultipartParseError(
                f"Part exceeds maximum size of {max_part_size} bytes"
            )

        # Parse the part
        part = _parse_raw_part(raw_part)
        if part is not None:
            yield part
            part_count += 1

        if delim_pos == -1:
            break

        # Check for closing -- or skip CRLF/LF
        if end_pos < len(body):
            if body[end_pos : end_pos + 2] == b"--":
                break  # final boundary
            if body[end_pos : end_pos + 2] == b"\r\n":
                end_pos += 2
            elif body[end_pos : end_pos + 1] == b"\n":
                end_pos += 1

        pos = end_pos


def _find_next_boundary(
    body: bytes, delimiter: bytes, delim_len: int, start: int
) -> int:
    """Find the next real boundary in the body starting from *start*.

    A real boundary is ``delimiter`` preceded by CRLF or LF (or at the
    very start of the body) and followed by CRLF, LF, or ``--``.  This
    prevents false matches when boundary-like strings appear in part data.

    Returns:
        The index of the first byte of the delimiter, or -1 if not found.
    """
    search_from = start
    while True:
        idx = body.find(delimiter, search_from)
        if idx == -1:
            return -1

        # Check preceding bytes: must be CRLF, LF, or start of body
        if idx > 0:
            if body[idx - 2 : idx] == b"\r\n":
                pass  # valid: preceded by CRLF
            elif body[idx - 1 : idx] == b"\n":
                pass  # valid: preceded by LF
            else:
                # Not a real boundary — keep searching
                search_from = idx + 1
                continue

        # Check following bytes: must be CRLF, LF, or "--"
        after = idx + delim_len
        if after >= len(body):
            return idx  # at end of body — accept
        suffix = body[after : after + 2]
        if suffix == b"\r\n" or suffix == b"--":
            return idx
        if body[after : after + 1] == b"\n":
            return idx

        # Not a real boundary — keep searching
        search_from = idx + 1


def _parse_raw_part(raw: bytes) -> Part | None:
    """Parse a single raw part (headers + body) into a Part object."""
    if not raw:
        return None

    # Split headers from body
    sep_crlf = raw.find(b"\r\n\r\n")
    sep_lf = raw.find(b"\n\n")

    if sep_crlf == -1 and sep_lf == -1:
        return None  # no header/body separator

    if sep_crlf == -1:
        header_bytes = raw[:sep_lf]
        body = raw[sep_lf + 2 :]
    elif sep_lf == -1:
        header_bytes = raw[:sep_crlf]
        body = raw[sep_crlf + 4 :]
    else:
        # Use whichever comes first
        if sep_crlf <= sep_lf:
            header_bytes = raw[:sep_crlf]
            body = raw[sep_crlf + 4 :]
        else:
            header_bytes = raw[:sep_lf]
            body = raw[sep_lf + 2 :]

    # Guard against oversized headers
    if len(header_bytes) > _MAX_HEADER_SIZE:
        raise MultipartParseError(
            f"Part headers exceed maximum size of {_MAX_HEADER_SIZE} bytes"
        )

    headers = _parse_headers(header_bytes)

    # Extract Content-Disposition parameters
    cd = headers.get("content-disposition", "")
    if not cd:
        raise MultipartParseError("Part is missing Content-Disposition header")

    params = _parse_header_params(cd)
    name = params.get("name")
    if name is None:
        raise MultipartParseError(
            "Content-Disposition is missing required 'name' parameter"
        )

    # Prefer filename* (RFC 5987) over filename
    filename = None
    if "filename*" in params:
        filename = _decode_rfc5987(params["filename*"])
    elif "filename" in params:
        filename = params["filename"]

    # Strip path components from filename for security
    if filename:
        filename = filename.replace("\\", "/")
        if "/" in filename:
            filename = filename.rsplit("/", 1)[1]

    # Determine content type
    content_type = headers.get("content-type", "")
    if not content_type:
        content_type = (
            "application/octet-stream" if filename is not None else "text/plain"
        )

    # Handle Content-Transfer-Encoding
    transfer_encoding = headers.get("content-transfer-encoding")
    body = _decode_transfer(body, transfer_encoding)

    return Part(
        name=name,
        data=body,
        filename=filename,
        content_type=content_type,
        headers=headers,
    )


def _parse_headers(raw: bytes) -> dict[str, str]:
    """Parse MIME headers from bytes into a lowercase-keyed dict.

    Handles header continuation (folded headers) per RFC 2822.
    """
    text = raw.decode("latin-1")
    headers: dict[str, str] = {}
    current_key: str | None = None
    current_val: str = ""

    for line in text.split("\n"):
        line = line.rstrip("\r")
        if not line:
            continue
        # Continuation line (starts with whitespace)
        if line[0] in (" ", "\t"):
            if current_key is not None:
                current_val += " " + line.strip()
            continue
        # Save previous header
        if current_key is not None:
            headers[current_key] = current_val
        # Parse new header
        if ":" in line:
            key, val = line.split(":", 1)
            current_key = key.strip().lower()
            current_val = val.strip()
        else:
            current_key = None

    # Save last header
    if current_key is not None:
        headers[current_key] = current_val

    return headers


def _parse_header_params(header_value: str) -> dict[str, str]:
    """Extract key=value parameters from a header value.

    Returns:
        Dict of parameter names to values (unquoted, unescaped).
    """
    params: dict[str, str] = {}
    for match in _PARAM_RE.finditer(header_value):
        key = match.group(1).lower()
        # Prefer quoted value (group 2) over unquoted (group 3)
        value = match.group(2) if match.group(2) is not None else match.group(3)
        # Unescape backslash sequences in quoted values
        if match.group(2) is not None:
            value = value.replace('\\"', '"').replace("\\\\", "\\")
        params[key] = value
    return params


def _decode_rfc5987(value: str) -> str:
    """Decode RFC 5987 extended parameter value.

    Format: ``charset'language'percent-encoded-value``

    Args:
        value: The raw parameter value (e.g. ``UTF-8''%C3%A9.txt``).

    Returns:
        The decoded string.
    """
    parts = value.split("'", 2)
    if len(parts) != 3:
        return value  # malformed, return as-is
    charset, _language, encoded = parts
    return urllib.parse.unquote(encoded, encoding=charset or "utf-8")


def _decode_transfer(data: bytes, transfer_encoding: str | None) -> bytes:
    """Apply Content-Transfer-Encoding decoding if needed.

    Args:
        data: Raw part body bytes.
        transfer_encoding: The encoding name, or None.

    Returns:
        Decoded bytes.
    """
    if not transfer_encoding:
        return data
    te = transfer_encoding.strip().lower()
    if te == "base64":
        return base64.b64decode(data)
    if te == "quoted-printable":
        return quopri.decodestring(data)
    # 7bit, 8bit, binary → no transformation
    return data


def _extract_charset(content_type: str) -> str:
    """Extract charset from a Content-Type header, defaulting to UTF-8."""
    match = re.search(r"charset\s*=\s*([^\s;]+)", content_type, re.IGNORECASE)
    if match:
        return match.group(1).strip('"')
    return "utf-8"


def _quote_name(value: str) -> str:
    """Escape a string for use in a quoted Content-Disposition parameter."""
    return value.replace("\\", "\\\\").replace('"', '\\"')
