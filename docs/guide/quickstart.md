---
title: 快速开始
---

# 快速开始

**zerodep** 是一系列零依赖、单文件的 Python 模块，仅使用标准库（Python 3.10+）重新实现了常用第三方库的功能。无需 `pip install`，只需将一个 `.py` 文件复制到项目中即可直接导入使用。

## 安装 CLI

=== "pip"

    ```bash
    pip install zerodep
    ```

=== "免安装"

    ```bash
    curl -O https://raw.githubusercontent.com/Oaklight/zerodep/master/zerodep.py
    python zerodep.py --help
    ```

## 获取你的第一个模块

使用 `zerodep` CLI 获取 `yaml` 模块：

```bash
zerodep add yaml
```

这会将 `yaml.py` 下载到当前目录。无需虚拟环境，无需处理依赖树——只有一个文件。

!!! tip "手动下载"

    你也可以直接下载文件：

    ```bash
    curl -O https://raw.githubusercontent.com/Oaklight/zerodep/master/yaml/yaml.py
    ```

## 使用模块

```python
from yaml import load, dump

data = load("name: Alice\nage: 30")
print(data)   # {'name': 'Alice', 'age': 30}
print(dump(data))
```

就是这么简单——API 与 PyYAML 基本一致，无需任何安装步骤。

## 再看一个例子：Retry 装饰器

获取 `retry` 模块：

```bash
zerodep add retry
```

将它应用到任意函数：

```python
from retry import retry

@retry(max_retries=3, retry_on=(ConnectionError, TimeoutError))
def fetch_data(url: str) -> str:
    # 自动重试最多 3 次，使用指数退避策略
    ...
```

!!! note

    同样支持异步函数——直接装饰 `async def`，重试逻辑会自动处理 `await`。

## 下一步

- [CLI 工具](cli.md) -- 完整命令参考（`add`、`list`、`info`、`update` 等）
- [模块总览](../modules/index.md) -- 浏览全部 30+ 可用模块
- [设计理念](philosophy.md) -- 何时适合（及不适合）使用 zerodep
