# 命令运行器

零依赖的结构化子进程执行模块 -- 仅依赖标准库，Python 3.10+。

## 概述

Runner 模块提供了结构化的外部命令执行方式，支持超时升级、流式输出、环境隔离和跨平台运行 -- 无需任何第三方依赖。

| 文件 | 说明 | 依赖 |
|------|------|------|
| `runner.py` | 纯 Python 实现 | 无（仅标准库：`subprocess`、`asyncio`、`shlex`、`shutil`、`threading`、`time`） |

功能特性：

- **同步 + 异步** 执行，API 完全一致
- **流式输出** 支持回调函数或上下文管理器迭代器
- **SIGTERM 到 SIGKILL 超时升级**，可配置 kill 延迟
- **环境控制** -- 替换、增补或移除环境变量
- **命令策略** -- 白名单/黑名单安全防护
- **结构化结果** -- `RunResult` 数据类，包含 stdout、stderr、returncode、duration、pid
- **跨平台** -- Windows `CREATE_NO_WINDOW`，平台感知引号处理

## 快速开始

将单个 `.py` 文件复制到你的项目中：

```bash
cp runner/runner.py your_project/
```

然后直接导入：

```python
from runner import run, run_async, stream, stream_async
```

## 使用示例

### 基本命令执行

```python
from runner import run

# 列表形式（推荐）
result = run(["echo", "hello", "world"])
print(result.stdout)      # "hello world\n"
print(result.returncode)  # 0
print(result.duration)    # 0.003

# 字符串形式（通过 shlex 自动拆分）
result = run("echo hello world")
```

### 标准输入

```python
from runner import run

result = run(
    ["python3", "-c", "import sys; print(sys.stdin.read().upper())"],
    input="hello world",
)
print(result.stdout)  # "HELLO WORLD\n"
```

### 错误处理

```python
from runner import run, CommandFailedError, CommandTimeoutError

# check=True（默认） -- 非零退出码时抛出异常
try:
    run(["false"])
except CommandFailedError as e:
    print(e.result.returncode)  # 1
    print(e.result.stderr)

# 抑制异常
result = run(["false"], check=False)
print(result.returncode)  # 1
```

### 超时与强制终止升级

```python
from runner import run, CommandTimeoutError

try:
    run(["sleep", "60"], timeout=5.0, kill_delay=2.0)
except CommandTimeoutError as e:
    print(f"超时：{e.timeout} 秒")
    print(e.partial_stdout)  # 超时前的输出
```

超时策略：

1. 等待最多 `timeout` 秒
2. 发送 SIGTERM（优雅关闭）
3. 等待最多 `kill_delay` 秒
4. 发送 SIGKILL（强制终止）

### 环境控制

```python
from runner import run

# 向继承的环境中添加变量
result = run(["env"], env_extra={"MY_VAR": "hello"})

# 移除敏感变量
result = run(["env"], env_remove=["SECRET_KEY", "AWS_ACCESS_KEY_ID"])

# 完全替换（干净环境）
result = run(["env"], env={"PATH": "/usr/bin", "HOME": "/tmp"})

# 三者可组合：从 env 开始，移除后再添加
result = run(
    ["env"],
    env={"PATH": "/usr/bin"},
    env_remove=["OLDVAR"],
    env_extra={"NEWVAR": "value"},
)
```

### 回调流式输出

```python
from runner import run

# 流式读取 stdout，同时仍捕获完整输出
result = run(
    ["make", "build"],
    on_stdout=lambda line: print(f"[build] {line}", end=""),
    on_stderr=lambda line: print(f"[ERR]   {line}", end=""),
)
# result.stdout 包含完整的捕获输出
```

### 上下文管理器流式输出

```python
from runner import stream

# 逐行迭代 stdout
with stream(["make", "build"]) as proc:
    for line in proc.iter_lines():
        print(f"[build] {line}", end="")
print(f"退出码: {proc.returncode}")

# 交错读取 stdout 和 stderr
with stream(["make", "build"]) as proc:
    for source, line in proc.iter_any():
        prefix = "[OUT]" if source == "stdout" else "[ERR]"
        print(f"{prefix} {line}", end="")
```

### 异步执行

```python
import asyncio
from runner import run_async, stream_async

async def main():
    # 基本异步执行
    result = await run_async("ls -la")
    print(result.stdout)

    # 异步流式输出
    async with stream_async(["make", "build"]) as proc:
        async for line in proc.aiter_lines():
            print(line, end="")

asyncio.run(main())
```

### 命令策略（白名单/黑名单）

```python
from runner import run, CommandBlockedError

# 仅允许特定命令
try:
    run(["rm", "-rf", "/"], allowed_commands=["echo", "cat", "ls"])
except CommandBlockedError as e:
    print(f"{e.command} 被阻止: {e.reason}")

# 阻止危险命令
run(["echo", "safe"], blocked_commands=["rm", "dd", "mkfs"])
```

### 工具函数

```python
from runner import shell_split, shell_quote, which

# 解析 shell 字符串为参数列表
args = shell_split('git commit -m "hello world"')
# ['git', 'commit', '-m', 'hello world']

# 引号转义以安全插入 shell
quoted = shell_quote("hello world", "it's fine")
# "'hello world' \"it's fine\""

# 在 PATH 中定位命令
path = which("git")
# '/usr/bin/git'
```

## API 参考

### `run(cmd, *, ...)`

同步执行命令，返回 `RunResult`。

**参数：**

| 名称 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `cmd` | `str \| Sequence[str]` | *（必需）* | 命令字符串（自动拆分）或参数列表 |
| `input` | `str \| None` | `None` | 发送到 stdin 的文本 |
| `cwd` | `str \| Path \| None` | `None` | 工作目录 |
| `env` | `dict[str, str] \| None` | `None` | 完全替换的环境变量 |
| `env_extra` | `dict[str, str] \| None` | `None` | 合并到继承环境中的额外变量 |
| `env_remove` | `Sequence[str] \| None` | `None` | 从继承环境中移除的变量 |
| `timeout` | `float \| None` | `30.0` | 最大等待秒数；`None` = 无限制 |
| `kill_delay` | `float` | `5.0` | SIGTERM 到 SIGKILL 之间的等待秒数 |
| `check` | `bool` | `True` | 非零退出码时抛出 `CommandFailedError` |
| `encoding` | `str` | `"utf-8"` | stdout/stderr 的文本编码 |
| `on_stdout` | `Callable \| None` | `None` | 每行 stdout 的回调函数 |
| `on_stderr` | `Callable \| None` | `None` | 每行 stderr 的回调函数 |
| `allowed_commands` | `Sequence[str] \| None` | `None` | 允许的命令白名单 |
| `blocked_commands` | `Sequence[str] \| None` | `None` | 拒绝的命令黑名单 |

**返回值：** `RunResult`

**异常：** `CommandNotFoundError`、`CommandFailedError`、`CommandTimeoutError`、`CommandBlockedError`、`ValueError`

---

### `run_async(cmd, *, ...)`

`run()` 的异步版本。参数和返回类型完全相同。

---

### `stream(cmd, *, ...)`

上下文管理器，生成 `StreamHandle` 用于流式输出。参数与 `run()` 相同，但没有 `check`、`on_stdout`/`on_stderr`，且 `timeout` 默认为 `None`。

---

### `stream_async(cmd, *, ...)`

异步上下文管理器，生成 `AsyncStreamHandle`。参数与 `stream()` 相同。

---

### `RunResult`

冻结数据类，字段：`command`、`returncode`、`stdout`、`stderr`、`duration`、`pid`。

### `StreamHandle`

活动进程句柄，提供 `iter_lines(source="stdout")`、`iter_any()`、`kill()`、`returncode`、`pid`。

### `AsyncStreamHandle`

异步活动进程句柄，提供 `aiter_lines(source="stdout")`、`aiter_any()`、`kill()`、`returncode`、`pid`。

## 与竞品对比

| 特性 | zerodep runner | sh.py | Plumbum | subprocess（标准库） |
|------|---------------|-------|---------|---------------------|
| 依赖 | 无 | 无 | 无 | *（标准库）* |
| 跨平台 | 是 | 仅 Unix | 是 | 是 |
| 单文件 | 是 | 否 | 否 | *（标准库）* |
| 结构化结果 | `RunResult` 数据类 | 动态对象 | `Future` | `CompletedProcess` |
| 超时升级 | SIGTERM+SIGKILL | 基本 | 基本 | 仅 `TimeoutExpired` |
| 流式 + 捕获 | 同时进行 | 二选一 | 二选一 | 手动实现 |
| 异步支持 | 原生 `asyncio` | 仅后台 | 仅后台 | `asyncio.subprocess` |
| 环境控制 | `env`/`env_extra`/`env_remove` | `_env` 字典 | `TypedEnv` | `env` 字典 |
| 命令策略 | 白名单/黑名单 | 无 | 无 | 无 |
| Shell 安全 | 永不使用 `shell=True` | 永不使用 | 永不使用 | 可使用 `shell=True` |
| 魔法 API | 无 | `sh.git()` | `local["git"]` | 无 |

## 性能测试

与 `sh` 和原生 `subprocess` 在简单命令、输出捕获、标准输入、流式输出、环境变量传递等场景下进行了对比测试。

详见 [Runner 性能测试](../benchmarks/runner.md)。
