# ANSI Terminal Styling

ANSI escape code primitives for terminal styling -- zero dependencies, stdlib only, Python 3.10+.

## Overview

A lightweight module providing named colors (standard 8 + bright 8), text attributes (bold, dim, italic, underline, strikethrough, reverse), 256-color and 24-bit true-color support, terminal capability detection, and utility helpers.

| File | Description | Dependencies |
|------|-------------|--------------|
| `ansi.py` | ANSI escape code primitives | None (stdlib only: `os`, `re`, `sys`) |

This module serves as the **foundation layer** for terminal visual output across other zerodep modules (`structlog`, `prompt`, `markdown`, etc.).

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp ansi/ansi.py your_project/
```

Then import directly:

```python
from ansi import style, fg, bg, strip_ansi, visible_len
```

## Usage Examples

### Quick Styling

```python
from ansi import style

print(style("Error!", fg="red", bold=True))
print(style("Success", fg="green"))
print(style("Warning", fg="yellow", underline=True))
print(style("Note", fg="cyan", italic=True))
print(style("Highlight", fg="white", bg="blue", bold=True))
```

### Foreground Colors

```python
from ansi import fg, RESET

# Named colors (8 standard + 8 bright)
print(fg("red") + "red text" + RESET)
print(fg("bright_cyan") + "bright cyan" + RESET)

# Hex colors (24-bit true color)
print(fg("#ff8800") + "orange" + RESET)

# 256-color palette
print(fg(214) + "256-color orange" + RESET)

# RGB tuples
print(fg((100, 200, 50)) + "custom green" + RESET)
```

### Background Colors

```python
from ansi import fg, bg, RESET

print(bg("yellow") + fg("black") + "black on yellow" + RESET)
print(bg("#003366") + fg("white") + "white on dark blue" + RESET)
print(bg(53) + fg("white") + "white on purple" + RESET)
```

### Text Attributes

```python
from ansi import style

print(style("bold", bold=True))
print(style("dim", dim=True))
print(style("italic", italic=True))
print(style("underline", underline=True))
print(style("strikethrough", strikethrough=True))
print(style("reverse", reverse=True))

# Combine multiple attributes
print(style("bold italic red", fg="red", bold=True, italic=True))
```

### Terminal Detection

```python
from ansi import supports_color, color_depth

if supports_color():
    depth = color_depth()
    if depth >= 16_777_216:
        print("True color supported")
    elif depth >= 256:
        print("256-color supported")
    else:
        print("Basic 16-color")
else:
    print("No color support")
```

Respects `NO_COLOR` (see [no-color.org](https://no-color.org/)) and `FORCE_COLOR` environment variables.

### Stripping ANSI and Measuring Visible Length

```python
from ansi import style, strip_ansi, visible_len

colored = style("hello", fg="red", bold=True)
print(strip_ansi(colored))      # "hello"
print(visible_len(colored))     # 5
```

`visible_len()` is particularly useful for aligning table columns when text contains color codes.

### Cursor Control

```python
from ansi import cursor_move, CURSOR_HIDE, CURSOR_SHOW, CLEAR_LINE

print(CURSOR_HIDE, end="")       # Hide cursor
print(cursor_move(3, "up"))      # Move up 3 lines
print(CLEAR_LINE, end="")        # Clear current line
print(CURSOR_SHOW, end="")       # Show cursor
```

## API Reference

### Constants

#### Text Attributes

| Constant | SGR Code | Effect |
|----------|----------|--------|
| `RESET` | `\033[0m` | Reset all styling |
| `BOLD` | `\033[1m` | Bold / bright |
| `DIM` | `\033[2m` | Dim / faint |
| `ITALIC` | `\033[3m` | Italic |
| `UNDERLINE` | `\033[4m` | Underline |
| `BLINK` | `\033[5m` | Blink |
| `REVERSE` | `\033[7m` | Swap fg/bg |
| `HIDDEN` | `\033[8m` | Hidden |
| `STRIKETHROUGH` | `\033[9m` | Strikethrough |

#### Named Colors

`NAMED_COLORS` dict contains the standard 8 foreground SGR codes:
`black` (30), `red` (31), `green` (32), `yellow` (33), `blue` (34), `magenta` (35), `cyan` (36), `white` (37).

`BRIGHT_COLORS` dict contains 8 bright variants:
`bright_black` (90) through `bright_white` (97).

#### Cursor Control

| Constant | Effect |
|----------|--------|
| `CURSOR_UP` | Move cursor up 1 line |
| `CURSOR_DOWN` | Move cursor down 1 line |
| `CURSOR_FORWARD` | Move cursor forward 1 column |
| `CURSOR_BACK` | Move cursor back 1 column |
| `CURSOR_HIDE` | Hide cursor |
| `CURSOR_SHOW` | Show cursor |
| `CLEAR_LINE` | Clear from cursor to end of line |
| `CLEAR_SCREEN` | Clear entire screen |
| `CURSOR_HOME` | Move cursor to top-left |

### Functions

See the [API Reference](../api/ansi.md) for full function signatures and docstrings.

## Sibling Module Integration

This module can be used as a shared dependency by other zerodep modules via guarded imports:

```python
# In another zerodep module
try:
    from ansi import style, fg, RESET
except ImportError:
    # Fallback: inline ANSI constants
    RESET = "\033[0m"
    def fg(color): return ""
    def style(text, **kw): return text
```

Currently, `structlog` and `prompt` maintain inline ANSI constants that are aligned with this module's coverage (8 standard colors + 8 bright + all text attributes).

## Benchmark

No benchmark is provided for this module. As a utility module with no direct third-party counterpart, performance comparison is not applicable -- see [ANSI Benchmark](../benchmarks/ansi.md) for details.
