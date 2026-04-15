# ACP 性能测试

zerodep ACP 与 [`agent-client-protocol`](https://pypi.org/project/agent-client-protocol/) 的同类对比性能测试。

!!! info "测试环境"
    - **平台:** x86_64 Linux
    - **Python:** 3.10.20
    - **工具:** pytest-benchmark 5.2.3（报告均值）

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
| 小型 | 2.9 us | 0.7 us | 0.24x |
| 中型 | 43.5 us | 6.6 us | 0.15x |
| 大型 | 679.4 us | 40.6 us | 0.06x |

## 反序列化性能（均值）

dict → 对象重建。zerodep 使用 `from_raw()`；参考库使用 Pydantic 的 `model_validate()`。

| 数据规模 | zerodep | agent-client-protocol | 倍数 |
|----------|---------|----------------------|------|
| 小型 | 0.4 us | 0.8 us | **快 2.0x** |
| 中型 | 0.7 us | 30.5 us | **快 40.7x** |
| 大型 | 15.0 us | 39.5 us | **快 2.6x** |

## JSON 往返性能（均值）

完整循环：对象 → dict → JSON 字符串 → dict → 对象。

| 数据规模 | zerodep | agent-client-protocol | 倍数 |
|----------|---------|----------------------|------|
| 小型 | 6.0 us | 4.2 us | 0.69x |
| 中型 | 56.9 us | 44.2 us | 0.78x |
| 大型 | 868.7 us | 238.6 us | 0.27x |

## 要点总结

- **反序列化快 2-41 倍** -- zerodep 的 `from_raw()` 使用轻量级 dict 重建，不进行深度模式验证；Pydantic 的 `model_validate()` 执行完整的类型检查和强制转换。这使 zerodep 非常适合高吞吐量的消息接收。
- **序列化更慢** -- Pydantic v2 的 `model_dump()` 由编译的 Rust 代码支持，使其显著快于 zerodep 的纯 Python `to_dict()` 递归转换。差距随数据规模增大而扩大。
- **JSON 往返反映序列化差距** -- 由于序列化主导往返开销，参考库的 Rust 加速序列化在端到端场景中占优。
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
