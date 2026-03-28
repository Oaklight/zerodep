# Design Philosophy

## Why zerodep?

Modern Python development often means pulling in a tree of transitive dependencies for a single feature. A YAML parser brings in a C extension build chain. An HTTP client pulls in half a dozen sub-packages. Each dependency is a potential supply-chain risk, a version conflict, and a maintenance burden.

**zerodep** takes a different approach: every module is a self-contained, single `.py` file that uses only the Python standard library. You copy what you need, commit it alongside your code, and move on.

## Core Principles

### Zero External Dependencies

Every module depends only on Python's standard library (`urllib`, `json`, `ast`, `re`, `ssl`, `struct`, etc.). No `pip install` required at runtime. This makes zerodep modules ideal for:

- **Constrained environments** — air-gapped servers, embedded systems, minimal containers
- **Bootstrapping tools** — scripts that must run before `pip` is available
- **Supply-chain-sensitive projects** — fewer third-party packages to audit

### Single File per Module

Each module is one `.py` file (occasionally two for a variant like `aes_openssl.py`). This means:

- **Vendor easily** — `cp scheduler.py your_project/`
- **Audit easily** — one file to read, no hidden package structure
- **Version easily** — every module carries its own `__version__`

### Correctness First, Then Performance

Every module is tested apple-to-apple against the reference library it reimplements (`PyYAML`, `httpx`, `pydantic`, etc.). Correctness tests run first; benchmark comparisons come second. The goal is not to beat the reference — it is to be a faithful, usable replacement.

### Explicit Dependencies Between Modules

Some modules build on others:

| Module | Depends on |
|--------|-----------|
| `sse` | `httpclient` |
| `vcs` | `diff` |

These relationships are declared in each module's source via `__deps__`:

```python
__deps__: list[str] = ["httpclient"]
```

The [CLI tool](cli.md) resolves these automatically when you add a module.

## When to Use zerodep

zerodep modules are a good fit when:

- You need **one feature** from a large library (e.g., YAML parsing, retry logic)
- You want to **minimize your dependency tree** for security or operational reasons
- You are building **CLI tools or scripts** that should run with just Python
- You work in an environment where **`pip install` is not available**

## When NOT to Use zerodep

Prefer the established library when:

- You need **full spec compliance** (e.g., the entire YAML 1.2 spec, not just the common subset)
- You need **C-extension performance** for hot loops (e.g., `pycryptodome`'s AES vs. our pure-Python AES)
- You rely on **ecosystem integrations** (e.g., Django's ORM expects `psycopg2`, not a hand-rolled driver)

## Module Lifecycle

```
Idea → Implement → Correctness tests → Benchmarks → Documentation → Manifest
```

1. **Implement** — write a single `.py` file with `__version__` and `__deps__`
2. **Test** — add `test_<module>_correctness.py` comparing against the reference library
3. **Benchmark** — add `test_<module>_benchmark.py` with `pytest-benchmark`
4. **Document** — add module page, API reference, and benchmark results to docs
5. **Register** — run `zerodep manifest` to regenerate `manifest.json`
