# Dotenv 环境变量

.env 文件解析与加载 -- 零依赖，仅标准库，Python 3.10+。

> **可替代:** `python-dotenv`

## 概述

Dotenv 模块提供了 `python-dotenv` 核心功能的直接替代方案。它可以解析 `.env` 文件、将变量加载到 `os.environ` 中，以及操作 `.env` 文件中的键值对——全部无需任何第三方依赖。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `dotenv.py` | 纯 Python 实现 | 无（仅标准库） |

该模块支持所有常见的 `.env` 语法：注释、单引号/双引号/无引号值、`export` 前缀、多行双引号值，以及 `$VAR`、`${VAR}` 和 `${VAR:-default}` 变量插值。

## 如何在你的项目中使用

只需将 `.py` 文件复制到你的项目中：

```bash
cp dotenv/dotenv.py your_project/
```

然后直接导入：

```python
from dotenv import load_dotenv, dotenv_values, find_dotenv
```

## API 参考

### `load_dotenv(dotenv_path, stream, verbose, interpolate, override, encoding)`

读取 `.env` 文件并设置 `os.environ`。

```python
def load_dotenv(
    dotenv_path: str | os.PathLike[str] | None = None,
    stream: IO[str] | None = None,
    verbose: bool = False,
    interpolate: bool = True,
    override: bool = False,
    encoding: str = "utf-8",
) -> bool
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `dotenv_path` | `str \| os.PathLike \| None` | `None` | `.env` 文件路径。如果为 `None`，使用 `find_dotenv()` 自动查找。 |
| `stream` | `IO[str] \| None` | `None` | 用于读取的文本流（优先于 `dotenv_path`）。 |
| `verbose` | `bool` | `False` | 文件缺失时向 stderr 打印警告。 |
| `interpolate` | `bool` | `True` | 展开值中的 `$VAR` 和 `${VAR}` 引用。 |
| `override` | `bool` | `False` | 如果为 `True`，覆盖已存在的环境变量。 |
| `encoding` | `str` | `"utf-8"` | 文件编码。 |

**返回值：** `bool` -- 如果找到并加载了文件则返回 `True`。

**示例：**

```python
from dotenv import load_dotenv

# 从自动检测的路径加载 .env
load_dotenv()

# 加载指定文件，覆盖已有环境变量
load_dotenv("/path/to/config.env", override=True)
```

---

### `dotenv_values(dotenv_path, stream, verbose, interpolate, override, encoding)`

解析 `.env` 文件并返回字典，**不修改** `os.environ`。

```python
def dotenv_values(
    dotenv_path: str | os.PathLike[str] | None = None,
    stream: IO[str] | None = None,
    verbose: bool = False,
    interpolate: bool = True,
    override: bool = False,
    encoding: str = "utf-8",
) -> dict[str, str | None]
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `dotenv_path` | `str \| os.PathLike \| None` | `None` | `.env` 文件路径。如果为 `None`，使用 `find_dotenv()` 自动查找。 |
| `stream` | `IO[str] \| None` | `None` | 用于读取的文本流（优先于 `dotenv_path`）。 |
| `verbose` | `bool` | `False` | 文件缺失时向 stderr 打印警告。 |
| `interpolate` | `bool` | `True` | 展开值中的 `$VAR` 和 `${VAR}` 引用。 |
| `override` | `bool` | `False` | 未使用，仅为兼容 `python-dotenv` API 而保留。 |
| `encoding` | `str` | `"utf-8"` | 文件编码。 |

**返回值：** `dict[str, str | None]` -- 将变量名映射到其值的字典。

**示例：**

```python
from dotenv import dotenv_values

config = dotenv_values(".env")
db_host = config.get("DB_HOST")
```

---

### `find_dotenv(filename, raise_error_if_not_found, usecwd)`

从调用文件所在目录（或当前工作目录）向上遍历查找 `.env` 文件。

```python
def find_dotenv(
    filename: str = ".env",
    raise_error_if_not_found: bool = False,
    usecwd: bool = False,
) -> str
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `filename` | `str` | `".env"` | 要搜索的文件名。 |
| `raise_error_if_not_found` | `bool` | `False` | 如果未找到文件则抛出 `IOError`。 |
| `usecwd` | `bool` | `False` | 从当前工作目录开始搜索，而非调用文件所在目录。 |

**返回值：** `str` -- 找到的文件的绝对路径，未找到则返回空字符串。

**示例：**

```python
from dotenv import find_dotenv

path = find_dotenv()                     # 从调用者所在目录向上搜索
path = find_dotenv(usecwd=True)          # 从当前工作目录向上搜索
path = find_dotenv(".env.production")    # 查找自定义文件名
```

---

### `get_key(dotenv_path, key_to_get, encoding)`

从 `.env` 文件中获取单个值。

```python
def get_key(
    dotenv_path: str | os.PathLike[str],
    key_to_get: str,
    encoding: str = "utf-8",
) -> str | None
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `dotenv_path` | `str \| os.PathLike` | -- | `.env` 文件路径。 |
| `key_to_get` | `str` | -- | 要获取的键名。 |
| `encoding` | `str` | `"utf-8"` | 文件编码。 |

**返回值：** `str | None` -- 键对应的值，未找到则返回 `None`。

**示例：**

```python
from dotenv import get_key

secret = get_key(".env", "SECRET_KEY")
```

---

### `set_key(dotenv_path, key_to_set, value_to_set, quote_mode, export, encoding)`

在 `.env` 文件中设置键值对，如果文件不存在则创建。

```python
def set_key(
    dotenv_path: str | os.PathLike[str],
    key_to_set: str,
    value_to_set: str,
    quote_mode: str = "always",
    export: bool = False,
    encoding: str = "utf-8",
) -> tuple[bool, str, str]
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `dotenv_path` | `str \| os.PathLike` | -- | `.env` 文件路径。 |
| `key_to_set` | `str` | -- | 要设置的键名。 |
| `value_to_set` | `str` | -- | 要设置的值。 |
| `quote_mode` | `str` | `"always"` | 引号策略：`"always"`、`"auto"` 或 `"never"`。 |
| `export` | `bool` | `False` | 是否在行首添加 `export` 前缀。 |
| `encoding` | `str` | `"utf-8"` | 文件编码。 |

**返回值：** `tuple[bool, str, str]` -- 元组 `(success, key, value)`。

**示例：**

```python
from dotenv import set_key

set_key(".env", "DB_HOST", "localhost")
set_key(".env", "API_KEY", "s3cret", quote_mode="auto")
set_key(".env", "PATH_VAR", "/usr/local/bin", export=True)
```

---

### `unset_key(dotenv_path, key_to_unset, quote_mode, encoding)`

从 `.env` 文件中移除一个键。

```python
def unset_key(
    dotenv_path: str | os.PathLike[str],
    key_to_unset: str,
    quote_mode: str = "always",
    encoding: str = "utf-8",
) -> tuple[bool, str]
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `dotenv_path` | `str \| os.PathLike` | -- | `.env` 文件路径。 |
| `key_to_unset` | `str` | -- | 要移除的键名。 |
| `quote_mode` | `str` | `"always"` | 未使用，仅为 API 兼容性保留。 |
| `encoding` | `str` | `"utf-8"` | 文件编码。 |

**返回值：** `tuple[bool, str]` -- 元组 `(success, key)`。

**示例：**

```python
from dotenv import unset_key

unset_key(".env", "OLD_VARIABLE")
```

## 用法示例

### 基本加载

```python
from dotenv import load_dotenv
import os

# 自动查找并加载 .env
load_dotenv()

# 从 os.environ 访问变量
database_url = os.environ.get("DATABASE_URL")
debug_mode = os.environ.get("DEBUG")
```

### 解析但不修改环境变量

```python
from dotenv import dotenv_values

config = dotenv_values(".env")

# 直接使用字典中的值
print(config["APP_NAME"])
print(config["SECRET_KEY"])
```

### 变量插值

给定一个 `.env` 文件：

```dotenv
BASE_DIR=/opt/myapp
DATA_DIR=${BASE_DIR}/data
LOG_DIR=${BASE_DIR}/logs
DEFAULT_PORT=${PORT:-8080}
```

```python
from dotenv import dotenv_values

config = dotenv_values(".env")
print(config["DATA_DIR"])        # /opt/myapp/data
print(config["LOG_DIR"])         # /opt/myapp/logs
print(config["DEFAULT_PORT"])    # 8080（回退值，因为 PORT 未设置）
```

### 覆盖行为

```python
import os
from dotenv import load_dotenv

os.environ["EXISTING"] = "original"

# 默认：不覆盖已存在的环境变量
load_dotenv()
print(os.environ["EXISTING"])  # "original"

# 使用 override=True：覆盖已存在的环境变量
load_dotenv(override=True)
print(os.environ["EXISTING"])  # .env 文件中的值
```

### 从流中读取

```python
import io
from dotenv import load_dotenv, dotenv_values

env_content = """
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
"""

# 从字符串流解析
config = dotenv_values(stream=io.StringIO(env_content))
print(config)  # {'DB_HOST': 'localhost', 'DB_PORT': '5432', 'DB_NAME': 'myapp'}
```

## 支持的特性

解析器支持以下 `.env` 文件语法：

| 特性 | 语法 | 示例 |
|------|------|------|
| 简单值 | `KEY=value` | `HOST=localhost` |
| 双引号 | `KEY="value"` | `MSG="hello world"` |
| 单引号 | `KEY='value'` | `MSG='no $interpolation'` |
| 无引号 | `KEY=value` | `PORT=8080` |
| 注释 | `# comment` | `# This is a comment` |
| 行内注释 | `KEY=value # comment` | `PORT=8080 # default port` |
| Export 前缀 | `export KEY=value` | `export PATH=/usr/bin` |
| 空值 | `KEY=` | `EMPTY=` |
| 仅键名 | `KEY` | `UNDEFINED`（解析为 `None`） |
| 多行（双引号） | `KEY="line1\nline2"` | `"..."` 中的实际换行符 |
| 转义序列 | `\n`、`\t`、`\\`、`\"`、`\$` | 在双引号值中 |
| 变量插值 | `$VAR`、`${VAR}` | `URL=http://$HOST:$PORT` |
| 默认值 | `${VAR:-default}` | `PORT=${PORT:-3000}` |
| UTF-8 BOM | 自动去除 | -- |

**插值解析顺序：** 优先查找文件内定义的变量，然后查找 `os.environ`，最后返回空字符串。

**单引号值**被视为字面量——不进行转义处理或变量插值。

## 注意事项

!!! info "与 python-dotenv 的 API 兼容性"
    本模块设计为 `python-dotenv` 的直接替代品。公开函数签名（`load_dotenv`、`dotenv_values`、`find_dotenv`、`get_key`、`set_key`、`unset_key`）与 `python-dotenv` 一致，可以直接替换而无需修改代码。

!!! info "dotenv_values 中的 override 参数"
    `dotenv_values()` 中的 `override` 参数被接受但未使用——它仅为与 `python-dotenv` 的签名兼容性而存在。由于 `dotenv_values()` 不修改 `os.environ`，该参数没有实际效果。

!!! info "unset_key 中的 quote_mode 参数"
    `unset_key()` 中的 `quote_mode` 参数被接受但未使用——它仅为与 `python-dotenv` 的签名兼容性而存在。

- **Python 版本：** 需要 Python 3.10+（使用了 `X | Y` 联合类型语法）。
- **文件创建：** `set_key()` 在文件不存在时会创建 `.env` 文件（及父目录）。
- **编码：** 所有函数默认使用 UTF-8。解析时自动去除 UTF-8 BOM。
- **无 CLI：** 与 `python-dotenv` 不同，本模块不提供命令行接口。

## 性能测试

与 `python-dotenv` 在三种 `.env` 文件大小（10、50、500 条目）下进行对比。

详见 [Dotenv 性能测试](../benchmarks/dotenv.md)。
