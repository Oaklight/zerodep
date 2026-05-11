# Retry

Zero-dependency decorator-based retry with configurable backoff strategies -- stdlib only, Python 3.10+.

> **Replaces:** `tenacity`, `retrying`, `backoff`

## Overview

The Retry module provides a decorator and imperative API for retrying failed function calls with configurable backoff, jitter, exception/result filtering, and sync+async support -- all without any third-party dependencies.

| File | Description | Dependencies |
|------|-------------|--------------|
| `retry.py` | Pure Python implementation | None (stdlib only: `time`, `functools`, `random`, `asyncio`, `inspect`) |

The module supports exponential, linear, and fixed backoff strategies, three jitter modes, exception type filtering, HTTP status code filtering, result-based retry predicates, an `on_retry` callback, and automatic async detection.

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp retry/retry.py your_project/
```

Then import directly:

```python
from retry import retry, retry_call, RetryError
```

## Usage Examples

### Basic Decorator

```python
from retry import retry

# Bare decorator (defaults: 3 retries, exponential backoff)
@retry
def call_api():
    return get("https://api.example.com/data")

# With parentheses (same defaults)
@retry()
def call_api():
    return get("https://api.example.com/data")

# With custom options
@retry(max_retries=5, backoff="linear", base_delay=0.5)
def call_api():
    return get("https://api.example.com/data")
```

### Async Support

```python
import asyncio
from retry import retry

@retry(max_retries=3, retry_on=(ConnectionError, TimeoutError))
async def fetch_data():
    return await async_get("https://api.example.com/data")

asyncio.run(fetch_data())
```

The decorator automatically detects async functions and uses `asyncio.sleep` instead of `time.sleep`.

### Exception Filtering

```python
from retry import retry, retry_if_exception

# Retry only on specific exception types (tuple form)
@retry(retry_on=(ConnectionError, TimeoutError))
def call_api():
    return get("https://api.example.com/data")

# Retry using a predicate function
@retry(retry_on=retry_if_exception(ConnectionError, TimeoutError))
def call_api():
    return get("https://api.example.com/data")
```

### HTTP Status Code Retry

```python
from retry import retry, retry_if_status

@retry(retry_on=retry_if_status(429, 502, 503))
def call_api():
    resp = get("https://api.example.com/data")
    resp.raise_for_status()
    return resp
```

Works with any exception that has a `status_code` attribute (e.g. `httpclient.HTTPError`).

### Result-Based Retry

```python
from retry import retry, retry_if_result

# Retry when the result is None
@retry(retry_on_result=retry_if_result(lambda r: r is None))
def get_value():
    return cache.get("key")

# Retry when the response body is empty
@retry(retry_on_result=lambda r: r.text == "")
def call_api():
    return get("https://api.example.com/data")
```

!!! note "RetryError on Exhaustion"
    When retries are exhausted due to `retry_on_result`, a `RetryError` is raised (since there is no exception to re-raise).

### on_retry Callback

```python
from retry import retry, RetryState
import logging

def log_retry(state: RetryState):
    logging.warning(
        "Retry %d after %.2fs (delay=%.2fs): %s",
        state.attempt,
        state.elapsed,
        state.delay,
        state.exception or f"result={state.result}",
    )

@retry(max_retries=5, on_retry=log_retry)
def call_api():
    return get("https://api.example.com/data")
```

### Imperative Usage

```python
from retry import retry_call

# Call with retry without decorating
result = retry_call(call_api, max_retries=5, backoff="linear")

# Pass arguments to the target function
result = retry_call(
    call_api,
    args=("https://api.example.com/data",),
    kwargs={"timeout": 10},
    max_retries=3,
)
```

### Backoff Strategies

```python
from retry import retry

# Exponential backoff (default): delay = base_delay * (backoff_factor ** attempt)
@retry(backoff="exponential", base_delay=1.0, backoff_factor=2.0)
def f(): ...

# Linear backoff: delay = base_delay * (attempt + 1)
@retry(backoff="linear", base_delay=0.5)
def f(): ...

# Fixed backoff: delay = base_delay
@retry(backoff="fixed", base_delay=2.0)
def f(): ...
```

### Jitter Modes

```python
from retry import retry

# Full jitter (default): uniform random in [0, delay]
@retry(jitter="full")
def f(): ...

# Equal jitter: delay/2 + uniform random in [0, delay/2]
@retry(jitter="equal")
def f(): ...

# No jitter: exact computed delay
@retry(jitter="none")
def f(): ...
```

## API Reference

### `retry(fn=None, *, max_retries, base_delay, max_delay, backoff, backoff_factor, jitter, retry_on, retry_on_result, on_retry)`

Decorator that retries a function on failure with configurable backoff. Can be used with or without arguments (`@retry`, `@retry()`, or `@retry(max_retries=5)`).

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `fn` | `Callable \| None` | `None` | The function to decorate (set automatically when used as `@retry` without parentheses). |
| `max_retries` | `int` | `3` | Maximum number of retries (not counting the initial call). |
| `base_delay` | `float` | `1.0` | Base delay in seconds before the first retry. |
| `max_delay` | `float` | `60.0` | Upper bound on computed delay. |
| `backoff` | `str` | `"exponential"` | Backoff strategy: `"exponential"`, `"linear"`, or `"fixed"`. |
| `backoff_factor` | `float` | `2.0` | Multiplier for exponential backoff. |
| `jitter` | `str` | `"full"` | Jitter mode: `"full"`, `"equal"`, or `"none"`. |
| `retry_on` | `tuple[type[Exception], ...] \| Callable` | `(Exception,)` | Exception types or a callable `(exc) -> bool` deciding whether to retry. |
| `retry_on_result` | `Callable \| None` | `None` | Optional callable `(result) -> bool`. When it returns `True` the call is retried. |
| `on_retry` | `Callable[[RetryState], None] \| None` | `None` | Optional callback invoked before each retry sleep. |

**Returns:** The decorated function (sync or async, matching the original).

**Raises:**

- `RetryError` -- when retries are exhausted due to `retry_on_result`.
- The original exception -- when retries are exhausted due to exceptions.

---

### `retry_call(fn, args=(), kwargs=None, **retry_kwargs)`

Call a function with retry logic without using a decorator.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `fn` | `Callable` | -- | The callable to invoke. |
| `args` | `tuple` | `()` | Positional arguments for `fn`. |
| `kwargs` | `dict \| None` | `None` | Keyword arguments for `fn`. |
| `**retry_kwargs` | -- | -- | Same keyword arguments accepted by `retry`. |

**Returns:** The return value of `fn` on success.

---

### `retry_if_exception(*exc_types)`

Build a predicate that matches specific exception types.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `*exc_types` | `type[BaseException]` | Exception classes to retry on. |

**Returns:** A callable `(exc) -> bool`.

---

### `retry_if_result(predicate)`

Mark a callable as a result-retry predicate (identity helper for self-documenting call sites).

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `predicate` | `Callable[[Any], bool]` | A callable `(result) -> bool` returning `True` to retry. |

**Returns:** The same callable.

---

### `retry_if_status(*status_codes)`

Build a predicate that retries on HTTP status codes. Works with any exception carrying a `status_code` attribute.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `*status_codes` | `int` | HTTP status codes to retry on (e.g. 429, 502, 503). |

**Returns:** A callable `(exc) -> bool`.

---

### `RetryError`

Raised when all retry attempts are exhausted (only for result-based retries). Subclass of `Exception`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `last_exception` | `BaseException \| None` | The exception from the final attempt, or `None` if retries were triggered by result predicate. |
| `attempts` | `int` | Total number of calls made (initial + retries). |

---

### `RetryState`

Dataclass with information about the current retry, passed to the `on_retry` callback.

| Field | Type | Description |
|-------|------|-------------|
| `attempt` | `int` | 1-based retry number (1 = first retry, not the initial call). |
| `exception` | `BaseException \| None` | The exception that triggered this retry, or `None`. |
| `result` | `Any` | The return value that triggered this retry, or `None`. |
| `delay` | `float` | Seconds to sleep before the next attempt. |
| `elapsed` | `float` | Seconds elapsed since the initial call. |

## Comparison with tenacity / backoff

| Feature | zerodep retry | tenacity | backoff |
|---------|--------------|----------|--------|
| Dependencies | None (stdlib only) | `None` | `None` |
| Backoff strategies | exponential, linear, fixed | exponential, fixed, custom | exponential, fixed, constant |
| Jitter modes | full, equal, none | full, equal, decorrelated | full, none |
| Async support | Yes (auto-detected) | Yes | Yes |
| Exception filtering | Yes | Yes | Yes |
| Result-based retry | Yes | Yes | No |
| HTTP status filtering | Yes (built-in helper) | Via custom predicate | No |
| on_retry callback | Yes | Yes (before/after) | Yes |
| Imperative API | `retry_call()` | `.call()` | No |
| Decorator overhead | ~377 ns | ~8.4 us | -- |
| Implementation | Single file (~460 lines) | Package (multiple files) | Package (multiple files) |

**When to use zerodep:** You need a lightweight retry decorator with zero dependencies and your use case covers standard backoff patterns.

**When to use tenacity:** You need advanced features like decorrelated jitter, retry statistics, or wait-chain composition.

## Benchmark

Benchmarked against `tenacity` across decorator overhead, retry execution, and backoff calculation scenarios.

See [Retry Benchmark](../benchmarks/retry.md) for detailed results.
