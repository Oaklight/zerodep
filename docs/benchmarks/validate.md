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
| Simple (3 fields) | 9.9 us | 648 ns | pydantic 15x faster |
| Nested (TypedDict in TypedDict) | 15.3 us | 674 ns | pydantic 23x faster |
| Constrained (Annotated Gt/Ge/Le) | 15.5 us | 977 ns | pydantic 16x faster |
| List of 50 dicts | 18.9 us | 12.1 us | pydantic 1.6x faster |
| JSON Schema generation | 434 us | 135 us | pydantic 3.2x faster |

## Key Takeaways

- **pydantic v2 uses a Rust-compiled core** (`pydantic-core`), so raw speed is not a fair pure-Python comparison. zerodep is pure Python with zero dependencies.
- **For bulk data** (list of 50 dicts), the gap narrows to only **1.6x** -- the per-item overhead becomes dominant and pure Python scales well.
- **In absolute terms**, zerodep validates a simple 3-field TypedDict in **~10 us** -- fast enough for API request/response validation where network latency is the bottleneck.
- **JSON Schema generation** at 434 us is a one-time cost typically called at startup, not per-request.
- zerodep has **zero pip dependencies** and uses only stdlib `typing`, `dataclasses`, and `re`.

## Run It Yourself

```bash
pip install pytest pytest-benchmark pydantic
pytest validate/test_validate_benchmark.py --benchmark-only -v
```
