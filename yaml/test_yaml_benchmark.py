"""Benchmark: zerodep YAML vs PyYAML."""

import os
import sys

import pytest

# Our yaml.py shadows PyYAML. Import PyYAML via path manipulation.
_this_dir = os.path.dirname(__file__)

_saved_path = sys.path[:]
sys.path = [
    p
    for p in sys.path
    if os.path.abspath(p)
    not in (
        os.path.abspath(_this_dir),
        os.path.abspath(os.path.join(_this_dir, "..")),
    )
]
_cached_yaml = sys.modules.pop("yaml", None)

try:
    import yaml as _pyyaml

    if not hasattr(_pyyaml, "safe_load"):
        raise ImportError("Not the real PyYAML")
    _pyyaml_safe_load = _pyyaml.safe_load
    _pyyaml_dump = _pyyaml.dump
except ImportError:
    pytest.skip("PyYAML not installed", allow_module_level=True)
finally:
    sys.path = _saved_path
    sys.modules.pop("yaml", None)
    if _cached_yaml is not None:
        sys.modules["yaml"] = _cached_yaml

sys.path.insert(0, _this_dir)

from yaml import dump as zd_dump
from yaml import load as zd_load

# ── Test data ──

SMALL = "name: Alice\nage: 30\nactive: true\ncity: NYC\nscore: 9.5"

MEDIUM = """
database:
  host: localhost
  port: 5432
  name: mydb
  credentials:
    user: admin
    password: secret
  options:
    pool_size: 10
    timeout: 30
    ssl: true

servers:
  - name: web-1
    ip: 10.0.0.1
    roles: [web, api]
  - name: web-2
    ip: 10.0.0.2
    roles: [web]
  - name: db-1
    ip: 10.0.0.3
    roles: [database, backup]

features:
  auth: true
  cache: true
  logging: true
  debug: false

limits:
  max_connections: 1000
  max_request_size: 10485760
  rate_limit: 100
""".strip()

_large_items = []
for i in range(100):
    _large_items.append(
        f"item_{i}:\n"
        f"  id: {i}\n"
        f"  name: 'Item {i}'\n"
        f"  value: {i * 1.5}\n"
        f"  active: {'true' if i % 2 == 0 else 'false'}\n"
        f"  tags: [tag_a, tag_b, tag_{i}]"
    )
LARGE = "\n".join(_large_items)

# Pre-parsed data for dump benchmarks
SMALL_DATA = {"name": "Alice", "age": 30, "active": True, "city": "NYC", "score": 9.5}
MEDIUM_DATA = _pyyaml_safe_load(MEDIUM)
LARGE_DATA = _pyyaml_safe_load(LARGE)


# ── Load benchmarks ──


class TestLoadSmall:
    def test_zerodep(self, benchmark):
        benchmark(zd_load, SMALL)

    def test_pyyaml(self, benchmark):
        benchmark(_pyyaml_safe_load, SMALL)


class TestLoadMedium:
    def test_zerodep(self, benchmark):
        benchmark(zd_load, MEDIUM)

    def test_pyyaml(self, benchmark):
        benchmark(_pyyaml_safe_load, MEDIUM)


class TestLoadLarge:
    def test_zerodep(self, benchmark):
        benchmark(zd_load, LARGE)

    def test_pyyaml(self, benchmark):
        benchmark(_pyyaml_safe_load, LARGE)


# ── Dump benchmarks ──


class TestDumpSmall:
    def test_zerodep(self, benchmark):
        benchmark(zd_dump, SMALL_DATA)

    def test_pyyaml(self, benchmark):
        benchmark(_pyyaml_dump, SMALL_DATA, default_flow_style=False)


class TestDumpMedium:
    def test_zerodep(self, benchmark):
        benchmark(zd_dump, MEDIUM_DATA)

    def test_pyyaml(self, benchmark):
        benchmark(_pyyaml_dump, MEDIUM_DATA, default_flow_style=False)


class TestDumpLarge:
    def test_zerodep(self, benchmark):
        benchmark(zd_dump, LARGE_DATA)

    def test_pyyaml(self, benchmark):
        benchmark(_pyyaml_dump, LARGE_DATA, default_flow_style=False)
