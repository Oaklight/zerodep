# jsonx Benchmark

Performance comparison between zerodep jsonx and reference libraries for both JSONC and JSONL parsing.

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **References:** commentjson 0.9.0, ndjson 0.3.1, jsonlines 4.0.0
    - **Last Updated:** 2026-06-13

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `jsonx.py` | Regex-based comment stripping + stdlib `json.loads`; batch fast-path for JSONL |
| **commentjson** | *(JSONC reference)* | Lark LALR parser + AST reconstruction + stdlib `json.loads` |
| **ndjson** | *(JSONL reference)* | Joins lines into JSON array, single `json.loads` call via custom decoder |
| **jsonlines** | *(JSONL reference)* | Per-line `json.loads` with Reader/Writer API |

---

## JSONC Performance (vs commentjson)

### Data Sizes

| Label | Description |
|-------|-------------|
| Small | 5-key object with `//` comments |
| Medium | Nested config (~40 lines) with `//`, `#` comments and trailing commas |
| Large | 100-item object with inline `//` comments and trailing commas |

### Results (Mean)

| Data Size | zerodep | commentjson | Speedup |
|-----------|---------|-------------|---------|
| Small | 15.5 µs | 1,330.0 µs | 86x faster |
| Medium | 96.4 µs | 9,300.0 µs | 97x faster |
| Large | 1,920.0 µs | 217,820.0 µs | 113x faster |

### Takeaways

- **86–113x faster** — zerodep strips comments via lightweight regex then delegates to C-accelerated `json.loads`, while commentjson builds a full Lark LALR parse tree.
- Speedup ratio improves with data size, showing lower per-element overhead.

---

## JSONL / NDJSON Performance (vs ndjson, jsonlines)

### Data Sizes

| Label | Description |
|-------|-------------|
| Small | 10 JSON objects (one per line) |
| Medium | 100 JSON objects (one per line) |
| Large | 1,000 JSON objects (one per line) |

### Results (Mean)

| Data Size | zerodep | ndjson | jsonlines | vs ndjson | vs jsonlines |
|-----------|---------|--------|-----------|-----------|--------------|
| Small (10) | 4.5 µs | 5.6 µs | 16.3 µs | 1.3x faster | 3.6x faster |
| Medium (100) | 33.6 µs | 32.8 µs | 133.4 µs | on par | 4.0x faster |
| Large (1000) | 336.7 µs | 313.0 µs | 1,380.6 µs | on par | 4.1x faster |

### Takeaways

- **On par with ndjson** — both use the same batch strategy: join lines into a JSON array and parse in a single `json.loads` call, minimizing Python-level loop overhead.
- **3.6–4.1x faster than jsonlines** — jsonlines uses a per-line `json.loads` loop with a Reader wrapper, adding significant Python overhead.
- **JSONC bonus** — unlike ndjson/jsonlines, zerodep automatically falls back to per-line JSONC processing when comments or trailing commas are present. Clean JSONL gets the fast path; commented JSONL still works.

---

## Run It Yourself

```bash
pip install pytest pytest-benchmark commentjson ndjson jsonlines
pytest jsonx/test_jsonx_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/jsonx.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
