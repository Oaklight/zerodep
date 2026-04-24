# JSON Schema 展平器

零依赖的 JSON Schema 展平与清理模块 —— 仅使用标准库，支持 Python 3.10+。

## 概述

`jsonschema` 模块将包含 `$ref`、`allOf`、`anyOf`、`oneOf` 的复杂 JSON Schema 展平为简单的、LLM provider 兼容的 schema。专为 Anthropic、OpenAI 和 Google GenAI API 的工具 schema 设计。

| 文件 | 描述 | 依赖 |
|------|------|------|
| `jsonschema.py` | 纯 Python 实现 | 无（仅标准库） |

### 主要特性

- **`$ref` 解析** —— 内联所有本地 `$ref` 指针（`#/$defs/...`、`#/definitions/...`），合并兄弟键
- **`allOf` 合并** —— 深度合并多个子 schema，语义完整（属性合并、required 取并集、type 取交集、数值约束取严格值）
- **`anyOf`/`oneOf` 简化** —— nullable 检测、单变体展开、多变体回退
- **Schema 清理** —— 剥离不支持的关键字（`$schema`、`$id`、`const`、`examples` 等），校验 `required` 为 `properties` 的子集
- **分层管线** —— 每个阶段可独立调用：`resolve_refs` -> `merge_allof` -> `simplify_unions` -> `sanitize`
- **不可变** —— 所有函数深拷贝输入，不修改原始 schema

## 在你的项目中使用

将模块文件复制到你的项目中：

```bash
cp jsonschema/jsonschema.py your_project/
```

然后导入：

```python
from jsonschema import flatten_schema
```

## 使用示例

### 一键展平

```python
from jsonschema import flatten_schema

schema = {
    "type": "object",
    "properties": {
        "user": {"$ref": "#/$defs/User"},
        "role": {
            "anyOf": [
                {"type": "string", "enum": ["admin", "user"]},
                {"type": "null"},
            ],
        },
    },
    "$defs": {
        "User": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
    },
}

result = flatten_schema(schema)
# {
#     "type": "object",
#     "properties": {
#         "user": {
#             "type": "object",
#             "properties": {"name": {"type": "string"}},
#             "required": ["name"],
#         },
#         "role": {
#             "type": "string",
#             "enum": ["admin", "user"],
#             "nullable": True,
#         },
#     },
# }
```

### 分步管线

```python
from jsonschema import resolve_refs, merge_allof, simplify_unions, sanitize

# 阶段 1：解析 $ref 指针
resolved = resolve_refs(schema)

# 阶段 2：合并 allOf 子 schema
merged = merge_allof(resolved)

# 阶段 3：简化 anyOf/oneOf
simplified = simplify_unions(merged)

# 阶段 4：剥离不支持的键并校验 required
clean = sanitize(simplified)
```

### allOf 深度合并语义

```python
from jsonschema import flatten_schema

schema = {
    "allOf": [
        {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
            },
            "required": ["age"],
        },
        {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "minimum": 18, "maximum": 120},
                "name": {"type": "string"},
            },
            "required": ["name"],
        },
    ],
}

result = flatten_schema(schema)
# age 约束取严格值：minimum=18（取 max(0,18)），maximum=120（取 min(150,120)）
# required 取并集：["age", "name"]
```

### 自定义剥离键

```python
from jsonschema import flatten_schema, UNSUPPORTED_SCHEMA_KEYS

# 添加额外要剥离的键
extra = UNSUPPORTED_SCHEMA_KEYS | {"title", "description"}
result = flatten_schema(schema, strip_keys=extra)
```

## 管线架构

```
输入 Schema
    |
    v
resolve_refs()      <- 阶段 1：收集 $defs/definitions，内联 $ref，合并兄弟键
    |
    v
merge_allof()       <- 阶段 2：递归查找 allOf，深度合并所有子 schema
    |
    v
simplify_unions()   <- 阶段 3：递归查找 anyOf/oneOf，检测 nullable/单变体
    |
    v
sanitize()          <- 阶段 4：剥离不支持的键，修剪 required 数组
    |
    v
输出 Schema
```

### 深度合并语义（阶段 2）

| 键 | 策略 |
|----|------|
| `properties` | 递归合并每个子属性 |
| `required` | 取并集（去重） |
| `type` | 取交集 |
| `minimum`、`minLength`、`minItems` | 取 max（更严格） |
| `maximum`、`maxLength`、`maxItems` | 取 min（更严格） |
| `enum` | 取交集 |
| `items` | 递归深度合并 |
| 其他键 | 后者覆盖前者 |

## API 参考

### `flatten_schema(schema, *, strip_keys=None)`

一键全流程：resolve -> merge -> simplify -> sanitize。

**参数：**

| 名称 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `schema` | `dict` | -- | 要展平的 JSON Schema。 |
| `strip_keys` | `set[str] \| None` | `None` | 要剥离的键集合。默认为 `UNSUPPORTED_SCHEMA_KEYS`。 |

**返回：** `dict` —— 展平后的 schema。

### `resolve_refs(schema)`

解析本地 `$ref` 指针并内联定义。

### `merge_allof(schema)`

将 `allOf` 子 schema 深度合并为单个 schema。

### `simplify_unions(schema)`

简化 `anyOf`/`oneOf`：nullable 检测、单变体展开。

### `sanitize(schema, *, strip_keys=None)`

剥离不支持的关键字并校验 `required` 为 `properties` 的子集。

### `UNSUPPORTED_SCHEMA_KEYS`

默认要剥离的 JSON Schema 关键字集合：

`$schema`、`$id`、`$comment`、`$anchor`、`$dynamicAnchor`、`$dynamicRef`、`contentEncoding`、`contentMediaType`、`contentSchema`、`deprecated`、`readOnly`、`writeOnly`、`examples`、`propertyNames`、`const`

## 与替代方案对比

| 特性 | zerodep jsonschema | allof-merge (JS) | llm-rosetta |
|------|-------------------|------------------|-------------|
| 语言 | Python | JavaScript | Python |
| 依赖 | 无（标准库） | json-crawl | httpx、pydantic |
| `$ref` 解析 | 所有上下文 | 仅 allOf 内部 | 基础 |
| `allOf` 深度合并 | 完整语义 | 完整语义 | 仅单元素 |
| `anyOf`/`oneOf` 简化 | 是 | 否 | 浅层（dict.update） |
| Schema 清理 | 是 | 否 | 是 |
| `required` 校验 | 是 | 否 | 否 |
| 独立使用 | 是（单文件） | npm 包 | 网关组件 |

**适用场景（zerodep）：** 需要在 Python 中进行 JSON Schema 展平且不想引入任何依赖，尤其适用于 LLM 工具 schema。

**适用场景（allof-merge）：** 在 Node.js 环境下工作，只需要 `$ref` + `allOf` 解析。

## 性能测试

与 `allof-merge`（JavaScript）的五级复杂度对比性能测试。

详见 [JSON Schema 性能测试](../benchmarks/jsonschema.md)。
