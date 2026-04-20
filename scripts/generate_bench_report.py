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
    "openssl",
    "_ours",
    "ours_",
)

# Known reference library method fragments → display name
_REF_LIBS: dict[str, str] = {
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
    "readability_lxml": "readability-lxml",
    "mozilla_js": "Mozilla Readability.js",
    "reference": "reference",
    "sqlitedict": "sqlitedict",
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


def _pairing_key(method: str) -> str:
    """Derive a canonical key by stripping zerodep/reference markers.

    For example ``test_encode_small_ours`` and ``test_encode_small_ref``
    both map to ``encode_small``, so they will be paired together while
    ``encode_large_*`` variants form a separate pair.
    """
    # Check markers on the FULL lowered name first (before stripping test_),
    # so that patterns like "_ours" in "test_ours" are detected correctly.
    m = method.lower()

    # Strip zerodep markers
    for marker in _ZERODEP_MARKERS:
        if marker in m:
            m = m.replace(marker, "", 1)
            break
    else:
        # Strip reference library markers — longest key first so that
        # e.g. "httpx_sse" matches before "httpx".
        for frag in sorted(_REF_LIBS, key=len, reverse=True):
            if frag in m:
                m = m.replace(frag, "", 1)
                break
        else:
            # Last resort: strip generic "_ref" suffix
            # (e.g. toon's test_encode_small_ref)
            if m.endswith("_ref"):
                m = m[:-4]

    # NOW strip "test_" prefix (after marker removal to avoid boundary issues)
    m = m.removeprefix("test_").removeprefix("test")

    # Normalise residual underscores
    m = m.strip("_")
    while "__" in m:
        m = m.replace("__", "_")

    return m


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

            # Group by canonical pairing key so that only same-size /
            # same-operation variants are compared (e.g. encode_small_ours
            # pairs with encode_small_ref, NOT encode_large_ref).
            zd_by_key: dict[str, list] = defaultdict(list)
            for e in zd_entries:
                zd_by_key[_pairing_key(e["method"])].append(e)

            ref_by_key: dict[str, list] = defaultdict(list)
            for e in ref_entries:
                ref_by_key[_pairing_key(e["method"])].append(e)

            common_keys = set(zd_by_key) & set(ref_by_key)

            if common_keys:
                # Pair by matching canonical keys
                matched_zd_keys: set[str] = set()
                matched_ref_keys: set[str] = set()

                for key in sorted(common_keys):
                    matched_zd_keys.add(key)
                    matched_ref_keys.add(key)
                    for zd in zd_by_key[key]:
                        for ref in ref_by_key[key]:
                            ratio = (
                                zd["mean"] / ref["mean"]
                                if ref["mean"] > 0
                                else float("inf")
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

                # Unmatched zerodep entries → standalone
                for key in sorted(set(zd_by_key) - matched_zd_keys):
                    for e in zd_by_key[key]:
                        standalone.append(
                            {
                                "operation": op_name,
                                "variant": e["method"].removeprefix("test_"),
                                "mean": e["mean"],
                                "ops": e["ops"],
                            }
                        )

                # Unmatched reference entries → standalone
                for key in sorted(set(ref_by_key) - matched_ref_keys):
                    for e in ref_by_key[key]:
                        standalone.append(
                            {
                                "operation": op_name,
                                "variant": e["label"],
                                "mean": e["mean"],
                                "ops": e["ops"],
                            }
                        )
            else:
                # No canonical keys overlap — fall back to cross-product
                # pairing (e.g. persistdict where zerodep variants like
                # _json/_sqlite have no 1:1 reference counterpart).
                for zd in zd_entries:
                    for ref in ref_entries:
                        ratio = (
                            zd["mean"] / ref["mean"]
                            if ref["mean"] > 0
                            else float("inf")
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
:root, [data-theme="light"] {
  --bg: #fff; --fg: #1a1a2e; --card-bg: #f8f9fa; --border: #dee2e6;
  --green: #198754; --red: #dc3545; --yellow: #b8860b; --blue: #0d6efd;
  --accent: #6f42c1; --meta: #666;
}
[data-theme="dark"] {
  --bg: #1a1a2e; --fg: #e0e0e0; --card-bg: #16213e; --border: #334155;
  --green: #4ade80; --red: #f87171; --yellow: #facc15; --blue: #60a5fa;
  --accent: #a78bfa; --meta: #999;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #1a1a2e; --fg: #e0e0e0; --card-bg: #16213e; --border: #334155;
    --green: #4ade80; --red: #f87171; --yellow: #facc15; --blue: #60a5fa;
    --accent: #a78bfa; --meta: #999;
  }
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg); color: var(--fg); line-height: 1.6;
  max-width: 1200px; margin: 0 auto; padding: 2rem 1rem;
  transition: background .2s, color .2s;
}
h1 { font-size: 1.8rem; margin-bottom: .5rem; }
h2 {
  font-size: 1.4rem; margin: 2rem 0 1rem;
  border-bottom: 2px solid var(--accent); padding-bottom: .3rem;
}
h3 { font-size: 1.1rem; margin: 1rem 0 .5rem; color: var(--accent); }
.meta { color: var(--meta); font-size: .9rem; margin-bottom: 2rem; }
.header-row {
  display: flex; align-items: center; justify-content: space-between;
}
.theme-toggle {
  background: var(--card-bg); border: 1px solid var(--border);
  border-radius: 6px; padding: .4rem .8rem; cursor: pointer;
  color: var(--fg); font-size: .85rem;
}
.theme-toggle:hover { border-color: var(--accent); }
.summary-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem; margin-bottom: 2rem;
}
.summary-card {
  background: var(--card-bg); border: 1px solid var(--border);
  border-radius: 8px; padding: 1rem; text-align: center;
}
.summary-card .num { font-size: 2rem; font-weight: bold; }
.summary-card .label { font-size: .85rem; color: var(--meta); }
table {
  width: 100%; border-collapse: collapse; margin-bottom: 1rem;
  font-size: .9rem;
}
th, td {
  padding: .5rem .75rem; border: 1px solid var(--border);
  text-align: left;
}
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
.standalone-table { margin-top: 1rem; }
"""

_CHART_COLORS = {
    "zerodep": "rgba(111, 66, 193, 0.8)",  # purple
    "reference": "rgba(13, 110, 253, 0.6)",  # blue
}


def _ratio_class(ratio: float) -> str:
    if ratio < 0.95:
        return "faster"
    if ratio > 1.05:
        return "slower"
    return "similar"


def _ratio_text(ratio: float) -> str:
    if ratio < 0.95:
        return f"{1 / ratio:.1f}x faster"
    if ratio > 1.05:
        return f"{ratio:.1f}x slower"
    return "~equal"


def _build_sparkline_init_js(module_names: list[str], data_js_path: str) -> str:
    """Generate JS that loads history and draws a sparkline per module."""
    modules_json = json.dumps(module_names)
    return f"""\
(async function() {{
  var data = await loadHistory('{data_js_path}');
  if (!data || !data.entries || !data.entries.Benchmark) return;
  var modules = {modules_json};
  modules.forEach(function(mod) {{
    var canvas = document.getElementById('sparkline_' + mod);
    if (!canvas) return;
    var filtered = filterBenchesForModule(data.entries.Benchmark, mod);
    if (filtered.length < 2) {{ canvas.style.display = 'none'; return; }}
    // Compute median zerodep ops/s per entry
    var points = filtered.map(function(entry) {{
      var zdOps = entry.benches
        .filter(function(b) {{ return isZerodepBench(b.name); }})
        .map(function(b) {{ return b.value; }});
      if (!zdOps.length) return null;
      zdOps.sort(function(a,b) {{ return a - b; }});
      var mid = Math.floor(zdOps.length / 2);
      var median = zdOps.length % 2 ? zdOps[mid] : (zdOps[mid-1]+zdOps[mid])/2;
      return median;
    }}).filter(function(v) {{ return v !== null; }});
    if (points.length < 2) {{ canvas.style.display = 'none'; return; }}
    // Draw simple sparkline on canvas
    var ctx = canvas.getContext('2d');
    var w = canvas.width, h = canvas.height;
    var mn = Math.min.apply(null, points), mx = Math.max.apply(null, points);
    var range = mx - mn || 1;
    ctx.strokeStyle = getComputedStyle(document.documentElement)
      .getPropertyValue('--accent').trim() || '#6f42c1';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    points.forEach(function(v, i) {{
      var x = (i / (points.length - 1)) * w;
      var y = h - ((v - mn) / range) * (h - 2) - 1;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }});
    ctx.stroke();
  }});
}})();"""


def _generate_html(comparisons: list[dict], meta: dict) -> str:
    # Summary stats
    total_pairs = sum(len(m["pairs"]) for m in comparisons)
    n_modules = len([m for m in comparisons if m["pairs"] or m["standalone"]])

    faster_count = sum(1 for m in comparisons for p in m["pairs"] if p["ratio"] < 0.95)
    similar_count = sum(
        1 for m in comparisons for p in m["pairs"] if 0.95 <= p["ratio"] <= 1.05
    )
    slower_count = sum(1 for m in comparisons for p in m["pairs"] if p["ratio"] > 1.05)

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
        sparkline_id = f"sparkline_{module}"
        s += (
            f"<h2>{module}"
            f'<span class="sparkline-container">'
            f'<canvas id="{sparkline_id}" width="60" height="20">'
            f"</canvas></span>"
            f'<a href="modules/{module}.html" '
            f'style="font-size:.85rem;margin-left:.5rem;'
            f'color:var(--accent)">\u2197</a>'
            f"</h2>\n"
        )

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
    history_link = '<a href="history.html" class="history-link">\U0001f4c8 History</a>'
    nav = nav_open + " ".join(nav_links) + history_link + "</div>"

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

    # Build sparkline init JS for each module
    module_names = [m["module"] for m in comparisons if m["pairs"] or m["standalone"]]
    sparkline_init = _build_sparkline_init_js(module_names, "./data.js")

    html = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" '
        'content="width=device-width, initial-scale=1">\n'
        f"<title>zerodep Benchmark — {version}</title>\n"
        f"<style>{_CSS}\n{_TREND_CSS}</style>\n"
        f'<script src="{_CHARTJS_URL}"></script>\n'
        f'<script src="{_CHARTJS_ADAPTER_URL}"></script>\n'
        "</head>\n<body>\n"
        '<div class="header-row">\n'
        "<h1>zerodep Benchmark Report</h1>\n"
        '<button class="theme-toggle" id="theme-toggle">'
        "\u263e Dark</button>\n</div>\n"
        f'<p class="meta">{meta_line}</p>\n'
        f'<div class="summary-grid">\n{cards}\n</div>\n'
        f"{nav}\n"
        f"{''.join(sections)}\n"
        f"<script>\n{_HISTORY_JS}\n{''.join(charts_js)}\n"
        f"{sparkline_init}\n"
        f"{_THEME_JS}\n</script>\n"
        "</body>\n</html>"
    )
    return html


_THEME_JS = """\
(function() {
  var btn = document.getElementById('theme-toggle');
  if (!btn) return;
  function setTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    btn.textContent = t === 'dark' ? '\\u2600 Light' : '\\u263E Dark';
    localStorage.setItem('bench-theme', t);
  }
  var saved = localStorage.getItem('bench-theme');
  if (saved) setTheme(saved);
  btn.addEventListener('click', function() {
    var cur = document.documentElement.getAttribute('data-theme');
    if (!cur) {
      cur = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark' : 'light';
    }
    setTheme(cur === 'dark' ? 'light' : 'dark');
  });
})();"""

_CHARTJS_URL = "https://cdn.jsdelivr.net/npm/chart.js@4"

# ---------------------------------------------------------------------------
# Historical trend support (client-side)
# ---------------------------------------------------------------------------

_TREND_CSS = """\
.trend-section {
  margin-top: 2rem; padding-top: 1.5rem;
  border-top: 1px dashed var(--border);
}
.trend-section h3 { margin-bottom: .8rem; }
.trend-chart-container {
  background: var(--card-bg); border: 1px solid var(--border);
  border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem;
  height: 320px; position: relative;
}
.trend-empty {
  color: var(--meta); font-style: italic; text-align: center;
  padding: 2rem 0;
}
.sparkline-container {
  display: inline-block; vertical-align: middle; margin-left: .5rem;
}
.history-link {
  font-size: .9rem; margin-left: 1rem;
  color: var(--accent); text-decoration: none;
}
.history-link:hover { text-decoration: underline; }
.history-module-section { margin-bottom: 3rem; }
.history-chart-container {
  background: var(--card-bg); border: 1px solid var(--border);
  border-radius: 8px; padding: 1rem; height: 400px;
}
"""

# Shared JS for loading and processing data.js history
_HISTORY_JS = """\
async function loadHistory(dataJsPath) {
  try {
    var resp = await fetch(dataJsPath);
    if (!resp.ok) return null;
    var text = await resp.text();
    var jsonStr = text.replace(/^window\\.BENCHMARK_DATA\\s*=\\s*/, '')
                      .replace(/;\\s*$/, '');
    return JSON.parse(jsonStr);
  } catch(e) { return null; }
}

function filterBenchesForModule(entries, moduleName) {
  if (!entries || !entries.length) return [];
  return entries.map(function(entry) {
    return {
      date: entry.date,
      commit: entry.commit,
      benches: entry.benches.filter(function(b) {
        return b.name.split('/')[0] === moduleName;
      })
    };
  }).filter(function(e) { return e.benches.length > 0; });
}

function isZerodepBench(name) {
  var lower = name.toLowerCase();
  var markers = ['zerodep','pure_python','openssl','_ours','ours_'];
  return markers.some(function(m) { return lower.indexOf(m) !== -1; });
}

function benchLabel(name) {
  // "aes/test_aes_benchmark.py::TestEcbEncryptSmall::test_pure_python"
  // → "ECB Encrypt (Small) / pure_python"
  var parts = name.split('::');
  var method = parts[parts.length - 1] || name;
  return method.replace(/^test_/, '');
}

// Distinct colors for trend lines
var TREND_COLORS = [
  '#6f42c1','#0d6efd','#198754','#dc3545','#fd7e14',
  '#20c997','#e83e8c','#6610f2','#17a2b8','#ffc107'
];
"""

# JS to render a trend chart for a specific module page
_MODULE_TREND_INIT_JS = """\
(async function() {{
  var section = document.getElementById('trend-section');
  if (!section) return;
  var data = await loadHistory('{data_js_path}');
  if (!data || !data.entries || !data.entries.Benchmark) {{
    section.style.display = 'none'; return;
  }}
  var filtered = filterBenchesForModule(data.entries.Benchmark, '{module}');
  if (!filtered.length) {{ section.style.display = 'none'; return; }}

  // Collect unique zerodep bench names
  var nameSet = {{}};
  filtered.forEach(function(entry) {{
    entry.benches.forEach(function(b) {{
      if (isZerodepBench(b.name)) nameSet[b.name] = true;
    }});
  }});
  var names = Object.keys(nameSet).sort();
  if (!names.length) {{ section.style.display = 'none'; return; }}

  // Build datasets: one line per bench name
  var datasets = names.map(function(name, i) {{
    var pts = [];
    filtered.forEach(function(entry) {{
      var bench = entry.benches.find(function(b) {{ return b.name === name; }});
      if (bench) pts.push({{ x: new Date(entry.date), y: bench.value }});
    }});
    return {{
      label: benchLabel(name),
      data: pts,
      borderColor: TREND_COLORS[i % TREND_COLORS.length],
      backgroundColor: TREND_COLORS[i % TREND_COLORS.length] + '20',
      fill: false, tension: 0.3, pointRadius: 3, borderWidth: 2,
    }};
  }});

  section.style.display = '';
  new Chart(document.getElementById('trend-chart'), {{
    type: 'line',
    data: {{ datasets: datasets }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        legend: {{
          position: 'bottom',
          labels: {{ boxWidth: 12, font: {{ size: 11 }} }}
        }},
        title: {{
          display: true,
          text: '{module} — zerodep ops/s over time'
        }},
        tooltip: {{
          callbacks: {{
            title: function(items) {{
              var d = items[0].raw.x;
              return d.toLocaleDateString();
            }},
            afterTitle: function(items) {{
              // Show commit from filtered data
              var ts = items[0].raw.x.getTime();
              var entry = filtered.find(function(e) {{
                return Math.abs(e.date - ts) < 86400000;
              }});
              return entry ? 'commit: ' + (entry.commit.id || '').substring(0,8) : '';
            }}
          }}
        }}
      }},
      scales: {{
        x: {{
          type: 'time', time: {{ unit: 'day' }},
          title: {{ display: true, text: 'Date' }}
        }},
        y: {{
          type: 'logarithmic',
          title: {{ display: true, text: 'ops/s (log)' }}
        }}
      }}
    }}
  }});
}})();"""

# Chartjs-adapter-date-fns for time axis
_CHARTJS_ADAPTER_URL = "https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3"


def _generate_module_page(mod_data: dict, meta: dict) -> str | None:
    """Generate a standalone HTML page for a single module."""
    module = mod_data["module"]
    pairs = mod_data["pairs"]
    standalone = mod_data["standalone"]

    if not pairs and not standalone:
        return None

    version = meta.get("version", "unknown")
    commit = meta.get("commit", "")
    commit_short = commit[:8] if commit else "N/A"
    timestamp = meta.get("datetime", "")

    charts_js = []
    body = f"<h2>{module}</h2>\n"

    if pairs:
        body += "<table>\n<thead><tr>"
        body += "<th>Operation</th><th>zerodep</th>"
        body += "<th>Reference</th>"
        body += "<th>zerodep time</th><th>Ref time</th>"
        body += "<th>zerodep ops/s</th><th>Ref ops/s</th>"
        body += "<th>Ratio</th></tr></thead>\n<tbody>\n"

        for p in pairs:
            rc = _ratio_class(p["ratio"])
            body += "<tr>"
            body += f"<td>{p['operation']}</td>"
            body += f"<td>{p['zd_variant']}</td>"
            body += f"<td>{p['ref_label']}</td>"
            body += f"<td>{_human_time(p['zd_mean'])}</td>"
            body += f"<td>{_human_time(p['ref_mean'])}</td>"
            body += f"<td>{_human_ops(p['zd_ops'])}</td>"
            body += f"<td>{_human_ops(p['ref_ops'])}</td>"
            body += f'<td class="ratio-cell {rc}">{_ratio_text(p["ratio"])}</td>'
            body += "</tr>\n"
        body += "</tbody></table>\n"

        op_best: dict[str, dict] = {}
        for p in pairs:
            op = p["operation"]
            if op not in op_best or p["ref_ops"] > op_best[op]["ref_ops"]:
                op_best[op] = p

        labels = list(op_best.keys())
        zd_ops = [op_best[op]["zd_ops"] for op in labels]
        ref_ops = [op_best[op]["ref_ops"] for op in labels]
        ref_labels_list = [op_best[op]["ref_label"] for op in labels]

        cid = "chart_0"
        body += f'<div class="chart-container"><canvas id="{cid}"></canvas></div>\n'

        ref_name = json.dumps(
            ref_labels_list[0] if len(set(ref_labels_list)) == 1 else "Reference"
        )
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
        label: {ref_name} + ' (ops/s)',
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
      title: {{ display: true, text: '{module} — ops/s (higher is better)' }}
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
        body += "<h3>Standalone benchmarks</h3>\n"
        body += '<table class="standalone-table">\n<thead><tr>'
        body += "<th>Operation</th><th>Variant</th>"
        body += "<th>Mean</th><th>ops/s</th>"
        body += "</tr></thead>\n<tbody>\n"
        for st in standalone:
            body += "<tr>"
            body += f"<td>{st['operation']}</td>"
            body += f"<td>{st['variant']}</td>"
            body += f"<td>{_human_time(st['mean'])}</td>"
            body += f"<td>{_human_ops(st['ops'])}</td>"
            body += "</tr>\n"
        body += "</tbody></table>\n"

    meta_line = f"Version: {version} | Commit: {commit_short} | {timestamp}"

    # Trend section (initially hidden, revealed by JS if data available)
    trend_html = (
        '<div class="trend-section" id="trend-section" style="display:none">\n'
        "<h3>Performance Trend</h3>\n"
        '<div class="trend-chart-container">'
        '<canvas id="trend-chart"></canvas></div>\n'
        "</div>\n"
    )

    trend_init = _MODULE_TREND_INIT_JS.format(
        data_js_path="../data.js",
        module=module,
    )

    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" '
        'content="width=device-width, initial-scale=1">\n'
        f"<title>{module} Benchmark — zerodep</title>\n"
        f"<style>{_CSS}\n{_TREND_CSS}</style>\n"
        f'<script src="{_CHARTJS_URL}"></script>\n'
        f'<script src="{_CHARTJS_ADAPTER_URL}"></script>\n'
        "</head>\n<body>\n"
        '<div class="header-row">\n'
        f"<h1>{module}</h1>\n"
        '<button class="theme-toggle" id="theme-toggle">'
        "\u263e Dark</button>\n</div>\n"
        f'<p class="meta">{meta_line}</p>\n'
        f"{body}\n"
        f"{trend_html}\n"
        f"<script>\n{_HISTORY_JS}\n{''.join(charts_js)}\n"
        f"{trend_init}\n"
        f"{_THEME_JS}\n</script>\n"
        "</body>\n</html>"
    )


def _generate_history_page(module_names: list[str], meta: dict) -> str:
    """Generate a standalone history.html with trend charts for all modules."""
    version = meta.get("version", "unknown")
    commit = meta.get("commit", "")
    commit_short = commit[:8] if commit else "N/A"
    timestamp = meta.get("datetime", "")
    meta_line = (
        f"Version: {version} &nbsp;|&nbsp; "
        f"Commit: {commit_short} &nbsp;|&nbsp; {timestamp}"
    )

    # Build nav links to each module section
    nav_links = " ".join(
        f'<a href="#hist-{m}" style="margin-right:1rem">{m}</a>' for m in module_names
    )
    nav = (
        '<div style="margin-bottom:1.5rem;font-size:.9rem">'
        f'<a href="index.html" style="margin-right:1rem">'
        f"\u2190 Back to Report</a>"
        f"{nav_links}</div>"
    )

    # Module sections — each gets a chart container
    sections = []
    for mod in module_names:
        sections.append(
            f'<div class="history-module-section" id="hist-{mod}">\n'
            f"<h2>{mod}</h2>\n"
            f'<div class="history-chart-container">'
            f'<canvas id="hist-chart-{mod}"></canvas></div>\n'
            f"</div>\n"
        )

    # JS to load data.js and render all charts
    modules_json = json.dumps(module_names)
    init_js = f"""\
(async function() {{
  var data = await loadHistory('./data.js');
  var modules = {modules_json};
  if (!data || !data.entries || !data.entries.Benchmark) {{
    modules.forEach(function(mod) {{
      var container = document.getElementById('hist-' + mod);
      if (container) {{
        container.querySelector('.history-chart-container').innerHTML =
          '<p class="trend-empty">No historical data available yet.</p>';
      }}
    }});
    return;
  }}
  modules.forEach(function(mod) {{
    var canvas = document.getElementById('hist-chart-' + mod);
    if (!canvas) return;
    var filtered = filterBenchesForModule(data.entries.Benchmark, mod);
    if (!filtered.length) {{
      canvas.parentElement.innerHTML =
        '<p class="trend-empty">No historical data for this module.</p>';
      return;
    }}
    // Collect unique zerodep bench names
    var nameSet = {{}};
    filtered.forEach(function(entry) {{
      entry.benches.forEach(function(b) {{
        if (isZerodepBench(b.name)) nameSet[b.name] = true;
      }});
    }});
    var names = Object.keys(nameSet).sort();
    if (!names.length) {{
      canvas.parentElement.innerHTML =
        '<p class="trend-empty">No zerodep benchmarks in history.</p>';
      return;
    }}
    var datasets = names.map(function(name, i) {{
      var pts = [];
      filtered.forEach(function(entry) {{
        var bench = entry.benches.find(function(b) {{ return b.name === name; }});
        if (bench) pts.push({{ x: new Date(entry.date), y: bench.value }});
      }});
      return {{
        label: benchLabel(name),
        data: pts,
        borderColor: TREND_COLORS[i % TREND_COLORS.length],
        backgroundColor: TREND_COLORS[i % TREND_COLORS.length] + '20',
        fill: false, tension: 0.3, pointRadius: 3, borderWidth: 2,
      }};
    }});
    new Chart(canvas, {{
      type: 'line',
      data: {{ datasets: datasets }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{
            position: 'bottom',
            labels: {{ boxWidth: 12, font: {{ size: 11 }} }}
          }},
          title: {{ display: true, text: mod + ' — zerodep ops/s over time' }},
          tooltip: {{
            callbacks: {{
              title: function(items) {{
                return items[0].raw.x.toLocaleDateString();
              }},
              afterTitle: function(items) {{
                var ts = items[0].raw.x.getTime();
                var entry = filtered.find(function(e) {{
                  return Math.abs(e.date - ts) < 86400000;
                }});
                return entry
                  ? 'commit: ' + (entry.commit.id || '').substring(0,8) : '';
              }}
            }}
          }}
        }},
        scales: {{
          x: {{
            type: 'time',
            time: {{ unit: 'day' }},
            title: {{ display: true, text: 'Date' }}
          }},
          y: {{
            type: 'logarithmic',
            title: {{ display: true, text: 'ops/s (log)' }}
          }}
        }}
      }}
    }});
  }});
}})();"""

    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" '
        'content="width=device-width, initial-scale=1">\n'
        f"<title>Performance History — zerodep</title>\n"
        f"<style>{_CSS}\n{_TREND_CSS}</style>\n"
        f'<script src="{_CHARTJS_URL}"></script>\n'
        f'<script src="{_CHARTJS_ADAPTER_URL}"></script>\n'
        "</head>\n<body>\n"
        '<div class="header-row">\n'
        "<h1>\U0001f4c8 Performance History</h1>\n"
        '<button class="theme-toggle" id="theme-toggle">'
        "\u263e Dark</button>\n</div>\n"
        f'<p class="meta">{meta_line}</p>\n'
        f"{nav}\n"
        f"{''.join(sections)}\n"
        f"<script>\n{_HISTORY_JS}\n{init_js}\n"
        f"{_THEME_JS}\n</script>\n"
        "</body>\n</html>"
    )


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

    # Generate per-module pages
    modules_dir = output_path.parent / "modules"
    modules_dir.mkdir(parents=True, exist_ok=True)
    mod_count = 0
    for mod_data in comparisons:
        page = _generate_module_page(mod_data, meta)
        if page is None:
            continue
        mod_path = modules_dir / f"{mod_data['module']}.html"
        mod_path.write_text(page)
        mod_count += 1
    print(f"  {mod_count} module pages written to {modules_dir}/")

    # Generate history page
    module_names = [m["module"] for m in comparisons if m["pairs"] or m["standalone"]]
    history_html = _generate_history_page(module_names, meta)
    history_path = output_path.parent / "history.html"
    history_path.write_text(history_html)
    print(f"  History page written to {history_path}")

    # Print summary
    total_pairs = sum(len(m["pairs"]) for m in comparisons)
    faster = sum(1 for m in comparisons for p in m["pairs"] if p["ratio"] < 0.95)
    slower = sum(1 for m in comparisons for p in m["pairs"] if p["ratio"] > 1.05)
    print(f"  {total_pairs} comparisons: {faster} faster, {slower} slower")


if __name__ == "__main__":
    main()
