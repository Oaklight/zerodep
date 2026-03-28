# /// zerodep
# version = "0.1.0"
# deps = ["yaml"]
# ///
"""Frontmatter parser and serializer — zero dependencies, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Parse and serialize file-header metadata (frontmatter) in YAML, TOML, or JSON
format. YAML ``---`` frontmatter is the de facto standard used by Jekyll, Hugo,
Astro, MkDocs, Obsidian, and many other tools.

Example::

    from frontmatter import loads, dumps, Document

    # Parse
    doc = loads(\"\"\"---
    title: Hello World
    tags: [python, zerodep]
    ---
    # Hello

    This is the content.
    \"\"\")
    print(doc.metadata)  # {'title': 'Hello World', 'tags': ['python', 'zerodep']}
    print(doc.content)   # '# Hello\\n\\nThis is the content.\\n'

    # Serialize
    doc = Document({"title": "New Post"}, "Some content.")
    print(dumps(doc))

    # TOML frontmatter (Python 3.11+)
    doc = loads(\"\"\"+++
    title = "Hello"
    +++
    Content here.
    \"\"\")

    # JSON frontmatter
    doc = loads('{\"title\": \"Hello\"}\\nContent here.')

Requires Python 3.10+.
"""

from __future__ import annotations

import dataclasses
import json
import os
import sys
from pathlib import Path
from typing import IO, Any

# ── Sibling yaml import (guarded) ──

try:
    _yaml_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "yaml")
    if _yaml_dir not in sys.path:
        sys.path.insert(0, _yaml_dir)
    from yaml import dump as _yaml_dump
    from yaml import load as _yaml_load

    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

# ── Optional TOML support (Python 3.11+ stdlib) ──

try:
    import tomllib  # Python 3.11+

    _HAS_TOMLLIB = True
except ImportError:
    _HAS_TOMLLIB = False


# ── Constants ──

_YAML_FENCE = "---"
_TOML_FENCE = "+++"
_BOM = "\ufeff"


# ── Exceptions ──


class FrontmatterError(Exception):
    """Base exception for frontmatter parsing errors."""


class HandlerError(FrontmatterError):
    """Raised when a requested handler is not available."""


# ── Data class ──


@dataclasses.dataclass
class Document:
    """A document with frontmatter metadata and body content.

    Attributes:
        metadata: Parsed frontmatter key-value pairs.
        content: The body text after the frontmatter block.
    """

    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)
    content: str = ""

    def __bool__(self) -> bool:
        return bool(self.metadata) or bool(self.content)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a metadata value by key."""
        return self.metadata.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.metadata[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.metadata

    def keys(self) -> Any:
        """Return metadata keys."""
        return self.metadata.keys()

    def values(self) -> Any:
        """Return metadata values."""
        return self.metadata.values()

    def items(self) -> Any:
        """Return metadata items."""
        return self.metadata.items()


# ── Handler registry ──

_Handler = str  # "yaml" | "toml" | "json"


def _parse_yaml(raw: str) -> dict[str, Any]:
    """Parse YAML frontmatter content."""
    if not _HAS_YAML:
        raise HandlerError(
            "YAML handler requires the sibling yaml module. "
            "Place yaml.py in a sibling directory or on sys.path."
        )
    result = _yaml_load(raw)
    if not isinstance(result, dict):
        raise FrontmatterError(
            f"YAML frontmatter must be a mapping, got {type(result).__name__}"
        )
    return result


def _dump_yaml(data: dict[str, Any], **kwargs: Any) -> str:
    """Serialize metadata to YAML."""
    if not _HAS_YAML:
        raise HandlerError(
            "YAML handler requires the sibling yaml module. "
            "Place yaml.py in a sibling directory or on sys.path."
        )
    sort_keys = kwargs.pop("sort_keys", False)
    result = _yaml_dump(data, sort_keys=sort_keys, **kwargs)
    assert isinstance(result, str)
    return result


def _parse_toml(raw: str) -> dict[str, Any]:
    """Parse TOML frontmatter content."""
    if not _HAS_TOMLLIB:
        raise HandlerError("TOML handler requires Python 3.11+ (tomllib)")
    return tomllib.loads(raw)


def _dump_toml(data: dict[str, Any], **_kwargs: Any) -> str:
    """Serialize metadata to TOML (simple key=value format)."""
    lines: list[str] = []
    for key, value in data.items():
        lines.append(f"{key} = {_toml_value(value)}")
    return "\n".join(lines) + "\n" if lines else ""


def _toml_value(value: Any) -> str:
    """Format a Python value as a TOML literal."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)  # JSON string escaping is TOML-compatible
    if isinstance(value, list):
        items = ", ".join(_toml_value(v) for v in value)
        return f"[{items}]"
    if isinstance(value, dict):
        raise FrontmatterError(
            "TOML serialization of nested tables in frontmatter "
            "is not supported; use YAML handler instead."
        )
    return json.dumps(value)


def _parse_json(raw: str) -> dict[str, Any]:
    """Parse JSON frontmatter content."""
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise FrontmatterError(
            f"JSON frontmatter must be an object, got {type(result).__name__}"
        )
    return result


def _dump_json(data: dict[str, Any], **kwargs: Any) -> str:
    """Serialize metadata to JSON."""
    indent = kwargs.pop("indent", 2)
    ensure_ascii = kwargs.pop("ensure_ascii", False)
    return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii, **kwargs) + "\n"


# ── Detection and parsing ──


def detect_handler(text: str) -> str | None:
    """Detect the frontmatter format of a text string.

    Args:
        text: The full document text.

    Returns:
        ``"yaml"``, ``"toml"``, ``"json"``, or ``None`` if no frontmatter
        is detected.
    """
    stripped = text.lstrip(_BOM)
    if stripped.startswith(_YAML_FENCE + "\n") or stripped.startswith(
        _YAML_FENCE + "\r\n"
    ):
        return "yaml"
    if stripped.startswith(_TOML_FENCE + "\n") or stripped.startswith(
        _TOML_FENCE + "\r\n"
    ):
        return "toml"
    if stripped.startswith("{"):
        return "json"
    return None


def check(text: str) -> bool:
    """Check whether a text string contains frontmatter.

    Args:
        text: The full document text.

    Returns:
        ``True`` if frontmatter is detected.
    """
    return detect_handler(text) is not None


def _split_fenced(text: str, fence: str) -> tuple[str, str] | None:
    """Split text at a fenced frontmatter block.

    Returns (raw_frontmatter, body) or None if no valid block found.
    """
    stripped = text.lstrip(_BOM)
    if not (stripped.startswith(fence + "\n") or stripped.startswith(fence + "\r\n")):
        return None

    # Find the closing fence
    start = stripped.index("\n") + 1
    end = stripped.find("\n" + fence, start)
    if end == -1:
        return None

    raw = stripped[start:end]

    # Body starts after closing fence line
    body_start = end + 1 + len(fence)
    if body_start < len(stripped) and stripped[body_start] == "\n":
        body_start += 1
    elif (
        body_start + 1 < len(stripped)
        and stripped[body_start : body_start + 2] == "\r\n"
    ):
        body_start += 2

    body = stripped[body_start:]
    return raw, body


def _split_json(text: str) -> tuple[str, str] | None:
    """Split text at a JSON frontmatter block (opening ``{`` to matching ``}``)."""
    stripped = text.lstrip(_BOM)
    if not stripped.startswith("{"):
        return None

    # Find matching closing brace (handle nesting)
    depth = 0
    in_string = False
    escape = False
    for i, ch in enumerate(stripped):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                raw = stripped[: i + 1]
                body = stripped[i + 1 :]
                # Strip leading newline from body
                if body.startswith("\r\n"):
                    body = body[2:]
                elif body.startswith("\n"):
                    body = body[1:]
                return raw, body
    return None


# ── Public API ──


def loads(text: str, *, handler: str | None = None) -> Document:
    """Parse a text string with frontmatter.

    Args:
        text: The full document text.
        handler: Force a specific format (``"yaml"``, ``"toml"``, ``"json"``).
            If ``None``, the format is auto-detected.

    Returns:
        A ``Document`` with parsed metadata and body content.

    Raises:
        FrontmatterError: If parsing fails.
        HandlerError: If the requested handler is not available.

    Example::

        doc = loads("---\\ntitle: Hello\\n---\\nBody text.")
        doc.metadata  # {'title': 'Hello'}
        doc.content   # 'Body text.'
    """
    if handler is None:
        handler = detect_handler(text)

    if handler is None:
        # No frontmatter detected — entire text is content
        return Document(metadata={}, content=text)

    if handler == "yaml":
        parts = _split_fenced(text, _YAML_FENCE)
        if parts is None:
            return Document(metadata={}, content=text)
        raw, body = parts
        if not raw.strip():
            return Document(metadata={}, content=body)
        metadata = _parse_yaml(raw)
        return Document(metadata=metadata, content=body)

    if handler == "toml":
        parts = _split_fenced(text, _TOML_FENCE)
        if parts is None:
            return Document(metadata={}, content=text)
        raw, body = parts
        if not raw.strip():
            return Document(metadata={}, content=body)
        metadata = _parse_toml(raw)
        return Document(metadata=metadata, content=body)

    if handler == "json":
        parts = _split_json(text)
        if parts is None:
            return Document(metadata={}, content=text)
        raw, body = parts
        metadata = _parse_json(raw)
        return Document(metadata=metadata, content=body)

    raise HandlerError(f"unknown handler: {handler!r} (expected yaml/toml/json)")


def load(
    source: IO[str] | str | Path,
    *,
    handler: str | None = None,
) -> Document:
    """Parse a file with frontmatter.

    Args:
        source: A file path (``str`` or ``Path``) or an open text stream.
        handler: Force a specific format. If ``None``, auto-detect.

    Returns:
        A ``Document`` with parsed metadata and body content.

    Example::

        doc = load("post.md")
        doc = load(Path("post.md"))
        with open("post.md") as f:
            doc = load(f)
    """
    if isinstance(source, (str, Path)):
        text = Path(source).read_text(encoding="utf-8")
    else:
        text = source.read()
    return loads(text, handler=handler)


def dumps(
    doc: Document,
    *,
    handler: str = "yaml",
    **kwargs: Any,
) -> str:
    """Serialize a ``Document`` to a string with frontmatter.

    Args:
        doc: The document to serialize.
        handler: Output format (``"yaml"``, ``"toml"``, ``"json"``).
            Defaults to ``"yaml"``.
        **kwargs: Passed to the underlying serializer.

    Returns:
        The full document text with frontmatter and body.

    Example::

        doc = Document({"title": "Hello"}, "Body text.")
        text = dumps(doc)
        # ---
        # title: Hello
        # ---
        # Body text.
    """
    if handler == "yaml":
        fence = _YAML_FENCE
        raw = _dump_yaml(doc.metadata, **kwargs) if doc.metadata else ""
    elif handler == "toml":
        fence = _TOML_FENCE
        raw = _dump_toml(doc.metadata, **kwargs) if doc.metadata else ""
    elif handler == "json":
        raw_json = _dump_json(doc.metadata, **kwargs) if doc.metadata else ""
        # JSON uses { } as delimiters, no fence
        if doc.content:
            return raw_json + doc.content
        return raw_json
    else:
        raise HandlerError(f"unknown handler: {handler!r} (expected yaml/toml/json)")

    parts = [fence, "\n"]
    if raw:
        # Ensure raw ends with newline
        if not raw.endswith("\n"):
            raw += "\n"
        parts.append(raw)
    parts.append(fence)
    parts.append("\n")
    if doc.content:
        parts.append(doc.content)
    return "".join(parts)


def dump(
    doc: Document,
    dest: IO[str] | str | Path,
    *,
    handler: str = "yaml",
    **kwargs: Any,
) -> None:
    """Serialize a ``Document`` to a file with frontmatter.

    Args:
        doc: The document to serialize.
        dest: A file path (``str`` or ``Path``) or an open text stream.
        handler: Output format. Defaults to ``"yaml"``.
        **kwargs: Passed to the underlying serializer.

    Example::

        dump(doc, "post.md")
        dump(doc, Path("post.md"), handler="toml")
        with open("post.md", "w") as f:
            dump(doc, f)
    """
    text = dumps(doc, handler=handler, **kwargs)
    if isinstance(dest, (str, Path)):
        Path(dest).write_text(text, encoding="utf-8")
    else:
        dest.write(text)
