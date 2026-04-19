#!/usr/bin/env python3
"""Three-way readability benchmark: zerodep vs readability-lxml vs Mozilla JS.

Runs each implementation on Mozilla's test fixtures and prints a comparison
table.  JS timing is measured internally by bench_mozilla.js (no subprocess
overhead in the numbers).

Usage:
    python benchmark_compare.py              # all fixtures
    python benchmark_compare.py 001 bbc-1    # specific fixtures
    python benchmark_compare.py --rounds 20  # more rounds
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import timeit

# ── Setup paths ──────────────────────────────────────────────────────────────

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_TEST_PAGES_DIR = os.path.join(_THIS_DIR, "test-pages")
_BENCH_JS = os.path.join(_THIS_DIR, "bench_mozilla.js")

sys.path.insert(0, _THIS_DIR)


# ── Discover fixtures ────────────────────────────────────────────────────────


def discover_fixtures() -> list[str]:
    """Return sorted list of available fixture names."""
    if not os.path.isdir(_TEST_PAGES_DIR):
        return []
    return sorted(
        d
        for d in os.listdir(_TEST_PAGES_DIR)
        if os.path.isdir(os.path.join(_TEST_PAGES_DIR, d))
        and os.path.isfile(os.path.join(_TEST_PAGES_DIR, d, "source.html"))
    )


def load_source(name: str) -> str:
    """Load source HTML for a fixture."""
    path = os.path.join(_TEST_PAGES_DIR, name, "source.html")
    with open(path, encoding="utf-8") as f:
        return f.read()


# ── Python: zerodep readability ──────────────────────────────────────────────


def bench_zerodep(html: str, rounds: int) -> dict:
    """Benchmark our readability.extract() and return timing dict."""
    from readability import extract

    # Warm-up.
    result = extract(html)

    times = []
    for _ in range(rounds):
        t0 = timeit.default_timer()
        extract(html)
        t1 = timeit.default_timer()
        times.append((t1 - t0) * 1000)  # ms

    return {
        "times_ms": times,
        "min_ms": min(times),
        "mean_ms": sum(times) / len(times),
        "max_ms": max(times),
        "title": result.title,
        "length": result.length,
    }


# ── Python: readability-lxml ────────────────────────────────────────────────


def _load_readability_lxml():
    """Load readability-lxml's Document class, working around name clash."""
    import importlib
    import importlib.metadata

    try:
        importlib.metadata.version("readability-lxml")
    except importlib.metadata.PackageNotFoundError:
        return None

    saved_path = sys.path[:]
    saved_modules = {
        k: sys.modules.pop(k)
        for k in list(sys.modules)
        if k == "readability" or k.startswith("readability.")
    }
    try:
        sys.path = [
            p for p in sys.path if os.path.abspath(p) != os.path.abspath(_THIS_DIR)
        ]
        mod = importlib.import_module("readability")
        return mod.Document
    finally:
        sys.path = saved_path
        for k in list(sys.modules):
            if k == "readability" or k.startswith("readability."):
                del sys.modules[k]
        sys.modules.update(saved_modules)


_RefDocument = _load_readability_lxml()


def bench_readability_lxml(html: str, rounds: int) -> dict | None:
    """Benchmark readability-lxml and return timing dict, or None."""
    if _RefDocument is None:
        return None

    # Warm-up.
    doc = _RefDocument(html)
    summary = doc.summary()

    times = []
    for _ in range(rounds):
        t0 = timeit.default_timer()
        doc = _RefDocument(html)
        doc.summary()
        t1 = timeit.default_timer()
        times.append((t1 - t0) * 1000)

    # Extract title from summary HTML (basic).
    title = doc.short_title() if hasattr(doc, "short_title") else ""
    length = len(summary) if summary else 0

    return {
        "times_ms": times,
        "min_ms": min(times),
        "mean_ms": sum(times) / len(times),
        "max_ms": max(times),
        "title": title,
        "length": length,
    }


# ── JavaScript: Mozilla Readability.js ───────────────────────────────────────


def bench_mozilla_js(fixture_name: str, rounds: int) -> dict | None:
    """Benchmark Mozilla Readability.js via Node.js subprocess.

    Timing is measured internally by bench_mozilla.js — no subprocess
    overhead in the reported numbers.
    """
    if not shutil.which("node"):
        return None
    if not os.path.isfile(_BENCH_JS):
        return None

    source_path = os.path.join(_TEST_PAGES_DIR, fixture_name, "source.html")
    try:
        result = subprocess.run(
            ["node", _BENCH_JS, source_path, str(rounds)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=_THIS_DIR,
        )
        if result.returncode != 0:
            print(f"  [JS error: {result.stderr.strip()[:100]}]", file=sys.stderr)
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


# ── Output formatting ────────────────────────────────────────────────────────

# ANSI colors (disabled if not a terminal).
if sys.stdout.isatty():
    _BOLD = "\033[1m"
    _GREEN = "\033[32m"
    _YELLOW = "\033[33m"
    _CYAN = "\033[36m"
    _RESET = "\033[0m"
    _DIM = "\033[2m"
else:
    _BOLD = _GREEN = _YELLOW = _CYAN = _RESET = _DIM = ""


def _fmt_ms(ms: float) -> str:
    """Format milliseconds with appropriate unit."""
    if ms < 1:
        return f"{ms * 1000:.0f} µs"
    if ms < 1000:
        return f"{ms:.1f} ms"
    return f"{ms / 1000:.2f} s"


def _ratio_str(ms: float, baseline: float) -> str:
    """Format a ratio relative to baseline."""
    if baseline <= 0:
        return ""
    ratio = ms / baseline
    if ratio < 1.05:
        return f"{_GREEN}1.00x{_RESET}"
    return f"{_YELLOW}{ratio:.2f}x{_RESET}"


def print_results(
    fixture_name: str,
    html_size: int,
    zd: dict,
    lxml: dict | None,
    js: dict | None,
) -> None:
    """Print a single fixture's results as a formatted row."""
    baseline = zd["mean_ms"]

    cols = [
        f"  {_BOLD}{fixture_name:<28s}{_RESET}",
        f"{_DIM}{html_size / 1024:>7.1f} KB{_RESET}",
        f"{_CYAN}zerodep{_RESET}  {_fmt_ms(zd['mean_ms']):>10s}"
        f" {_ratio_str(zd['mean_ms'], baseline)}",
    ]

    if lxml is not None:
        cols.append(
            f"{_CYAN}lxml{_RESET}     {_fmt_ms(lxml['mean_ms']):>10s}"
            f" {_ratio_str(lxml['mean_ms'], baseline)}"
        )
    else:
        cols.append(f"{_DIM}lxml     {'n/a':>10s}{_RESET}")

    if js is not None:
        cols.append(
            f"{_CYAN}mozilla{_RESET}  {_fmt_ms(js['mean_ms']):>10s}"
            f" {_ratio_str(js['mean_ms'], baseline)}"
        )
    else:
        cols.append(f"{_DIM}mozilla  {'n/a':>10s}{_RESET}")

    print("  ".join(cols))


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Three-way readability benchmark comparison."
    )
    parser.add_argument(
        "fixtures",
        nargs="*",
        help="Fixture names to benchmark (default: all).",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=10,
        help="Number of timing rounds per fixture (default: 10).",
    )
    args = parser.parse_args()

    all_fixtures = discover_fixtures()
    if not all_fixtures:
        print("No test fixtures found in test-pages/", file=sys.stderr)
        sys.exit(1)

    fixtures = args.fixtures if args.fixtures else all_fixtures
    # Validate fixture names.
    for name in fixtures:
        if name not in all_fixtures:
            print(f"Unknown fixture: {name}", file=sys.stderr)
            print(f"Available: {', '.join(all_fixtures)}", file=sys.stderr)
            sys.exit(1)

    rounds = args.rounds

    # Header.
    print()
    print(f"{_BOLD}Readability Benchmark ({rounds} rounds per fixture){_RESET}")
    has_node = shutil.which("node") is not None
    has_lxml = _RefDocument is not None
    status = []
    status.append(f"zerodep: {_GREEN}yes{_RESET}")
    lxml_status = _GREEN + "yes" + _RESET if has_lxml else _DIM + "no" + _RESET
    status.append(f"readability-lxml: {lxml_status}")
    status.append(
        f"mozilla js: {_GREEN + 'yes' + _RESET if has_node else _DIM + 'no' + _RESET}"
    )
    print(f"  Implementations: {' | '.join(status)}")
    print(f"  {_DIM}Times shown are mean. Ratios relative to zerodep.{_RESET}")
    print()

    # Column headers.
    print(
        f"  {'Fixture':<28s}  {'Size':>9s}  "
        f"{'zerodep':>19s}  {'readability-lxml':>19s}  "
        f"{'mozilla js':>19s}"
    )
    print("  " + "─" * 110)

    for name in fixtures:
        html = load_source(name)
        html_size = len(html.encode("utf-8"))

        # Benchmark all three.
        zd = bench_zerodep(html, rounds)
        lxml = bench_readability_lxml(html, rounds)
        js = bench_mozilla_js(name, rounds)

        print_results(name, html_size, zd, lxml, js)

    print()


if __name__ == "__main__":
    main()
