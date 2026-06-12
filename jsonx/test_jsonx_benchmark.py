"""Benchmark: zerodep jsonx (JSONC + JSONL) vs commentjson / jsonlines / ndjson."""

import os
import sys

import pytest

try:
    import commentjson as _cj
except ImportError:
    _cj = None

try:
    import jsonlines as _jl
except ImportError:
    _jl = None

try:
    import ndjson as _ndjson
except ImportError:
    _ndjson = None

sys.path.insert(0, os.path.dirname(__file__))
from jsonx import loads as zd_loads  # noqa: E402
from jsonx import loads_lines as zd_loads_lines  # noqa: E402

_skip_commentjson = pytest.mark.skipif(_cj is None, reason="commentjson not installed")
_skip_jsonlines = pytest.mark.skipif(_jl is None, reason="jsonlines not installed")
_skip_ndjson = pytest.mark.skipif(_ndjson is None, reason="ndjson not installed")

# ── Test data ──

SMALL = """{
  // Basic config
  "name": "Alice",
  "age": 30,
  "active": true,
  "city": "NYC",
  "score": 9.5
}"""

MEDIUM = """{
  // Database configuration
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "mydb",
    "credentials": {
      "user": "admin", // admin user
      "password": "secret"
    },
    "options": {
      "pool_size": 10,
      "timeout": 30,
      "ssl": true,
    },
  },
  // Server list
  "servers": [
    {"name": "web-1", "ip": "10.0.0.1", "roles": ["web", "api"]},
    {"name": "web-2", "ip": "10.0.0.2", "roles": ["web"]},
    {"name": "db-1", "ip": "10.0.0.3", "roles": ["database", "backup"]},
  ],
  # Feature flags
  "features": {
    "auth": true,
    "cache": true,
    "logging": true,
    "debug": false,
  },
  "limits": {
    "max_connections": 1000,
    "max_request_size": 10485760,
    "rate_limit": 100,
  },
}"""

_large_items = []
for i in range(100):
    _large_items.append(
        f'  "item_{i}": {{\n'
        f'    "id": {i},\n'
        f'    "name": "Item {i}", // item name\n'
        f'    "value": {i * 1.5},\n'
        f'    "active": {"true" if i % 2 == 0 else "false"},\n'
        f'    "tags": ["tag_a", "tag_b", "tag_{i}"],\n'
        f"  }}"
    )
LARGE = "{\n" + ",\n".join(_large_items) + "\n}"


# ── Load benchmarks ──


class TestLoadSmall:
    def test_zerodep(self, benchmark):
        benchmark(zd_loads, SMALL)

    @_skip_commentjson
    def test_commentjson(self, benchmark):
        benchmark(_cj.loads, SMALL)


class TestLoadMedium:
    def test_zerodep(self, benchmark):
        benchmark(zd_loads, MEDIUM)

    @_skip_commentjson
    def test_commentjson(self, benchmark):
        benchmark(_cj.loads, MEDIUM)


class TestLoadLarge:
    def test_zerodep(self, benchmark):
        benchmark(zd_loads, LARGE)

    @_skip_commentjson
    def test_commentjson(self, benchmark):
        benchmark(_cj.loads, LARGE)


# ── Fixture data: real-world config files ──

_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
_FIXTURE_CACHE: dict[str, str] = {}

_FIXTURE_FILES = {
    "vscode-settings": "vscode-settings.jsonc",
    "tsconfig": "tsconfig.jsonc",
    "eslint-config": "eslint-config.jsonc",
}


def _fixture_available(name: str) -> bool:
    return os.path.isfile(os.path.join(_FIXTURES_DIR, _FIXTURE_FILES.get(name, "")))


def _get_fixture(name: str) -> str:
    if name not in _FIXTURE_CACHE:
        path = os.path.join(_FIXTURES_DIR, _FIXTURE_FILES[name])
        with open(path, encoding="utf-8") as f:
            _FIXTURE_CACHE[name] = f.read()
    return _FIXTURE_CACHE[name]


# ── Fixture load benchmarks ──


@pytest.mark.skipif(not _fixture_available("vscode-settings"), reason="fixture missing")
class TestFixtureLoadVscodeSettings:
    def test_zerodep(self, benchmark):
        benchmark(zd_loads, _get_fixture("vscode-settings"))

    @_skip_commentjson
    def test_commentjson(self, benchmark):
        benchmark(_cj.loads, _get_fixture("vscode-settings"))


@pytest.mark.skipif(not _fixture_available("tsconfig"), reason="fixture missing")
class TestFixtureLoadTsconfig:
    def test_zerodep(self, benchmark):
        benchmark(zd_loads, _get_fixture("tsconfig"))

    @_skip_commentjson
    def test_commentjson(self, benchmark):
        benchmark(_cj.loads, _get_fixture("tsconfig"))


@pytest.mark.skipif(not _fixture_available("eslint-config"), reason="fixture missing")
class TestFixtureLoadEslintConfig:
    def test_zerodep(self, benchmark):
        benchmark(zd_loads, _get_fixture("eslint-config"))

    @_skip_commentjson
    def test_commentjson(self, benchmark):
        benchmark(_cj.loads, _get_fixture("eslint-config"))


# ── JSONL benchmarks ──────────────────────────────────────────────────────────────────────

_JSONL_SMALL = "\n".join(f'{{"id":{i},"name":"item_{i}","value":{i*1.5}}}' for i in range(10))
_JSONL_MEDIUM = "\n".join(f'{{"id":{i},"name":"item_{i}","value":{i*1.5},"active":{"true" if i%2==0 else "false"},"tags":["a","b"]}}' for i in range(100))
_JSONL_LARGE = "\n".join(f'{{"id":{i},"name":"item_{i}","value":{i*1.5},"active":{"true" if i%2==0 else "false"},"tags":["a","b","c_{i}"],"meta":{{"k":{i}}}}}' for i in range(1000))


def _jsonlines_loads(text: str) -> list:
    """Parse JSONL with the jsonlines library."""
    import io
    reader = _jl.Reader(io.StringIO(text))
    return list(reader)


def _ndjson_loads(text: str) -> list:
    """Parse JSONL with the ndjson library."""
    return _ndjson.loads(text)


class TestJsonlSmall:
    def test_zerodep(self, benchmark):
        benchmark(zd_loads_lines, _JSONL_SMALL)

    @_skip_jsonlines
    def test_jsonlines(self, benchmark):
        benchmark(_jsonlines_loads, _JSONL_SMALL)

    @_skip_ndjson
    def test_ndjson(self, benchmark):
        benchmark(_ndjson_loads, _JSONL_SMALL)


class TestJsonlMedium:
    def test_zerodep(self, benchmark):
        benchmark(zd_loads_lines, _JSONL_MEDIUM)

    @_skip_jsonlines
    def test_jsonlines(self, benchmark):
        benchmark(_jsonlines_loads, _JSONL_MEDIUM)

    @_skip_ndjson
    def test_ndjson(self, benchmark):
        benchmark(_ndjson_loads, _JSONL_MEDIUM)


class TestJsonlLarge:
    def test_zerodep(self, benchmark):
        benchmark(zd_loads_lines, _JSONL_LARGE)

    @_skip_jsonlines
    def test_jsonlines(self, benchmark):
        benchmark(_jsonlines_loads, _JSONL_LARGE)

    @_skip_ndjson
    def test_ndjson(self, benchmark):
        benchmark(_ndjson_loads, _JSONL_LARGE)
