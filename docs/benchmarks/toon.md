# TOON Benchmarks

Performance comparison between zerodep TOON and `toon_format`.

## Running Benchmarks

```bash
make benchmark-toon
```

## Test Data

| Size | Description |
|------|-------------|
| Small | Simple 3-field object |
| Medium | Nested object with 20-row tabular array |
| Large | 5 departments × 4 teams × 5 members (deep nesting) |

## What is Measured

- **Encode**: Python dict/list → TOON string
- **Decode**: TOON string → Python dict/list
- **Token efficiency**: Character count comparison (TOON vs JSON)

## Expected Results

The zerodep implementation is comparable to or faster than `toon_format`:

- **Encode**: ~1.3-1.5x faster (single-file overhead reduction)
- **Decode**: ~1.1x faster
- **Token savings**: 30-60% fewer characters than JSON (data-dependent)
