# SyncTeX 解析器

SyncTeX 反向搜索解析器 -- 零依赖，仅标准库，Python 3.10+。

## 概述

SyncTeX 模块解析 TeX 引擎（使用 `-synctex=1`）生成的 `.synctex` 和 `.synctex.gz` 文件，提供空间查询将 PDF 坐标映射回源文件和行号（反向搜索）。纯 Python 实现，无外部依赖。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `synctex.py` | 纯 Python 实现 | 无（仅标准库：`gzip`、`re`、`dataclasses`） |

### 主要特性

- **SyncTeX 解析** -- 读取纯文本 `.synctex` 和 gzip 压缩的 `.synctex.gz` 文件
- **反向搜索** -- 将 PDF 页面坐标（PDF points）映射到源文件和行号
- **路径规范化** -- 去除可配置前缀（如 Docker 构建中的 `/workspace/`）和 `./` 前缀
- **空间匹配** -- 多阶段最近盒子算法：垂直包含、水平包含、最近距离回退

## 快速开始

将单个 `.py` 文件复制到你的项目中：

```bash
cp synctex/synctex.py your_project/
```

然后直接导入：

```python
from synctex import parse_synctex, inverse_search, SyncTeXData
```

## 使用示例

### 基本反向搜索

```python
from synctex import parse_synctex, inverse_search

# 解析 SyncTeX 文件
data = parse_synctex("main.synctex.gz")

# 查找第 1 页上某点对应的源位置
result = inverse_search(data, page=1, x=150.0, y=300.0)
if result:
    print(f"{result['file']}:{result['line']}")
    # 例如 "main.tex:42"
```

### Docker / 远程构建

```python
from synctex import parse_synctex, inverse_search

# 去除 Docker 工作区路径前缀
data = parse_synctex("main.synctex.gz", strip_prefix="/workspace/")

result = inverse_search(data, page=2, x=100.0, y=200.0)
# result["file"] 将是 "chapter1.tex" 而非 "/workspace/chapter1.tex"
```

### 检查解析数据

```python
from synctex import parse_synctex

data = parse_synctex("main.synctex")

# 列出所有输入文件
for tag, path in data.inputs.items():
    print(f"  [{tag}] {path}")

# 统计每页的盒子数
for page, boxes in data.pages.items():
    print(f"  第 {page} 页：{len(boxes)} 个 hbox")

# 查看前导信息
print(f"Magnification: {data.magnification}")
print(f"Unit: {data.unit}")
```

## API 参考

### 函数

| 函数 | 说明 |
|------|------|
| `parse_synctex(path, *, strip_prefix="")` | 解析 `.synctex` 或 `.synctex.gz` 文件 |
| `inverse_search(data, page, x, y)` | 根据 PDF 坐标查找源位置 |

### 类

| 类 | 说明 |
|----|------|
| `SyncTeXData` | 解析后的 SyncTeX 数据，包含 inputs、pages、magnification、unit、offsets |
| `HBox` | 水平盒子记录，包含 tag、line、x、y、width、height、depth |

### `parse_synctex(synctex_path, *, strip_prefix="")`

解析 SyncTeX 文件并返回 `SyncTeXData` 对象。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `synctex_path` | `str` | `.synctex` 或 `.synctex.gz` 文件路径 |
| `strip_prefix` | `str` | 从输入文件路径中去除的前缀（默认：`""`） |

**返回：** `SyncTeXData`

**异常：** 文件不存在时抛出 `FileNotFoundError`。

---

### `inverse_search(data, page, x, y)`

查找 PDF 页面上某点对应的源文件和行号。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `data` | `SyncTeXData` | `parse_synctex()` 返回的解析数据 |
| `page` | `int` | 从 1 开始的页码 |
| `x` | `float` | 水平位置，PDF points（72 DPI） |
| `y` | `float` | 垂直位置，PDF points（72 DPI） |

**返回：** `{"file": str, "line": int}` 或 `None`（无匹配时）。

---

### `SyncTeXData`

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `inputs` | `dict[int, str]` | `{}` | 文件标签到路径的映射 |
| `pages` | `dict[int, list[HBox]]` | `{}` | 页码到 hbox 列表的映射 |
| `magnification` | `int` | `1000` | TeX 放大倍数 |
| `unit` | `int` | `1` | 坐标单位（scaled points） |
| `x_offset` | `int` | `0` | 水平偏移 |
| `y_offset` | `int` | `0` | 垂直偏移 |

---

### `HBox`

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `tag` | `int` | -- | 输入文件标签 |
| `line` | `int` | -- | 源代码行号 |
| `x` | `int` | -- | 左边缘（scaled points） |
| `y` | `int` | -- | 基线位置（scaled points） |
| `width` | `int` | `0` | 盒子宽度 |
| `height` | `int` | `0` | 盒子高度（基线以上） |
| `depth` | `int` | `0` | 盒子深度（基线以下） |
