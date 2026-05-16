# Multipart Benchmark

Apple-to-apple performance comparison between zerodep multipart (pure Python) and [`python-multipart`](https://pypi.org/project/python-multipart/) (callback-based parser).

!!! info "Test Environment"
    - **CPU:** x86_64 Linux
    - **Python:** 3.12
    - **Tool:** pytest-benchmark 5.2.3 (mean values reported)
    - **Reference:** python-multipart 0.0.20
    - **Last Updated:** 2026-05-16

## Implementations

| Implementation | File/Package | Description |
|----------------|--------------|-------------|
| **zerodep** | `multipart.py` | stdlib-only boundary-split parser and encoder |
| **python-multipart** | *(reference)* | Callback-based streaming multipart parser |

## Payload Shapes

| Label | Description | Approx. Size |
|-------|-------------|--------------|
| Small | 3 text fields | ~200 B |
| Medium | 5 text fields + 2 small files (2 KB each) | ~10 KB |
| Large | 10 text fields + 5 files (80 KB each) | ~500 KB |

## Parse Performance (Mean)

| Payload | zerodep | python-multipart | Speedup |
|---------|---------|------------------|---------|
| Small | 21.7 μs | 87.6 μs | **4.0x faster** |
| Medium | 63.0 μs | 239.9 μs | **3.8x faster** |
| Large | 463.4 μs | 645.0 μs | **1.4x faster** |

## Encode Performance (Mean, zerodep only)

python-multipart does not provide an encoder, so these are zerodep-only measurements.

| Payload | zerodep |
|---------|---------|
| Small | 4.0 μs |
| Medium | 7.8 μs |
| Large | 38.8 μs |

## Round-Trip Performance (Mean, zerodep only)

Encode → parse cycle.

| Payload | zerodep |
|---------|---------|
| Small | 24.2 μs |
| Medium | 73.2 μs |

## Key Takeaways

- **1.4–4.0x faster parsing** — zerodep's boundary-split algorithm outperforms python-multipart's callback-based streaming parser across all payload sizes.
- **Speedup is highest on small payloads** — per-call overhead dominates for small bodies; zerodep avoids the callback setup cost entirely.
- **Encoding is fast** — building a 500 KB multipart body takes only ~39 μs, making it negligible compared to network I/O.
- **Round-trip under 75 μs** — encode + parse for a medium payload (10 KB) completes in ~73 μs.
- **python-multipart has no encoder** — zerodep provides both parse and encode in one file; python-multipart is parse-only.
- **Benchmarks use pre-built payloads** — payload generation cost is excluded from timing.
- zerodep has **zero pip dependencies** — uses only stdlib (`re`, `base64`, `quopri`, `dataclasses`).

## Run It Yourself

```bash
pip install pytest pytest-benchmark python-multipart
pytest multipart/test_multipart_benchmark.py --benchmark-only -v
```

---

## Latest CI Results

<iframe
  src="https://oaklight.github.io/zerodep/dev/bench/modules/multipart.html"
  width="100%" height="600" frameborder="0"
  style="border: 1px solid #dee2e6; border-radius: 8px;">
</iframe>

> Updated automatically on each release via [Benchmark CI](https://github.com/Oaklight/zerodep/actions/workflows/benchmark.yml).
