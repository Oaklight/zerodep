# 伪终端传输

异步伪终端（PTY/ConPTY）传输 — 零依赖，仅用标准库，Python 3.10+。

> **替代:** `ptyprocess`、`pywinpty`（部分）

## 概述

`ptyx` 在伪终端上启动子进程，并通过 asyncio 接口暴露原始字节 I/O。PTY 让只能以终端方式运行的程序保持其交互行为：交互模式、提示符渲染、终端查询与粘贴处理。

按平台选择后端：

| 平台 | 后端 |
|------|------|
| POSIX | `pty.openpty` + `termios`/`fcntl`；子进程运行在独立会话中 |
| Windows | 通过 `ctypes` 调用 ConPTY（`CreatePseudoConsole`），无需第三方包 |

| 文件 | 说明 | 依赖 |
|------|------|------|
| `ptyx.py` | 跨平台 PTY/ConPTY 传输 | 无（仅标准库：`asyncio`、`ctypes`、`os`、`pty`、`termios`、`fcntl`、`threading`） |

## 主要特性

- **两个平台统一异步 API** -- `spawn`、`read`、`write`、`resize`、`wait`、`close`
- **POSIX 后端** -- 独立会话与进程组、`TIOCSWINSZ` 调整大小、终端查询应答（`CSI 6n`、`CSI c`）、`SIGTERM` → `SIGKILL` 结束进程
- **Windows 后端** -- 通过 `ctypes` 调用 ConPTY，不依赖 `pywinpty`；子进程以 `STARTF_USESTDHANDLES` 和空标准句柄创建，使其控制台绑定到伪终端
- **写入不截断** -- `write()` 为异步方法，循环处理部分写入与 `EAGAIN`
- **背压** -- 有界队列，持续输出的子进程不会无限占用内存
- **括号粘贴** -- 写入 `ESC[200~ ... ESC[201~` 即可向 TUI 粘贴
- **可靠清理** -- 先发 Ctrl+C，等待 `grace` 后终止进程并关闭伪终端

## 使用方式

将单个 `.py` 文件复制到项目中：

```bash
cp ptyx/ptyx.py your_project/
```

然后直接导入：

```python
from ptyx import PtyProcess
```

## 使用示例

### 读取命令输出

```python
import asyncio
import sys
from ptyx import PtyProcess

async def main():
    proc = await PtyProcess.spawn([sys.executable, "-c", "print('hello ptyx')"])
    out = b""
    while chunk := await proc.read():
        out += chunk
    print(out.decode())
    print(await proc.close())

asyncio.run(main())
```

### 交互式会话

```python
proc = await PtyProcess.spawn(["/bin/bash"], rows=40, cols=120)
await proc.write(b"echo hello\r")
chunk = await asyncio.wait_for(proc.read(), timeout=5)
print(chunk.decode(errors="replace"))
await proc.close()
```

### 向终端 UI 粘贴

```python
prompt = "解释这个仓库"
await proc.write(b"\x1b[200~" + prompt.encode() + b"\x1b[201~")
await asyncio.sleep(0.15)
await proc.write(b"\r")
```

### 调整大小

```python
proc.resize(30, 100)   # 行、列
```

### 上下文管理器

```python
async with await PtyProcess.spawn(["/bin/bash"]) as proc:
    await proc.write(b"exit\r")
```

## 平台说明

- **POSIX EOF** 与从端（slave）绑定，而不是子进程：当所有持有从端的进程关闭后，`read()` 返回 `b""`。存活的孙进程会让流一直打开，直到 `close()`。
- **Windows EOF** 在子进程退出且 ConPTY 的最后输出排空后（最多 0.5 秒）返回。
- **无控制终端**：子进程是会话首进程但没有设置 `TIOCSCTTY`，因此 `/dev/tty` 不可用。需要它的程序（`sudo`、`ssh` 密码提示）需要真实终端；agent CLI 只使用 stdin/stdout。
- **写入时保持读取**：等待的是可写的主端，回显输入的子进程可能填满输出侧。
- **要求**：Python 3.10+；Windows 10 1809 或更高版本（ConPTY）。
