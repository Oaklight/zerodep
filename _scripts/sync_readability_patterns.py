#!/usr/bin/env python3
"""Sync upstream trafilatura XPath keyword patterns with local readability.py.

Fetches trafilatura's ``xpaths.py`` from GitHub, extracts all class/id keyword
patterns from the XPath expressions, then compares them against the regex-based
patterns already present in ``readability/readability.py``.

Modes:

  **Report** (default): produces a diff showing covered, new, and local-only
  keywords.  Use ``--json`` for machine-readable output.

  **Apply** (``--apply``): patches ``readability.py`` to add new upstream
  keywords to ``NEGATIVE_RE`` (discard) and ``POSITIVE_RE`` (positive).
  Combine with ``--dry-run`` to preview changes without writing.

Exit codes:
  0 — no new patterns found, or ``--apply`` succeeded
  1 — error (fetch failure, parse error, regex compilation failure)
  2 — new patterns detected (report mode only; useful for CI gating)

Usage::

    python _scripts/sync_readability_patterns.py            # report
    python _scripts/sync_readability_patterns.py --json      # CI report
    python _scripts/sync_readability_patterns.py --apply     # auto-patch
    python _scripts/sync_readability_patterns.py --apply --dry-run  # preview

Requires only the Python standard library (urllib, re, pathlib, subprocess).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import NamedTuple
from urllib.error import URLError
from urllib.request import urlopen

# ── Constants ────────────────────────────────────────────────────────────────

UPSTREAM_URL = (
    "https://raw.githubusercontent.com/adbar/trafilatura/master/trafilatura/xpaths.py"
)
LOCAL_READABILITY = (
    Path(__file__).resolve().parent.parent / "readability" / "readability.py"
)

# Regex names in readability.py and what role they play
LOCAL_REGEX_DEFS = {
    "UNLIKELY_CANDIDATES_RE": "discard",
    "OK_MAYBE_CANDIDATE_RE": "positive",
    "POSITIVE_RE": "positive",
    "NEGATIVE_RE": "discard",
}

# Which local regexes to modify with --apply (conservative)
APPLY_TARGETS = {
    "discard": "NEGATIVE_RE",
    "positive": "POSITIVE_RE",
}

# Upstream XPath variable names and their semantic role
UPSTREAM_XPATH_ROLES = {
    "BODY_XPATH": "positive",
    "OVERALL_DISCARD_XPATH": "discard",
    "COMMENTS_XPATH": "discard",
    "REMOVE_COMMENTS_XPATH": "discard",
    "TEASER_DISCARD_XPATH": "discard",
    "PRECISION_DISCARD_XPATH": "discard",
    "COMMENTS_DISCARD_XPATH": "discard",
    "DISCARD_IMAGE_ELEMENTS": "discard",
}

# Keywords shorter than this are too generic (e.g. "ad")
MIN_KEYWORD_LENGTH = 3

# Regex metacharacters that indicate a keyword is not a plain string
_REGEX_META_RE = re.compile(r"[\[\]()+*?{}\\^$]")

# Generic keywords that would cause excessive false positives
_GENERIC_BLOCKLIST = frozenset(
    {
        "bar",  # matches sidebar, navbar, etc.
        "hide",  # too broad; -hide- and hide- are more targeted
        "link",  # matches any link-related class
    }
)

# Max keywords per r"..." line when rebuilding a regex block
KEYWORDS_PER_LINE = 12


class UpstreamKeyword(NamedTuple):
    """A keyword extracted from an upstream XPath expression."""

    keyword: str
    match_type: str  # "contains", "starts-with", "exact"
    attribute: str  # "class", "id", "class|id", "role", etc.
    source_var: str  # e.g. "OVERALL_DISCARD_XPATH"
    role: str  # "positive" or "discard"


class LocalPattern(NamedTuple):
    """A keyword extracted from a local regex pattern."""

    keyword: str
    source_var: str  # e.g. "NEGATIVE_RE"
    role: str  # "positive" or "discard"


# ── Upstream parsing ─────────────────────────────────────────────────────────


def fetch_upstream(url: str | None = None, local_path: str | None = None) -> str:
    """Fetch the upstream xpaths.py content."""
    if local_path:
        return Path(local_path).read_text(encoding="utf-8")
    target = url or UPSTREAM_URL
    try:
        with urlopen(target, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except URLError as exc:
        print(
            f"[ERROR] Failed to fetch {target}: {exc}",
            file=sys.stderr,
        )
        print(
            "[HINT] Try: python _scripts/sync_readability_patterns.py"
            " --local /path/to/xpaths.py",
            file=sys.stderr,
        )
        sys.exit(1)


def _split_xpath_blocks(source: str) -> dict[str, str]:
    """Split xpaths.py source into variable-name to raw-string blocks.

    Each block spans from the variable assignment to the next block.
    """
    block_re = re.compile(
        r"^(\w+_XPATH(?:S)?)\s*=\s*\[XPath",
        re.MULTILINE,
    )
    blocks: dict[str, str] = {}
    matches = list(block_re.finditer(source))
    for i, m in enumerate(matches):
        var_name = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(source)
        blocks[var_name] = source[start:end]
    return blocks


def parse_upstream_keywords(
    source: str,
) -> list[UpstreamKeyword]:
    """Extract all class/id keyword patterns from upstream XPaths."""
    blocks = _split_xpath_blocks(source)
    keywords: list[UpstreamKeyword] = []

    # contains(@class, "xxx") / contains(@id|@class, "xxx")
    contains_re = re.compile(
        r"contains\s*\(\s*"
        r"(?:translate\s*\([^)]+\)\s*"
        r"|@([\w|@]+))\s*,\s*"
        r'["\']([^"\']+)["\']\s*\)',
    )
    starts_re = re.compile(
        r"starts-with\s*\(\s*@([\w|@]+)\s*,\s*"
        r'["\']([^"\']+)["\']\s*\)',
    )
    exact_re = re.compile(
        r'@(class|id|role)\s*=\s*["\']([^"\']+)["\']',
    )
    translate_re = re.compile(
        r"contains\s*\(\s*translate\s*\(\s*@([\w|@]+)\s*,"
        r'\s*"[^"]*"\s*,\s*"[^"]*"\s*\)\s*,\s*'
        r'["\']([^"\']+)["\']\s*\)',
    )

    for var_name, block in blocks.items():
        role = UPSTREAM_XPATH_ROLES.get(var_name, "unknown")
        if role == "unknown":
            continue

        seen: set[tuple[str, str, str]] = set()

        for m in translate_re.finditer(block):
            attr = _normalize_attr(m.group(1))
            kw = m.group(2).strip()
            key = (kw, "contains", attr)
            if key not in seen:
                seen.add(key)
                keywords.append(UpstreamKeyword(kw, "contains", attr, var_name, role))

        for m in contains_re.finditer(block):
            attr_raw = m.group(1)
            kw = m.group(2).strip()
            if not attr_raw:
                continue
            attr = _normalize_attr(attr_raw)
            key = (kw, "contains", attr)
            if key not in seen:
                seen.add(key)
                keywords.append(UpstreamKeyword(kw, "contains", attr, var_name, role))

        for m in starts_re.finditer(block):
            attr = _normalize_attr(m.group(1))
            kw = m.group(2).strip()
            key = (kw, "starts-with", attr)
            if key not in seen:
                seen.add(key)
                keywords.append(
                    UpstreamKeyword(kw, "starts-with", attr, var_name, role)
                )

        for m in exact_re.finditer(block):
            attr = m.group(1)
            kw = m.group(2).strip()
            key = (kw, "exact", attr)
            if key not in seen:
                seen.add(key)
                keywords.append(UpstreamKeyword(kw, "exact", attr, var_name, role))

    return keywords


def _normalize_attr(attr: str) -> str:
    """Normalize attribute references like '@id|@class' to 'class|id'."""
    attr = attr.replace("@", "")
    parts = sorted(attr.split("|"))
    return "|".join(parts)


# ── Local parsing ────────────────────────────────────────────────────────────

_REGEX_BLOCK_RE_TEMPLATE = r"^{var}\s*=\s*re\.compile\(\s*\n(.*?)\n\s*re\.I"


def _find_regex_block(src: str, var_name: str) -> re.Match | None:
    """Find a named regex definition block in readability.py source."""
    pat = re.compile(
        _REGEX_BLOCK_RE_TEMPLATE.format(var=re.escape(var_name)),
        re.MULTILINE | re.DOTALL,
    )
    return pat.search(src)


def _extract_keywords_from_block(
    raw_block: str, *, preserve_whitespace: bool = False
) -> list[str]:
    """Extract individual keywords from a regex block's r'...' segments.

    Args:
        raw_block: Raw content inside re.compile().
        preserve_whitespace: If True, keep leading/trailing spaces in
            keywords (important for patterns like " hid ").
    """
    segments = re.findall(r'r"([^"]*)"', raw_block)
    full_pattern = "".join(segments)
    keywords: list[str] = []
    for kw in full_pattern.split("|"):
        if not preserve_whitespace:
            kw = kw.strip()
        if kw:
            keywords.append(kw)
    return keywords


def _clean_keyword_for_comparison(kw: str) -> str:
    """Strip regex anchors for comparison purposes."""
    clean = re.sub(r"[\^\$]", "", kw)
    clean = clean.replace(r"\b", "").strip()
    return clean


def parse_local_patterns(
    path: Path | None = None,
) -> list[LocalPattern]:
    """Extract keywords from local readability.py regex patterns."""
    src = (path or LOCAL_READABILITY).read_text(encoding="utf-8")
    patterns: list[LocalPattern] = []

    for var_name, role in LOCAL_REGEX_DEFS.items():
        m = _find_regex_block(src, var_name)
        if not m:
            print(
                f"[WARN] Could not find {var_name} in {path or LOCAL_READABILITY}",
                file=sys.stderr,
            )
            continue

        for kw in _extract_keywords_from_block(m.group(1)):
            clean = _clean_keyword_for_comparison(kw)
            if clean:
                patterns.append(LocalPattern(clean, var_name, role))

    return patterns


# ── Comparison ───────────────────────────────────────────────────────────────


def _build_local_compiled_regexes(
    local_patterns: list[LocalPattern],
) -> dict[str, re.Pattern]:
    """Rebuild compiled regexes from the local patterns for testing."""
    result: dict[str, re.Pattern] = {}
    src = LOCAL_READABILITY.read_text(encoding="utf-8")
    for var_name in LOCAL_REGEX_DEFS:
        m = _find_regex_block(src, var_name)
        if not m:
            continue
        segments = re.findall(r'r"([^"]*)"', m.group(1))
        full_pattern = "".join(segments)
        try:
            result[var_name] = re.compile(full_pattern, re.I)
        except re.error:
            pass
    return result


def compare_patterns(
    upstream: list[UpstreamKeyword],
    local: list[LocalPattern],
) -> tuple[
    list[UpstreamKeyword],
    list[UpstreamKeyword],
    list[LocalPattern],
]:
    """Compare upstream keywords against local patterns.

    Returns:
        (covered, new_upstream, local_only):
        - covered: upstream keywords matched by a local regex
        - new_upstream: upstream keywords NOT matched locally
        - local_only: local keywords absent from upstream
    """
    compiled = _build_local_compiled_regexes(local)

    discard_regexes = [
        compiled[v]
        for v, role in LOCAL_REGEX_DEFS.items()
        if role == "discard" and v in compiled
    ]
    positive_regexes = [
        compiled[v]
        for v, role in LOCAL_REGEX_DEFS.items()
        if role == "positive" and v in compiled
    ]

    covered: list[UpstreamKeyword] = []
    new_upstream: list[UpstreamKeyword] = []

    for uk in upstream:
        test_string = uk.keyword
        if uk.role == "discard":
            matched = any(rx.search(test_string) for rx in discard_regexes)
        elif uk.role == "positive":
            matched = any(rx.search(test_string) for rx in positive_regexes)
        else:
            all_rx = discard_regexes + positive_regexes
            matched = any(rx.search(test_string) for rx in all_rx)

        if matched:
            covered.append(uk)
        else:
            new_upstream.append(uk)

    # Find local-only keywords
    upstream_kw_set = {uk.keyword.lower() for uk in upstream}
    local_only: list[LocalPattern] = []
    for lp in local:
        kw_lower = lp.keyword.lower().strip()
        if not any(kw_lower in uk_kw for uk_kw in upstream_kw_set):
            local_only.append(lp)

    return covered, new_upstream, local_only


# ── Safety filter ────────────────────────────────────────────────────────────


def filter_keywords_for_apply(
    new_upstream: list[UpstreamKeyword],
) -> tuple[list[UpstreamKeyword], list[dict]]:
    """Filter new upstream keywords for safe automatic application.

    Returns:
        (safe, skipped): safe keywords to apply, and skipped with reasons.
    """
    safe: list[UpstreamKeyword] = []
    skipped: list[dict] = []

    for uk in new_upstream:
        kw = uk.keyword

        # Skip style-based patterns (not suitable for class/id regex)
        if uk.attribute == "style":
            skipped.append({"keyword": kw, "reason": "style attribute pattern"})
            continue

        # Skip too-short keywords
        if len(kw) < MIN_KEYWORD_LENGTH:
            skipped.append(
                {"keyword": kw, "reason": f"too short (<{MIN_KEYWORD_LENGTH} chars)"}
            )
            continue

        # Skip keywords with regex metacharacters
        if _REGEX_META_RE.search(kw):
            skipped.append({"keyword": kw, "reason": "contains regex metacharacters"})
            continue

        # Skip pure digits
        if kw.isdigit():
            skipped.append({"keyword": kw, "reason": "pure digits"})
            continue

        # Skip overly generic keywords
        if kw.lower() in _GENERIC_BLOCKLIST:
            skipped.append({"keyword": kw, "reason": "too generic"})
            continue

        safe.append(uk)

    return safe, skipped


# ── Apply mode ───────────────────────────────────────────────────────────────


def _rebuild_regex_block(keywords: list[str], indent: str = "    ") -> str:
    """Rebuild a multi-line regex block from a list of keywords.

    Produces lines like:
        r"alpha|beta|gamma|delta|"
        r"epsilon|zeta|eta",
    """
    lines: list[str] = []
    for i in range(0, len(keywords), KEYWORDS_PER_LINE):
        chunk = keywords[i : i + KEYWORDS_PER_LINE]
        joined = "|".join(chunk)
        is_last = i + KEYWORDS_PER_LINE >= len(keywords)
        if is_last:
            lines.append(f'{indent}r"{joined}",')
        else:
            lines.append(f'{indent}r"{joined}|"')
    return "\n".join(lines)


def apply_keywords(
    readability_path: Path,
    new_upstream: list[UpstreamKeyword],
    dry_run: bool = False,
) -> dict:
    """Patch readability.py to add new upstream keywords.

    Args:
        readability_path: Path to readability.py.
        new_upstream: New upstream keywords to add.
        dry_run: If True, report changes without writing.

    Returns:
        Dict with apply results (added, skipped, errors).
    """
    safe, skipped = filter_keywords_for_apply(new_upstream)

    # Group safe keywords by target regex (deduplicate)
    by_target: dict[str, list[str]] = {}
    seen_per_target: dict[str, set[str]] = {}
    for uk in safe:
        target = APPLY_TARGETS.get(uk.role)
        if target:
            lower = uk.keyword.lower()
            if lower not in seen_per_target.setdefault(target, set()):
                seen_per_target[target].add(lower)
                by_target.setdefault(target, []).append(uk.keyword)

    if not by_target:
        return {
            "applied": False,
            "added": {},
            "skipped": skipped,
            "errors": [],
        }

    src = readability_path.read_text(encoding="utf-8")
    modified_src = src
    added: dict[str, list[str]] = {}
    errors: list[str] = []

    for var_name, new_kws in by_target.items():
        m = _find_regex_block(modified_src, var_name)
        if not m:
            errors.append(f"Could not find {var_name} in source")
            continue

        # Extract existing keywords (raw, preserving spaces and anchors)
        existing = _extract_keywords_from_block(m.group(1), preserve_whitespace=True)
        existing_clean = {_clean_keyword_for_comparison(k).lower() for k in existing}

        # Deduplicate new keywords against existing
        truly_new = [kw for kw in new_kws if kw.lower() not in existing_clean]

        if not truly_new:
            continue

        # Merge: keep existing order, append new sorted
        merged = existing + sorted(truly_new, key=str.lower)

        # Validate the merged regex compiles
        test_pattern = "|".join(merged)
        try:
            re.compile(test_pattern, re.I)
        except re.error as exc:
            errors.append(f"{var_name}: merged regex fails to compile: {exc}")
            continue

        # Rebuild the regex block
        new_block = _rebuild_regex_block(merged)

        # Replace in source: find the full re.compile(...) statement
        full_re = re.compile(
            rf"^({re.escape(var_name)}\s*=\s*re\.compile\(\s*\n)"
            r"(.*?)"
            r"(\n\s*re\.I,?\s*\n\s*\))",
            re.MULTILINE | re.DOTALL,
        )
        full_m = full_re.search(modified_src)
        if not full_m:
            errors.append(f"Could not find full re.compile block for {var_name}")
            continue

        replacement = full_m.group(1) + new_block + full_m.group(3)
        modified_src = (
            modified_src[: full_m.start()] + replacement + modified_src[full_m.end() :]
        )
        added[var_name] = truly_new

    result = {
        "applied": bool(added) and not dry_run,
        "dry_run": dry_run,
        "added": added,
        "skipped": skipped,
        "errors": errors,
    }

    if added and not dry_run:
        readability_path.write_text(modified_src, encoding="utf-8")
        # Try ruff format (non-fatal)
        _try_ruff_format(readability_path)

    return result


def _try_ruff_format(path: Path) -> None:
    """Attempt to run ruff format on the file (best-effort)."""
    for ruff in ("/usr/bin/ruff", "ruff"):
        try:
            subprocess.run(
                [ruff, "format", str(path)],
                capture_output=True,
                timeout=30,
            )
            return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    print(
        "[WARN] ruff not found; skipping format",
        file=sys.stderr,
    )


# ── Reporting ────────────────────────────────────────────────────────────────


def _format_keyword_table(items: list, header: str) -> str:
    """Format a list of keywords into a readable table."""
    if not items:
        return f"\n{header}\n{'─' * len(header)}\n  (none)\n"

    lines = [f"\n{header}", "─" * len(header)]
    if isinstance(items[0], UpstreamKeyword):
        by_source: dict[str, list[UpstreamKeyword]] = {}
        for item in items:
            by_source.setdefault(item.source_var, []).append(item)
        for src, kws in sorted(by_source.items()):
            lines.append(f"  [{src}] ({kws[0].role})")
            for kw in sorted(kws, key=lambda x: x.keyword):
                lines.append(
                    f'    {kw.match_type:12s} {kw.attribute:10s} "{kw.keyword}"'
                )
    elif isinstance(items[0], LocalPattern):
        by_source: dict[str, list[LocalPattern]] = {}
        for item in items:
            by_source.setdefault(item.source_var, []).append(item)
        for src, kws in sorted(by_source.items()):
            lines.append(f"  [{src}] ({kws[0].role})")
            for kw in sorted(kws, key=lambda x: x.keyword):
                lines.append(f'    "{kw.keyword}"')
    return "\n".join(lines) + "\n"


def print_report(
    upstream: list[UpstreamKeyword],
    local: list[LocalPattern],
    covered: list[UpstreamKeyword],
    new_upstream: list[UpstreamKeyword],
    local_only: list[LocalPattern],
) -> None:
    """Print a formatted comparison report."""
    width = 72
    print("=" * width)
    print("  Readability Pattern Sync Report")
    print("  trafilatura/xpaths.py ↔ readability/readability.py")
    print("=" * width)

    print(f"\n  Upstream keywords extracted:  {len(upstream)}")
    print(f"  Local regex keywords:         {len(local)}")
    print("  ──────────────────────────────────────")
    print(f"  Already covered:              {len(covered)}")
    print(f"  New from upstream:            {len(new_upstream)}")
    print(f"  Local-only:                   {len(local_only)}")

    print(
        _format_keyword_table(covered, "✓ Already Covered (upstream → local regexes)")
    )
    print(_format_keyword_table(new_upstream, "★ New From Upstream (not yet in local)"))
    print(_format_keyword_table(local_only, "◆ Local-Only (not in upstream XPaths)"))

    print("=" * width)
    if new_upstream:
        print(
            textwrap.dedent("""\
            Suggested actions:
              1. Review new upstream keywords for relevance
              2. Add via: --apply (or --apply --dry-run to preview)
              3. Run readability tests to verify no regressions
        """)
        )
    else:
        print("  All upstream patterns are covered. No action needed.\n")


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync trafilatura XPath patterns with local readability.py",
    )
    parser.add_argument(
        "--local",
        metavar="PATH",
        help="Use a local copy of trafilatura/xpaths.py"
        " instead of fetching from GitHub",
    )
    parser.add_argument(
        "--readability",
        metavar="PATH",
        help=f"Path to readability.py (default: {LOCAL_READABILITY})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Patch readability.py with new upstream keywords",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --apply, preview changes without writing",
    )
    args = parser.parse_args()

    log_out = sys.stderr if args.json else sys.stdout

    # ── Fetch and parse ──────────────────────────────────────────────
    print(
        "Fetching upstream patterns from: ",
        end="",
        flush=True,
        file=log_out,
    )
    if args.local:
        print(args.local, file=log_out)
    else:
        print(UPSTREAM_URL, file=log_out)
    upstream_src = fetch_upstream(local_path=args.local)
    upstream = parse_upstream_keywords(upstream_src)
    print(
        f"  → extracted {len(upstream)} keywords from upstream\n",
        file=log_out,
    )

    readability_path = Path(args.readability) if args.readability else LOCAL_READABILITY
    if not readability_path.exists():
        print(
            f"[ERROR] readability.py not found at {readability_path}",
            file=sys.stderr,
        )
        sys.exit(1)
    local = parse_local_patterns(readability_path)
    print(
        f"  → extracted {len(local)} keywords from local\n",
        file=log_out,
    )

    # ── Compare ──────────────────────────────────────────────────────
    covered, new_upstream, local_only = compare_patterns(upstream, local)

    # ── Apply mode ───────────────────────────────────────────────────
    if args.apply:
        apply_result = apply_keywords(
            readability_path, new_upstream, dry_run=args.dry_run
        )

        if args.json:
            import json

            output = {
                "mode": "apply",
                "summary": {
                    "upstream_total": len(upstream),
                    "local_total": len(local),
                    "new_upstream": len(new_upstream),
                },
                "apply": apply_result,
            }
            print(json.dumps(output, indent=2))
        else:
            _print_apply_report(apply_result)

        if apply_result.get("errors"):
            sys.exit(1)
        sys.exit(0)

    # ── Report mode ──────────────────────────────────────────────────
    if args.json:
        import json

        result = {
            "mode": "report",
            "summary": {
                "upstream_total": len(upstream),
                "local_total": len(local),
                "covered": len(covered),
                "new_upstream": len(new_upstream),
                "local_only": len(local_only),
            },
            "covered": [
                {
                    "keyword": k.keyword,
                    "source": k.source_var,
                    "role": k.role,
                }
                for k in covered
            ],
            "new_upstream": [
                {
                    "keyword": k.keyword,
                    "match_type": k.match_type,
                    "attribute": k.attribute,
                    "source": k.source_var,
                    "role": k.role,
                }
                for k in new_upstream
            ],
            "local_only": [
                {
                    "keyword": k.keyword,
                    "source": k.source_var,
                    "role": k.role,
                }
                for k in local_only
            ],
        }
        print(json.dumps(result, indent=2))
    else:
        print_report(upstream, local, covered, new_upstream, local_only)

    # Exit 2 if new patterns found (CI gating signal)
    if new_upstream:
        sys.exit(2)


def _print_apply_report(result: dict) -> None:
    """Print human-readable apply results."""
    width = 72
    print("=" * width)
    print("  Readability Pattern Apply Report")
    print("=" * width)

    if result.get("dry_run"):
        print("\n  ⚠ DRY RUN — no files modified\n")

    added = result.get("added", {})
    if added:
        for var_name, kws in added.items():
            print(f"\n  [{var_name}] +{len(kws)} keywords:")
            for kw in sorted(kws):
                print(f'    + "{kw}"')
    else:
        print("\n  No keywords to add.")

    skipped = result.get("skipped", [])
    if skipped:
        print(f"\n  Skipped ({len(skipped)}):")
        for s in skipped:
            print(f'    ✗ "{s["keyword"]}" — {s["reason"]}')

    errors = result.get("errors", [])
    if errors:
        print("\n  Errors:")
        for e in errors:
            print(f"    ✗ {e}")

    print("\n" + "=" * width)


if __name__ == "__main__":
    main()
