# Soup 性能测试

zerodep soup 与 [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/) 的性能对比。

!!! info "测试环境"
    - **平台:** x86_64 Linux
    - **Python:** 3.10.20
    - **工具:** pytest-benchmark 5.2.3（报告均值）

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
| Small | 149.2 μs | 446.2 μs | 快 2.99x |
| Medium | 1,236.6 μs | 3,683.9 μs | 快 2.98x |
| Large | 12,662.5 μs | 37,061.8 μs | 快 2.93x |

## 要点总结

- **全规模快约 3 倍** —— zerodep 直接从 `html.parser` 构建最小化 DOM 树，无需 BeautifulSoup 的抽象层（NavigableString、PageElement 层级、soupsieve 集成）。
- **加速比稳定** —— 2.9-3.0x 的优势在不同文档复杂度下保持一致，表明开销来自每个元素而非每个文档。
- **无需任何 pip 依赖** —— zerodep 仅使用标准库 `re` 和 `html.parser`。BeautifulSoup 需要 `soupsieve`，可选 `lxml` 或 `html5lib`。

## 自行运行

```bash
pip install pytest pytest-benchmark beautifulsoup4
pytest soup/test_soup_benchmark.py --benchmark-only -v
```
