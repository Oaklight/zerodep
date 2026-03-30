# /// zerodep
# version = "0.2.1"
# deps = []
# tier = "medium"
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
    - Backslash escapes

Does NOT implement:
    - Raw HTML passthrough (escaped for safety)
    - Footnotes, definition lists, math/LaTeX
    - Strikethrough, task lists

Example::

    from markdown import render
    render("# Hello\\n\\nThis is **bold**.")
    # '<h1>Hello</h1>\\n<p>This is <strong>bold</strong>.</p>\\n'
"""

from __future__ import annotations

import html
import re

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
_HARD_BREAK_RE = re.compile(r"(?:\\| {2,})\n")

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

    # 6. Emphasis (process from longest to shortest, protect with placeholders)
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


def _parse_list_block(
    lines: list[str],
    start_idx: int,
    ref_links: dict[str, tuple[str, str | None]],
) -> tuple[str, int]:
    """Parse a list block starting at start_idx. Returns (html, next_idx)."""
    idx = start_idx
    first_line = lines[idx]

    ol_m = _OL_ITEM_RE.match(first_line)
    ul_m = _UL_ITEM_RE.match(first_line)

    if ol_m:
        ordered = True
        base_indent = len(ol_m.group(1))
        start_num = int(ol_m.group(2))
    elif ul_m:
        ordered = False
        base_indent = len(ul_m.group(1))
        start_num = 1
    else:
        return "", start_idx

    items: list[list[str]] = []
    current_item_lines: list[str] = []

    while idx < len(lines):
        line = lines[idx]

        if _BLANK_RE.match(line):
            # Blank line — could be between items or end of list
            # Look ahead to see if next line continues the list
            if idx + 1 < len(lines):
                next_line = lines[idx + 1]
                next_ol = _OL_ITEM_RE.match(next_line)
                next_ul = _UL_ITEM_RE.match(next_line)
                next_indent = len(next_line) - len(next_line.lstrip())

                if (ordered and next_ol and len(next_ol.group(1)) == base_indent) or (
                    not ordered and next_ul and len(next_ul.group(1)) == base_indent
                ):
                    # Next line is a same-level list item
                    current_item_lines.append("")
                    idx += 1
                    continue
                elif next_indent > base_indent and not _BLANK_RE.match(next_line):
                    # Continuation or nested content
                    current_item_lines.append("")
                    idx += 1
                    continue
            # End of list
            break

        if ordered:
            m = _OL_ITEM_RE.match(line)
            if m and len(m.group(1)) == base_indent:
                if current_item_lines:
                    items.append(current_item_lines)
                current_item_lines = [m.group(4)]
                idx += 1
                continue
        else:
            m = _UL_ITEM_RE.match(line)
            if m and len(m.group(1)) == base_indent:
                if current_item_lines:
                    items.append(current_item_lines)
                current_item_lines = [m.group(3)]
                idx += 1
                continue

        # Check for nested list or continuation
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent > base_indent and current_item_lines:
            # Remove the base indentation for nested content
            # Keep relative indent for nested lists
            dedented = line[base_indent + 2 :] if len(line) > base_indent + 2 else ""
            current_item_lines.append(dedented)
            idx += 1
            continue

        # Not part of this list
        break

    if current_item_lines:
        items.append(current_item_lines)

    # Render items
    tag = "ol" if ordered else "ul"
    start_attr = f' start="{start_num}"' if ordered and start_num != 1 else ""
    out: list[str] = [f"<{tag}{start_attr}>\n"]

    for item_lines in items:
        content = "\n".join(item_lines)
        # Check if item contains sub-list or multi-paragraph
        has_sublist = False
        for il in item_lines[1:]:
            if _UL_ITEM_RE.match(il) or _OL_ITEM_RE.match(il):
                has_sublist = True
                break

        if has_sublist:
            # Parse the first line as inline, then recurse for nested content
            first = _parse_inline(item_lines[0], ref_links)
            sub_lines = item_lines[1:]
            sub_html = _parse_blocks(sub_lines, ref_links)
            out.append("<li>" + first + sub_html + "</li>\n")
        else:
            rendered = _parse_inline(content.strip(), ref_links)
            out.append("<li>" + rendered + "</li>\n")

    out.append(f"</{tag}>\n")
    return "".join(out), idx


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

        # Thematic break (check before setext heading and list)
        if _THEMATIC_BREAK_RE.match(line) and not para_lines:
            flush_paragraph()
            out.append("<hr />\n")
            idx += 1
            continue

        # ATX heading
        m = _ATX_HEADING_RE.match(line)
        if m and not para_lines:
            flush_paragraph()
            level = len(m.group(1))
            content = m.group(2).strip()
            # Strip trailing # sequences
            content = re.sub(r"\s+#+\s*$", "", content)
            tag = f"h{level}"
            out.append(f"<{tag}>{_parse_inline(content, ref_links)}</{tag}>\n")
            idx += 1
            continue

        # Setext heading (only if we have accumulated paragraph lines)
        if para_lines and _SETEXT_HEADING_RE.match(line):
            level = 1 if line.strip().startswith("=") else 2
            content = "\n".join(para_lines)
            tag = f"h{level}"
            out.append(f"<{tag}>{_parse_inline(content.strip(), ref_links)}</{tag}>\n")
            para_lines.clear()
            idx += 1
            continue

        # Fenced code block
        m = _FENCED_CODE_RE.match(line)
        if m and not para_lines:
            flush_paragraph()
            fence_indent = len(m.group(1))
            fence_char = m.group(2)[0]
            fence_len = len(m.group(2))
            lang = m.group(3).strip()
            code_lines: list[str] = []
            idx += 1
            while idx < len(lines):
                cl = lines[idx]
                # Check for closing fence
                close_pat = (
                    r"^ {0,3}"
                    + re.escape(fence_char)
                    + r"{"
                    + str(fence_len)
                    + r",}\s*$"
                )
                close_m = re.match(close_pat, cl)
                if close_m:
                    idx += 1
                    break
                # Remove up to fence_indent spaces from start
                if fence_indent > 0:
                    stripped = cl
                    for _ in range(fence_indent):
                        if stripped.startswith(" "):
                            stripped = stripped[1:]
                        else:
                            break
                    code_lines.append(stripped)
                else:
                    code_lines.append(cl)
                idx += 1
            code = "\n".join(code_lines)
            if code and not code.endswith("\n"):
                code += "\n"
            escaped_code = html.escape(code, quote=False)
            if lang:
                lang_attr = f' class="language-{html.escape(lang, quote=True)}"'
            else:
                lang_attr = ""
            out.append(f"<pre><code{lang_attr}>{escaped_code}</code></pre>\n")
            continue

        # Indented code block (4 spaces, only if not in paragraph)
        if _INDENT_CODE_RE.match(line) and not para_lines:
            flush_paragraph()
            code_lines_ic: list[str] = []
            while idx < len(lines):
                ic_line = lines[idx]
                ic_m = _INDENT_CODE_RE.match(ic_line)
                if ic_m:
                    code_lines_ic.append(ic_m.group(1))
                    idx += 1
                elif _BLANK_RE.match(ic_line):
                    # Blank line might be part of code block
                    if idx + 1 < len(lines) and _INDENT_CODE_RE.match(lines[idx + 1]):
                        code_lines_ic.append("")
                        idx += 1
                    else:
                        break
                else:
                    break
            # Remove trailing blank lines
            while code_lines_ic and code_lines_ic[-1] == "":
                code_lines_ic.pop()
            code = "\n".join(code_lines_ic)
            escaped_code = html.escape(code, quote=False)
            out.append(f"<pre><code>{escaped_code}</code></pre>\n")
            continue

        # Block quote (can interrupt a paragraph per CommonMark spec)
        bq_m = _BLOCK_QUOTE_RE.match(line)
        if bq_m:
            flush_paragraph()
            bq_lines: list[str] = []
            while idx < len(lines):
                bq_line = lines[idx]
                bq_match = _BLOCK_QUOTE_RE.match(bq_line)
                if bq_match:
                    bq_lines.append(bq_match.group(1))
                    idx += 1
                elif _BLANK_RE.match(bq_line):
                    # Check if quote continues after blank
                    if idx + 1 < len(lines) and _BLOCK_QUOTE_RE.match(lines[idx + 1]):
                        bq_lines.append("")
                        idx += 1
                    else:
                        break
                elif bq_line.strip() and not _BLANK_RE.match(bq_line):
                    # Lazy continuation (paragraph text without >)
                    bq_lines.append(bq_line)
                    idx += 1
                else:
                    break
            inner = _parse_blocks(bq_lines, ref_links)
            out.append("<blockquote>\n" + inner + "</blockquote>\n")
            continue

        # Lists
        if (_UL_ITEM_RE.match(line) or _OL_ITEM_RE.match(line)) and not para_lines:
            flush_paragraph()
            list_html, idx = _parse_list_block(lines, idx, ref_links)
            out.append(list_html)
            continue

        # Table (check for header + delimiter pattern)
        if not para_lines and idx + 1 < len(lines) and "|" in line:
            next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
            if _TABLE_DELIM_RE.match(next_line):
                flush_paragraph()
                header_line = line
                align_line = next_line
                body_lines_tbl: list[str] = []
                idx += 2
                while idx < len(lines):
                    tl = lines[idx]
                    if "|" in tl and not _BLANK_RE.match(tl):
                        body_lines_tbl.append(tl)
                        idx += 1
                    else:
                        break
                out.append(
                    _render_table(header_line, align_line, body_lines_tbl, ref_links)
                )
                continue

        # Paragraph accumulation
        para_lines.append(line)
        idx += 1

    flush_paragraph()
    return "".join(out)


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
