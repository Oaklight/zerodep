"""Zero-dependency interactive CLI prompts (confirm, select, text).

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Provides interactive command-line prompts similar to *questionary*,
using only the Python standard library.  Works on Linux, macOS (via
``termios``/``tty``) and Windows (via ``msvcrt``) with an automatic
fallback to plain ``input()`` when a TTY is unavailable.

Basic usage::

    answer = confirm("Continue?")
    choice = select("Pick one:", ["a", "b", "c"])
    name   = text("Your name:", validate=lambda s: True if s else "Required")
"""

from __future__ import annotations

__version__ = "0.1.0"

import contextlib
import io
import os
import sys
from collections.abc import Callable, Generator
from typing import Any, TextIO

# ---------------------------------------------------------------------------
# Platform-specific raw-mode helpers
# ---------------------------------------------------------------------------

_IS_WINDOWS = sys.platform == "win32"

if _IS_WINDOWS:
    try:
        import msvcrt  # type: ignore[import-untyped]
    except ImportError:  # pragma: no cover – safety net
        msvcrt = None
else:
    try:
        import termios
        import tty
    except ImportError:  # pragma: no cover – not a real TTY
        termios = None  # type: ignore
        tty = None  # type: ignore


@contextlib.contextmanager
def _raw_mode(fd: int) -> Generator[None, None, None]:
    """Context manager that puts *fd* into raw mode and restores on exit.

    On Windows this is a no-op (``msvcrt`` handles key reading directly).
    """
    if _IS_WINDOWS or termios is None:
        yield
        return

    old_attrs = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_attrs)


def _read_key(input_stream: TextIO | None = None) -> str:
    """Read a single keypress and return a logical key name.

    Returns one of:
    - ``"up"``, ``"down"`` for arrow keys
    - ``"enter"`` for Enter / Return
    - ``"ctrl-c"`` for Ctrl-C / ETX
    - ``"ctrl-d"`` for Ctrl-D / EOT
    - the character itself for printable keys

    Args:
        input_stream: Optional stream override (used in tests).
    """
    if _IS_WINDOWS and msvcrt is not None and input_stream is None:
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            ch2 = msvcrt.getwch()
            if ch2 == "H":
                return "up"
            if ch2 == "P":
                return "down"
            return ""
        if ch == "\r":
            return "enter"
        if ch == "\x03":
            return "ctrl-c"
        if ch == "\x04":
            return "ctrl-d"
        return ch

    stream: TextIO = input_stream or sys.stdin
    ch = stream.read(1)
    if not ch:
        return "ctrl-d"
    if ch == "\x1b":
        ch2 = stream.read(1)
        if ch2 == "[":
            ch3 = stream.read(1)
            if ch3 == "A":
                return "up"
            if ch3 == "B":
                return "down"
            if ch3 == "C":
                return "right"
            if ch3 == "D":
                return "left"
        return "esc"
    if ch in ("\r", "\n"):
        return "enter"
    if ch == "\x03":
        return "ctrl-c"
    if ch == "\x04":
        return "ctrl-d"
    return ch


def _is_tty() -> bool:
    """Return ``True`` when both stdin and stdout are connected to a TTY."""
    try:
        return os.isatty(sys.stdin.fileno()) and os.isatty(sys.stdout.fileno())
    except (AttributeError, ValueError, io.UnsupportedOperation):
        return False


def _supports_color(stream: Any = None) -> bool:
    """Check if the output stream supports ANSI color codes.

    Respects the ``FORCE_COLOR`` and ``NO_COLOR`` environment variables
    (see https://force-color.org/ and https://no-color.org/).

    Args:
        stream: The output stream to check.  Defaults to ``sys.stdout``.

    Returns:
        True if the stream is a color-capable terminal.
    """
    if os.environ.get("FORCE_COLOR"):
        return True
    if os.environ.get("NO_COLOR"):
        return False
    s = stream or sys.stdout
    if not hasattr(s, "isatty") or not s.isatty():
        return False
    if os.environ.get("TERM", "") == "dumb":
        return False
    return True


# ---------------------------------------------------------------------------
# ANSI helpers
# ---------------------------------------------------------------------------

_ANSI_RESET = "\033[0m"
_ANSI_BOLD = "\033[1m"
_ANSI_DIM = "\033[2m"
_ANSI_ITALIC = "\033[3m"
_ANSI_UNDERLINE = "\033[4m"
_ANSI_STRIKETHROUGH = "\033[9m"
_ANSI_REVERSE = "\033[7m"
_ANSI_CLEAR_LINE = "\033[K"
_ANSI_CURSOR_UP = "\033[A"
_ANSI_HIDE_CURSOR = "\033[?25l"
_ANSI_SHOW_CURSOR = "\033[?25h"

# Named colours → SGR foreground codes (standard 8 + bright 8)
_NAMED_COLORS: dict[str, int] = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    "bright_black": 90,
    "bright_red": 91,
    "bright_green": 92,
    "bright_yellow": 93,
    "bright_blue": 94,
    "bright_magenta": 95,
    "bright_cyan": 96,
    "bright_white": 97,
}


def _hex_to_ansi_fg(hex_color: str) -> str:
    """Convert a ``#RRGGBB`` hex colour to a 24-bit ANSI foreground escape.

    Args:
        hex_color: A colour string such as ``"#ff0000"``.

    Returns:
        An ANSI escape sequence like ``"\\033[38;2;255;0;0m"``.

    Raises:
        ValueError: If *hex_color* is not a valid 6-digit hex colour.
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex colour: #{hex_color}")
    r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:], 16)
    return f"\033[38;2;{r};{g};{b}m"


def _parse_style_string(style_str: str) -> str:
    """Parse a style description string into concatenated ANSI codes.

    The string may contain space-separated tokens such as ``"fg:#00ff00 bold
    underline"`` or ``"fg:red italic"``.

    Recognised tokens:
    - ``fg:#RRGGBB`` – 24-bit foreground colour
    - ``fg:<name>`` – named colour (red, green, bright_red, …)
    - ``bold``, ``dim``, ``italic``, ``underline``, ``strikethrough``,
      ``reverse`` – text decorations

    Args:
        style_str: The style description to parse.

    Returns:
        A string of concatenated ANSI escape codes (may be empty).
    """
    _ATTR_MAP: dict[str, str] = {
        "bold": _ANSI_BOLD,
        "dim": _ANSI_DIM,
        "italic": _ANSI_ITALIC,
        "underline": _ANSI_UNDERLINE,
        "strikethrough": _ANSI_STRIKETHROUGH,
        "reverse": _ANSI_REVERSE,
    }
    codes: list[str] = []
    for token in style_str.strip().split():
        lower = token.lower()
        if lower in _ATTR_MAP:
            codes.append(_ATTR_MAP[lower])
        elif lower.startswith("fg:"):
            color_val = lower[3:]
            if color_val.startswith("#"):
                codes.append(_hex_to_ansi_fg(color_val))
            elif color_val in _NAMED_COLORS:
                codes.append(f"\033[{_NAMED_COLORS[color_val]}m")
        # Silently ignore unrecognised tokens for forward-compat.
    return "".join(codes)


# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------

# Default role → ANSI mappings used when no custom Style is provided.
_DEFAULT_STYLES: dict[str, str] = {
    "question": _ANSI_BOLD,
    "answer": f"\033[{_NAMED_COLORS['cyan']}m",
    "pointer": f"\033[{_NAMED_COLORS['cyan']}m{_ANSI_BOLD}",
    "highlighted": f"\033[{_NAMED_COLORS['cyan']}m{_ANSI_UNDERLINE}",
    "error": f"\033[{_NAMED_COLORS['red']}m{_ANSI_BOLD}",
    "instruction": f"\033[{_NAMED_COLORS['yellow']}m",
}


class Style:
    """ANSI styling configuration for prompts.

    Users may supply a list of ``(role, style_string)`` tuples to customise
    how each visual element is rendered.  Recognised roles are ``"question"``,
    ``"answer"``, ``"pointer"``, ``"highlighted"``, ``"error"``, and
    ``"instruction"``.

    Example::

        style = Style([
            ("question", "fg:#00ff00 bold"),
            ("answer",   "fg:#ffffff"),
        ])
        confirm("Continue?", style=style)
    """

    def __init__(
        self,
        style_list: list[tuple[str, str]] | None = None,
        *,
        colors: bool | None = None,
    ) -> None:
        self._roles: dict[str, str] = dict(_DEFAULT_STYLES)
        if style_list:
            for role, sstr in style_list:
                self._roles[role] = _parse_style_string(sstr)
        self._colors = _supports_color() if colors is None else colors

    def apply(self, role: str, text: str) -> str:
        """Wrap *text* with the ANSI codes for *role* and a trailing reset.

        Args:
            role: One of the recognised role names.
            text: The text to style.

        Returns:
            The styled string with a trailing ANSI reset sequence,
            or plain *text* when colors are disabled.
        """
        if not self._colors:
            return text
        prefix = self._roles.get(role, "")
        if prefix:
            return f"{prefix}{text}{_ANSI_RESET}"
        return text

    def get(self, role: str) -> str:
        """Return raw ANSI prefix for *role* (empty string if unknown)."""
        return self._roles.get(role, "")


def _default_style() -> Style:
    """Return the default ``Style`` instance."""
    return Style()


# ---------------------------------------------------------------------------
# Choice normalisation
# ---------------------------------------------------------------------------


def _normalise_choices(
    choices: list[str] | list[dict[str, str]],
) -> list[dict[str, str]]:
    """Normalise a user-provided choice list into ``[{"name": …, "value": …}]``.

    Args:
        choices: Either a list of plain strings or a list of dicts with at
            least a ``"name"`` key.  If ``"value"`` is absent it defaults to
            ``"name"``.

    Returns:
        A list of dicts each with ``"name"`` and ``"value"`` keys.

    Raises:
        ValueError: If *choices* is empty.
    """
    if not choices:
        raise ValueError("choices must not be empty")

    result: list[dict[str, str]] = []
    for c in choices:
        if isinstance(c, str):
            result.append({"name": c, "value": c})
        elif isinstance(c, dict):
            name = c.get("name", c.get("value", ""))
            value = c.get("value", name)
            result.append({"name": name, "value": value})
        else:
            result.append({"name": str(c), "value": str(c)})
    return result


# ---------------------------------------------------------------------------
# confirm()
# ---------------------------------------------------------------------------


def _parse_confirm_input(text: str, default: bool) -> bool | None:
    """Parse user input for a yes/no confirmation.

    Args:
        text: Raw user input (may be empty).
        default: The default value when input is empty.

    Returns:
        ``True`` for yes, ``False`` for no, ``None`` if the input is
        unrecognised.
    """
    text = text.strip().lower()
    if text == "":
        return default
    if text in ("y", "yes"):
        return True
    if text in ("n", "no"):
        return False
    return None


def confirm(
    message: str,
    default: bool = True,
    style: Style | None = None,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> bool | None:
    """Ask a yes/no question.

    Args:
        message: The question to display.
        default: Pre-selected answer (``True`` → Yes).
        style: Optional ``Style`` for visual customisation.
        input_stream: Override for ``sys.stdin`` (useful in tests).
        output_stream: Override for ``sys.stdout`` (useful in tests).

    Returns:
        ``True`` for yes, ``False`` for no, or ``None`` if the user
        cancelled with Ctrl-C.

    Example::

        if confirm("Proceed with installation?"):
            install()
    """
    sty = style or _default_style()
    out = output_stream or sys.stdout
    inp = input_stream or sys.stdin

    hint = "(Y/n)" if default else "(y/N)"
    q_part = sty.apply("question", "? " + message)
    h_part = sty.apply("instruction", hint)
    prompt_str = f"{q_part} {h_part} "

    while True:
        try:
            out.write(prompt_str)
            out.flush()
            line = inp.readline()
            if not line:  # EOF
                return None
            result = _parse_confirm_input(line, default)
            if result is not None:
                answer_text = "Yes" if result else "No"
                out.write(f"{sty.apply('answer', answer_text)}\n")
                out.flush()
                return result
            # Unrecognised → re-prompt
            out.write("  Please answer y or n.\n")
            out.flush()
        except (KeyboardInterrupt, EOFError):
            out.write("\n")
            out.flush()
            return None


# ---------------------------------------------------------------------------
# select()
# ---------------------------------------------------------------------------


def _render_select(
    choices: list[dict[str, str]],
    index: int,
    sty: Style,
) -> str:
    """Render the select menu as a string (without the question line).

    Args:
        choices: Normalised choice list.
        index: Currently highlighted index.
        sty: Style instance.

    Returns:
        A multi-line string representing the rendered menu.
    """
    lines: list[str] = []
    for i, c in enumerate(choices):
        if i == index:
            pointer = sty.apply("pointer", "❯")
            label = sty.apply("highlighted", c["name"])
            lines.append(f"  {pointer} {label}")
        else:
            lines.append(f"    {c['name']}")
    return "\n".join(lines)


def select(
    message: str,
    choices: list[str] | list[dict[str, str]],
    default: str | None = None,
    style: Style | None = None,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> str | None:
    """Show a list of choices with arrow-key navigation.

    Args:
        message: The question to display above the list.
        choices: Either plain strings or ``{"name": …, "value": …}`` dicts.
        default: Value to pre-select.  Defaults to the first choice.
        style: Optional ``Style`` for visual customisation.
        input_stream: Override for ``sys.stdin`` (useful in tests).
        output_stream: Override for ``sys.stdout`` (useful in tests).

    Returns:
        The ``value`` of the selected choice, or ``None`` if cancelled.

    Example::

        lang = select("Language:", ["Python", "Rust", "Go"])
    """
    sty = style or _default_style()
    out: TextIO = output_stream or sys.stdout
    norm = _normalise_choices(choices)

    # Determine starting index
    index = 0
    if default is not None:
        for i, c in enumerate(norm):
            if c["value"] == default:
                index = i
                break

    use_tty = (
        input_stream is None
        and output_stream is None
        and _is_tty()
        and (not _IS_WINDOWS or msvcrt is not None)
        and (_IS_WINDOWS or termios is not None)
    )

    if not use_tty:
        return _select_fallback(message, norm, index, sty, input_stream, out)

    return _select_interactive(message, norm, index, sty, out)


def _select_fallback(
    message: str,
    choices: list[dict[str, str]],
    index: int,
    sty: Style,
    inp: TextIO | None,
    out: TextIO,
) -> str | None:
    """Non-TTY fallback for ``select``: show numbered list, accept a number."""
    inp = inp or sys.stdin
    out.write(f"{sty.apply('question', '? ' + message)}\n")
    for i, c in enumerate(choices):
        marker = ">" if i == index else " "
        out.write(f"  {marker} {i + 1}. {c['name']}\n")
    out.write(f"Enter number [1-{len(choices)}]: ")
    out.flush()
    try:
        line = inp.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            return choices[index]["value"]
        num = int(line)
        if 1 <= num <= len(choices):
            return choices[num - 1]["value"]
        return choices[index]["value"]
    except (KeyboardInterrupt, EOFError):
        return None
    except ValueError:
        return choices[index]["value"]


def _select_interactive(
    message: str,
    choices: list[dict[str, str]],
    index: int,
    sty: Style,
    out: TextIO,
) -> str | None:
    """Full interactive select with arrow keys (requires TTY)."""
    num_choices = len(choices)

    out.write(_ANSI_HIDE_CURSOR)
    out.write(f"{sty.apply('question', '? ' + message)}\n")
    out.write(_render_select(choices, index, sty))
    out.flush()

    fd = sys.stdin.fileno()

    try:
        with _raw_mode(fd):
            while True:
                key = _read_key()
                if key == "up":
                    index = (index - 1) % num_choices
                elif key == "down":
                    index = (index + 1) % num_choices
                elif key == "enter":
                    # Clear the menu and show final answer
                    _clear_lines(out, num_choices)
                    out.write(f"  {sty.apply('answer', choices[index]['name'])}\n")
                    out.write(_ANSI_SHOW_CURSOR)
                    out.flush()
                    return choices[index]["value"]
                elif key in ("ctrl-c", "ctrl-d", "esc"):
                    _clear_lines(out, num_choices)
                    out.write("\n")
                    out.write(_ANSI_SHOW_CURSOR)
                    out.flush()
                    return None
                else:
                    continue  # ignore other keys

                # Redraw the menu
                _clear_lines(out, num_choices)
                out.write(_render_select(choices, index, sty))
                out.flush()
    except (KeyboardInterrupt, EOFError):
        out.write(_ANSI_SHOW_CURSOR)
        out.write("\n")
        out.flush()
        return None


def _clear_lines(out: TextIO, count: int) -> None:
    """Move the cursor up *count* lines, clearing each one."""
    for _ in range(count):
        out.write(f"{_ANSI_CURSOR_UP}{_ANSI_CLEAR_LINE}")


# ---------------------------------------------------------------------------
# text()
# ---------------------------------------------------------------------------


def text(
    message: str,
    default: str = "",
    validate: Callable[[str], bool | str] | None = None,
    style: Style | None = None,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> str | None:
    """Prompt the user for free-form text input.

    Args:
        message: The question to display.
        default: Default value (used when the user presses Enter without
            typing anything).
        validate: Optional callable that receives the current input string.
            Return ``True`` to accept, or a string to show as an error
            message and re-prompt.
        style: Optional ``Style`` for visual customisation.
        input_stream: Override for ``sys.stdin`` (useful in tests).
        output_stream: Override for ``sys.stdout`` (useful in tests).

    Returns:
        The entered string, or ``None`` if cancelled with Ctrl-C.

    Example::

        name = text("Your name:", validate=lambda s: True if s else "Name required")
    """
    sty = style or _default_style()
    out = output_stream or sys.stdout
    inp = input_stream or sys.stdin

    default_hint = f" ({default})" if default else ""
    q_part = sty.apply("question", "? " + message)
    h_part = sty.apply("instruction", default_hint)
    prompt_str = f"{q_part}{h_part} "

    while True:
        try:
            out.write(prompt_str)
            out.flush()
            line = inp.readline()
            if not line:  # EOF
                return None
            value = line.rstrip("\n").rstrip("\r")
            if not value and default:
                value = default

            if validate is not None:
                result = validate(value)
                if result is True:
                    out.write(f"  {sty.apply('answer', value)}\n")
                    out.flush()
                    return value
                elif isinstance(result, str):
                    out.write(f"  {sty.apply('error', '✗ ' + result)}\n")
                    out.flush()
                    continue
                else:
                    # result is False or falsy but not a string → reject silently
                    out.write(f"  {sty.apply('error', '✗ Invalid input')}\n")
                    out.flush()
                    continue
            else:
                out.write(f"  {sty.apply('answer', value)}\n")
                out.flush()
                return value
        except (KeyboardInterrupt, EOFError):
            out.write("\n")
            out.flush()
            return None


# ---------------------------------------------------------------------------
# Module-level exports
# ---------------------------------------------------------------------------

__all__ = [
    "Style",
    "confirm",
    "select",
    "text",
    # Internal but useful for testing:
    "_parse_confirm_input",
    "_normalise_choices",
    "_parse_style_string",
    "_hex_to_ansi_fg",
    "_render_select",
    "_read_key",
    "_is_tty",
    "_ANSI_RESET",
    "_ANSI_BOLD",
    "_ANSI_DIM",
    "_ANSI_ITALIC",
    "_ANSI_UNDERLINE",
    "_ANSI_STRIKETHROUGH",
    "_ANSI_REVERSE",
    "_NAMED_COLORS",
]
