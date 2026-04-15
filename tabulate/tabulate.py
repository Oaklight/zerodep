# /// zerodep
# version = "0.1.1"
# deps = []
# tier = "medium"
# category = "terminal"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///

"""Tabulate — zero dependencies, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Pretty-print tabular data as formatted text tables.  Supports multiple
output formats (plain, simple, grid, pipe, github, orgtbl, pretty),
flexible header modes, column alignment, number formatting, CJK-aware
column widths, and various input data shapes.

Example::

    from tabulate import tabulate

    data = [["Alice", 24], ["Bob", 30]]
    print(tabulate(data, headers=["Name", "Age"], tablefmt="grid"))
    # +--------+-------+
    # | Name   |   Age |
    # +========+=======+
    # | Alice  |    24 |
    # | Bob    |    30 |
    # +--------+-------+
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Sequence

# ── Configuration ────────────────────────────────────────────────────────────

# When True, CJK / East Asian wide characters are counted as width 2.
# When False (default, matches reference tabulate), len(s) is used.
WIDE_CHARS_MODE: bool = False

# ── CJK / visible-width helpers ──────────────────────────────────────────────


def _visible_width(s: str) -> int:
    """Return the visible width of *s*, counting CJK / wide chars as 2.

    This function respects the ``WIDE_CHARS_MODE`` flag.  When the flag is
    ``False`` (the default, matching the reference *tabulate* library),
    width equals ``len(s)``.
    """
    if not WIDE_CHARS_MODE:
        return len(s)
    w = 0
    for ch in s:
        eaw = unicodedata.east_asian_width(ch)
        if eaw in ("W", "F"):
            w += 2
        else:
            w += 1
    return w


def _pad(s: str, width: int, align: str) -> str:
    """Pad string *s* to *width* columns using alignment *align*.

    Args:
        s: The string to pad.
        width: Target width (character or visible depending on mode).
        align: One of ``"left"``, ``"right"``, ``"center"``.

    Returns:
        The padded string.
    """
    vw = _visible_width(s)
    diff = width - vw
    if diff <= 0:
        return s
    if align == "right":
        return " " * diff + s
    if align == "center":
        left = diff // 2
        right = diff - left
        return " " * left + s + " " * right
    # default: left
    return s + " " * diff


# ── Table format definitions ─────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class TableFormat:
    """Defines the line/border/separator characters for one table style."""

    lineabove: _Line | None = None
    linebelowheader: _Line | None = None
    linebetweenrows: _Line | None = None
    linebelow: _Line | None = None
    headerrow: _DataRow | None = None
    datarow: _DataRow | None = None
    padding: int = 0
    with_header_hide: list[str] = field(default_factory=list)
    # When True, column width = max(data_max, header_width + MIN_PADDING)
    # When False (pretty), column width = max(data_max, header_width)
    header_pad_width: bool = True


@dataclass(frozen=True, slots=True)
class _Line:
    begin: str = ""
    hline: str = ""
    sep: str = ""
    end: str = ""


@dataclass(frozen=True, slots=True)
class _DataRow:
    begin: str = ""
    sep: str = ""
    end: str = ""


# Minimum extra padding added to header width when computing column widths
# (applies to all formats except pretty).
_HEADER_MIN_PAD = 2

# ── Built-in table formats ───────────────────────────────────────────────────

_table_formats: dict[str, TableFormat] = {
    "plain": TableFormat(
        datarow=_DataRow("", "  ", ""),
        headerrow=_DataRow("", "  ", ""),
    ),
    "simple": TableFormat(
        lineabove=_Line("", "-", "  ", ""),
        linebelowheader=_Line("", "-", "  ", ""),
        linebelow=_Line("", "-", "  ", ""),
        headerrow=_DataRow("", "  ", ""),
        datarow=_DataRow("", "  ", ""),
        with_header_hide=["lineabove", "linebelow"],
    ),
    "grid": TableFormat(
        lineabove=_Line("+", "-", "+", "+"),
        linebelowheader=_Line("+", "=", "+", "+"),
        linebetweenrows=_Line("+", "-", "+", "+"),
        linebelow=_Line("+", "-", "+", "+"),
        headerrow=_DataRow("|", "|", "|"),
        datarow=_DataRow("|", "|", "|"),
        padding=1,
    ),
    "pipe": TableFormat(
        linebelowheader=_Line("|", "-", "|", "|"),
        headerrow=_DataRow("|", "|", "|"),
        datarow=_DataRow("|", "|", "|"),
        padding=1,
    ),
    "orgtbl": TableFormat(
        linebelowheader=_Line("|", "-", "+", "|"),
        headerrow=_DataRow("|", "|", "|"),
        datarow=_DataRow("|", "|", "|"),
        padding=1,
    ),
    "pretty": TableFormat(
        lineabove=_Line("+", "-", "+", "+"),
        linebelowheader=_Line("+", "-", "+", "+"),
        linebelow=_Line("+", "-", "+", "+"),
        headerrow=_DataRow("|", "|", "|"),
        datarow=_DataRow("|", "|", "|"),
        padding=1,
        header_pad_width=False,
    ),
    "github": TableFormat(
        linebelowheader=_Line("|", "-", "|", "|"),
        headerrow=_DataRow("|", "|", "|"),
        datarow=_DataRow("|", "|", "|"),
        padding=1,
    ),
}

# ── Number detection & formatting ────────────────────────────────────────────

_NUMERIC_RE = re.compile(
    r"""
    ^
    [+-]?
    (?:
        \d+\.?\d*       # integer or decimal
        | \.\d+         # .NNN
    )
    (?:[eE][+-]?\d+)?   # optional exponent
    $
    """,
    re.VERBOSE,
)


def _isnumber(v: Any) -> bool:
    """Return True if *v* is numeric (int, float, or numeric string)."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return True
    if isinstance(v, str):
        return bool(_NUMERIC_RE.match(v.strip()))
    return False


def _format_number(v: Any, floatfmt: str, missingval: str) -> str:
    """Format a single value for display.

    Args:
        v: The value to format.
        floatfmt: Format spec for floats (e.g. ``"g"``, ``".2f"``).
        missingval: Replacement for ``None``.

    Returns:
        Formatted string representation.
    """
    if v is None:
        return missingval
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, str):
        return v
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if math.isinf(v):
            return "inf" if v > 0 else "-inf"
        if math.isnan(v):
            return "nan"
        return format(v, floatfmt)
    return str(v)


# ── Data normalisation ───────────────────────────────────────────────────────


def _resolve_headers(
    headers: Any,
    keys_default: list[str],
) -> list[str]:
    """Return resolved header list from a header spec and a default.

    Args:
        headers: ``"keys"`` to use *keys_default*, a list/tuple to use
            directly, or anything else for no headers.
        keys_default: Headers to use when *headers* is ``"keys"``.

    Returns:
        Resolved header strings.
    """
    if headers == "keys":
        return keys_default
    if isinstance(headers, (list, tuple)) and len(headers) > 0:
        return [str(h) for h in headers]
    return []


def _rows_from_dict(
    tabular_data: dict,
    headers: Any,
) -> tuple[list[list[Any]], list[str]]:
    """Normalise a dict into rows and headers.

    Handles two sub-cases: dict-of-lists (columnar) and single dict
    (key-value pairs).

    Args:
        tabular_data: A dict.
        headers: Header specification.

    Returns:
        Tuple of (rows, headers).
    """
    keys = list(tabular_data.keys())
    vals = list(tabular_data.values())
    if vals and isinstance(vals[0], (list, tuple)):
        return _rows_from_dict_of_lists(keys, vals, headers)
    # single dict → two-column table (key, value)
    rows = [[str(k), v] for k, v in tabular_data.items()]
    hdrs = _resolve_headers(headers, ["keys", "values"])
    return rows, hdrs


def _rows_from_dict_of_lists(
    keys: list,
    vals: list,
    headers: Any,
) -> tuple[list[list[Any]], list[str]]:
    """Convert dict-of-lists (columnar) into rows.

    Args:
        keys: Dict keys (column names).
        vals: Dict values (column data lists).
        headers: Header specification.

    Returns:
        Tuple of (rows, headers).
    """
    col_lists: list[list[Any] | tuple[Any, ...]] = [
        v for v in vals if isinstance(v, (list, tuple))
    ]
    max_len = max((len(v) for v in col_lists), default=0)
    rows = [[v[i] if i < len(v) else None for v in col_lists] for i in range(max_len)]
    hdrs = _resolve_headers(headers, [str(k) for k in keys])
    return rows, hdrs


def _unique_keys_from_dicts(raw: list[dict]) -> list[str]:
    """Return ordered unique keys across a list of dicts.

    Args:
        raw: List of dicts.

    Returns:
        Unique keys in insertion order.
    """
    seen: dict[str, None] = {}
    for d in raw:
        for k in d:
            if k not in seen:
                seen[k] = None
    return list(seen.keys())


def _rows_from_list_of_dicts(
    raw: list[dict],
    headers: Any,
) -> tuple[list[list[Any]], list[str]]:
    """Convert a list of dicts into rows and headers.

    Args:
        raw: List of dicts.
        headers: Header specification.

    Returns:
        Tuple of (rows, headers).
    """
    unique_keys = _unique_keys_from_dicts(raw)
    if isinstance(headers, (list, tuple)) and len(headers) > 0:
        hdrs = [str(h) for h in headers]
    else:
        hdrs = unique_keys
    rows = [[d.get(k) for k in hdrs] for d in raw]
    return rows, hdrs


def _rows_from_list_of_lists(
    raw: list,
    headers: Any,
) -> tuple[list[list[Any]], list[str]]:
    """Convert a list of lists/tuples into rows and headers.

    Args:
        raw: List of lists/tuples/iterables.
        headers: Header specification.

    Returns:
        Tuple of (rows, headers).
    """
    rows = [list(r) for r in raw]
    if headers == "firstrow":
        if rows:
            hdrs = [str(h) for h in rows[0]]
            rows = rows[1:]
        else:
            hdrs = []
        return rows, hdrs
    hdrs = _resolve_headers(headers, [])
    return rows, hdrs


def _apply_showindex(
    rows: list[list[Any]],
    hdrs: list[str],
    showindex: bool | str | Sequence,
) -> None:
    """Prepend index column to *rows* and *hdrs* in-place.

    Args:
        rows: Data rows (mutated).
        hdrs: Header list (mutated).
        showindex: Index specification.
    """
    if showindex is False:
        return
    if isinstance(showindex, (list, tuple)):
        indices: Sequence = showindex
    else:
        indices = list(range(len(rows)))
    for i, row in enumerate(rows):
        idx = indices[i] if i < len(indices) else ""
        row.insert(0, idx)
    if hdrs:
        hdrs.insert(0, "")


def _normalise_tabular_data(
    tabular_data: Any,
    headers: Any,
    showindex: bool | str | Sequence,
) -> tuple[list[list[Any]], list[str]]:
    """Convert arbitrary tabular data + headers into (rows, headers).

    Args:
        tabular_data: Input data in any supported shape.
        headers: Header specification.
        showindex: Whether/how to show row indices.

    Returns:
        Tuple of (rows as list-of-lists of raw values, header strings).
    """
    if isinstance(tabular_data, dict):
        rows, hdrs = _rows_from_dict(tabular_data, headers)
    elif hasattr(tabular_data, "__iter__"):
        raw = list(tabular_data)
        if not raw:
            rows, hdrs = [], _resolve_headers(headers, [])
        elif isinstance(raw[0], dict):
            rows, hdrs = _rows_from_list_of_dicts(raw, headers)
        else:
            rows, hdrs = _rows_from_list_of_lists(raw, headers)
    else:
        rows, hdrs = [], []

    _apply_showindex(rows, hdrs, showindex)
    return rows, hdrs


# ── Column type detection ────────────────────────────────────────────────────


def _column_type(raw_rows: list[list[Any]], col: int) -> str:
    """Detect whether column *col* is numeric or text from raw values.

    Checks the original (pre-formatting) values. ``None`` and empty strings
    are skipped so that missing values do not affect the column type.

    Returns ``"number"`` if all non-empty, non-None cells are numeric,
    otherwise ``"text"``.
    """
    for row in raw_rows:
        if col < len(row):
            v = row[col]
            if v is None or v == "":
                continue
            if not _isnumber(v):
                return "text"
    return "number"


# ── Alignment helpers ────────────────────────────────────────────────────────


def _align_decimal(formatted: list[str], width: int) -> list[str]:
    """Align on the decimal point (or end-of-integer).

    Values are shifted so that decimal points line up, then the whole
    block is right-aligned within *width*.
    """
    dot_positions: list[int] = []
    for s in formatted:
        pos = s.find(".")
        if pos < 0:
            pos = _visible_width(s)
        dot_positions.append(pos)
    max_dot = max(dot_positions) if dot_positions else 0

    # Compute the natural width after decimal alignment (max shifted width).
    aligned_strs: list[str] = []
    for s, dp in zip(formatted, dot_positions):
        leading = max_dot - dp
        aligned_strs.append(" " * leading + s)

    natural_width = max((_visible_width(a) for a in aligned_strs), default=0)

    # Right-align the aligned block within *width*.
    extra = max(0, width - natural_width)
    result: list[str] = []
    for a in aligned_strs:
        padded = " " * extra + a
        padded = _pad(padded, width, "left")
        result.append(padded)
    return result


def _decimal_column_width(cells: list[str]) -> int:
    """Compute the column width needed for decimal-aligned *cells*.

    The width equals ``max(before_dot) + max(after_dot_including_dot)``
    so that the decimal points line up vertically.

    Args:
        cells: Formatted cell strings.

    Returns:
        Required column width.
    """
    if not cells:
        return 0
    max_before = 0
    max_after = 0
    for s in cells:
        if not s:
            continue
        dot = s.find(".")
        if dot >= 0:
            before = _visible_width(s[:dot])
            after = _visible_width(s[dot:])
        else:
            before = _visible_width(s)
            after = 0
        max_before = max(max_before, before)
        max_after = max(max_after, after)
    return max_before + max_after


# ── Separator / data-row building ────────────────────────────────────────────


def _build_line(
    colwidths: list[int],
    line: _Line,
    padding: int,
) -> str:
    """Build a horizontal separator line.

    Args:
        colwidths: Column widths (visible chars, not counting padding).
        line: Line characters.
        padding: Padding on each side of each column.

    Returns:
        The constructed line string.
    """
    segments = [line.hline * (w + 2 * padding) for w in colwidths]
    return line.begin + line.sep.join(segments) + line.end


def _build_simple_row(
    cells: list[str],
    row_spec: _DataRow,
    padding: int,
) -> str:
    """Build a row from pre-aligned cell strings.

    Args:
        cells: Pre-aligned cell strings (already padded to column width).
        row_spec: Row border characters.
        padding: Padding on each side.

    Returns:
        The constructed row string.
    """
    pad_str = " " * padding
    padded = [pad_str + cell + pad_str for cell in cells]
    return row_spec.begin + row_spec.sep.join(padded) + row_spec.end


# ── Pipe / GitHub alignment markers ─────────────────────────────────────────


def _build_pipe_separator(
    colwidths: list[int],
    aligns: list[str],
    line: _Line,
    padding: int,
) -> str:
    """Build the header-separator for pipe format with alignment markers.

    Args:
        colwidths: Column widths.
        aligns: Per-column alignment.
        line: Line characters.
        padding: Padding value.

    Returns:
        The pipe-style separator string.
    """
    segments: list[str] = []
    for i, w in enumerate(colwidths):
        align = aligns[i] if i < len(aligns) else "left"
        total = w + 2 * padding
        if align in ("right", "decimal"):
            seg = line.hline * (total - 1) + ":"
        elif align == "center":
            seg = ":" + line.hline * (total - 2) + ":"
        else:
            # left or default
            seg = ":" + line.hline * (total - 1)
        segments.append(seg)
    return line.begin + line.sep.join(segments) + line.end


# ── Tabulate helpers ────────────────────────────────────────────────────────


def _format_cells(
    rows: list[list[Any]],
    floatfmt: str,
    missingval: str,
) -> list[list[str]]:
    """Format every cell in *rows* as a display string.

    Args:
        rows: Raw data rows.
        floatfmt: Format spec for floats.
        missingval: Replacement for ``None``.

    Returns:
        List of lists of formatted strings.
    """
    return [[_format_number(v, floatfmt, missingval) for v in row] for row in rows]


def _equalise_columns(
    str_rows: list[list[str]],
    str_hdrs: list[str],
    missingval: str,
) -> tuple[list[str], int]:
    """Ensure all rows and headers have the same column count.

    *str_rows* is mutated in place. Returns the (possibly truncated/padded)
    header list and the total column count.

    Args:
        str_rows: Formatted data rows (mutated).
        str_hdrs: Header strings.
        missingval: Fill value for short rows.

    Returns:
        Tuple of (adjusted headers, ncols).
    """
    ncols = max((len(row) for row in str_rows), default=0)
    if ncols == 0 and str_hdrs:
        ncols = len(str_hdrs)
    for row in str_rows:
        while len(row) < ncols:
            row.append(missingval)
    if str_hdrs:
        str_hdrs = str_hdrs[:ncols]
        while len(str_hdrs) < ncols:
            str_hdrs.append("")
    return str_hdrs, ncols


def _determine_alignments(
    raw_rows: list[list[Any]],
    ncols: int,
    colalign: Sequence[str] | None,
    eff_numalign: str,
    eff_stralign: str,
) -> list[str]:
    """Determine per-column alignment.

    Args:
        raw_rows: Original (pre-format) rows for type detection.
        ncols: Number of columns.
        colalign: Per-column alignment overrides (may be ``None``).
        eff_numalign: Default alignment for numeric columns.
        eff_stralign: Default alignment for text columns.

    Returns:
        List of alignment strings, one per column.
    """
    aligns: list[str] = []
    for col in range(ncols):
        if colalign and col < len(colalign) and colalign[col]:
            aligns.append(colalign[col])
        elif _column_type(raw_rows, col) == "number":
            aligns.append(eff_numalign)
        else:
            aligns.append(eff_stralign)
    return aligns


def _compute_column_widths(
    str_rows: list[list[str]],
    str_hdrs: list[str],
    aligns: list[str],
    ncols: int,
    fmt: TableFormat,
) -> list[int]:
    """Compute the display width of each column.

    Args:
        str_rows: Formatted data rows.
        str_hdrs: Header strings.
        aligns: Per-column alignment.
        ncols: Number of columns.
        fmt: Table format (controls header padding).

    Returns:
        List of column widths.
    """
    has_headers = bool(str_hdrs)
    colwidths: list[int] = [0] * ncols
    for col in range(ncols):
        cells = [row[col] if col < len(row) else "" for row in str_rows]
        if aligns[col] == "decimal":
            data_max = _decimal_column_width(cells)
        else:
            data_max = max((_visible_width(c) for c in cells), default=0)
        if has_headers:
            hdr_w = _visible_width(str_hdrs[col])
            pad = _HEADER_MIN_PAD if fmt.header_pad_width else 0
            colwidths[col] = max(data_max, hdr_w + pad)
        else:
            colwidths[col] = data_max
    return colwidths


def _align_all_cells(
    str_rows: list[list[str]],
    str_hdrs: list[str],
    aligns: list[str],
    colwidths: list[int],
    ncols: int,
) -> None:
    """Pad every data cell and header to its column width in place.

    Args:
        str_rows: Formatted data rows (mutated).
        str_hdrs: Header strings (mutated).
        aligns: Per-column alignment.
        colwidths: Column widths.
        ncols: Number of columns.
    """
    header_aligns = ["right" if a == "decimal" else a for a in aligns]

    for col in range(ncols):
        col_cells = [row[col] if col < len(row) else "" for row in str_rows]
        w = colwidths[col]
        if aligns[col] == "decimal":
            aligned = _align_decimal(col_cells, w)
        else:
            aligned = [_pad(c, w, aligns[col]) for c in col_cells]
        for ri, row in enumerate(str_rows):
            if col < len(row):
                row[col] = aligned[ri]

    if str_hdrs:
        for col in range(ncols):
            str_hdrs[col] = _pad(str_hdrs[col], colwidths[col], header_aligns[col])


def _build_table_lines(
    str_rows: list[list[str]],
    str_hdrs: list[str],
    aligns: list[str],
    colwidths: list[int],
    fmt: TableFormat,
    tablefmt: str,
) -> list[str]:
    """Assemble all table lines (borders, headers, data rows).

    Args:
        str_rows: Pre-aligned data rows.
        str_hdrs: Pre-aligned header strings.
        aligns: Per-column alignment.
        colwidths: Column widths.
        fmt: Table format definition.
        tablefmt: Format name (for pipe/github special-casing).

    Returns:
        List of line strings (not yet stripped).
    """
    has_headers = bool(str_hdrs)
    padding = fmt.padding
    lines: list[str] = []

    # Decide which structural elements to show.
    show_lineabove = fmt.lineabove is not None and not (
        has_headers and "lineabove" in fmt.with_header_hide
    )
    show_linebelow = fmt.linebelow is not None and not (
        has_headers and "linebelow" in fmt.with_header_hide
    )

    if show_lineabove and fmt.lineabove is not None:
        lines.append(_build_line(colwidths, fmt.lineabove, padding))

    if has_headers and fmt.headerrow is not None:
        lines.append(_build_simple_row(str_hdrs, fmt.headerrow, padding))

    _append_header_separator(lines, has_headers, tablefmt, fmt, colwidths, aligns)

    for i, row in enumerate(str_rows):
        if fmt.datarow is not None:
            lines.append(_build_simple_row(row, fmt.datarow, padding))
        if fmt.linebetweenrows is not None and i < len(str_rows) - 1:
            lines.append(_build_line(colwidths, fmt.linebetweenrows, padding))

    if show_linebelow and fmt.linebelow is not None:
        lines.append(_build_line(colwidths, fmt.linebelow, padding))

    return lines


def _append_header_separator(
    lines: list[str],
    has_headers: bool,
    tablefmt: str,
    fmt: TableFormat,
    colwidths: list[int],
    aligns: list[str],
) -> None:
    """Append the header separator line to *lines* if applicable.

    Args:
        lines: Accumulator list (mutated).
        has_headers: Whether headers are present.
        tablefmt: Format name.
        fmt: Table format definition.
        colwidths: Column widths.
        aligns: Per-column alignment.
    """
    if fmt.linebelowheader is None:
        return
    show = has_headers or tablefmt in ("pipe", "github")
    if not show:
        return
    if tablefmt == "pipe":
        lines.append(
            _build_pipe_separator(colwidths, aligns, fmt.linebelowheader, fmt.padding)
        )
    else:
        lines.append(_build_line(colwidths, fmt.linebelowheader, fmt.padding))


# ── Public API ───────────────────────────────────────────────────────────────


def tabulate(
    tabular_data: Any,
    headers: Any = (),
    tablefmt: str = "simple",
    floatfmt: str = "g",
    numalign: str = "decimal",
    stralign: str = "left",
    missingval: str = "",
    showindex: bool | str | Sequence = False,
    colalign: Sequence[str] | None = None,
) -> str:
    """Format tabular data as a pretty-printed text table.

    Args:
        tabular_data: Input data.  Accepted shapes: list of lists, list of
            dicts, dict of lists/values, or any iterable of iterables.
        headers: Column headers.  Can be a list/tuple of strings,
            ``"firstrow"`` (use first data row), ``"keys"`` (use dict keys
            or column indices), or an empty tuple for no headers.
        tablefmt: Output format name — one of ``"plain"``, ``"simple"``,
            ``"grid"``, ``"pipe"``, ``"orgtbl"``, ``"pretty"``, ``"github"``.
        floatfmt: Format string for float values (passed to ``format()``).
        numalign: Default alignment for numeric columns (``"right"``,
            ``"left"``, ``"center"``, ``"decimal"``).
        stralign: Default alignment for text columns.
        missingval: String to display in place of ``None``.
        showindex: If truthy, prepend row indices.  Can be ``True``,
            ``"always"``, or a sequence of explicit index values.
        colalign: Per-column alignment overrides.

    Returns:
        The formatted table as a string.

    Raises:
        ValueError: If *tablefmt* is not recognised.

    Example::

        data = [["Alice", 24], ["Bob", 30]]
        print(tabulate(data, headers=["Name", "Age"]))
        # Name      Age
        # ------  -----
        # Alice      24
        # Bob        30
    """
    if tablefmt not in _table_formats:
        raise ValueError(
            f"Unknown table format {tablefmt!r}. "
            f"Supported: {', '.join(sorted(_table_formats))}"
        )

    fmt = _table_formats[tablefmt]

    # Effective alignment defaults for pretty format (center everything)
    if tablefmt == "pretty":
        eff_numalign, eff_stralign = "center", "center"
    else:
        eff_numalign = numalign if numalign else "decimal"
        eff_stralign = stralign if stralign else "left"

    # 1. Normalise data
    rows, hdrs = _normalise_tabular_data(tabular_data, headers, showindex)

    # 2. Format every cell as string
    str_rows = _format_cells(rows, floatfmt, missingval)
    str_hdrs = list(hdrs)

    # 3. Equalise column count
    str_hdrs, ncols = _equalise_columns(str_rows, str_hdrs, missingval)
    if ncols == 0:
        return ""

    # 4. Determine per-column alignment
    aligns = _determine_alignments(rows, ncols, colalign, eff_numalign, eff_stralign)

    # 5. Compute column widths
    colwidths = _compute_column_widths(str_rows, str_hdrs, aligns, ncols, fmt)

    # 6. Pre-align all cells and headers
    _align_all_cells(str_rows, str_hdrs, aligns, colwidths, ncols)

    # 7. Build and return the table
    lines = _build_table_lines(str_rows, str_hdrs, aligns, colwidths, fmt, tablefmt)
    return "\n".join(line.rstrip() for line in lines)


# ── Module-level convenience ─────────────────────────────────────────────────

# Expose format names for introspection.
tabulate_formats: list[str] = sorted(_table_formats.keys())

__all__ = ["tabulate", "tabulate_formats", "WIDE_CHARS_MODE"]
