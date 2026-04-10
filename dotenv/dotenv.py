# /// zerodep
# version = "0.3.0"
# deps = []
# tier = "simple"
# category = "data"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///

""".env file parser and loader — zero dependencies, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Drop-in replacement for python-dotenv core functionality.

Example::

    load_dotenv()                       # load .env into os.environ
    values = dotenv_values(".env")       # parse without modifying environ
    path = find_dotenv()                 # search up for .env file
"""

from __future__ import annotations

import inspect
import os
import re
import sys
from pathlib import Path
from typing import IO, Iterator, Mapping

__all__ = [
    "find_dotenv",
    "get_key",
    "set_key",
    "unset_key",
    "dotenv_values",
    "load_dotenv",
]

# ── Constants / Regex ──────────────────────────────────────────────────────────

_ESCAPE_MAP = {
    "\\": "\\",
    "'": "'",
    '"': '"',
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "$": "$",
    " ": " ",
}

# Matches a single .env binding line.  Groups:
#   key   – variable name
#   sq    – single-quoted value content
#   dq    – double-quoted value content (may span multiple lines)
#   uq    – unquoted value content
_BINDING_RE = re.compile(
    r"""
    \A\s*                              # leading whitespace
    (?:export\s+)?                     # optional export prefix
    (?P<key>[A-Za-z_]\w*)              # key (must start with letter or _)
    (?:                                # optional =value part
      \s*=\s*                          # equals sign
      (?:
        '(?P<sq>[^']*)'                # single-quoted (no escapes)
      | "(?P<dq>(?:[^"\\]|\\.)*)"      # double-quoted (with escapes)
      | (?P<uq>[^\#\r\n]*)            # unquoted (up to # or EOL)
      )
    )?                                 # entire =value is optional
    \s*                                # trailing whitespace
    (?:\#.*)?                          # optional inline comment
    \s*\Z                              # end
    """,
    re.VERBOSE,
)

_INTERPOLATE_RE = re.compile(
    r"""
    (?<!\\)                            # not preceded by backslash
    \$                                 # dollar sign
    (?:
      \{(?P<brace>[^}]*)\}            # ${VAR} or ${VAR:-default}
    | (?P<name>[A-Za-z_]\w*)           # $VAR
    )
    """,
    re.VERBOSE,
)


# ── Internal helpers ───────────────────────────────────────────────────────────


def _unescape_double_quoted(s: str) -> str:
    """Process escape sequences in a double-quoted value."""

    def _replace(m: re.Match[str]) -> str:
        ch = m.group(1)
        return _ESCAPE_MAP.get(ch, "\\" + ch)

    return re.sub(r"\\(.)", _replace, s)


def _interpolate(
    value: str,
    env: dict[str, str | None],
    os_environ: Mapping[str, str],
) -> str:
    """Expand $VAR and ${VAR} references in *value*.

    Resolution order: file-local *env*, then *os_environ*, then empty string.
    Supports ${VAR:-default} syntax.
    """

    def _replace(m: re.Match[str]) -> str:
        brace = m.group("brace")
        if brace is not None:
            # Handle ${VAR:-default}
            if ":-" in brace:
                name, default = brace.split(":-", 1)
                name = name.strip()
                val = env.get(name) if name in env else os_environ.get(name)
                return val if val is not None else default
            name = brace.strip()
        else:
            name = m.group("name")
        val = env.get(name) if name in env else os_environ.get(name)
        return val if val is not None else ""

    return _INTERPOLATE_RE.sub(_replace, value)


def _parse_stream(
    stream: IO[str],
    interpolate: bool = True,
    override: bool = False,
    os_environ: Mapping[str, str] | None = None,
) -> Iterator[tuple[str, str | None]]:
    """Parse an .env stream, yielding (key, value) tuples."""
    if os_environ is None:
        os_environ = os.environ

    env: dict[str, str | None] = {}
    content = stream.read()

    # Strip UTF-8 BOM
    if content.startswith("\ufeff"):
        content = content[1:]

    lines = content.splitlines(keepends=True)
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        i += 1

        # Skip blank lines and comment-only lines
        if not stripped or stripped.startswith("#"):
            continue

        # Check for multiline double-quoted values
        # Detect pattern: KEY="value without closing quote
        ml_match = re.match(
            r'\A\s*(?:export\s+)?([A-Za-z_]\w*)\s*=\s*"',
            line,
        )
        if ml_match:
            # Find the content after the opening quote
            after_eq_quote = line[ml_match.end() :]
            # Check if the quote is closed on this line
            # We need to find an unescaped closing quote
            closed = False
            temp = after_eq_quote
            pos = 0
            while pos < len(temp):
                if temp[pos] == "\\" and pos + 1 < len(temp):
                    pos += 2
                    continue
                if temp[pos] == '"':
                    closed = True
                    break
                pos += 1

            if not closed:
                # Multiline: accumulate lines until closing "
                key = ml_match.group(1)
                parts = [after_eq_quote]
                while i < len(lines):
                    next_line = lines[i]
                    i += 1
                    # Check for closing quote
                    pos = 0
                    found_close = False
                    while pos < len(next_line):
                        if next_line[pos] == "\\" and pos + 1 < len(next_line):
                            pos += 2
                            continue
                        if next_line[pos] == '"':
                            found_close = True
                            break
                        pos += 1
                    if found_close:
                        parts.append(next_line[:pos])
                        break
                    parts.append(next_line)

                raw_value = "".join(parts)
                value = _unescape_double_quoted(raw_value)
                if interpolate:
                    value = _interpolate(value, env, os_environ)
                env[key] = value
                yield key, value
                continue

        # Single-line binding
        m = _BINDING_RE.match(stripped)
        if m is None:
            continue

        key = m.group("key")

        if m.group("sq") is not None:
            # Single-quoted: literal, no escapes
            value: str | None = m.group("sq")
        elif m.group("dq") is not None:
            # Double-quoted: process escapes
            value = _unescape_double_quoted(m.group("dq"))
        elif m.group("uq") is not None:
            # Unquoted: strip trailing whitespace
            value = m.group("uq").rstrip()
        else:
            # KEY with no =value
            value = None

        if value is not None and interpolate:
            value = _interpolate(value, env, os_environ)

        env[key] = value
        yield key, value


# ── File search ────────────────────────────────────────────────────────────────


def find_dotenv(
    filename: str = ".env",
    raise_error_if_not_found: bool = False,
    usecwd: bool = False,
) -> str:
    """Walk up from the calling file's directory (or cwd) to find *filename*.

    Args:
        filename: Name of the file to search for.
        raise_error_if_not_found: Raise IOError if the file is not found.
        usecwd: Start from the current working directory instead of the
            calling file's directory.

    Returns:
        Absolute path to the found file, or empty string if not found.
    """
    if usecwd:
        start = Path.cwd()
    else:
        frame = inspect.currentframe()
        caller = frame.f_back if frame is not None else None
        if caller is not None and caller.f_globals.get("__file__"):
            start = Path(caller.f_globals["__file__"]).resolve().parent
        else:
            start = Path.cwd()

    current = start
    while True:
        candidate = current / filename
        if candidate.is_file():
            return str(candidate)
        parent = current.parent
        if parent == current:
            break
        current = parent

    if raise_error_if_not_found:
        raise IOError(f"File {filename!r} not found starting from {start}")
    return ""


# ── File I/O (set / unset) ────────────────────────────────────────────────────


def get_key(
    dotenv_path: str | os.PathLike[str],
    key_to_get: str,
    encoding: str = "utf-8",
) -> str | None:
    """Get a single value from a .env file.

    Args:
        dotenv_path: Path to the .env file.
        key_to_get: The key to retrieve.
        encoding: File encoding.

    Returns:
        The value for the key, or None if not found.
    """
    values = dotenv_values(dotenv_path, encoding=encoding)
    return values.get(key_to_get)


def set_key(
    dotenv_path: str | os.PathLike[str],
    key_to_set: str,
    value_to_set: str,
    quote_mode: str = "always",
    export: bool = False,
    encoding: str = "utf-8",
) -> tuple[bool, str, str]:
    """Set a key=value pair in a .env file, creating it if needed.

    Args:
        dotenv_path: Path to the .env file.
        key_to_set: The key to set.
        value_to_set: The value to set.
        quote_mode: Quoting strategy: "always", "auto", or "never".
        export: Whether to prefix with ``export``.
        encoding: File encoding.

    Returns:
        Tuple of (success, key, value).
    """
    path = Path(dotenv_path)

    if quote_mode == "always":
        value_out = f'"{value_to_set}"'
    elif quote_mode == "never":
        value_out = value_to_set
    else:
        # auto: quote if value contains spaces or special chars
        if re.search(r"[\s#\"']", value_to_set):
            value_out = f'"{value_to_set}"'
        else:
            value_out = value_to_set

    export_prefix = "export " if export else ""
    new_line = f"{export_prefix}{key_to_set}={value_out}\n"

    if path.is_file():
        lines = path.read_text(encoding=encoding).splitlines(keepends=True)
        replaced = False
        for idx, line in enumerate(lines):
            m = re.match(
                r"\A\s*(?:export\s+)?(" + re.escape(key_to_set) + r")\s*=",
                line,
            )
            if m:
                lines[idx] = new_line
                replaced = True
                break
        if not replaced:
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines.append(new_line)
        path.write_text("".join(lines), encoding=encoding)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_line, encoding=encoding)

    return True, key_to_set, value_to_set


def unset_key(
    dotenv_path: str | os.PathLike[str],
    key_to_unset: str,
    quote_mode: str = "always",
    encoding: str = "utf-8",
) -> tuple[bool, str]:
    """Remove a key from a .env file.

    Args:
        dotenv_path: Path to the .env file.
        key_to_unset: The key to remove.
        quote_mode: Unused, kept for API compatibility.
        encoding: File encoding.

    Returns:
        Tuple of (success, key).
    """
    path = Path(dotenv_path)
    if not path.is_file():
        return True, key_to_unset

    lines = path.read_text(encoding=encoding).splitlines(keepends=True)
    new_lines = []
    for line in lines:
        m = re.match(
            r"\A\s*(?:export\s+)?(" + re.escape(key_to_unset) + r")\s*=",
            line,
        )
        if m:
            continue
        new_lines.append(line)

    path.write_text("".join(new_lines), encoding=encoding)
    return True, key_to_unset


# ── Public API ─────────────────────────────────────────────────────────────────


def dotenv_values(
    dotenv_path: str | os.PathLike[str] | None = None,
    stream: IO[str] | None = None,
    verbose: bool = False,
    interpolate: bool = True,
    override: bool = False,
    encoding: str = "utf-8",
) -> dict[str, str | None]:
    """Parse a .env file and return a dict without modifying ``os.environ``.

    Args:
        dotenv_path: Path to the .env file. If None, uses ``find_dotenv()``.
        stream: A text stream to read from (overrides *dotenv_path*).
        verbose: Print a warning when the file is missing.
        interpolate: Expand ``$VAR`` and ``${VAR}`` references.
        override: Unused for dotenv_values (kept for API compatibility).
        encoding: File encoding.

    Returns:
        Dictionary mapping variable names to their values.
    """
    if stream is not None:
        return dict(_parse_stream(stream, interpolate=interpolate))

    if dotenv_path is None:
        dotenv_path = find_dotenv(usecwd=True)

    path = Path(dotenv_path)
    if not path.is_file():
        if verbose:
            print(  # noqa: T201
                f"Python-dotenv could not find configuration file {path}.",
                file=sys.stderr,
            )
        return {}

    with open(path, encoding=encoding) as f:
        return dict(_parse_stream(f, interpolate=interpolate))


def load_dotenv(
    dotenv_path: str | os.PathLike[str] | None = None,
    stream: IO[str] | None = None,
    verbose: bool = False,
    interpolate: bool = True,
    override: bool = False,
    encoding: str = "utf-8",
) -> bool:
    """Read a .env file and set ``os.environ``.

    Args:
        dotenv_path: Path to the .env file. If None, uses ``find_dotenv()``.
        stream: A text stream to read from (overrides *dotenv_path*).
        verbose: Print a warning when the file is missing.
        interpolate: Expand ``$VAR`` and ``${VAR}`` references.
        override: If True, overwrite existing environment variables.
        encoding: File encoding.

    Returns:
        True if a file was found and loaded.
    """
    if stream is not None:
        for key, value in _parse_stream(stream, interpolate=interpolate):
            if value is not None:
                if override or key not in os.environ:
                    os.environ[key] = value
        return True

    if dotenv_path is None:
        dotenv_path = find_dotenv(usecwd=True)

    path = Path(dotenv_path)
    if not path.is_file():
        if verbose:
            print(  # noqa: T201
                f"Python-dotenv could not find configuration file {path}.",
                file=sys.stderr,
            )
        return False

    with open(path, encoding=encoding) as f:
        for key, value in _parse_stream(f, interpolate=interpolate):
            if value is not None:
                if override or key not in os.environ:
                    os.environ[key] = value
    return True
