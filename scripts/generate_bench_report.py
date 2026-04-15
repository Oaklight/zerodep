#!/usr/bin/env python3
"""Generate a benchmark comparison report from pytest-benchmark JSON output.

Reads benchmark-results.json produced by pytest-benchmark and generates a
static HTML page that groups results by module, compares zerodep
implementations against reference libraries, and renders both summary
tables and bar charts (via Chart.js).
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

# Substrings that identify a zerodep (ours) implementation
_ZERODEP_MARKERS = (
    "zerodep",
    "pure_python",
    "_ours",
    "ours_",
)

# Known reference library method fragments → display name
_REF_LIBS: dict[str, str] = {
    "openssl": "OpenSSL",
    "pycryptodome": "PyCryptodome",
    "httpx": "httpx",
    "a2a_protocol": "a2a-protocol",
    "acp_ref": "acp (ref)",
    "pyyaml": "PyYAML",
    "python_frontmatter": "python-frontmatter",
    "xmltodict": "xmltodict",
    "packaging": "packaging",
    "decouple": "python-decouple",
    "structlog": "structlog",
    "qrcode": "qrcode",
    "python_dotenv": "python-dotenv",
    "commentjson": "commentjson",
    "tenacity": "tenacity",
    "beautifulsoup4": "beautifulsoup4",
    "pydantic": "pydantic",
    "httpx_sse": "httpx-sse",
    "mistune": "mistune",
    "unidiff": "unidiff",
    "croniter": "croniter",
    "apscheduler": "APScheduler",
    "schedule": "schedule",
    "rank_bm25": "rank-bm25",
    "cachetools": "cachetools",
    "shelve": "shelve",
    "jsonrpcserver": "jsonrpcserver",
    "google": "google (protobuf)",
}


def _is_zerodep(method: str) -> bool:
    m = method.lower()
    return any(marker in m for marker in _ZERODEP_MARKERS)


def _ref_display_name(method: str) -> str:
    m = method.lower().removeprefix("test_")
    for frag, name in _REF_LIBS.items():
        if frag in m:
            return name
    return method.removeprefix("test_")


def _human_time(seconds: float) -> str:
    if seconds < 1e-6:
        return f"{seconds * 1e9:.1f} ns"
    if seconds < 1e-3:
        return f"{seconds * 1e6:.1f} \u00b5s"
    if seconds < 1:
        return f"{seconds * 1e3:.2f} ms"
    return f"{seconds:.3f} s"


def _human_ops(ops: float) -> str:
    if ops >= 1e6:
        return f"{ops / 1e6:.2f}M"
    if ops >= 1e3:
        return f"{ops / 1e3:.1f}K"
    return f"{ops:.1f}"


# ---------------------------------------------------------------------------
# Data processing
# ---------------------------------------------------------------------------


def _parse_benchmarks(data: dict) -> dict:
    """Return nested structure: module -> operation -> list of entries."""
    modules: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))

    for b in data["benchmarks"]:
        fullname = b.get("fullname", b["name"])
        parts = fullname.split("::")
        file_part = parts[0]  # e.g. aes/test_aes_benchmark.py
        module = file_part.split("/")[0]

        if len(parts) == 3:
            test_class = parts[1]
            test_method = parts[2]
            # For jsonrpc-style: class name IS the operation
            operation = _class_to_operation(test_class)
        elif len(parts) == 2:
            # Function-level tests (no class)
            test_method = parts[1]
            test_class = None
            operation = test_method
        else:
            test_method = b["name"]
            test_class = None
            operation = test_method

        is_zd = _is_zerodep(test_method)

        entry = {
            "method": test_method,
            "is_zerodep": is_zd,
            "label": "zerodep" if is_zd else _ref_display_name(test_method),
            "mean": b["stats"]["mean"],
            "ops": b["stats"]["ops"],
            "stddev": b["stats"].get("stddev", 0),
            "min": b["stats"].get("min", b["stats"]["mean"]),
            "max": b["stats"].get("max", b["stats"]["mean"]),
            "rounds": b["stats"].get("rounds", 0),
        }

        modules[module][operation].append(entry)

    return dict(modules)


def _class_to_operation(cls_name: str) -> str:
    """Convert TestEcbEncryptSmall → ECB Encrypt (Small)."""
    name = cls_name.removeprefix("Test")
    # Insert spaces before capitals
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    # Wrap size suffixes in parens
    spaced = re.sub(r"\s+(Small|Medium|Large|1k)$", r" (\1)", spaced)
    return spaced


# ---------------------------------------------------------------------------
# Pairing: for each operation, pair zerodep with each reference
# ---------------------------------------------------------------------------


def _build_comparisons(modules: dict) -> list[dict]:
    """Build a list of module summaries with paired comparisons."""
    result = []
    for module in sorted(modules):
        operations = modules[module]
        pairs = []
        standalone = []

        for op_name, entries in sorted(operations.items()):
            zd_entries = [e for e in entries if e["is_zerodep"]]
            ref_entries = [e for e in entries if not e["is_zerodep"]]

            if not zd_entries and not ref_entries:
                continue

            if not ref_entries:
                # Standalone zerodep benchmarks (no reference)
                for e in zd_entries:
                    standalone.append(
                        {
                            "operation": op_name,
                            "variant": e["method"].removeprefix("test_"),
                            "mean": e["mean"],
                            "ops": e["ops"],
                        }
                    )
                continue

            if not zd_entries:
                # Reference-only (shouldn't happen often, but handle it)
                for e in ref_entries:
                    standalone.append(
                        {
                            "operation": op_name,
                            "variant": e["label"],
                            "mean": e["mean"],
                            "ops": e["ops"],
                        }
                    )
                continue

            # Pair each zerodep variant with each reference
            for zd in zd_entries:
                for ref in ref_entries:
                    # ratio = zerodep_time / ref_time
                    # < 1 means zerodep is faster
                    ratio = (
                        zd["mean"] / ref["mean"] if ref["mean"] > 0 else float("inf")
                    )
                    zd_variant = zd["method"].removeprefix("test_")
                    pairs.append(
                        {
                            "operation": op_name,
                            "zd_variant": zd_variant,
                            "zd_mean": zd["mean"],
                            "zd_ops": zd["ops"],
                            "ref_label": ref["label"],
                            "ref_mean": ref["mean"],
                            "ref_ops": ref["ops"],
                            "ratio": ratio,
                        }
                    )

        result.append(
            {
                "module": module,
                "pairs": pairs,
                "standalone": standalone,
            }
        )

    return result


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

_CSS = """\
:root {
  --bg: #fff; --fg: #1a1a2e; --card-bg: #f8f9fa; --border: #dee2e6;
  --green: #198754; --red: #dc3545; --yellow: #ffc107; --blue: #0d6efd;
  --accent: #6f42c1;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #1a1a2e; --fg: #e0e0e0; --card-bg: #16213e; --border: #334155;
    --green: #4ade80; --red: #f87171; --yellow: #facc15; --blue: #60a5fa;
    --accent: #a78bfa;
  }
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg); color: var(--fg); line-height: 1.6;
  max-width: 1200px; margin: 0 auto; padding: 2rem 1rem;
}
h1 { font-size: 1.8rem; margin-bottom: .5rem; }
h2 {
  font-size: 1.4rem; margin: 2rem 0 1rem;
  border-bottom: 2px solid var(--accent); padding-bottom: .3rem;
}
h3 { font-size: 1.1rem; margin: 1rem 0 .5rem; color: var(--accent); }
.meta { color: #888; font-size: .9rem; margin-bottom: 2rem; }
.summary-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem; margin-bottom: 2rem;
}
.summary-card {
  background: var(--card-bg); border: 1px solid var(--border);
  border-radius: 8px; padding: 1rem; text-align: center;
}
.summary-card .num { font-size: 2rem; font-weight: bold; }
.summary-card .label { font-size: .85rem; color: #888; }
table {
  width: 100%; border-collapse: collapse; margin-bottom: 1rem;
  font-size: .9rem;
}
th, td { padding: .5rem .75rem; border: 1px solid var(--border); text-align: left; }
th { background: var(--card-bg); font-weight: 600; white-space: nowrap; }
td { white-space: nowrap; }
.ratio-cell { font-weight: bold; }
.faster { color: var(--green); }
.slower { color: var(--red); }
.similar { color: var(--yellow); }
.chart-container {
  background: var(--card-bg); border: 1px solid var(--border);
  border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem;
  max-height: 450px;
}
.module-section { margin-bottom: 3rem; }
.toggle-btn {
  background: var(--card-bg); border: 1px solid var(--border);
  border-radius: 4px; padding: .3rem .8rem; cursor: pointer;
  color: var(--fg); font-size: .85rem; margin-bottom: .5rem;
}
.toggle-btn:hover { border-color: var(--accent); }
.standalone-table { margin-top: 1rem; }
"""

_CHART_COLORS = {
    "zerodep": "rgba(111, 66, 193, 0.8)",  # purple
    "reference": "rgba(13, 110, 253, 0.6)",  # blue
}


def _ratio_class(ratio: float) -> str:
    if ratio <= 0.8:
        return "faster"
    if ratio >= 1.5:
        return "slower"
    return "similar"


def _ratio_text(ratio: float) -> str:
    if ratio < 1:
        return f"{1 / ratio:.1f}x faster"
    if ratio > 1:
        return f"{ratio:.1f}x slower"
    return "equal"


def _generate_html(comparisons: list[dict], meta: dict) -> str:
    # Summary stats
    total_pairs = sum(len(m["pairs"]) for m in comparisons)
    n_modules = len([m for m in comparisons if m["pairs"] or m["standalone"]])

    faster_count = sum(1 for m in comparisons for p in m["pairs"] if p["ratio"] < 0.8)
    similar_count = sum(
        1 for m in comparisons for p in m["pairs"] if 0.8 <= p["ratio"] <= 1.5
    )
    slower_count = sum(1 for m in comparisons for p in m["pairs"] if p["ratio"] > 1.5)

    charts_js = []
    chart_id = 0

    sections = []
    for mod_data in comparisons:
        module = mod_data["module"]
        pairs = mod_data["pairs"]
        standalone = mod_data["standalone"]

        if not pairs and not standalone:
            continue

        s = f'<div class="module-section" id="mod-{module}">\n'
        s += f"<h2>{module}</h2>\n"

        if pairs:
            # --- Comparison table ---
            s += "<table>\n<thead><tr>"
            s += "<th>Operation</th><th>zerodep</th><th>Reference</th>"
            s += "<th>zerodep time</th><th>Ref time</th>"
            s += "<th>zerodep ops/s</th><th>Ref ops/s</th>"
            s += "<th>Ratio</th></tr></thead>\n<tbody>\n"

            for p in pairs:
                rc = _ratio_class(p["ratio"])
                s += "<tr>"
                s += f"<td>{p['operation']}</td>"
                s += f"<td>{p['zd_variant']}</td>"
                s += f"<td>{p['ref_label']}</td>"
                s += f"<td>{_human_time(p['zd_mean'])}</td>"
                s += f"<td>{_human_time(p['ref_mean'])}</td>"
                s += f"<td>{_human_ops(p['zd_ops'])}</td>"
                s += f"<td>{_human_ops(p['ref_ops'])}</td>"
                s += f'<td class="ratio-cell {rc}">{_ratio_text(p["ratio"])}</td>'
                s += "</tr>\n"

            s += "</tbody></table>\n"

            # --- Chart: group by operation, show zerodep vs best-reference ops/s ---
            # Deduplicate operations, pick best reference per operation
            op_best: dict[str, dict] = {}
            for p in pairs:
                op = p["operation"]
                if op not in op_best or p["ref_ops"] > op_best[op]["ref_ops"]:
                    op_best[op] = p

            labels = list(op_best.keys())
            zd_ops = [op_best[op]["zd_ops"] for op in labels]
            ref_ops = [op_best[op]["ref_ops"] for op in labels]
            ref_labels_list = [op_best[op]["ref_label"] for op in labels]

            cid = f"chart_{chart_id}"
            chart_id += 1

            s += f'<div class="chart-container"><canvas id="{cid}"></canvas></div>\n'

            # Log scale for values differing by orders of magnitude
            charts_js.append(
                f"""
new Chart(document.getElementById('{cid}'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(labels)},
    datasets: [
      {{
        label: 'zerodep (ops/s)',
        data: {json.dumps(zd_ops)},
        backgroundColor: '{_CHART_COLORS["zerodep"]}',
        borderRadius: 4,
      }},
      {{
        label: {
                    json.dumps(
                        ref_labels_list[0]
                        if len(set(ref_labels_list)) == 1
                        else "Reference"
                    )
                } + ' (ops/s)',
        data: {json.dumps(ref_ops)},
        backgroundColor: '{_CHART_COLORS["reference"]}',
        borderRadius: 4,
      }}
    ]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ position: 'top' }},
      title: {{ display: true, text: '{module} — ops/s comparison (higher is better)' }}
    }},
    scales: {{
      y: {{
        type: 'logarithmic',
        title: {{ display: true, text: 'ops/s (log scale)' }}
      }}
    }}
  }}
}});"""
            )

        if standalone:
            s += "<h3>Standalone benchmarks</h3>\n"
            s += '<table class="standalone-table">\n<thead><tr>'
            s += "<th>Operation</th><th>Variant</th><th>Mean</th><th>ops/s</th>"
            s += "</tr></thead>\n<tbody>\n"
            for st in standalone:
                s += "<tr>"
                s += f"<td>{st['operation']}</td>"
                s += f"<td>{st['variant']}</td>"
                s += f"<td>{_human_time(st['mean'])}</td>"
                s += f"<td>{_human_ops(st['ops'])}</td>"
                s += "</tr>\n"
            s += "</tbody></table>\n"

        s += "</div>\n"
        sections.append(s)

    # Build nav
    nav_links = []
    for mod_data in comparisons:
        if mod_data["pairs"] or mod_data["standalone"]:
            m = mod_data["module"]
            np = len(mod_data["pairs"])
            link = f'<a href="#mod-{m}" style="margin-right:1rem">'
            nav_links.append(f"{link}{m} ({np})</a>")

    nav_open = '<div style="margin-bottom:1.5rem;font-size:.9rem">'
    nav = nav_open + " ".join(nav_links) + "</div>"

    version = meta.get("version", "unknown")
    commit = meta.get("commit", "")
    timestamp = meta.get("datetime", "")

    commit_short = commit[:8] if commit else "N/A"
    meta_line = (
        f"Version: {version} &nbsp;|&nbsp; "
        f"Commit: {commit_short} &nbsp;|&nbsp; {timestamp}"
    )

    def _card(css: str, val: str | int, label: str) -> str:
        return (
            f'<div class="summary-card">'
            f'<div class="num {css}">{val}</div>'
            f'<div class="label">{label}</div></div>'
        )

    cards = "\n".join(
        [
            _card("", n_modules, "Modules"),
            _card("", total_pairs, "Comparisons"),
            _card("faster", faster_count, "Faster than ref"),
            _card("similar", similar_count, "Similar"),
            _card("slower", slower_count, "Slower than ref"),
        ]
    )

    chartjs = "https://cdn.jsdelivr.net/npm/chart.js@4"

    html = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" '
        'content="width=device-width, initial-scale=1">\n'
        f"<title>zerodep Benchmark — {version}</title>\n"
        f"<style>{_CSS}</style>\n"
        f'<script src="{chartjs}"></script>\n'
        "</head>\n<body>\n"
        "<h1>zerodep Benchmark Report</h1>\n"
        f'<p class="meta">{meta_line}</p>\n'
        f'<div class="summary-grid">\n{cards}\n</div>\n'
        f"{nav}\n"
        f"{''.join(sections)}\n"
        f"<script>\n{''.join(charts_js)}\n</script>\n"
        "</body>\n</html>"
    )
    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: generate_bench_report.py "
            "<benchmark-results.json> [output.html] "
            "[version] [commit]"
        )
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = (
        Path(sys.argv[2]) if len(sys.argv) > 2 else Path("benchmark-report.html")
    )
    version = sys.argv[3] if len(sys.argv) > 3 else "dev"
    commit = sys.argv[4] if len(sys.argv) > 4 else ""

    with open(input_path) as f:
        data = json.load(f)

    meta = {
        "version": version,
        "commit": commit,
        "datetime": data.get("datetime", ""),
    }

    modules = _parse_benchmarks(data)
    comparisons = _build_comparisons(modules)
    html = _generate_html(comparisons, meta)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)
    print(f"Report written to {output_path} ({len(html)} bytes)")

    # Print summary
    total_pairs = sum(len(m["pairs"]) for m in comparisons)
    faster = sum(1 for m in comparisons for p in m["pairs"] if p["ratio"] < 0.8)
    slower = sum(1 for m in comparisons for p in m["pairs"] if p["ratio"] > 1.5)
    print(f"  {total_pairs} comparisons: {faster} faster, {slower} slower")


if __name__ == "__main__":
    main()
