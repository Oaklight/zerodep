---
title: Migration Guide
---

# Migration Guide

This page documents breaking changes between zerodep versions and how to update your code.

## Migrating to 2026.4.11 (CalVer)

### Versioning Scheme Change

Starting with this release, the **project-level** version uses [CalVer](https://calver.org/) (`YYYY.M.patch`):

- `2026.4.11` — first stable release of April 2026
- `2026.4.1` — second release in the same month (if needed)
- `2026.5.0` — first release of May 2026

**Module-level** versions remain independent SemVer (e.g., `yaml` 0.3.0, `aes` 0.4.0). Each module's version tracks its own API evolution and is declared in the frontmatter `version` field.

**What this means for users:**

- `pip install zerodep` installs the CLI at the CalVer version
- Modules obtained via `zerodep add` carry their own SemVer version
- All modules within the same CalVer release are guaranteed compatible
- When copying modules manually, always use files from the same release

### Module Frontmatter Note

All modules now include a `note` field in their frontmatter:

```python
# /// zerodep
# version = "0.3.0"
# deps = ["dotenv", "yaml", "jsonc"]
# note = "Install/update via zerodep CLI (...). Manual copy may miss deps."
# ///
```

When copied via `zerodep add`, the note is automatically updated with the specific module name. **No code changes needed** — this is informational only.

### New Maintainer Commands

Three new CLI commands are available for module interdependency management:

- `zerodep version-check` — detect modules with code changes since their declared version
- `zerodep dep-graph` — visualize module dependency graph
- `zerodep dep-check` — run tests for changed modules and their downstream dependents

See [CLI Tool](cli.md) for usage details.

## Migrating to 0.3.0

### Type Annotations (Style Change)

All modules now use PEP 604 union syntax and PEP 585 built-in generics instead of `typing` aliases.

```python
# Before
from typing import Optional, Dict, List

def fetch(url: str, headers: Optional[Dict[str, str]] = None) -> List[str]: ...

# After
def fetch(url: str, headers: dict[str, str] | None = None) -> list[str]: ...
```

If you were importing type aliases from any zerodep module, update your code to match the new style. This requires Python 3.10+ at runtime, or `from __future__ import annotations` on 3.9.

### A2A and ACP: JSON-RPC Extraction

The JSON-RPC layer has been extracted into a shared `jsonrpc` module. If you use `a2a.py` or `acp.py`, you now also need `jsonrpc.py` alongside them.

```python
# Before: a2a.py was self-contained
project/
    a2a.py

# After: jsonrpc.py is a required sibling
project/
    a2a.py
    jsonrpc.py
```

`A2AError` now subclasses `JSONRPCException` from the `jsonrpc` module instead of defining its own base:

```python
# Before
except A2AError:  # standalone exception hierarchy

# After — still works, but the base class changed
from jsonrpc import JSONRPCException
except JSONRPCException:  # catches both A2A and ACP errors
```

ACP serialization methods have been unified into a single recursive `to_dict()` method. If you called any other serialization helpers, switch to `to_dict()`.

### New `__all__` Exports

All modules now define `__all__`. If you rely on `from module import *`, only explicitly exported names are available. Import any previously-implicit names by name:

```python
# Before — grabbed everything
from yaml import *

# After — if a helper is no longer in __all__, import it directly
from yaml import parse, dump, _internal_helper  # explicit import
```

### Frozen Dataclasses: `slots=True`

`slots=True` has been added to frozen dataclasses across modules. This improves memory usage but prevents adding dynamic attributes:

```python
# This now raises AttributeError
msg = A2AMessage(...)
msg.custom_field = "value"  # AttributeError: 'A2AMessage' has no __dict__
```

If you were attaching ad-hoc attributes to frozen dataclass instances, store them in a separate dict instead.

---

## Migrating to 0.2.2

### HTTP Client Exception Renames

Two built-in-shadowing exception names have been renamed:

| Old name | New name | Notes |
|---|---|---|
| `ConnectionError` | `HttpConnectionError` | Avoids shadowing the built-in |
| `TimeoutError` | `HttpTimeoutError` | Avoids shadowing the built-in |

The old names are kept as aliases but are deprecated and will be removed in a future release. Update your `except` clauses now:

```python
# Before
from httpclient import ConnectionError, TimeoutError

try:
    resp = fetch(url)
except ConnectionError:
    ...
except TimeoutError:
    ...

# After
from httpclient import HttpConnectionError, HttpTimeoutError

try:
    resp = fetch(url)
except HttpConnectionError:
    ...
except HttpTimeoutError:
    ...
```

### New Base Exceptions

Two new base exception classes have been introduced:

- `HttpClientError` -- base for all HTTP client exceptions. Use it to catch any HTTP-related error in a single clause.
- `ConfigError` -- base for all config module exceptions.

```python
# Catch any HTTP error generically
from httpclient import HttpClientError

try:
    resp = fetch(url)
except HttpClientError:
    ...
```

---

## Migrating to 0.2.0

### Module Metadata: PEP 723 Frontmatter

Module metadata has migrated from module-level attributes to PEP 723 inline script metadata (frontmatter comment block at the top of each file).

- `module.__version__` still works (re-exported for compatibility).
- `module.__deps__` is **removed**. Dependencies are now declared in the PEP 723 `# /// script` block:

```python
# Before (0.1.x)
__version__ = "0.1.5"
__deps__ = ["pycryptodome>=3.20"]

# After (0.2.0+) — top-of-file frontmatter
# /// script
# version = "0.2.0"
# deps = ["pycryptodome>=3.20"]
# ///
```

If you were reading `__deps__` programmatically, parse the frontmatter instead. The zerodep CLI provides `zerodep info <module>` for this purpose.

### CLI: Recursive Scanning

The CLI now supports recursive module scanning and nested directory structures. No code changes are required, but be aware that `zerodep list` may now return modules from subdirectories that were previously invisible.
