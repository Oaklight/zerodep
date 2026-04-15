# A2A 性能测试

zerodep A2A 与 [`a2a-protocol`](https://pypi.org/project/a2a-protocol/) 的同类对比性能测试。

!!! info "测试环境"
    - **平台:** x86_64 Linux
    - **Python:** 3.10.20
    - **工具:** pytest-benchmark 5.2.3（报告均值）

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `a2a.py` | 仅依赖标准库的 A2A 协议，自定义 `to_dict()` / `from_dict()` |
| **a2a-protocol** | *（参考库）* | 官方 A2A Python SDK，使用普通 dataclass |

## 测试数据规模

| 标签 | 说明 |
|------|------|
| 小型 | 单个 `Message`，包含 1 个文本 Part |
| 中型 | `Task`，包含 10 个 Artifact（各 3 个 Part）和 5 条历史消息 |
| 大型 | 50 个 `Task` 对象，各含 3 个 Artifact 和 4 条历史消息 |

## 序列化性能（均值）

对象 → dict 转换。zerodep 使用自定义 `to_dict()`；参考库使用 `dataclasses.asdict()`。

| 数据规模 | zerodep | a2a-protocol | 倍数 |
|----------|---------|--------------|------|
| 小型 | 5.5 us | 7.2 us | **快 1.3x** |
| 中型 | 118.6 us | 171.8 us | **快 1.4x** |
| 大型 | 2,131.6 us | 3,178.0 us | **快 1.5x** |

## 反序列化性能（均值）

dict → 对象重建。zerodep 使用 `from_dict()` 进行枚举解析和类型分发；参考库直接构造 dataclass（无 `from_dict` API）。

| 数据规模 | zerodep | a2a-protocol | 倍数 |
|----------|---------|--------------|------|
| 小型 | 2.5 us | 0.6 us | 0.24x |
| 中型 | 39.3 us | 20.5 us | 0.52x |
| 大型 | 988.6 us | 424.7 us | 0.43x |

!!! note "反序列化方法说明"
    参考库（`a2a-protocol`）使用普通 dataclass，没有 `from_dict()` 方法。测试中直接从已知字段构造对象，而非从任意 dict 解析。zerodep 的 `from_dict()` 执行完整的 dict → 对象重建，包括枚举解析和类型分发，是更丰富的操作。

## JSON 往返性能（均值）

完整循环：对象 → dict → JSON 字符串 → dict → 对象。

| 数据规模 | zerodep | a2a-protocol | 倍数 |
|----------|---------|--------------|------|
| 小型 | 11.7 us | 12.1 us | 1.0x（持平） |
| 中型 | 192.1 us | 220.7 us | **快 1.1x** |
| 大型 | 3,914.0 us | 4,006.5 us | 1.0x（持平） |

!!! note "往返方法说明"
    zerodep 执行完整的 `to_dict → json.dumps → json.loads → from_dict` 重建。参考库执行 `asdict → json.dumps → json.loads` 但不进行对象重建（无 `from_dict`）。尽管有这些额外工作，zerodep 仍持平或更快。

## 要点总结

- **序列化快 1.3-1.5 倍** -- zerodep 的自定义 `to_dict()` 避免了 `dataclasses.asdict()` 的昂贵深拷贝，在所有规模下均有稳定优势。
- **反序列化更慢但功能更强** -- zerodep 的 `from_dict()` 执行完整的 dict 到对象重建，包括枚举解析和类型分发。参考库没有对应功能 -- 仅支持直接构造。
- **JSON 往返持平** -- 序列化优势弥补了更丰富的反序列化操作，端到端性能相当。
- **零依赖** -- 与需要安装的参考库不同，zerodep 的 A2A 是单文件，无外部包依赖。

## 自行运行

```bash
pip install pytest pytest-benchmark a2a-protocol
pytest a2a/test_a2a_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/a2a.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
