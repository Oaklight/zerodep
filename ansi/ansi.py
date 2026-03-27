"""ANSI escape code primitives for terminal styling.

Zero dependencies, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Provides named colors, text attributes, 256-color and 24-bit true-color
support, terminal capability detection, and utility helpers for stripping
escape sequences and measuring visible text width.

Quick styling::

    from ansi import style
    print(style("Error!", fg="red", bold=True))
    print(style("Success", fg="green", bg="black", italic=True))

Programmatic color construction::

    from ansi import fg, bg, BOLD, RESET
    print(f"{BOLD}{fg('blue')}hello{RESET}")
    print(f"{fg('#ff8800')}orange text{RESET}")
    print(f"{fg(214)}256-color{RESET}")
    print(f"{bg(55)}{fg('white')}white on purple{RESET}")

Terminal detection::

    from ansi import supports_color, color_depth
    if supports_color():
        depth = color_depth()  # 16, 256, or 16777216
"""

from __future__ import annotations

import os
import re
import sys

# ── Text Attributes ─────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
REVERSE = "\033[7m"
HIDDEN = "\033[8m"
STRIKETHROUGH = "\033[9m"

# ── Cursor Control ──────────────────────────────────────────────────

CURSOR_UP = "\033[A"
CURSOR_DOWN = "\033[B"
CURSOR_FORWARD = "\033[C"
CURSOR_BACK = "\033[D"
CURSOR_HIDE = "\033[?25l"
CURSOR_SHOW = "\033[?25h"
CLEAR_LINE = "\033[K"
CLEAR_SCREEN = "\033[2J"
CURSOR_HOME = "\033[H"

# ── Named Colors ────────────────────────────────────────────────────

# Standard 8 colors — foreground SGR codes (add 10 for background).
NAMED_COLORS: dict[str, int] = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
}

# Bright variants — foreground SGR codes (add 10 for background).
BRIGHT_COLORS: dict[str, int] = {
    "bright_black": 90,
    "bright_red": 91,
    "bright_green": 92,
    "bright_yellow": 93,
    "bright_blue": 94,
    "bright_magenta": 95,
    "bright_cyan": 96,
    "bright_white": 97,
}

# Merged lookup for all named colors.
_ALL_COLORS: dict[str, int] = {**NAMED_COLORS, **BRIGHT_COLORS}

# ── Color Constructors ──────────────────────────────────────────────


def _parse_color(
    color: str | int | tuple[int, int, int],
    offset: int,
) -> str:
    """Build an SGR escape for foreground or background color.

    Uses *offset* = 38 for foreground, 48 for background.

    Args:
        color: A color specified as:
            - Named string: ``"red"``, ``"bright_cyan"``, etc.
            - Hex string: ``"#ff8800"``
            - 256-color int: ``0``–``255``
            - RGB tuple: ``(255, 136, 0)``
        offset: ``38`` for foreground, ``48`` for background.

    Returns:
        An ANSI escape string such as ``"\\033[31m"`` or ``"\\033[38;2;255;0;0m"``.

    Raises:
        ValueError: If *color* cannot be resolved.
    """
    if isinstance(color, int):
        if not 0 <= color <= 255:
            raise ValueError(f"256-color index must be 0–255, got {color}")
        return f"\033[{offset};5;{color}m"

    if isinstance(color, tuple):
        if len(color) != 3:
            raise ValueError(f"RGB tuple must have 3 elements, got {len(color)}")
        r, g, b = color
        return f"\033[{offset};2;{r};{g};{b}m"

    # String: named or hex.
    name = color.lower().strip()
    if name.startswith("#"):
        hex_str = name.lstrip("#")
        if len(hex_str) != 6:
            raise ValueError(f"Invalid hex color: {color}")
        r = int(hex_str[:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:], 16)
        return f"\033[{offset};2;{r};{g};{b}m"

    if name in _ALL_COLORS:
        code = _ALL_COLORS[name]
        if offset == 48:
            # Background codes are foreground + 10.
            code += 10
        return f"\033[{code}m"

    raise ValueError(
        f"Unknown color name: {color!r}. Valid names: {', '.join(sorted(_ALL_COLORS))}"
    )


def fg(color: str | int | tuple[int, int, int]) -> str:
    """Return an ANSI escape for the given foreground color.

    Args:
        color: A color name (``"red"``, ``"bright_cyan"``), hex string
            (``"#ff8800"``), 256-color index (``0``–``255``), or RGB
            tuple (``(255, 136, 0)``).

    Returns:
        An ANSI escape string.

    Example::

        print(fg("red") + "error" + RESET)
        print(fg("#00ff00") + "green" + RESET)
        print(fg(214) + "orange" + RESET)
        print(fg((100, 200, 50)) + "custom" + RESET)
    """
    return _parse_color(color, 38)


def bg(color: str | int | tuple[int, int, int]) -> str:
    """Return an ANSI escape for the given background color.

    Args:
        color: Same formats as :func:`fg`.

    Returns:
        An ANSI escape string.
    """
    return _parse_color(color, 48)


# ── High-Level Styling ──────────────────────────────────────────────


def style(
    text: str,
    *,
    fg: str | int | tuple[int, int, int] | None = None,  # noqa: A002
    bg: str | int | tuple[int, int, int] | None = None,  # noqa: A002
    bold: bool = False,
    dim: bool = False,
    italic: bool = False,
    underline: bool = False,
    strikethrough: bool = False,
    reverse: bool = False,
    reset: bool = True,
) -> str:
    """Wrap *text* with ANSI escape codes.

    Args:
        text: The string to style.
        fg: Foreground color (name, hex, 256-index, or RGB tuple).
        bg: Background color (same formats as *fg*).
        bold: Apply bold weight.
        dim: Apply dim/faint rendering.
        italic: Apply italic style.
        underline: Apply underline decoration.
        strikethrough: Apply strikethrough decoration.
        reverse: Swap foreground and background.
        reset: Append a ``RESET`` sequence after *text* (default ``True``).

    Returns:
        The styled string.

    Example::

        style("Error!", fg="red", bold=True)
        style("note", fg="cyan", italic=True)
        style("warn", fg="yellow", bg="black", underline=True)
    """
    parts: list[str] = []
    if bold:
        parts.append(BOLD)
    if dim:
        parts.append(DIM)
    if italic:
        parts.append(ITALIC)
    if underline:
        parts.append(UNDERLINE)
    if strikethrough:
        parts.append(STRIKETHROUGH)
    if reverse:
        parts.append(REVERSE)
    if fg is not None:
        parts.append(_parse_color(fg, 38))
    if bg is not None:
        parts.append(_parse_color(bg, 48))

    if not parts:
        return text

    prefix = "".join(parts)
    suffix = RESET if reset else ""
    return f"{prefix}{text}{suffix}"


# ── Terminal Detection ──────────────────────────────────────────────

# Regex matching COLORTERM values that indicate true-color support.
_TRUECOLOR_RE = re.compile(r"truecolor|24bit", re.IGNORECASE)


def supports_color(stream: object | None = None) -> bool:
    """Check if the output stream supports ANSI color codes.

    Respects the ``NO_COLOR`` environment variable
    (see `<https://no-color.org/>`_) and the ``FORCE_COLOR`` variable.

    Args:
        stream: The output stream to check.  Defaults to ``sys.stderr``.

    Returns:
        True if the stream is a color-capable terminal.
    """
    if os.environ.get("FORCE_COLOR"):
        return True
    if os.environ.get("NO_COLOR"):
        return False
    s = stream or sys.stderr
    if not hasattr(s, "isatty") or not s.isatty():
        return False
    if os.environ.get("TERM", "") == "dumb":
        return False
    return True


def color_depth(stream: object | None = None) -> int:
    """Detect the color depth of the terminal.

    Args:
        stream: The output stream to check.  Defaults to ``sys.stderr``.

    Returns:
        - ``0`` — no color support
        - ``16`` — standard 16 colors
        - ``256`` — 256 color palette
        - ``16777216`` — 24-bit true color
    """
    if not supports_color(stream):
        return 0

    colorterm = os.environ.get("COLORTERM", "").lower()
    if _TRUECOLOR_RE.search(colorterm):
        return 16_777_216

    term = os.environ.get("TERM", "")
    if "256color" in term:
        return 256

    # Most modern terminals support at least 16 colors.
    return 16


# ── Utilities ───────────────────────────────────────────────────────

_ANSI_ESCAPE_RE = re.compile(r"\033\[[0-9;]*[A-Za-z]|\033\[\?[0-9;]*[A-Za-z]")


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences from *text*.

    Args:
        text: A string potentially containing ANSI escapes.

    Returns:
        The plain text without escape sequences.

    Example::

        strip_ansi("\\033[1m\\033[31mhello\\033[0m")  # "hello"
    """
    return _ANSI_ESCAPE_RE.sub("", text)


def visible_len(text: str) -> int:
    """Return the visible character count of *text*, ignoring ANSI escapes.

    Useful for aligning columns when text contains color codes.

    Args:
        text: A string potentially containing ANSI escapes.

    Returns:
        The number of visible characters.
    """
    return len(strip_ansi(text))


def cursor_move(n: int = 1, direction: str = "up") -> str:
    """Return an ANSI escape to move the cursor.

    Args:
        n: Number of positions to move.
        direction: One of ``"up"``, ``"down"``, ``"forward"``, ``"back"``.

    Returns:
        An ANSI escape string.

    Raises:
        ValueError: If *direction* is not recognised.
    """
    codes = {"up": "A", "down": "B", "forward": "C", "back": "D"}
    if direction not in codes:
        raise ValueError(f"Unknown direction: {direction!r}. Valid: {', '.join(codes)}")
    return f"\033[{n}{codes[direction]}"
