"""Benchmark: zerodep config vs python-decouple."""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from config import Config, Csv

ref_decouple = pytest.importorskip("decouple", reason="python-decouple not installed")

# ── Fixtures ────────────────────────────────────────────────────────────────

_tmpdir = tempfile.mkdtemp()

# .env with 50 keys
_env_content = "\n".join(f"BENCH_KEY_{i}=value_{i}" for i in range(50))
_env_path = os.path.join(_tmpdir, ".env")
with open(_env_path, "w") as _f:
    _f.write(_env_content)

# JSON config with nested structure
_json_data = {
    "database": {"host": "localhost", "port": 5432, "name": "mydb"},
    "cache": {"ttl": 300, "backend": "redis"},
}
for i in range(20):
    _json_data[f"section_{i}"] = {f"key_{j}": f"val_{i}_{j}" for j in range(5)}
_json_path = os.path.join(_tmpdir, "config.json")
with open(_json_path, "w") as _f:
    json.dump(_json_data, _f)

# Pre-create Config instances
_cfg_env = Config(dotenv_path=_env_path, prefix="")
_cfg_json = Config(dotenv_path=None, config_path=_json_path)

# Set env vars for decouple comparison
for i in range(50):
    os.environ[f"BENCH_KEY_{i}"] = f"value_{i}"
os.environ["BENCH_CAST_INT"] = "42"
os.environ["BENCH_CAST_BOOL"] = "true"
os.environ["BENCH_CSV"] = "a, b, c, d, e"


# ── Env var lookup ──────────────────────────────────────────────────────────


class TestEnvLookup:
    def test_zerodep(self, benchmark):
        cfg = Config(dotenv_path=None)
        benchmark(cfg, "BENCH_KEY_25")

    def test_decouple(self, benchmark):
        benchmark(ref_decouple.config, "BENCH_KEY_25")


# ── .env file lookup ────────────────────────────────────────────────────────


class TestDotenvLookup:
    def test_zerodep(self, benchmark):
        benchmark(_cfg_env, "BENCH_KEY_25")

    def test_decouple(self, benchmark):
        benchmark(ref_decouple.config, "BENCH_KEY_25")


# ── Cast int ────────────────────────────────────────────────────────────────


class TestCastInt:
    def test_zerodep(self, benchmark):
        cfg = Config(dotenv_path=None)
        benchmark(cfg, "BENCH_CAST_INT", cast=int)

    def test_decouple(self, benchmark):
        benchmark(ref_decouple.config, "BENCH_CAST_INT", cast=int)


# ── Cast bool ───────────────────────────────────────────────────────────────


class TestCastBool:
    def test_zerodep(self, benchmark):
        cfg = Config(dotenv_path=None)
        benchmark(cfg, "BENCH_CAST_BOOL", cast=bool)

    def test_decouple(self, benchmark):
        benchmark(ref_decouple.config, "BENCH_CAST_BOOL", cast=bool)


# ── Csv ─────────────────────────────────────────────────────────────────────


class TestCsvCast:
    def test_zerodep(self, benchmark):
        cfg = Config(dotenv_path=None)
        benchmark(cfg, "BENCH_CSV", cast=Csv())

    def test_decouple(self, benchmark):
        benchmark(ref_decouple.config, "BENCH_CSV", cast=ref_decouple.Csv())


# ── Nested JSON config lookup ──────────────────────────────────────────────


class TestNestedJsonLookup:
    def test_zerodep(self, benchmark):
        benchmark(_cfg_json, "database__host")


# ── Config init (construction cost) ────────────────────────────────────────


class TestConfigInit:
    def test_zerodep_env_only(self, benchmark):
        benchmark(Config, dotenv_path=None)

    def test_zerodep_with_dotenv(self, benchmark):
        benchmark(Config, dotenv_path=_env_path)

    def test_zerodep_with_json(self, benchmark):
        benchmark(Config, dotenv_path=None, config_path=_json_path)
