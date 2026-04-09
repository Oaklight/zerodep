# Protobuf 性能测试

zerodep protobuf（纯 Python）与 [`google-protobuf`](https://pypi.org/project/protobuf/)（C/upb 扩展）的同类对比性能测试。

!!! info "测试环境"
    - **平台:** x86_64 Linux
    - **Python:** 3.10.20
    - **google-protobuf:** 7.34.1（upb C 后端）
    - **工具:** pytest-benchmark 5.2.3（报告均值）

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
| 小型 | 4.86 μs | 0.094 μs | 慢 52x |
| 中型 | 60.7 μs | 0.169 μs | 慢 359x |
| 大型 | 294.0 μs | 1.29 μs | 慢 228x |

## 解码性能（均值）

| 消息规模 | zerodep | google-protobuf | 倍数 |
|----------|---------|-----------------|------|
| 小型 | 4.60 μs | 0.263 μs | 慢 17x |
| 中型 | 51.7 μs | 0.565 μs | 慢 91x |
| 大型 | 412.4 μs | 2.50 μs | 慢 165x |

## 往返性能（均值）

| 消息规模 | zerodep | google-protobuf | 倍数 |
|----------|---------|-----------------|------|
| 小型 | 9.78 μs | 0.367 μs | 慢 27x |
| 中型 | 89.4 μs | 0.769 μs | 慢 116x |
| 大型 | 722.8 μs | 3.84 μs | 慢 188x |

## 字典转换（大型消息，仅 zerodep）

| 操作 | 耗时 |
|------|------|
| `to_dict()` | 173.2 μs |
| `from_dict()` | 126.3 μs |

## 要点总结

- **google-protobuf 快 50-200 倍** -- 这是预期结果，因为它使用编译的 C/upb 后端，而 zerodep 是纯 Python 实现。差距随消息复杂度增大。
- **解码差距相对较小** -- zerodep 解码差距（17-165x）小于编码（52-359x），因为 Python 开销在字段解析中分布更均匀。
- **zerodep 面向不同的使用场景** -- 其核心优势是零依赖、无 `protoc`、无 `.proto` 文件、无 C 扩展、单文件即用。适用于：
    - 配置和元数据交换（低频操作）
    - CLI 工具、脚本和原型开发
    - 无法使用 C 扩展的环境
    - 需要 proto3 线格式兼容但不想引入构建工具链的项目
- **小型消息约 5 μs** -- 在中等吞吐量下（200K ops/s）仍足够处理每请求元数据或 RPC 头部。
- **字典转换无 google 等价物** -- `to_dict()` / `from_dict()` 提供 JSON 友好的序列化，无需 MessageToDict 开销。

## 自行运行

```bash
pip install pytest pytest-benchmark protobuf
pytest protobuf/test_protobuf_benchmark.py --benchmark-only -v
```
