# 版本解析器

PEP 440 版本解析与比较器 -- 零依赖，仅标准库，Python 3.10+。

## 概述

`semver.py` 是一个单文件版本解析模块，实现完整的 PEP 440 版本解析、规范化和比较功能。可作为 `packaging.version` 核心功能的 drop-in 替代。**无需任何 pip 依赖**。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `semver.py` | 纯 Python 实现 | 无（仅标准库：`re`、`functools`） |

## 快速开始

### 解析版本

```python
from semver import Version, version_parse

v = Version("1.2.3")
v = version_parse("1.2.3")  # 等价的便利函数
```

### 版本比较

```python
from semver import Version

assert Version("2.0") > Version("1.0")
assert Version("1.0a1") < Version("1.0")
assert Version("1.0") == Version("1.0.0")
assert Version("1.0") <= Version("2.0")
```

### 排序和选择

```python
from semver import Version

versions = [Version("3.0"), Version("1.0"), Version("2.0b1"), Version("2.0")]
print(sorted(versions))
# [<Version('1.0')>, <Version('2.0b1')>, <Version('2.0')>, <Version('3.0')>]

print(max(versions))
# <Version('3.0')>
```

### 预发布和开发版检测

```python
from semver import Version

v = Version("1.0a1")
print(v.is_prerelease)  # True
print(v.is_devrelease)  # False

v = Version("1.0.dev3")
print(v.is_prerelease)  # True（dev 版本也是预发布）
print(v.is_devrelease)  # True
```

### 版本属性

```python
from semver import Version

v = Version("2!1.2.3a1.post2.dev3+local.1")
print(v.epoch)         # 2
print(v.release)       # (1, 2, 3)
print(v.major)         # 1
print(v.minor)         # 2
print(v.micro)         # 3
print(v.pre)           # ('a', 1)
print(v.post)          # 2
print(v.dev)           # 3
print(v.local)         # 'local.1'
print(v.base_version)  # '2!1.2.3'
print(v.public)        # '2!1.2.3a1.post2.dev3'
```

### 字符串规范化

```python
from semver import Version

print(str(Version("1.0alpha1")))   # '1.0a1'
print(str(Version("1.0beta2")))    # '1.0b2'
print(str(Version("1.0preview1"))) # '1.0rc1'
print(str(Version("v1.0")))        # '1.0'
print(str(Version("1.0-1")))       # '1.0.post1'
```

### 错误处理

```python
from semver import Version, InvalidVersion

try:
    Version("not a version")
except InvalidVersion as e:
    print(e)  # Invalid version: 'not a version'
```

## PEP 440 排序规则

模块实现了完整的 PEP 440 版本排序：

```
.devN < aN (alpha) < bN (beta) < rcN < release < .postN
```

## API 参考

### `Version(version: str)`

解析 PEP 440 版本字符串。

**异常：** 不符合 PEP 440 时抛出 `InvalidVersion`。

**属性：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `epoch` | `int` | epoch 段（不存在时为 `0`） |
| `release` | `tuple[int, ...]` | 发布段整数元组 |
| `pre` | `tuple[str, int] \| None` | 预发布标签，如 `('a', 1)` |
| `post` | `int \| None` | 后续发布编号 |
| `dev` | `int \| None` | 开发版编号 |
| `local` | `str \| None` | 本地版本标签 |
| `major` | `int` | 发布段第一位 |
| `minor` | `int` | 发布段第二位（不存在时为 `0`） |
| `micro` | `int` | 发布段第三位（不存在时为 `0`） |
| `base_version` | `str` | 不含 pre/post/dev/local 的版本 |
| `public` | `str` | 不含 local 段的版本 |
| `is_prerelease` | `bool` | 预发布或开发版为 `True` |
| `is_devrelease` | `bool` | 开发版为 `True` |
| `is_postrelease` | `bool` | 后续发布为 `True` |

**运算符：** `==`、`!=`、`<`、`>`、`<=`、`>=`、`hash()`、`str()`、`repr()`

---

### `version_parse(version: str) -> Version`

便利函数，等价于 `Version(version)`。

---

### `InvalidVersion`

无法解析的版本字符串抛出的异常。继承自 `ValueError`。

## 与 packaging 的对比

| 特性 | zerodep semver | packaging |
|------|---------------|-----------|
| 依赖 | 无（仅标准库） | 无（但增加一个 pip 依赖） |
| API | `Version("1.0")` | `Version("1.0")` |
| 比较 | 全部运算符 | 全部运算符 |
| 规范化 | 完整 PEP 440 | 完整 PEP 440 |
| 性能 | 相当（详见性能测试） | 相当 |
| 实现 | 单文件（~300 行） | 完整包 |

**何时使用 zerodep：** 只需 PEP 440 版本解析/比较，不想引入 pip 依赖。

**何时使用 packaging：** 需要完整的 packaging 库功能（specifiers、requirements、markers、tags）。

## 性能测试

与 `packaging` 在解析、排序、比较和属性访问等场景下进行对比。

详见 [版本解析器性能测试](../benchmarks/semver.md)。
