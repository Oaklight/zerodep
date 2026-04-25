# Protobuf 性能测试

zerodep protobuf（纯 Python）与 [`google-protobuf`](https://pypi.org/project/protobuf/)（C/upb 扩展）的同类对比性能测试。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** protobuf (google) 7.34.1
    - **最后更新:** 2026-04-26

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `protobuf.py` | 纯 Python proto3 编解码器，使用 dataclass 定义消息 |
| **google-protobuf** | *（参考库）* | Google 官方 protobuf 库，带 C/upb 加速 |

## 消息结构

| 标签 | 说明 |
|------|------|
| 小型 | 3 个字段：string + int32 + bool |
| 中型 | 5 个字段：uint64 + string + double + repeated[str] (4) + repeated[int32] (100) |
| 大型 | 6 个字段：uint64 + string + 50 个嵌套消息 + map[str,str] (20) + repeated[double] (100) + bool |

## 编码性能（均值）

| 消息规模 | zerodep | google-protobuf | 倍数 |
|----------|---------|-----------------|------|
| 小型 | 2.5 μs | 0.2 μs | 慢 11x |
| 中型 | 27.6 μs | 0.4 μs | 慢 67x |
| 大型 | 161.0 μs | 2.4 μs | 慢 66x |

## 解码性能（均值）

| 消息规模 | zerodep | google-protobuf | 倍数 |
|----------|---------|-----------------|------|
| 小型 | 7.3 μs | 0.5 μs | 慢 15x |
| 中型 | 61.6 μs | 1.0 μs | 慢 59x |
| 大型 | 481.8 μs | 4.8 μs | 慢 101x |

## 往返性能（均值）

| 消息规模 | zerodep | google-protobuf | 倍数 |
|----------|---------|-----------------|------|
| 小型 | 10.0 μs | 0.7 μs | 慢 14x |
| 中型 | 89.3 μs | 1.4 μs | 慢 64x |
| 大型 | 643.4 μs | 7.3 μs | 慢 88x |

## 字典转换（大型消息，仅 zerodep）

| 操作 | 耗时 |
|------|------|
| `to_dict()` | 192.6 μs |
| `from_dict()` | 244.9 μs |

## 要点总结

- **google-protobuf 快 11-101 倍** -- 这是预期结果，因为它使用编译的 C/upb 后端，而 zerodep 是纯 Python 实现。差距随消息复杂度增大。
- **解码差距相对较小** -- zerodep 解码差距（15-101x）与编码差距（11-67x）相近，编码在近期版本中得到了更积极的优化。
- **zerodep 面向不同的使用场景** -- 其核心优势是零依赖、无 `protoc`、无 `.proto` 文件、无 C 扩展、单文件即用。适用于：
    - 配置和元数据交换（低频操作）
    - CLI 工具、脚本和原型开发
    - 无法使用 C 扩展的环境
    - 需要 proto3 线格式兼容但不想引入构建工具链的项目
- **小型消息编码约 2.5 μs** -- 在高吞吐量下（约 400K ops/s）可处理每请求元数据或 RPC 头部。
- **字典转换无 google 等价物** -- `to_dict()` / `from_dict()` 提供 JSON 友好的序列化，无需 MessageToDict 开销。
- **`byte_size()` 无需序列化** -- 计算序列化消息大小而不分配 bytes，适用于协议帧长度计算和缓冲区预分配。

## 自行运行

```bash
pip install pytest pytest-benchmark protobuf
pytest protobuf/test_protobuf_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/protobuf.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
