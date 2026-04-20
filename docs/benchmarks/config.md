# Config Benchmark

Apple-to-apple performance comparison between zerodep config and [`python-decouple`](https://pypi.org/project/python-decouple/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** python-decouple 3.8
    - **Last Updated:** 2026-04-21

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

## Performance Comparison (Mean)

| Test | zerodep | python-decouple | Speedup |
|------|---------|-----------------|---------|
| Env Lookup | 0.9 μs | 1.7 μs | **1.9x faster** |
| Dotenv Lookup | 0.7 μs | 1.6 μs | **2.2x faster** |
| Cast Int | 1.2 μs | 2.2 μs | **1.8x faster** |
| Cast Bool | 1.3 μs | 2.5 μs | **1.9x faster** |
| CSV | 2.7 μs | 12.3 μs | **4.6x faster** |

## Additional Benchmarks (zerodep only)

| Test | Mean | Description |
|------|------|-------------|
| Nested JSON Lookup | 1.7 μs | Lookup nested key from JSON config file |
| Config Init (env only) | 0.5 μs | Construct `Config()` without file loading |
| Config Init (with JSON) | 38.9 μs | Construct `Config()` with JSON config file |
| Config Init (with .env) | 759.8 μs | Construct `Config()` with .env file (50 entries) |

## Key Takeaways

- **Consistently faster** -- zerodep config is 1.8x-4.6x faster than python-decouple across all comparable operations.
- **CSV parsing advantage** -- the largest speedup (4.6x) is in CSV casting, where zerodep's simpler implementation avoids python-decouple's overhead.
- **Lightweight init** -- constructing a `Config` with no file loading costs only ~0.5 μs; JSON config loading adds ~39 μs, .env loading ~760 μs.
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
