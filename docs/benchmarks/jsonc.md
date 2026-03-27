# JSONC 性能测试

zerodep JSONC 与 [`commentjson`](https://pypi.org/project/commentjson/) 的性能对比。

!!! info "测试环境"
    - **平台:** x86_64 Linux
    - **Python:** 3.10.20
    - **工具:** pytest-benchmark 5.2.3（报告均值）

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `jsonc.py` | 基于正则的注释/尾逗号剥离 + 标准库 `json.loads` |
| **commentjson** | *（参考库）* | Lark LALR 解析器 + AST 重建 + 标准库 `json.loads` |

## 性能对比（均值）

| 测试项 | zerodep | commentjson | 倍数 |
|--------|---------|-------------|------|
| 小型 | 8.7 μs | 781.6 μs | 快 90x |
| 中型 | 52.3 μs | 5,859.0 μs | 快 112x |
| 大型 | 1,068.7 μs | 128,453.0 μs | 快 120x |

## 要点总结

- zerodep 比 commentjson 快 **90-120 倍**，数据量越大优势越明显。
- **正则方案**避免了构建完整解析树的开销——zerodep 用正则剥离注释和尾逗号后，直接委托给 C 加速的标准库 `json.loads` 完成解析。
- **commentjson** 使用 Lark LALR 解析器构建 AST 后重建 JSON，开销远高于正则预处理。
- zerodep **无需任何 pip 依赖**——仅使用标准库 `re` 和 `json`。

## 自行运行

```bash
pip install pytest pytest-benchmark commentjson
pytest jsonc/test_jsonc_benchmark.py --benchmark-only -v
```
