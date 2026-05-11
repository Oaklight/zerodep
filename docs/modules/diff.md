# Diff 差异工具

Unified diff 解析器、补丁应用/反转和三路合并 —— 零依赖，仅使用标准库，支持 Python 3.10+。

> **可替代:** `unidiff`、`patch`

## 概述

Diff 模块提供统一差异格式的结构化解析、补丁应用/反转以及带冲突检测的三路合并。完全基于标准库 `difflib` 模块构建 —— 无需任何第三方依赖。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `diff.py` | 纯 Python 实现 | 无（仅标准库） |

模块使用 `difflib.unified_diff` 生成差异（后处理添加 `\ No newline at end of file` 标记），使用状态机解析器解析 unified diff 文本，使用基于 `difflib.SequenceMatcher` 操作码的扫描线算法进行三路合并。

## 如何在项目中使用

只需将单个 `.py` 文件复制到你的项目中：

```bash
cp diff/diff.py your_project/
```

然后直接导入：

```python
from diff import make_diff, parse_patch, apply_patch, reverse_patch, merge3
```

## API 参考

### `make_diff(a, b, ...)`

从两个文本输入生成 unified diff 字符串。

```python
def make_diff(
    a: str,
    b: str,
    filename_a: str = "a",
    filename_b: str = "b",
    context: int = 3,
) -> str
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `a` | `str` | -- | 原始文本。 |
| `b` | `str` | -- | 修改后的文本。 |
| `filename_a` | `str` | `"a"` | diff 头部中源文件的标签。 |
| `filename_b` | `str` | `"b"` | diff 头部中目标文件的标签。 |
| `context` | `int` | `3` | 每处变更周围的上下文行数。 |

**返回值：** `str` -- Unified diff 文本。无差异时返回空字符串。

**示例：**

```python
from diff import make_diff

d = make_diff("hello\nworld\n", "hello\nbrave new world\n")
print(d)
# --- a
# +++ b
# @@ -1,2 +1,2 @@
#  hello
# -world
# +brave new world
```

### `parse_patch(patch_text)`

将 unified diff 文本解析为结构化的 `Patch` 对象。

```python
def parse_patch(patch_text: str) -> Patch
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `patch_text` | `str` | -- | Unified diff 文本。 |

**返回值：** `Patch` -- 包含文件和 hunk 的结构化补丁。

**异常：** `PatchParseError` -- diff 文本格式错误时抛出。

### `apply_patch(source, patch)`

将补丁应用到源文本并返回结果。

```python
def apply_patch(source: str, patch: Patch | PatchedFile) -> str
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `source` | `str` | -- | 需要打补丁的原始文本。 |
| `patch` | `Patch` 或 `PatchedFile` | -- | 解析后的补丁或单文件补丁。 |

**返回值：** `str` -- 打补丁后的文本。

**异常：** `PatchApplyError` -- 源文本与补丁预期不匹配时抛出。

### `reverse_patch(patch)`

反转补丁，使其撤销原始变更。

```python
def reverse_patch(patch: Patch) -> Patch
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `patch` | `Patch` | -- | 需要反转的补丁。 |

**返回值：** `Patch` -- 撤销原始变更的新补丁。

### `merge3(base, ours, theirs, ...)`

执行带冲突检测的三路合并。

```python
def merge3(
    base: str,
    ours: str,
    theirs: str,
    label_ours: str = "ours",
    label_theirs: str = "theirs",
) -> MergeResult
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `base` | `str` | -- | 共同祖先文本。 |
| `ours` | `str` | -- | 我方修改版本。 |
| `theirs` | `str` | -- | 对方修改版本。 |
| `label_ours` | `str` | `"ours"` | 冲突标记中我方的标签。 |
| `label_theirs` | `str` | `"theirs"` | 冲突标记中对方的标签。 |

**返回值：** `MergeResult` -- 包含 `content`（合并文本）、`has_conflicts`（布尔值）和 `conflicts`（`ConflictRegion` 列表）。

## 数据结构

### `Patch`

一个或多个文件差异的容器。支持 `len()`、迭代和索引。

- `files: list[PatchedFile]`

### `PatchedFile`

单个文件的差异及元数据。

- `source_file: str | None` -- 源文件名（新文件时为 `"/dev/null"`）。
- `target_file: str | None` -- 目标文件名（删除时为 `"/dev/null"`）。
- `hunks: list[Hunk]`
- `is_added` / `is_deleted` -- 标识新增/删除文件的属性。

### `Hunk`

一段连续的变更区域。

- `src_start`, `src_len` -- 源区域（1-based 起始位置）。
- `tgt_start`, `tgt_len` -- 目标区域（1-based 起始位置）。
- `lines: list[tuple[str, str]]` -- `(标签, 内容)` 列表，标签为 `" "`、`"+"`  或 `"-"`。

### `MergeResult`

- `content: str` -- 合并文本（存在冲突时包含冲突标记）。
- `has_conflicts: bool`
- `conflicts: list[ConflictRegion]`

### `ConflictRegion`

- `base_start`, `base_end` -- base 中的 0-based 行范围。
- `ours: list[str]`, `theirs: list[str]` -- 双方冲突的行。

## 使用示例

### 补丁往返

```python
from diff import make_diff, parse_patch, apply_patch, reverse_patch

a = "line1\nline2\nline3\n"
b = "line1\nmodified\nline3\n"

# 生成 diff
diff_text = make_diff(a, b)

# 解析并应用
patch = parse_patch(diff_text)
assert apply_patch(a, patch) == b

# 反转并应用以还原
rev = reverse_patch(patch)
assert apply_patch(b, rev) == a
```

### 三路合并

```python
from diff import merge3

base = "line1\nline2\nline3\nline4\nline5\n"
ours = "line1\nmodified\nline3\nline4\nline5\n"
theirs = "line1\nline2\nline3\nline4\nchanged\n"

result = merge3(base, ours, theirs)
assert not result.has_conflicts
print(result.content)
# line1
# modified
# line3
# line4
# changed
```

### 冲突检测

```python
from diff import merge3

base = "line1\nline2\nline3\n"
ours = "line1\nours\nline3\n"
theirs = "line1\ntheirs\nline3\n"

result = merge3(base, ours, theirs)
assert result.has_conflicts
assert len(result.conflicts) == 1
print(result.content)
# line1
# <<<<<<< ours
# ours
# =======
# theirs
# >>>>>>> theirs
# line3
```

### 多文件补丁解析

```python
from diff import make_diff, parse_patch

d1 = make_diff("a\n", "b\n", filename_a="file1.txt", filename_b="file1.txt")
d2 = make_diff("c\n", "d\n", filename_a="file2.txt", filename_b="file2.txt")
combined = d1 + d2

patch = parse_patch(combined)
assert len(patch.files) == 2
print(patch[0].source_file)  # file1.txt
print(patch[1].source_file)  # file2.txt
```

## 异常

| 异常 | 触发条件 |
|------|----------|
| `DiffError` | 所有 diff 错误的基类。 |
| `PatchParseError` | diff 文本格式错误（包含 `line_no` 和 `detail`）。 |
| `PatchApplyError` | 源文本与补丁预期不匹配（包含 `hunk_index`、`expected`、`actual`）。 |

## 不支持的特性

- 二进制差异处理
- Git 扩展 diff 头（`index`、`mode`、`rename from/to`）
- 模糊/偏移补丁匹配（要求精确上下文匹配）
- 合并提交的组合差异

## 注意事项

!!! info "基于 difflib 的生成"
    `make_diff()` 使用标准库的 `difflib.unified_diff` 并进行后处理以插入 `\ No newline at end of file` 标记。生成的 diff 与 `git apply` 和 `patch` 等标准工具兼容。

!!! info "严格应用"
    `apply_patch()` 要求上下文行精确匹配。与支持偏移和模糊匹配的 `git apply` 不同，本实现在上下文行不完全匹配时会抛出 `PatchApplyError`。这确保了正确性，代价是灵活性。

- **Python 版本：** 需要 Python 3.10+（使用 `X | Y` 联合类型语法）。
- **性能：** 补丁解析速度约为 `unidiff` 的 8-9 倍。
- **往返不变量：** `apply_patch(a, parse_patch(make_diff(a, b))) == b` 对所有有效输入成立。

## 性能测试

与 `unidiff` 在三种差异规模（小、中、大）下进行对比测试。

详见 [Diff 性能测试](../benchmarks/diff.md)。
