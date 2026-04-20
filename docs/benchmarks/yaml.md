# YAML Benchmark

Apple-to-apple performance comparison between zerodep YAML and [`PyYAML`](https://pypi.org/project/PyYAML/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** PyYAML 6.0.3
    - **Last Updated:** 2026-04-21

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `yaml.py` | stdlib-only YAML subset parser/emitter |
| **PyYAML** | *(reference)* | Full YAML 1.1 spec library (C loader not used) |

## Data Sizes Tested

| Label | Description |
|-------|-------------|
| Small | Simple key-value mapping (~5 keys) |
| Medium | Nested config with lists and mappings (~30 keys) |
| Large | Large document with deeply nested structures (~200 keys) |

## Load Performance (Mean)

| Data Size | zerodep | PyYAML | Speedup |
|-----------|---------|--------|---------|
| Small | 39.9 us | 294.8 us | 7.4x faster |
| Medium | 290.3 us | 1,910.0 us | 6.6x faster |
| Large | 6,220.0 us | 43,110.0 us | 6.9x faster |

## Dump Performance (Mean)

| Data Size | zerodep | PyYAML | Speedup |
|-----------|---------|--------|---------|
| Small | 18.9 us | 175.9 us | 9.3x faster |
| Medium | 146.5 us | 988.6 us | 6.7x faster |
| Large | 2,570.0 us | 20,460.0 us | 8.0x faster |

## Key Takeaways

- **Load is ~7x faster** -- zerodep consistently outperforms PyYAML across all data sizes for parsing.
- **Dump is ~7--9x faster** -- serialization is 6.7--9.3x faster, with the largest speedup on small inputs.
- **Pure Python, yet faster** -- zerodep achieves this speedup despite being pure Python by targeting a common YAML subset without the full spec overhead of PyYAML's scanner/parser/composer pipeline.
- **Zero pip dependencies** -- unlike PyYAML, zerodep uses only the standard library.

## Run It Yourself

```bash
pip install pytest pytest-benchmark pyyaml
pytest yaml/test_yaml_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/yaml.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
