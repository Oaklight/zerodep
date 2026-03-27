# ANSI 终端样式

ANSI 转义码终端样式原语 -- 零依赖，仅标准库，Python 3.10+。

## 概述

轻量级模块，提供命名颜色（标准 8 色 + 高亮 8 色）、文本属性（粗体、暗淡、斜体、下划线、删除线、反色）、256 色和 24 位真彩色支持、终端能力检测以及实用工具函数。

| 文件 | 描述 | 依赖 |
|------|------|------|
| `ansi.py` | ANSI 转义码原语 | 无（仅标准库：`os`、`re`、`sys`） |

本模块作为终端视觉输出的**基础层**，为其他 zerodep 模块（`structlog`、`prompt`、`markdown` 等）提供颜色支持。

## 在项目中使用

将单个 `.py` 文件复制到你的项目中：

```bash
cp ansi/ansi.py your_project/
```

然后直接导入：

```python
from ansi import style, fg, bg, strip_ansi, visible_len
```

## 使用示例

### 快速样式

```python
from ansi import style

print(style("错误！", fg="red", bold=True))
print(style("成功", fg="green"))
print(style("警告", fg="yellow", underline=True))
print(style("提示", fg="cyan", italic=True))
print(style("高亮", fg="white", bg="blue", bold=True))
```

### 前景色

```python
from ansi import fg, RESET

# 命名颜色（8 标准 + 8 高亮）
print(fg("red") + "红色文本" + RESET)
print(fg("bright_cyan") + "高亮青色" + RESET)

# Hex 颜色（24 位真彩色）
print(fg("#ff8800") + "橙色" + RESET)

# 256 色调色板
print(fg(214) + "256 色橙色" + RESET)

# RGB 元组
print(fg((100, 200, 50)) + "自定义绿色" + RESET)
```

### 背景色

```python
from ansi import fg, bg, RESET

print(bg("yellow") + fg("black") + "黄底黑字" + RESET)
print(bg("#003366") + fg("white") + "深蓝底白字" + RESET)
print(bg(53) + fg("white") + "紫底白字" + RESET)
```

### 文本属性

```python
from ansi import style

print(style("粗体", bold=True))
print(style("暗淡", dim=True))
print(style("斜体", italic=True))
print(style("下划线", underline=True))
print(style("删除线", strikethrough=True))
print(style("反色", reverse=True))

# 组合多个属性
print(style("粗体斜体红色", fg="red", bold=True, italic=True))
```

### 终端检测

```python
from ansi import supports_color, color_depth

if supports_color():
    depth = color_depth()
    if depth >= 16_777_216:
        print("支持真彩色")
    elif depth >= 256:
        print("支持 256 色")
    else:
        print("基础 16 色")
else:
    print("不支持颜色")
```

支持 `NO_COLOR` 环境变量（参见 [no-color.org](https://no-color.org/)）和 `FORCE_COLOR` 环境变量。

### 去除 ANSI 和测量可见长度

```python
from ansi import style, strip_ansi, visible_len

colored = style("hello", fg="red", bold=True)
print(strip_ansi(colored))      # "hello"
print(visible_len(colored))     # 5
```

`visible_len()` 在文本包含颜色代码时对齐表格列特别有用。

### 光标控制

```python
from ansi import cursor_move, CURSOR_HIDE, CURSOR_SHOW, CLEAR_LINE

print(CURSOR_HIDE, end="")       # 隐藏光标
print(cursor_move(3, "up"))      # 向上移动 3 行
print(CLEAR_LINE, end="")        # 清除当前行
print(CURSOR_SHOW, end="")       # 显示光标
```

## API 参考

### 常量

#### 文本属性

| 常量 | SGR 代码 | 效果 |
|------|----------|------|
| `RESET` | `\033[0m` | 重置所有样式 |
| `BOLD` | `\033[1m` | 粗体 / 高亮 |
| `DIM` | `\033[2m` | 暗淡 |
| `ITALIC` | `\033[3m` | 斜体 |
| `UNDERLINE` | `\033[4m` | 下划线 |
| `BLINK` | `\033[5m` | 闪烁 |
| `REVERSE` | `\033[7m` | 前景/背景互换 |
| `HIDDEN` | `\033[8m` | 隐藏 |
| `STRIKETHROUGH` | `\033[9m` | 删除线 |

#### 命名颜色

`NAMED_COLORS` 字典包含标准 8 色前景 SGR 代码：
`black` (30)、`red` (31)、`green` (32)、`yellow` (33)、`blue` (34)、`magenta` (35)、`cyan` (36)、`white` (37)。

`BRIGHT_COLORS` 字典包含 8 种高亮变体：
`bright_black` (90) 到 `bright_white` (97)。

#### 光标控制

| 常量 | 效果 |
|------|------|
| `CURSOR_UP` | 光标上移 1 行 |
| `CURSOR_DOWN` | 光标下移 1 行 |
| `CURSOR_FORWARD` | 光标前移 1 列 |
| `CURSOR_BACK` | 光标后移 1 列 |
| `CURSOR_HIDE` | 隐藏光标 |
| `CURSOR_SHOW` | 显示光标 |
| `CLEAR_LINE` | 清除光标到行尾 |
| `CLEAR_SCREEN` | 清除整个屏幕 |
| `CURSOR_HOME` | 光标移到左上角 |

### 函数

完整函数签名和文档字符串请参阅 [API 参考](../api/ansi.md)。

## 兄弟模块集成

本模块可通过受保护的导入作为其他 zerodep 模块的共享依赖：

```python
# 在其他 zerodep 模块中
try:
    from ansi import style, fg, RESET
except ImportError:
    # 回退：内联 ANSI 常量
    RESET = "\033[0m"
    def fg(color): return ""
    def style(text, **kw): return text
```

目前 `structlog` 和 `prompt` 维护的内联 ANSI 常量与本模块的覆盖范围一致（8 标准色 + 8 高亮色 + 全部文本属性）。
