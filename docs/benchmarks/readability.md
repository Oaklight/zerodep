# Readability 性能测试

zerodep readability、[`readability-lxml`](https://pypi.org/project/readability-lxml/) 和 [Mozilla Readability.js](https://github.com/mozilla/readability) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Node.js:** 22（用于 Mozilla Readability.js）
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **参考库:** readability-lxml 0.8.4.1、@mozilla/readability + jsdom
    - **最后更新:** 2026-04-20

## 实现

| 实现 | 文件/包 | 描述 |
|------|---------|------|
| **zerodep** | `readability.py` + `soup.py` | 仅标准库的正文提取器 |
| **readability-lxml** | *（参考）* | 基于 lxml 的 Python readability 移植版 |
| **Mozilla Readability.js** | *（参考）* | 原始 JS 参考实现 |

## 测试数据

基准测试使用 Mozilla Readability.js 测试套件中的真实网页：

| 级别 | Fixture | 描述 |
|------|---------|------|
| 小型 | 001 | 简单文章页面（~2 KB） |
| 中型 | bbc-1 | BBC 新闻文章（~25 KB） |
| 大型 | wikipedia | 维基百科文章（~16 KB） |

## Python 性能对比（zerodep vs readability-lxml）

| Fixture | zerodep | readability-lxml | 比率 |
|---------|---------|------------------|------|
| 小型 (001) | ~3 ms | ~5 ms | 快约 1.7x |
| 中型 (bbc-1) | ~30 ms | ~15 ms | 慢约 2x |
| 大型 (wikipedia) | ~25 ms | ~12 ms | 慢约 2x |

## 三方对比

`benchmark_compare.py` 脚本提供包含 Mozilla JavaScript 实现的三方对比：

```bash
python readability/benchmark_compare.py --rounds 10
```

该脚本在相同 fixture 上运行所有三种实现，并报告计时和比率。

## 关键结论

- **zerodep 在小/中型页面上具有竞争力** —— 对于典型博客文章和新闻报道，提取时间在几毫秒级别
- **readability-lxml 在大型页面上更快** —— lxml 的 C 解析器在复杂 HTML 上有优势。zerodep 使用纯 Python 的 `html.parser` 解析
- **zerodep 元数据更丰富** —— JSON-LD 提取、RTL 支持和 OpenGraph 元数据是 readability-lxml 所不具备的
- **零 pip 依赖** —— zerodep 仅需标准库，而 readability-lxml 依赖 lxml 和 cssselect

## 自行运行

```bash
# Python 基准测试（zerodep vs readability-lxml）
pip install pytest pytest-benchmark readability-lxml
pytest readability/test_readability_benchmark.py --benchmark-only -v

# 三方对比（需要 Node.js）
cd readability && npm install
python readability/benchmark_compare.py --rounds 10
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/readability.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发布时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
