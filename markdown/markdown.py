# /// zerodep
# version = "0.4.1"
# deps = []
# tier = "medium"
# category = "text"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///

"""Markdown to HTML renderer — zero dependencies, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Drop-in replacement for mistune's ``mistune.html()`` for common Markdown.

Supports:
    - ATX and Setext headings
    - Paragraphs, thematic breaks, hard line breaks
    - Emphasis (bold, italic, bold-italic)
    - Inline code and fenced/indented code blocks
    - Links (inline, reference, autolink) and images
    - Ordered and unordered lists with nesting
    - Block quotes with nesting
    - GFM tables with column alignment
    - GFM strikethrough (~~text~~)
    - GFM task lists (- [ ] / - [x])
    - GFM extended autolinks (bare URLs)
    - Backslash escapes

Does NOT implement:
    - Raw HTML passthrough (escaped for safety)
    - Footnotes, definition lists, math/LaTeX

Example::

    from markdown import render
    render("# Hello\\n\\nThis is **bold**.")
    # '<h1>Hello</h1>\\n<p>This is <strong>bold</strong>.</p>\\n'
"""

from __future__ import annotations

import html
import re

__all__ = [
    "render",
]

# ── Constants ─────────────────────────────────────────────────────────────────

_ESCAPED_CHARS = r"\\!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~"

_HARMFUL_PROTOCOLS = ("javascript:", "vbscript:", "file:", "data:")
_SAFE_DATA_PREFIXES = (
    "data:image/gif;",
    "data:image/png;",
    "data:image/jpeg;",
    "data:image/webp;",
)

# ── Block-level patterns ─────────────────────────────────────────────────────

_ATX_HEADING_RE = re.compile(r"^(#{1,6})(?:\s+|$)(.*?)(?:\s+#+\s*)?$")
_SETEXT_HEADING_RE = re.compile(r"^(=+|-+)\s*$")
_FENCED_CODE_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})\s*(\S*)\s*$")
_THEMATIC_BREAK_RE = re.compile(
    r"^ {0,3}(?:(?:-[ \t]*){3,}|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,})\s*$"
)
_BLOCK_QUOTE_RE = re.compile(r"^ {0,3}>[ \t]?(.*)")
_UL_ITEM_RE = re.compile(r"^( *)([-*+]) (.*)")
_OL_ITEM_RE = re.compile(r"^( *)(\d{1,9})([.)]) (.*)")
_INDENT_CODE_RE = re.compile(r"^(?: {4}|\t)(.*)")
_REF_LINK_RE = re.compile(
    r"""^ {0,3}\[([^\]]+)\]:\s+<?(\S+?)>?(?:\s+["'(](.+?)["')])?\s*$"""
)
_TABLE_DELIM_RE = re.compile(
    r"^ {0,3}\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?\s*$"
)
_BLANK_RE = re.compile(r"^\s*$")

# ── Inline patterns ──────────────────────────────────────────────────────────

_BACKSLASH_ESCAPE_RE = re.compile(r"\\([" + _ESCAPED_CHARS + r"])")
_CODE_SPAN_RE = re.compile(r"(?<!`)(`+)(?!`)([\s\S]*?[^`])(\1)(?!`)")
_AUTOLINK_RE = re.compile(r"<([a-zA-Z][a-zA-Z0-9.+-]{1,31}:[^<>\s]*)>")
_AUTOEMAIL_RE = re.compile(
    r"<([a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)>"
)
_IMAGE_RE = re.compile(
    r"!\[([^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*)\]"
    r"""\(\s*(\S+?)(?:\s+["'](.+?)["'])?\s*\)"""
)
_LINK_RE = re.compile(
    r"\[([^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*)\]"
    r"""\(\s*(\S+?)(?:\s+["'](.+?)["'])?\s*\)"""
)
_REF_LINK_USE_RE = re.compile(r"\[([^\[\]]+)\]\[([^\[\]]*)\]")
_REF_LINK_SHORT_RE = re.compile(r"\[([^\[\]]+)\](?!\()")
_STRONG_EM_RE = re.compile(r"\*{3}(.+?)\*{3}|_{3}(.+?)_{3}")
_STRONG_RE = re.compile(r"\*{2}(.+?)\*{2}|_{2}(.+?)_{2}")
_EM_RE = re.compile(r"(?<!\w)\*(.+?)\*(?!\w)|(?<!\w)_(.+?)_(?!\w)")
_STRIKETHROUGH_RE = re.compile(r"~~(.+?)~~")
_BARE_URL_RE = re.compile(r"(https?://[^\s<>\[\]]*[^\s<>\[\].,;:!?'\")}\]])")
_HARD_BREAK_RE = re.compile(r"(?:\\| {2,})\n")

# Task list marker: [ ], [x], or [X] at start of list item content
_TASK_LIST_RE = re.compile(r"^\[([ xX])\]\s+")

# ── Placeholder system ───────────────────────────────────────────────────────

_PH_PREFIX = "\x00PH"
_PH_SUFFIX = "\x00"


class _Placeholders:
    """Manages placeholder substitution to protect parsed regions."""

    __slots__ = ("_store", "_counter")

    def __init__(self) -> None:
        self._store: list[str] = []
        self._counter = 0

    def put(self, value: str) -> str:
        idx = self._counter
        self._counter += 1
        self._store.append(value)
        return f"{_PH_PREFIX}{idx}{_PH_SUFFIX}"

    def restore(self, text: str) -> str:
        for i in range(len(self._store) - 1, -1, -1):
            text = text.replace(f"{_PH_PREFIX}{i}{_PH_SUFFIX}", self._store[i])
        return text


# ── URL safety ────────────────────────────────────────────────────────────────


def _safe_url(url: str) -> str:
    """Sanitize a URL, blocking dangerous protocols."""
    lower = url.strip().lower()
    if lower.startswith(_HARMFUL_PROTOCOLS) and not lower.startswith(
        _SAFE_DATA_PREFIXES
    ):
        return "#harmful-link"
    return html.escape(url, quote=True)


# ── Inline helper functions ──────────────────────────────────────────────────


def _apply_bare_urls(text: str, ph: _Placeholders) -> str:
    """Replace bare http/https URLs with link placeholders."""

    def _bare_url_repl(m: re.Match[str]) -> str:
        url = m.group(1)
        return ph.put('<a href="' + _safe_url(url) + '">' + html.escape(url) + "</a>")

    return _BARE_URL_RE.sub(_bare_url_repl, text)


def _apply_emphasis(
    text: str,
    ph: _Placeholders,
    ref_links: dict[str, tuple[str, str | None]],
) -> str:
    """Apply bold-italic, bold, italic, and strikethrough replacements."""

    # Bold-italic ***text***
    def _strong_em_repl(m: re.Match[str]) -> str:
        content = m.group(1) or m.group(2)
        return ph.put(
            "<em><strong>" + _parse_inline(content, ref_links) + "</strong></em>"
        )

    text = _STRONG_EM_RE.sub(_strong_em_repl, text)

    # Bold **text**
    def _strong_repl(m: re.Match[str]) -> str:
        content = m.group(1) or m.group(2)
        return ph.put("<strong>" + _parse_inline(content, ref_links) + "</strong>")

    text = _STRONG_RE.sub(_strong_repl, text)

    # Italic *text*
    def _em_repl(m: re.Match[str]) -> str:
        content = m.group(1) or m.group(2)
        return ph.put("<em>" + _parse_inline(content, ref_links) + "</em>")

    text = _EM_RE.sub(_em_repl, text)

    # Strikethrough ~~text~~
    def _strike_repl(m: re.Match[str]) -> str:
        content = m.group(1)
        return ph.put("<del>" + _parse_inline(content, ref_links) + "</del>")

    text = _STRIKETHROUGH_RE.sub(_strike_repl, text)
    return text


# ── Inline parser ─────────────────────────────────────────────────────────────


def _parse_inline(
    text: str,
    ref_links: dict[str, tuple[str, str | None]],
) -> str:
    """Parse inline Markdown elements and return HTML."""
    ph = _Placeholders()

    # 1. Backslash escapes → placeholder
    def _escape_repl(m: re.Match[str]) -> str:
        return ph.put(html.escape(m.group(1), quote=True))

    text = _BACKSLASH_ESCAPE_RE.sub(_escape_repl, text)

    # 2. Code spans → placeholder (no further parsing inside)
    def _code_repl(m: re.Match[str]) -> str:
        code = m.group(2).strip()
        return ph.put("<code>" + html.escape(code, quote=True) + "</code>")

    text = _CODE_SPAN_RE.sub(_code_repl, text)

    # 3. Autolinks
    def _autolink_repl(m: re.Match[str]) -> str:
        url = m.group(1)
        return ph.put('<a href="' + _safe_url(url) + '">' + html.escape(url) + "</a>")

    text = _AUTOLINK_RE.sub(_autolink_repl, text)

    # 3b. Auto emails
    def _autoemail_repl(m: re.Match[str]) -> str:
        email = m.group(1)
        return ph.put(
            '<a href="mailto:' + html.escape(email) + '">' + html.escape(email) + "</a>"
        )

    text = _AUTOEMAIL_RE.sub(_autoemail_repl, text)

    # 4. Images
    def _image_repl(m: re.Match[str]) -> str:
        alt = html.escape(m.group(1), quote=True)
        url = _safe_url(m.group(2))
        title = m.group(3)
        s = '<img src="' + url + '" alt="' + alt + '"'
        if title:
            s += ' title="' + html.escape(title, quote=True) + '"'
        s += " />"
        return ph.put(s)

    text = _IMAGE_RE.sub(_image_repl, text)

    # 5. Inline links
    def _link_repl(m: re.Match[str]) -> str:
        link_text = _parse_inline(m.group(1), ref_links)
        url = _safe_url(m.group(2))
        title = m.group(3)
        s = '<a href="' + url + '"'
        if title:
            s += ' title="' + html.escape(title, quote=True) + '"'
        s += ">" + link_text + "</a>"
        return ph.put(s)

    text = _LINK_RE.sub(_link_repl, text)

    # 5b. Reference links [text][ref]
    def _ref_link_repl(m: re.Match[str]) -> str:
        link_text = m.group(1)
        ref_key = (m.group(2) or link_text).strip().lower()
        ref = ref_links.get(ref_key)
        if ref is None:
            return m.group(0)
        url, title = ref
        s = '<a href="' + _safe_url(url) + '"'
        if title:
            s += ' title="' + html.escape(title, quote=True) + '"'
        s += ">" + _parse_inline(link_text, ref_links) + "</a>"
        return ph.put(s)

    text = _REF_LINK_USE_RE.sub(_ref_link_repl, text)

    # 5c. Shortcut reference links [ref]
    def _ref_short_repl(m: re.Match[str]) -> str:
        link_text = m.group(1)
        ref_key = link_text.strip().lower()
        ref = ref_links.get(ref_key)
        if ref is None:
            return m.group(0)
        url, title = ref
        s = '<a href="' + _safe_url(url) + '"'
        if title:
            s += ' title="' + html.escape(title, quote=True) + '"'
        s += ">" + _parse_inline(link_text, ref_links) + "</a>"
        return ph.put(s)

    text = _REF_LINK_SHORT_RE.sub(_ref_short_repl, text)

    # 5d. Extended autolinks (bare URLs without angle brackets)
    text = _apply_bare_urls(text, ph)

    # 6. Emphasis + strikethrough
    text = _apply_emphasis(text, ph, ref_links)

    # 7. Hard line breaks (protect with placeholder)
    text = _HARD_BREAK_RE.sub(lambda m: ph.put("<br />\n"), text)

    # 8. Escape remaining HTML in text
    # We need to be careful: only escape text that hasn't been processed.
    # The placeholder system handles this — placeholders contain final HTML.
    # We escape the remaining raw text segments between placeholders.
    parts = re.split(r"(\x00PH\d+\x00)", text)
    for i, part in enumerate(parts):
        if not part.startswith(_PH_PREFIX):
            parts[i] = html.escape(part, quote=False)
    text = "".join(parts)

    # 9. Restore placeholders
    text = ph.restore(text)

    return text


# ── Table parser ──────────────────────────────────────────────────────────────


def _parse_table_row(line: str) -> list[str]:
    """Split a table row into cells."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    # Split on unescaped pipes
    cells = re.split(r"(?<!\\)\|", line)
    return [c.strip() for c in cells]


def _parse_table_align(line: str) -> list[str | None]:
    """Parse alignment row, return list of 'left', 'right', 'center', or None."""
    cells = _parse_table_row(line)
    aligns: list[str | None] = []
    for cell in cells:
        cell = cell.strip()
        left = cell.startswith(":")
        right = cell.endswith(":")
        if left and right:
            aligns.append("center")
        elif right:
            aligns.append("right")
        elif left:
            aligns.append("left")
        else:
            aligns.append(None)
    return aligns


def _render_table(
    header_line: str,
    align_line: str,
    body_lines: list[str],
    ref_links: dict[str, tuple[str, str | None]],
) -> str:
    """Render a GFM table to HTML."""
    headers = _parse_table_row(header_line)
    aligns = _parse_table_align(align_line)

    out: list[str] = ["<table>\n<thead>\n<tr>\n"]
    for i, h in enumerate(headers):
        align = aligns[i] if i < len(aligns) else None
        style = f' style="text-align:{align}"' if align else ""
        out.append(f"  <th{style}>{_parse_inline(h, ref_links)}</th>\n")
    out.append("</tr>\n</thead>\n")

    if body_lines:
        out.append("<tbody>\n")
        for line in body_lines:
            cells = _parse_table_row(line)
            out.append("<tr>\n")
            for i, cell in enumerate(cells):
                align = aligns[i] if i < len(aligns) else None
                style = f' style="text-align:{align}"' if align else ""
                out.append(f"  <td{style}>{_parse_inline(cell, ref_links)}</td>\n")
            out.append("</tr>\n")
        out.append("</tbody>\n")

    out.append("</table>\n")
    return "".join(out)


# ── List parser ───────────────────────────────────────────────────────────────


def _detect_list_type(
    line: str,
) -> tuple[bool, int, int] | None:
    """Detect whether a line starts a list item.

    Returns:
        (ordered, base_indent, start_num) or None if not a list item.
    """
    ol_m = _OL_ITEM_RE.match(line)
    if ol_m:
        return True, len(ol_m.group(1)), int(ol_m.group(2))
    ul_m = _UL_ITEM_RE.match(line)
    if ul_m:
        return False, len(ul_m.group(1)), 1
    return None


def _blank_continues_list(
    lines: list[str],
    idx: int,
    ordered: bool,
    base_indent: int,
) -> bool:
    """Check whether a blank line at *idx* is followed by list continuation."""
    if idx + 1 >= len(lines):
        return False
    next_line = lines[idx + 1]
    if _BLANK_RE.match(next_line):
        return False
    # Same-level item?
    if ordered:
        m = _OL_ITEM_RE.match(next_line)
        if m and len(m.group(1)) == base_indent:
            return True
    else:
        m = _UL_ITEM_RE.match(next_line)
        if m and len(m.group(1)) == base_indent:
            return True
    # Indented continuation / nested content
    next_indent = len(next_line) - len(next_line.lstrip())
    return next_indent > base_indent


def _match_same_level_item(
    line: str,
    ordered: bool,
    base_indent: int,
) -> str | None:
    """If *line* is a same-level list item, return its content text."""
    if ordered:
        m = _OL_ITEM_RE.match(line)
        if m and len(m.group(1)) == base_indent:
            return m.group(4)
    else:
        m = _UL_ITEM_RE.match(line)
        if m and len(m.group(1)) == base_indent:
            return m.group(3)
    return None


def _collect_list_items(
    lines: list[str],
    start_idx: int,
    ordered: bool,
    base_indent: int,
) -> tuple[list[list[str]], int]:
    """Collect raw item line groups from a list block.

    Returns:
        (items, next_idx) where each item is a list of content lines.
    """
    idx = start_idx
    items: list[list[str]] = []
    current: list[str] = []

    while idx < len(lines):
        line = lines[idx]

        # Blank line — may separate items or end the list
        if _BLANK_RE.match(line):
            if _blank_continues_list(lines, idx, ordered, base_indent):
                current.append("")
                idx += 1
                continue
            break

        # Same-level item starts a new entry
        content = _match_same_level_item(line, ordered, base_indent)
        if content is not None:
            if current:
                items.append(current)
            current = [content]
            idx += 1
            continue

        # Nested / continuation line
        indent = len(line) - len(line.lstrip())
        if indent > base_indent and current:
            dedented = line[base_indent + 2 :] if len(line) > base_indent + 2 else ""
            current.append(dedented)
            idx += 1
            continue

        break

    if current:
        items.append(current)
    return items, idx


def _render_list_item(
    item_lines: list[str],
    ref_links: dict[str, tuple[str, str | None]],
) -> str:
    """Render a single <li> element, recursing for nested sub-lists."""
    # Detect task list marker
    task_class = ""
    task_checkbox = ""
    first_line = item_lines[0]
    task_m = _TASK_LIST_RE.match(first_line)
    if task_m:
        checked = task_m.group(1) in ("x", "X")
        task_class = ' class="task-list-item"'
        task_checkbox = (
            '<input class="task-list-item-checkbox" type="checkbox" disabled'
        )
        if checked:
            task_checkbox += " checked"
        task_checkbox += "/>"
        item_lines = [first_line[task_m.end() :]] + item_lines[1:]

    has_sublist = any(
        _UL_ITEM_RE.match(il) or _OL_ITEM_RE.match(il) for il in item_lines[1:]
    )
    open_tag = f"<li{task_class}>" + task_checkbox
    if has_sublist:
        first = _parse_inline(item_lines[0], ref_links)
        sub_html = _parse_blocks(item_lines[1:], ref_links)
        return open_tag + first + sub_html + "</li>\n"
    content = "\n".join(item_lines).strip()
    return open_tag + _parse_inline(content, ref_links) + "</li>\n"


def _parse_list_block(
    lines: list[str],
    start_idx: int,
    ref_links: dict[str, tuple[str, str | None]],
) -> tuple[str, int]:
    """Parse a list block starting at *start_idx*. Returns (html, next_idx)."""
    info = _detect_list_type(lines[start_idx])
    if info is None:
        return "", start_idx
    ordered, base_indent, start_num = info

    items, idx = _collect_list_items(lines, start_idx, ordered, base_indent)

    tag = "ol" if ordered else "ul"
    start_attr = f' start="{start_num}"' if ordered and start_num != 1 else ""
    parts: list[str] = [f"<{tag}{start_attr}>\n"]
    for item_lines in items:
        parts.append(_render_list_item(item_lines, ref_links))
    parts.append(f"</{tag}>\n")
    return "".join(parts), idx


# ── Block-level try-parse helpers ────────────────────────────────────────────

_BlockResult = tuple[str, int, bool]
"""(html, new_idx, consumed_para) returned by each _try_parse_* helper."""


def _try_parse_hr(
    lines: list[str],
    idx: int,
    ref_links: dict[str, tuple[str, str | None]],
    para_lines: list[str],
) -> _BlockResult | None:
    """Try to parse a thematic break."""
    if para_lines:
        return None
    if _THEMATIC_BREAK_RE.match(lines[idx]):
        return "<hr />\n", idx + 1, False
    return None


def _try_parse_atx_heading(
    lines: list[str],
    idx: int,
    ref_links: dict[str, tuple[str, str | None]],
    para_lines: list[str],
) -> _BlockResult | None:
    """Try to parse an ATX heading."""
    if para_lines:
        return None
    m = _ATX_HEADING_RE.match(lines[idx])
    if not m:
        return None
    level = len(m.group(1))
    content = re.sub(r"\s+#+\s*$", "", m.group(2).strip())
    tag = f"h{level}"
    h = f"<{tag}>{_parse_inline(content, ref_links)}</{tag}>\n"
    return h, idx + 1, False


def _try_parse_setext_heading(
    lines: list[str],
    idx: int,
    ref_links: dict[str, tuple[str, str | None]],
    para_lines: list[str],
) -> _BlockResult | None:
    """Try to parse a Setext heading (requires accumulated paragraph lines)."""
    if not para_lines:
        return None
    line = lines[idx]
    if not _SETEXT_HEADING_RE.match(line):
        return None
    level = 1 if line.strip().startswith("=") else 2
    content = "\n".join(para_lines)
    tag = f"h{level}"
    h = f"<{tag}>{_parse_inline(content.strip(), ref_links)}</{tag}>\n"
    return h, idx + 1, True  # consumed_para=True


def _try_parse_code_fence(
    lines: list[str],
    idx: int,
    ref_links: dict[str, tuple[str, str | None]],
    para_lines: list[str],
) -> _BlockResult | None:
    """Try to parse a fenced code block."""
    if para_lines:
        return None
    m = _FENCED_CODE_RE.match(lines[idx])
    if not m:
        return None
    fence_indent = len(m.group(1))
    fence_char = m.group(2)[0]
    fence_len = len(m.group(2))
    lang = m.group(3).strip()

    code_lines: list[str] = []
    j = idx + 1
    close_re = re.compile(
        r"^ {0,3}" + re.escape(fence_char) + r"{" + str(fence_len) + r",}\s*$"
    )
    while j < len(lines):
        cl = lines[j]
        if close_re.match(cl):
            j += 1
            break
        code_lines.append(_strip_fence_indent(cl, fence_indent))
        j += 1

    code = "\n".join(code_lines)
    if code and not code.endswith("\n"):
        code += "\n"
    escaped_code = html.escape(code, quote=False)
    lang_attr = f' class="language-{html.escape(lang, quote=True)}"' if lang else ""
    h = f"<pre><code{lang_attr}>{escaped_code}</code></pre>\n"
    return h, j, False


def _strip_fence_indent(line: str, indent: int) -> str:
    """Remove up to *indent* leading spaces from *line*."""
    if indent <= 0:
        return line
    for _ in range(indent):
        if line.startswith(" "):
            line = line[1:]
        else:
            break
    return line


def _try_parse_indent_code(
    lines: list[str],
    idx: int,
    ref_links: dict[str, tuple[str, str | None]],
    para_lines: list[str],
) -> _BlockResult | None:
    """Try to parse an indented code block (4-space indent)."""
    if para_lines:
        return None
    if not _INDENT_CODE_RE.match(lines[idx]):
        return None

    code_lines: list[str] = []
    j = idx
    while j < len(lines):
        ic_m = _INDENT_CODE_RE.match(lines[j])
        if ic_m:
            code_lines.append(ic_m.group(1))
            j += 1
        elif _BLANK_RE.match(lines[j]):
            if j + 1 < len(lines) and _INDENT_CODE_RE.match(lines[j + 1]):
                code_lines.append("")
                j += 1
            else:
                break
        else:
            break
    # Remove trailing blank lines
    while code_lines and code_lines[-1] == "":
        code_lines.pop()
    escaped_code = html.escape("\n".join(code_lines), quote=False)
    h = f"<pre><code>{escaped_code}</code></pre>\n"
    return h, j, False


def _try_parse_blockquote(
    lines: list[str],
    idx: int,
    ref_links: dict[str, tuple[str, str | None]],
    para_lines: list[str],
) -> _BlockResult | None:
    """Try to parse a block quote (can interrupt a paragraph)."""
    if not _BLOCK_QUOTE_RE.match(lines[idx]):
        return None

    bq_lines: list[str] = []
    j = idx
    while j < len(lines):
        bq_match = _BLOCK_QUOTE_RE.match(lines[j])
        if bq_match:
            bq_lines.append(bq_match.group(1))
            j += 1
        elif _BLANK_RE.match(lines[j]):
            if j + 1 < len(lines) and _BLOCK_QUOTE_RE.match(lines[j + 1]):
                bq_lines.append("")
                j += 1
            else:
                break
        elif lines[j].strip():
            # Lazy continuation
            bq_lines.append(lines[j])
            j += 1
        else:
            break
    inner = _parse_blocks(bq_lines, ref_links)
    h = "<blockquote>\n" + inner + "</blockquote>\n"
    return h, j, False


def _try_parse_list(
    lines: list[str],
    idx: int,
    ref_links: dict[str, tuple[str, str | None]],
    para_lines: list[str],
) -> _BlockResult | None:
    """Try to parse an ordered or unordered list."""
    if para_lines:
        return None
    if not (_UL_ITEM_RE.match(lines[idx]) or _OL_ITEM_RE.match(lines[idx])):
        return None
    list_html, new_idx = _parse_list_block(lines, idx, ref_links)
    return list_html, new_idx, False


def _try_parse_table(
    lines: list[str],
    idx: int,
    ref_links: dict[str, tuple[str, str | None]],
    para_lines: list[str],
) -> _BlockResult | None:
    """Try to parse a GFM table."""
    if para_lines:
        return None
    line = lines[idx]
    if "|" not in line or idx + 1 >= len(lines):
        return None
    if not _TABLE_DELIM_RE.match(lines[idx + 1]):
        return None

    header_line = line
    align_line = lines[idx + 1]
    body: list[str] = []
    j = idx + 2
    while j < len(lines):
        tl = lines[j]
        if "|" in tl and not _BLANK_RE.match(tl):
            body.append(tl)
            j += 1
        else:
            break
    h = _render_table(header_line, align_line, body, ref_links)
    return h, j, False


# Ordered list of try-parse functions used by the block dispatcher.
_BLOCK_PARSERS = (
    _try_parse_hr,
    _try_parse_atx_heading,
    _try_parse_setext_heading,
    _try_parse_code_fence,
    _try_parse_indent_code,
    _try_parse_blockquote,
    _try_parse_list,
    _try_parse_table,
)


# ── Block parser ──────────────────────────────────────────────────────────────


def _collect_ref_links(
    lines: list[str],
) -> dict[str, tuple[str, str | None]]:
    """First pass: collect reference link definitions."""
    refs: dict[str, tuple[str, str | None]] = {}
    for line in lines:
        m = _REF_LINK_RE.match(line)
        if m:
            key = m.group(1).strip().lower()
            url = m.group(2)
            title = m.group(3)
            refs[key] = (url, title)
    return refs


def _parse_blocks(
    lines: list[str],
    ref_links: dict[str, tuple[str, str | None]],
) -> str:
    """Parse block-level Markdown elements from a list of lines."""
    out: list[str] = []
    idx = 0
    para_lines: list[str] = []

    def flush_paragraph() -> None:
        if para_lines:
            text = "\n".join(para_lines)
            out.append("<p>" + _parse_inline(text.strip(), ref_links) + "</p>\n")
            para_lines.clear()

    while idx < len(lines):
        line = lines[idx]

        # Skip reference link definitions (already collected)
        if _REF_LINK_RE.match(line):
            flush_paragraph()
            idx += 1
            continue

        # Blank line
        if _BLANK_RE.match(line):
            flush_paragraph()
            idx += 1
            continue

        # Try each block-level parser in priority order
        result = _dispatch_block(lines, idx, ref_links, para_lines)
        if result is not None:
            block_html, idx, consumed_para = result
            if consumed_para:
                para_lines.clear()
            else:
                flush_paragraph()
            out.append(block_html)
            continue

        # Paragraph accumulation
        para_lines.append(line)
        idx += 1

    flush_paragraph()
    return "".join(out)


def _dispatch_block(
    lines: list[str],
    idx: int,
    ref_links: dict[str, tuple[str, str | None]],
    para_lines: list[str],
) -> _BlockResult | None:
    """Try each registered block parser; return first match or None."""
    for try_fn in _BLOCK_PARSERS:
        result = try_fn(lines, idx, ref_links, para_lines)
        if result is not None:
            return result
    return None


# ── Public API ────────────────────────────────────────────────────────────────


def render(text: str) -> str:
    """Convert Markdown text to HTML.

    Args:
        text: Markdown source string.

    Returns:
        HTML string.
    """
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Split into lines
    lines = text.split("\n")

    # Remove trailing newline that produces empty last element
    if lines and lines[-1] == "":
        lines.pop()

    # First pass: collect reference link definitions
    ref_links = _collect_ref_links(lines)

    # Second pass: parse blocks
    return _parse_blocks(lines, ref_links)
