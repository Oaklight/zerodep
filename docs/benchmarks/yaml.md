# YAML Benchmark

Apple-to-apple performance comparison between zerodep YAML and [`PyYAML`](https://pypi.org/project/PyYAML/).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.10.20
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)

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
| Small | 11.2 us | 118.2 us | 10.6x faster |
| Medium | 64.2 us | 685.3 us | 10.7x faster |
| Large | 1,403.9 us | 14,576.1 us | 10.4x faster |

## Dump Performance (Mean)

| Data Size | zerodep | PyYAML | Speedup |
|-----------|---------|--------|---------|
| Small | 23.8 us | 188.5 us | 7.9x faster |
| Medium | 170.8 us | 1,234.1 us | 7.2x faster |
| Large | 3,901.1 us | 27,279.1 us | 7.0x faster |

## Key Takeaways

- **Load is ~10x faster** -- zerodep consistently outperforms PyYAML by over 10x across all data sizes for parsing.
- **Dump is ~7x faster** -- serialization is 7-8x faster, with the gap slightly narrowing at larger sizes.
- **Pure Python, yet faster** -- zerodep achieves this speedup despite being pure Python by targeting a common YAML subset without the full spec overhead of PyYAML's scanner/parser/composer pipeline.
- **Zero pip dependencies** -- unlike PyYAML, zerodep uses only the standard library.

## Run It Yourself

```bash
pip install pytest pytest-benchmark pyyaml
pytest yaml/test_yaml_benchmark.py --benchmark-only -v
```
