# TOON 性能测试

zerodep TOON 与 `toon_format` 的性能对比。

## 运行测试

```bash
make benchmark-toon
```

## 测试数据

| 规模 | 描述 |
|------|------|
| Small | 简单的 3 字段对象 |
| Medium | 包含 20 行表格数组的嵌套对象 |
| Large | 5 个部门 × 4 个团队 × 5 名成员（深度嵌套） |

## 测试内容

- **编码**：Python dict/list → TOON 字符串
- **解码**：TOON 字符串 → Python dict/list
- **Token 效率**：字符数对比（TOON vs JSON）

## 预期结果

zerodep 实现与 `toon_format` 性能相当或更快：

- **编码**：约 1.3-1.5 倍更快（单文件减少开销）
- **解码**：约 1.1 倍更快
- **Token 节省**：比 JSON 减少 30-60% 字符数（取决于数据结构）
