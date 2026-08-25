# Internal Conventions

This page documents the cross-module implementation patterns used throughout zerodep. These are not shared runtime code — each module carries its own copy — but they follow standardized conventions so that every module reads as if written by the same author.

If you are contributing a new module or modifying an existing one, check whether your change touches one of the patterns below and follow the established convention.

## Pattern Overview

| # | Pattern | Status | Key Modules |
|---|---------|--------|-------------|
| 1 | [Optional Sibling Import](#optional-sibling-import) | Standardized | config, vcs, sse |
| 2 | [Terminal Color Detection](#terminal-color-detection) | Standardized | ansi, structlog, prompt |
| 3 | [Cleanup Semantics](#cleanup-semantics) | Standardized | httpclient, runner, scheduler, sse, vcs |
| 4 | [Explicit Injection](#explicit-injection) | Implemented | vcs, config, sse |
| 5 | [Subprocess Execution](#subprocess-execution) | Standardized | runner, vcs |
| 6 | [Sync/Async API Mirroring](#syncasync-api-mirroring) | Standardized | runner, httpclient |
| 7 | [Error Type Design](#error-type-design) | Standardized | all subsystem modules |
| 8 | [Large Module Internal Layering](#large-module-internal-layering) | Standardized | httpclient, runner, scheduler |

---

## Optional Sibling Import

### Problem

A zerodep module must work standalone when copied alone, but should auto-enhance when sibling modules are present alongside it.

### Canonical Recipe

Every sibling import follows this sequence:

1. **Compute sibling directory** — relative to `__file__`
2. **Insert into `sys.path`** — only once, only if needed
3. **Attempt import** — catch `ImportError`
4. **Set capability flag** — `_HAS_<NAME> = True/False`
5. **Defer errors** — raise user-friendly messages only when the capability is actually needed at runtime

Both **flat** and **nested** vendor layouts are supported:

- **Nested:** `yaml/yaml.py` alongside `config/config.py` (default repo layout)
- **Flat:** `_vendor/yaml.py` alongside `_vendor/config.py` (vendored into a project)

The `_ensure_sibling_path` helper adds both the module's own directory and the nested sibling path to `sys.path`:

```python
def _ensure_sibling_path(name: str) -> str:
    """Add sibling module paths to sys.path for flat and nested layouts."""
    base = os.path.dirname(os.path.abspath(__file__))
    for candidate in [base, os.path.normpath(os.path.join(base, "..", name))]:
        if candidate not in sys.path:
            sys.path.insert(0, candidate)
    return base
```

Then use it with lazy loading and deferred errors:

```python
def _load_yaml():
    _ensure_sibling_path("yaml")
    try:
        from yaml import load as _yaml_load
        return _yaml_load
    except ImportError as exc:
        raise NotImplementedError(
            "YAML support requires the zerodep yaml module. "
            "Place yaml/yaml.py alongside this file."
        ) from exc
```

#### Legacy pattern (pre-v2026.8.25)

Older modules may still use the manual path insertion pattern. This only supports the nested layout:

```python
# Only works for nested layout (yaml/yaml.py)
_sibling_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "yaml")
if _sibling_dir not in sys.path:
    sys.path.insert(0, _sibling_dir)
```

New modules should use `_ensure_sibling_path` instead.

### Naming Conventions

| Element | Convention | Examples |
|---------|-----------|----------|
| Path variable | `_<name>_dir` | `_yaml_dir`, `_diff_dir` |
| Capability flag | `_HAS_<NAME>` | `_HAS_YAML`, `_HAS_DIFF_MODULE` |
| Import alias | `from mod import x as _x` | `from yaml import load as _yaml_load` |

---

## Terminal Color Detection

### Problem

Terminal-facing modules must agree on whether to emit ANSI escape sequences, respecting user environment and OS signals.

### Canonical Precedence

All terminal modules use this priority order:

```
FORCE_COLOR  →  force ON
NO_COLOR     →  force OFF
isatty()     →  OFF if not a TTY
TERM=dumb    →  OFF
default      →  ON
```

### Reference Implementation

`ansi/ansi.py` is the reference for color detection. Other terminal modules (`structlog`, `prompt`) align to it.

### Capability Layering

| Module | Color Scope | Notes |
|--------|------------|-------|
| `ansi` | Full: named, bright, 256, hex, RGB, fg/bg | Reference implementation |
| `prompt` | 16 named colors; hex foreground when needed | Interactive layer |
| `structlog` | Fixed 16-color mapping | Log rendering; no custom palette |

---

## Cleanup Semantics

### Problem

Network, process, and streaming modules require resource cleanup that is often best-effort. Without conventions, the codebase drifts toward `except Exception: pass` everywhere, hiding resource hygiene issues.

### Three-Tier Classification

Every cleanup path in zerodep is classified into one of three tiers:

#### Tier 1 — Must Succeed

Failure means the object is left in an inconsistent or unsafe state. These paths **raise or propagate exceptions**.

**Typical scenarios:**

- Process termination with escalation (SIGTERM then SIGKILL)
- Connection pool finally-block management (return-or-close decision)
- Event loop closure
- Context manager delegation to close methods

**Code pattern:**

```python
# Tier 1: must-succeed — failure propagates
finally:
    if not streaming:
        pool.release(conn)
    else:
        conn.close()
```

#### Tier 2 — Best-Effort Observable

Failure does not affect correctness but signals a resource hygiene issue. These paths **log a warning or emit a diagnostic**.

**Typical scenarios:**

- Streaming response close with active connection
- Scheduler callback errors
- Pipe reader close during process teardown

**Code pattern:**

```python
# Tier 2: best-effort — log on failure
try:
    response.close()
except Exception:
    logger.debug("failed to close response for %s", url, exc_info=True)
```

#### Tier 3 — Best-Effort Silent

Failure is expected, harmless, and high-frequency. These are the **only** paths that may use bare `except Exception: pass`.

**Typical scenarios:**

- Stale connection eviction from pool during health check
- Secondary close on already-closed resource
- Temp file cleanup (`os.unlink` in finally)
- Bulk pool shutdown during interpreter exit

**Code pattern:**

```python
# Tier 3: best-effort-silent — expected failures
try:
    conn.close()
except Exception:
    pass
```

### Current Classification Map

| Module | Tier 1 (Must Succeed) | Tier 2 (Observable) | Tier 3 (Silent) |
|--------|----------------------|--------------------|-----------------|
| httpclient | `_sync_request` / `_async_request` finally, `Client.__exit__` | `StreamingResponse.close/aclose` | Pool acquire/release/close_all, proxy cleanup |
| runner | Process termination escalation, `stream()` / `stream_async()` context managers | Pipe reader `ValueError` | — |
| scheduler | Job status reset in finally, event loop close | Event listener errors, `on_success` / `on_error` callbacks | — |
| sse | `SSEClient.__exit__` / `AsyncSSEClient.__aexit__` | — | `_close_response` (reconnect) |
| vcs | — | — | `merge_file` temp file cleanup |

### Rules

1. **`except Exception: pass` is only acceptable for Tier 3** — truly harmless, expected failures
2. **Tier 2 must have a signal** — `logger.debug(...)` with `exc_info=True`, or `warnings.warn(ResourceWarning(...))`
3. **Cleanup structure is consistent** — mark state first, attempt release, then fallback

---

## Explicit Injection

### Problem

Sibling imports use `sys.path` manipulation to auto-discover neighboring modules. While convenient for copy-and-use scenarios, this creates implicit dependencies that are hard to test, may conflict with user code, and don't work when modules are embedded in larger packages.

### Solution: Three-State Injection Parameters

Modules that use sibling imports expose explicit injection parameters on their constructors. Each parameter uses a private `_Unset` sentinel class to distinguish three states:

| Value | Meaning |
|-------|---------|
| `_UNSET` (default) | Use sibling auto-discovery — current behavior, fully backward compatible |
| `None` | Explicitly disable the capability |
| Callable / dict | User-injected implementation — bypasses `sys.path` entirely |

### Sentinel Pattern

Each module defines its own `_Unset` singleton (no shared code across modules):

```python
class _Unset:
    """Sentinel indicating 'use default sibling auto-discovery'."""
    _instance: _Unset | None = None

    def __new__(cls) -> _Unset:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNSET"

_UNSET = _Unset()
```

Use `isinstance(value, _Unset)` for type narrowing (not `value is _UNSET`), so that `ty` can narrow the union correctly.

### Per-Module Injection Points

#### VCS — `merge_func`

`Mercurial` and `Jujutsu` accept a `merge_func` parameter for three-way merging. `Git` uses its own `git merge-file` CLI and does not need injection.

```python
from vcs import Mercurial

# Default: auto-discover sibling diff module
hg = Mercurial("/path/to/repo")

# Injected: use your own merge function
hg = Mercurial("/path/to/repo", merge_func=my_merge3)

# Disabled: merge_file() raises NotImplementedError
hg = Mercurial("/path/to/repo", merge_func=None)
```

The `detect()` function forwards `merge_func` to the backend it constructs.

#### Config — `loaders` and `dotenv_loader`

`Config` accepts two injection parameters:

- **`loaders`**: Override the file-format loader registry (default uses sibling yaml/jsonx modules)
- **`dotenv_loader`**: Override the dotenv loading mechanism (default uses sibling dotenv module)

```python
from config import Config

# Default: auto-discover sibling yaml, jsonx, dotenv
cfg = Config(config_path="settings.yaml")

# Injected: use custom loaders
cfg = Config(
    config_path="settings.yaml",
    loaders={".yaml": my_yaml_loader},
    dotenv_loader=my_dotenv_factory,
)

# Disabled: skip .env loading
cfg = Config(dotenv_loader=None)
```

#### SSE — `transport`

`SSEClient` and `AsyncSSEClient` accept a `transport` parameter that replaces the sibling `httpclient` dependency.

```python
from sse import SSEClient, AsyncSSEClient

# Default: auto-discover sibling httpclient
client = SSEClient("https://example.com/events")

# Injected: use your own HTTP GET function
client = SSEClient("https://example.com/events", transport=my_get_func)
```

The sync transport must accept `(url, *, headers, stream, timeout, verify)` and return an object with `.status_code`, `.ok`, `.close()`, and `.iter_lines()`. The async transport returns an object with `.aclose()` and `.aiter_lines()` instead.

When a custom transport is injected, reconnection error handling catches only stdlib `ConnectionError` and `OSError` (not httpclient-specific exceptions).

### Design Rules

1. **Per-instance injection** — injection targets instance attributes, never module globals. This keeps things thread-safe.
2. **No new files** — sentinel classes are defined inline in each module. No shared `_core` or utility layer.
3. **Backward compatible** — all new parameters default to `_UNSET`, preserving existing behavior.
4. **`isinstance` for narrowing** — use `isinstance(value, _Unset)` rather than `value is _UNSET` so that type checkers can narrow the union.

---

## Error Type Design

### Problem

Subsystem modules each define domain-specific exceptions. Without conventions, exception naming, hierarchy depth, context fields, and message style diverge across modules, making it harder to catch, log, or display errors consistently.

### Canonical Convention

#### Hierarchy

Each subsystem module defines a single base exception that inherits from `Exception`. All module-specific exceptions inherit from that base. Maximum depth is two levels.

```python
class HttpClientError(Exception):
    """Base exception for all httpclient operations."""

class HTTPError(HttpClientError):
    """Raised on non-2xx status."""
    ...

class HttpConnectionError(HttpClientError):
    """Raised on connection failures."""
    ...
```

This lets callers catch all module errors with a single `except HttpClientError`, or target specific errors individually.

#### Naming

Exception names follow the pattern `<Module><Noun>Error`:

| Module | Base | Examples |
|--------|------|----------|
| httpclient | `HttpClientError` | `HTTPError`, `HttpConnectionError`, `HttpTimeoutError`, `TooManyRedirects` |
| runner | `RunnerError` | `CommandNotFoundError`, `CommandFailedError`, `CommandTimeoutError`, `CommandBlockedError` |
| scheduler | `SchedulerError` | `SchedulerAlreadyRunning`, `SchedulerNotRunning`, `JobNotFound`, `InvalidCronExpression` |
| vcs | `VCSError` | `BinaryNotFoundError`, `CommandError`, `NotARepoError` |
| sse | `SSEError` | `SSEConnectionError`, `SSEHTTPError` |
| config | `ConfigError` | `UndefinedValueError` |
| frontmatter | `FrontmatterError` | `HandlerError` |
| validate | `ValidationError` | *(standalone — uses `ErrorDetail` dataclass for structured reporting)* |
| retry | `RetryError` | *(standalone — carries `last_exception` and `attempts`)* |

**Rule**: never shadow Python builtins (`ConnectionError`, `TimeoutError`, etc.). Use module-prefixed names instead.

#### Context Fields

Exceptions store context as instance attributes set in `__init__`. Error messages are computed at construction time using f-strings.

```python
class HttpConnectionError(HttpClientError):
    def __init__(self, message: str, *, host: str = "", port: int = 0) -> None:
        self.host = host
        self.port = port
        self.message = message
        super().__init__(message)
```

Minimum context per error category:

| Error Category | Required Context |
|---------------|-----------------|
| Network/HTTP | `url`, `host`, `port`, or `status_code` |
| Command execution | `command`, `returncode`, key `stderr` |
| Scheduling | `job_id` or `cron expression` |
| Configuration | key name |
| File format | handler or format name |

#### Modules Without Custom Exceptions

Simple utility modules (`cache`, `search`, `dotenv`, `yaml`, `jsonx`, `aes`, `qr`, etc.) use standard library exceptions (`ValueError`, `KeyError`, `FileNotFoundError`). Custom exceptions are only needed when the module has domain-specific failure modes that callers need to distinguish.

---

## Subprocess Execution

### Problem

Both `runner` and `vcs` execute external processes, but with different conventions for binary discovery, timeout handling, encoding, and error reporting. Without alignment, new modules that need subprocess execution would have no clear reference to follow.

### Reference Implementations

`runner` is the full-featured general-purpose implementation. `vcs` is the domain-specific thin wrapper. Both serve as references for different use cases.

### Canonical Conventions

#### Binary Discovery

| Step | Description | Used By |
|------|------------|---------|
| 1 | Environment variable override (`ZERODEP_<NAME>_PATH`) | vcs |
| 2 | `shutil.which()` — cross-platform PATH search | runner, vcs |
| 3 | Platform-specific fallback directories (Windows only) | vcs |

`runner` exposes `which()` as a public utility. `vcs` uses the extended `_find_binary()` with env override and Windows fallbacks. Both are valid — simple modules can use step 2 alone; modules that need robust binary discovery on Windows should follow `vcs`.

#### Encoding

Default encoding is `utf-8`, explicit and configurable:

```python
def _run(cmd, *, encoding="utf-8", ...):
    result = subprocess.run(cmd, text=True, encoding=encoding, ...)
```

Both `runner` and `vcs` use this convention.

#### Timeout

- Default: `30.0` seconds, explicit and configurable per-call
- Error: raise a domain-specific timeout error with the command and timeout value

**Escalation** (runner only): For long-running or untrusted processes, `runner` uses SIGTERM → SIGKILL escalation with a configurable grace period (`kill_delay=5.0`). `vcs` uses simple `subprocess.run(timeout=...)` without escalation, which is appropriate for short-lived VCS commands.

#### Return Code Handling

Use an `allowed_returncodes` tuple to specify acceptable exit codes:

```python
def _run(cmd, *, allowed_returncodes=(0,), ...):
    ...
    if result.returncode not in allowed_returncodes:
        raise CommandError(cmd, result.returncode, result.stderr)
```

Some commands legitimately use non-zero codes (e.g., `git diff` returns 1 for "has changes"). Pass `allowed_returncodes=(0, 1)` for those cases.

#### Error Context on Timeout

Timeout errors must capture partial output when available and include the timeout value:

```python
except subprocess.TimeoutExpired as exc:
    raise CommandError(
        cmd, -1,
        (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
        timeout=timeout,
    ) from exc
```

#### Windows Support

On Windows, suppress console windows for background processes:

```python
if os.name == "nt":
    kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
```

### Intentional Differences

| Aspect | runner | vcs | Reason |
|--------|--------|-----|--------|
| SIGTERM→SIGKILL | Yes (5s grace) | No | VCS commands are short-lived; no need for graceful shutdown |
| Async support | Yes (`asyncio.create_subprocess_exec`) | No | VCS operations are fast enough for sync-only |
| Environment control | Full API (`env`, `env_extra`, `env_remove`) | Inherits current env | VCS commands need the user's PATH, HOME, etc. |
| Streaming output | Yes (callback + iterator) | No | VCS output is small enough to capture in full |

---

## Sync/Async API Mirroring

### Problem

Modules that offer both synchronous and asynchronous APIs need consistent naming, structure, and error behavior across both paths. Without conventions, sync/async pairs drift apart in subtle ways — different error messages, missing context fields, inconsistent cleanup order.

### Naming Conventions

#### Classes

All async class variants use the `Async` prefix:

| Sync | Async |
|------|-------|
| `Client` | `AsyncClient` |
| `StreamHandle` | `AsyncStreamHandle` |
| `SSEClient` | `AsyncSSEClient` |
| `EventSource` | `AsyncEventSource` |

#### Public Functions

Two conventions exist in the codebase:

| Module | Sync | Async | Convention |
|--------|------|-------|-----------|
| runner | `run` | `run_async` | Suffix `_async` |
| runner | `stream` | `stream_async` | Suffix `_async` |
| httpclient | `get` | `async_get` | Prefix `async_` |
| sse | `connect` | `async_connect` | Prefix `async_` |

Both are acceptable for existing APIs. **For new code, prefer the `_async` suffix** (`foo_async`) as it reads more naturally and groups alphabetically with its sync counterpart.

#### Internal Functions

Use explicit `_sync_` / `_async_` prefixes:

```python
def _sync_request(method, url, ...):    ...
async def _async_request(method, url, ...):    ...
```

### Structural Conventions

#### Shared Logic

Extract request validation, input parsing, and policy checks into sync-only helpers that both paths call:

```python
def _validate_command(cmd, policy):   ...  # called by both run() and run_async()
```

#### Phase Annotations

Long sync/async function pairs use matching phase comments to maintain alignment:

```python
# Sync path
def _sync_request(...):
    # Phase 1: build URL
    # Phase 2: set headers
    # Phase 3: connect
    # Phase 4: send request
    ...

# Async path
async def _async_request(...):
    # Phase 1: build URL
    # Phase 2: set headers
    # Phase 3: connect (asyncio.open_connection)
    # Phase 4: send request (writer.write)
    ...
```

This makes it easy to audit whether both paths handle the same cases.

#### Error Behavior

Both paths must raise the same exception types with the same context fields. The exception classes themselves are sync — only the code that raises them differs:

```python
# Both paths raise the same error type
raise HttpTimeoutError(msg, url=url, timeout=timeout)
```

#### Context Managers

Sync classes implement `__enter__` / `__exit__`. Async classes implement `__aenter__` / `__aexit__`. Both delegate to the same `close()` / `aclose()` method.

### Current Module Coverage

| Module | Sync API | Async API | Shared Core |
|--------|----------|-----------|-------------|
| httpclient | `Client`, `get`/`post`/... | `AsyncClient`, `async_get`/`async_post`/... | URL building, header setup, auth |
| runner | `run`, `stream` | `run_async`, `stream_async` | Command parsing, policy validation, env building |
| sse | `SSEClient`, `connect` | `AsyncSSEClient`, `async_connect` | `_SSEParser`, `SSEEvent` dataclass |
| scheduler | `Scheduler` (unified) | *(async jobs run in isolated event loops)* | Single class handles both |

---

## Large Module Internal Layering

### Problem

Subsystem modules (`httpclient`, `runner`, `scheduler`) are 1000+ LOC single files. Without internal structure, navigation is difficult, sync/async paths are hard to audit side by side, and contributors cannot quickly locate the right section.

### Section Marker Convention

Each large module uses horizontal-rule comments to divide the file into named sections:

```python
# ── Section Name ──────────────────────────────────────────────────────
```

The trailing dashes extend to column 72 for visual consistency. All sections use this format.

### Canonical Section Order

Sections follow a top-down dependency order — each section only references items defined above it:

| Order | Section | Contents |
|-------|---------|----------|
| 1 | Imports | stdlib, then conditional sibling imports |
| 2 | Constants / Defaults | Module-level constants, default values |
| 3 | Exceptions | Exception class hierarchy |
| 4 | Data Models | Dataclasses, TypedDicts, named tuples |
| 5 | Internal Helpers | Private utility functions |
| 6 | Core Logic | Main implementation (sync block, then async block) |
| 7 | Public API | User-facing functions and classes |

Not every module needs all sections. Simple modules may skip sections 5–6 and jump straight to the public API.

### Phase Annotations

Inside long functions (especially sync/async transport pairs), use numbered phase comments to mark logical stages:

```python
async def _async_request(method, url, ...):
    # Phase 1: build URL and headers
    ...
    # Phase 2: authentication setup
    ...
    # Phase 3: acquire connection
    ...
    # Phase 4: send request
    ...
    # Phase 5: read response
    ...
    # Phase 6: handle redirects
    ...
```

Both sync and async paths use the same phase numbering. This makes it easy to `diff` or side-by-side audit the two paths.

### Current Module Structures

#### httpclient (12 sections)

`Imports → Constants → Exceptions → Data Models (Response) → Auth → Compression → Streaming Response → Connection Pools → Transport → Request Building → Public API Functions → Client Classes`

#### runner (14 sections)

`Imports → Defaults → Exceptions → Data Models → Platform → Environment → Command Parsing → Policy → Process Lifecycle → Sync Execution → Async Execution → Sync Streaming → Async Streaming → Public API`

#### scheduler (7 sections)

`Imports → Constants → Exceptions → Cron Parser → Triggers → Data Models → Scheduler Core`

### Rules

1. **Section markers are mandatory** for files over 500 LOC
2. **Section order follows dependency** — no forward references between sections
3. **Sync before async** — when a section has both sync and async variants, the sync block comes first
4. **Phase numbers match** — sync phase N and async phase N must handle the same logical stage
