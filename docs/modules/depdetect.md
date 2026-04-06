# 依赖检测

依赖检测与验证 — 零依赖、仅使用标准库、Python 3.10+。

## 概述

从 Python 源代码、requirements 文件和自由文本兼容性字符串中解析依赖信息。验证当前系统上的二进制程序、Python 包和环境变量是否可用。

| 文件 | 描述 | 依赖 |
|------|------|------|
| `depdetect.py` | 依赖检测与验证 | 无（仅标准库） |

**核心功能：**

- 通过 AST 解析 `import` / `from ... import` 语句，自动过滤标准库
- 解析 `requirements.txt` 文件，支持版本约束和 extras
- 解析自由文本兼容性字符串（如 `"Python 3.10+, pandoc >= 3.0"`）
- 从 `allowed-tools` 字段中提取二进制程序提示（如 `Bash(git:* docker:*)`）
- 解析 import 名称与 pip 包名之间的映射（三级回退：元数据 → 静态映射 → 启发式）
- 通过 `shutil.which()` 检测二进制程序，支持跨平台别名
- 通过 `importlib.util.find_spec()` 检测 Python 包的可导入性
- 通过超时保护的子进程调用获取二进制程序版本
- 将依赖检查结果汇总为结构化报告

## 如何在项目中使用

将单个 `.py` 文件复制到你的项目中：

```bash
cp depdetect/depdetect.py your_project/
```

或通过 CLI 安装：

```bash
zerodep add depdetect
```

然后直接导入：

```python
from depdetect import parse_imports, analyze_source, check_requirements
```

## 使用示例

### 分析 Python 源代码

```python
from depdetect import parse_imports, analyze_source

# 提取第三方 import 名称（自动过滤标准库）
imports = parse_imports("import requests\nimport os\nfrom PIL import Image\n")
# → {"requests", "PIL"}

# 解析为 pip 可安装的包名
pip_names = analyze_source("import yaml\nfrom PIL import Image\n")
# → {"pyyaml", "pillow"}
```

### 解析 Requirements 文件

```python
from depdetect import parse_requirements

reqs = parse_requirements("""
requests>=2.28.0
pillow>=10.0
python-dotenv[cli]>=1.0
# 这是一条注释
-r other-requirements.txt
""")
# → [Requirement("requests", "python", ">=", "2.28.0"),
#    Requirement("pillow", "python", ">=", "10.0"),
#    Requirement("python-dotenv", "python", ">=", "1.0", extras="cli")]
```

### 解析兼容性字符串

```python
from depdetect import parse_compatibility

reqs = parse_compatibility("Python 3.10+, pandoc >= 3.0, Node.js >= 18")
# → [Requirement("Python", "runtime", ">=", "3.10"),
#    Requirement("pandoc", "binary", ">=", "3.0"),
#    Requirement("Node.js", "runtime", ">=", "18")]
```

### 从工具声明中提取二进制程序提示

```python
from depdetect import parse_tool_hints

binaries = parse_tool_hints("Bash(git:* docker:* npm:*) Read Write")
# → ["git", "docker", "npm"]
```

### 解析 import 名称到 pip 包名

```python
from depdetect import resolve_pip_name

resolve_pip_name("PIL")     # → "pillow"
resolve_pip_name("yaml")    # → "pyyaml"（或从元数据获取 "PyYAML"）
resolve_pip_name("dotenv")  # → "python-dotenv"
resolve_pip_name("bs4")     # → "beautifulsoup4"
```

### 检测系统依赖

```python
from depdetect import check_binary, check_python_package, get_binary_version, check_env_var

# 二进制程序检测
path = check_binary("git")          # "/usr/bin/git" 或 None
path = check_binary("node.js")      # 解析别名 → 检查 "node"

# 二进制程序版本
ver = get_binary_version("git")     # "2.43.0" 或 None

# Python 包
ok = check_python_package("requests")  # True / False
ok = check_python_package("pillow")    # 内部检查 "PIL"

# 环境变量
ok = check_env_var("OPENAI_API_KEY")   # 如果已设置且非空则返回 True
```

### 完整依赖检查与报告

```python
from depdetect import Requirement, check_requirements

reqs = [
    Requirement("git", "binary", ">=", "2.0"),
    Requirement("requests", "python", ">=", "2.28"),
    Requirement("Python", "runtime", ">=", "3.10"),
    Requirement("OPENAI_API_KEY", "env"),
]

report = check_requirements(reqs)

if report.satisfied:
    print("所有依赖均已满足！")
else:
    print("缺少以下依赖：")
    for dep in report.missing:
        print(f"  - {dep.name}: {dep.message}")

print(report.summary())
# [OK] git (2.43.0): found at /usr/bin/git
# [OK] requests (2.31.0): importable
# [OK] Python (3.12.0): current interpreter
# [MISSING] OPENAI_API_KEY: OPENAI_API_KEY not set
#
# 3/4 dependencies satisfied.
```

## 名称解析

`resolve_pip_name()` 函数使用三级回退策略将 import 名称映射到 pip 包名：

| 级别 | 来源 | 示例 |
|------|------|------|
| 1. 元数据 | `importlib.metadata`（已安装的包） | 动态，与环境相关 |
| 2. 静态映射 | 内置 `_IMPORT_TO_PIP` 字典（约 10 条） | `PIL` → `pillow`, `yaml` → `pyyaml` |
| 3. 启发式 | 将 `_` 替换为 `-` | `my_package` → `my-package` |

反向映射（pip 包名 → import 名称）由 `_PIP_TO_IMPORT` 在 `check_python_package()` 等函数内部处理。

## 数据类

| 类 | 描述 |
|----|------|
| `Requirement` | 已解析的依赖项（名称、类别、版本约束、extras） |
| `DependencyStatus` | 单个依赖的检查结果（是否找到、版本、路径、消息） |
| `DependencyReport` | 汇总结果，提供 `.satisfied`、`.missing`、`.summary()` |

## API 参考

请参阅 [API 参考](../api/depdetect.md) 获取完整的函数签名和文档字符串。

## 性能测试

本模块不提供性能测试。作为一个用于依赖检测的开发工具，没有直接对应的第三方库可供对比测试——详见 [Depdetect 性能测试](../benchmarks/depdetect.md)。
