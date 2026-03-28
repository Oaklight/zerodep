# Runner

Zero-dependency structured subprocess execution -- stdlib only, Python 3.10+.

## Overview

The Runner module provides a structured way to execute external commands with timeout escalation, streaming output, environment isolation, and cross-platform support -- all without any third-party dependencies.

| File | Description | Dependencies |
|------|-------------|--------------|
| `runner.py` | Pure Python implementation | None (stdlib only: `subprocess`, `asyncio`, `shlex`, `shutil`, `threading`, `time`) |

Key features:

- **Sync + async** execution with identical APIs
- **Streaming output** via callbacks or context-manager iterators
- **SIGTERM to SIGKILL timeout escalation** with configurable kill delay
- **Environment control** -- replacement, augmentation, or variable removal
- **Command policy** -- allowlist/blocklist for safety guardrails
- **Structured results** -- `RunResult` dataclass with stdout, stderr, returncode, duration, pid
- **Cross-platform** -- Windows `CREATE_NO_WINDOW`, platform-aware quoting

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp runner/runner.py your_project/
```

Then import directly:

```python
from runner import run, run_async, stream, stream_async
```

## Usage Examples

### Basic Command Execution

```python
from runner import run

# List form (recommended)
result = run(["echo", "hello", "world"])
print(result.stdout)      # "hello world\n"
print(result.returncode)  # 0
print(result.duration)    # 0.003

# String form (auto-split via shlex)
result = run("echo hello world")
```

### Stdin Input

```python
from runner import run

result = run(
    ["python3", "-c", "import sys; print(sys.stdin.read().upper())"],
    input="hello world",
)
print(result.stdout)  # "HELLO WORLD\n"
```

### Error Handling

```python
from runner import run, CommandFailedError, CommandTimeoutError

# check=True by default -- raises on non-zero exit
try:
    run(["false"])
except CommandFailedError as e:
    print(e.result.returncode)  # 1
    print(e.result.stderr)

# Suppress the exception
result = run(["false"], check=False)
print(result.returncode)  # 1
```

### Timeout with Kill Escalation

```python
from runner import run, CommandTimeoutError

try:
    run(["sleep", "60"], timeout=5.0, kill_delay=2.0)
except CommandTimeoutError as e:
    print(f"Timed out after {e.timeout}s")
    print(e.partial_stdout)  # Any output before timeout
```

The timeout strategy is:

1. Wait up to `timeout` seconds
2. Send SIGTERM (graceful shutdown)
3. Wait up to `kill_delay` seconds
4. Send SIGKILL (forced termination)

### Environment Control

```python
from runner import run

# Add variables to inherited environment
result = run(["env"], env_extra={"MY_VAR": "hello"})

# Remove sensitive variables
result = run(["env"], env_remove=["SECRET_KEY", "AWS_ACCESS_KEY_ID"])

# Complete replacement (clean slate)
result = run(["env"], env={"PATH": "/usr/bin", "HOME": "/tmp"})

# All three compose: start from env, remove, then add
result = run(
    ["env"],
    env={"PATH": "/usr/bin"},
    env_remove=["OLDVAR"],
    env_extra={"NEWVAR": "value"},
)
```

### Streaming with Callbacks

```python
from runner import run

# Stream stdout while still capturing full output
lines = []
result = run(
    ["make", "build"],
    on_stdout=lambda line: print(f"[build] {line}", end=""),
    on_stderr=lambda line: print(f"[ERR]   {line}", end=""),
)
# result.stdout contains the full captured output
```

### Streaming with Context Manager

```python
from runner import stream

# Iterate over stdout lines
with stream(["make", "build"]) as proc:
    for line in proc.iter_lines():
        print(f"[build] {line}", end="")
print(f"Exit code: {proc.returncode}")

# Interleave stdout and stderr
with stream(["make", "build"]) as proc:
    for source, line in proc.iter_any():
        prefix = "[OUT]" if source == "stdout" else "[ERR]"
        print(f"{prefix} {line}", end="")
```

### Async Execution

```python
import asyncio
from runner import run_async, stream_async

async def main():
    # Basic async execution
    result = await run_async("ls -la")
    print(result.stdout)

    # Async streaming
    async with stream_async(["make", "build"]) as proc:
        async for line in proc.aiter_lines():
            print(line, end="")

asyncio.run(main())
```

### Command Policy (Allowlist/Blocklist)

```python
from runner import run, CommandBlockedError

# Only allow specific commands
try:
    run(["rm", "-rf", "/"], allowed_commands=["echo", "cat", "ls"])
except CommandBlockedError as e:
    print(f"{e.command} blocked: {e.reason}")

# Block dangerous commands
run(["echo", "safe"], blocked_commands=["rm", "dd", "mkfs"])
```

### Utilities

```python
from runner import shell_split, shell_quote, which

# Parse a shell string into arguments
args = shell_split('git commit -m "hello world"')
# ['git', 'commit', '-m', 'hello world']

# Quote arguments for safe shell interpolation
quoted = shell_quote("hello world", "it's fine")
# "'hello world' \"it's fine\""

# Locate a command on PATH
path = which("git")
# '/usr/bin/git'
```

## API Reference

### `run(cmd, *, ...)`

Run a command synchronously and return a `RunResult`.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `cmd` | `str \| Sequence[str]` | *(required)* | Command as string (auto-split) or argument list |
| `input` | `str \| None` | `None` | Text to send on stdin |
| `cwd` | `str \| Path \| None` | `None` | Working directory |
| `env` | `dict[str, str] \| None` | `None` | Complete replacement environment |
| `env_extra` | `dict[str, str] \| None` | `None` | Extra vars merged into inherited env |
| `env_remove` | `Sequence[str] \| None` | `None` | Vars to strip from inherited env |
| `timeout` | `float \| None` | `30.0` | Max seconds to wait; `None` = no limit |
| `kill_delay` | `float` | `5.0` | Seconds between SIGTERM and SIGKILL |
| `check` | `bool` | `True` | Raise `CommandFailedError` on non-zero exit |
| `encoding` | `str` | `"utf-8"` | Text encoding for stdout/stderr |
| `on_stdout` | `Callable \| None` | `None` | Per-line stdout callback |
| `on_stderr` | `Callable \| None` | `None` | Per-line stderr callback |
| `allowed_commands` | `Sequence[str] \| None` | `None` | Allowlist of permitted commands |
| `blocked_commands` | `Sequence[str] \| None` | `None` | Blocklist of rejected commands |

**Returns:** `RunResult`

**Raises:** `CommandNotFoundError`, `CommandFailedError`, `CommandTimeoutError`, `CommandBlockedError`, `ValueError`

---

### `run_async(cmd, *, ...)`

Async counterpart of `run()`. Same parameters and return type.

---

### `stream(cmd, *, ...)`

Context manager yielding a `StreamHandle` for streaming output. Same parameters as `run()` except no `check` or `on_stdout`/`on_stderr`, and `timeout` defaults to `None`.

---

### `stream_async(cmd, *, ...)`

Async context manager yielding an `AsyncStreamHandle`. Same parameters as `stream()`.

---

### `RunResult`

Frozen dataclass with fields: `command`, `returncode`, `stdout`, `stderr`, `duration`, `pid`.

### `StreamHandle`

Live process handle with `iter_lines(source="stdout")`, `iter_any()`, `kill()`, `returncode`, `pid`.

### `AsyncStreamHandle`

Async live process handle with `aiter_lines(source="stdout")`, `aiter_any()`, `kill()`, `returncode`, `pid`.

## Comparison with Alternatives

| Feature | zerodep runner | sh.py | Plumbum | subprocess (stdlib) |
|---------|---------------|-------|---------|---------------------|
| Dependencies | None | None | None | *(stdlib)* |
| Cross-platform | Yes | Unix only | Yes | Yes |
| Single file | Yes | No | No | *(stdlib)* |
| Structured result | `RunResult` dataclass | Dynamic | `Future` | `CompletedProcess` |
| Timeout escalation | SIGTERM+SIGKILL | Basic | Basic | `TimeoutExpired` only |
| Streaming + capture | Both simultaneously | Either/or | Either/or | Manual |
| Async support | Native `asyncio` | Background only | Background | `asyncio.subprocess` |
| Environment control | `env`/`env_extra`/`env_remove` | `_env` dict | `TypedEnv` | `env` dict |
| Command policy | Allowlist/blocklist | None | None | None |
| Shell safety | Never `shell=True` | Never | Never | `shell=True` available |
| Magic API | No | `sh.git()` | `local["git"]` | No |

## Benchmark

See [Runner Benchmark](../benchmarks/runner.md) for detailed performance comparison against `sh` and raw `subprocess`.
