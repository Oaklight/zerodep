# 交互式提示

零依赖的交互式 CLI 提示（confirm、select、text）—— 仅使用标准库，支持 Python 3.10+。

## 概述

Prompt 模块提供类似 *questionary* 的交互式命令行提示，仅使用 Python 标准库。支持 Linux 和 macOS（通过 `termios`/`tty`）以及 Windows（通过 `msvcrt`），在无 TTY 环境下自动回退到纯 `input()` 模式。

| 文件 | 描述 | 依赖 |
|------|------|------|
| `prompt.py` | 纯 Python 实现 | 无（仅标准库：`sys`、`os`、`io`、`contextlib`、`termios`/`tty` 或 `msvcrt`） |

## 在你的项目中使用

只需将单个 `.py` 文件复制到你的项目中：

```bash
cp prompt/prompt.py your_project/
```

然后直接导入：

```python
from prompt import confirm, select, text, Style
```

## 使用示例

### confirm()

```python
from prompt import confirm

answer = confirm("Continue with installation?")
if answer:
    print("Installing...")
else:
    print("Cancelled.")
```

自定义默认值：

```python
# 默认选择"否"
answer = confirm("Delete all files?", default=False)
```

### select()

```python
from prompt import select

# 简单字符串选项
lang = select("Choose a language:", ["Python", "Rust", "Go"])
print(f"You chose: {lang}")
```

使用 name/value 字典：

```python
choice = select("Pick a color:", [
    {"name": "Red", "value": "#ff0000"},
    {"name": "Green", "value": "#00ff00"},
    {"name": "Blue", "value": "#0000ff"},
])
print(f"Hex: {choice}")
```

设置默认选项：

```python
lang = select("Language:", ["Python", "Rust", "Go"], default="Python")
```

### text()

```python
from prompt import text

name = text("Your name:")
print(f"Hello, {name}!")
```

带验证：

```python
email = text(
    "Email address:",
    validate=lambda s: True if "@" in s else "Must contain @",
)
```

带默认值：

```python
host = text("Hostname:", default="localhost")
```

### 自定义样式

```python
from prompt import confirm, Style

style = Style([
    ("question", "fg:#00ff00 bold"),
    ("answer", "fg:#ffffff"),
    ("pointer", "fg:#ff0000"),
    ("highlighted", "fg:#00ffff bold"),
    ("instruction", "fg:#888888"),
    ("error", "fg:#ff0000 bold"),
])

answer = confirm("Continue?", style=style)
```

## API 参考

### `confirm(message, default=True, style=None)`

询问是/否问题。

**参数：**

| 名称 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `message` | `str` | -- | 要显示的问题。 |
| `default` | `bool` | `True` | 预选答案（`True` = 是）。 |
| `style` | `Style \| None` | `None` | 可选的样式自定义。 |

**返回：** `True` 表示是，`False` 表示否，`None` 表示取消（Ctrl-C）。

---

### `select(message, choices, default=None, style=None)`

显示选项列表，支持方向键导航。

**参数：**

| 名称 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `message` | `str` | -- | 列表上方的问题。 |
| `choices` | `list[str] \| list[dict]` | -- | 纯字符串或 `{"name": ..., "value": ...}` 字典。 |
| `default` | `str \| None` | `None` | 预选值。默认为第一个选项。 |
| `style` | `Style \| None` | `None` | 可选的样式自定义。 |

**返回：** 所选选项的 `value`，取消时返回 `None`。

---

### `text(message, default="", validate=None, style=None)`

提示用户输入自由文本。

**参数：**

| 名称 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `message` | `str` | -- | 要显示的问题。 |
| `default` | `str` | `""` | 默认值（按 Enter 时使用）。 |
| `validate` | `Callable \| None` | `None` | 可调用对象 `(str) -> bool \| str`。返回 `True` 接受，或返回错误消息字符串。 |
| `style` | `Style \| None` | `None` | 可选的样式自定义。 |

**返回：** 输入的字符串，取消时（Ctrl-C）返回 `None`。

---

### `Style(style_list=None)`

提示的 ANSI 样式配置。

**参数：**

| 名称 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `style_list` | `list[tuple[str, str]] \| None` | `None` | `(角色, 样式字符串)` 元组列表。 |

**支持的角色：** `"question"`、`"answer"`、`"pointer"`、`"highlighted"`、`"error"`、`"instruction"`。

**样式字符串格式：** 空格分隔的标记：`fg:#hex颜色`、`bg:#hex颜色`、`bold`、`italic`、`underline`。

## TTY 检测与回退

在非 TTY 环境（管道输入、CI 环境等）下运行时，模块会自动为 `select()` 回退到编号列表模式，其他提示使用纯 `input()`。这使得使用 `prompt.py` 的脚本可以安全地在非交互式环境中运行。

## 与 questionary 的对比

| 特性 | zerodep prompt | questionary |
|------|---------------|-------------|
| 依赖 | 无（仅标准库） | `prompt_toolkit` |
| 文件数 | 单文件 | 多文件包 |
| confirm / select / text | 是 | 是 |
| checkbox / password / path / autocomplete | 否 | 是 |
| 自定义样式 | 是（hex 颜色、粗体、斜体） | 是（通过 prompt_toolkit Style） |
| 非 TTY 回退 | 是（自动） | 部分 |
| Windows 支持 | 是（通过 `msvcrt`） | 是（通过 prompt_toolkit） |

**适用场景（zerodep）：** 需要基本的交互式提示（confirm、select、text），零依赖且跨平台支持。

**适用场景（questionary）：** 需要高级提示类型（checkbox、password、autocomplete）或 prompt_toolkit 的全部功能。
