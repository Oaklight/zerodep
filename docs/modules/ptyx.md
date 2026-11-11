# PTY Transport

Async pseudo-terminal (PTY/ConPTY) transport — stdlib only, Python 3.10+.

> **Replaces:** `ptyprocess`, `pywinpty` (partial)

## Overview

`ptyx` spawns a child process on a pseudo-terminal and exposes raw byte I/O through an asyncio API. A PTY is what makes terminal-only programs behave as they do for a person: interactive mode, prompt rendering, terminal queries, and paste handling.

The backend is selected per platform:

| Platform | Backend |
|----------|---------|
| POSIX | `pty.openpty` plus `termios`/`fcntl`; the child runs in its own session |
| Windows | ConPTY (`CreatePseudoConsole`) through `ctypes`; no third-party package |

| File | Description | Dependencies |
|------|-------------|--------------|
| `ptyx.py` | Cross-platform PTY/ConPTY transport | None (stdlib only: `asyncio`, `ctypes`, `os`, `pty`, `termios`, `fcntl`, `threading`) |

## Key Features

- **One async API on both platforms** -- `spawn`, `read`, `write`, `resize`, `wait`, `close`
- **POSIX backend** -- own session and process group, `TIOCSWINSZ` resize, cursor-position replies (`CSI 6n` only), `SIGTERM` → `SIGKILL` teardown
- **Windows backend** -- ConPTY via `ctypes`, no `pywinpty`; the child is created with `STARTF_USESTDHANDLES` and NULL standard handles so its console binds to the pseudoconsole
- **No silent truncation** -- `write()` is async and loops over partial writes and `EAGAIN`
- **Backpressure** -- bounded queues; a chatty child cannot grow memory without bound, and the ConPTY reader blocks on the queue instead of dropping output
- **Failures are distinguishable** -- a ConPTY pipe failure while the child runs raises `PtyReadError`; it is never reported as end-of-stream
- **Bracketed paste** -- write the usual `ESC[200~ ... ESC[201~` sequence to paste into TUIs
- **Reliable teardown** -- Ctrl+C first, then terminate and close the pseudoconsole after `grace`

## How to Use in Your Project

Copy the single `.py` file into your project:

```bash
cp ptyx/ptyx.py your_project/
```

Then import directly:

```python
from ptyx import PtyProcess
```

## Usage Examples

### Read a command's output

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

### Interactive session

```python
proc = await PtyProcess.spawn(["/bin/bash"], rows=40, cols=120)
await proc.write(b"echo hello\r")
chunk = await asyncio.wait_for(proc.read(), timeout=5)
print(chunk.decode(errors="replace"))
await proc.close()
```

### Paste into a terminal UI

```python
prompt = "Explain this repository"
await proc.write(b"\x1b[200~" + prompt.encode() + b"\x1b[201~")
await asyncio.sleep(0.15)
await proc.write(b"\r")
```

### Resize

```python
proc.resize(30, 100)   # rows, cols
```

### Context manager

```python
async with await PtyProcess.spawn(["/bin/bash"]) as proc:
    await proc.write(b"exit\r")
```

## Errors

| Exception | When | Base |
|-----------|------|------|
| `PtyStartupError` | The pseudo-terminal or the child cannot be created, on either platform | `RuntimeError` |
| `PtyReadError` | A ConPTY pipe call (`PeekNamedPipe`, `ReadFile`) fails while the child is still running | `RuntimeError` |

Both are in `__all__`. A pipe failure during teardown, or after the child has exited, is the normal end of stream and returns `b""` instead.

## Terminal Queries

The POSIX backend answers `CSI 6n` (cursor position request) with `ESC[1;1R`. It leaves every other query unanswered -- DA1 (`CSI c`), DA2 (`CSI > c`) and kitty-keyboard queries included. A fixed reply would claim capabilities the pseudo-terminal does not have, and a program handles a missing reply better than a wrong one.

## Platform Notes

- **POSIX EOF** is tied to the slave, not the child: `read()` returns `b""` when every holder of the slave closes it. A surviving grandchild keeps the stream open until `close()`. `EIO` from the master is treated as that same end of stream.
- **Windows EOF** is after the child exits and ConPTY's final output is drained (bounded at 0.5 s). A pipe failure while the child still runs is not EOF: the blocked `read()` raises `PtyReadError`.
- **Read errors are per terminal**: once `PtyReadError` is raised, later reads raise it again rather than returning `b""`. Recreate the process.
- **No controlling terminal**: the child is a session leader without `TIOCSCTTY`, so `/dev/tty` is unavailable. Programs that require it (`sudo`, `ssh` password prompts) need a real terminal; agent CLIs use stdin/stdout only.
- **Keep reading while writing**: the wait is for a writable master, so a child that echoes input can fill the output side.
- **Requirements**: Python 3.10+; Windows 10 1809 or later (ConPTY).
