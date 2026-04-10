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
| 简单验证（3 字段） | 9.9 us | 648 ns | pydantic 快 15x |
| 嵌套验证（TypedDict 套 TypedDict） | 15.3 us | 674 ns | pydantic 快 23x |
| 约束验证（Annotated Gt/Ge/Le） | 15.5 us | 977 ns | pydantic 快 16x |
| 列表验证（50 个 dict） | 18.9 us | 12.1 us | pydantic 快 1.6x |
| JSON Schema 生成 | 434 us | 135 us | pydantic 快 3.2x |

## 要点总结

- **pydantic v2 使用 Rust 编译核心**（`pydantic-core`），因此原始速度对比并不公平。zerodep 是纯 Python 实现，零依赖。
- **批量数据**（50 个 dict 列表）场景下差距缩小至仅 **1.6 倍**——逐项开销占主导时，纯 Python 扩展性表现良好。
- **绝对性能**方面，zerodep 验证一个简单 3 字段 TypedDict 仅需 **~10 us**——对于网络延迟是瓶颈的 API 请求/响应验证完全足够。
- **JSON Schema 生成**的 434 us 是一次性启动成本，非每次请求。
- zerodep **无需任何 pip 依赖**——仅使用标准库 `typing`、`dataclasses`、`re`。

!!! tip "v0.4.2 缓存优化"
    从 v0.4.2 起，`_typeddict_fields()`、`_dataclass_fields()` 和 `_find_discriminator()` 使用 `@functools.lru_cache(maxsize=None)` 缓存，消除了对相同类型重复验证时的冗余 `get_type_hints()` 调用。对于复杂嵌套 TypedDict 结构（同一类型被多次解析），性能提升 **8-10 倍**。上述性能数据采集于此优化之前，嵌套/重复类型验证的实际吞吐量将显著更高。

## 自行运行

```bash
pip install pytest pytest-benchmark pydantic
pytest validate/test_validate_benchmark.py --benchmark-only -v
```
