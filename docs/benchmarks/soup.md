# Soup 性能测试

zerodep soup 与 [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** beautifulsoup4 4.14.3
    - **最后更新:** 2026-04-15

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `soup.py` | 单文件 HTML 解析器，仅标准库 |
| **beautifulsoup4** | *（参考库）* | 流行的 HTML/XML 解析器（使用 `html.parser` 后端） |

## 测试数据

| 规模 | 描述 |
|------|------|
| Small | 简单 HTML 页面，少量元素（约 200 字符） |
| Medium | 包含导航、列表和嵌套 div 的结构化页面（约 2 KB） |
| Large | 包含表格、表单、脚本和深层嵌套的复杂页面（约 10 KB） |

## 解析 + 查询性能（均值）

| 数据规模 | zerodep | beautifulsoup4 | 倍数 |
|----------|---------|----------------|------|
| Small | 207.6 μs | 651.0 μs | 快 3.1x |
| Medium | 1,796.2 μs | 5,482.2 μs | 快 3.1x |
| Large | 22,110.0 μs | 48,220.6 μs | 快 2.2x |

## 要点总结

- **全规模快 2.2-3.1 倍** —— zerodep 直接从 `html.parser` 构建最小化 DOM 树，无需 BeautifulSoup 的抽象层（NavigableString、PageElement 层级、soupsieve 集成）。
- **中小文档加速比最大** —— 小型和中型文档可达 3.1x 加速，大型文档缩窄至 2.2x，表明每元素开销优势在复杂页面中被树管理工作部分抵消。
- **无需任何 pip 依赖** —— zerodep 仅使用标准库 `re` 和 `html.parser`。BeautifulSoup 需要 `soupsieve`，可选 `lxml` 或 `html5lib`。

## 自行运行

```bash
pip install pytest pytest-benchmark beautifulsoup4
pytest soup/test_soup_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/soup.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
