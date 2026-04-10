# /// zerodep
# version = "0.1.0"
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
    rows: list[list[Any]]
    hdrs: list[str]

    # --- convert data to list-of-lists ---
    if isinstance(tabular_data, dict):
        keys = list(tabular_data.keys())
        vals = list(tabular_data.values())
        if vals and isinstance(vals[0], (list, tuple)):
            # dict of lists  →  columns
            col_lists: list[list[Any] | tuple[Any, ...]] = [
                v for v in vals if isinstance(v, (list, tuple))
            ]
            max_len = max((len(v) for v in col_lists), default=0)
            rows = []
            for i in range(max_len):
                rows.append([v[i] if i < len(v) else None for v in col_lists])
            if headers == "keys":
                hdrs = [str(k) for k in keys]
            elif isinstance(headers, (list, tuple)) and len(headers) > 0:
                hdrs = [str(h) for h in headers]
            else:
                hdrs = []
        else:
            # single dict  →  two-column table (key, value)
            rows = [[str(k), v] for k, v in tabular_data.items()]
            if headers == "keys":
                hdrs = ["keys", "values"]
            elif isinstance(headers, (list, tuple)) and len(headers) > 0:
                hdrs = [str(h) for h in headers]
            else:
                hdrs = []
    elif hasattr(tabular_data, "__iter__"):
        raw = list(tabular_data)
        if not raw:
            rows = []
            if isinstance(headers, (list, tuple)) and len(headers) > 0:
                hdrs = [str(h) for h in headers]
            else:
                hdrs = []
        elif isinstance(raw[0], dict):
            # list of dicts
            if headers == "keys":
                seen: dict[str, None] = {}
                for d in raw:
                    for k in d:
                        if k not in seen:
                            seen[k] = None
                hdrs = list(seen.keys())
            elif isinstance(headers, (list, tuple)) and len(headers) > 0:
                hdrs = [str(h) for h in headers]
            else:
                seen = {}
                for d in raw:
                    for k in d:
                        if k not in seen:
                            seen[k] = None
                hdrs = list(seen.keys())
            rows = [[d.get(k) for k in hdrs] for d in raw]
        else:
            # list of lists / tuples / iterables (always copy to avoid
            # mutating caller's data when showindex inserts values)
            rows = [list(r) for r in raw]
            if headers == "firstrow":
                if rows:
                    hdrs = [str(h) for h in rows[0]]
                    rows = rows[1:]
                else:
                    hdrs = []
            elif headers == "keys":
                hdrs = []
            elif isinstance(headers, (list, tuple)) and len(headers) > 0:
                hdrs = [str(h) for h in headers]
            else:
                hdrs = []
    else:
        rows = []
        hdrs = []

    # --- showindex ---
    if showindex is not False:
        if isinstance(showindex, (list, tuple)):
            indices: Sequence = showindex
        elif isinstance(showindex, str) and showindex != "":
            indices = list(range(len(rows)))
        else:
            indices = list(range(len(rows)))
        for i, row in enumerate(rows):
            idx = indices[i] if i < len(indices) else ""
            row.insert(0, idx)
        if hdrs:
            hdrs.insert(0, "")

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
        eff_numalign = "center"
        eff_stralign = "center"
    else:
        eff_numalign = numalign if numalign else "decimal"
        eff_stralign = stralign if stralign else "left"

    # 1. Normalise data
    rows, hdrs = _normalise_tabular_data(tabular_data, headers, showindex)

    # 2. Format every cell as string
    str_rows: list[list[str]] = []
    for row in rows:
        str_row: list[str] = []
        for v in row:
            str_row.append(_format_number(v, floatfmt, missingval))
        str_rows.append(str_row)

    str_hdrs = list(hdrs)

    # 3. Equalise column count.
    # ncols is driven by data rows; headers are truncated/padded to match.
    ncols = 0
    for row in str_rows:
        ncols = max(ncols, len(row))
    # If there are no data rows, fall back to header count.
    if ncols == 0 and str_hdrs:
        ncols = len(str_hdrs)
    for row in str_rows:
        while len(row) < ncols:
            row.append(missingval)
    if str_hdrs:
        # Truncate extra headers beyond data columns
        str_hdrs = str_hdrs[:ncols]
        # Pad if data has more columns than headers
        while len(str_hdrs) < ncols:
            str_hdrs.append("")

    if ncols == 0:
        return ""

    # 4. Determine per-column alignment
    aligns: list[str] = []
    for col in range(ncols):
        if colalign and col < len(colalign) and colalign[col]:
            aligns.append(colalign[col])
        else:
            ctype = _column_type(rows, col)
            if ctype == "number":
                aligns.append(eff_numalign)
            else:
                aligns.append(eff_stralign)

    # 5. Compute column widths
    has_headers = bool(str_hdrs)
    colwidths: list[int] = [0] * ncols
    for col in range(ncols):
        cells = [row[col] if col < len(row) else "" for row in str_rows]

        if aligns[col] == "decimal":
            # Decimal-aligned width = max(before_dot) + max(after_dot)
            data_max = _decimal_column_width(cells)
        else:
            data_max = max((_visible_width(c) for c in cells), default=0)

        if has_headers:
            hdr_w = _visible_width(str_hdrs[col])
            if fmt.header_pad_width:
                colwidths[col] = max(data_max, hdr_w + _HEADER_MIN_PAD)
            else:
                colwidths[col] = max(data_max, hdr_w)
        else:
            colwidths[col] = data_max

    # Headers use the same alignment as data columns, except "decimal"
    # columns use "right" for headers (can't decimal-align a text header).
    header_aligns = ["right" if a == "decimal" else a for a in aligns]

    # 6. Pre-align data cells per column (needed for decimal alignment).
    # After this step, each cell string is padded to its column width.
    for col in range(ncols):
        col_cells = [row[col] if col < len(row) else "" for row in str_rows]
        align = aligns[col]
        w = colwidths[col]
        if align == "decimal":
            aligned = _align_decimal(col_cells, w)
        else:
            aligned = [_pad(c, w, align) for c in col_cells]
        for ri, row in enumerate(str_rows):
            if col < len(row):
                row[col] = aligned[ri]

    # Also pre-align headers
    if has_headers:
        for col in range(ncols):
            align = header_aligns[col]
            w = colwidths[col]
            str_hdrs[col] = _pad(str_hdrs[col], w, align)

    # 7. Build the table
    padding = fmt.padding

    lines: list[str] = []

    # Decide which structural elements to show.
    # with_header_hide: elements to HIDE when headers ARE present.
    show_lineabove = fmt.lineabove is not None
    show_linebelow = fmt.linebelow is not None

    if has_headers:
        if "lineabove" in fmt.with_header_hide:
            show_lineabove = False
        if "linebelow" in fmt.with_header_hide:
            show_linebelow = False

    # line above
    if show_lineabove and fmt.lineabove is not None:
        lines.append(_build_line(colwidths, fmt.lineabove, padding))

    # header row
    if has_headers and fmt.headerrow is not None:
        lines.append(_build_simple_row(str_hdrs, fmt.headerrow, padding))

    # line below header (pipe/github always show the separator)
    show_header_sep = has_headers and fmt.linebelowheader is not None
    if (
        not has_headers
        and tablefmt in ("pipe", "github")
        and fmt.linebelowheader is not None
    ):
        show_header_sep = True
    if show_header_sep and fmt.linebelowheader is not None:
        if tablefmt == "pipe":
            lines.append(
                _build_pipe_separator(colwidths, aligns, fmt.linebelowheader, padding)
            )
        else:
            lines.append(_build_line(colwidths, fmt.linebelowheader, padding))

    # data rows
    for i, row in enumerate(str_rows):
        if fmt.datarow is not None:
            lines.append(_build_simple_row(row, fmt.datarow, padding))
        if fmt.linebetweenrows is not None and i < len(str_rows) - 1:
            lines.append(_build_line(colwidths, fmt.linebetweenrows, padding))

    # line below
    if show_linebelow and fmt.linebelow is not None:
        lines.append(_build_line(colwidths, fmt.linebelow, padding))

    return "\n".join(line.rstrip() for line in lines)


# ── Module-level convenience ─────────────────────────────────────────────────

# Expose format names for introspection.
tabulate_formats: list[str] = sorted(_table_formats.keys())

__all__ = ["tabulate", "tabulate_formats", "WIDE_CHARS_MODE"]
