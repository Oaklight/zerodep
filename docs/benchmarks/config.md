# Config Benchmark

Apple-to-apple performance comparison between zerodep config and [`python-decouple`](https://pypi.org/project/python-decouple/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **Tool:** pytest-benchmark 5.2.3 (median values reported)

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `config.py` | stdlib-only unified config loader |
| **python-decouple** | *(reference)* | Popular 12-factor config library |

## Tests Performed

| Test | Description |
|------|-------------|
| Env Lookup | Single key lookup from `os.environ` |
| Dotenv Lookup | Key lookup from pre-loaded `.env` file (50 entries) |
| Cast Int | Env lookup + `cast=int` |
| Cast Bool | Env lookup + `cast=bool` |
| CSV | Env lookup + `cast=Csv()` |

## Performance Comparison (Median)

| Test | zerodep | python-decouple | Speedup |
|------|---------|-----------------|---------|
| Env Lookup | 657 ns | 977 ns | **1.5x faster** |
| Dotenv Lookup | 650 ns | 938 ns | **1.4x faster** |
| Cast Int | 788 ns | 1,223 ns | **1.6x faster** |
| Cast Bool | 869 ns | 1,437 ns | **1.7x faster** |
| CSV | 1,816 ns | 9,509 ns | **5.2x faster** |

## Additional Benchmarks (zerodep only)

| Test | Median | Description |
|------|--------|-------------|
| Nested JSON Lookup | 1,177 ns | Lookup nested key from JSON config file |
| Config Init (env only) | 319 ns | Construct `Config()` without file loading |
| Config Init (with JSON) | 19,360 ns | Construct `Config()` with JSON config file |
| Config Init (with .env) | 95,706 ns | Construct `Config()` with .env file (50 entries) |

## Key Takeaways

- **Consistently faster** -- zerodep config is 1.4x-5.2x faster than python-decouple across all comparable operations.
- **CSV parsing advantage** -- the largest speedup (5.2x) is in CSV casting, where zerodep's simpler implementation avoids python-decouple's overhead.
- **Lightweight init** -- constructing a `Config` with no file loading costs only ~319 ns; JSON config loading adds ~19 us, .env loading ~96 us.
- **Extra features at no cost** -- zerodep adds config file support (JSON/YAML/TOML/INI), nested keys, and prefix support while maintaining better performance.

## Run It Yourself

```bash
pip install pytest pytest-benchmark python-decouple
pytest config/test_config_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/config.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
