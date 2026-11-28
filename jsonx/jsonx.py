# /// zerodep
# version = "2.1.0"
# deps = []
# tier = "simple"
# category = "serialization"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///

"""Extended JSON parser — zero dependencies, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Drop-in replacement for commentjson / stdlib json with JSONC support,
plus JSONL (JSON Lines) helpers.

Supports:
    - Single-line comments: ``//`` and ``#``
    - Block comments: ``/* ... */``
    - Trailing commas in objects and arrays
    - All standard JSON types
    - JSONL (one JSON value per line, with optional comments)
    - Best-effort repair of damaged JSON (``repair``, ``loads(repair=True)``)

Example::

    loads('{"a": 1, // comment\n"b": 2}')
    # {'a': 1, 'b': 2}
    load(open("config.jsonc"))
    # {...}

    # JSONL with comments
    loads_lines('{"a":1}\n// skip\n{"b":2}')
    # [{'a': 1}, {'b': 2}]
"""

from __future__ import annotations

import json
import json.scanner
import re
from typing import IO, Any

__all__ = [
    "JSONCDecodeError",
    "JSONRepairError",
    "RepairReport",
    "loads",
    "load",
    "dumps",
    "dump",
    "repair",
    "loads_lines",
    "load_lines",
    "dumps_lines",
    "dump_lines",
]

# ── Comment stripping ─────────────────────────────────────────────────────────

# Matches (in priority order):
#   1. Double-quoted strings (group 1) — preserved as-is
#   2. Single-line // comments — removed
#   3. Single-line # comments — removed
#   4. Block /* ... */ comments — removed
_COMMENT_RE = re.compile(
    r"""
    ( "(?:[^"\\]|\\.)*" )   # group 1: double-quoted string (keep)
    | //[^\n]*              # single-line // comment
    | \#[^\n]*              # single-line # comment
    | /\*[\s\S]*?\*/        # block /* */ comment
    """,
    re.VERBOSE | re.MULTILINE,
)

# Trailing comma before closing ] or }
_TRAILING_COMMA_RE = re.compile(
    r"""
    ( "(?:[^"\\]|\\.)*" )   # group 1: double-quoted string (keep)
    | ,\s*(?=[}\]])         # comma followed by optional whitespace then } or ]
    """,
    re.VERBOSE,
)


def _strip_comments(text: str) -> str:
    """Remove ``//``, ``#``, and ``/* */`` comments, preserving strings."""

    def _replace(m: re.Match[str]) -> str:
        if m.group(1) is not None:
            return m.group(1)
        return ""

    return _COMMENT_RE.sub(_replace, text)


def _strip_trailing_commas(text: str) -> str:
    """Remove trailing commas before ``}`` and ``]``, preserving strings."""

    def _replace(m: re.Match[str]) -> str:
        if m.group(1) is not None:
            return m.group(1)
        return ""

    return _TRAILING_COMMA_RE.sub(_replace, text)


def _preprocess(text: str) -> str:
    """Strip comments and trailing commas from JSONC text."""
    text = _strip_comments(text)
    text = _strip_trailing_commas(text)
    return text


# ── Line-number error mapping ────────────────────────────────────────────────


def _remap_error_position(
    original: str, cleaned: str, clean_pos: int
) -> tuple[int, int]:
    """Map a character offset in *cleaned* text back to *original* line/col.

    Returns (line, column), both 1-based.
    """
    # Build a mapping from cleaned-offset → original-offset by replaying the
    # comment-stripping regex.  Each matched region in the original either maps
    # 1:1 (strings) or collapses to zero length (comments).
    orig_idx = 0
    clean_idx = 0
    mapping: list[tuple[int, int, int]] = []  # (clean_start, clean_end, orig_start)

    for m in _COMMENT_RE.finditer(original):
        # Characters before this match map 1:1
        pre_len = m.start() - orig_idx
        if pre_len > 0:
            mapping.append((clean_idx, clean_idx + pre_len, orig_idx))
            clean_idx += pre_len
        orig_idx = m.start()

        if m.group(1) is not None:
            # Preserved string — maps 1:1
            span_len = m.end() - m.start()
            mapping.append((clean_idx, clean_idx + span_len, orig_idx))
            clean_idx += span_len
        # else: comment — removed, clean_idx doesn't advance

        orig_idx = m.end()

    # Tail after last match
    tail_len = len(original) - orig_idx
    if tail_len > 0:
        mapping.append((clean_idx, clean_idx + tail_len, orig_idx))

    # Look up clean_pos in the mapping
    orig_offset = clean_pos  # fallback
    for cs, ce, os_ in mapping:
        if cs <= clean_pos < ce:
            orig_offset = os_ + (clean_pos - cs)
            break
        if clean_pos < cs:
            orig_offset = os_
            break

    # Convert original offset to line/col
    line = original[:orig_offset].count("\n") + 1
    last_nl = original.rfind("\n", 0, orig_offset)
    col = orig_offset - last_nl  # 1-based
    return line, col


# ── Repair ───────────────────────────────────────────────────────────────────
#
# The repair path parses the damaged text directly into Python objects, in one
# pass, without building a repaired copy of the document: a 660 KB body costs
# one scan and the result. Strings and numbers use the stdlib C helpers the
# stdlib decoder itself uses (``scanstring``, ``NUMBER_RE``), so the Python
# loop only walks the structure.
#
# It never silently invents bytes: where a value is missing (a key with no
# value, an element lost to a splice) the value is dropped and the report says
# so. Everything that parsed before the damage is kept.

_MISSING = object()
_WS = " \t\r\n"
_NUMBER_RE = json.scanner.NUMBER_RE
_scanstring: Any = getattr(
    json.decoder, "scanstring", getattr(json.decoder, "py_scanstring", None)
)
if _scanstring is None:  # pragma: no cover - stdlib always ships one
    raise ImportError("json.decoder has no string scanner")
_MAX_DEPTH = 512
_UNICODE_ESCAPE = set("0123456789abcdefABCDEF")
_UNESCAPE = {
    '"': '"',
    "\\": "\\",
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


class JSONRepairError(ValueError):
    """Raised when no JSON value can be recovered from the text.

    Attributes:
        report: What the failed attempt had repaired so far.
    """

    def __init__(self, message: str, report: RepairReport) -> None:
        super().__init__(message)
        self.report = report


class RepairReport:
    """What :func:`repair` had to fix.

    Attributes:
        counts: Repair kind to number of times it was applied. The kinds are
            ``missing_comma``, ``missing_colon``, ``missing_value``,
            ``unclosed``, ``unterminated_string``, ``stray_closer``,
            ``skipped_token``, ``unquoted_key``, ``bad_number``,
            ``empty_entry`` and ``trailing_garbage``.
        replaced_characters: Undecodable bytes (``U+FFFD``) in byte input.
    """

    __slots__ = ("counts", "replaced_characters")

    def __init__(
        self, counts: dict[str, int] | None = None, replaced_characters: int = 0
    ) -> None:
        self.counts = counts or {}
        self.replaced_characters = replaced_characters

    @property
    def total(self) -> int:
        """Number of repairs, byte replacements included."""
        return sum(self.counts.values()) + self.replaced_characters

    def __bool__(self) -> bool:
        return self.total > 0

    def __repr__(self) -> str:
        head = ", ".join(f"{k}={v}" for k, v in sorted(self.counts.items()))
        if self.replaced_characters:
            head += f", replaced_characters={self.replaced_characters}"
        return f"RepairReport({head or 'clean'})"


class _Repairer:
    __slots__ = ("text", "n", "counts")

    def __init__(self, text: str) -> None:
        self.text = text
        self.n = len(text)
        self.counts: dict[str, int] = {}

    def note(self, kind: str) -> None:
        counts = self.counts
        counts[kind] = counts.get(kind, 0) + 1

    def skip(self, i: int) -> int:
        """Skip whitespace and comments."""
        text, n = self.text, self.n
        while i < n:
            c = text[i]
            if c in _WS:
                i += 1
            elif c == "/" and i + 1 < n and text[i + 1] == "/":
                j = text.find("\n", i + 2)
                i = n if j < 0 else j + 1
            elif c == "/" and i + 1 < n and text[i + 1] == "*":
                j = text.find("*/", i + 2)
                i = n if j < 0 else j + 2
            elif c == "#":
                j = text.find("\n", i + 1)
                i = n if j < 0 else j + 1
            else:
                break
        return i

    def string(self, i: int) -> tuple[str, int]:
        """Read a string. *i* points at the opening quote."""
        try:
            return _scanstring(self.text, i + 1, False)
        except ValueError:
            self.note("unterminated_string")
            return self._lenient_string(i + 1)

    def _lenient_string(self, i: int) -> tuple[str, int]:
        text, n = self.text, self.n
        buf: list[str] = []
        while i < n:
            c = text[i]
            if c == "\\":
                if i + 1 >= n:
                    return "".join(buf), n
                e = text[i + 1]
                if e == "u":
                    hex4 = text[i + 2 : i + 6]
                    if len(hex4) == 4 and set(hex4) <= _UNICODE_ESCAPE:
                        buf.append(chr(int(hex4, 16)))
                        i += 6
                    else:
                        i += 2
                    continue
                buf.append(_UNESCAPE.get(e, e))
                i += 2
                continue
            if c == '"':
                return "".join(buf), i + 1
            buf.append(c)
            i += 1
        return "".join(buf), n

    def number(self, i: int) -> tuple[Any, int]:
        m = _NUMBER_RE.match(self.text, i)
        if m:
            literal = m.group()
            return (
                float(literal) if any(ch in literal for ch in ".eE") else int(literal)
            ), m.end()
        text, n = self.text, self.n
        j = i + 1
        while j < n and (text[j].isdigit() or text[j] in ".eE+-"):
            j += 1
        self.note("bad_number")
        literal = text[i:j]
        try:
            return int(literal), j
        except ValueError:
            try:
                return float(literal), j
            except ValueError:
                return None, j

    def value(self, i: int, depth: int) -> tuple[Any, int]:
        text, n = self.text, self.n
        i = self.skip(i)
        if i >= n:
            self.note("missing_value")
            return _MISSING, i
        c = text[i]
        if c in "}]" or c == ",":
            self.note("missing_value")
            return _MISSING, i
        if c == "{":
            if depth >= _MAX_DEPTH:
                raise JSONRepairError("nesting too deep", RepairReport(self.counts))
            return self.object(i, depth + 1)
        if c == "[":
            if depth >= _MAX_DEPTH:
                raise JSONRepairError("nesting too deep", RepairReport(self.counts))
            return self.array(i, depth + 1)
        if c == '"':
            return self.string(i)
        if text.startswith("true", i):
            return True, i + 4
        if text.startswith("false", i):
            return False, i + 5
        if text.startswith("null", i):
            return None, i + 4
        if text.startswith("NaN", i):
            return float("nan"), i + 3
        if text.startswith("Infinity", i):
            return float("inf"), i + 8
        if text.startswith("-Infinity", i):
            return float("-inf"), i + 9
        if c == "-" or c.isdigit():
            return self.number(i)
        # A spliced token: skip to the next structural character.
        self.note("skipped_token")
        j = i + 1
        while j < n and text[j] not in ",}]":
            j += 1
        return _MISSING, j

    def object(self, i: int, depth: int) -> tuple[dict[str, Any], int]:
        text, n = self.text, self.n
        i += 1
        obj: dict[str, Any] = {}
        while True:
            i = self.skip(i)
            if i >= n:
                self.note("unclosed")
                return obj, n
            c = text[i]
            if c == "}":
                return obj, i + 1
            if c == "]":
                self.note("stray_closer")
                i += 1
                continue
            if c == ",":
                self.note("empty_entry")
                i += 1
                continue
            if c == '"':
                key, i = self.string(i)
            else:
                j = i
                while j < n and text[j] not in ":,} \t\r\n":
                    j += 1
                key, i = text[i:j], j
                self.note("unquoted_key")
            i = self.skip(i)
            if i < n and text[i] == ":":
                i += 1
            else:
                self.note("missing_colon")
            value, i = self.value(i, depth)
            if value is not _MISSING:
                obj[key] = value
            i = self.skip(i)
            if i < n and text[i] == ",":
                i += 1
            elif i < n and text[i] != "}":
                self.note("missing_comma")

    def array(self, i: int, depth: int) -> tuple[list[Any], int]:
        text, n = self.text, self.n
        i += 1
        arr: list[Any] = []
        while True:
            i = self.skip(i)
            if i >= n:
                self.note("unclosed")
                return arr, n
            c = text[i]
            if c == "]":
                return arr, i + 1
            if c == "}":
                self.note("stray_closer")
                i += 1
                continue
            if c == ",":
                self.note("empty_entry")
                i += 1
                continue
            value, i = self.value(i, depth)
            if value is not _MISSING:
                arr.append(value)
            i = self.skip(i)
            if i < n and text[i] == ",":
                i += 1
            elif i < n and text[i] != "]":
                self.note("missing_comma")


def _repair_document(
    text: str, replaced_characters: int = 0
) -> tuple[Any, RepairReport]:
    if text.startswith("\ufeff"):
        text = text[1:]
    try:
        value, report = _repair_once(text, 0)
        if value is _MISSING:
            # A splice can put junk in front of the document; the container
            # that follows it is still the document.
            starts = [p for p in (text.find("{"), text.find("[")) if p > 0]
            if starts:
                value, report = _repair_once(text, min(starts))
                if value is not _MISSING:
                    report.counts["discarded_prefix"] = 1
        if not isinstance(value, (dict, list)) and value is not _MISSING:
            # Damage that removes the opening brace leaves a bare string (or
            # number) in front of the rest of the document. When a container
            # covers more of the text, that container is the document.
            starts = [p for p in (text.find("{"), text.find("[")) if p > 0]
            if starts:
                other, other_report = _repair_once(text, min(starts))
                if isinstance(other, (dict, list)):
                    other_report.counts["discarded_prefix"] = 1
                    value, report = other, other_report
    except RecursionError:
        raise JSONRepairError(
            "nesting too deep", RepairReport({}, replaced_characters)
        ) from None
    if value is _MISSING:
        raise JSONRepairError("no JSON value found", report)
    return value, RepairReport(report.counts, replaced_characters)


def _repair_once(text: str, start: int) -> tuple[Any, RepairReport]:
    fixer = _Repairer(text)
    value, i = fixer.value(start, 0)
    i = fixer.skip(i)
    if i < fixer.n:
        fixer.note("trailing_garbage")
    return value, RepairReport(fixer.counts)


def repair(text: str | bytes | bytearray) -> tuple[Any, RepairReport]:
    """Recover a value from JSON that is damaged but still readable.

    Accepts truncation, missing commas or colons, stray brackets, spliced
    tokens, comments and trailing commas. Byte input is decoded with
    ``errors="replace"``, which is how a body damaged in transit usually
    arrives; each replaced byte is counted.

    Repair keeps every value that parsed before the damage and drops the ones
    the damage made unreadable. It cannot detect bytes replaced inside a
    string: such values come back wrong without an error. Use it on data that
    is better recovered approximately than lost, and never as the default
    parser for input you validate.

    Args:
        text: Damaged JSON text, or bytes to decode first.

    Returns:
        ``(value, report)`` where ``report`` counts what was repaired.

    Raises:
        JSONRepairError: If no JSON value can be recovered at all.
    """
    if isinstance(text, (bytes, bytearray)):
        decoded = bytes(text).decode("utf-8", "replace")
        replaced = decoded.count("�")
        return _repair_document(decoded, replaced)
    if not isinstance(text, str):
        raise TypeError(f"repair() requires str or bytes, not {type(text).__name__}")
    return _repair_document(text)


class JSONCDecodeError(json.JSONDecodeError):
    """Error raised when JSONC parsing fails.

    Provides line and column numbers relative to the original JSONC source
    (before comment/trailing-comma stripping).
    """


# ── Public API ────────────────────────────────────────────────────────────────


def loads(
    text: str,
    *,
    cls: type[json.JSONDecoder] | None = None,
    object_hook: Any = None,
    parse_float: Any = None,
    parse_int: Any = None,
    parse_constant: Any = None,
    object_pairs_hook: Any = None,
    repair: bool = False,
    **kwargs: Any,
) -> Any:
    """Deserialize a JSONC string to a Python object.

    Strips ``//``, ``#``, and ``/* */`` comments and trailing commas before
    delegating to :func:`json.loads`. Documents that already parse as plain
    JSON skip the preprocessing pass entirely; a custom decoder or hook opts
    out of that fast path, so it never parses the same text twice.

    Hooks (``object_hook``, ``object_pairs_hook``, ``parse_float``, …) must
    not raise :class:`json.JSONDecodeError` to reject a document: that
    exception is the syntax-error signal, so a hook raising it is
    indistinguishable from a parse failure. Raise ``ValueError`` instead.

    Args:
        text: JSONC source string. Only ``str`` is accepted; decode bytes
            before calling this function.
        cls: Custom JSON decoder class.
        object_hook: Called with the result of any object literal decoded.
        parse_float: Called with every JSON float string decoded.
        parse_int: Called with every JSON int string decoded.
        parse_constant: Called with ``-Infinity``, ``Infinity``, ``NaN``.
        object_pairs_hook: Called with an ordered list of pairs.
        repair: Recover a damaged document with :func:`repair` instead of
            raising. The returned value may be missing whatever the damage
            made unreadable. Cannot be combined with a custom decoder or
            hook, because repaired values bypass them.
        **kwargs: Additional keyword arguments passed to :func:`json.loads`.

    Returns:
        Deserialized Python object.

    Raises:
        JSONCDecodeError: If the text is not valid JSONC and ``repair`` is
            False.
        JSONRepairError: If ``repair`` is True and no value can be recovered.
        ValueError: If ``repair`` is True and a custom decoder or hook is
            given.
    """

    if not isinstance(text, str):
        raise TypeError(
            f"loads() requires str input, not {type(text).__name__}; "
            "decode bytes before calling it"
        )

    def _decode(s: str) -> Any:
        return json.loads(
            s,
            cls=cls,
            object_hook=object_hook,
            parse_float=parse_float,
            parse_int=parse_int,
            parse_constant=parse_constant,
            object_pairs_hook=object_pairs_hook,
            **kwargs,
        )

    # Fast path: JSON is a subset of JSONC, so a document that parses as
    # plain JSON needs no preprocessing — a successful json.loads is the
    # same answer. Only a failed parse pays for the comment scanner.
    #
    # A custom decoder or a caller hook opts out: the speculative parse would
    # otherwise invoke it on values the caller never receives, and then again
    # on the fallback parse.  A custom decoder may also accept JSONC itself,
    # in which case preprocessing must still run first.
    custom_parse = (
        cls is not None
        or object_hook is not None
        or object_pairs_hook is not None
        or parse_float is not None
        or parse_int is not None
        or parse_constant is not None
    )
    if repair and custom_parse:
        raise ValueError(
            "repair=True cannot be combined with a custom decoder or hook: "
            "repaired values bypass them"
        )
    if not custom_parse:
        try:
            return _decode(text)
        except json.JSONDecodeError as exc:
            cleaned = _preprocess(text)
            if cleaned == text:
                # Nothing JSONC to strip, so a retry would parse the same
                # document for the same result.  Report the failure exactly
                # as the pre-fast-path code did.
                if repair:
                    return _repair_document(text)[0]
                raise JSONCDecodeError(exc.msg, text, exc.pos) from None
    else:
        cleaned = _preprocess(text)

    try:
        return _decode(cleaned)
    except json.JSONDecodeError as exc:
        if repair:
            return _repair_document(text)[0]
        raise JSONCDecodeError(exc.msg, text, exc.pos) from None


def load(
    fp: IO[str],
    *,
    cls: type[json.JSONDecoder] | None = None,
    object_hook: Any = None,
    parse_float: Any = None,
    parse_int: Any = None,
    parse_constant: Any = None,
    object_pairs_hook: Any = None,
    **kwargs: Any,
) -> Any:
    """Deserialize a JSONC file to a Python object.

    Args:
        fp: A text file-like object containing JSONC.
        cls: Custom JSON decoder class.
        object_hook: Called with the result of any object literal decoded.
        parse_float: Called with every JSON float string decoded.
        parse_int: Called with every JSON int string decoded.
        parse_constant: Called with ``-Infinity``, ``Infinity``, ``NaN``.
        object_pairs_hook: Called with an ordered list of pairs.
        **kwargs: Additional keyword arguments passed to :func:`json.loads`.

    Returns:
        Deserialized Python object.

    Raises:
        JSONCDecodeError: If the content is not valid JSONC.
    """
    return loads(
        fp.read(),
        cls=cls,
        object_hook=object_hook,
        parse_float=parse_float,
        parse_int=parse_int,
        parse_constant=parse_constant,
        object_pairs_hook=object_pairs_hook,
        **kwargs,
    )


def dumps(
    obj: Any,
    *,
    skipkeys: bool = False,
    ensure_ascii: bool = True,
    check_circular: bool = True,
    allow_nan: bool = False,
    cls: type[json.JSONEncoder] | None = None,
    indent: int | str | None = None,
    separators: tuple[str, str] | None = None,
    default: Any = None,
    sort_keys: bool = False,
    **kwargs: Any,
) -> str:
    """Serialize a Python object to a JSON string.

    This is a pass-through to :func:`json.dumps` for API compatibility.

    Args:
        obj: Python object to serialize.
        skipkeys: Skip keys that are not basic types.
        ensure_ascii: Escape non-ASCII characters.
        check_circular: Check for circular references.
        allow_nan: Emit ``NaN``, ``Infinity`` and ``-Infinity`` as the bare
            constants. These are not valid JSON: ``JSON.parse``, Go's
            ``encoding/json`` and a strict parser reject the document. The
            default refuses them with :class:`ValueError`; opt in only when
            the consumer is known to accept Python's constants.
        cls: Custom JSON encoder class.
        indent: Indentation level for pretty-printing.
        separators: Item and key separators.
        default: Called for objects that are not serializable.
        sort_keys: Sort dictionary keys.
        **kwargs: Additional keyword arguments passed to :func:`json.dumps`.

    Returns:
        JSON string.
    """
    return json.dumps(
        obj,
        skipkeys=skipkeys,
        ensure_ascii=ensure_ascii,
        check_circular=check_circular,
        allow_nan=allow_nan,
        cls=cls,
        indent=indent,
        separators=separators,
        default=default,
        sort_keys=sort_keys,
        **kwargs,
    )


def dump(
    obj: Any,
    fp: IO[str],
    *,
    skipkeys: bool = False,
    ensure_ascii: bool = True,
    check_circular: bool = True,
    allow_nan: bool = False,
    cls: type[json.JSONEncoder] | None = None,
    indent: int | str | None = None,
    separators: tuple[str, str] | None = None,
    default: Any = None,
    sort_keys: bool = False,
    **kwargs: Any,
) -> None:
    """Serialize a Python object to a JSON file.

    This is a pass-through to :func:`json.dump` for API compatibility.

    Args:
        obj: Python object to serialize.
        fp: A text file-like object to write to.
        skipkeys: Skip keys that are not basic types.
        ensure_ascii: Escape non-ASCII characters.
        check_circular: Check for circular references.
        allow_nan: Emit ``NaN``, ``Infinity`` and ``-Infinity`` as the bare
            constants. These are not valid JSON: ``JSON.parse``, Go's
            ``encoding/json`` and a strict parser reject the document. The
            default refuses them with :class:`ValueError`; opt in only when
            the consumer is known to accept Python's constants.
        cls: Custom JSON encoder class.
        indent: Indentation level for pretty-printing.
        separators: Item and key separators.
        default: Called for objects that are not serializable.
        sort_keys: Sort dictionary keys.
        **kwargs: Additional keyword arguments passed to :func:`json.dump`.
    """
    json.dump(
        obj,
        fp,
        skipkeys=skipkeys,
        ensure_ascii=ensure_ascii,
        check_circular=check_circular,
        allow_nan=allow_nan,
        cls=cls,
        indent=indent,
        separators=separators,
        default=default,
        sort_keys=sort_keys,
        **kwargs,
    )


# ── JSONL (JSON Lines) API ────────────────────────────────────────────────────────────

# JSONL = one JSON value per line.  Each line is preprocessed through the
# JSONC comment/trailing-comma stripper, so "JSONL with comments" works
# out of the box.


def _is_blank_or_comment(line: str) -> bool:
    """Return *True* if *line* is empty or a pure-comment line."""
    s = line.strip()
    return s == "" or s.startswith("//") or s.startswith("#")


def loads_lines(
    text: str,
    **kwargs: Any,
) -> list[Any]:
    """Deserialize a JSONL string to a list of Python objects.

    Uses a batch fast-path for clean JSONL: non-empty lines are joined
    into a JSON array and parsed in a single :func:`json.loads` call,
    matching ``ndjson``-level performance.  If that fails (comments,
    trailing commas, etc.), falls back to per-line JSONC processing.

    A custom decoder or hook opts out of the batch fast-path, so the
    callback is never invoked on a speculative parse and a hook that raises
    :class:`json.JSONDecodeError` is not retried.

    Args:
        text: JSONL source string (one JSON value per line).
        **kwargs: Keyword arguments forwarded to :func:`json.loads`
            (or :func:`loads` on fallback).

    Returns:
        List of deserialized Python objects.

    Raises:
        JSONCDecodeError: If any line contains invalid JSON/JSONC.
    """
    lines = text.split("\n")
    stripped = [ln for ln in lines if ln.strip()]
    if not stripped:
        return []
    # A custom decoder or hook opts out of the batch parse: the speculative
    # attempt would invoke it on rows that parsed before the failure, and the
    # per-line fallback would invoke it again — including a hook that raised
    # JSONDecodeError to reject a value, whose refusal must not be retried.
    custom_parse = any(
        key in kwargs
        for key in (
            "cls",
            "object_hook",
            "object_pairs_hook",
            "parse_float",
            "parse_int",
            "parse_constant",
        )
    )
    _json_loads = json.loads
    if not custom_parse:
        # Fast path: join non-empty lines into a JSON array, single parse.
        # This avoids per-line Python overhead and lets the C json parser
        # handle everything in one call.
        try:
            return _json_loads("[" + ",".join(stripped) + "]", **kwargs)
        except json.JSONDecodeError:
            pass
    # Slow path: comments, trailing commas, or JSONC syntax present.
    results: list[Any] = []
    for line in lines:
        if _is_blank_or_comment(line):
            continue
        if custom_parse:
            # ``loads`` preprocesses before parsing, so callbacks see each
            # value exactly once even when the line is JSONC.
            results.append(loads(line, **kwargs))
            continue
        try:
            results.append(_json_loads(line, **kwargs))
        except json.JSONDecodeError:
            results.append(loads(line, **kwargs))
    return results


def load_lines(
    fp: IO[str],
    **kwargs: Any,
) -> list[Any]:
    """Deserialize a JSONL file to a list of Python objects.

    Args:
        fp: A text file-like object containing JSONL.
        **kwargs: Keyword arguments forwarded to :func:`loads`.

    Returns:
        List of deserialized Python objects.

    Raises:
        JSONCDecodeError: If any line contains invalid JSON/JSONC.
    """
    return loads_lines(fp.read(), **kwargs)


def dumps_lines(
    objects: list[Any],
    **kwargs: Any,
) -> str:
    """Serialize a list of Python objects to a JSONL string.

    Each object is serialized on its own line using :func:`json.dumps`.
    No trailing newline is emitted (consistent with ``"\\n".join(...)``
    semantics).

    Non-finite floats are refused, matching :func:`dumps`; pass
    ``allow_nan=True`` to emit Python's constants.

    Args:
        objects: Iterable of Python objects to serialize.
        **kwargs: Keyword arguments forwarded to :func:`json.dumps`.

    Returns:
        JSONL string (one JSON value per line).
    """
    kwargs.setdefault("allow_nan", False)
    return "\n".join(json.dumps(obj, **kwargs) for obj in objects)


def dump_lines(
    objects: list[Any],
    fp: IO[str],
    **kwargs: Any,
) -> None:
    """Serialize a list of Python objects to a JSONL file.

    Args:
        objects: Iterable of Python objects to serialize.
        fp: A text file-like object to write to.
        **kwargs: Keyword arguments forwarded to :func:`json.dumps`.
    """
    fp.write(dumps_lines(objects, **kwargs))
    fp.write("\n")
