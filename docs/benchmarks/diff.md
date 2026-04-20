# Diff 性能测试

zerodep diff 实现与 [`unidiff`](https://pypi.org/project/unidiff/) 的同条件性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** unidiff 0.7.5
    - **最后更新:** 2026-04-21

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `diff.py` | 仅标准库的 unified diff 解析器和补丁应用器 |
| **unidiff** | *（参考库）* | 流行的 unified diff 解析库 |

## 测试数据大小

| 标签 | 说明 |
|------|------|
| 小 | 5 行文件，1 处变更 |
| 中 | 50 行文件，3 处变更（3 个 hunk） |
| 大 | 1000 行文件，10 处变更（10 个 hunk） |

## 解析性能对比（均值）

| 测试 | zerodep | unidiff | 比率 |
|------|---------|---------|------|
| 小 | 10.5 μs | 21.9 μs | **快 2.1 倍** |
| 中 | 31.5 μs | 63.2 μs | **快 2.0 倍** |
| 大 | 96.5 μs | 194.2 μs | **快 2.0 倍** |

## 应用性能（仅 zerodep）

`unidiff` 不提供补丁应用功能，因此这些是 zerodep 独有的基准测试。

| 测试 | zerodep |
|------|---------|
| 小 | 2.0 μs |
| 中 | 6.5 μs |
| 大 | 55.2 μs |

## 要点总结

- **持续更快** —— zerodep 的 diff 解析器在所有差异规模下均比 unidiff **快 2.0-2.1 倍**。
- **线性增长** —— 两种实现都随差异大小线性增长，符合预期。
- **功能更多** —— zerodep 除了解析外，还提供补丁应用、反转和三路合并功能，而 unidiff 仅提供解析。
- **往返正确性** —— `apply_patch(a, parse_patch(make_diff(a, b))) == b` 已通过 13 个参数化测试用例验证，包括边缘情况（Unicode、无尾换行、Windows 换行符）。

## 自行运行

```bash
pip install pytest pytest-benchmark unidiff
pytest diff/test_diff_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/diff.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
