# ACP 性能测试

zerodep ACP 与 [`agent-client-protocol`](https://pypi.org/project/agent-client-protocol/) 的同类对比性能测试。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** agent-client-protocol 0.9.0
    - **最后更新:** 2026-04-21

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `acp.py` | 仅依赖标准库的 ACP 协议，使用普通 dataclass |
| **agent-client-protocol** | *（参考库）* | 官方 ACP SDK，使用 Pydantic v2（Rust 加速） |

## 测试数据规模

| 标签 | 说明 |
|------|------|
| 小型 | 单个 `TextContent` 块 |
| 中型 | `PromptParams`（10 个内容块）+ `InitializeResult`（含 capabilities） |
| 大型 | 20 个 `ToolCallUpdate` 对象，含嵌套 locations 和 raw input/output |

## 序列化性能（均值）

对象 → dict 转换。zerodep 使用 `to_dict()`；参考库使用 Pydantic 的 `model_dump()`。

| 数据规模 | zerodep | agent-client-protocol | 倍数 |
|----------|---------|----------------------|------|
| 小型 | 4.0 μs | 1.3 μs | 慢 3.2x |
| 中型 | 62.7 μs | 12.7 μs | 慢 4.9x |
| 大型 | 526.5 μs | 73.3 μs | 慢 7.2x |

## 反序列化性能（均值）

dict → 对象重建。zerodep 使用 `from_raw()`；参考库使用 Pydantic 的 `model_validate()`。

| 数据规模 | zerodep | agent-client-protocol | 倍数 |
|----------|---------|----------------------|------|
| 小型 | 1.7 μs | 1.8 μs | 持平 |
| 中型 | 6.0 μs | 61.0 μs | **快 10.2x** |
| 大型 | 153.0 μs | 78.4 μs | 慢 2.0x |

## JSON 往返性能（均值）

完整循环：对象 → dict → JSON 字符串 → dict → 对象。

| 数据规模 | zerodep | agent-client-protocol | 倍数 |
|----------|---------|----------------------|------|
| 小型 | 10.1 μs | 7.0 μs | 慢 1.4x |
| 中型 | 90.4 μs | 84.6 μs | 慢 1.1x |
| 大型 | 941.6 μs | 397.4 μs | 慢 2.4x |

## 要点总结

- **反序列化结果不一** -- zerodep 的 `from_raw()` 在中型数据规模下快 10.2 倍，此时 Pydantic 深度模式验证的开销最为明显。小型规模下两者持平，大型规模下 zerodep 慢 2.0 倍。
- **序列化慢 3.2-7.2 倍** -- Pydantic v2 的 `model_dump()` 由编译的 Rust 代码支持，使其显著快于 zerodep 的纯 Python `to_dict()` 递归转换。差距随数据规模增大而扩大。
- **JSON 往返慢 1.1-2.4 倍** -- 中型规模下 zerodep 接近持平（慢 1.1 倍）。小型规模下 zerodep 慢 1.4 倍，大型规模下慢 2.4 倍，主要反映序列化开销。
- **不同的设计权衡** -- zerodep 优先考虑零依赖和简洁性；参考库通过编译扩展优先考虑原始吞吐量。对于大多数 ACP 用例（编辑器与智能体之间的 stdio IPC），两者都足够快 -- 瓶颈在 AI 模型，而非序列化。

## 自行运行

```bash
pip install pytest pytest-benchmark agent-client-protocol
pytest acp/test_acp_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/acp.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
