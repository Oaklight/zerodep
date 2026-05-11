# Semver

PEP 440 version parser and comparator -- zero dependencies, stdlib only, Python 3.10+.

> **Replaces:** `packaging` (Version), `semver`

## Overview

The Semver module provides PEP 440 version parsing, normalisation, and comparison using only the Python standard library. It is a drop-in replacement for the core functionality of `packaging.version`.

| File | Description | Dependencies |
|------|-------------|--------------|
| `semver.py` | Pure Python implementation | None (stdlib only: `re`, `functools`) |

## How to Use in Your Project

Just copy the single `.py` file into your project:

```bash
cp semver/semver.py your_project/
```

Then import directly:

```python
from semver import Version, version_parse, InvalidVersion
```

## Usage Examples

### Parsing Versions

```python
from semver import Version, version_parse

v = Version("1.2.3")
v = version_parse("1.2.3")  # equivalent convenience function
```

### Comparing Versions

```python
from semver import Version

assert Version("2.0") > Version("1.0")
assert Version("1.0a1") < Version("1.0")
assert Version("1.0") == Version("1.0.0")
assert Version("1.0") <= Version("2.0")
```

### Sorting and Selecting

```python
from semver import Version

versions = [Version("3.0"), Version("1.0"), Version("2.0b1"), Version("2.0")]
print(sorted(versions))
# [<Version('1.0')>, <Version('2.0b1')>, <Version('2.0')>, <Version('3.0')>]

print(max(versions))
# <Version('3.0')>
```

### Pre-release and Dev Detection

```python
from semver import Version

v = Version("1.0a1")
print(v.is_prerelease)  # True
print(v.is_devrelease)  # False

v = Version("1.0.dev3")
print(v.is_prerelease)  # True (dev releases are also pre-releases)
print(v.is_devrelease)  # True
```

### Version Properties

```python
from semver import Version

v = Version("2!1.2.3a1.post2.dev3+local.1")
print(v.epoch)         # 2
print(v.release)       # (1, 2, 3)
print(v.major)         # 1
print(v.minor)         # 2
print(v.micro)         # 3
print(v.pre)           # ('a', 1)
print(v.post)          # 2
print(v.dev)           # 3
print(v.local)         # 'local.1'
print(v.base_version)  # '2!1.2.3'
print(v.public)        # '2!1.2.3a1.post2.dev3'
```

### String Normalisation

```python
from semver import Version

print(str(Version("1.0alpha1")))   # '1.0a1'
print(str(Version("1.0beta2")))    # '1.0b2'
print(str(Version("1.0preview1"))) # '1.0rc1'
print(str(Version("v1.0")))        # '1.0'
print(str(Version("1.0-1")))       # '1.0.post1'
```

### Error Handling

```python
from semver import Version, InvalidVersion

try:
    Version("not a version")
except InvalidVersion as e:
    print(e)  # Invalid version: 'not a version'
```

## PEP 440 Ordering

The module implements the full PEP 440 version ordering:

```
.devN < aN (alpha) < bN (beta) < rcN < release < .postN
```

Example:

```python
from semver import Version

chain = [
    Version("1.0.dev0"),
    Version("1.0a1"),
    Version("1.0b1"),
    Version("1.0rc1"),
    Version("1.0"),
    Version("1.0.post1"),
]
assert chain == sorted(chain)  # already in order
```

## API Reference

### `Version(version: str)`

Parse a PEP 440 version string.

**Raises:** `InvalidVersion` if the string does not conform to PEP 440.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `epoch` | `int` | Epoch segment (`0` when absent) |
| `release` | `tuple[int, ...]` | Release segment as integers |
| `pre` | `tuple[str, int] \| None` | Pre-release tag, e.g. `('a', 1)` |
| `post` | `int \| None` | Post-release number |
| `dev` | `int \| None` | Dev-release number |
| `local` | `str \| None` | Local version label |
| `major` | `int` | First release component |
| `minor` | `int` | Second release component (`0` if absent) |
| `micro` | `int` | Third release component (`0` if absent) |
| `base_version` | `str` | Version without pre/post/dev/local |
| `public` | `str` | Version without local segment |
| `is_prerelease` | `bool` | `True` if pre-release or dev-release |
| `is_devrelease` | `bool` | `True` if dev-release |
| `is_postrelease` | `bool` | `True` if post-release |

**Operators:** `==`, `!=`, `<`, `>`, `<=`, `>=`, `hash()`, `str()`, `repr()`

---

### `version_parse(version: str) -> Version`

Convenience function equivalent to `Version(version)`.

---

### `InvalidVersion`

Exception raised for unparseable version strings. Subclass of `ValueError`.

## Comparison with packaging

| Feature | zerodep semver | packaging |
|---------|---------------|-----------|
| Dependencies | None (stdlib only) | None (but adds a pip dependency) |
| API | `Version("1.0")` | `Version("1.0")` |
| Comparison | All operators | All operators |
| Properties | `is_prerelease`, `is_devrelease`, etc. | Same |
| Normalisation | Full PEP 440 | Full PEP 440 |
| Performance | Comparable (see benchmark) | Comparable |
| Implementation | Single file (~300 lines) | Package |

**When to use zerodep:** You want zero pip dependencies and only need PEP 440 version parsing/comparison.

**When to use packaging:** You need the full `packaging` library (specifiers, requirements, markers, tags).

## Benchmark

Benchmarked against `packaging` across parsing, sorting, comparison, and property access.

See [Semver Benchmark](../benchmarks/semver.md) for detailed results.
