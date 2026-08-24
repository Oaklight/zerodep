---
name: zerodep
version: 1.0.0
description: "Manage the zerodep module library: scaffold new modules, run tests and benchmarks, bump versions, regenerate manifest, check dependencies, and update bilingual docs. Use when the user asks to create/test/bump/release zerodep modules or manage the module registry."
---

# zerodep — zero-dependency Python module library

A growing library of stdlib-only, single-file Python modules. Each module is a self-contained `.py` file you copy (vendor) into your project — no `pip install` at runtime, no transitive dependencies, no supply-chain risk.

Repo: <https://github.com/Oaklight/zerodep>
Docs: [English](https://zerodep.readthedocs.io/en/) | [中文](https://zerodep.readthedocs.io/zh-cn/)

## When to activate

- User wants to install the zerodep CLI or vendor modules into a project.
- User asks what zerodep modules are (or are not), or how they differ from pip packages.
- User wants to add, update, or check for outdated vendored modules.
- User wants to contribute: fix a bug, improve a module, or add a new one.

## Installing the CLI

The CLI is a single-file Python script published on PyPI. It requires Python 3.10+.

```bash
pip install zerodep        # or: pipx install zerodep
```

The CLI itself has zero dependencies. It fetches the module registry from GitHub and copies `.py` files into your project. That's all it does — it is not a runtime dependency.

**Do NOT add `zerodep` to your project's `dependencies` in `pyproject.toml`.** The PyPI package is the CLI only — it contains no modules. Vendored modules are plain `.py` files in your source tree with zero imports outside stdlib. If you want the CLI available during development, put it in an optional dev group:

```toml
[project.optional-dependencies]
dev = ["zerodep", ...]
```

## Using the CLI

The CLI is self-documenting. Run `zerodep --help` to see all available subcommands, and `zerodep <subcommand> --help` for details on any specific command.

The typical workflow is: browse modules, pick what you need, vendor them into your project directory. Dependencies between modules are resolved automatically — if module A depends on module B, both are copied.

Quick reference:

```bash
zerodep list                        # Browse all modules by category
zerodep info sse                    # Show module details and deps
zerodep add sse retry -d lib/       # Copy sse + httpclient + retry to lib/
zerodep add sse --nested            # Copy into sse/ and httpclient/ subdirs
zerodep update sse -d lib/          # Update existing modules in lib/
zerodep outdated -d lib/            # Check for upstream changes in lib/
```

The `-d`/`--dir` flag is shared by `add`, `update`, and `outdated` — it specifies the target directory (defaults to `.`).

## What zerodep modules are

- **Single `.py` files** that implement functionality normally provided by third-party PyPI packages (YAML parsing, HTTP client, SSE, protobuf, etc.).
- **Stdlib only** — every module uses only Python's standard library. No `pip install` needed at runtime.
- **Vendored, not installed** — you copy the file into your project and import it directly. It becomes part of your source tree.
- **Independently versioned** — each module has its own SemVer version, independent of the project's CalVer releases.
- **Benchmarked** — correctness tests compare output against the reference library (PyYAML, httpx, pydantic, etc.); benchmarks measure performance parity.

## What zerodep modules are NOT

- **Not a framework** — there's no runtime, no global state, no plugin system. Each module is standalone.
- **Not a replacement for every library** — modules target the common 80% of each library's API surface. Edge cases or advanced features may not be covered.
- **Not installed via pip at runtime** — `pip install zerodep` installs the CLI tool only. The modules themselves are copied files.
- **Not a project dependency** — vendored files have no connection back to the zerodep package. They are your source code now.
- **Not automatically updated** — once vendored, the file is yours. Use the CLI to check for and pull newer versions when you choose to.

## Vendoring modules into your project

Once the CLI is installed, use it to browse, add, and update modules. The CLI's `--help` output explains all options.

The recommended convention is to vendor into a `_vendor/` directory inside your package, keeping vendored code separate from your own:

```bash
myproject/
  __init__.py
  app.py
  _vendor/          # zerodep modules go here
    yaml.py
    httpclient.py
    __init__.py     # empty, makes it a package
```

Then import with a relative path:

```python
# inside myproject/app.py
from ._vendor.yaml import load, dump

data = load("name: Alice\nage: 30")
print(data)  # {'name': 'Alice', 'age': 30}
```

The `_vendor` prefix signals these are internal vendored files, not part of your public API. Exclude the directory from linting and type-checking in `pyproject.toml`:

```toml
[tool.ruff]
exclude = ["*/_vendor"]

[tool.ty]
exclude = ["*/_vendor"]
```

The vendored file is plain Python — no magic, no runtime hooks. Read it, modify it, vendor it into wherever your project needs it.

## Contributing

### Setup

```bash
git clone https://github.com/Oaklight/zerodep.git
cd zerodep
pip install -e ".[dev]"
pre-commit install
```

### Fixing or improving an existing module

1. Make changes to `<module>/<module>.py` (stdlib only — no third-party imports).
2. Run tests: `make test-<module>`.
3. Run lint: `make lint`.
4. Bump the version via the CLI (see `zerodep bump --help`).
5. Regenerate the manifest: `make manifest`.
6. Open a PR with a clear description of what changed and why.

### Adding a new module

1. Scaffold via the CLI (see `zerodep new --help`).
2. Implement in `<name>/<name>.py` — Python stdlib only.
3. Write correctness tests in `<name>/test_<name>_correctness.py`.
4. If benchmarking against a reference library, add a `bench-<name>` optional dep in `pyproject.toml`.
5. Write benchmarks in `<name>/test_<name>_benchmark.py`.
6. Run `make test-<name>` and `make lint`.
7. Bump version and regenerate manifest.
8. Submit a PR.

### Module frontmatter

Every module file starts with a PEP 723-style metadata block:

```python
# /// zerodep
# version = "0.3.1"
# deps = ["httpclient"]
# tier = "subsystem"
# category = "serialization"
# ///
```

- **version**: managed by the CLI's bump command. Never edit manually.
- **deps**: inter-module dependencies. Must match actual imports from other zerodep modules.
- Do not edit `manifest.json` by hand — it is auto-generated.

### PR guidelines

- One feature or fix per PR.
- Branch naming: `feature/xxx`, `fix/xxx`, `docs/xxx`, `refactor/xxx`, `test/xxx`.
- Merge strategy: rebase (not squash).
- Ensure `make lint` and `make test-<module>` pass before submitting.
- AI-assisted contributions are welcome. No `Co-authored-by` tags for AI tools in commits; disclose in PR description if needed.
