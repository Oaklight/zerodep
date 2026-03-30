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
| 5 | Subprocess Execution | Planned | runner, vcs |
| 6 | Sync/Async API Mirroring | Planned | runner, httpclient |
| 7 | Error Type Design | Planned | all subsystem modules |
| 8 | Large Module Internal Layering | Planned | httpclient, runner, scheduler |

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

```python
# Step 1-2: locate sibling
_sibling_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "yaml")
if _sibling_dir not in sys.path:
    sys.path.insert(0, _sibling_dir)

# Step 3-4: probe
try:
    from yaml import load as _yaml_load
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

# Step 5: deferred error (inside the function that needs it)
def load_yaml(path):
    if not _HAS_YAML:
        raise RuntimeError(
            "YAML support requires the zerodep yaml module. "
            "Copy yaml/yaml.py alongside this file."
        )
    ...
```

### Lazy Loading

Sibling modules are lazy-loaded to avoid import-time side effects. Instead of importing at module load, the import is deferred until the capability is first used:

```python
_yaml_mod = None

def _get_yaml():
    global _yaml_mod
    if _yaml_mod is None:
        _sibling_dir = os.path.join(os.path.dirname(__file__), "..", "yaml")
        if _sibling_dir not in sys.path:
            sys.path.insert(0, _sibling_dir)
        try:
            import yaml as _mod
            _yaml_mod = _mod
        except ImportError:
            raise RuntimeError("YAML support requires the zerodep yaml module.")
    return _yaml_mod
```

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

- **`loaders`**: Override the file-format loader registry (default uses sibling yaml/jsonc modules)
- **`dotenv_loader`**: Override the dotenv loading mechanism (default uses sibling dotenv module)

```python
from config import Config

# Default: auto-discover sibling yaml, jsonc, dotenv
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
