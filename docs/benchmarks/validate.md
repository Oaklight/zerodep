# Validate Benchmark

Apple-to-apple performance comparison between zerodep validate and [`pydantic`](https://pypi.org/project/pydantic/) v2.

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** pydantic 2.13.0
    - **Last Updated:** 2026-04-21

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `validate.py` | stdlib-only runtime validator (pure Python) |
| **pydantic** | *(reference)* | Popular validation library with Rust core |

## Performance Comparison (Mean)

| Test | zerodep | pydantic | Ratio |
|------|---------|----------|-------|
| Simple (3 fields) | 5.6 us | 1.5 us | pydantic 3.8x faster |
| Nested (TypedDict in TypedDict) | 10.0 us | 2.1 us | pydantic 4.7x faster |
| Constrained (Annotated Gt/Ge/Le) | 9.3 us | 1.5 us | pydantic 6.1x faster |
| List of 50 dicts | 220.7 us | 31.6 us | pydantic 7.0x faster |
| JSON Schema generation | 9.9 us | 200.5 us | zerodep 20.2x faster |

## Discriminated Union Scaling (v0.6.0+)

Real-world LLM agent conversations contain hundreds to thousands of messages, each with mixed content parts (text, tool\_call, tool\_result, etc.) validated against a 10-variant discriminated union. Since v0.6.0, `validate` uses a cached O(1) dispatch table for discriminated unions instead of O(variants) linear probing.

| Test | Items | Mean | Per Item |
|------|-------|------|----------|
| Flat 50 parts | 50 | 0.18 ms | 3.6 us |
| Flat 500 parts | 500 | 2.4 ms | 4.8 us |
| Flat 2000 parts | 2000 | 6.5 ms | 3.3 us |
| 20 msgs x 3 parts | 60 parts | 2.9 ms | 48 us/msg |
| 200 msgs x 5 parts | 1000 parts | 12 ms | 60 us/msg |
| 1000 msgs x 5 parts | 5000 parts | 32 ms | 32 us/msg |
| 10 tools x 5 params | 50 params | 0.33 ms | 33 us/tool |
| 50 tools x 8 params | 400 params | 2.9 ms | 58 us/tool |
| 200 tools x 10 params | 2000 params | 12 ms | 60 us/tool |

!!! success "Production Impact"
    Before v0.6.0, a 500-message agent conversation spent **917ms** (93% of total conversion time) in union validation. After the dispatch table optimization, the same workload completes in under **13ms** — a **~70x improvement**.

## Key Takeaways

- **pydantic v2 uses a Rust-compiled core** (`pydantic-core`), so raw speed is not a fair pure-Python comparison. zerodep is pure Python with zero dependencies.
- **For per-object validation**, pydantic is 4-7x faster due to its Rust core. zerodep validates a simple 3-field TypedDict in **~5.6 us** -- still fast enough for API request/response validation where network latency is the bottleneck.
- **JSON Schema generation is zerodep's strong point** -- at 9.9 us, it is **20.2x faster** than pydantic's 200.5 us. This matters for applications that generate schemas dynamically rather than at startup.
- **Discriminated unions scale linearly** with item count thanks to O(1) dispatch. 5000 content parts across 1000 messages validate in 32ms.
- zerodep has **zero pip dependencies** and uses only stdlib `typing`, `dataclasses`, and `re`.

!!! tip "Caching Optimization (v0.4.0+)"
    Since v0.4.0, multiple internal helpers are cached with `@functools.lru_cache(maxsize=None)`, including `_typeddict_fields()`, `_dataclass_fields()`, `_find_discriminator()`, `_is_typeddict()`, `_is_dataclass_type()`, and `_unwrap_annotated()`. This eliminates redundant `get_type_hints()` and type introspection calls on repeated validations of the same type, providing **3-5x speedup** for simple types and up to **10x** for complex nested TypedDict structures.

!!! tip "Dispatch Table Optimization (v0.6.0+)"
    Since v0.6.0, `_try_discriminated` builds a cached `{literal_value: TypedDict}` dispatch table per union type, reducing discriminated union validation from O(variants) to O(1) per item. This is critical for LLM API payloads with large message histories.

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
