# /// zerodep
# version = "0.1.0"
# deps = []
# tier = "simple"
# category = "protocol"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///

"""llms.txt parser — zero dependencies, stdlib only, Python 3.10+.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Parse llms.txt files per the llmstxt.org specification into structured data,
and generate candidate per-page markdown URLs for content discovery.

Example::

    from llmstxt import parse, find_candidates

    doc = parse(\"\"\"# My Project
    > A cool project

    Some details here.

    ## Docs
    - [Guide](https://example.com/guide.md): The main guide
    \"\"\")
    print(doc.title)       # 'My Project'
    print(doc.sections)    # {'Docs': [FileEntry(name='Guide', ...)]}

    # With a parsed llms.txt — looks up matching entries, falls back to heuristic
    matches = find_candidates("https://example.com/guide", doc=doc)
    # [FileEntry(name='Guide', url='https://example.com/guide.md', ...)]

    # Without llms.txt — pure heuristic URL generation
    matches = find_candidates("https://example.com/docs")
    # [FileEntry(name='', url='https://example.com/docs.md', ...)]
"""

from __future__ import annotations

import dataclasses
import re
import urllib.error
import urllib.parse
import urllib.request

__all__ = [
    "LlmsTxtError",
    "FileEntry",
    "LlmsTxt",
    "DiscoveryResult",
    "parse",
    "find_candidates",
    "discover",
]

# ── Exceptions ───────────────────────────────────────────────────────────────


class LlmsTxtError(Exception):
    """Raised when llms.txt parsing fails due to structural issues."""


# ── Data Classes ─────────────────────────────────────────────────────────────


@dataclasses.dataclass(frozen=True, slots=True)
class FileEntry:
    """A linked resource entry from an llms.txt file list.

    Attributes:
        name: Display name of the link.
        url: URL of the linked resource.
        notes: Descriptive text after the ``: `` separator, or empty string.
    """

    name: str
    url: str
    notes: str = ""


@dataclasses.dataclass(frozen=True, slots=True)
class LlmsTxt:
    """Parsed representation of an llms.txt file.

    Attributes:
        title: The H1 heading (project/site name).
        description: The blockquote summary, or empty string if absent.
        details: Text paragraphs between blockquote and first H2, or empty
            string.
        sections: Mapping of H2 section name to list of file entries.
            The special ``"Optional"`` section is excluded from this dict.
        optional: Entries from the ``## Optional`` section, or empty list.
    """

    title: str
    description: str = ""
    details: str = ""
    sections: dict[str, list[FileEntry]] = dataclasses.field(default_factory=dict)
    optional: list[FileEntry] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True, slots=True)
class DiscoveryResult:
    """Result of probing a site for llms.txt and llms-full.txt.

    Attributes:
        llms_txt: Raw content of ``/llms.txt``, or ``None`` if not found.
        llms_full_txt: Raw content of ``/llms-full.txt``, or ``None`` if not
            found.
        source_url: The root URL (``{scheme}://{netloc}``) that was probed.
    """

    llms_txt: str | None = None
    llms_full_txt: str | None = None
    source_url: str = ""


# ── Regex Patterns ───────────────────────────────────────────────────────────

_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_H2_SPLIT_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
_BLOCKQUOTE_RE = re.compile(r"^>\s?(.*)$", re.MULTILINE)
_LINK_RE = re.compile(r"^-\s*\[([^\]]+)\]\(([^)]+)\)(?:\s*:\s*(.*))?$", re.MULTILINE)

# ── Internal Helpers ─────────────────────────────────────────────────────────


def _parse_links(text: str) -> list[FileEntry]:
    """Extract link entries from a section body."""
    return [
        FileEntry(
            name=m.group(1).strip(),
            url=m.group(2).strip(),
            notes=(m.group(3) or "").strip(),
        )
        for m in _LINK_RE.finditer(text)
    ]


def _parse_preamble(text: str) -> tuple[str, str]:
    """Extract description (blockquote) and details from preamble text.

    Returns:
        A (description, details) tuple.
    """
    lines = text.split("\n")

    # Skip leading blank lines
    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1

    # Collect consecutive blockquote lines
    bq_lines: list[str] = []
    pos = start
    while pos < len(lines):
        m = _BLOCKQUOTE_RE.match(lines[pos])
        if m:
            bq_lines.append(m.group(1))
            pos += 1
        else:
            break

    description = "\n".join(bq_lines).strip()

    # Everything after blockquote block is details
    details = "\n".join(lines[pos:]).strip()

    return description, details


def _strip_url(url: str) -> str:
    """Remove query string and fragment from a URL, return base."""
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, "", "", "")
    )


def _url_path(url: str) -> str:
    """Extract the path component from a URL."""
    return urllib.parse.urlparse(url).path


# ── Public API ───────────────────────────────────────────────────────────────


def parse(text: str) -> LlmsTxt:
    """Parse llms.txt content into structured data.

    Args:
        text: Raw text content of an llms.txt file.

    Returns:
        Parsed ``LlmsTxt`` object.

    Raises:
        LlmsTxtError: If the required H1 title is missing.
    """
    text = text.replace("\r\n", "\n").strip()
    if not text:
        raise LlmsTxtError("empty input")

    # Extract H1 title
    h1_match = _H1_RE.search(text)
    if not h1_match:
        raise LlmsTxtError("missing required H1 title")
    title = h1_match.group(1).strip()

    # Split on H2 headers: [preamble, name1, body1, name2, body2, ...]
    parts = _H2_SPLIT_RE.split(text)
    preamble = parts[0]

    # Remove the H1 line from preamble before parsing description/details
    preamble = preamble[h1_match.end() :]

    description, details = _parse_preamble(preamble)

    # Parse sections
    sections: dict[str, list[FileEntry]] = {}
    for i in range(1, len(parts), 2):
        section_name = parts[i].strip()
        section_body = parts[i + 1] if i + 1 < len(parts) else ""
        sections[section_name] = _parse_links(section_body)

    # Separate "Optional" section
    optional = sections.pop("Optional", [])

    return LlmsTxt(
        title=title,
        description=description,
        details=details,
        sections=sections,
        optional=optional,
    )


def _candidate_md_urls(page_url: str) -> list[str]:
    """Generate candidate per-page markdown URLs for a given page URL."""
    base = _strip_url(page_url)
    path = _url_path(page_url)

    if path.endswith(".md"):
        return [base]

    if path.endswith("/") or path in ("", "/"):
        stripped = base.rstrip("/")
        return [
            stripped + "/index.md",
            stripped + "/index.html.md",
        ]

    return [
        base + ".md",
        base + "/index.md",
        base + "/index.html.md",
    ]


def find_candidates(url: str, doc: LlmsTxt | None = None) -> list[FileEntry]:
    """Find candidate markdown resources for a given URL.

    When *doc* is provided, searches all sections and optional entries for
    URLs that relate to *url* (exact match > extension variation > path
    prefix).  If no match is found (or *doc* is ``None``), falls back to
    heuristic URL generation based on common per-page ``.md`` conventions.

    Args:
        url: The page URL to look up.
        doc: An optional parsed ``LlmsTxt`` object to search in.

    Returns:
        List of ``FileEntry`` candidates, ordered by match quality.
    """
    base = _strip_url(url)
    base_path = _url_path(url).rstrip("/")

    # ── Search llms.txt entries ──
    if doc is not None:
        all_entries: list[FileEntry] = []
        for entries in doc.sections.values():
            all_entries.extend(entries)
        all_entries.extend(doc.optional)

        exact: list[FileEntry] = []
        extension: list[FileEntry] = []
        prefix: list[FileEntry] = []

        for entry in all_entries:
            entry_base = _strip_url(entry.url)
            entry_path = _url_path(entry.url).rstrip("/")

            if entry_base == base:
                exact.append(entry)
                continue

            if entry_path == base_path + ".md" or entry_path == base_path + ".html.md":
                extension.append(entry)
                continue
            if base_path == entry_path + ".md" or base_path == entry_path + ".html.md":
                extension.append(entry)
                continue

            if entry_path.startswith(base_path + "/") or base_path.startswith(
                entry_path + "/"
            ):
                prefix.append(entry)

        results = exact + extension + prefix
        if results:
            return results

    # ── Fallback: heuristic URL candidates ──
    return [FileEntry(name="", url=u) for u in _candidate_md_urls(url)]


# ── Discovery ──────────────────────────────────────────────────────────────

_USER_AGENT = "zerodep-llmstxt/0.1 (https://github.com/Oaklight/zerodep)"


def _fetch_text(url: str, timeout: int) -> str | None:
    """Fetch a URL and return decoded text, or ``None`` on any failure."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def discover(url: str, *, timeout: int = 10) -> DiscoveryResult:
    """Probe a site for ``/llms.txt`` and ``/llms-full.txt``.

    Given any URL, extracts the root (``{scheme}://{netloc}``) and attempts to
    fetch both ``/llms.txt`` and ``/llms-full.txt``.  If the input URL already
    points to one of these files, it is still fetched (along with its sibling).

    Args:
        url: Any URL belonging to the target site.
        timeout: HTTP request timeout in seconds (per request).

    Returns:
        A ``DiscoveryResult`` with the raw content of whichever files were
        found (fields are ``None`` when the file does not exist or could not
        be fetched).

    Example::

        result = discover("https://example.com/docs/guide")
        content = result.llms_full_txt or result.llms_txt
        if content:
            doc = parse(content)
    """
    parsed = urllib.parse.urlparse(url)
    root = f"{parsed.scheme}://{parsed.netloc}"

    llms_txt = _fetch_text(f"{root}/llms.txt", timeout)
    llms_full_txt = _fetch_text(f"{root}/llms-full.txt", timeout)

    return DiscoveryResult(
        llms_txt=llms_txt,
        llms_full_txt=llms_full_txt,
        source_url=root,
    )
