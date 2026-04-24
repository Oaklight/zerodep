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

# Our jsonschema.py shadows the third-party 'jsonschema' package (pulled in
# by pydantic / other deps).  Evict it from sys.modules before importing ours.
_this_dir = os.path.dirname(__file__)
_cached_jsonschema = sys.modules.pop("jsonschema", None)
_cached_jsonschema_sub = {}
for _k in list(sys.modules):
    if _k.startswith("jsonschema."):
        _cached_jsonschema_sub[_k] = sys.modules.pop(_k)

sys.path.insert(0, _this_dir)

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
#
# allof-merge only resolves $ref and merges allOf.  It does NOT simplify
# anyOf/oneOf or strip unsupported keys.  So we compare zerodep's
# resolve_refs + merge_allof (Phase 1+2) against allof-merge's output.
# ---------------------------------------------------------------------------


def _normalize(schema: dict) -> dict:
    """Sort keys and required arrays for deterministic comparison."""
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


def _collect_diffs(zd: dict, js: dict, path: str = "") -> list[str]:
    """Recursively compare two schema dicts, returning human-readable diffs.

    Skips ``$defs``/``definitions`` (zerodep strips them, allof-merge keeps).
    """
    if not isinstance(zd, dict) or not isinstance(js, dict):
        if zd != js:
            return [f"{path}: {zd!r} vs {js!r}"]
        return []

    diffs: list[str] = []
    zd_n = _normalize(zd)
    js_n = _normalize(js)

    # If JS side still has a $ref (not inlined), skip this subtree —
    # zerodep inlined it so the shapes are legitimately different.
    if "$ref" in js_n:
        return []

    all_keys = set(zd_n) | set(js_n)
    # zerodep strips $defs and inlines all $ref (including inside anyOf);
    # allof-merge keeps $defs and only inlines $ref inside allOf.
    skip_keys = {"$defs", "definitions", "$ref"}
    for key in sorted(all_keys - skip_keys):
        zval = zd_n.get(key)
        jval = js_n.get(key)
        if zval == jval:
            continue
        if isinstance(zval, dict) and isinstance(jval, dict):
            diffs.extend(_collect_diffs(zval, jval, f"{path}.{key}"))
        elif isinstance(zval, list) and isinstance(jval, list):
            if len(zval) != len(jval):
                diffs.append(f"{path}.{key}: len {len(zval)} vs {len(jval)}")
            else:
                for i, (a, b) in enumerate(zip(zval, jval)):
                    if isinstance(a, dict) and isinstance(b, dict):
                        diffs.extend(_collect_diffs(a, b, f"{path}.{key}[{i}]"))
                    elif a != b:
                        diffs.append(f"{path}.{key}[{i}]: {a!r} vs {b!r}")
        else:
            diffs.append(f"{path}.{key}: {zval!r} vs {jval!r}")
    return diffs


def _has_keyword(d: dict, keyword: str) -> bool:
    """Check if *keyword* appears anywhere in *d* recursively."""
    if not isinstance(d, dict):
        return False
    if keyword in d:
        return True
    for v in d.values():
        if isinstance(v, dict) and _has_keyword(v, keyword):
            return True
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict) and _has_keyword(item, keyword):
                    return True
    return False


@pytest.mark.skipif(not _HAS_NODE, reason="Node.js or npm deps missing")
class TestCorrectnessVsJs:
    """Compare zerodep resolve_refs+merge_allof against allof-merge.

    Only Phase 1+2 are comparable — allof-merge does not simplify
    anyOf/oneOf or strip unsupported keys.
    """

    @pytest.mark.parametrize("tier", ["tiny", "small", "medium", "large", "xlarge"])
    def test_structural_match(self, tier):
        schema = ALL_SCHEMAS[tier]
        # zerodep: Phase 1 + Phase 2 only (matching allof-merge scope).
        zd_result = merge_allof(resolve_refs(schema))
        js_output = _run_js(schema, rounds=1)
        js_result = js_output["result"]
        diffs = _collect_diffs(zd_result, js_result)
        assert not diffs, f"Structural differences at {tier}:\n" + "\n".join(diffs)

    @pytest.mark.parametrize("tier", ["medium", "large", "xlarge"])
    def test_allof_fully_resolved(self, tier):
        """Both implementations should eliminate all allOf keywords."""
        schema = ALL_SCHEMAS[tier]
        zd_result = merge_allof(resolve_refs(schema))
        js_result = _run_js(schema, rounds=1)["result"]
        assert not _has_keyword(zd_result, "allOf"), "zerodep still has allOf"
        assert not _has_keyword(js_result, "allOf"), "allof-merge still has allOf"

    @pytest.mark.parametrize("tier", ["medium", "large", "xlarge"])
    def test_zerodep_refs_fully_resolved(self, tier):
        """zerodep should eliminate all $ref pointers."""
        schema = ALL_SCHEMAS[tier]
        zd_result = merge_allof(resolve_refs(schema))
        assert not _has_keyword(zd_result, "$ref"), "zerodep still has $ref"

    @pytest.mark.parametrize("tier", ["medium", "large"])
    def test_js_refs_resolved_in_allof(self, tier):
        """allof-merge resolves $ref inside allOf contexts."""
        schema = ALL_SCHEMAS[tier]
        js_result = _run_js(schema, rounds=1)["result"]
        assert not _has_keyword(js_result, "$ref"), "allof-merge still has $ref"


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
