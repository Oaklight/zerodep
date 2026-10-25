# jsonx 扩展 JSON 解析器

零依赖的扩展 JSON 解析器，支持 JSONC（JSON with Comments）、JSONL/NDJSON（换行分隔 JSON）、单行注释（`//`、`#`）、块注释（`/* */`）和尾逗号。

> **可替代:** `commentjson`、`json5`（部分）

## 特性

- **单行注释**：`//` 和 `#` 两种风格
- **块注释**：`/* ... */`（支持多行）
- **尾逗号**：对象和数组末尾允许多余的逗号
- **JSONL/NDJSON**：换行分隔 JSON 的解析和序列化
- **直接替换**：与标准库 `json` 模块相同的 API，但有一处刻意差异——`dumps` / `dump` 默认拒绝 `NaN` 与 `Infinity`，因为它们并非合法 JSON
- **字符串安全**：引号内的注释标记不会被误处理
- **错误报告**：`JSONCDecodeError` 包含位置信息

## 快速开始

```python
from jsonx import loads, load, dumps, dump

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

将 JSONC 字符串反序列化为 Python 对象。先剥离注释和尾逗号，再委托给 `json.loads`；若文档本身即为合法 JSON，则跳过该预处理。传入 `cls` 或任一钩子（`object_hook`、`object_pairs_hook`、`parse_float`、`parse_int`、`parse_constant`）会退出快速路径，因此回调不会在试探性解析中被调用。仅接受 `str`；传入 `bytes` 会抛出 `TypeError`，请先解码。

支持 `json.loads` 的所有关键字参数（`cls`、`object_hook`、`parse_float`、`parse_int`、`parse_constant`、`object_pairs_hook`）。

### `load(fp, **kwargs)`

从文件对象反序列化 JSONC。读取流内容后传递给 `loads`。

### `dumps(obj, **kwargs)` / `dump(obj, fp, **kwargs)`

转发到 `json.dumps` / `json.dump`，但 `allow_nan` 默认为 `False`：遇到非有限浮点数会抛出
`ValueError`，而不是写成裸 `NaN` / `Infinity`——`JSON.parse`、Go 的 `encoding/json`
与 serde 都拒绝这些常量。确认使用方接受 Python 常量时，可传 `allow_nan=True`。

```python
>>> dumps({"x": float("nan")})
ValueError: Out of range float values are not JSON compliant
>>> dumps({"x": float("nan")}, allow_nan=True)
'{"x": NaN}'
```

`dumps_lines` / `dump_lines` 以同样的默认值转发给 `json.dumps`，JSONL 辅助函数行为一致。

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

| 特性 | zerodep jsonx | commentjson |
|------|--------------|-------------|
| `//` 注释 | 支持 | 支持 |
| `#` 注释 | 支持 | 支持 |
| `/* */` 注释 | 支持 | 不支持（PyPI 0.9.0） |
| 尾逗号 | 支持 | 支持 |
| JSONL/NDJSON | 支持 | 不支持 |
| 依赖 | 无（仅标准库） | `lark-parser` |
| 实现方式 | 正则 + `json.loads` | LALR 解析器 + 重建 |
| 维护状态 | 活跃 | 停止维护（2021） |
