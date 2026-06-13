# jsonx 性能测试

zerodep jsonx 与参考库在 JSONC 和 JSONL 解析上的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** commentjson 0.9.0、ndjson 0.3.1、jsonlines 4.0.0
    - **最后更新:** 2026-06-13

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `jsonx.py` | 基于正则的注释/尾逗号剥离 + 标准库 `json.loads`；JSONL 批量快速路径 |
| **commentjson** | *（JSONC 参考库）* | Lark LALR 解析器 + AST 重建 + 标准库 `json.loads` |
| **ndjson** | *（JSONL 参考库）* | 将所有行拼接为 JSON 数组，通过自定义解码器单次 `json.loads` 调用 |
| **jsonlines** | *（JSONL 参考库）* | 逐行 `json.loads`，Reader/Writer API |

---

## JSONC 性能（vs commentjson）

### 测试数据规模

| 规模 | 说明 |
|------|------|
| 小型 | 包含 `//` 注释的 5 个键的对象 |
| 中型 | 嵌套配置（约 40 行），含 `//`、`#` 注释和尾逗号 |
| 大型 | 包含行内 `//` 注释和尾逗号的 100 个条目的对象 |

### 结果（均值）

| 测试项 | zerodep | commentjson | 倍数 |
|--------|---------|-------------|------|
| 小型 | 15.5 µs | 1,330.0 µs | 快 86x |
| 中型 | 96.4 µs | 9,300.0 µs | 快 97x |
| 大型 | 1,920.0 µs | 217,820.0 µs | 快 113x |

### 要点

- 比 commentjson 快 **86–113 倍**——zerodep 用正则剥离注释后直接委托给 C 加速的 `json.loads`，而 commentjson 需要构建完整的 Lark LALR 解析树。
- 数据量越大加速比越高，说明正则方案的单元素开销更低。

---

## JSONL / NDJSON 性能（vs ndjson、jsonlines）

### 测试数据规模

| 规模 | 说明 |
|------|------|
| 小型 | 10 个 JSON 对象（每行一个） |
| 中型 | 100 个 JSON 对象（每行一个） |
| 大型 | 1,000 个 JSON 对象（每行一个） |

### 结果（均值）

| 测试项 | zerodep | ndjson | jsonlines | vs ndjson | vs jsonlines |
|--------|---------|--------|-----------|-----------|--------------|
| 小型 (10) | 4.5 µs | 5.6 µs | 16.3 µs | 快 1.3x | 快 3.6x |
| 中型 (100) | 33.6 µs | 32.8 µs | 133.4 µs | 持平 | 快 4.0x |
| 大型 (1000) | 336.7 µs | 313.0 µs | 1,380.6 µs | 持平 | 快 4.1x |

### 要点

- **与 ndjson 持平**——两者都使用相同的批量策略：将所有行拼接为 JSON 数组，通过单次 `json.loads` 调用完成解析，最大限度减少 Python 层循环开销。
- **比 jsonlines 快 3.6–4.1 倍**——jsonlines 使用逐行 `json.loads` 循环配合 Reader 封装，Python 层开销显著。
- **JSONC 附加能力**——与 ndjson/jsonlines 不同，zerodep 在遇到注释或尾逗号时自动降级为逐行 JSONC 处理。干净 JSONL 走快速路径；带注释的 JSONL 同样可用。

---

## 自行运行

```bash
pip install pytest pytest-benchmark commentjson ndjson jsonlines
pytest jsonx/test_jsonx_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/jsonx.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
