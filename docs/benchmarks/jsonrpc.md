# JSON-RPC 性能测试

zerodep JSON-RPC 与 [`jsonrpcserver`](https://pypi.org/project/jsonrpcserver/) 的同类对比性能测试。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** jsonrpcserver 5.0.9
    - **最后更新:** 2026-04-15

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
| 成功 | 6.3 μs | 118.5 μs | **快 18.8x** |
| 错误 | 8.1 μs | 112.0 μs | **快 13.8x** |
| 方法未找到 | 7.0 μs | 92.4 μs | **快 13.2x** |
| 批量（20 个请求） | 124.9 μs | 2,400.5 μs | **快 19.2x** |

## 序列化性能（均值，仅 zerodep）

`jsonrpcserver` 不暴露模型对象，因此序列化仅测试 zerodep。

| 操作 | 耗时 |
|------|------|
| Request `to_dict()` | 300 ns |
| Response `to_dict()` | 300 ns |
| Request `from_dict()` | 700 ns |
| Response `from_dict()` | 700 ns |
| 完整 JSON 往返 | 6.4 μs |

## ID 生成（均值）

| 操作 | 耗时 |
|------|------|
| `next_id()` | 93 ns |

## 要点总结

- **分发快约 13--19 倍** -- zerodep 在所有分发场景下大幅优于 jsonrpcserver，因为它避免了 jsonrpcserver 的 schema 验证开销和函数内省机制。
- **批量处理线性扩展** -- 20 个请求的批量测试展现了相同的约 19 倍加速，证实除处理函数本身外没有额外的逐请求开销。
- **序列化亚微秒级** -- 数据类 `to_dict()` / `from_dict()` 相比完整分发极其轻量。
- **ID 生成约 93 ns** -- `itertools.count` 开销几乎为零。

## 自行运行

```bash
pip install pytest pytest-benchmark jsonrpcserver
pytest jsonrpc/test_jsonrpc_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/jsonrpc.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
