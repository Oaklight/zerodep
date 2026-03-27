# JSONC 解析器

零依赖的 JSONC（JSON with Comments）解析器，支持单行注释（`//`、`#`）、块注释（`/* */`）和尾逗号。

## 特性

- **单行注释**：`//` 和 `#` 两种风格
- **块注释**：`/* ... */`（支持多行）
- **尾逗号**：对象和数组末尾允许多余的逗号
- **直接替换**：与标准库 `json` 模块相同的 API
- **字符串安全**：引号内的注释标记不会被误处理
- **错误报告**：`JSONCDecodeError` 包含位置信息

## 快速开始

```python
from jsonc import loads, load, dumps, dump

# 解析 JSONC 字符串
config = loads("""
{
    // 数据库设置
    "host": "localhost",
    "port": 5432,  // 默认 PostgreSQL 端口
    "options": {
        "ssl": true,
        "timeout": 30,  # 秒
    },
}
""")

# 解析 JSONC 文件
with open("config.jsonc") as f:
    config = load(f)

# 序列化（透传到 json.dumps）
text = dumps(config, indent=2)
```

## API

### `loads(text, **kwargs)`

将 JSONC 字符串反序列化为 Python 对象。先剥离注释和尾逗号，再委托给 `json.loads`。

支持 `json.loads` 的所有关键字参数（`cls`、`object_hook`、`parse_float`、`parse_int`、`parse_constant`、`object_pairs_hook`）。

### `load(fp, **kwargs)`

从文件对象反序列化 JSONC。读取流内容后传递给 `loads`。

### `dumps(obj, **kwargs)` / `dump(obj, fp, **kwargs)`

透传到 `json.dumps` / `json.dump`，保持 API 兼容。

### `JSONCDecodeError`

`json.JSONDecodeError` 的子类，在 JSONC 解析失败时抛出。

## 注释风格

```jsonc
{
    // C 风格单行注释
    "a": 1,

    # Python 风格单行注释
    "b": 2,

    /* C 风格块注释 */
    "c": 3,

    /*
     * 多行
     * 块注释
     */
    "d": 4
}
```

## 尾逗号

```jsonc
{
    "array": [1, 2, 3,],
    "nested": {
        "key": "value",
    },
}
```

## 与 commentjson 的对比

| 特性 | zerodep JSONC | commentjson |
|------|--------------|-------------|
| `//` 注释 | 支持 | 支持 |
| `#` 注释 | 支持 | 支持 |
| `/* */` 注释 | 支持 | 不支持（PyPI 0.9.0） |
| 尾逗号 | 支持 | 支持 |
| 依赖 | 无（仅标准库） | `lark-parser` |
| 实现方式 | 正则 + `json.loads` | LALR 解析器 + 重建 |
| 维护状态 | 活跃 | 停止维护（2021） |
