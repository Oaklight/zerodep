# Validate Benchmark

Apple-to-apple performance comparison between zerodep validate and [`pydantic`](https://pypi.org/project/pydantic/) v2.

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10
    - **Tool:** pytest-benchmark (mean values reported)
    - **pydantic:** v2.12.5 (Rust-compiled core)

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `validate.py` | stdlib-only runtime validator (pure Python) |
| **pydantic** | *(reference)* | Popular validation library with Rust core |

## Performance Comparison (Mean)

| Test | zerodep | pydantic | Ratio |
|------|---------|----------|-------|
| Simple (3 fields) | 3.3 us | 650 ns | pydantic 5x faster |
| Nested (TypedDict in TypedDict) | 5.9 us | 710 ns | pydantic 8.4x faster |
| Constrained (Annotated Gt/Ge/Le) | 6.2 us | 980 ns | pydantic 6.3x faster |
| List of 50 dicts | 6.1 us | 11.9 us | zerodep 2x faster |
| JSON Schema generation | 132 us | 127 us | ~equal |

## Key Takeaways

- **pydantic v2 uses a Rust-compiled core** (`pydantic-core`), so raw speed is not a fair pure-Python comparison. zerodep is pure Python with zero dependencies.
- **For bulk data** (list of 50 dicts), zerodep is now **2x faster** than pydantic -- caching amortizes the per-type overhead, and the Rust-to-Python bridge overhead becomes the bottleneck for pydantic.
- **In absolute terms**, zerodep validates a simple 3-field TypedDict in **~3.3 us** -- fast enough for API request/response validation where network latency is the bottleneck.
- **JSON Schema generation** at 132 us is a one-time cost typically called at startup, not per-request. With caching, this is now on par with pydantic.
- zerodep has **zero pip dependencies** and uses only stdlib `typing`, `dataclasses`, and `re`.

!!! tip "Caching Optimization (v0.4.0+)"
    Since v0.4.0, multiple internal helpers are cached with `@functools.lru_cache(maxsize=None)`, including `_typeddict_fields()`, `_dataclass_fields()`, `_find_discriminator()`, `_is_typeddict()`, `_is_dataclass_type()`, and `_unwrap_annotated()`. This eliminates redundant `get_type_hints()` and type introspection calls on repeated validations of the same type, providing **3-5x speedup** for simple types and up to **10x** for complex nested TypedDict structures.

## Run It Yourself

```bash
pip install pytest pytest-benchmark pydantic
pytest validate/test_validate_benchmark.py --benchmark-only -v
```
