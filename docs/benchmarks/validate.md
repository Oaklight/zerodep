# 验证器性能测试

zerodep validate 与 [`pydantic`](https://pypi.org/project/pydantic/) v2 的性能对比。

!!! info "测试环境"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **工具:** pytest-benchmark（报告均值）
    - **pydantic:** v2.12.5（Rust 编译核心）

## 实现对比

| 实现 | 文件/包 | 说明 |
|------|---------|------|
| **zerodep** | `validate.py` | 仅依赖标准库的运行时验证器（纯 Python） |
| **pydantic** | *（参考库）* | 使用 Rust 核心的流行验证库 |

## 性能对比（均值）

| 测试项 | zerodep | pydantic | 比率 |
|--------|---------|----------|------|
| 简单验证（3 字段） | 3.3 us | 650 ns | pydantic 快 5x |
| 嵌套验证（TypedDict 套 TypedDict） | 5.9 us | 710 ns | pydantic 快 8.4x |
| 约束验证（Annotated Gt/Ge/Le） | 6.2 us | 980 ns | pydantic 快 6.3x |
| 列表验证（50 个 dict） | 6.1 us | 11.9 us | zerodep 快 2x |
| JSON Schema 生成 | 132 us | 127 us | 基本持平 |

## 要点总结

- **pydantic v2 使用 Rust 编译核心**（`pydantic-core`），因此原始速度对比并不公平。zerodep 是纯 Python 实现，零依赖。
- **批量数据**（50 个 dict 列表）场景下，zerodep 现在**比 pydantic 快 2 倍**——缓存摊销了逐类型开销，pydantic 的 Rust-Python 桥接开销反而成为瓶颈。
- **绝对性能**方面，zerodep 验证一个简单 3 字段 TypedDict 仅需 **~3.3 us**——对于网络延迟是瓶颈的 API 请求/响应验证完全足够。
- **JSON Schema 生成**的 132 us 是一次性启动成本，非每次请求。通过缓存，现已与 pydantic 持平。
- zerodep **无需任何 pip 依赖**——仅使用标准库 `typing`、`dataclasses`、`re`。

!!! tip "缓存优化（v0.4.0+）"
    从 v0.4.0 起，多个内部辅助函数使用 `@functools.lru_cache(maxsize=None)` 缓存，包括 `_typeddict_fields()`、`_dataclass_fields()`、`_find_discriminator()`、`_is_typeddict()`、`_is_dataclass_type()` 和 `_unwrap_annotated()`。这消除了对相同类型重复验证时的冗余 `get_type_hints()` 和类型内省调用，简单类型提速 **3-5 倍**，复杂嵌套 TypedDict 结构提速可达 **10 倍**。

## 自行运行

```bash
pip install pytest pytest-benchmark pydantic
pytest validate/test_validate_benchmark.py --benchmark-only -v
```
