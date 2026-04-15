# JSONC 性能测试

zerodep JSONC 与 [`commentjson`](https://pypi.org/project/commentjson/) 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** commentjson 0.9.0
    - **最后更新:** 2026-04-15

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `jsonc.py` | 基于正则的注释/尾逗号剥离 + 标准库 `json.loads` |
| **commentjson** | *（参考库）* | Lark LALR 解析器 + AST 重建 + 标准库 `json.loads` |

## 性能对比（均值）

| 测试项 | zerodep | commentjson | 倍数 |
|--------|---------|-------------|------|
| 小型 | 14.6 μs | 1,150.8 μs | 快 79x |
| 中型 | 91.5 μs | 8,466.3 μs | 快 93x |
| 大型 | 1,809.7 μs | 218,981.4 μs | 快 121x |

## 要点总结

- zerodep 比 commentjson 快 **79--121 倍**，数据量越大优势越明显。
- **正则方案**避免了构建完整解析树的开销——zerodep 用正则剥离注释和尾逗号后，直接委托给 C 加速的标准库 `json.loads` 完成解析。
- **commentjson** 使用 Lark LALR 解析器构建 AST 后重建 JSON，开销远高于正则预处理。
- zerodep **无需任何 pip 依赖**——仅使用标准库 `re` 和 `json`。

## 自行运行

```bash
pip install pytest pytest-benchmark commentjson
pytest jsonc/test_jsonc_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/jsonc.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
