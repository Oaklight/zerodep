---
title: Home
hide:
  - navigation
---

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

## Overview

Each module is a **self-contained single file** that you can copy directly into your project. No `pip install` required.

## Philosophy

- **Zero external dependencies** — only Python standard library
- **Single file** — copy one `.py` file into your project
- **Python 3.10+** — leverages modern Python features
- **Correctness first** — apple-to-apple tests against reference libraries
- **Performance parity** — benchmarked against popular alternatives ([live dashboard](https://oaklight.github.io/zerodep/dev/bench))
