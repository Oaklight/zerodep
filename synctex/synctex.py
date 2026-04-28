# /// zerodep
# version = "0.1.0"
# deps = []
# tier = "simple"
# category = "text"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///
"""SyncTeX parser for inverse search (PDF position -> source location).

Pure Python implementation using only the standard library.
Parses .synctex or .synctex.gz files produced by TeX engines with
``-synctex=1`` and provides spatial queries to map PDF coordinates
back to source file and line number.

Typical usage::

    data = parse_synctex("main.synctex.gz", strip_prefix="/workspace/")
    result = inverse_search(data, page=1, x=150.0, y=300.0)
    # result: {"file": "main.tex", "line": 42}

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.
"""

from __future__ import annotations

import gzip
import re
from dataclasses import dataclass, field

__all__ = [
    "SyncTeXData",
    "parse_synctex",
    "inverse_search",
]

# 1 TeX point = 65536 scaled points
# 1 inch = 72.27 TeX points = 72 PDF points (bp)
# So 1 bp = 72.27/72 pt = 1.00375 pt
_BP_TO_SP = 65536.0 * 72.27 / 72.0  # ≈ 65781.76


@dataclass
class HBox:
    """A horizontal box record from a SyncTeX file.

    Represents a line-level element with its source location and
    bounding box in scaled points.
    """

    tag: int
    line: int
    x: int  # left edge in scaled points
    y: int  # top edge in scaled points (from page top)
    width: int = 0
    height: int = 0
    depth: int = 0


@dataclass
class SyncTeXData:
    """Parsed SyncTeX data ready for spatial queries.

    Attributes:
        inputs: Mapping from file tag (int) to file path (str).
        pages: Mapping from 1-based page number to list of HBox records.
        magnification: TeX magnification factor (typically 1000).
        unit: Coordinate unit in scaled points (typically 1).
        x_offset: Horizontal offset in scaled points.
        y_offset: Vertical offset in scaled points.
    """

    inputs: dict[int, str] = field(default_factory=dict)
    pages: dict[int, list[HBox]] = field(default_factory=dict)
    magnification: int = 1000
    unit: int = 1
    x_offset: int = 0
    y_offset: int = 0


def parse_synctex(
    synctex_path: str,
    *,
    strip_prefix: str = "",
) -> SyncTeXData:
    """Parse a SyncTeX file (.synctex or .synctex.gz).

    Args:
        synctex_path: Path to the SyncTeX file.
        strip_prefix: Prefix to strip from input file paths.
            For Docker builds this is typically ``"/workspace/"``.

    Returns:
        Parsed SyncTeX data for use with :func:`inverse_search`.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be parsed.
    """
    content = _read_synctex(synctex_path)
    return _parse_content(content, strip_prefix=strip_prefix)


def inverse_search(
    data: SyncTeXData,
    page: int,
    x: float,
    y: float,
) -> dict[str, str | int] | None:
    """Find the source location for a point on a PDF page.

    Args:
        data: Parsed SyncTeX data from :func:`parse_synctex`.
        page: 1-based page number.
        x: Horizontal position in PDF points (72 DPI), from the left edge.
        y: Vertical position in PDF points (72 DPI), from the top edge.

    Returns:
        A dict ``{"file": "...", "line": N}`` on success, or ``None``
        if no matching source location is found.
    """
    boxes = data.pages.get(page)
    if not boxes:
        return None

    # Convert PDF points to scaled points
    scale = data.unit * data.magnification / 1000.0
    if scale == 0:
        scale = 1.0
    target_x = int(x * _BP_TO_SP / scale) + data.x_offset
    target_y = int(y * _BP_TO_SP / scale) + data.y_offset

    best = _find_closest_hbox(boxes, target_x, target_y)
    if best is None:
        return None

    file_path = data.inputs.get(best.tag)
    if file_path is None:
        return None

    return {"file": file_path, "line": best.line}


# -- Internal helpers ------------------------------------------------------


def _read_synctex(path: str) -> str:
    """Read a .synctex or .synctex.gz file and return its text content."""
    if path.endswith(".gz"):
        with gzip.open(path, "rt", errors="replace") as f:
            return f.read()
    with open(path, errors="replace") as f:
        return f.read()


_INPUT_RE = re.compile(r"^Input:(\d+):(.+)$")
_PAGE_OPEN_RE = re.compile(r"^\{(\d+)")
_PAGE_CLOSE_RE = re.compile(r"^\}(\d+)")
# Match hbox records: (tag,line:x,y:w,h,d  or  (tag,line:x,y
_HBOX_RE = re.compile(
    r"^\((\d+),(\d+):(-?\d+),(-?\d+)" r"(?::(-?\d+),(-?\d+),(-?\d+))?$"
)
# Match void hbox records: h tag,line:x,y:w,h,d
_VOID_HBOX_RE = re.compile(
    r"^h(\d+),(\d+):(-?\d+),(-?\d+)" r"(?::(-?\d+),(-?\d+),(-?\d+))?$"
)


def _parse_content(content: str, *, strip_prefix: str = "") -> SyncTeXData:
    """Parse the text content of a SyncTeX file."""
    data = SyncTeXData()
    current_page: int | None = None

    for raw_line in content.split("\n"):
        line = raw_line.rstrip("\r")

        # Preamble fields
        if line.startswith("Input:"):
            m = _INPUT_RE.match(line)
            if m:
                tag = int(m.group(1))
                path = _clean_path(m.group(2), strip_prefix)
                data.inputs[tag] = path
            continue

        if line.startswith("Magnification:"):
            try:
                data.magnification = int(line.split(":", 1)[1])
            except (ValueError, IndexError):
                pass
            continue

        if line.startswith("Unit:"):
            try:
                data.unit = int(line.split(":", 1)[1])
            except (ValueError, IndexError):
                pass
            continue

        if line.startswith("X Offset:"):
            try:
                data.x_offset = int(line.split(":", 1)[1])
            except (ValueError, IndexError):
                pass
            continue

        if line.startswith("Y Offset:"):
            try:
                data.y_offset = int(line.split(":", 1)[1])
            except (ValueError, IndexError):
                pass
            continue

        # Page boundaries
        m = _PAGE_OPEN_RE.match(line)
        if m:
            current_page = int(m.group(1))
            if current_page not in data.pages:
                data.pages[current_page] = []
            continue

        m = _PAGE_CLOSE_RE.match(line)
        if m:
            current_page = None
            continue

        if current_page is None:
            continue

        # HBox records (most useful for inverse search)
        hbox = _try_parse_hbox(line)
        if hbox is not None:
            data.pages[current_page].append(hbox)

    return data


def _try_parse_hbox(line: str) -> HBox | None:
    """Try to parse a line as an hbox or void hbox record."""
    m = _HBOX_RE.match(line)
    if m is None:
        m = _VOID_HBOX_RE.match(line)
    if m is None:
        return None

    tag = int(m.group(1))
    ln = int(m.group(2))
    x = int(m.group(3))
    y = int(m.group(4))
    w = int(m.group(5)) if m.group(5) else 0
    h = int(m.group(6)) if m.group(6) else 0
    d = int(m.group(7)) if m.group(7) else 0

    return HBox(tag=tag, line=ln, x=x, y=y, width=w, height=h, depth=d)


def _clean_path(path: str, strip_prefix: str) -> str:
    """Clean up a file path from a SyncTeX Input record.

    Strips the given prefix and normalizes ``./`` prefixes.
    """
    if strip_prefix and path.startswith(strip_prefix):
        path = path[len(strip_prefix) :]
    # Normalize leading ./
    while path.startswith("./"):
        path = path[2:]
    return path


def _find_closest_hbox(
    boxes: list[HBox],
    target_x: int,
    target_y: int,
) -> HBox | None:
    """Find the hbox closest to (target_x, target_y).

    Strategy:
    1. Collect hboxes whose vertical span contains target_y.
    2. Among those, prefer the smallest box that also contains target_x.
    3. If no containing box, pick the one with the nearest center.
    4. If no vertical match at all, pick the globally nearest box by
       vertical distance.
    """
    if not boxes:
        return None

    # Phase 1: boxes whose y-range contains target_y
    # A box spans from (y - height) to (y + depth) in synctex coords
    # where y is the baseline, height goes up, depth goes down.
    y_matches: list[HBox] = []
    for box in boxes:
        top = box.y - box.height
        bottom = box.y + box.depth
        if top <= target_y <= bottom:
            y_matches.append(box)

    if y_matches:
        # Phase 2: among y-matches, find containing box
        containing: list[HBox] = []
        for box in y_matches:
            if box.x <= target_x <= box.x + box.width:
                containing.append(box)

        if containing:
            # Pick the smallest containing box (most specific)
            return min(containing, key=lambda b: b.width * (b.height + b.depth))

        # Phase 3: nearest by horizontal distance among y-matches
        return min(y_matches, key=lambda b: _x_distance(b, target_x))

    # Phase 4: no vertical match -- find nearest by vertical distance
    return min(boxes, key=lambda b: _y_distance(b, target_y))


def _x_distance(box: HBox, target_x: int) -> int:
    """Horizontal distance from target_x to box's x-range."""
    if target_x < box.x:
        return box.x - target_x
    if target_x > box.x + box.width:
        return target_x - box.x - box.width
    return 0


def _y_distance(box: HBox, target_y: int) -> int:
    """Vertical distance from target_y to box's y-range."""
    top = box.y - box.height
    bottom = box.y + box.depth
    if target_y < top:
        return top - target_y
    if target_y > bottom:
        return target_y - bottom
    return 0
