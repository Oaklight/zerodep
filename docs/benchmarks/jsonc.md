# JSONC 性能测试

zerodep JSONC 与 `commentjson` 的性能对比。

## 运行基准测试

```bash
make benchmark-jsonc
```

## 测试数据

| 规模 | 描述 |
|------|------|
| Small | 5 个键的对象，含 `//` 注释 |
| Medium | 嵌套配置（~40 行），含 `//`、`#` 注释和尾逗号 |
| Large | 100 个条目的对象，含行内 `//` 注释和尾逗号 |

## 实现说明

- **zerodep**：基于正则的注释/尾逗号剥离 + 标准库 `json.loads`
- **commentjson**：Lark LALR 解析器 + AST 重建 + 标准库 `json.loads`

正则方案避免了构建完整解析树的开销，对典型 JSONC 文件来说明显更快。两种实现最终都委托给 C 加速的 `json.loads` 完成实际的 JSON 解析。
