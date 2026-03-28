# Config 配置加载器

统一配置加载器 -- 零依赖，仅标准库，Python 3.10+。

## 概述

Config 模块提供了 `python-decouple` 和 `dynaconf`（子集）核心功能的直接替代方案。它从多种来源加载配置——环境变量、`.env` 文件和配置文件（JSON、JSONC、YAML、TOML、INI）——支持类型转换、前缀命名空间和嵌套键访问，遵循 [12-factor app](https://12factor.net/config) 模式。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `config.py` | 纯 Python 实现 | `dotenv`、`yaml`、`jsonc`（均为可选兄弟模块） |

该模块支持所有常见的配置模式：带前缀命名空间的环境变量查找、`.env` 文件自动发现、通过分隔符的嵌套键访问，以及内置的 `bool`、`int`、`float`、`list`、`tuple` 类型转换，还有 `Csv` 和 `Choices` 辅助类。

## 如何在你的项目中使用

将 `.py` 文件复制到你的项目中：

```bash
cp config/config.py your_project/
```

如需完整功能，还可复制可选的兄弟模块：

```bash
cp dotenv/dotenv.py your_project/   # .env 文件支持
cp yaml/yaml.py your_project/       # YAML 配置文件支持
cp jsonc/jsonc.py your_project/     # JSONC 配置文件支持
```

然后直接导入：

```python
from config import config, setup, Config, Csv, Choices
```

## 配置源优先级

配置值按以下顺序解析（优先级从高到低）：

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1（最高） | 环境变量 | `os.environ`，支持可选前缀 |
| 2 | `.env` 文件 | 通过兄弟 `dotenv` 模块加载，自动发现或指定路径 |
| 3 | 配置文件 | JSON、JSONC、YAML、TOML 或 INI 文件 |
| 4（最低） | 默认值 | 传入 `get()` / `__call__()` 的 `default` 参数 |

## API 参考

### `Config(dotenv_path, config_path, prefix, separator)`

主配置类。从多个来源加载配置，按优先级解析值。

```python
class Config:
    def __init__(
        self,
        *,
        dotenv_path: str | os.PathLike | None | _Auto = _AUTO,
        config_path: str | os.PathLike | None = None,
        prefix: str = "",
        separator: str = "__",
    ) -> None
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `dotenv_path` | `str \| os.PathLike \| None` | `_AUTO` | `.env` 文件路径。`_AUTO` = 自动发现，`None` = 禁用。 |
| `config_path` | `str \| os.PathLike \| None` | `None` | 配置文件路径（格式由扩展名自动检测）。 |
| `prefix` | `str` | `""` | 环境变量查找前缀（如 `"MYAPP_"`）。 |
| `separator` | `str` | `"__"` | 嵌套键访问的分隔符。 |

**示例：**

```python
from config import Config

cfg = Config(config_path="settings.yaml", prefix="MYAPP_")
debug = cfg("DEBUG", default=False, cast=bool)
db_host = cfg("DATABASE__HOST", default="localhost")
```

---

### `Config.__call__(key, default, cast)` / `Config.get(key, default, cast)`

获取配置值。

```python
def get(
    self,
    key: str,
    *,
    default: Any = MISSING,
    cast: type | Callable | None = None,
) -> Any
```

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `key` | `str` | -- | 要查找的配置键。 |
| `default` | `Any` | `MISSING` | 键不存在时的回退值。省略则该键为必填。 |
| `cast` | `type \| Callable \| None` | `None` | 用于转换值的类型或可调用对象。 |

**返回值：** 解析后（可选转换后）的配置值。

**异常：** 键不存在且未提供默认值时抛出 `UndefinedValueError`。

**示例：**

```python
cfg = Config(dotenv_path=None)

port = cfg("PORT", default=8000, cast=int)
debug = cfg("DEBUG", default=False, cast=bool)
hosts = cfg("ALLOWED_HOSTS", cast=Csv())
```

---

### `Config.has(key)`

检查键是否存在于任一配置源中。

```python
def has(self, key: str) -> bool
```

---

### `Config.as_dict()`

返回所有配置源的合并扁平化字典。

```python
def as_dict(self) -> dict[str, Any]
```

---

### `setup(dotenv_path, config_path, prefix, separator)`

初始化模块级 `Config` 实例。

```python
def setup(
    *,
    dotenv_path=_AUTO,
    config_path=None,
    prefix="",
    separator="__",
) -> Config
```

**返回值：** 新创建的 `Config` 实例。

---

### `config(key, default, cast)`

模块级便捷函数。如果未调用 `setup()`，会自动创建默认 `Config`。

```python
def config(
    key: str,
    *,
    default: Any = MISSING,
    cast: type | Callable | None = None,
) -> Any
```

**示例：**

```python
from config import config, setup

setup(prefix="MYAPP_")
port = config("PORT", default=8000, cast=int)
debug = config("DEBUG", default=False, cast=bool)
```

---

### `Csv(cast, delimiter, strip, post_process)`

解析逗号分隔值，支持可选的逐项类型转换。

```python
class Csv:
    def __init__(
        self,
        cast: Callable = str,
        delimiter: str = ",",
        strip: str = " %s",
        post_process: Callable = list,
    ) -> None
```

**示例：**

```python
Csv()("a, b, c")           # ["a", "b", "c"]
Csv(cast=int)("1,2,3")     # [1, 2, 3]
Csv(delimiter=";")("a;b")  # ["a", "b"]
Csv(post_process=tuple)("a,b")  # ("a", "b")
```

---

### `Choices(choices, cast)`

验证值是否属于固定集合。

```python
class Choices:
    def __init__(
        self,
        choices: Sequence[Any],
        cast: Callable = str,
    ) -> None
```

**示例：**

```python
Choices(["dev", "staging", "prod"])("dev")  # "dev"
Choices([1, 2, 3], cast=int)("2")           # 2
Choices(["a", "b"])("c")                    # 抛出 ValueError
```

## 使用示例

### 基本环境变量

```python
from config import config, setup

setup(prefix="MYAPP_", dotenv_path=None)

# 从 os.environ 读取 MYAPP_PORT
port = config("PORT", default=8000, cast=int)
debug = config("DEBUG", default=False, cast=bool)
```

### 从 .env 文件加载

```python
from config import Config

# 自动发现 .env 文件
cfg = Config()
db_host = cfg("DB_HOST")
db_port = cfg("DB_PORT", cast=int)

# 或指定明确路径
cfg = Config(dotenv_path="/path/to/.env")
```

### 从配置文件加载

```python
from config import Config

# JSON 配置
cfg = Config(dotenv_path=None, config_path="config.json")

# YAML 配置（需要兄弟 yaml 模块）
cfg = Config(dotenv_path=None, config_path="settings.yaml")

# TOML 配置（需要 Python 3.11+）
cfg = Config(dotenv_path=None, config_path="config.toml")

# INI 配置
cfg = Config(dotenv_path=None, config_path="settings.ini")
```

### 嵌套键访问

给定 `config.yaml`：

```yaml
database:
  host: localhost
  port: 5432
  name: myapp
```

```python
from config import Config

cfg = Config(dotenv_path=None, config_path="config.yaml")
host = cfg("database__host")           # "localhost"
port = cfg("database__port", cast=int)  # 5432
```

环境变量会覆盖嵌套配置：

```bash
export database__host=production-db.example.com
```

```python
host = cfg("database__host")  # "production-db.example.com"
```

### 优先级覆盖

```python
import os
from config import Config

# config.json: {"APP_MODE": "config"}
# .env:         APP_MODE=dotenv
# os.environ:   APP_MODE=environ

cfg = Config(dotenv_path=".env", config_path="config.json")
cfg("APP_MODE")  # "environ"（环境变量优先）

del os.environ["APP_MODE"]
cfg("APP_MODE")  # "dotenv"（.env 优先于配置文件）
```

## 支持的配置文件格式

| 扩展名 | 解析器 | 要求 |
|--------|--------|------|
| `.json` | 标准库 `json` | -- |
| `.jsonc` | 兄弟 `jsonc` 模块，回退到 `json` | jsonc（可选） |
| `.yaml`、`.yml` | 兄弟 `yaml` 模块 | yaml（必需） |
| `.toml` | 标准库 `tomllib` | Python 3.11+ |
| `.ini`、`.cfg` | 标准库 `configparser` | -- |

## 内置类型转换

| `cast` | 行为 |
|--------|------|
| `int` | `int(value)` |
| `float` | `float(value)` |
| `bool` | 真值：`"1"`、`"true"`、`"yes"`、`"on"`、`"t"`、`"y"` / 假值：`"0"`、`"false"`、`"no"`、`"off"`、`"f"`、`"n"`、`""` |
| `list` | 先尝试 JSON 数组解析，失败则逗号分割 |
| `tuple` | 同 `list` 但返回 `tuple` |
| `Csv(...)` | 可配置的 CSV 解析 |
| `Choices(...)` | 值白名单验证 |
| 任意可调用对象 | 调用 `cast(value)` |

## 注意事项

!!! info "与 python-decouple 的 API 兼容性"
    `config()` 函数和 `Csv`/`Choices` 辅助类与 `python-decouple` 的 API 一致，因此可以最小化代码修改进行替换。`Config` 类添加了 `python-decouple` 中没有的额外功能（配置文件、嵌套键）。

!!! info "兄弟模块依赖"
    `dotenv`、`yaml` 和 `jsonc` 兄弟模块是**可选的**。没有它们时，对应功能会优雅降级：跳过 `.env` 自动发现，YAML 配置文件抛出 `ImportError`，JSONC 回退到普通 JSON 解析。

!!! info "INI 段落展平"
    对于 `.ini`/`.cfg` 文件，段落会被展平为分隔符连接的键。例如，`[database]` 段落中的 `host = localhost` 变为 `database__host`。

- **Python 版本：** 需要 Python 3.10+（使用 `X | Y` 联合类型语法）。
- **TOML 支持：** 需要 Python 3.11+（使用标准库 `tomllib`）。
- **大小写敏感：** 环境变量查找区分大小写。配置文件嵌套查找不区分大小写。

## 性能测试

与 `python-decouple` 在环境变量查找、类型转换和 CSV 解析方面进行了基准测试。

详细结果请参见 [Config 性能测试](../benchmarks/config.md)。
