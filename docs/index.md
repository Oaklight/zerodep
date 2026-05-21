---
title: 首页
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

零依赖、单文件的 Python 常用库实现 —— 仅使用标准库，性能对标主流库，支持 Python 3.10+。

## 概述

每个模块都是一个**独立的单文件**，可以直接复制到你的项目中使用，无需 `pip install`。

## 设计理念

- **零外部依赖** —— 仅使用 Python 标准库
- **单文件** —— 复制一个 `.py` 文件到你的项目即可
- **Python 3.10+** —— 利用现代 Python 特性
- **正确性优先** —— 与参考库进行 apple-to-apple 测试
- **性能对等** —— 与流行替代方案进行基准测试（[在线面板](https://oaklight.github.io/zerodep/dev/bench)）
