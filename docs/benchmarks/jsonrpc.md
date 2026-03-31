# JSON-RPC 性能测试

zerodep JSON-RPC 与 [`jsonrpcserver`](https://pypi.org/project/jsonrpcserver/) 的同类对比性能测试。

!!! info "测试环境"
    - **平台:** x86_64 Linux
    - **Python:** 3.10.20
    - **工具:** pytest-benchmark 5.2.3（报告均值）

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `jsonrpc.py` | 仅依赖标准库的 JSON-RPC 2.0，含分发器、传输层和流式支持 |
| **jsonrpcserver** | *（参考库）* | 流行的 JSON-RPC 服务器库 |

## 测试方法

端到端分发对比：JSON 字符串 → 解析 → 分发 → 序列化 → JSON 字符串。这是最公平的比较方式，因为 `jsonrpcserver` 基于序列化的 JSON 字符串操作。

## 分发性能（均值）

| 场景 | zerodep | jsonrpcserver | 倍数 |
|------|---------|---------------|------|
| 成功 | 4.5 μs | 69.0 μs | **快 15.4x** |
| 错误 | 5.4 μs | 68.9 μs | **快 12.8x** |
| 方法未找到 | 4.7 μs | 54.3 μs | **快 11.5x** |
| 批量（20 个请求） | 85.2 μs | 1,436.8 μs | **快 16.9x** |

## 序列化性能（均值，仅 zerodep）

`jsonrpcserver` 不暴露模型对象，因此序列化仅测试 zerodep。

| 操作 | 耗时 |
|------|------|
| Request `to_dict()` | 187 ns |
| Response `to_dict()` | 143 ns |
| Request `from_dict()` | 360 ns |
| Response `from_dict()` | 414 ns |
| 完整 JSON 往返 | 3.8 μs |

## ID 生成（均值）

| 操作 | 耗时 |
|------|------|
| `next_id()` | 55 ns |

## 要点总结

- **分发快约 12-17 倍** -- zerodep 在所有分发场景下大幅优于 jsonrpcserver，因为它避免了 jsonrpcserver 的 schema 验证开销和函数内省机制。
- **批量处理线性扩展** -- 20 个请求的批量测试展现了相同的约 17 倍加速，证实除处理函数本身外没有额外的逐请求开销。
- **序列化亚微秒级** -- 数据类 `to_dict()` / `from_dict()` 相比完整分发极其轻量。
- **ID 生成约 55 ns** -- `itertools.count` 开销几乎为零。

## 自行运行

```bash
pip install pytest pytest-benchmark jsonrpcserver
pytest jsonrpc/test_jsonrpc_benchmark.py --benchmark-only -v
```
