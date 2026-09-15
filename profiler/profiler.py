# /// zerodep
# version = "0.0.0"
# deps = []
# tier = "medium"
# category = "devtools"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
# ///

"""Ergonomic cProfile wrapper with text and HTML report output.

Wraps ``cProfile``/``pstats`` in sync and async context managers
and renders profiling data as formatted text or self-contained HTML
with a sortable, filterable table.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Quick start::

    from profiler import Profiler

    with Profiler() as p:
        do_work()

    print(p.output_text())
    p.output_html(file="report.html")

Async usage::

    async with Profiler(async_mode=True) as p:
        await do_async_work()

    html = p.output_html()
"""

from __future__ import annotations

import cProfile
import html as _html
import io
import pstats
from pathlib import Path
from typing import Any, cast

__all__ = ["Profiler", "ProfilerError"]

_SORT_KEYS = {
    "cumulative": "cumulative",
    "cumtime": "cumulative",
    "tottime": "tottime",
    "total": "tottime",
    "calls": "calls",
    "ncalls": "calls",
    "name": "name",
    "filename": "filename",
}

_VALID_STYLES = {"table", "flamegraph", "icicle"}


class ProfilerError(Exception):
    """Raised when profiler operations fail."""


class Profiler:
    """Ergonomic wrapper around cProfile with text and HTML output.

    Args:
        async_mode: If True, the profiler can be used as an async context
            manager.  cProfile still captures the synchronous execution
            underneath the event loop.
        timer: Custom timer function passed to ``cProfile.Profile``.
        builtins: Whether to profile built-in functions (default True).
        subcalls: Whether to profile subcalls (default True).
        sort_by: Default sort key for output methods.  One of
            ``"cumulative"``, ``"tottime"``, ``"calls"``, ``"name"``.
    """

    def __init__(
        self,
        *,
        async_mode: bool = False,
        timer: Any = None,
        builtins: bool = True,
        subcalls: bool = True,
        sort_by: str = "cumulative",
    ) -> None:
        self._async_mode = async_mode
        self._builtins = builtins
        self._subcalls = subcalls
        self._default_sort = self._resolve_sort_key(sort_by)
        self._timer = timer
        self._profile = self._make_profile()
        self._stats: pstats.Stats | None = None
        self._running = False

    def _make_profile(self) -> cProfile.Profile:
        if self._timer is not None:
            return cProfile.Profile(timer=self._timer)
        return cProfile.Profile()

    @staticmethod
    def _resolve_sort_key(key: str) -> str:
        resolved = _SORT_KEYS.get(key)
        if resolved is None:
            raise ValueError(
                f"unknown sort key {key!r}, expected one of: "
                f"{', '.join(sorted(_SORT_KEYS))}"
            )
        return resolved

    # -- Lifecycle -----------------------------------------------------------

    def start(self) -> None:
        """Enable the profiler.  No-op if already running."""
        if self._running:
            return
        self._profile.enable(subcalls=self._subcalls, builtins=self._builtins)
        self._running = True

    def stop(self) -> None:
        """Disable the profiler and build internal stats.  No-op if not running."""
        if not self._running:
            return
        self._profile.disable()
        self._running = False
        stream = io.StringIO()
        self._stats = pstats.Stats(self._profile, stream=stream)

    def reset(self) -> None:
        """Clear all collected data so the instance can be reused."""
        if self._running:
            self._profile.disable()
            self._running = False
        self._profile = self._make_profile()
        self._stats = None

    # -- Context managers ----------------------------------------------------

    def __enter__(self) -> Profiler:
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()

    async def __aenter__(self) -> Profiler:
        if not self._async_mode:
            raise ProfilerError(
                "async context manager requires Profiler(async_mode=True)"
            )
        self.start()
        return self

    async def __aexit__(self, *args: object) -> None:
        self.stop()

    # -- Properties ----------------------------------------------------------

    @property
    def stats(self) -> pstats.Stats:
        """The underlying ``pstats.Stats`` object.

        Raises:
            ProfilerError: If accessed before profiling has completed.
        """
        if self._stats is None:
            raise ProfilerError("no profiling data — call stop() first")
        return self._stats

    @property
    def is_running(self) -> bool:
        """Whether the profiler is currently enabled."""
        return self._running

    @property
    def total_time(self) -> float:
        """Total time recorded by the profiler (seconds).

        Raises:
            ProfilerError: If accessed before profiling has completed.
        """
        # CPython internal; no public accessor for total wall time
        return cast(Any, self.stats).total_tt

    # -- Output --------------------------------------------------------------

    def _ensure_stopped(self) -> None:
        if self._stats is None:
            raise ProfilerError("no profiling data — run the profiler first")

    def output_text(
        self,
        *,
        sort_by: str | None = None,
        limit: int | None = None,
        file: str | Path | None = None,
    ) -> str:
        """Return formatted profiling stats as text.

        Args:
            sort_by: Override the default sort key.
            limit: Show only the top N functions.
            file: If provided, also write output to this file path.

        Returns:
            Formatted stats text.

        Raises:
            ProfilerError: If called before profiling has completed.
        """
        self._ensure_stopped()
        sort_key = self._resolve_sort_key(sort_by) if sort_by else self._default_sort

        assert self._stats is not None  # noqa: S101
        stream = io.StringIO()
        cast(Any, self._stats).stream = stream
        self._stats.sort_stats(sort_key)
        if limit is not None:
            self._stats.print_stats(limit)
        else:
            self._stats.print_stats()
        text = stream.getvalue()

        if file is not None:
            Path(file).write_text(text, encoding="utf-8")

        return text

    def output_html(
        self,
        *,
        style: str = "table",
        sort_by: str | None = None,
        limit: int | None = None,
        title: str = "Profile Report",
        file: str | Path | None = None,
    ) -> str:
        """Return a self-contained HTML profiling report.

        Args:
            style: Output style. Currently ``"table"`` is supported.
                Future: ``"flamegraph"``, ``"icicle"``.
            sort_by: Override the default sort key for initial table order.
            limit: Show only the top N functions.
            title: HTML page title.
            file: If provided, also write the HTML to this file path.

        Returns:
            Complete HTML document string with inline CSS/JS.

        Raises:
            ProfilerError: If called before profiling has completed.
            ValueError: If *style* is not recognized.
        """
        self._ensure_stopped()
        if style not in _VALID_STYLES:
            raise ValueError(
                f"unknown style {style!r}, expected one of: "
                f"{', '.join(sorted(_VALID_STYLES))}"
            )

        if style in ("flamegraph", "icicle"):
            tree = self._extract_call_tree()
            doc = self._build_flame_html(tree, title, inverted=(style == "icicle"))
        else:
            rows = self._extract_rows(sort_by=sort_by, limit=limit)
            doc = self._build_table_html(rows, title)

        if file is not None:
            Path(file).write_text(doc, encoding="utf-8")

        return doc

    # -- Data extraction -----------------------------------------------------

    def _extract_rows(
        self,
        *,
        sort_by: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Extract profiling data as a sorted list of dicts."""
        assert self._stats is not None  # noqa: S101
        sort_key = self._resolve_sort_key(sort_by) if sort_by else self._default_sort

        stats_any = cast(Any, self._stats)
        total_tt = stats_any.total_tt or 1e-9

        rows: list[dict[str, Any]] = []
        for (filename, lineno, funcname), (
            cc,
            nc,
            tt,
            ct,
            _callers,
        ) in stats_any.stats.items():
            rows.append(
                {
                    "func": funcname,
                    "file": filename,
                    "lineno": lineno,
                    "calls": nc,
                    "primitive_calls": cc,
                    "tottime": tt,
                    "cumtime": ct,
                    "percall_tot": tt / nc if nc else 0.0,
                    "percall_cum": ct / cc if cc else 0.0,
                    "tottime_pct": tt / total_tt * 100,
                    "cumtime_pct": ct / total_tt * 100,
                }
            )

        sort_map = {
            "cumulative": lambda r: r["cumtime"],
            "tottime": lambda r: r["tottime"],
            "calls": lambda r: r["calls"],
            "name": lambda r: r["func"],
            "filename": lambda r: r["file"],
        }
        key_fn = sort_map.get(sort_key, sort_map["cumulative"])
        reverse = sort_key not in ("name", "filename")
        rows.sort(key=key_fn, reverse=reverse)

        if limit is not None:
            rows = rows[:limit]

        return rows

    def _extract_call_tree(self) -> list[dict[str, Any]]:
        """Build a call tree from caller/callee data for flamegraph rendering.

        Returns a list of root nodes.  Each node is a dict with keys:
        name, file, lineno, cumtime, tottime, calls, children (list of nodes).
        """
        assert self._stats is not None  # noqa: S101
        stats_any = cast(Any, self._stats)
        self._stats.calc_callees()
        all_callees: dict[tuple, dict[tuple, tuple]] = stats_any.all_callees
        total_tt = stats_any.total_tt or 1e-9

        roots: list[tuple] = []
        for key, (cc, nc, tt, ct, callers) in stats_any.stats.items():
            if (
                not callers
                and key[2] != "<method 'disable' of '_lsprof.Profiler' objects>"
            ):
                roots.append(key)

        def _build_node(
            key: tuple, visited: frozenset[tuple], edge_ct: float | None
        ) -> dict[str, Any]:
            cc, nc, tt, ct, _callers = stats_any.stats[key]
            node_ct = edge_ct if edge_ct is not None else ct
            children: list[dict[str, Any]] = []
            callees = all_callees.get(key, {})
            for callee_key, edge in callees.items():
                if callee_key in visited:
                    continue
                child_ct = edge[3] if len(edge) == 4 else edge[1]
                children.append(
                    _build_node(callee_key, visited | {callee_key}, child_ct)
                )
            children.sort(key=lambda c: c["cumtime"], reverse=True)
            return {
                "name": key[2],
                "file": key[0],
                "lineno": key[1],
                "cumtime": node_ct,
                "tottime": tt,
                "calls": nc,
                "cumtime_pct": node_ct / total_tt * 100,
                "children": children,
            }

        tree = []
        for root_key in roots:
            tree.append(_build_node(root_key, frozenset({root_key}), None))
        tree.sort(key=lambda n: n["cumtime"], reverse=True)
        return tree

    # -- HTML rendering ------------------------------------------------------

    def _build_flame_html(
        self,
        tree: list[dict[str, Any]],
        title: str,
        *,
        inverted: bool = False,
    ) -> str:
        """Build a self-contained flamegraph or icicle chart HTML document."""
        import json as _json

        total_time = self.total_time or 1e-9
        style_name = "Icicle Chart" if inverted else "Flamegraph"

        return (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f"<title>{_html.escape(title)}</title>\n"
            f"<style>\n{_FLAME_CSS}\n</style>\n"
            "</head>\n<body>\n"
            '<div class="wrap">\n'
            f"<h1>{_html.escape(title)}</h1>\n"
            f'<p class="meta">{_html.escape(style_name)} &middot; '
            f"Total time: {total_time:.6f}s</p>\n"
            '<div class="toolbar">\n'
            '<input type="text" id="filter-input" class="filter-input" '
            'placeholder="Search functions…" autocomplete="off">\n'
            '<button id="reset-zoom" class="btn">Reset Zoom</button>\n'
            '<button id="theme-toggle" class="btn" title="Toggle theme">'
            "\U0001f319</button>\n"
            "</div>\n"
            f'<div id="flame-container" class="flame-container'
            f'{" inverted" if inverted else ""}">\n'
            "</div>\n</div>\n"
            "<script>\n"
            f"var FLAME_DATA={_json.dumps(tree, separators=(',', ':'))};\n"
            f"var TOTAL_TIME={total_time};\n"
            f"{_FLAME_JS}\n"
            "</script>\n"
            "</body>\n</html>"
        )

    def _build_table_html(self, rows: list[dict[str, Any]], title: str) -> str:
        max_cumtime = max((r["cumtime"] for r in rows), default=1.0) or 1e-9
        max_tottime = max((r["tottime"] for r in rows), default=1.0) or 1e-9

        tbody_parts: list[str] = []
        for r in rows:
            func_display = _html.escape(f"{r['file']}:{r['lineno']}({r['func']})")
            cum_bar = r["cumtime"] / max_cumtime * 100
            tot_bar = r["tottime"] / max_tottime * 100

            calls_str = (
                str(r["calls"])
                if r["calls"] == r["primitive_calls"]
                else f"{r['calls']}/{r['primitive_calls']}"
            )

            tbody_parts.append(
                f"<tr>"
                f'<td class="fn" title="{func_display}">{func_display}</td>'
                f'<td class="num bar-cell" data-sort-value="{r["cumtime"]:.9f}">'
                f'<div class="bar" style="width:{cum_bar:.1f}%"></div>'
                f'<span class="val">{r["cumtime"]:.6f}</span></td>'
                f'<td class="num bar-cell" data-sort-value="{r["tottime"]:.9f}">'
                f'<div class="bar" style="width:{tot_bar:.1f}%"></div>'
                f'<span class="val">{r["tottime"]:.6f}</span></td>'
                f'<td class="num" data-sort-value="{r["calls"]}">{calls_str}</td>'
                f'<td class="num" data-sort-value="{r["percall_cum"]:.9f}">'
                f"{r['percall_cum']:.6f}</td>"
                f'<td class="num" data-sort-value="{r["cumtime_pct"]:.2f}">'
                f"{r['cumtime_pct']:.1f}%</td>"
                f"</tr>"
            )

        total_funcs = len(rows)
        total_time_s = self.total_time

        return (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f"<title>{_html.escape(title)}</title>\n"
            f"<style>\n{_TABLE_CSS}\n</style>\n"
            "</head>\n<body>\n"
            '<div class="wrap">\n'
            f"<h1>{_html.escape(title)}</h1>\n"
            f'<p class="meta">Total time: {total_time_s:.6f}s &middot; '
            f"{total_funcs} functions</p>\n"
            '<div class="toolbar">\n'
            '<input type="text" id="filter-input" class="filter-input" '
            'placeholder="Filter functions…" autocomplete="off">\n'
            '<button id="theme-toggle" class="btn" title="Toggle theme">'
            "\U0001f319</button>\n"
            "</div>\n"
            '<div class="table-wrap">\n'
            '<table id="profile-table">\n<thead><tr>\n'
            '<th data-sortable data-sort-type="string">Function'
            '<span class="arrow"></span></th>\n'
            '<th data-sortable data-sort-type="number">Cumulative'
            '<span class="arrow"></span></th>\n'
            '<th data-sortable data-sort-type="number">Total (self)'
            '<span class="arrow"></span></th>\n'
            '<th data-sortable data-sort-type="number">Calls'
            '<span class="arrow"></span></th>\n'
            '<th data-sortable data-sort-type="number">Per Call (cum)'
            '<span class="arrow"></span></th>\n'
            '<th data-sortable data-sort-type="number">% of Total'
            '<span class="arrow"></span></th>\n'
            "</tr></thead>\n<tbody>\n"
            + "\n".join(tbody_parts)
            + "\n</tbody></table>\n</div>\n</div>\n"
            f"<script>\n{_TABLE_JS}\n</script>\n"
            "</body>\n</html>"
        )


# ---------------------------------------------------------------------------
# Inline CSS for HTML table output
# ---------------------------------------------------------------------------

_TABLE_CSS = """\
:root,[data-theme="light"]{
  --bg:#fff;--fg:#1a1a2e;--card:#f8f9fa;--border:#dee2e6;
  --bar-bg:rgba(13,110,253,.12);--bar-fg:rgba(13,110,253,.55);
  --hover:#f0f4ff;--meta:#666;--input-bg:#fff;--input-border:#ccc;
}
[data-theme="dark"]{
  --bg:#1a1a2e;--fg:#e0e0e0;--card:#252540;--border:#3a3a5c;
  --bar-bg:rgba(99,140,255,.15);--bar-fg:rgba(99,140,255,.5);
  --hover:#2a2a4a;--meta:#999;--input-bg:#252540;--input-border:#3a3a5c;
}
@media(prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --bg:#1a1a2e;--fg:#e0e0e0;--card:#252540;--border:#3a3a5c;
    --bar-bg:rgba(99,140,255,.15);--bar-fg:rgba(99,140,255,.5);
    --hover:#2a2a4a;--meta:#999;--input-bg:#252540;--input-border:#3a3a5c;
  }
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,sans-serif;background:var(--bg);
  color:var(--fg);line-height:1.5}
.wrap{max-width:1200px;margin:0 auto;padding:1.5rem}
h1{font-size:1.4rem;margin-bottom:.25rem}
.meta{color:var(--meta);font-size:.85rem;margin-bottom:1rem}
.toolbar{display:flex;gap:.5rem;margin-bottom:1rem;align-items:center}
.filter-input{flex:1;padding:.4rem .6rem;font-size:.85rem;border:1px solid
  var(--input-border);border-radius:4px;background:var(--input-bg);
  color:var(--fg);outline:none}
.filter-input:focus{border-color:var(--bar-fg)}
.btn{padding:.35rem .7rem;font-size:.85rem;border:1px solid var(--border);
  border-radius:4px;background:var(--card);color:var(--fg);cursor:pointer}
.btn:hover{background:var(--hover)}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.82rem;
  font-variant-numeric:tabular-nums}
th,td{padding:.4rem .6rem;text-align:left;border-bottom:1px solid var(--border)}
th{background:var(--card);cursor:pointer;user-select:none;white-space:nowrap;
  position:sticky;top:0;z-index:1}
th:hover{background:var(--hover)}
.arrow{margin-left:4px;font-size:.65rem;opacity:.3}
th.asc .arrow::after{content:'\\25B2';opacity:1}
th.desc .arrow::after{content:'\\25BC';opacity:1}
tr:hover{background:var(--hover)}
.fn{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.78rem;
  max-width:500px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.num{text-align:right;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:.78rem;white-space:nowrap}
.bar-cell{position:relative}
.bar{position:absolute;left:0;top:0;bottom:0;background:var(--bar-bg);
  border-right:2px solid var(--bar-fg);pointer-events:none}
.val{position:relative;z-index:1}
"""

# ---------------------------------------------------------------------------
# Inline JS for HTML table sorting, filtering, and theme toggle
# ---------------------------------------------------------------------------

_TABLE_JS = """\
(function(){
  var col=-1,asc=true;
  function sortTable(ci){
    var t=document.getElementById('profile-table');
    var tb=t.tBodies[0],rows=Array.prototype.slice.call(tb.rows);
    var th=t.tHead.rows[0].cells[ci];
    if(col===ci)asc=!asc;else{col=ci;asc=th.getAttribute('data-sort-type')!=='number';}
    var numeric=th.getAttribute('data-sort-type')==='number';
    rows.sort(function(a,b){
      var va=a.cells[ci].getAttribute('data-sort-value')||a.cells[ci].textContent;
      var vb=b.cells[ci].getAttribute('data-sort-value')||b.cells[ci].textContent;
      if(numeric){va=parseFloat(va)||0;vb=parseFloat(vb)||0;}
      else{va=va.toLowerCase();vb=vb.toLowerCase();}
      var c=va<vb?-1:va>vb?1:0;
      return asc?c:-c;
    });
    for(var i=0;i<rows.length;i++)tb.appendChild(rows[i]);
    var ths=t.tHead.rows[0].cells;
    for(var j=0;j<ths.length;j++){
      ths[j].classList.remove('asc','desc');
    }
    th.classList.add(asc?'asc':'desc');
  }
  function filterTable(){
    var q=document.getElementById('filter-input').value.toLowerCase();
    var rows=document.getElementById('profile-table').tBodies[0].rows;
    for(var i=0;i<rows.length;i++){
      rows[i].style.display=rows[i].textContent.toLowerCase().indexOf(q)>=0?'':'none';
    }
  }
  document.addEventListener('DOMContentLoaded',function(){
    var ths=document.querySelectorAll('#profile-table th[data-sortable]');
    for(var i=0;i<ths.length;i++){
      (function(idx){ths[idx].addEventListener('click',function(){sortTable(idx);});})(i);
    }
    var fi=document.getElementById('filter-input');
    if(fi)fi.addEventListener('input',filterTable);
    var tb=document.getElementById('theme-toggle');
    if(tb)tb.addEventListener('click',function(){
      var html=document.documentElement;
      var cur=html.getAttribute('data-theme');
      var next=cur==='dark'?'light':'dark';
      if(!cur){
        var mq=window.matchMedia&&window.matchMedia('(prefers-color-scheme:dark)');
        next=mq&&mq.matches?'light':'dark';
      }
      html.setAttribute('data-theme',next);
      tb.textContent=next==='dark'?'\\u2600':'\\uD83C\\uDF19';
    });
  });
})();
"""


# ---------------------------------------------------------------------------
# Inline CSS for flamegraph / icicle chart
# ---------------------------------------------------------------------------

_FLAME_CSS = """\
:root,[data-theme="light"]{
  --bg:#fff;--fg:#1a1a2e;--card:#f8f9fa;--border:#dee2e6;
  --hover:#f0f4ff;--meta:#666;--input-bg:#fff;--input-border:#ccc;
  --tooltip-bg:rgba(30,30,50,.92);--tooltip-fg:#f0f0f0;
}
[data-theme="dark"]{
  --bg:#1a1a2e;--fg:#e0e0e0;--card:#252540;--border:#3a3a5c;
  --hover:#2a2a4a;--meta:#999;--input-bg:#252540;--input-border:#3a3a5c;
  --tooltip-bg:rgba(240,240,255,.92);--tooltip-fg:#1a1a2e;
}
@media(prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --bg:#1a1a2e;--fg:#e0e0e0;--card:#252540;--border:#3a3a5c;
    --hover:#2a2a4a;--meta:#999;--input-bg:#252540;--input-border:#3a3a5c;
    --tooltip-bg:rgba(240,240,255,.92);--tooltip-fg:#1a1a2e;
  }
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,sans-serif;background:var(--bg);
  color:var(--fg);line-height:1.5}
.wrap{max-width:1200px;margin:0 auto;padding:1.5rem}
h1{font-size:1.4rem;margin-bottom:.25rem}
.meta{color:var(--meta);font-size:.85rem;margin-bottom:1rem}
.toolbar{display:flex;gap:.5rem;margin-bottom:1rem;align-items:center}
.filter-input{flex:1;padding:.4rem .6rem;font-size:.85rem;border:1px solid
  var(--input-border);border-radius:4px;background:var(--input-bg);
  color:var(--fg);outline:none}
.filter-input:focus{border-color:#6f8cff}
.btn{padding:.35rem .7rem;font-size:.85rem;border:1px solid var(--border);
  border-radius:4px;background:var(--card);color:var(--fg);cursor:pointer}
.btn:hover{background:var(--hover)}
.flame-container{width:100%;overflow:hidden;position:relative}
.flame-frame{position:absolute;height:22px;border:1px solid rgba(0,0,0,.15);
  border-radius:2px;overflow:hidden;cursor:pointer;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:11px;line-height:22px;padding:0 4px;white-space:nowrap;
  text-overflow:ellipsis;transition:opacity .15s}
.flame-frame:hover{border-color:rgba(0,0,0,.4);z-index:2}
.flame-frame.dimmed{opacity:.35}
.flame-frame.highlight{border-color:#ff6600;border-width:2px;z-index:3}
#tooltip{position:fixed;pointer-events:none;z-index:100;max-width:450px;
  padding:6px 10px;border-radius:4px;font-size:12px;line-height:1.4;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  background:var(--tooltip-bg);color:var(--tooltip-fg);
  box-shadow:0 2px 8px rgba(0,0,0,.25);display:none}
"""

# ---------------------------------------------------------------------------
# Inline JS for flamegraph / icicle rendering, zoom, search, tooltip
# ---------------------------------------------------------------------------

_FLAME_JS = """\
(function(){
  var container=document.getElementById('flame-container');
  var tooltip=document.createElement('div');
  tooltip.id='tooltip';document.body.appendChild(tooltip);

  var COLORS=[
    '#ff6633','#ffcc33','#33cc66','#3399ff','#cc66ff',
    '#ff9966','#66cccc','#9999ff','#ff6699','#99cc33',
    '#cc9933','#6699cc','#cc6699','#66cc99','#9966cc',
    '#ff9933','#33cccc','#6666ff','#cc3366','#339966'
  ];
  function hashColor(name){
    var h=0;for(var i=0;i<name.length;i++)h=((h<<5)-h+name.charCodeAt(i))|0;
    return COLORS[Math.abs(h)%COLORS.length];
  }

  var zoomStack=[];
  var inverted=container.classList.contains('inverted');

  function flatten(nodes,depth,parentLeft,parentWidth,totalTime,arr){
    var x=parentLeft;
    for(var i=0;i<nodes.length;i++){
      var n=nodes[i];
      var w=parentWidth*(n.cumtime/totalTime);
      if(w<0.3)continue;
      arr.push({n:n,depth:depth,left:x,width:w});
      if(n.children&&n.children.length){
        flatten(n.children,depth+1,x,w,n.cumtime,arr);
      }
      x+=w;
    }
    return arr;
  }

  function render(data,totalTime){
    var cw=container.clientWidth;
    var frames=flatten(data,0,0,cw,totalTime,[]);
    var maxDepth=0;
    for(var i=0;i<frames.length;i++){
      if(frames[i].depth>maxDepth)maxDepth=frames[i].depth;
    }
    var levelH=24;
    var totalH=(maxDepth+1)*levelH;
    container.style.height=totalH+'px';
    container.innerHTML='';

    for(var i=0;i<frames.length;i++){
      var f=frames[i];
      var el=document.createElement('div');
      el.className='flame-frame';
      el.style.left=f.left+'px';
      el.style.width=Math.max(f.width-1,1)+'px';
      if(inverted){
        el.style.top=(f.depth*levelH)+'px';
      }else{
        el.style.bottom=(f.depth*levelH)+'px';
      }
      el.style.position='absolute';
      el.style.background=hashColor(f.n.name);
      el.textContent=f.width>40?f.n.name:'';
      el.setAttribute('data-name',f.n.name);
      el.setAttribute('data-file',f.n.file+':'+f.n.lineno);
      el.setAttribute('data-cumtime',f.n.cumtime.toFixed(6));
      el.setAttribute('data-calls',f.n.calls);
      el.setAttribute('data-pct',f.n.cumtime_pct.toFixed(1));
      el._node=f.n;el._totalTime=totalTime;
      el.addEventListener('click',onFrameClick);
      el.addEventListener('mouseenter',showTooltip);
      el.addEventListener('mousemove',moveTooltip);
      el.addEventListener('mouseleave',hideTooltip);
      container.appendChild(el);
    }
  }

  function onFrameClick(e){
    var node=this._node;
    zoomStack.push({data:FLAME_DATA,total:TOTAL_TIME});
    render([node],node.cumtime);
  }

  function showTooltip(e){
    var el=this;
    tooltip.innerHTML='<b>'+escH(el.getAttribute('data-name'))+'</b><br>'
      +escH(el.getAttribute('data-file'))+'<br>'
      +'Cumulative: '+el.getAttribute('data-cumtime')+'s ('
      +el.getAttribute('data-pct')+'%)<br>'
      +'Calls: '+el.getAttribute('data-calls');
    tooltip.style.display='block';
  }
  function moveTooltip(e){
    var x=e.clientX+12,y=e.clientY+12;
    if(x+tooltip.offsetWidth>window.innerWidth)x=e.clientX-tooltip.offsetWidth-8;
    if(y+tooltip.offsetHeight>window.innerHeight)y=e.clientY-tooltip.offsetHeight-8;
    tooltip.style.left=x+'px';tooltip.style.top=y+'px';
  }
  function hideTooltip(){tooltip.style.display='none';}
  function escH(s){
    var d=document.createElement('div');
    d.textContent=s;return d.innerHTML;
  }

  document.getElementById('reset-zoom').addEventListener('click',function(){
    zoomStack=[];
    render(FLAME_DATA,TOTAL_TIME);
  });

  var fi=document.getElementById('filter-input');
  fi.addEventListener('input',function(){
    var q=fi.value.toLowerCase();
    var els=container.querySelectorAll('.flame-frame');
    for(var i=0;i<els.length;i++){
      var name=els[i].getAttribute('data-name').toLowerCase();
      if(!q){els[i].classList.remove('dimmed','highlight');}
      else if(name.indexOf(q)>=0){
        els[i].classList.remove('dimmed');
        els[i].classList.add('highlight');
      }
      else{els[i].classList.add('dimmed');els[i].classList.remove('highlight');}
    }
  });

  var tb=document.getElementById('theme-toggle');
  tb.addEventListener('click',function(){
    var html=document.documentElement;
    var cur=html.getAttribute('data-theme');
    var next=cur==='dark'?'light':'dark';
    if(!cur){
      var mq=window.matchMedia&&window.matchMedia('(prefers-color-scheme:dark)');
      next=mq&&mq.matches?'light':'dark';
    }
    html.setAttribute('data-theme',next);
    tb.textContent=next==='dark'?'\\u2600':'\\uD83C\\uDF19';
  });

  render(FLAME_DATA,TOTAL_TIME);
})();
"""
