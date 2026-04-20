# Readability 性能测试

zerodep readability、[`readability-lxml`](https://pypi.org/project/readability-lxml/) 和 [Mozilla Readability.js](https://github.com/mozilla/readability) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Node.js:** 22（用于 Mozilla Readability.js）
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **参考库:** readability-lxml 0.8.4.1、@mozilla/readability + jsdom
    - **最后更新:** 2026-04-21

## 实现

| 实现 | 文件/包 | 描述 |
|------|---------|------|
| **zerodep** | `readability.py` + `soup.py` | 仅标准库的正文提取器 |
| **readability-lxml** | *（参考）* | 基于 lxml 的 Python readability 移植版 |
| **Mozilla Readability.js** | *（参考）* | 原始 JS 参考实现 |

## 测试数据

基准测试使用 Mozilla Readability.js 测试套件中的真实网页，以及用于受控缩放测试的合成 Fixture：

| 级别 | Fixture | 描述 |
|------|---------|------|
| 小型 | 001 | 简单文章页面（~2 KB） |
| 中型 | bbc-1 | BBC 新闻文章（~25 KB） |
| 大型 | wikipedia | 维基百科文章（~16 KB） |
| 合成小型 | generated | 合成文章（~1 KB，受控结构） |
| 合成中型 | generated | 合成文章（~5 KB，受控结构） |
| 合成大型 | generated | 合成文章（~20 KB，受控结构） |

## 性能对比：zerodep vs readability-lxml

| Fixture | zerodep | readability-lxml | 比率 |
|---------|---------|------------------|------|
| 小型 (001) | 276.1 μs | 680.3 μs | **快 2.5x** |
| 中型 (bbc-1) | 2.59 ms | 3.19 ms | **快 1.2x** |
| 大型 (wikipedia) | 33.85 ms | 28.52 ms | 慢 1.2x |
| 合成小型 | 458.7 μs | 757.7 μs | **快 1.7x** |
| 合成中型 | 1.16 ms | 2.40 ms | **快 2.1x** |
| 合成大型 | 5.69 ms | 13.08 ms | **快 2.3x** |

## 性能对比：zerodep vs Mozilla Readability.js

所有三种实现现已通过 pytest-benchmark 在同一 CI 运行中进行基准测试。Mozilla Readability.js 通过 Node.js 子进程调用。

| Fixture | zerodep | Mozilla JS | 比率 |
|---------|---------|------------|------|
| 小型 (001) | 276.1 μs | 5.59 ms | **快 20x** |
| 中型 (bbc-1) | 2.59 ms | 8.21 ms | **快 3.2x** |
| 大型 (wikipedia) | 33.85 ms | 423 ms | **快 12.5x** |
| 合成小型 | 458.7 μs | 8.10 ms | **快 17.7x** |
| 合成中型 | 1.16 ms | 13.50 ms | **快 11.6x** |
| 合成大型 | 5.69 ms | 28.95 ms | **快 5.1x** |

## 关键结论

- **zerodep 在小型和合成页面上优势显著** —— 在小型真实页面上**快 2.5 倍**，在所有合成数据上**快 1.7-2.3 倍**（vs readability-lxml）。优化后的评分和树遍历算法在结构较规范的 HTML 上表现出色。
- **readability-lxml 在大型复杂页面上仍有优势** —— lxml 的 C 解析器在维基百科等复杂 HTML 上依然占优（慢 1.2 倍）。
- **大幅超越 Mozilla Readability.js** —— zerodep 在所有 Fixture 上比原始 JS 参考实现**快 3.2-20 倍**。JS 实现的 jsdom DOM 构建带来了很大的开销。
- **zerodep 元数据更丰富** —— JSON-LD 提取、RTL 支持和 OpenGraph 元数据是 readability-lxml 所不具备的
- **零 pip 依赖** —— zerodep 仅需标准库，而 readability-lxml 依赖 lxml 和 cssselect

## 自行运行

```bash
# 全部基准测试（zerodep vs readability-lxml vs Mozilla JS，需要 Node.js）
pip install pytest pytest-benchmark readability-lxml
cd readability && npm install
pytest readability/test_readability_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/readability.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发布时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
