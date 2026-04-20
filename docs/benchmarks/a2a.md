# A2A 性能测试

zerodep A2A 与 [`a2a-protocol`](https://pypi.org/project/a2a-protocol/) 的同类对比性能测试。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** a2a-protocol 0.1.0
    - **最后更新:** 2026-04-20

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
| 小型 | 1.9 μs | 4.2 μs | **快 2.2x** |
| 中型 | 36.3 μs | 93.0 μs | **快 2.6x** |
| 大型 | 917.0 μs | 2,236.7 μs | **快 2.4x** |

## 反序列化性能（均值）

dict → 对象重建。zerodep 使用 `from_dict()` 进行枚举解析和类型分发；参考库直接构造 dataclass（无 `from_dict` API）。

| 数据规模 | zerodep | a2a-protocol | 倍数 |
|----------|---------|--------------|------|
| 小型 | 1.5 μs | 0.9 μs | 慢 1.7x |
| 中型 | 27.7 μs | 25.9 μs | 慢 1.1x |
| 大型 | 795.2 μs | 685.5 μs | 慢 1.2x |

!!! note "反序列化方法说明"
    参考库（`a2a-protocol`）使用普通 dataclass，没有 `from_dict()` 方法。测试中直接从已知字段构造对象，而非从任意 dict 解析。zerodep 的 `from_dict()` 执行完整的 dict → 对象重建，包括枚举解析和类型分发，是更丰富的操作。

## JSON 往返性能（均值）

完整循环：对象 → dict → JSON 字符串 → dict → 对象。

| 数据规模 | zerodep | a2a-protocol | 倍数 |
|----------|---------|--------------|------|
| 小型 | 7.9 μs | 10.9 μs | **快 1.4x** |
| 中型 | 114.0 μs | 167.4 μs | **快 1.5x** |
| 大型 | 2,912.0 μs | 4,085.4 μs | **快 1.4x** |

!!! note "往返方法说明"
    zerodep 执行完整的 `to_dict → json.dumps → json.loads → from_dict` 重建。参考库执行 `asdict → json.dumps → json.loads` 但不进行对象重建（无 `from_dict`）。尽管多了对象重建步骤，zerodep 优化后的序列化使得整体往返速度更快。

## 要点总结

- **序列化快 2.2-2.6 倍** -- zerodep 优化后的 `to_dict()` 现已大幅超越参考库的 `dataclasses.asdict()`。改进源于避免了 `dataclasses.asdict()` 的递归深拷贝开销。此前慢 1.4-2.1 倍，现在**快 2.2-2.6 倍**。
- **反序列化慢 1.1-1.7 倍** -- zerodep 的 `from_dict()` 执行完整的 dict 到对象重建，包括枚举解析和类型分发。参考库直接构造 dataclass，不进行解析。差距已大幅缩小（此前慢 1.8-4.1 倍），得益于优化的枚举解析和类型分发路径。
- **JSON 往返现已快 1.4-1.5 倍** -- 序列化的提升完全弥补了反序列化的开销，使 zerodep 的端到端性能更优。此前慢 1.6-1.8 倍。
- **零依赖** -- 与需要安装的参考库不同，zerodep 的 A2A 是单文件，无外部包依赖。性能现在是优势而非折中。

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
