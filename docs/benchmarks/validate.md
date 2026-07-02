# 验证器性能测试

zerodep validate 与 [`pydantic`](https://pypi.org/project/pydantic/) v2 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **工具:** pytest-benchmark 5.2.3（报告均值）
    - **对标库:** pydantic 2.13.0
    - **最后更新:** 2026-04-21

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `validate.py` | 仅依赖标准库的运行时验证器（纯 Python） |
| **pydantic** | *（参考库）* | 使用 Rust 核心的流行验证库 |

## 性能对比（均值）

| 测试项 | zerodep | pydantic | 比率 |
|--------|---------|----------|------|
| 简单验证（3 字段） | 5.6 μs | 1.5 μs | pydantic 快 3.8x |
| 嵌套验证（TypedDict 套 TypedDict） | 10.0 μs | 2.1 μs | pydantic 快 4.7x |
| 约束验证（Annotated Gt/Ge/Le） | 9.3 μs | 1.5 μs | pydantic 快 6.1x |
| 列表验证（50 个 dict） | 220.7 μs | 31.6 μs | pydantic 快 7.0x |
| JSON Schema 生成 | 9.9 μs | 200.5 μs | zerodep 快 20.2x |

## 可辨识联合类型扩展性（v0.6.0+）

实际 LLM 代理对话包含数百到数千条消息，每条消息有混合内容部分（text、tool\_call、tool\_result 等），需要针对 10 变体可辨识联合类型进行验证。从 v0.6.0 起，`validate` 使用缓存的 O(1) 分发表替代 O(variants) 线性探测。

| 测试项 | 数据量 | 均值 | 单项 |
|--------|--------|------|------|
| 扁平 50 个部分 | 50 | 0.18 ms | 3.6 μs |
| 扁平 500 个部分 | 500 | 2.4 ms | 4.8 μs |
| 扁平 2000 个部分 | 2000 | 6.5 ms | 3.3 μs |
| 20 条消息 x 3 部分 | 60 部分 | 2.9 ms | 48 μs/条 |
| 200 条消息 x 5 部分 | 1000 部分 | 12 ms | 60 μs/条 |
| 1000 条消息 x 5 部分 | 5000 部分 | 32 ms | 32 μs/条 |
| 10 工具 x 5 参数 | 50 参数 | 0.33 ms | 33 μs/工具 |
| 50 工具 x 8 参数 | 400 参数 | 2.9 ms | 58 μs/工具 |
| 200 工具 x 10 参数 | 2000 参数 | 12 ms | 60 μs/工具 |

!!! success "生产环境效果"
    v0.6.0 之前，500 条消息的代理对话花费 **917ms**（总转换时间的 93%）在联合类型验证上。分发表优化后，同样的工作负载在 **13ms** 内完成——提升约 **70 倍**。

## 要点总结

- **pydantic v2 使用 Rust 编译核心**（`pydantic-core`），因此原始速度对比并不公平。zerodep 是纯 Python 实现，零依赖。
- **单对象验证**方面，pydantic 凭借 Rust 核心快 4-7 倍。zerodep 验证一个简单 3 字段 TypedDict 仅需 **~5.6 μs**——对于网络延迟是瓶颈的 API 请求/响应验证完全足够。
- **JSON Schema 生成是 zerodep 的强项** —— 仅需 9.9 μs，比 pydantic 的 200.5 μs **快 20.2 倍**。这对动态生成 Schema 而非仅启动时生成的应用尤为重要。
- **可辨识联合类型线性扩展** —— 得益于 O(1) 分发，1000 条消息中的 5000 个内容部分仅需 32ms 即可完成验证。
- zerodep **无需任何 pip 依赖** —— 仅使用标准库 `typing`、`dataclasses`、`re`。

!!! tip "缓存优化（v0.4.0+）"
    从 v0.4.0 起，多个内部辅助函数使用 `@functools.lru_cache(maxsize=None)` 缓存，包括 `_typeddict_fields()`、`_dataclass_fields()`、`_find_discriminator()`、`_is_typeddict()`、`_is_dataclass_type()` 和 `_unwrap_annotated()`。这消除了对相同类型重复验证时的冗余 `get_type_hints()` 和类型内省调用，简单类型提速 **3-5 倍**，复杂嵌套 TypedDict 结构提速可达 **10 倍**。

!!! tip "分发表优化（v0.6.0+）"
    从 v0.6.0 起，`_try_discriminated` 为每个联合类型构建缓存的 `{字面量值: TypedDict}` 分发表，将可辨识联合类型验证从 O(variants) 降至 O(1)。这对包含大量消息历史的 LLM API 负载至关重要。

## 自行运行

```bash
pip install pytest pytest-benchmark pydantic
pytest validate/test_validate_benchmark.py --benchmark-only -v
```

---

## 最新 CI 结果

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/validate.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> 每次发版时通过 [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml) 自动更新。
