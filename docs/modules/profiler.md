# 性能分析器

零依赖的 cProfile 封装，支持文本和 HTML 报告输出。

> **替代:** `cProfile`（原始）、`pyinstrument`（部分）

## 概述

Profiler 模块将 `cProfile`/`pstats` 封装为同步和异步上下文管理器，支持将分析数据渲染为格式化文本或包含可排序、可过滤表格及交互式火焰图/冰柱图的独立 HTML 文件。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `profiler.py` | cProfile 封装 + HTML 报告 | 无（仅标准库：`cProfile`、`pstats`、`sys`、`threading`） |

## 主要特性

- **同步 + 异步上下文管理器** -- `with Profiler()` 和 `async with Profiler(async_mode=True)`
- **文本输出** -- 通过 `output_text()` 输出格式化分析表格
- **HTML 报告** -- 通过 `output_html()` 生成独立 HTML，支持排序、搜索和暗色模式
- **火焰图 / 冰柱图** -- 交互式可视化，支持缩放、搜索和折叠调用栈
- **TracingProfiler** -- 逐调用跟踪分析，使用 `sys.monitoring`（PEP 669，Python 3.12+）并回退到 `sys.settrace`
- **分析统计** -- `stats()`、`total_time()`、`is_running()` 内省方法

## 使用方式

```bash
cp profiler/profiler.py your_project/
```

## 使用示例

### 基本分析

```python
from profiler import Profiler

with Profiler() as p:
    do_work()

print(p.output_text())
p.output_html(file="report.html")
```

### 异步分析

```python
from profiler import Profiler

async with Profiler(async_mode=True) as p:
    await do_async_work()

html = p.output_html()
```

### 跟踪分析器

```python
from profiler import TracingProfiler

with TracingProfiler() as p:
    do_work()

for trace in p.traces():
    print(trace)

p.output_html(file="traces.html", style="flamegraph")
```
