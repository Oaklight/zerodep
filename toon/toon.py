# /// zerodep
# version = "0.2.1"
# deps = []
# tier = "simple"
# ///

"""TOON encoder/decoder — zero dependencies, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Drop-in replacement for toon_format core functionality (encode/decode).

TOON is a compact, human-readable serialization format designed for LLM contexts,
achieving 30-60% token reduction vs JSON. It combines YAML-like indentation with
CSV-like tabular arrays.

Example::

    encode({"name": "Alice", "age": 30})
    # 'name: Alice\nage: 30'
    decode("name: Alice\nage: 30")
    # {'name': 'Alice', 'age': 30}
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import PurePath
from typing import Any, Literal, TypedDict, TypeGuard, Union

# ── Types ─────────────────────────────────────────────────────────────────────

JsonPrimitive = Union[str, int, float, bool, None]
JsonObject = dict[str, Any]
JsonArray = list[Any]
JsonValue = Union[JsonPrimitive, JsonArray, JsonObject]


class EncodeOptions(TypedDict, total=False):
    """Options for TOON encoding.

    Attributes:
        indent: Number of spaces per indentation level (default: 2).
        delimiter: Delimiter character for arrays (default: ",").
        lengthMarker: Marker to prefix array lengths (default: False).
    """

    indent: int
    delimiter: str
    lengthMarker: Union[Literal["#"], Literal[False]]


class DecodeOptions(TypedDict, total=False):
    """Options for TOON decoding.

    Attributes:
        indent: Number of spaces per indentation level (default: 2).
        strict: Enable strict validation (default: True).
    """

    indent: int
    strict: bool


class ToonDecodeError(Exception):
    """Error raised when TOON decoding fails."""


# ── Constants ─────────────────────────────────────────────────────────────────

_COMMA = ","
_COLON = ":"
_PIPE = "|"
_TAB = "\t"
_BACKSLASH = "\\"
_DQUOTE = '"'
_LIST_PREFIX = "- "

_DELIMITERS: dict[str, str] = {"comma": _COMMA, "tab": _TAB, "pipe": _PIPE}

_NUMERIC_RE = re.compile(r"^-?\d+(?:\.\d+)?(?:e[+-]?\d+)?$", re.IGNORECASE)
_OCTAL_RE = re.compile(r"^0\d+$")
_VALID_KEY_RE = re.compile(r"^[A-Za-z_][\w.]*$")

# ── String utilities ──────────────────────────────────────────────────────────


def _escape(value: str) -> str:
    """Escape special characters for TOON encoding."""
    return (
        value.replace(_BACKSLASH, _BACKSLASH + _BACKSLASH)
        .replace(_DQUOTE, _BACKSLASH + _DQUOTE)
        .replace("\n", _BACKSLASH + "n")
        .replace("\r", _BACKSLASH + "r")
        .replace("\t", _BACKSLASH + "t")
    )


def _unescape(value: str) -> str:
    """Process escape sequences in a TOON string."""
    _MAP = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\", '"': '"'}
    result: list[str] = []
    i = 0
    while i < len(value):
        if value[i] == _BACKSLASH:
            if i + 1 >= len(value):
                raise ValueError("Backslash at end of string")
            nxt = value[i + 1]
            if nxt not in _MAP:
                raise ValueError(f"Invalid escape sequence: \\{nxt}")
            result.append(_MAP[nxt])
            i += 2
        else:
            result.append(value[i])
            i += 1
    return "".join(result)


def _iter_unquoted(line: str, start: int = 0):
    """Iterate chars yielding (index, char, is_quoted)."""
    in_q = False
    i = start
    while i < len(line):
        ch = line[i]
        if ch == _DQUOTE:
            yield (i, ch, in_q)
            in_q = not in_q
        elif ch == _BACKSLASH and i + 1 < len(line) and in_q:
            yield (i, ch, True)
            i += 1
            if i < len(line):
                yield (i, line[i], True)
        else:
            yield (i, ch, in_q)
        i += 1


def _find_unquoted(line: str, target: str, start: int = 0) -> int:
    """Find first unquoted occurrence of *target* char, or -1."""
    for i, ch, is_q in _iter_unquoted(line, start):
        if ch == target and not is_q:
            return i
    return -1


def _find_first_unquoted(
    line: str, chars: list[str], start: int = 0
) -> tuple[int, str]:
    """Find first unquoted occurrence of any char in *chars*."""
    s = set(chars)
    for i, ch, is_q in _iter_unquoted(line, start):
        if ch in s and not is_q:
            return (i, ch)
    return (-1, "")


def _parse_delimited(line: str, delimiter: str) -> list[str]:
    """Split *line* on unquoted *delimiter*, respecting quotes."""
    tokens: list[str] = []
    cur: list[str] = []
    for _i, ch, is_q in _iter_unquoted(line):
        if ch == delimiter and not is_q:
            tokens.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if cur or tokens:
        tokens.append("".join(cur))
    return tokens


# ── Validation helpers ────────────────────────────────────────────────────────


def _is_bool_or_null(token: str) -> bool:
    return token in ("true", "false", "null")


def _is_numeric_literal(token: str) -> bool:
    if not token:
        return False
    start = 1 if token.startswith("-") else 0
    if start >= len(token):
        return False
    if len(token) > start + 1 and token[start] == "0" and token[start + 1] != ".":
        return False
    try:
        n = float(token)
        return math.isfinite(n)
    except ValueError:
        return False


def _is_numeric_like(value: str) -> bool:
    return bool(_NUMERIC_RE.match(value) or _OCTAL_RE.match(value))


def _valid_unquoted_key(key: str) -> bool:
    return bool(key and _VALID_KEY_RE.match(key))


def _safe_unquoted(value: str, delimiter: str = _COMMA) -> bool:
    """Check if string can be encoded without quotes."""
    if not value or value != value.strip():
        return False
    if _is_bool_or_null(value) or _is_numeric_like(value):
        return False
    if ":" in value or '"' in value or "\\" in value:
        return False
    if re.search(r"[\[\]{}]", value):
        return False
    if re.search(r"[\n\r\t]", value):
        return False
    if delimiter in value:
        return False
    if value.startswith("-"):
        return False
    return True


# ── Type guards ───────────────────────────────────────────────────────────────


def _is_primitive(value: Any) -> TypeGuard[JsonPrimitive]:
    return value is None or isinstance(value, (str, int, float, bool))


def _is_array(value: Any) -> TypeGuard[JsonArray]:
    return isinstance(value, list)


def _is_object(value: Any) -> TypeGuard[JsonObject]:
    return isinstance(value, dict)


def _all_primitives(arr: list[Any]) -> bool:
    return all(_is_primitive(x) for x in arr)


def _all_arrays(arr: list[Any]) -> bool:
    return all(_is_array(x) for x in arr)


def _all_objects(arr: list[Any]) -> bool:
    return all(_is_object(x) for x in arr)


# ── Value normalization ───────────────────────────────────────────────────────


def _normalize(value: Any) -> JsonValue:
    """Normalize Python value to JSON-compatible type."""
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        if value == 0.0 and math.copysign(1.0, value) == -1.0:
            return 0
        return value
    if isinstance(value, Decimal):
        return None if not value.is_finite() else float(value)
    if isinstance(value, PurePath):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [_normalize(x) for x in value]
    if isinstance(value, tuple):
        return [_normalize(x) for x in value]
    if isinstance(value, (set, frozenset)):
        try:
            return [_normalize(x) for x in sorted(value)]
        except TypeError:
            return [_normalize(x) for x in sorted(value, key=repr)]
    if isinstance(value, Mapping):
        return {str(k): _normalize(v) for k, v in value.items()}
    if callable(value):
        return None
    return None


# ── Line writer ───────────────────────────────────────────────────────────────


class _Writer:
    __slots__ = ("_lines", "_indent_str", "_cache")

    def __init__(self, indent: int) -> None:
        self._lines: list[str] = []
        self._indent_str = " " * max(indent, 1)
        self._cache: dict[int, str] = {0: ""}

    def push(self, depth: int, content: str) -> None:
        if depth not in self._cache:
            self._cache[depth] = self._indent_str * depth
        self._lines.append(self._cache[depth] + content)

    def to_string(self) -> str:
        return "\n".join(self._lines)


# ── Encoding primitives ──────────────────────────────────────────────────────


def _encode_string(value: str, delimiter: str = _COMMA) -> str:
    if _safe_unquoted(value, delimiter):
        return value
    return f'"{_escape(value)}"'


def _encode_primitive(value: JsonPrimitive, delimiter: str = _COMMA) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        s = str(value)
        if "e" in s or "E" in s:
            s = format(Decimal(str(value)), "f")
        return s
    return _encode_string(value, delimiter)


def _encode_key(key: str) -> str:
    if _valid_unquoted_key(key):
        return key
    return f'"{_escape(key)}"'


def _join_values(values: list[str], delimiter: str) -> str:
    return delimiter.join(values)


def _format_header(
    key: str | None,
    length: int,
    fields: list[str] | None,
    delimiter: str,
    length_marker: str | Literal[False],
) -> str:
    marker = length_marker if length_marker else ""
    fields_str = ""
    if fields:
        encoded = [_encode_key(f) for f in fields]
        fields_str = "{" + delimiter.join(encoded) + "}"
    if delimiter != _COMMA:
        length_str = f"[{marker}{length}{delimiter}]"
    else:
        length_str = f"[{marker}{length}]"
    if key:
        return f"{_encode_key(key)}{length_str}{fields_str}:"
    return f"{length_str}{fields_str}:"


# ── Encoder ───────────────────────────────────────────────────────────────────


class _ResolvedOpts:
    __slots__ = ("indent", "delimiter", "length_marker")

    def __init__(
        self,
        indent: int = 2,
        delimiter: str = ",",
        length_marker: str | Literal[False] = False,
    ):
        self.indent = indent
        self.delimiter = delimiter
        self.length_marker = length_marker


def _resolve_encode_opts(options: EncodeOptions | None) -> _ResolvedOpts:
    if options is None:
        return _ResolvedOpts()
    indent = options.get("indent", 2)
    delim = options.get("delimiter", _COMMA)
    lm = options.get("lengthMarker", False)
    if delim in _DELIMITERS:
        delim = _DELIMITERS[delim]
    return _ResolvedOpts(indent=indent, delimiter=delim, length_marker=lm)


def _detect_tabular(arr: list[JsonObject], delimiter: str) -> list[str] | None:
    """Return field keys if *arr* qualifies for tabular format, else None."""
    if not arr:
        return None
    first_keys = list(arr[0].keys())
    first_set = set(first_keys)
    for obj in arr:
        if set(obj.keys()) != first_set:
            return None
        if not all(_is_primitive(v) for v in obj.values()):
            return None
    return first_keys


def _enc_value(value: JsonValue, opts: _ResolvedOpts, w: _Writer, depth: int) -> None:
    if _is_primitive(value):
        w.push(depth, _encode_primitive(value, opts.delimiter))
    elif _is_array(value):
        _enc_array(value, opts, w, depth, None)
    elif _is_object(value):
        _enc_object(value, opts, w, depth, None)


def _enc_object(
    obj: JsonObject, opts: _ResolvedOpts, w: _Writer, depth: int, key: str | None
) -> None:
    if key:
        w.push(depth, f"{_encode_key(key)}:")
    for k, v in obj.items():
        _enc_kv(k, v, opts, w, depth if not key else depth + 1)


def _enc_kv(
    key: str, value: JsonValue, opts: _ResolvedOpts, w: _Writer, depth: int
) -> None:
    if _is_primitive(value):
        w.push(depth, f"{_encode_key(key)}: {_encode_primitive(value, opts.delimiter)}")
    elif _is_array(value):
        _enc_array(value, opts, w, depth, key)
    elif _is_object(value):
        _enc_object(value, opts, w, depth, key)


def _enc_array(
    arr: JsonArray, opts: _ResolvedOpts, w: _Writer, depth: int, key: str | None
) -> None:
    if not arr:
        header = _format_header(key, 0, None, opts.delimiter, opts.length_marker)
        w.push(depth, header)
        return
    if _all_primitives(arr):
        _enc_inline_prim(arr, opts, w, depth, key)
    elif _all_arrays(arr):
        _enc_array_of_arrays(arr, opts, w, depth, key)
    elif _all_objects(arr):
        fields = _detect_tabular(arr, opts.delimiter)
        if fields:
            _enc_tabular(arr, fields, opts, w, depth, key)
        else:
            _enc_list_items(arr, opts, w, depth, key)
    else:
        _enc_list_items(arr, opts, w, depth, key)


def _enc_inline_prim(
    arr: JsonArray, opts: _ResolvedOpts, w: _Writer, depth: int, key: str | None
) -> None:
    encoded = [_encode_primitive(x, opts.delimiter) for x in arr]
    joined = _join_values(encoded, opts.delimiter)
    header = _format_header(key, len(arr), None, opts.delimiter, opts.length_marker)
    w.push(depth, f"{header} {joined}")


def _enc_array_of_arrays(
    arr: JsonArray, opts: _ResolvedOpts, w: _Writer, depth: int, key: str | None
) -> None:
    header = _format_header(key, len(arr), None, opts.delimiter, opts.length_marker)
    w.push(depth, header)
    for item in arr:
        if _all_primitives(item):
            encoded = [_encode_primitive(v, opts.delimiter) for v in item]
            joined = _join_values(encoded, opts.delimiter)
            ih = _format_header(
                None, len(item), None, opts.delimiter, opts.length_marker
            )
            line = f"- {ih}"
            if joined:
                line += f" {joined}"
            w.push(depth + 1, line)
        else:
            _enc_array(item, opts, w, depth + 1, None)


def _enc_tabular(
    arr: list[JsonObject],
    fields: list[str],
    opts: _ResolvedOpts,
    w: _Writer,
    depth: int,
    key: str | None,
) -> None:
    header = _format_header(key, len(arr), fields, opts.delimiter, opts.length_marker)
    w.push(depth, header)
    for obj in arr:
        row = [_encode_primitive(obj[f], opts.delimiter) for f in fields]
        w.push(depth + 1, _join_values(row, opts.delimiter))


def _enc_list_items(
    arr: JsonArray, opts: _ResolvedOpts, w: _Writer, depth: int, key: str | None
) -> None:
    header = _format_header(key, len(arr), None, opts.delimiter, opts.length_marker)
    w.push(depth, header)
    for item in arr:
        if _is_primitive(item):
            w.push(depth + 1, f"- {_encode_primitive(item, opts.delimiter)}")
        elif _is_object(item):
            _enc_obj_list_item(item, opts, w, depth + 1)
        elif _is_array(item):
            sub = item
            if _all_primitives(sub):
                encoded = [_encode_primitive(v, opts.delimiter) for v in sub]
                joined = _join_values(encoded, opts.delimiter)
                ih = _format_header(
                    None, len(sub), None, opts.delimiter, opts.length_marker
                )
                line = f"- {ih}"
                if joined:
                    line += f" {joined}"
                w.push(depth + 1, line)
            else:
                tf = None
                if _all_objects(sub):
                    tf = _detect_tabular(sub, opts.delimiter)
                ih = _format_header(
                    None, len(sub), tf, opts.delimiter, opts.length_marker
                )
                w.push(depth + 1, f"- {ih}")
                _enc_array_content(sub, opts, w, depth + 2)


def _enc_obj_list_item(
    obj: JsonObject, opts: _ResolvedOpts, w: _Writer, depth: int
) -> None:
    items = list(obj.items())
    if not items:
        w.push(depth, "-")
        return
    k0, v0 = items[0]
    if _is_primitive(v0):
        w.push(depth, f"- {_encode_key(k0)}: {_encode_primitive(v0, opts.delimiter)}")
    elif _is_array(v0):
        sub = v0
        if _all_primitives(sub):
            encoded = [_encode_primitive(x, opts.delimiter) for x in sub]
            joined = _join_values(encoded, opts.delimiter)
            ih = _format_header(k0, len(sub), None, opts.delimiter, opts.length_marker)
            line = f"- {ih}"
            if joined:
                line += f" {joined}"
            w.push(depth, line)
        else:
            tf = None
            if _all_objects(sub):
                tf = _detect_tabular(sub, opts.delimiter)
            ih = _format_header(k0, len(sub), tf, opts.delimiter, opts.length_marker)
            w.push(depth, f"- {ih}")
            _enc_array_content(sub, opts, w, depth + 1)
    else:
        w.push(depth, "-")
        _enc_kv(k0, v0, opts, w, depth + 1)
    for k, v in items[1:]:
        _enc_kv(k, v, opts, w, depth + 1)


def _enc_array_content(
    arr: JsonArray, opts: _ResolvedOpts, w: _Writer, depth: int
) -> None:
    """Write array body (header already written)."""
    if not arr:
        return
    if _all_objects(arr):
        fields = _detect_tabular(arr, opts.delimiter)
        if fields:
            for obj in arr:
                row = [_encode_primitive(obj[f], opts.delimiter) for f in fields]
                w.push(depth, _join_values(row, opts.delimiter))
            return
        for item in arr:
            _enc_obj_list_item(item, opts, w, depth)
        return
    for item in arr:
        if _is_primitive(item):
            w.push(depth, f"- {_encode_primitive(item, opts.delimiter)}")
        elif _is_object(item):
            _enc_obj_list_item(item, opts, w, depth)
        elif _is_array(item):
            _enc_array(item, opts, w, depth, None)


# ── Scanner ───────────────────────────────────────────────────────────────────


@dataclass
class _Line:
    raw: str
    depth: int
    indent: int
    content: str
    line_num: int

    @property
    def is_blank(self) -> bool:
        return not self.content.strip()


def _scan(source: str, indent_size: int, strict: bool) -> list[_Line]:
    """Scan source text into structured lines with depth info."""
    if not source.strip():
        return []
    lines: list[_Line] = []
    for i, raw in enumerate(source.split("\n")):
        num = i + 1
        indent = 0
        while indent < len(raw) and raw[indent] == " ":
            indent += 1
        content = raw[indent:]
        depth = indent // indent_size if indent_size > 0 else 0
        is_blank = not content.strip()
        if strict and not is_blank:
            ws_end = 0
            while ws_end < len(raw) and raw[ws_end] in (" ", "\t"):
                ws_end += 1
            if "\t" in raw[:ws_end]:
                raise ToonDecodeError(f"Line {num}: Tabs not allowed in indentation")
            if indent > 0 and indent % indent_size != 0:
                raise ToonDecodeError(
                    f"Line {num}: Indent must be multiple of "
                    f"{indent_size}, got {indent}"
                )
        lines.append(
            _Line(
                raw=raw,
                depth=depth,
                indent=indent,
                content=content.strip(),
                line_num=num,
            )
        )
    return lines


# ── Decoder ───────────────────────────────────────────────────────────────────


def _parse_primitive(token: str) -> JsonValue:
    """Parse a TOON primitive token."""
    token = token.strip()
    if token.startswith(_DQUOTE):
        if not token.endswith(_DQUOTE) or len(token) < 2:
            raise ToonDecodeError("Unterminated string")
        return _unescape(token[1:-1])
    if _is_bool_or_null(token):
        if token == "true":
            return True
        if token == "false":
            return False
        return None
    if token and _is_numeric_literal(token):
        try:
            if "." not in token and "e" not in token.lower():
                return int(token)
            return float(token)
        except ValueError:
            pass
    return token


def _parse_key(key_str: str) -> str:
    key_str = key_str.strip()
    if key_str.startswith(_DQUOTE):
        if not key_str.endswith(_DQUOTE) or len(key_str) < 2:
            raise ToonDecodeError("Unterminated quoted key")
        return _unescape(key_str[1:-1])
    return key_str


def _split_kv(line: str) -> tuple[str, str]:
    idx = _find_unquoted(line, _COLON)
    if idx == -1:
        raise ToonDecodeError("Missing colon after key")
    return (line[:idx].strip(), line[idx + 1 :].strip())


def _parse_header(line: str) -> tuple[str | None, int, str, list[str] | None] | None:
    """Parse array header. Returns (key, length, delimiter, fields) or None."""
    line = line.strip()
    bstart = _find_unquoted(line, "[")
    if bstart == -1:
        return None
    key = None
    if bstart > 0:
        kp = line[:bstart].strip()
        key = _parse_key(kp) if kp else None
    bend = _find_unquoted(line, "]", bstart)
    if bend == -1:
        return None
    bc = line[bstart + 1 : bend]
    if bc.startswith("#"):
        bc = bc[1:]
    delimiter = _COMMA
    length_str = bc
    if bc.endswith(_TAB):
        delimiter = _TAB
        length_str = bc[:-1]
    elif bc.endswith(_PIPE):
        delimiter = _PIPE
        length_str = bc[:-1]
    elif bc.endswith(_COMMA):
        delimiter = _COMMA
        length_str = bc[:-1]
    try:
        length = int(length_str)
    except ValueError:
        return None
    fields = None
    after = line[bend + 1 :].strip()
    if after.startswith("{"):
        brace_end = _find_unquoted(after, "}")
        if brace_end == -1:
            raise ToonDecodeError("Unterminated fields segment")
        fc = after[1:brace_end]
        ft = _parse_delimited(fc, delimiter)
        fields = [_parse_key(f.strip()) for f in ft]
        after = after[brace_end + 1 :].strip()
    if not after.startswith(_COLON):
        return None
    return (key, length, delimiter, fields)


def _is_row_line(line: str, delimiter: str) -> bool:
    pos, ch = _find_first_unquoted(line, [delimiter, _COLON])
    if pos == -1:
        return True
    return ch == delimiter


def _dec_object(
    lines: list[_Line], start: int, parent_depth: int, strict: bool
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    i = start
    expected = parent_depth if start == 0 else parent_depth + 1
    while i < len(lines):
        ln = lines[i]
        if ln.is_blank:
            i += 1
            continue
        if ln.depth < expected:
            break
        if ln.depth > expected:
            i += 1
            continue
        hdr = _parse_header(ln.content)
        if hdr is not None and hdr[0] is not None:
            arr_val, next_i = _dec_array_from_hdr(lines, i, ln.depth, hdr, strict)
            result[hdr[0]] = arr_val
            i = next_i
            continue
        try:
            ks, vs = _split_kv(ln.content)
        except ToonDecodeError:
            if strict:
                raise
            i += 1
            continue
        key = _parse_key(ks)
        if not vs:
            result[key] = _dec_object(lines, i + 1, ln.depth, strict)
            i += 1
            while i < len(lines) and lines[i].depth > ln.depth:
                i += 1
        else:
            result[key] = _parse_primitive(vs)
            i += 1
    return result


def _dec_array_from_hdr(
    lines: list[_Line],
    hdr_idx: int,
    hdr_depth: int,
    hdr_info: tuple[str | None, int, str, list[str] | None],
    strict: bool,
) -> tuple[list[Any], int]:
    key, length, delimiter, fields = hdr_info
    hdr_line = lines[hdr_idx].content
    try:
        _, inline = _split_kv(hdr_line)
    except ToonDecodeError:
        inline = ""
    if inline or (not fields and length == 0):
        return (_dec_inline_array(inline, delimiter, length, strict), hdr_idx + 1)
    if fields is not None:
        return _dec_tabular(
            lines, hdr_idx + 1, hdr_depth, fields, delimiter, length, strict
        )
    return _dec_list_array(lines, hdr_idx + 1, hdr_depth, delimiter, length, strict)


def _dec_inline_array(
    content: str, delimiter: str, expected: int, strict: bool
) -> list[Any]:
    if not content and expected == 0:
        return []
    tokens = _parse_delimited(content, delimiter)
    values = [_parse_primitive(t) for t in tokens]
    if strict and len(values) != expected:
        raise ToonDecodeError(f"Expected {expected} values, got {len(values)}")
    return values


def _dec_tabular(
    lines: list[_Line],
    start: int,
    hdr_depth: int,
    fields: list[str],
    delimiter: str,
    expected: int,
    strict: bool,
) -> tuple[list[dict[str, Any]], int]:
    result: list[dict[str, Any]] = []
    i = start
    row_depth = hdr_depth + 1
    while i < len(lines):
        ln = lines[i]
        if ln.is_blank:
            if strict:
                if ln.depth >= row_depth:
                    raise ToonDecodeError("Blank lines not allowed inside arrays")
                break
            i += 1
            continue
        if ln.depth < row_depth or ln.depth > row_depth:
            break
        if not _is_row_line(ln.content, delimiter):
            break
        tokens = _parse_delimited(ln.content, delimiter)
        values = [_parse_primitive(t) for t in tokens]
        if strict and len(values) != len(fields):
            raise ToonDecodeError(
                f"Expected {len(fields)} values in row, got {len(values)}"
            )
        obj = {fields[j]: values[j] for j in range(min(len(fields), len(values)))}
        result.append(obj)
        i += 1
    if strict and len(result) != expected:
        raise ToonDecodeError(f"Expected {expected} rows, got {len(result)}")
    return result, i


def _dec_list_array(
    lines: list[_Line],
    start: int,
    hdr_depth: int,
    delimiter: str,
    expected: int,
    strict: bool,
) -> tuple[list[Any], int]:
    result: list[Any] = []
    i = start
    item_depth = hdr_depth + 1
    while i < len(lines):
        ln = lines[i]
        if ln.is_blank:
            if strict:
                if ln.depth >= item_depth:
                    raise ToonDecodeError("Blank lines not allowed inside arrays")
                break
            i += 1
            continue
        if ln.depth < item_depth:
            break
        content = ln.content
        if not content.startswith("-"):
            break
        ic = content[2:].strip() if len(content) > 2 else ""
        ih = _parse_header(ic)
        if ih is not None:
            ikey, ilen, idelim, ifields = ih
            if ikey is None:
                ci = ic.find(_COLON)
                if ci != -1:
                    ip = ic[ci + 1 :].strip()
                    if ip or ilen == 0:
                        result.append(_dec_inline_array(ip, idelim, ilen, strict))
                        i += 1
                        continue
            else:
                item_obj: dict[str, Any] = {}
                arr_val, next_i = _dec_array_from_hdr(lines, i, ln.depth, ih, strict)
                item_obj[ikey] = arr_val
                i = next_i
                while i < len(lines) and lines[i].depth == ln.depth + 1:
                    fl = lines[i]
                    if fl.is_blank:
                        i += 1
                        continue
                    fh = _parse_header(fl.content)
                    if fh is not None and fh[0] is not None:
                        fv, ni = _dec_array_from_hdr(lines, i, fl.depth, fh, strict)
                        item_obj[fh[0]] = fv
                        i = ni
                        continue
                    try:
                        fks, fvs = _split_kv(fl.content)
                        fk = _parse_key(fks)
                        if not fvs:
                            item_obj[fk] = _dec_object(lines, i + 1, fl.depth, strict)
                            i += 1
                            while i < len(lines) and lines[i].depth > fl.depth:
                                i += 1
                        else:
                            item_obj[fk] = _parse_primitive(fvs)
                            i += 1
                    except ToonDecodeError:
                        break
                result.append(item_obj)
                continue
        try:
            ks, vs = _split_kv(ic)
            obj_item: dict[str, Any] = {}
            key = _parse_key(ks)
            if not vs:
                nested = _dec_object(lines, i + 1, ln.depth + 1, strict)
                obj_item[key] = nested
                i += 1
                while i < len(lines) and lines[i].depth > ln.depth + 1:
                    i += 1
            else:
                obj_item[key] = _parse_primitive(vs)
                i += 1
            while i < len(lines) and lines[i].depth == ln.depth + 1:
                fl = lines[i]
                if fl.is_blank:
                    i += 1
                    continue
                fh = _parse_header(fl.content)
                if fh is not None and fh[0] is not None:
                    fv, ni = _dec_array_from_hdr(lines, i, fl.depth, fh, strict)
                    obj_item[fh[0]] = fv
                    i = ni
                    continue
                try:
                    fks, fvs = _split_kv(fl.content)
                    fk = _parse_key(fks)
                    if not fvs:
                        obj_item[fk] = _dec_object(lines, i + 1, fl.depth, strict)
                        i += 1
                        while i < len(lines) and lines[i].depth > fl.depth:
                            i += 1
                    else:
                        obj_item[fk] = _parse_primitive(fvs)
                        i += 1
                except ToonDecodeError:
                    break
            result.append(obj_item)
        except ToonDecodeError:
            if not ic:
                result.append({})
            else:
                result.append(_parse_primitive(ic))
            i += 1
    if strict and len(result) != expected:
        raise ToonDecodeError(f"Expected {expected} items, got {len(result)}")
    return result, i


# ── Public API ────────────────────────────────────────────────────────────────


def encode(value: Any, options: EncodeOptions | None = None) -> str:
    """Encode a Python value into TOON format.

    Args:
        value: The value to encode (must be JSON-serializable or a supported
            Python type such as datetime, Decimal, set, Path).
        options: Optional encoding options (indent, delimiter, lengthMarker).

    Returns:
        TOON-formatted string.

    Examples::

        encode({"name": "Alice", "age": 30})
        # 'name: Alice\nage: 30'
        encode([{"id": 1, "name": "A"}, {"id": 2, "name": "B"}])
        # '[2,]{id,name}:\n  1,A\n  2,B'
    """
    normalized = _normalize(value)
    opts = _resolve_encode_opts(options)
    w = _Writer(opts.indent)
    _enc_value(normalized, opts, w, 0)
    return w.to_string()


def decode(text: str, options: DecodeOptions | None = None) -> Any:
    """Decode a TOON-formatted string to a Python value.

    Args:
        text: TOON-formatted string.
        options: Optional decoding options (indent, strict).

    Returns:
        Decoded Python value.

    Raises:
        ToonDecodeError: If the input is malformed.

    Examples::

        decode("name: Alice\nage: 30")
        # {'name': 'Alice', 'age': 30}
        decode("[3]: 1,2,3")
        # [1, 2, 3]
    """
    indent = 2
    strict = True
    if options is not None:
        indent = options.get("indent", 2)
        strict = options.get("strict", True)
    try:
        lines = _scan(text, indent, strict)
    except ToonDecodeError:
        raise
    non_blank = [ln for ln in lines if not ln.is_blank]
    if not non_blank:
        return {}
    first = non_blank[0]
    hdr = _parse_header(first.content)
    if hdr is not None and hdr[0] is None:
        arr, _ = _dec_array_from_hdr(
            lines, 0 if lines[0] == first else lines.index(first), 0, hdr, strict
        )
        return arr
    if len(non_blank) == 1:
        try:
            _split_kv(first.content)
        except ToonDecodeError:
            if hdr is None:
                return _parse_primitive(first.content)
    return _dec_object(lines, 0, 0, strict)
