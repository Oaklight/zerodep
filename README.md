# zerodep

[![PyPI](https://img.shields.io/pypi/v/zerodep?color=green)](https://pypi.org/project/zerodep/)
[![GitHub Release](https://img.shields.io/github/v/release/Oaklight/zerodep?color=green)](https://github.com/Oaklight/zerodep/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/pypi/pyversions/zerodep?color=green)](https://pypi.org/project/zerodep/)
[![CI](https://img.shields.io/github/actions/workflow/status/Oaklight/zerodep/ci.yml?label=CI)](https://github.com/Oaklight/zerodep/actions/workflows/ci.yml)
[![Benchmarks](https://img.shields.io/badge/benchmarks-live-blue)](https://oaklight.github.io/zerodep/dev/bench)
[![Docs](https://img.shields.io/readthedocs/zerodep)](https://zerodep.readthedocs.io)
[![arXiv](https://img.shields.io/badge/arXiv-2605.21405-b31b1b.svg)](https://arxiv.org/abs/2605.21405)

Zero-dependency, single-file Python implementations of popular libraries — stdlib only, benchmarked for performance parity, Python 3.10+.

零依赖、单文件的 Python 常用库实现 —— 仅使用标准库，性能对标主流库，支持 Python 3.10+。

[English Docs](https://zerodep.readthedocs.io/en/) | [中文文档](https://zerodep.readthedocs.io/zh-cn/)

## Quick Start

```bash
pip install zerodep          # install the CLI
zerodep add yaml retry       # copy modules into your project
```

```python
from yaml import load, dump

data = load("name: Alice\nage: 30")
print(data)  # {'name': 'Alice', 'age': 30}
```

Each module is a **self-contained single `.py` file** — copy it into your project and import. No `pip install` needed at runtime.

## Modules

Modules span Agent Protocols, Web & Networking, Data Formats, Data Validation, Text & Markup, Search & Retrieval, Configuration, CLI & Terminal, Security, and Infrastructure & Tools.

See the [full module list](https://zerodep.readthedocs.io/en/latest/modules/) for details, versions, and benchmarks.

## Versioning

- **Project**: [CalVer](https://calver.org/) `YYYY.M.D` (e.g., `2026.4.15`)
- **Modules**: independent [SemVer](https://semver.org/) per module (e.g., `0.4.1`)

Releases are automated via the [Release workflow](https://github.com/Oaklight/zerodep/actions/workflows/release.yml) — lint, test, bump module versions, tag, and create a GitHub Release in one step.

## Documentation

- **English**: [zerodep.readthedocs.io/en/](https://zerodep.readthedocs.io/en/)
- **中文**: [zerodep.readthedocs.io/zh-cn/](https://zerodep.readthedocs.io/zh-cn/)
- **Benchmarks**: [Live benchmark dashboard](https://oaklight.github.io/zerodep/dev/bench)

## License

[MIT](LICENSE)
