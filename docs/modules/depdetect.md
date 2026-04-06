# Dependency Detection

Dependency detection and verification — zero dependencies, stdlib only, Python 3.10+.

## Overview

Parse dependency information from Python source code, requirements files, and free-text compatibility strings. Verify that binaries, Python packages, and environment variables are present on the current system.

| File | Description | Dependencies |
|------|-------------|--------------|
| `depdetect.py` | Dependency detection and verification | None (stdlib only) |

**Key capabilities:**

- Parse `import` / `from ... import` statements via AST, filtering stdlib automatically
- Parse `requirements.txt` files with version constraints and extras
- Parse free-text compatibility strings (e.g. `"Python 3.10+, pandoc >= 3.0"`)
- Extract binary hints from `allowed-tools` fields (e.g. `Bash(git:* docker:*)`)
- Resolve import name ↔ pip package name (3-level fallback: metadata → static map → heuristic)
- Check binary availability via `shutil.which()` with cross-platform alias support
- Check Python package importability via `importlib.util.find_spec()`
- Get binary version strings with timeout-protected subprocess calls
- Aggregate dependency checks into a structured report

## How to Use in Your Project

Copy the single `.py` file into your project:

```bash
cp depdetect/depdetect.py your_project/
```

Or install via the CLI:

```bash
zerodep add depdetect
```

Then import directly:

```python
from depdetect import parse_imports, analyze_source, check_requirements
```

## Usage Examples

### Analyze Python Source Code

```python
from depdetect import parse_imports, analyze_source

# Extract third-party import names (stdlib filtered out)
imports = parse_imports("import requests\nimport os\nfrom PIL import Image\n")
# → {"requests", "PIL"}

# Resolve to pip-installable package names
pip_names = analyze_source("import yaml\nfrom PIL import Image\n")
# → {"pyyaml", "pillow"}
```

### Parse Requirements Files

```python
from depdetect import parse_requirements

reqs = parse_requirements("""
requests>=2.28.0
pillow>=10.0
python-dotenv[cli]>=1.0
# this is a comment
-r other-requirements.txt
""")
# → [Requirement("requests", "python", ">=", "2.28.0"),
#    Requirement("pillow", "python", ">=", "10.0"),
#    Requirement("python-dotenv", "python", ">=", "1.0", extras="cli")]
```

### Parse Compatibility Strings

```python
from depdetect import parse_compatibility

reqs = parse_compatibility("Python 3.10+, pandoc >= 3.0, Node.js >= 18")
# → [Requirement("Python", "runtime", ">=", "3.10"),
#    Requirement("pandoc", "binary", ">=", "3.0"),
#    Requirement("Node.js", "runtime", ">=", "18")]
```

### Extract Binary Hints from Tool Declarations

```python
from depdetect import parse_tool_hints

binaries = parse_tool_hints("Bash(git:* docker:* npm:*) Read Write")
# → ["git", "docker", "npm"]
```

### Resolve Import Names to pip Names

```python
from depdetect import resolve_pip_name

resolve_pip_name("PIL")     # → "pillow"
resolve_pip_name("yaml")    # → "pyyaml" (or "PyYAML" from metadata)
resolve_pip_name("dotenv")  # → "python-dotenv"
resolve_pip_name("bs4")     # → "beautifulsoup4"
```

### Check System Dependencies

```python
from depdetect import check_binary, check_python_package, get_binary_version, check_env_var

# Binary detection
path = check_binary("git")          # "/usr/bin/git" or None
path = check_binary("node.js")      # resolves alias → checks "node"

# Binary version
ver = get_binary_version("git")     # "2.43.0" or None

# Python package
ok = check_python_package("requests")  # True / False
ok = check_python_package("pillow")    # checks "PIL" internally

# Environment variable
ok = check_env_var("OPENAI_API_KEY")   # True if set and non-empty
```

### Full Dependency Check with Report

```python
from depdetect import Requirement, check_requirements

reqs = [
    Requirement("git", "binary", ">=", "2.0"),
    Requirement("requests", "python", ">=", "2.28"),
    Requirement("Python", "runtime", ">=", "3.10"),
    Requirement("OPENAI_API_KEY", "env"),
]

report = check_requirements(reqs)

if report.satisfied:
    print("All dependencies met!")
else:
    print("Missing dependencies:")
    for dep in report.missing:
        print(f"  - {dep.name}: {dep.message}")

print(report.summary())
# [OK] git (2.43.0): found at /usr/bin/git
# [OK] requests (2.31.0): importable
# [OK] Python (3.12.0): current interpreter
# [MISSING] OPENAI_API_KEY: OPENAI_API_KEY not set
#
# 3/4 dependencies satisfied.
```

## Name Resolution

The `resolve_pip_name()` function uses a three-level fallback to map import names to pip package names:

| Level | Source | Example |
|-------|--------|---------|
| 1. Metadata | `importlib.metadata` (installed packages) | Dynamic, environment-specific |
| 2. Static map | Built-in `_IMPORT_TO_PIP` dict (~10 entries) | `PIL` → `pillow`, `yaml` → `pyyaml` |
| 3. Heuristic | Replace `_` with `-` | `my_package` → `my-package` |

The reverse mapping (pip name → import name) is handled internally by `_PIP_TO_IMPORT` for functions like `check_python_package()`.

## Data Classes

| Class | Description |
|-------|-------------|
| `Requirement` | Parsed dependency (name, category, version constraint, extras) |
| `DependencyStatus` | Result of checking one dependency (found, version, path, message) |
| `DependencyReport` | Aggregated results with `.satisfied`, `.missing`, `.summary()` |

## API Reference

See the [API Reference](../api/depdetect.md) for full function signatures and docstrings.

## Benchmark

No benchmark is provided for this module. As a development tool for dependency detection with no direct third-party counterpart for performance comparison, benchmarking is not applicable -- see [Depdetect Benchmark](../benchmarks/depdetect.md) for details.
