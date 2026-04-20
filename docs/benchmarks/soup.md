# Soup 性能测试

zerodep soup 与 [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** beautifulsoup4 4.14.3
    - **最后更新:** 2026-04-21

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
| Small | 276.5 μs | 740.3 μs | 快 2.7x |
| Medium | 2,190.0 μs | 6,140.0 μs | 快 2.8x |
| Large | 24,580.0 μs | 63,020.0 μs | 快 2.6x |

## 序列化性能（均值）

| 数据规模 | zerodep | beautifulsoup4 | 倍数 |
|----------|---------|----------------|------|
| Small | 307.3 μs | 986.4 μs | 快 3.2x |
| Medium | 2,230.0 μs | 8,310.0 μs | 快 3.7x |
| Large | 25,290.0 μs | 83,800.0 μs | 快 3.3x |

## 树操作性能（均值）

| 数据规模 | zerodep | beautifulsoup4 | 倍数 |
|----------|---------|----------------|------|
| Small | 333.9 μs | 888.8 μs | 快 2.7x |
| Medium | 2,370.0 μs | 6,810.0 μs | 快 2.9x |
| Large | 26,780.0 μs | 67,650.0 μs | 快 2.5x |

## 要点总结

- **全规模、全操作快 2.5-3.7 倍** —— zerodep 直接从 `html.parser` 构建最小化 DOM 树，无需 BeautifulSoup 的抽象层（NavigableString、PageElement 层级、soupsieve 集成）。
- **序列化加速比最大** —— 快 3.2-3.7 倍，zerodep 的轻量节点结构在树到字符串转换时开销更小。
- **各工作负载表现一致** —— 解析（2.7-2.8x）、序列化（3.2-3.7x）和树操作（2.5-2.9x）均表现出显著优势，仅在最大文档上略有缩窄。
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
