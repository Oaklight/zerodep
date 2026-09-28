# Profiler

Zero-dependency cProfile wrapper with text and HTML report output.

> **Replaces:** `cProfile` (raw), `pyinstrument` (partial)

## Overview

The Profiler module wraps `cProfile`/`pstats` in sync and async context managers and renders profiling data as formatted text or self-contained HTML with sortable, filterable tables and interactive flamegraph/icicle chart visualizations.

| File | Description | Dependencies |
|------|-------------|--------------|
| `profiler.py` | cProfile wrapper + HTML reports | None (stdlib only: `cProfile`, `pstats`, `sys`, `threading`) |

## Key Features

- **Sync + async context managers** -- `with Profiler()` and `async with Profiler(async_mode=True)`
- **Text output** -- formatted profiling table via `output_text()`
- **HTML reports** -- self-contained HTML with sortable table, search, and dark mode via `output_html()`
- **Flamegraph / icicle chart** -- interactive visualizations with zoom, search, and collapsible stacks
- **TracingProfiler** -- per-call tracing with thread-aware collection using `sys.monitoring` (PEP 669, Python 3.12+) with `sys.settrace` fallback
- **Profile statistics** -- `stats()`, `total_time()`, `is_running()` introspection

## How to Use in Your Project

```bash
cp profiler/profiler.py your_project/
```

## Usage Examples

### Basic Profiling

```python
from profiler import Profiler

with Profiler() as p:
    do_work()

print(p.output_text())
p.output_html(file="report.html")
```

### Async Profiling

```python
from profiler import Profiler

async with Profiler(async_mode=True) as p:
    await do_async_work()

html = p.output_html()
```

### Tracing Profiler

```python
from profiler import TracingProfiler

with TracingProfiler() as p:
    do_work()

for trace in p.traces():
    print(trace)

p.output_html(file="traces.html", style="flamegraph")
```
