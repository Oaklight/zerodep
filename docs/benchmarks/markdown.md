# Markdown 性能测试

zerodep Markdown 实现与 [`mistune`](https://pypi.org/project/mistune/) 的同条件性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** mistune 3.2.0
    - **最后更新:** 2026-04-21

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `markdown.py` | 仅标准库的 Markdown → HTML 渲染器 |
| **mistune** | *（参考库）* | 流行的 Markdown 解析库 |

## 测试数据大小

| 标签 | 说明 |
|------|------|
| 小 | 2 行：一个带粗体的标题，一个带强调和代码的段落 |
| 中 | ~15 个块：标题、段落、代码块、块引用、列表、表格、分隔线 |
| 大 | 50 个重复段落，每段包含标题、段落、代码块、引用和列表 |

## 性能对比（均值）

| 测试 | zerodep | mistune | 比率 |
|------|---------|---------|------|
| 小 | 51.4 us | 70.5 us | **快 1.4 倍** |
| 中 | 357.8 us | 694.5 us | **快 1.9 倍** |
| 大 | 5,740.0 us | 9,790.0 us | **快 1.7 倍** |

## 要点总结

- **持续更快** —— zerodep 的 Markdown 渲染器在所有文档规模下均比 mistune **快 1.4--1.9 倍**。
- **线性增长** —— 两种实现都随文档大小线性增长，符合预期。
- **更简单的架构** —— zerodep 跳过中间 AST 直接拼接 HTML，这是性能优势的重要来源。代价是仅支持 HTML 输出，且难以通过插件或替代渲染器进行扩展。
- **输出兼容** —— zerodep 对所有支持的 Markdown 特性生成与 `mistune.html()` 完全一致的 HTML 输出（82 个正确性测试全部精确匹配通过）。

## 自行运行

```bash
pip install pytest pytest-benchmark mistune
pytest markdown/test_markdown_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/markdown.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
