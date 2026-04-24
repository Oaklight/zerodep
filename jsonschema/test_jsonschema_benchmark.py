"""Benchmark: zerodep jsonschema vs allof-merge (JS).

Compares both **correctness** (output equivalence) and **performance**
across five schema complexity tiers.
"""

import json
import os
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from jsonschema import flatten_schema, merge_allof, resolve_refs  # noqa: E402

# ---------------------------------------------------------------------------
# JS engine
# ---------------------------------------------------------------------------

_THIS_DIR = os.path.dirname(__file__)
_BENCH_JS = os.path.join(_THIS_DIR, "bench_allof_merge.js")
_NODE_MODULES = os.path.join(_THIS_DIR, "node_modules")
_HAS_NODE = shutil.which("node") is not None and os.path.isdir(_NODE_MODULES)


def _run_js(schema: dict, rounds: int = 1) -> dict:
    """Run allof-merge via Node.js and return ``{result, times_ms, ...}``."""
    proc = subprocess.run(
        ["node", _BENCH_JS, str(rounds)],
        input=json.dumps(schema),
        capture_output=True,
        text=True,
        timeout=30,
        cwd=_THIS_DIR,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"JS error: {proc.stderr}")
    return json.loads(proc.stdout)


# ---------------------------------------------------------------------------
# Test schemas — five complexity tiers
# ---------------------------------------------------------------------------

# Tier 1: Tiny — no composition keywords at all (passthrough baseline).
TINY_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
    },
    "required": ["name"],
}

# Tier 2: Small — single anyOf nullable.
SMALL_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 0},
        "email": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
        },
    },
    "required": ["name", "age"],
}

# Tier 3: Medium — $ref + allOf + anyOf combined.
MEDIUM_SCHEMA = {
    "type": "object",
    "properties": {
        "user": {
            "allOf": [
                {"$ref": "#/$defs/Person"},
                {
                    "properties": {
                        "role": {"type": "string", "enum": ["admin", "user"]},
                    },
                    "required": ["role"],
                },
            ],
        },
        "settings": {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {
                        "theme": {"type": "string"},
                        "lang": {"type": "string"},
                    },
                },
                {"type": "null"},
            ],
        },
    },
    "$defs": {
        "Person": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
            },
            "required": ["name"],
        },
    },
}

# Tier 4: Large — multiple $ref + nested allOf + oneOf.
LARGE_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "minLength": 1},
        "filters": {
            "allOf": [
                {"$ref": "#/$defs/BaseFilter"},
                {"$ref": "#/$defs/DateFilter"},
                {
                    "properties": {
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 0,
                            "maxItems": 20,
                        },
                    },
                },
            ],
        },
        "output": {
            "allOf": [
                {"$ref": "#/$defs/Pagination"},
                {
                    "properties": {
                        "format": {
                            "oneOf": [
                                {"type": "string", "enum": ["json", "csv"]},
                                {"type": "null"},
                            ],
                        },
                        "fields": {
                            "type": "array",
                            "items": {
                                "allOf": [
                                    {"$ref": "#/$defs/FieldSpec"},
                                    {
                                        "properties": {
                                            "alias": {
                                                "anyOf": [
                                                    {"type": "string"},
                                                    {"type": "null"},
                                                ],
                                            },
                                        },
                                    },
                                ],
                            },
                        },
                    },
                },
            ],
        },
    },
    "required": ["query"],
    "$defs": {
        "BaseFilter": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000},
                "offset": {"type": "integer", "minimum": 0},
            },
            "required": ["limit"],
        },
        "DateFilter": {
            "type": "object",
            "properties": {
                "start_date": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                "end_date": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            },
        },
        "Pagination": {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "minimum": 1},
                "per_page": {"type": "integer", "minimum": 1, "maximum": 100},
            },
        },
        "FieldSpec": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "sort": {
                    "oneOf": [
                        {"type": "string", "enum": ["asc", "desc"]},
                        {"type": "null"},
                    ],
                },
            },
            "required": ["name"],
        },
    },
}


def _make_xlarge_schema(n_fields: int = 50, n_defs: int = 10) -> dict:
    """Generate a synthetic XLarge schema with many fields and definitions."""
    defs = {}
    for i in range(n_defs):
        defs[f"Def{i}"] = {
            "type": "object",
            "properties": {
                f"field_{i}_{j}": {"type": "string", "minLength": 1, "maxLength": 255}
                for j in range(5)
            },
            "required": [f"field_{i}_0"],
        }

    properties: dict = {}
    for i in range(n_fields):
        def_idx = i % n_defs
        if i % 5 == 0:
            # allOf with $ref
            properties[f"prop_{i}"] = {
                "allOf": [
                    {"$ref": f"#/$defs/Def{def_idx}"},
                    {
                        "properties": {
                            f"extra_{i}": {"type": "integer", "minimum": 0},
                        },
                    },
                ],
            }
        elif i % 5 == 1:
            # anyOf nullable
            properties[f"prop_{i}"] = {
                "anyOf": [
                    {"$ref": f"#/$defs/Def{def_idx}"},
                    {"type": "null"},
                ],
            }
        elif i % 5 == 2:
            # oneOf
            properties[f"prop_{i}"] = {
                "oneOf": [
                    {"type": "string"},
                    {"type": "integer"},
                    {"type": "null"},
                ],
            }
        elif i % 5 == 3:
            # Nested allOf with numeric constraints
            properties[f"prop_{i}"] = {
                "allOf": [
                    {"type": "integer", "minimum": 0, "maximum": 1000},
                    {"minimum": 10, "maximum": 500},
                ],
            }
        else:
            # Plain field
            properties[f"prop_{i}"] = {"type": "string"}

    return {
        "type": "object",
        "properties": properties,
        "required": [f"prop_{i}" for i in range(0, n_fields, 3)],
        "$defs": defs,
    }


XLARGE_SCHEMA = _make_xlarge_schema()

ALL_SCHEMAS = {
    "tiny": TINY_SCHEMA,
    "small": SMALL_SCHEMA,
    "medium": MEDIUM_SCHEMA,
    "large": LARGE_SCHEMA,
    "xlarge": XLARGE_SCHEMA,
}

# ---------------------------------------------------------------------------
# Correctness comparison — zerodep output vs allof-merge output
# ---------------------------------------------------------------------------


def _normalize(schema: dict) -> dict:
    """Normalize a schema for comparison: sort required arrays, remove
    keys that only one implementation produces (e.g. nullable vs type array)."""
    if not isinstance(schema, dict):
        return schema
    result = {}
    for k, v in sorted(schema.items()):
        if isinstance(v, dict):
            result[k] = _normalize(v)
        elif isinstance(v, list):
            if k == "required":
                result[k] = sorted(v)
            else:
                result[k] = [
                    _normalize(item) if isinstance(item, dict) else item for item in v
                ]
        else:
            result[k] = v
    return result


def _structural_match(zd: dict, js: dict, path: str = "") -> list[str]:
    """Compare two flattened schemas structurally, returning differences.

    Allows known semantic divergences between zerodep and allof-merge:
    - zerodep uses ``nullable: true``; allof-merge may keep ``anyOf``
    - allof-merge may retain ``$defs``; zerodep strips them
    """
    diffs: list[str] = []
    zd_n = _normalize(zd)
    js_n = _normalize(js)

    # Check that all properties and types agree at this level.
    all_keys = set(zd_n) | set(js_n)
    # Skip keys that represent known implementation differences.
    skip = {"nullable", "$defs", "definitions", "anyOf", "oneOf"}
    for key in sorted(all_keys - skip):
        zval = zd_n.get(key)
        jval = js_n.get(key)
        if zval != jval:
            diffs.append(f"{path}.{key}: zerodep={zval!r} vs js={jval!r}")

    # Recurse into properties.
    zprops = zd_n.get("properties", {})
    jprops = js_n.get("properties", {})
    for pname in set(zprops) | set(jprops):
        if pname in zprops and pname in jprops:
            if isinstance(zprops[pname], dict) and isinstance(jprops[pname], dict):
                diffs.extend(
                    _structural_match(
                        zprops[pname], jprops[pname], f"{path}.properties.{pname}"
                    )
                )

    return diffs


@pytest.mark.skipif(not _HAS_NODE, reason="Node.js or npm deps missing")
class TestCorrectnessVsJs:
    """Compare zerodep flatten_schema output against allof-merge."""

    @pytest.mark.parametrize("tier", ["tiny", "small", "medium", "large", "xlarge"])
    def test_structural_match(self, tier):
        schema = ALL_SCHEMAS[tier]
        zd_result = flatten_schema(schema)
        js_output = _run_js(schema, rounds=1)
        js_result = js_output["result"]
        diffs = _structural_match(zd_result, js_result)
        assert not diffs, f"Structural differences at {tier}:\n" + "\n".join(diffs)

    @pytest.mark.parametrize("tier", ["medium", "large"])
    def test_allof_fully_resolved(self, tier):
        """Both implementations should eliminate all allOf keywords."""
        schema = ALL_SCHEMAS[tier]
        zd_result = flatten_schema(schema)
        js_output = _run_js(schema, rounds=1)
        js_result = js_output["result"]

        def _has_allof(d):
            if not isinstance(d, dict):
                return False
            if "allOf" in d:
                return True
            return any(
                _has_allof(v) for v in d.values() if isinstance(v, (dict, list))
            ) or any(
                _has_allof(item)
                for v in d.values()
                if isinstance(v, list)
                for item in v
                if isinstance(item, dict)
            )

        assert not _has_allof(zd_result), "zerodep output still contains allOf"
        assert not _has_allof(js_result), "allof-merge output still contains allOf"

    @pytest.mark.parametrize("tier", ["medium", "large"])
    def test_refs_fully_resolved(self, tier):
        """Both implementations should eliminate all $ref pointers."""
        schema = ALL_SCHEMAS[tier]
        zd_result = flatten_schema(schema)
        js_output = _run_js(schema, rounds=1)
        js_result = js_output["result"]

        def _has_ref(d):
            if not isinstance(d, dict):
                return False
            if "$ref" in d:
                return True
            return any(
                _has_ref(v) for v in d.values() if isinstance(v, (dict, list))
            ) or any(
                _has_ref(item)
                for v in d.values()
                if isinstance(v, list)
                for item in v
                if isinstance(item, dict)
            )

        assert not _has_ref(zd_result), "zerodep output still contains $ref"
        assert not _has_ref(js_result), "allof-merge output still contains $ref"


# ---------------------------------------------------------------------------
# Performance benchmarks
# ---------------------------------------------------------------------------


def _zd_flatten(schema: dict) -> None:
    flatten_schema(schema)


class TestPerfTiny:
    def test_zerodep(self, benchmark):
        benchmark(_zd_flatten, TINY_SCHEMA)

    @pytest.mark.skipif(not _HAS_NODE, reason="Node.js or npm deps missing")
    def test_allof_merge_js(self, benchmark):
        benchmark(_run_js, TINY_SCHEMA, 1)


class TestPerfSmall:
    def test_zerodep(self, benchmark):
        benchmark(_zd_flatten, SMALL_SCHEMA)

    @pytest.mark.skipif(not _HAS_NODE, reason="Node.js or npm deps missing")
    def test_allof_merge_js(self, benchmark):
        benchmark(_run_js, SMALL_SCHEMA, 1)


class TestPerfMedium:
    def test_zerodep(self, benchmark):
        benchmark(_zd_flatten, MEDIUM_SCHEMA)

    @pytest.mark.skipif(not _HAS_NODE, reason="Node.js or npm deps missing")
    def test_allof_merge_js(self, benchmark):
        benchmark(_run_js, MEDIUM_SCHEMA, 1)


class TestPerfLarge:
    def test_zerodep(self, benchmark):
        benchmark(_zd_flatten, LARGE_SCHEMA)

    @pytest.mark.skipif(not _HAS_NODE, reason="Node.js or npm deps missing")
    def test_allof_merge_js(self, benchmark):
        benchmark(_run_js, LARGE_SCHEMA, 1)


class TestPerfXlarge:
    def test_zerodep(self, benchmark):
        benchmark(_zd_flatten, XLARGE_SCHEMA)

    @pytest.mark.skipif(not _HAS_NODE, reason="Node.js or npm deps missing")
    def test_allof_merge_js(self, benchmark):
        benchmark(_run_js, XLARGE_SCHEMA, 1)
