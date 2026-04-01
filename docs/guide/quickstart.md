---
title: Quick Start
---

# Quick Start

**zerodep** is a collection of zero-dependency, single-file Python modules that reimplement popular libraries using only the standard library (Python 3.10+). Instead of `pip install`, you copy a single `.py` file into your project and import it directly.

## Install the CLI

=== "pip"

    ```bash
    pip install zerodep
    ```

=== "No install"

    ```bash
    curl -O https://raw.githubusercontent.com/Oaklight/zerodep/master/zerodep.py
    python zerodep.py --help
    ```

## Get Your First Module

Use the `zerodep` CLI to fetch the `yaml` module:

```bash
zerodep add yaml
```

This downloads `yaml.py` into your current directory. No virtual environment, no dependency tree -- just one file.

!!! tip "Manual download"

    You can also grab the file directly:

    ```bash
    curl -O https://raw.githubusercontent.com/Oaklight/zerodep/master/yaml/yaml.py
    ```

## Use It

```python
from yaml import load, dump

data = load("name: Alice\nage: 30")
print(data)   # {'name': 'Alice', 'age': 30}
print(dump(data))
```

That's it -- the API mirrors what you already know from PyYAML, with no install step.

## Another Example: Retry Decorator

Fetch the `retry` module:

```bash
zerodep add retry
```

Apply it to any function:

```python
from retry import retry

@retry(max_retries=3, retry_on=(ConnectionError, TimeoutError))
def fetch_data(url: str) -> str:
    # Will automatically retry up to 3 times with exponential backoff
    ...
```

!!! note

    Async functions are supported too -- just decorate an `async def` and the retry logic handles `await` automatically.

## What's Next

- [CLI Tool](cli.md) -- full command reference (`add`, `list`, `info`, `update`, etc.)
- [Module Overview](../modules/index.md) -- browse all 30+ available modules
- [Design Philosophy](philosophy.md) -- when (and when not) to use zerodep
