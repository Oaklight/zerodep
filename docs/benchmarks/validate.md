# Validate Benchmark

Apple-to-apple performance comparison between zerodep validate and [`pydantic`](https://pypi.org/project/pydantic/) v2.

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** pydantic 2.13.0
    - **Last Updated:** 2026-04-15

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `validate.py` | stdlib-only runtime validator (pure Python) |
| **pydantic** | *(reference)* | Popular validation library with Rust core |

## Performance Comparison (Mean)

| Test | zerodep | pydantic | Ratio |
|------|---------|----------|-------|
| Simple (3 fields) | 4.6 us | 1.1 us | pydantic 4.3x faster |
| Nested (TypedDict in TypedDict) | 8.1 us | 1.7 us | pydantic 4.9x faster |
| Constrained (Annotated Gt/Ge/Le) | 8.0 us | 1.1 us | pydantic 7.2x faster |
| List of 50 dicts | 178.5 us | 24.4 us | pydantic 7.3x faster |
| JSON Schema generation | 8.1 us | 167.6 us | zerodep 20.6x faster |

## Key Takeaways

- **pydantic v2 uses a Rust-compiled core** (`pydantic-core`), so raw speed is not a fair pure-Python comparison. zerodep is pure Python with zero dependencies.
- **For per-object validation**, pydantic is 4-7x faster due to its Rust core. zerodep validates a simple 3-field TypedDict in **~4.6 us** -- still fast enough for API request/response validation where network latency is the bottleneck.
- **JSON Schema generation is zerodep's strong point** -- at 8.1 us, it is **20.6x faster** than pydantic's 167.6 us. This matters for applications that generate schemas dynamically rather than at startup.
- **Bulk data validation** (list of 50 dicts) shows pydantic 7.3x faster, as pydantic's Rust core handles repetitive type checking very efficiently.
- zerodep has **zero pip dependencies** and uses only stdlib `typing`, `dataclasses`, and `re`.

!!! tip "Caching Optimization (v0.4.0+)"
    Since v0.4.0, multiple internal helpers are cached with `@functools.lru_cache(maxsize=None)`, including `_typeddict_fields()`, `_dataclass_fields()`, `_find_discriminator()`, `_is_typeddict()`, `_is_dataclass_type()`, and `_unwrap_annotated()`. This eliminates redundant `get_type_hints()` and type introspection calls on repeated validations of the same type, providing **3-5x speedup** for simple types and up to **10x** for complex nested TypedDict structures.

## Run It Yourself

```bash
pip install pytest pytest-benchmark pydantic
pytest validate/test_validate_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/validate.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
