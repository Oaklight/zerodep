---
title: Installation
---

# Installation

## How It Works

zerodep modules are standalone, single `.py` files with zero external dependencies. You copy the file you need into your project directory and `import` it — no package manager required at runtime. This makes zerodep ideal for constrained environments, bootstrapping scripts, and supply-chain-sensitive projects where minimizing third-party code is a priority.

## Using the CLI (Recommended)

The easiest way to obtain modules is via the `zerodep` CLI:

```bash
pip install zerodep
zerodep add yaml retry
```

This fetches `yaml.py` and `retry.py` into your current directory, automatically resolving any inter-module dependencies. The CLI also handles caching, multi-source fallback, and offline mode.

See [CLI Tool](cli.md) for the full command reference.

## Manual Download

If you prefer not to install the CLI, you can download individual module files directly:

```bash
curl -O https://raw.githubusercontent.com/Oaklight/zerodep/master/yaml/yaml.py
```

Or clone the repository and copy the files you need:

```bash
git clone https://github.com/Oaklight/zerodep.git
cp zerodep/yaml/yaml.py ./
```

## Dependency Resolution

Some zerodep modules depend on other zerodep modules. The full dependency table is:

| Module | Depends On |
|--------|------------|
| `a2a` | `jsonrpc` |
| `acp` | `jsonrpc` |
| `config` | `dotenv`, `yaml`, `jsonc` |
| `frontmatter` | `yaml` |
| `skills` | `frontmatter`, `search` |
| `sse` | `httpclient` |
| `vcs` | `diff` |

All other modules are fully standalone with no inter-module dependencies.

**When using the CLI**, dependencies are resolved and fetched automatically — you just `zerodep add sse` and both `sse.py` and `httpclient.py` appear.

**When downloading manually**, you must fetch dependencies yourself. Check the `# /// zerodep` frontmatter block at the top of each module file for its `deps` list.

## Project Integration Patterns

### Flat (default)

Copy `.py` files directly into your project root:

```bash
zerodep add yaml retry
```

```
my-project/
├── main.py
├── yaml.py
└── retry.py
```

### Vendor Directory

Use `-d` to place modules in a dedicated directory:

```bash
zerodep add yaml retry -d vendor/
```

```
my-project/
├── main.py
└── vendor/
    ├── yaml.py
    └── retry.py
```

Then import with `from vendor.yaml import ...` or add `vendor/` to your Python path.

### Nested (Subdirectory Structure)

Use `--nested` to mirror the repository's directory layout:

```bash
zerodep add yaml retry --nested
```

```
my-project/
├── main.py
├── yaml/
│   └── yaml.py
└── retry/
    └── retry.py
```

This is useful when modules include variant files (e.g., `aes/aes.py` and `aes/aes_openssl.py`). You can combine `-d` and `--nested` together (e.g., `zerodep add sse -d lib/ --nested`).
