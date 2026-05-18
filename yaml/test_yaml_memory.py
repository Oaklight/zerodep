"""Memory benchmarks: zerodep yaml vs PyYAML.

Uses tracemalloc to measure peak heap allocation for load (parse) and
dump (serialize) at three input sizes (S/M/L).  Results are printed in
KB so they are visible in plain ``pytest -s`` output.  No
pytest-benchmark required.

Note: our ``yaml.py`` shadows PyYAML on sys.path, so PyYAML must be
imported with path manipulation (same technique as the time benchmark).
"""

import os
import sys
import tracemalloc

import pytest

# ── Import PyYAML without being shadowed by our yaml.py ──

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

from yaml import dump as zd_dump  # noqa: E402
from yaml import load as zd_load  # noqa: E402

# ── Test data (same as time benchmark) ──

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

SMALL_DATA = {"name": "Alice", "age": 30, "active": True, "city": "NYC", "score": 9.5}
MEDIUM_DATA = _pyyaml_safe_load(MEDIUM)
LARGE_DATA = _pyyaml_safe_load(LARGE)


# ── Helpers ──


def _measure_peak_kb(fn, *args) -> float:
    """Run *fn* with *args* under tracemalloc and return peak KB."""
    tracemalloc.start()
    try:
        fn(*args)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak / 1024


_DOC_SIZES = [
    pytest.param("small", SMALL, id="small"),
    pytest.param("medium", MEDIUM, id="medium"),
    pytest.param("large", LARGE, id="large"),
]

_DATA_SIZES = [
    pytest.param("small", SMALL_DATA, id="small"),
    pytest.param("medium", MEDIUM_DATA, id="medium"),
    pytest.param("large", LARGE_DATA, id="large"),
]


# ── Load (parse) memory tests ──


@pytest.mark.parametrize("label,doc", _DOC_SIZES)
def test_load_memory_zerodep(label: str, doc: str) -> None:
    """Measure peak memory for zerodep yaml.load."""
    peak_kb = _measure_peak_kb(zd_load, doc)
    print(f"\n[yaml load zerodep  {label:6s}] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.parametrize("label,doc", _DOC_SIZES)
def test_load_memory_pyyaml(label: str, doc: str) -> None:
    """Measure peak memory for PyYAML safe_load."""
    peak_kb = _measure_peak_kb(_pyyaml_safe_load, doc)
    print(f"\n[yaml load pyyaml   {label:6s}] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.parametrize("label,doc", _DOC_SIZES)
def test_load_memory_comparison(label: str, doc: str) -> None:
    """Compare zerodep vs PyYAML peak memory for load."""
    zd_kb = _measure_peak_kb(zd_load, doc)
    ref_kb = _measure_peak_kb(_pyyaml_safe_load, doc)
    ratio = zd_kb / ref_kb if ref_kb > 0 else float("inf")
    print(
        f"\n[yaml load compare  {label:6s}] zerodep={zd_kb:.1f} KB  "
        f"pyyaml={ref_kb:.1f} KB  ratio={ratio:.2f}x"
    )
    assert zd_kb >= 0
    assert ref_kb >= 0


# ── Dump (serialize) memory tests ──


@pytest.mark.parametrize("label,data", _DATA_SIZES)
def test_dump_memory_zerodep(label: str, data) -> None:
    """Measure peak memory for zerodep yaml.dump."""
    peak_kb = _measure_peak_kb(zd_dump, data)
    print(f"\n[yaml dump zerodep  {label:6s}] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


def _pyyaml_dump_block(data) -> str:
    """Wrap PyYAML dump with default_flow_style=False."""
    return _pyyaml_dump(data, default_flow_style=False)


@pytest.mark.parametrize("label,data", _DATA_SIZES)
def test_dump_memory_pyyaml(label: str, data) -> None:
    """Measure peak memory for PyYAML dump."""
    peak_kb = _measure_peak_kb(_pyyaml_dump_block, data)
    print(f"\n[yaml dump pyyaml   {label:6s}] peak memory: {peak_kb:.1f} KB")
    assert peak_kb >= 0


@pytest.mark.parametrize("label,data", _DATA_SIZES)
def test_dump_memory_comparison(label: str, data) -> None:
    """Compare zerodep vs PyYAML peak memory for dump."""
    zd_kb = _measure_peak_kb(zd_dump, data)
    ref_kb = _measure_peak_kb(_pyyaml_dump_block, data)
    ratio = zd_kb / ref_kb if ref_kb > 0 else float("inf")
    print(
        f"\n[yaml dump compare  {label:6s}] zerodep={zd_kb:.1f} KB  "
        f"pyyaml={ref_kb:.1f} KB  ratio={ratio:.2f}x"
    )
    assert zd_kb >= 0
    assert ref_kb >= 0
