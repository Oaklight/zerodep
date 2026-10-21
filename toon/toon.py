# /// zerodep
# version = "0.5.0"
# deps = []
# tier = "simple"
# category = "serialization"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///

"""TOON encoder/decoder — zero dependencies, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Targets the TOON 4.x encoding against the official spec 4.4 conformance
fixtures vendored in ``toon/fixtures/spec/``. It is not yet a full drop-in
replacement for ``toon_format``: the remaining conformance gaps are tracked
section by section in https://github.com/Oaklight/zerodep/issues/184, and
``toon/test_toon_conformance.py`` records the current pass level as a ratchet
so it can only move up.

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

__all__ = [
    # Type aliases
    "JsonPrimitive",
    "JsonObject",
    "JsonArray",
    "JsonValue",
    # Options
    "EncodeOptions",
    "DecodeOptions",
    # Exceptions
    "ToonDecodeError",
    # Public API
    "encode",
    "decode",
]

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
                raise ToonDecodeError("Backslash at end of string")
            nxt = value[i + 1]
            if nxt not in _MAP:
                raise ToonDecodeError(f"Invalid escape sequence: \\{nxt}")
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


def _normalize_float(value: float | Decimal) -> JsonValue:
    """Normalize a float or Decimal to a JSON-compatible value."""
    if isinstance(value, Decimal):
        return None if not value.is_finite() else float(value)
    if not math.isfinite(value):
        return None
    if value == 0.0 and math.copysign(1.0, value) == -1.0:
        return 0
    return value


def _normalize_collection(value: list | tuple | set | frozenset) -> list:
    """Normalize a sequence or set to a JSON-compatible list."""
    if isinstance(value, (set, frozenset)):
        try:
            return [_normalize(x) for x in sorted(value)]
        except TypeError:
            return [_normalize(x) for x in sorted(value, key=repr)]
    return [_normalize(x) for x in value]


def _normalize(value: Any) -> JsonValue:
    """Normalize Python value to JSON-compatible type."""
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, (float, Decimal)):
        return _normalize_float(value)
    if isinstance(value, PurePath):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (list, tuple, set, frozenset)):
        return _normalize_collection(value)
    if isinstance(value, Mapping):
        return {str(k): _normalize(v) for k, v in value.items()}
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
    fields: str | None,
    delimiter: str,
    length_marker: str | Literal[False],
) -> str:
    marker = length_marker if length_marker else ""
    fields_str = fields or ""
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


# A (possibly nested) tabular column tree: ``(key, None)`` is a leaf column
# holding a primitive; ``(key, subtree)`` is a nested column.
_FieldTree = list[tuple[str, "_FieldTree | None"]]


def _detect_fields(arr: list[JsonObject]) -> _FieldTree | None:
    """Return the field tree if *arr* qualifies for tabular format, else None.

    Every object must carry the same keys, and each key must hold a primitive
    in all rows (a leaf column) or a sub-object in all rows that itself
    qualifies (a nested column, rendered as ``d{x}``).  Anything else -- an
    array value, mixed kinds, ragged keys, an empty object -- disqualifies the
    whole array, which then falls back to the list form.
    """
    if not arr:
        return None
    first_keys = list(arr[0].keys())
    if not first_keys:
        return None
    first_set = set(first_keys)
    for obj in arr:
        if set(obj.keys()) != first_set:
            return None
    nodes: _FieldTree = []
    for key in first_keys:
        values = [obj[key] for obj in arr]
        if all(_is_primitive(v) for v in values):
            nodes.append((key, None))
        elif all(_is_object(v) for v in values):
            sub = _detect_fields(values)
            if sub is None:
                return None
            nodes.append((key, sub))
        else:
            return None
    return nodes


def _render_fields(nodes: _FieldTree, delimiter: str) -> str:
    """Render a field tree as a header segment, e.g. ``{n,d{x}}``."""
    parts: list[str] = []
    for key, sub in nodes:
        parts.append(_encode_key(key))
        if sub is not None:
            parts[-1] += _render_fields(sub, delimiter)
    return "{" + delimiter.join(parts) + "}"


def _leaf_paths(nodes: _FieldTree) -> list[tuple[str, ...]]:
    """Return the leaf column paths of a field tree, in row order."""
    paths: list[tuple[str, ...]] = []
    for key, sub in nodes:
        if sub is None:
            paths.append((key,))
        else:
            paths.extend((key,) + rest for rest in _leaf_paths(sub))
    return paths


def _row_values(obj: JsonObject, nodes: _FieldTree, delimiter: str) -> list[str]:
    """Flatten one object into the encoded row cells described by *nodes*."""
    cells: list[str] = []
    for key, sub in nodes:
        value = obj[key]
        if sub is None:
            cells.append(_encode_primitive(value, delimiter))
            continue
        if not isinstance(value, dict):
            # _detect_fields only marks a column nested when every row holds an
            # object there, so this is an internal invariant.  Raise rather
            # than assert, so it survives -O.
            raise ValueError(
                f"Column {key!r} is marked nested but holds "
                f"{type(value).__name__} on this row"
            )
        cells.extend(_row_values(value, sub, delimiter))
    return cells


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
        w.push(depth, f"{_encode_key(key)}: []" if key is not None else "[]")
        return
    if _all_primitives(arr):
        _enc_inline_prim(arr, opts, w, depth, key)
    elif _all_arrays(arr):
        _enc_array_of_arrays(arr, opts, w, depth, key)
    elif _all_objects(arr):
        fields = _detect_fields(arr)
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
    fields: _FieldTree,
    opts: _ResolvedOpts,
    w: _Writer,
    depth: int,
    key: str | None,
) -> None:
    header = _format_header(
        key,
        len(arr),
        _render_fields(fields, opts.delimiter),
        opts.delimiter,
        opts.length_marker,
    )
    w.push(depth, header)
    for obj in arr:
        row = _row_values(obj, fields, opts.delimiter)
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
                    detected = _detect_fields(sub)
                    if detected:
                        tf = _render_fields(detected, opts.delimiter)
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
        if not sub:
            # §9.1: an empty array in object-field position is ``key: []``;
            # the legacy ``key[0]:`` header MUST NOT be emitted.
            w.push(depth, f"- {_encode_key(k0)}: []")
        elif _all_primitives(sub):
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
                detected = _detect_fields(sub)
                if detected:
                    tf = _render_fields(detected, opts.delimiter)
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
        fields = _detect_fields(arr)
        if fields:
            for obj in arr:
                row = _row_values(obj, fields, opts.delimiter)
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


def _validate_indent(raw: str, indent: int, indent_size: int, line_num: int) -> None:
    """Check indentation in strict mode: no tabs, indent is a multiple of size."""
    ws_end = 0
    while ws_end < len(raw) and raw[ws_end] in (" ", "\t"):
        ws_end += 1
    if "\t" in raw[:ws_end]:
        raise ToonDecodeError(f"Line {line_num}: Tabs not allowed in indentation")
    if indent > 0 and indent % indent_size != 0:
        raise ToonDecodeError(
            f"Line {line_num}: Indent must be multiple of {indent_size}, got {indent}"
        )


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
        if strict and content.strip():
            _validate_indent(raw, indent, indent_size, num)
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
    if token == "[]":
        return []
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


def _match_brace(text: str, start: int = 0) -> int:
    """Return the index of the ``}`` matching the ``{`` at *start*, or -1."""
    depth = 0
    quote = ""
    idx = start
    while idx < len(text):
        ch = text[idx]
        if quote:
            if ch == "\\":
                idx += 2
                continue
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return idx
        idx += 1
    return -1


def _parse_fields(text: str, delimiter: str) -> _FieldTree:
    """Parse a ``{...}`` header body into a field tree.

    Understands the nested form (``name,data{x}``) so a decoded header carries
    the column shape needed to rebuild sub-objects from flattened rows.  The
    opening brace is located with the shared quote-aware scan, because a quoted
    key may itself contain a brace (``"a{"{x}`` on the wire).
    """
    tokens: list[str] = []
    current: list[str] = []
    depth = 0
    quote = ""
    idx = 0
    while idx < len(text):
        ch = text[idx]
        if quote:
            current.append(ch)
            if ch == "\\" and idx + 1 < len(text):
                current.append(text[idx + 1])
                idx += 1
            elif ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
            current.append(ch)
        elif ch == "{" or ch == "}":
            depth += 1 if ch == "{" else -1
            current.append(ch)
        elif ch == delimiter and depth == 0:
            tokens.append("".join(current))
            current = []
        else:
            current.append(ch)
        idx += 1
    tokens.append("".join(current))
    nodes: _FieldTree = []
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        brace = _find_unquoted(token, "{")
        if brace != -1 and _match_brace(token, brace) == len(token) - 1:
            nodes.append(
                (
                    _parse_key(token[:brace]),
                    _parse_fields(token[brace + 1 : -1], delimiter),
                )
            )
        else:
            nodes.append((_parse_key(token), None))
    return nodes


def _parse_header(line: str) -> tuple[str | None, int, str, _FieldTree | None] | None:
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
        brace_end = _match_brace(after)
        if brace_end == -1:
            raise ToonDecodeError("Unterminated fields segment")
        fields = _parse_fields(after[1:brace_end], delimiter)
        after = after[brace_end + 1 :].strip()
    if not after.startswith(_COLON):
        return None
    return (key, length, delimiter, fields)


def _is_row_line(line: str, delimiter: str) -> bool:
    pos, ch = _find_first_unquoted(line, [delimiter, _COLON])
    if pos == -1:
        return True
    return ch == delimiter


def _dec_kv_value(
    lines: list[_Line], i: int, ln: _Line, vs: str, strict: bool
) -> tuple[Any, int]:
    """Decode the value side of a key-value pair, returning (value, next_index)."""
    if vs:
        return _parse_primitive(vs), i + 1
    # Empty value → nested object; skip children after decoding
    child = _dec_object(lines, i + 1, ln.depth, strict)
    j = i + 1
    while j < len(lines) and lines[j].depth > ln.depth:
        j += 1
    return child, j


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
        result[key], i = _dec_kv_value(lines, i, ln, vs, strict)
    return result


def _dec_array_from_hdr(
    lines: list[_Line],
    hdr_idx: int,
    hdr_depth: int,
    hdr_info: tuple[str | None, int, str, _FieldTree | None],
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


def _assemble_fields(
    nodes: _FieldTree, values: list[JsonValue], pos: int
) -> tuple[dict[str, JsonValue], int]:
    """Rebuild one nested object from a flattened tabular row."""
    obj: dict[str, JsonValue] = {}
    for key, sub in nodes:
        if sub is None:
            obj[key] = values[pos] if pos < len(values) else None
            pos += 1
        else:
            obj[key], pos = _assemble_fields(sub, values, pos)
    return obj, pos


def _dec_tabular(
    lines: list[_Line],
    start: int,
    hdr_depth: int,
    fields: _FieldTree,
    delimiter: str,
    expected: int,
    strict: bool,
) -> tuple[list[dict[str, Any]], int]:
    result: list[dict[str, Any]] = []
    i = start
    row_depth = hdr_depth + 1
    width = len(_leaf_paths(fields))
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
        if strict and len(values) != width:
            raise ToonDecodeError(f"Expected {width} values in row, got {len(values)}")
        obj, _ = _assemble_fields(fields, values, 0)
        result.append(obj)
        i += 1
    if strict and len(result) != expected:
        raise ToonDecodeError(f"Expected {expected} rows, got {len(result)}")
    return result, i


def _dec_sibling_fields(
    lines: list[_Line],
    start: int,
    target_depth: int,
    obj: dict[str, Any],
    strict: bool,
) -> int:
    """Read consecutive sibling key-value lines at *target_depth* into *obj*.

    Returns the index of the first line that is no longer a sibling field.
    """
    i = start
    while i < len(lines) and lines[i].depth == target_depth:
        fl = lines[i]
        if fl.is_blank:
            i += 1
            continue
        fh = _parse_header(fl.content)
        if fh is not None and fh[0] is not None:
            fv, i = _dec_array_from_hdr(lines, i, fl.depth, fh, strict)
            obj[fh[0]] = fv
            continue
        try:
            fks, fvs = _split_kv(fl.content)
        except ToonDecodeError:
            break
        fk = _parse_key(fks)
        if not fvs:
            obj[fk] = _dec_object(lines, i + 1, fl.depth, strict)
            i += 1
            while i < len(lines) and lines[i].depth > fl.depth:
                i += 1
        else:
            obj[fk] = _parse_primitive(fvs)
            i += 1
    return i


def _dec_list_item_named_array(
    lines: list[_Line],
    idx: int,
    ln: _Line,
    hdr_info: tuple[str | None, int, str, _FieldTree | None],
    strict: bool,
) -> tuple[dict[str, Any], int]:
    """Decode a list item whose content starts with a named array header.

    Returns the decoded object and the next line index.
    """
    item_obj: dict[str, Any] = {}
    arr_val, next_i = _dec_array_from_hdr(lines, idx, ln.depth, hdr_info, strict)
    item_obj[hdr_info[0]] = arr_val  # type: ignore[index]
    next_i = _dec_sibling_fields(lines, next_i, ln.depth + 1, item_obj, strict)
    return item_obj, next_i


def _dec_list_item_object(
    lines: list[_Line],
    idx: int,
    ln: _Line,
    ic: str,
    strict: bool,
) -> tuple[dict[str, Any], int]:
    """Decode a list item whose content is a key-value pair.

    Returns the decoded object and the next line index.
    """
    ks, vs = _split_kv(ic)
    obj_item: dict[str, Any] = {}
    key = _parse_key(ks)
    if not vs:
        obj_item[key] = _dec_object(lines, idx + 1, ln.depth + 1, strict)
        i = idx + 1
        while i < len(lines) and lines[i].depth > ln.depth + 1:
            i += 1
    else:
        obj_item[key] = _parse_primitive(vs)
        i = idx + 1
    i = _dec_sibling_fields(lines, i, ln.depth + 1, obj_item, strict)
    return obj_item, i


def _try_inline_subarray(
    ic: str,
    hdr_info: tuple[str | None, int, str, _FieldTree | None],
    strict: bool,
) -> list[Any] | None:
    """Try to decode an inline sub-array from a keyless header.

    Returns the decoded list if the header has no key and contains inline data,
    otherwise returns None.
    """
    ikey, ilen, idelim, _ifields = hdr_info
    if ikey is not None:
        return None
    ci = ic.find(_COLON)
    if ci == -1:
        return None
    ip = ic[ci + 1 :].strip()
    if not ip and ilen != 0:
        return None
    return _dec_inline_array(ip, idelim, ilen, strict)


def _dec_one_list_item(
    lines: list[_Line],
    idx: int,
    ln: _Line,
    ic: str,
    strict: bool,
) -> tuple[Any, int]:
    """Decode a single ``- ...`` list item.

    Returns (decoded_value, next_line_index).
    """
    ih = _parse_header(ic)
    if ih is not None:
        inline = _try_inline_subarray(ic, ih, strict)
        if inline is not None:
            return inline, idx + 1
        if ih[0] is not None:
            return _dec_list_item_named_array(lines, idx, ln, ih, strict)
    try:
        return _dec_list_item_object(lines, idx, ln, ic, strict)
    except ToonDecodeError:
        return ({} if not ic else _parse_primitive(ic)), idx + 1


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
            if strict and ln.depth >= item_depth:
                raise ToonDecodeError("Blank lines not allowed inside arrays")
            if strict:
                break
            i += 1
            continue
        if ln.depth < item_depth:
            break
        content = ln.content
        if not content.startswith("-"):
            break
        ic = content[2:].strip() if len(content) > 2 else ""
        item, i = _dec_one_list_item(lines, i, ln, ic, strict)
        result.append(item)
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
