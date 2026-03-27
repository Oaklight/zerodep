# 表格格式化

零依赖的表格格式化工具，支持多种输出样式 —— 仅使用标准库，支持 Python 3.10+。

## 概述

Tabulate 模块将表格数据格式化为美观的文本表格。支持 7 种输出格式、灵活的表头模式、列对齐、数字格式化和 CJK 宽字符感知 —— 全部无需任何第三方依赖。

| 文件 | 描述 | 依赖 |
|------|------|------|
| `tabulate.py` | 纯 Python 实现 | 无（仅标准库：`re`、`math`、`unicodedata`、`dataclasses`） |

## 在你的项目中使用

只需将单个 `.py` 文件复制到你的项目中：

```bash
cp tabulate/tabulate.py your_project/
```

然后直接导入：

```python
from tabulate import tabulate
```

## 使用示例

### 基本表格

```python
from tabulate import tabulate

data = [["Alice", 24], ["Bob", 30]]
print(tabulate(data, headers=["Name", "Age"]))
# Name      Age
# ------  -----
# Alice      24
# Bob        30
```

### Grid 格式

```python
print(tabulate(data, headers=["Name", "Age"], tablefmt="grid"))
# +--------+-------+
# | Name   |   Age |
# +========+=======+
# | Alice  |    24 |
# | Bob    |    30 |
# +--------+-------+
```

### GitHub Markdown

```python
print(tabulate(data, headers=["Name", "Age"], tablefmt="github"))
# | Name   |   Age |
# |--------|-------|
# | Alice  |    24 |
# | Bob    |    30 |
```

### Pipe 格式（Markdown）

```python
print(tabulate(data, headers=["Name", "Age"], tablefmt="pipe"))
# | Name   |   Age |
# |:-------|------:|
# | Alice  |    24 |
# | Bob    |    30 |
```

### 不同输入形式

```python
# 字典列表
data = [{"name": "Alice", "age": 24}, {"name": "Bob", "age": 30}]
print(tabulate(data, headers="keys"))

# 列表字典
data = {"name": ["Alice", "Bob"], "age": [24, 30]}
print(tabulate(data, headers="keys"))
```

### 数字格式化

```python
data = [[3.14159, 2.71828], [1.41421, 1.73205]]
print(tabulate(data, headers=["Pi-ish", "E-ish"], floatfmt=".2f"))
# Pi-ish    E-ish
# --------  -------
# 3.14      2.72
# 1.41      1.73
```

### 行索引

```python
data = [["Alice", 24], ["Bob", 30]]
print(tabulate(data, headers=["Name", "Age"], showindex=True))
#       Name      Age
# --  ------  -----
#  0  Alice      24
#  1  Bob        30
```

### 列对齐

```python
data = [["Alice", 24], ["Bob", 30]]
print(tabulate(data, headers=["Name", "Age"], colalign=("center", "left")))
```

## 支持的格式

| 格式 | 描述 |
|------|------|
| `plain` | 无边框或分隔线 |
| `simple` | 简单表头分隔线（默认） |
| `grid` | 完整网格边框 |
| `pipe` | Markdown 管道表格（含对齐） |
| `orgtbl` | Emacs Org-mode 表格 |
| `pretty` | 居中、带边框表格 |
| `github` | GitHub 风格 Markdown |

## API 参考

### `tabulate(tabular_data, headers, tablefmt, floatfmt, numalign, stralign, missingval, showindex, colalign)`

将表格数据格式化为美观的文本表格。

**参数：**

| 名称 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `tabular_data` | `Any` | -- | 输入数据：列表的列表、字典列表、列表字典，或可迭代的可迭代对象。 |
| `headers` | `Any` | `()` | 列标题：字符串列表/元组、`"firstrow"`、`"keys"` 或空元组。 |
| `tablefmt` | `str` | `"simple"` | 输出格式：`"plain"`、`"simple"`、`"grid"`、`"pipe"`、`"orgtbl"`、`"pretty"`、`"github"`。 |
| `floatfmt` | `str` | `"g"` | 浮点值的格式字符串。 |
| `numalign` | `str` | `"decimal"` | 数字列对齐：`"right"`、`"left"`、`"center"`、`"decimal"`。 |
| `stralign` | `str` | `"left"` | 文本列对齐：`"right"`、`"left"`、`"center"`。 |
| `missingval` | `str` | `""` | `None` 值的显示字符串。 |
| `showindex` | `bool \| str \| Sequence` | `False` | 显示行索引。`True`、`"always"` 或索引值序列。 |
| `colalign` | `Sequence[str] \| None` | `None` | 按列的对齐方式覆盖。 |

**返回：** 格式化后的表格字符串。

**异常：** 当 `tablefmt` 不被识别时抛出 `ValueError`。

## 与 tabulate 的对比

| 特性 | zerodep tabulate | tabulate |
|------|-----------------|----------|
| 依赖 | 无（仅标准库） | 无 |
| 文件数 | 单文件 | 多文件包 |
| 表格格式 | 7 种（plain, simple, grid, pipe, orgtbl, pretty, github） | 20+ 种 |
| CJK 支持 | 是（通过 `WIDE_CHARS_MODE`） | 是 |
| 多行单元格 | 否 | 是 |
| 格式化速度（小） | 32.5 μs | 93.8 μs（慢 2.89x） |
| 格式化速度（大） | 3.9 ms | 13.8 ms（慢 3.56x） |

**适用场景（zerodep）：** 需要快速的表格格式化和常见输出样式，且无外部依赖。

**适用场景（tabulate）：** 需要小众输出格式（latex, rst, mediawiki）或多行单元格支持。

## 性能测试

与 `tabulate` 在小、中、大表格上进行了基准测试。

详见 [Tabulate 性能测试](../benchmarks/tabulate.md)。
