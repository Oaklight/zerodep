---
title: FAQ
---

# FAQ

## What Python versions are supported?

zerodep requires **Python 3.10+**. The codebase uses modern language features such as `match/case` statements, `X | Y` union type syntax, and other 3.10+ constructs. Earlier Python versions are not supported.

## How do I update a module?

Run `zerodep update <module>` to pull the latest version from the manifest. Alternatively, you can re-download the `.py` file from the repository and replace the one in your project manually.

## Can I use multiple modules together?

Yes. Some modules depend on each other — for example, `sse` depends on `httpclient`, and `a2a` depends on `jsonrpc`. The CLI resolves dependencies automatically when you use `zerodep add`, so all required files are fetched together.

## How do I handle module dependencies?

When module A depends on module B, both `.py` files must be present in your project. The `zerodep add` command handles this automatically by resolving the dependency graph and downloading all required modules. If you copy files manually, check each module's frontmatter for its `dependencies` field.

## Are these modules production-ready?

Every module is correctness-tested against its reference library (e.g. `yaml` against PyYAML, `jsonx` against `json5`) and includes performance benchmarks. That said, they are stdlib-only reimplementations — evaluate the test coverage and benchmark results against your specific requirements before adopting them in production.

## Why not publish on PyPI?

zerodep's core philosophy is **zero-dependency, single-file modules**. Publishing on PyPI would introduce packaging, versioning, and dependency management overhead that contradicts this goal. The CLI already provides a `pip`-like experience (`zerodep add`, `zerodep update`, `zerodep list`) without requiring any of that machinery.

## How do I contribute?

Contributions are welcome! Visit the [GitHub repository](https://github.com/Oaklight/zerodep) to file issues or open pull requests. Before contributing a new module or modifying an existing one, read the [Internal Conventions](internals.md) page for coding standards, frontmatter format, testing expectations, and naming rules.
