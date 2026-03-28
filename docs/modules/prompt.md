# Interactive Prompts

Zero-dependency interactive CLI prompts (confirm, select, text) -- stdlib only, Python 3.10+.

## Overview

The Prompt module provides interactive command-line prompts similar to *questionary*, using only the Python standard library. Works on Linux and macOS (via `termios`/`tty`) and Windows (via `msvcrt`) with an automatic fallback to plain `input()` when a TTY is unavailable.

| File | Description | Dependencies |
|------|-------------|--------------|
| `prompt.py` | Pure Python implementation | None (stdlib only: `sys`, `os`, `io`, `contextlib`, `termios`/`tty` or `msvcrt`) |

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp prompt/prompt.py your_project/
```

Then import directly:

```python
from prompt import confirm, select, text, Style
```

## Usage Examples

### confirm()

```python
from prompt import confirm

answer = confirm("Continue with installation?")
if answer:
    print("Installing...")
else:
    print("Cancelled.")
```

With custom default:

```python
# Default to "No"
answer = confirm("Delete all files?", default=False)
```

### select()

```python
from prompt import select

# Simple string choices
lang = select("Choose a language:", ["Python", "Rust", "Go"])
print(f"You chose: {lang}")
```

With name/value dicts:

```python
choice = select("Pick a color:", [
    {"name": "Red", "value": "#ff0000"},
    {"name": "Green", "value": "#00ff00"},
    {"name": "Blue", "value": "#0000ff"},
])
print(f"Hex: {choice}")
```

With a default selection:

```python
lang = select("Language:", ["Python", "Rust", "Go"], default="Python")
```

### text()

```python
from prompt import text

name = text("Your name:")
print(f"Hello, {name}!")
```

With validation:

```python
email = text(
    "Email address:",
    validate=lambda s: True if "@" in s else "Must contain @",
)
```

With default value:

```python
host = text("Hostname:", default="localhost")
```

### Custom Styling

```python
from prompt import confirm, Style

style = Style([
    ("question", "fg:#00ff00 bold"),
    ("answer", "fg:#ffffff"),
    ("pointer", "fg:#ff0000"),
    ("highlighted", "fg:#00ffff bold"),
    ("instruction", "fg:#888888"),
    ("error", "fg:#ff0000 bold"),
])

answer = confirm("Continue?", style=style)
```

## API Reference

### `confirm(message, default=True, style=None)`

Ask a yes/no question.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `message` | `str` | -- | The question to display. |
| `default` | `bool` | `True` | Pre-selected answer (`True` = Yes). |
| `style` | `Style \| None` | `None` | Optional style customisation. |

**Returns:** `True` for yes, `False` for no, or `None` if cancelled (Ctrl-C).

---

### `select(message, choices, default=None, style=None)`

Show a list of choices with arrow-key navigation.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `message` | `str` | -- | The question above the list. |
| `choices` | `list[str] \| list[dict]` | -- | Plain strings or `{"name": ..., "value": ...}` dicts. |
| `default` | `str \| None` | `None` | Value to pre-select. Defaults to first choice. |
| `style` | `Style \| None` | `None` | Optional style customisation. |

**Returns:** The `value` of the selected choice, or `None` if cancelled.

---

### `text(message, default="", validate=None, style=None)`

Prompt the user for free-form text input.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `message` | `str` | -- | The question to display. |
| `default` | `str` | `""` | Default value (used on empty Enter). |
| `validate` | `Callable \| None` | `None` | Callable `(str) -> bool \| str`. Return `True` to accept, or an error message string. |
| `style` | `Style \| None` | `None` | Optional style customisation. |

**Returns:** The entered string, or `None` if cancelled (Ctrl-C).

---

### `Style(style_list=None)`

ANSI styling configuration for prompts.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `style_list` | `list[tuple[str, str]] \| None` | `None` | List of `(role, style_string)` tuples. |

**Recognised roles:** `"question"`, `"answer"`, `"pointer"`, `"highlighted"`, `"error"`, `"instruction"`.

**Style string format:** Space-separated tokens: `fg:#hexcolor`, `bg:#hexcolor`, `bold`, `italic`, `underline`.

## TTY Detection and Fallback

When running without a TTY (piped input, CI environments, etc.), the module automatically falls back to a numbered-list mode for `select()` and plain `input()` for other prompts. This makes scripts using `prompt.py` safe to run in non-interactive contexts.

## Comparison with questionary

| Feature | zerodep prompt | questionary |
|---------|---------------|-------------|
| Dependencies | None (stdlib only) | `prompt_toolkit` |
| Files | Single file | Package (multiple files) |
| confirm / select / text | Yes | Yes |
| checkbox / password / path / autocomplete | No | Yes |
| Custom styling | Yes (hex colors, bold, italic) | Yes (via prompt_toolkit Style) |
| Non-TTY fallback | Yes (automatic) | Partial |
| Windows support | Yes (via `msvcrt`) | Yes (via prompt_toolkit) |

**When to use zerodep:** You need basic interactive prompts (confirm, select, text) with zero dependencies and cross-platform support.

**When to use questionary:** You need advanced prompt types (checkbox, password, autocomplete) or the full power of prompt_toolkit.

## Benchmark

No benchmark is provided for this module. Interactive prompts are bottlenecked by user input latency, not code execution -- see [Prompt Benchmark](../benchmarks/prompt.md) for details.
