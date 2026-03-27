# JSONC Benchmarks

Performance comparison between zerodep JSONC and `commentjson`.

## Running Benchmarks

```bash
make benchmark-jsonc
```

## Test Data

| Size | Description |
|------|-------------|
| Small | 5-key object with `//` comments |
| Medium | Nested config (~40 lines) with `//`, `#` comments and trailing commas |
| Large | 100-item object with inline `//` comments and trailing commas |

## Implementation Notes

- **zerodep**: Regex-based comment/trailing-comma stripping + stdlib `json.loads`
- **commentjson**: Lark LALR parser + AST reconstruction + stdlib `json.loads`

The regex approach avoids the overhead of building a full parse tree, making it significantly faster for typical JSONC files. Both implementations ultimately delegate to the C-accelerated `json.loads` for the actual JSON parsing.
