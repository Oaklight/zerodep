# /// zerodep
# version = "0.6.1"
# deps = []
# tier = "simple"
# category = "serialization"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///

"""TOON encoder/decoder — zero dependencies, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Implements the TOON 4.4 specification. The official conformance fixtures
(564 cases: 160 encode, 404 decode) are vendored in ``toon/fixtures/spec/``
and gated by ``toon/test_toon_conformance.py``.

The encoder and decoder follow the TOON reference implementation,
`toon-format/toon-python <https://github.com/toon-format/toon-python>`_
(MIT License, commit ``91413d14``), adapted to this module's single-file,
standard-library-only form and public API.

TOON is a compact, human-readable serialization format designed for LLM
contexts, achieving 30-60% token reduction vs JSON. It combines YAML-like
indentation with CSV-like tabular arrays.

Example::

    encode({"name": "Alice", "age": 30})
    # 'name: Alice\nage: 30'
    decode("name: Alice\nage: 30")
    # {'name': 'Alice', 'age': 30}
"""

from __future__ import annotations

import dataclasses
import math
import re
import sys
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from pathlib import PurePath
from typing import Any, TypeAlias, TypedDict, Union
from uuid import UUID

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

    The pre-4.0 ``lengthMarker`` option was removed by the specification;
    passing it raises :class:`ValueError` so callers notice the change.
    """

    indent: int
    delimiter: str


class DecodeOptions(TypedDict, total=False):
    """Options for TOON decoding.

    Attributes:
        indent: Number of spaces per indentation level (default: 2).
        strict: Enforce every check of specification §14 (default: True).
    """

    indent: int
    strict: bool


class ToonDecodeError(Exception):
    """Error raised when TOON decoding fails.

    Unlike :class:`json.JSONDecodeError`, this is not a :class:`ValueError`
    subclass: ``except ValueError`` does not catch decode failures, so catch
    ``ToonDecodeError`` instead.  This is the module's public contract.

    Attributes:
        msg: The unformatted error message.
        line: 1-based line number of the offending line, or ``None`` when the
            error is not tied to a line.
        source: The offending line as written, or ``None``.
    """

    msg: str
    line: int | None
    source: str | None

    def __init__(
        self, msg: str, line: int | None = None, source: str | None = None
    ) -> None:
        self.msg = msg
        self.line = line
        self.source = source
        super().__init__(f"line {line}: {msg}" if line is not None else msg)

    def __reduce__(
        self,
    ) -> tuple[type[ToonDecodeError], tuple[str, int | None, str | None]]:
        return type(self), (self.msg, self.line, self.source)


# ── Option validation ─────────────────────────────────────────────────────────


def _check_indent_size(indent: int) -> None:
    """Validate the ``indent`` option (§12)."""
    if isinstance(indent, bool) or not isinstance(indent, int):
        raise TypeError(f"indent must be an int, not {type(indent).__name__}")
    if indent < 1:
        raise ValueError(f"indent must be at least 1, got {indent}")


# ── Public API ────────────────────────────────────────────────────────────────


def encode(value: Any, options: EncodeOptions | None = None) -> str:
    """Serialize a Python value to a TOON document.

    Args:
        value: The value to encode. Mappings, sequences, strings, numbers,
            booleans and ``None`` map onto the JSON data model; dates, UUIDs,
            paths, enums and dataclasses are converted following §3.
        options: Optional encoding options (``indent``, ``delimiter``).
            Unknown keys raise :class:`TypeError` rather than being ignored.

    Returns:
        The TOON document, without a trailing newline.

    Raises:
        TypeError: A value or mapping key cannot be encoded, or an unknown
            option was supplied.
        ValueError: An option is invalid, a string contains an unpaired
            surrogate, a mapping has colliding keys, or the value is nested
            too deeply or contains a reference cycle.

    Examples::

        encode({"name": "Alice", "age": 30})
        # 'name: Alice\nage: 30'
        encode([1, 2, 3], EncodeOptions(delimiter="\t"))
        # '[3\t]: 1\t2\t3'
    """
    opts: Any = options or {}
    if opts.get("lengthMarker", False):
        raise ValueError(
            "lengthMarker was removed in TOON 4.4; re-encode without the option"
        )
    unknown = set(opts) - {"indent", "delimiter", "lengthMarker"}
    if unknown:
        names = ", ".join(sorted(repr(name) for name in unknown))
        raise TypeError(f"unknown encode option(s): {names}")
    indent = opts.get("indent", 2)
    delimiter = opts.get("delimiter", ",")
    _check_indent_size(indent)
    if delimiter not in DELIMITERS:
        raise ValueError(f"delimiter must be ',', '\\t', or '|', got {delimiter!r}")
    return _encode_document(
        value,
        indent_size=indent,
        delimiter=delimiter,
        default=None,
        sort_keys=False,
    )


def decode(text: str | bytes | bytearray, options: DecodeOptions | None = None) -> Any:
    """Deserialize a TOON document to a Python value.

    Args:
        text: TOON-formatted string, or UTF-8 encoded bytes.
        options: Optional decoding options (``indent``, ``strict``).
            Unknown keys raise :class:`TypeError` rather than being ignored.

    Returns:
        Decoded Python value.

    Raises:
        ToonDecodeError: If the input is malformed or is not valid UTF-8.
        TypeError: If ``text`` is not str/bytes/bytearray, an option is
            unknown, or ``indent`` is not an int.
        ValueError: If ``indent`` is less than one.

    Examples::

        decode("name: Alice\nage: 30")
        # {'name': 'Alice', 'age': 30}
        decode("[3]: 1,2,3")
        # [1, 2, 3]
    """
    if isinstance(text, (bytes, bytearray)):
        try:
            document = bytes(text).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ToonDecodeError(
                f"Invalid UTF-8: {exc.reason} at byte {exc.start}"
            ) from None
    elif isinstance(text, str):
        document = text
    else:
        raise TypeError(
            f"text must be str, bytes or bytearray, not {type(text).__name__}"
        )
    opts: Any = options or {}
    unknown = set(opts) - {"indent", "strict"}
    if unknown:
        names = ", ".join(sorted(repr(name) for name in unknown))
        raise TypeError(f"unknown decode option(s): {names}")
    indent = opts.get("indent", 2)
    strict = opts.get("strict", True)
    _check_indent_size(indent)
    return _decode_document(
        document,
        indent_size=indent,
        strict=strict,
        parse_int=None,
        parse_float=None,
        object_hook=None,
        object_pairs_hook=None,
    )


# ── Lexical rules (§2, §4, §7) ────────────────────────────────────────────────

COMMA = ","
TAB = "\t"
PIPE = "|"
DELIMITERS = (COMMA, TAB, PIPE)

# §7.3: keys and field names that may be written without quotes. ASCII only:
# Python's `\w` would also accept letters such as "é" (issue #65).
_UNQUOTED_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")

# §7.2: strings that look numeric must be quoted. This is wider than the
# decoder grammar on purpose: "05" and "+1" are quoted too.
_NUMERIC_LIKE = re.compile(r"[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")

# §4: the only unquoted tokens that decode as numbers. Leading zeros in the
# integer part ("05", "-007") are excluded, so those tokens stay strings.
_NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")

# Characters that force quoting wherever they appear in a string (§7.2).
_STRUCTURAL = re.compile(r'[:"\\\[\]{}\x00-\x1f]')

_ESCAPES = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}
_NEEDS_ESCAPE = re.compile(r'[\\"\x00-\x1f]')

_CANONICAL_MIN = Decimal("1e-6")
_CANONICAL_MAX = Decimal("1e21")


def is_number_token(token: str) -> bool:
    """Return whether an unquoted token decodes as a number (§4)."""
    return _NUMBER.fullmatch(token) is not None


def _escape_char(match: re.Match[str]) -> str:
    char = match.group()
    return _ESCAPES.get(char) or f"\\u{ord(char):04x}"


def quote(value: str) -> str:
    """Return ``value`` as a quoted token, escaped per §7.1."""
    return '"' + _NEEDS_ESCAPE.sub(_escape_char, value) + '"'


def _needs_quotes(value: str, delimiter: str) -> bool:
    return (
        not value
        or value[0] in " \t-#"
        or value[-1] in " \t"
        or value in ("true", "false", "null")
        or delimiter in value
        or _STRUCTURAL.search(value) is not None
        or _NUMERIC_LIKE.fullmatch(value) is not None
    )


def encode_string(value: str, delimiter: str) -> str:
    """Encode a string value, quoting it only when §7.2 requires it."""
    return quote(value) if _needs_quotes(value, delimiter) else value


def encode_key(key: str) -> str:
    """Encode an object key, entry key, or field name (§7.3)."""
    return key if _UNQUOTED_KEY.fullmatch(key) else quote(key)


def format_decimal(value: Decimal) -> str:
    """Format a finite decimal in the canonical number form of §2.

    Magnitudes in ``[1e-6, 1e21)`` use plain decimal notation without
    trailing zeros. Other magnitudes use JSON exponent notation with a
    lowercase ``e`` and an explicit exponent sign.
    """
    if not value:
        return "0"
    magnitude = abs(value)
    if _CANONICAL_MIN <= magnitude < _CANONICAL_MAX:
        text = f"{value:f}"
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text
    # Decimal.normalize() would round to the context precision, so strip
    # trailing zeros by hand to keep every significant digit.
    sign, digits, exponent = value.as_tuple()
    assert isinstance(exponent, int)
    mantissa = "".join(map(str, digits)).rstrip("0")
    exponent += len(digits) - 1
    if len(mantissa) > 1:
        mantissa = f"{mantissa[0]}.{mantissa[1:]}"
    exponent_sign = "+" if exponent >= 0 else "-"
    return f"{'-' if sign else ''}{mantissa}e{exponent_sign}{abs(exponent)}"


def format_float(value: float) -> str:
    """Format a finite float in the canonical number form of §2.

    ``repr`` yields the shortest digit string that round-trips, so the output
    decodes back to the same float. Integral floats of 2**53 and beyond are
    written with their exact digits instead: they decode as ``int``, and the
    shortest digits would not equal the float (``float(2**60) == 2**60`` but
    ``1152921504606847000 != 2**60``).
    """
    if value.is_integer() and abs(value) < 1e21:
        return str(int(value))
    return format_decimal(Decimal(repr(value)))


# ── Encoder (§1, §3, §8-§10) ─────────────────────────────────────────────────

Json: TypeAlias = (
    "bool | int | float | Decimal | str | list[Json] | dict[str, Json] | None"
)

# An ordered field list: each field is a leaf (``None``) or a nested field group.
Shape: TypeAlias = "tuple[tuple[str, Shape | None], ...]"

_SURROGATE = re.compile("[\ud800-\udfff]")


def _encode_document(
    obj: Any,
    *,
    indent_size: int,
    delimiter: str,
    default: Callable[[Any], Any] | None,
    sort_keys: bool,
) -> str:
    """Encode ``obj`` as a TOON document. Options are already validated."""
    try:
        value = _Normalizer(default, sort_keys).normalize(obj)
        encoder = _Encoder(indent_size, delimiter)
        encoder.root(value)
    except RecursionError:
        raise ValueError("Object is nested too deeply to encode") from None
    return "\n".join(encoder.lines)


# --------------------------------------------------------------------------
# Normalization (§3)
# --------------------------------------------------------------------------


def _check_string(value: str) -> str:
    if _SURROGATE.search(value):
        # §3: an unpaired surrogate has no TOON representation.
        raise ValueError(f"String contains an unpaired surrogate: {value!r}")
    return value


class _Normalizer:
    def __init__(self, default: Callable[[Any], Any] | None, sort_keys: bool) -> None:
        self.default = default
        self.sort_keys = sort_keys
        self.active: set[int] = set()

    def normalize(self, value: Any) -> Json:
        cls = type(value)
        if cls is str:
            return _check_string(value)
        if value is None or cls is bool or cls is int:
            return value  # type: ignore[no-any-return]
        if cls is float:
            return value if math.isfinite(value) else None
        if cls is dict or cls is list or cls is tuple:
            return self._container(value)
        return self._other(value)

    def _container(self, value: Any) -> Json:
        marker = id(value)
        if marker in self.active:
            raise ValueError("Circular reference detected")
        self.active.add(marker)
        try:
            if isinstance(value, Mapping):
                return self._mapping(value)
            items = value
            if isinstance(value, (set, frozenset)):
                items = _sorted_members(value)
            return [self.normalize(item) for item in items]
        finally:
            self.active.discard(marker)

    def _mapping(self, value: Mapping[Any, Any]) -> dict[str, Json]:
        pairs = [(_convert_key(key), item) for key, item in value.items()]
        if self.sort_keys:
            pairs.sort(key=lambda pair: pair[0])
        result: dict[str, Json] = {}
        for key, item in pairs:
            # Keys such as 1 and "1" collide once converted; keeping one value
            # would lose data, and a duplicate key is invalid TOON (§14).
            if key in result:
                raise ValueError(f"Duplicate key after conversion: {key!r}")
            result[key] = self.normalize(item)
        return result

    def _other(self, value: Any) -> Json:
        # Order matters: bool before int, str/int subclasses (StrEnum, IntEnum)
        # before Enum, datetime before date.
        if isinstance(value, str):
            return _check_string(str.__str__(value))
        if isinstance(value, bool):
            return bool(value)
        if isinstance(value, int):
            return int(value)
        if isinstance(value, float):
            number = float(value)
            return number if math.isfinite(number) else None
        if isinstance(value, Decimal):
            return value if value.is_finite() else None
        if isinstance(value, (Mapping, list, tuple, set, frozenset)):
            return self._container(value)
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if isinstance(value, (UUID, PurePath)):
            return str(value)
        if isinstance(value, Enum):
            return self._converted(value, value.value)
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            fields = {
                field.name: getattr(value, field.name)
                for field in dataclasses.fields(value)
            }
            return self._converted(value, fields)
        # attrs classes are recognized without importing attrs (§3).
        attributes = getattr(type(value), "__attrs_attrs__", None)
        if attributes is not None:
            fields = {field.name: getattr(value, field.name) for field in attributes}
            return self._converted(value, fields)
        pydantic = sys.modules.get("pydantic")
        if pydantic is not None and isinstance(value, pydantic.BaseModel):
            return self._converted(value, value.model_dump(mode="json"))
        if self.default is not None:
            return self._converted(value, self.default(value))
        raise TypeError(
            f"Object of type {type(value).__name__} is not TOON serializable"
        )

    def _converted(self, original: Any, replacement: Any) -> Json:
        """Normalize ``replacement``, which must not lead back to ``original``."""
        marker = id(original)
        if marker in self.active:
            raise ValueError("Circular reference detected")
        self.active.add(marker)
        try:
            return self.normalize(replacement)
        finally:
            self.active.discard(marker)


def _sorted_members(value: set[Any] | frozenset[Any]) -> list[Any]:
    """Order set members deterministically (Appendix E.6)."""
    try:
        return sorted(value)
    except TypeError:
        return sorted(value, key=repr)


def _convert_key(key: Any) -> str:
    """Coerce a mapping key to a string, following :func:`json.dumps`."""
    if isinstance(key, str):
        return _check_string(str.__str__(key))
    if key is None or isinstance(key, bool):
        return "null" if key is None else ("true" if key else "false")
    if isinstance(key, int):
        return str(int(key))
    if isinstance(key, float):
        if math.isfinite(key):
            return format_float(key)
        return "NaN" if math.isnan(key) else ("Infinity" if key > 0 else "-Infinity")
    raise TypeError(
        f"Keys must be str, int, float, bool or None, not {type(key).__name__}"
    )


# --------------------------------------------------------------------------
# Form detection (§9.3, §9.5)
# --------------------------------------------------------------------------


def _is_primitive(value: Json) -> bool:
    return not isinstance(value, (dict, list))


def _shape(objects: list[Json]) -> Shape | None:
    """Return the shared field list of ``objects``, or ``None`` if they are not uniform.

    Objects are uniform when all are non-empty objects with the same set of
    keys and every column is uniform-primitive or nested-uniform (§9.3).
    """
    first = objects[0]
    if not isinstance(first, dict) or not first:
        return None
    keys = first.keys()
    for obj in objects:
        if not isinstance(obj, dict) or len(obj) != len(keys) or obj.keys() != keys:
            return None
    fields: list[tuple[str, Shape | None]] = []
    for key in keys:
        column = [obj[key] for obj in objects if isinstance(obj, dict)]
        if all(map(_is_primitive, column)):
            fields.append((key, None))
            continue
        nested = _shape(column)
        if nested is None:
            return None
        fields.append((key, nested))
    return tuple(fields)


def _keyed_shape(obj: dict[str, Json]) -> Shape | None:
    """Field list for the keyed tabular form of an object (§9.5)."""
    if len(obj) < 2:
        return None
    return _shape(list(obj.values()))


def _leaves(obj: Json, shape: Shape) -> Iterator[Json]:
    """Yield the leaf values of ``obj`` in depth-first header order."""
    assert isinstance(obj, dict)
    for key, nested in shape:
        if nested is None:
            yield obj[key]
        else:
            yield from _leaves(obj[key], nested)


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


class _Encoder:
    def __init__(self, indent_size: int, delimiter: str) -> None:
        self.unit = " " * indent_size
        self.delimiter = delimiter
        # §11.1: every header declares the document delimiter; comma is implicit.
        self.symbol = "" if delimiter == "," else delimiter
        self.lines: list[str] = []

    def emit(self, depth: int, text: str) -> None:
        self.lines.append(self.unit * depth + text)

    def root(self, value: Json) -> None:
        if isinstance(value, dict):
            shape = _keyed_shape(value)
            if shape is not None:
                self.keyed("", value, shape, 0)
            else:
                self.fields(value, 0)  # an empty object is an empty document (§8)
        elif isinstance(value, list):
            if value:
                self.array("", value, 0, tabular=True)
            else:
                self.emit(0, "[]")
        elif isinstance(value, str) and value.startswith("\ufeff"):
            self.emit(0, quote(value))  # unquoted, it would read as a BOM (§7.2, §12)
        else:
            self.emit(0, self.primitive(value))

    def primitive(self, value: Json) -> str:
        if value is None:
            return "null"
        if value is True:
            return "true"
        if value is False:
            return "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return format_float(value)
        if isinstance(value, Decimal):
            return format_decimal(value)
        assert isinstance(value, str)
        return encode_string(value, self.delimiter)

    def join(self, values: Iterator[Json] | list[Json]) -> str:
        return self.delimiter.join(map(self.primitive, values))

    def field_list(self, shape: Shape) -> str:
        entries = (
            encode_key(key) + ("" if nested is None else self.field_list(nested))
            for key, nested in shape
        )
        return "{" + self.delimiter.join(entries) + "}"

    def fields(self, obj: dict[str, Json], depth: int) -> None:
        for key, value in obj.items():
            self.field(encode_key(key), value, depth)

    def field(self, key: str, value: Json, depth: int) -> None:
        """Emit one object field; ``key`` is already encoded (§8)."""
        if isinstance(value, dict):
            shape = _keyed_shape(value)
            if shape is not None:
                self.keyed(key, value, shape, depth)
            else:
                self.emit(depth, key + ":")
                self.fields(value, depth + 1)
        elif isinstance(value, list):
            if value:
                self.array(key, value, depth, tabular=True)
            else:
                self.emit(depth, key + ": []")
        else:
            self.emit(depth, f"{key}: {self.primitive(value)}")

    def array(
        self, prefix: str, array: list[Json], depth: int, *, tabular: bool
    ) -> None:
        """Emit a non-empty array whose header starts with ``prefix``.

        ``tabular`` is false for a keyless array that is itself a list item,
        where a field list is not allowed (§9.4).
        """
        head = f"{prefix}[{len(array)}{self.symbol}]"
        if all(map(_is_primitive, array)):
            self.emit(depth, f"{head}: {self.join(array)}")  # §9.1
            return
        shape = _shape(array) if tabular else None
        if shape is not None:
            self.emit(depth, f"{head}{self.field_list(shape)}:")  # §9.3
            for element in array:
                self.emit(depth + 1, self.join(_leaves(element, shape)))
            return
        self.emit(depth, head + ":")  # §9.2, §9.4
        for element in array:
            self.item(element, depth + 1)

    def keyed(self, key: str, obj: dict[str, Json], shape: Shape, depth: int) -> None:
        """Emit an object of uniform objects in keyed tabular form (§9.5)."""
        self.emit(depth, f"{key}[{len(obj)}:{self.symbol}]{self.field_list(shape)}:")
        for entry, value in obj.items():
            self.emit(
                depth + 1, f"{encode_key(entry)}: {self.join(_leaves(value, shape))}"
            )

    def item(self, value: Json, depth: int) -> None:
        """Emit one list item at ``depth`` (§9.4, §10)."""
        if isinstance(value, dict):
            if not value:
                self.emit(depth, "-")
                return
            # The object's fields stand at depth + 1; the first one moves onto
            # the hyphen line, so whatever scope it opens lands at depth + 2.
            first = len(self.lines)
            self.fields(value, depth + 1)
            indent = self.unit * depth
            self.lines[first] = (
                indent + "- " + self.lines[first][len(indent + self.unit) :]
            )
        elif isinstance(value, list):
            if value:
                self.array("- ", value, depth, tabular=False)
            else:
                self.emit(depth, f"- [0{self.symbol}]:")  # never "- []" (§9.2)
        else:
            self.emit(depth, "- " + self.primitive(value))


# ── Decoder (§5, §6, §9, §12, §14) ───────────────────────────────────────────

ObjectHook: TypeAlias = Callable[[dict[str, Any]], Any]
PairsHook: TypeAlias = Callable[[list[tuple[str, Any]]], Any]

# A parsed field list: each field is a leaf (``None``) or a nested field group.
Fields: TypeAlias = "tuple[tuple[str, Fields | None], ...]"

_BRACKET = re.compile(r"\[(0|[1-9][0-9]*)(:?)([\t|]?)\]")
_QUOTED = re.compile(r'"(?:[^"\\]|\\.)*"', re.DOTALL)
_HEX4 = re.compile(r"[0-9A-Fa-f]{4}")
_SIMPLE_ESCAPES = {"\\": "\\", '"': '"', "n": "\n", "r": "\r", "t": "\t"}


def _decode_document(
    text: str,
    *,
    indent_size: int,
    strict: bool,
    parse_int: Callable[[str], Any] | None,
    parse_float: Callable[[str], Any] | None,
    object_hook: ObjectHook | None,
    object_pairs_hook: PairsHook | None,
) -> Any:
    """Decode a TOON document. Options are already validated."""
    lines = _split_lines(text, indent_size, strict)
    parser = _Parser(
        lines, strict, parse_int, parse_float, object_hook, object_pairs_hook
    )
    try:
        return parser.document()
    except RecursionError:
        raise ToonDecodeError("Document is nested too deeply to decode") from None


# --------------------------------------------------------------------------
# Lines (§5.1, §12)
# --------------------------------------------------------------------------


@dataclass(slots=True)
class _Line:
    number: int
    """1-based line number in the original document."""
    depth: int
    content: str
    """The line without indentation and trailing spaces."""
    source: str
    """The line as written, for error messages."""
    blank_before: int | None
    """Number of the first blank line directly above this one, if any."""


def _split_lines(text: str, indent_size: int, strict: bool) -> list[_Line]:
    if text.startswith("\ufeff"):
        text = text[1:]  # byte-order mark (§12)
    lines: list[_Line] = []
    blank: int | None = None
    for number, source in enumerate(text.split("\n"), 1):
        if source.endswith("\r"):
            source = source[:-1]  # CRLF input (§12)
        stripped = source.lstrip(" ")
        if stripped.startswith("#"):
            continue  # comment line (§5.1); lines are adjacent across it
        content = stripped.rstrip(" ")
        # Tabs make a line blank only where they may indent it (§14.4).
        if not content or (not strict and not content.strip(" \t")):
            blank = blank or number
            continue
        spaces = len(source) - len(stripped)
        if content[0] == "\t":
            if strict:
                raise ToonDecodeError(
                    "Tabs are not allowed in indentation", number, source
                )
            # Non-strict: a tab counts as one level, spaces as usual (§14.4).
            run = len(content) - len(content.lstrip(" \t"))
            spaces += content.count(" ", 0, run)
            depth = content.count("\t", 0, run) + spaces // indent_size
            content = content[run:]
        else:
            if strict and spaces % indent_size:
                raise ToonDecodeError(
                    f"Indentation of {spaces} spaces is not a multiple of "
                    f"{indent_size}",
                    number,
                    source,
                )
            depth = spaces // indent_size
        lines.append(_Line(number, depth, content, source, blank))
        blank = None
    return lines


# --------------------------------------------------------------------------
# Line classes (§5.2)
# --------------------------------------------------------------------------


@dataclass(slots=True)
class _Header:
    key: str | None
    length: int
    keyed: bool
    delimiter: str
    fields: Fields | None
    rest: str
    """Inline content after the colon, trimmed."""


@dataclass(slots=True)
class _KeyValue:
    key: str
    rest: str


@dataclass(slots=True)
class _Scalar:
    token: str


def _is_list_item(content: str) -> bool:
    return content == "-" or content.startswith("- ")


def _quoted_end(text: str, start: int) -> int:
    """Index just past the quoted token at ``start``, or -1 if it is unterminated."""
    match = _QUOTED.match(text, start)
    return match.end() if match else -1


def _find_unquoted(text: str, char: str, start: int = 0) -> int:
    """Index of the first ``char`` outside double quotes, or -1."""
    if '"' not in text:
        return text.find(char, start)
    in_quotes = False
    i, n = start, len(text)
    while i < n:
        c = text[i]
        if in_quotes:
            if c == "\\":
                i += 1
            elif c == '"':
                in_quotes = False
        elif c == '"':
            in_quotes = True
        elif c == char:
            return i
        i += 1
    return -1


def _split(text: str, delimiter: str) -> list[str]:
    """Split on unquoted delimiters and trim each token (§11.2, Appendix B.3)."""
    if '"' not in text:
        return [token.strip(" ") for token in text.split(delimiter)]
    tokens: list[str] = []
    in_quotes = False
    start = i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if in_quotes:
            if c == "\\":
                i += 1
            elif c == '"':
                in_quotes = False
        elif c == '"':
            in_quotes = True
        elif c == delimiter:
            tokens.append(text[start:i].strip(" "))
            start = i + 1
        i += 1
    tokens.append(text[start:].strip(" "))
    return tokens


def _leaf_count(fields: Fields) -> int:
    return sum(1 if nested is None else _leaf_count(nested) for _, nested in fields)


# --------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------


class _Parser:
    def __init__(
        self,
        lines: list[_Line],
        strict: bool,
        parse_int: Callable[[str], Any] | None,
        parse_float: Callable[[str], Any] | None,
        object_hook: ObjectHook | None,
        object_pairs_hook: PairsHook | None,
    ) -> None:
        self.lines = lines
        self.pos = 0
        self.strict = strict
        self.parse_int = parse_int or int
        self.parse_float = parse_float
        self.object_hook = object_hook
        self.object_pairs_hook = object_pairs_hook
        # Number of enclosing header scopes that have consumed their first
        # item, row, or entry: a blank line inside any of them is a header span.
        self.spans = 0

    # -- infrastructure -----------------------------------------------------

    def error(self, msg: str, line: _Line) -> ToonDecodeError:
        return ToonDecodeError(msg, line.number, line.source)

    def peek(self) -> _Line | None:
        return self.lines[self.pos] if self.pos < len(self.lines) else None

    def take(self) -> _Line:
        line = self.lines[self.pos]
        if line.blank_before is not None and self.spans and self.strict:
            raise ToonDecodeError(
                "Blank line inside an array or keyed object", line.blank_before, ""
            )
        self.pos += 1
        return line

    def finish(self, obj: dict[str, Any]) -> Any:
        """Apply the object hooks to a fully decoded object."""
        if self.object_pairs_hook is not None:
            return self.object_pairs_hook(list(obj.items()))
        if self.object_hook is not None:
            return self.object_hook(obj)
        return obj

    def assign(self, obj: dict[str, Any], key: str, value: Any, line: _Line) -> None:
        if self.strict and key in obj:
            raise self.error(f"Duplicate key {key!r}", line)
        # Non-strict: last write wins (§14.4); like json.loads, the key keeps
        # the position of its first occurrence.
        obj[key] = value

    def scope_depth(self, expected: int) -> int:
        """Content depth of a scope; non-strict mode tolerates a deeper first line."""
        line = self.peek()
        if line is not None and not self.strict and line.depth > expected:
            return line.depth
        return expected

    # -- tokens (§4, §7) ----------------------------------------------------

    def unescape(self, body: str, line: _Line) -> str:
        if "\\" not in body:
            return body
        parts: list[str] = []
        i = 0
        while (j := body.find("\\", i)) >= 0:
            parts.append(body[i:j])
            c = body[j + 1] if j + 1 < len(body) else ""
            if c in _SIMPLE_ESCAPES:
                parts.append(_SIMPLE_ESCAPES[c])
                i = j + 2
            elif c == "u" and _HEX4.fullmatch(body, j + 2, j + 6):
                code = int(body[j + 2 : j + 6], 16)
                if 0xD800 <= code <= 0xDFFF:
                    raise self.error(f"Surrogate escape \\u{body[j + 2 : j + 6]}", line)
                parts.append(chr(code))
                i = j + 6
            else:
                raise self.error(f"Invalid escape sequence {body[j : j + 6]!r}", line)
        parts.append(body[i:])
        return "".join(parts)

    def quoted(self, token: str, line: _Line) -> str:
        """Decode a token that starts with a quote (§7.4 quoted-token boundary)."""
        end = _quoted_end(token, 0)
        if end < 0:
            raise self.error("Unterminated string", line)
        if end != len(token):
            raise self.error("Unexpected characters after closing quote", line)
        return self.unescape(token[1:-1], line)

    def key(self, token: str, line: _Line) -> str:
        token = token.strip(" ")
        return self.quoted(token, line) if token.startswith('"') else token

    def primitive(self, token: str, line: _Line) -> Any:
        if not token:
            return ""
        if token[0] == '"':
            return self.quoted(token, line)
        if token == "true":
            return True
        if token == "false":
            return False
        if token == "null":
            return None
        if is_number_token(token):
            return self.number(token, line)
        return token

    def number(self, token: str, line: _Line) -> Any:
        if "." not in token and "e" not in token and "E" not in token:
            try:
                return self.parse_int(token)
            except ValueError as exc:
                raise self.error(str(exc), line) from None
        if self.parse_float is not None:
            return self.parse_float(token)
        value = float(token)
        if math.isinf(value):
            raise self.error(f"Number {token} is out of range", line)
        return value or 0.0  # -0 decodes to 0 (§4)

    def values(self, text: str, delimiter: str, line: _Line) -> list[Any]:
        """Decode a delimited cell sequence; empty text is zero cells (§11.2)."""
        if not text:
            return []
        return [self.primitive(token, line) for token in _split(text, delimiter)]

    # -- headers (§6) -------------------------------------------------------

    def classify(self, content: str, line: _Line) -> _Header | _KeyValue | _Scalar:
        """Classify a line body as a header, a key-value line, or a scalar (§5.2)."""
        colon = _find_unquoted(content, ":")
        if content.startswith('"'):
            end = _quoted_end(content, 0)
            if end < 0:
                raise self.error("Unterminated string", line)
            if colon >= 0 and content.startswith("[", end):
                return self.header(content, end, line)
            after = content[end:].lstrip(" ")
            if not after:
                return _Scalar(content)
            if after[0] != ":":
                raise self.error("Unexpected characters after closing quote", line)
            return _KeyValue(self.quoted(content[:end], line), after[1:].strip(" "))
        bracket = _find_unquoted(content, "[")
        if 0 <= bracket < colon:
            return self.header(content, bracket, line)
        if colon >= 0:
            return _KeyValue(
                content[:colon].strip(" "), content[colon + 1 :].strip(" ")
            )
        return _Scalar(content)

    def header(self, content: str, bracket: int, line: _Line) -> _Header:
        """Parse a header whose bracket segment starts at ``bracket`` (§6)."""
        match = _BRACKET.match(content, bracket)
        if match is None:
            raise self.error("Malformed bracket segment", line)
        if content[bracket - 1 : bracket] in (" ", "\t"):  # SP and HTAB only (§1.2)
            raise self.error("Whitespace between a key and its bracket segment", line)
        delimiter = match.group(3) or ","
        pos = match.end()
        fields = None
        if content.startswith("{", pos):
            fields, pos = self.field_list(content, pos, delimiter, line)
        if not content.startswith(":", pos):
            raise self.error("Expected ':' after the array header", line)
        rest = content[pos + 1 :].strip(" ")
        keyed = bool(match.group(2))
        if keyed and fields is None:
            raise self.error("A keyed header requires a field list", line)
        if fields is not None and rest:
            raise self.error(
                "Unexpected content after a header with a field list", line
            )
        key_text = content[:bracket]
        key = self.key(key_text, line) if key_text else None
        return _Header(key, int(match.group(1)), keyed, delimiter, fields, rest)

    @staticmethod
    def _skip_spaces(text: str, pos: int) -> int:
        n = len(text)
        while pos < n and text[pos] == " ":
            pos += 1
        return pos

    def _field_name(self, text: str, pos: int, line: _Line) -> tuple[str, int]:
        """Parse one field name at ``pos``; return it and the index past it."""
        if text.startswith('"', pos):
            end = _quoted_end(text, pos)
            if end < 0:
                raise self.error("Unterminated field name", line)
            return self.unescape(text[pos + 1 : end - 1], line), end
        start, n = pos, len(text)
        while pos < n and text[pos] not in "{},|\t":
            if text[pos] == '"':
                end = _quoted_end(text, pos)
                pos = end if end >= 0 else n
            else:
                pos += 1
        name = text[start:pos].strip(" ")
        if not name:
            raise self.error("Empty field name in field list", line)
        return name, pos

    def _nested_fields(
        self, text: str, pos: int, delimiter: str, line: _Line
    ) -> tuple[Fields | None, int]:
        """Parse an optional ``{...}`` directly after a field name."""
        if not text.startswith("{", pos):
            return None, pos
        if text[pos - 1] == " ":
            raise self.error(
                "Whitespace between a field name and its nested field group", line
            )
        nested, pos = self.field_list(text, pos, delimiter, line)
        return nested, self._skip_spaces(text, pos)

    def field_list(
        self, text: str, pos: int, delimiter: str, line: _Line
    ) -> tuple[Fields, int]:
        """Parse the ``{...}`` at ``pos``; return the fields and the index past it."""
        fields: list[tuple[str, Fields | None]] = []
        seen: set[str] = set()
        n = len(text)
        pos = self._skip_spaces(text, pos + 1)
        while True:
            name, pos = self._field_name(text, pos, line)
            pos = self._skip_spaces(text, pos)
            nested, pos = self._nested_fields(text, pos, delimiter, line)
            if name in seen and self.strict:
                raise self.error(f"Duplicate field name {name!r}", line)
            seen.add(name)
            fields.append((name, nested))
            if pos >= n:
                raise self.error("Unmatched '{' in field list", line)
            separator = text[pos]
            pos += 1
            if separator == "}":
                return tuple(fields), pos
            if separator != delimiter:
                if separator in DELIMITERS:
                    raise self.error(
                        "Field list delimiter does not match the bracket segment", line
                    )
                raise self.error("Malformed field list", line)

    # -- document (§5) ------------------------------------------------------

    def document(self) -> Any:
        first = self.peek()
        if first is None:
            return self.finish({})  # empty document (§5)
        if first.depth > 0:
            raise self.over_indented(first)  # an indented first line (§5, §8)
        if first.content == "[]":
            self.take()
            self.end_of_root()
            return []
        kind = self.classify(first.content, first)
        if isinstance(kind, _Header) and kind.key is None:
            self.take()
            value = self.header_value(kind, first, 1)
            self.end_of_root()
            return value
        if isinstance(kind, _Scalar) and len(self.lines) == 1:
            self.take()
            return self.primitive(first.content, first)
        return self.finish(self.object_body(0, {}, -1))

    def end_of_root(self) -> None:
        """A root array or keyed object spans the whole document (§5)."""
        line = self.peek()
        if line is not None:
            raise self.error("Unexpected content after the root value", line)

    # -- objects (§8) -------------------------------------------------------

    def object_body(
        self, depth: int, obj: dict[str, Any], parent: int
    ) -> dict[str, Any]:
        """Parse the fields at ``depth`` of an object opened at ``parent`` (§8)."""
        while (line := self.peek()) is not None and line.depth > parent:
            if line.depth != depth:
                raise self.over_indented(line)
            self.take()
            self.field(line, obj, depth)
        return obj

    def over_indented(self, line: _Line) -> ToonDecodeError:
        """A line deeper than its scope that no line opened (§8, §14.2)."""
        return self.error("Unexpected indentation", line)

    def field(self, line: _Line, obj: dict[str, Any], depth: int) -> None:
        kind = self.classify(line.content, line)
        if isinstance(kind, _Header):
            if kind.key is None:
                raise self.error(
                    "A header without a key is only valid at the root", line
                )
            self.assign(obj, kind.key, self.header_value(kind, line, depth + 1), line)
            return
        if isinstance(kind, _Scalar):
            raise self.error("Expected 'key: value'", line)
        self.assign(obj, kind.key, self.field_value(kind.rest, line, depth), line)

    def field_value(self, rest: str, line: _Line, depth: int) -> Any:
        """Decode what follows ``key:`` for a field standing at ``depth``."""
        if rest:
            return [] if rest == "[]" else self.primitive(rest, line)
        child = self.peek()
        if child is None or child.depth <= depth:
            return self.finish({})
        if self.strict and child.depth != depth + 1:
            raise self.error("Indentation jumps more than one level", child)
        return self.finish(self.object_body(child.depth, {}, depth))

    # -- arrays and keyed objects (§9, §10) ---------------------------------

    def header_value(self, header: _Header, line: _Line, depth: int) -> Any:
        """Decode the value a header opens; ``depth`` is its content depth."""
        if header.keyed:
            return self.entries(header, line, self.scope_depth(depth), depth - 1)
        if header.fields is not None:
            return self.rows(header, line, self.scope_depth(depth), depth - 1)
        if header.rest:
            values = self.values(header.rest, header.delimiter, line)
            self.check_count(len(values), header, line)
            return values
        return self.items(header, line, self.scope_depth(depth), depth - 1)

    def check_count(self, count: int, header: _Header, line: _Line) -> None:
        if self.strict and count != header.length:
            raise self.error(f"Declared length {header.length} but found {count}", line)

    def check_width(self, cells: list[Any], fields: Fields, line: _Line) -> None:
        width = _leaf_count(fields)
        if len(cells) != width:
            raise self.error(f"Expected {width} values but found {len(cells)}", line)

    def items(self, header: _Header, line: _Line, depth: int, parent: int) -> list[Any]:
        """Parse the list items of an array in list form (§9.2, §9.4)."""
        items: list[Any] = []
        started = False
        try:
            while (item := self.peek()) and item.depth > parent:
                if item.depth != depth:
                    raise self.over_indented(item)
                if not _is_list_item(item.content):
                    break
                self.take()
                if not started:
                    self.spans += 1
                    started = True
                items.append(self.item(item, depth))
        finally:
            self.spans -= started
        self.check_count(len(items), header, line)
        return items

    def item(self, line: _Line, depth: int) -> Any:
        """Decode one list item at ``depth`` (§9.4, §10)."""
        rest = line.content[2:].strip(" ")
        if not rest:
            return self.finish({})
        if rest == "[]":
            return []
        kind = self.classify(rest, line)
        if isinstance(kind, _Scalar):
            return self.primitive(rest, line)
        if isinstance(kind, _Header) and kind.key is None:
            if kind.fields is not None:
                raise self.error(
                    "A header with a field list cannot be a list item", line
                )
            return self.header_value(kind, line, depth + 1)
        # An object whose first field sits on the hyphen line at depth + 1.
        obj: dict[str, Any] = {}
        if isinstance(kind, _Header):
            assert kind.key is not None
            obj[kind.key] = self.header_value(kind, line, depth + 2)
        else:
            obj[kind.key] = self.field_value(kind.rest, line, depth + 1)
        return self.finish(self.object_body(depth + 1, obj, depth))

    def rows(self, header: _Header, line: _Line, depth: int, parent: int) -> list[Any]:
        """Parse the rows of a tabular array (§9.3)."""
        assert header.fields is not None
        delimiter = header.delimiter
        rows: list[Any] = []
        started = False
        try:
            while (row := self.peek()) and row.depth > parent:
                if row.depth != depth:
                    raise self.over_indented(row)
                colon = _find_unquoted(row.content, ":")
                if colon >= 0:
                    split = _find_unquoted(row.content, delimiter)
                    if split < 0 or colon < split:
                        break  # a key-value line ends the rows
                self.take()
                if not started:
                    self.spans += 1
                    started = True
                cells = self.values(row.content, delimiter, row)
                self.check_width(cells, header.fields, row)
                rows.append(self.materialize(header.fields, iter(cells)))
        finally:
            self.spans -= started
        self.check_count(len(rows), header, line)
        return rows

    def entries(self, header: _Header, line: _Line, depth: int, parent: int) -> Any:
        """Parse the entry rows of a keyed tabular object (§9.5)."""
        assert header.fields is not None
        obj: dict[str, Any] = {}
        count = 0
        try:
            while (entry := self.peek()) and entry.depth > parent:
                if entry.depth != depth:
                    raise self.over_indented(entry)
                self.take()
                if not count:
                    self.spans += 1
                count += 1
                colon = _find_unquoted(entry.content, ":")
                if colon < 0:
                    raise self.error("Expected 'key: values' entry row", entry)
                key = self.key(entry.content[:colon], entry)
                cells = self.values(
                    entry.content[colon + 1 :].strip(" "), header.delimiter, entry
                )
                self.check_width(cells, header.fields, entry)
                self.assign(
                    obj, key, self.materialize(header.fields, iter(cells)), entry
                )
        finally:
            self.spans -= bool(count)
        self.check_count(count, header, line)
        return self.finish(obj)

    def materialize(self, fields: Fields, cells: Iterator[Any]) -> Any:
        """Build one object from row cells, walking the field list depth-first."""
        obj: dict[str, Any] = {}
        for name, nested in fields:
            obj[name] = (
                next(cells) if nested is None else self.materialize(nested, cells)
            )
        return self.finish(obj)
