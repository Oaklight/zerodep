"""Correctness tests for zerodep jsonschema module."""

import copy
import os
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

from jsonschema import (  # noqa: E402
    UNSUPPORTED_SCHEMA_KEYS,
    flatten_schema,
    merge_allof,
    resolve_refs,
    sanitize,
    simplify_unions,
)

# ---------------------------------------------------------------------------
# Phase 1 — resolve_refs
# ---------------------------------------------------------------------------


class TestResolveRefs:
    """$ref resolution tests."""

    def test_basic_defs(self):
        schema = {
            "type": "object",
            "properties": {"user": {"$ref": "#/$defs/User"}},
            "$defs": {
                "User": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            },
        }
        result = resolve_refs(schema)
        assert result["properties"]["user"] == {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        assert "$defs" not in result

    def test_definitions_key(self):
        schema = {
            "type": "object",
            "properties": {"item": {"$ref": "#/definitions/Item"}},
            "definitions": {
                "Item": {"type": "string"},
            },
        }
        result = resolve_refs(schema)
        assert result["properties"]["item"] == {"type": "string"}
        assert "definitions" not in result

    def test_sibling_keys_preserved(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "$ref": "#/$defs/User",
                    "description": "The user object",
                }
            },
            "$defs": {
                "User": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            },
        }
        result = resolve_refs(schema)
        user = result["properties"]["user"]
        assert user["description"] == "The user object"
        assert user["type"] == "object"

    def test_sibling_overrides_def(self):
        """Sibling keys should take priority over definition keys."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "$ref": "#/$defs/User",
                    "description": "overridden",
                }
            },
            "$defs": {
                "User": {
                    "type": "object",
                    "description": "from def",
                    "properties": {"name": {"type": "string"}},
                }
            },
        }
        result = resolve_refs(schema)
        assert result["properties"]["user"]["description"] == "overridden"

    def test_chained_refs(self):
        """A → B → C chain should resolve fully."""
        schema = {
            "type": "object",
            "properties": {"a": {"$ref": "#/$defs/A"}},
            "$defs": {
                "A": {"$ref": "#/$defs/B"},
                "B": {"type": "integer"},
            },
        }
        result = resolve_refs(schema)
        assert result["properties"]["a"] == {"type": "integer"}

    def test_unresolvable_ref_dropped(self):
        schema = {
            "type": "object",
            "properties": {
                "x": {"$ref": "#/$defs/Missing", "description": "kept"},
            },
            "$defs": {},
        }
        with pytest.warns(UserWarning, match="Unresolvable"):
            result = resolve_refs(schema)
        assert "$ref" not in result["properties"]["x"]
        assert result["properties"]["x"]["description"] == "kept"

    def test_nested_ref_in_items(self):
        schema = {
            "type": "array",
            "items": {"$ref": "#/$defs/Item"},
            "$defs": {"Item": {"type": "string"}},
        }
        result = resolve_refs(schema)
        assert result["items"] == {"type": "string"}

    def test_ref_in_allof(self):
        schema = {
            "allOf": [
                {"$ref": "#/$defs/Base"},
                {"properties": {"extra": {"type": "boolean"}}},
            ],
            "$defs": {
                "Base": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            },
        }
        result = resolve_refs(schema)
        # $ref inside allOf[0] should be resolved.
        assert result["allOf"][0] == {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }

    def test_input_not_mutated(self):
        schema = {
            "properties": {"x": {"$ref": "#/$defs/X"}},
            "$defs": {"X": {"type": "string"}},
        }
        original = copy.deepcopy(schema)
        resolve_refs(schema)
        assert schema == original

    def test_generic_json_pointer(self):
        """OpenAPI-style #/components/schemas/XXX reference."""
        schema = {
            "type": "object",
            "properties": {
                "error": {"$ref": "#/components/schemas/Error"},
            },
            "components": {
                "schemas": {
                    "Error": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "integer"},
                            "message": {"type": "string"},
                        },
                    }
                }
            },
        }
        result = resolve_refs(schema)
        assert result["properties"]["error"] == {
            "type": "object",
            "properties": {
                "code": {"type": "integer"},
                "message": {"type": "string"},
            },
        }
        # components should NOT be stripped (only $defs/definitions are)
        assert "components" in result

    def test_deeply_nested_pointer(self):
        """Multi-segment JSON Pointer resolution."""
        schema = {
            "type": "object",
            "properties": {
                "item": {"$ref": "#/a/b/c/Item"},
            },
            "a": {"b": {"c": {"Item": {"type": "string"}}}},
        }
        result = resolve_refs(schema)
        assert result["properties"]["item"] == {"type": "string"}

    def test_rfc6901_escapes(self):
        """RFC 6901: ~0 → ~, ~1 → /."""
        schema = {
            "type": "object",
            "properties": {
                "x": {"$ref": "#/$defs/a~1b"},
            },
            "$defs": {
                "a/b": {"type": "integer"},
            },
        }
        result = resolve_refs(schema)
        assert result["properties"]["x"] == {"type": "integer"}

    def test_circular_ref_protection(self):
        """Circular $ref should not cause infinite recursion."""
        schema = {
            "type": "object",
            "properties": {
                "node": {"$ref": "#/$defs/Node"},
            },
            "$defs": {
                "Node": {
                    "type": "object",
                    "properties": {
                        "child": {"$ref": "#/$defs/Node"},
                    },
                }
            },
        }
        result = resolve_refs(schema)
        # First level resolved
        node = result["properties"]["node"]
        assert node["type"] == "object"
        # Second level: circular ref dropped, child has no $ref
        child = node["properties"]["child"]
        assert "$ref" not in child

    def test_openapi_style_spec(self):
        """Full OpenAPI-like spec with components/schemas references."""
        schema = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {
                                                "$ref": "#/components/schemas/User"
                                            },
                                        }
                                    }
                                }
                            },
                            "422": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/Error"}
                                    }
                                }
                            },
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                        },
                    },
                    "Error": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "array",
                                "items": {
                                    "$ref": "#/components/schemas/ValidationError"
                                },
                            }
                        },
                    },
                    "ValidationError": {
                        "type": "object",
                        "properties": {
                            "loc": {"type": "array", "items": {"type": "string"}},
                            "msg": {"type": "string"},
                        },
                    },
                }
            },
        }
        result = resolve_refs(schema)

        # User inlined in items
        items = result["paths"]["/users"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["items"]
        assert items["type"] == "object"
        assert "id" in items["properties"]

        # Error inlined, with nested ValidationError also resolved
        error = result["paths"]["/users"]["get"]["responses"]["422"]["content"][
            "application/json"
        ]["schema"]
        assert error["type"] == "object"
        detail_items = error["properties"]["detail"]["items"]
        assert detail_items["type"] == "object"
        assert "msg" in detail_items["properties"]


# ---------------------------------------------------------------------------
# Phase 2 — merge_allof
# ---------------------------------------------------------------------------


class TestMergeAllOf:
    """allOf merging tests."""

    def test_single_element_unwrap(self):
        schema = {
            "allOf": [{"type": "object", "properties": {"a": {"type": "string"}}}]
        }
        result = merge_allof(schema)
        assert "allOf" not in result
        assert result["type"] == "object"
        assert result["properties"]["a"] == {"type": "string"}

    def test_merge_properties(self):
        schema = {
            "allOf": [
                {"type": "object", "properties": {"a": {"type": "string"}}},
                {"type": "object", "properties": {"b": {"type": "integer"}}},
            ]
        }
        result = merge_allof(schema)
        assert result["properties"]["a"] == {"type": "string"}
        assert result["properties"]["b"] == {"type": "integer"}

    def test_deep_merge_nested_properties(self):
        """Properties appearing in multiple allOf sub-schemas should be deep-merged."""
        schema = {
            "allOf": [
                {
                    "type": "object",
                    "properties": {
                        "user": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                        }
                    },
                },
                {
                    "type": "object",
                    "properties": {
                        "user": {
                            "type": "object",
                            "properties": {"age": {"type": "integer"}},
                        }
                    },
                },
            ]
        }
        result = merge_allof(schema)
        user = result["properties"]["user"]
        assert "name" in user["properties"]
        assert "age" in user["properties"]

    def test_required_union(self):
        schema = {
            "allOf": [
                {"required": ["a", "b"]},
                {"required": ["b", "c"]},
            ]
        }
        result = merge_allof(schema)
        assert result["required"] == ["a", "b", "c"]

    def test_type_intersection(self):
        schema = {
            "allOf": [
                {"type": ["object", "null"]},
                {"type": ["object", "string"]},
            ]
        }
        result = merge_allof(schema)
        assert result["type"] == "object"

    def test_type_intersection_no_overlap(self):
        schema = {
            "allOf": [
                {"type": "string"},
                {"type": "integer"},
            ]
        }
        result = merge_allof(schema)
        # Fallback: keep base type.
        assert result["type"] == "string"

    def test_numeric_constraints_tighten(self):
        schema = {
            "allOf": [
                {"minimum": 0, "maximum": 100},
                {"minimum": 10, "maximum": 50},
            ]
        }
        result = merge_allof(schema)
        assert result["minimum"] == 10  # max of lower bounds
        assert result["maximum"] == 50  # min of upper bounds

    def test_exclusive_constraints(self):
        schema = {
            "allOf": [
                {"exclusiveMinimum": 0, "exclusiveMaximum": 100},
                {"exclusiveMinimum": 5, "exclusiveMaximum": 80},
            ]
        }
        result = merge_allof(schema)
        assert result["exclusiveMinimum"] == 5
        assert result["exclusiveMaximum"] == 80

    def test_length_constraints(self):
        schema = {
            "allOf": [
                {"minLength": 1, "maxLength": 100},
                {"minLength": 5, "maxLength": 50},
            ]
        }
        result = merge_allof(schema)
        assert result["minLength"] == 5
        assert result["maxLength"] == 50

    def test_enum_intersection(self):
        schema = {
            "allOf": [
                {"enum": ["a", "b", "c"]},
                {"enum": ["b", "c", "d"]},
            ]
        }
        result = merge_allof(schema)
        assert result["enum"] == ["b", "c"]

    def test_enum_intersection_empty_fallback(self):
        schema = {
            "allOf": [
                {"enum": ["a"]},
                {"enum": ["b"]},
            ]
        }
        result = merge_allof(schema)
        # Fallback to override when intersection is empty.
        assert result["enum"] == ["b"]

    def test_items_deep_merge(self):
        schema = {
            "allOf": [
                {"items": {"type": "object", "properties": {"x": {"type": "string"}}}},
                {"items": {"type": "object", "properties": {"y": {"type": "integer"}}}},
            ]
        }
        result = merge_allof(schema)
        assert "x" in result["items"]["properties"]
        assert "y" in result["items"]["properties"]

    def test_sibling_keys_kept(self):
        schema = {
            "description": "top-level desc",
            "allOf": [
                {"type": "object", "properties": {"a": {"type": "string"}}},
            ],
        }
        result = merge_allof(schema)
        assert result["description"] == "top-level desc"
        assert result["type"] == "object"

    def test_nested_allof(self):
        schema = {
            "type": "object",
            "properties": {
                "inner": {
                    "allOf": [
                        {"type": "object", "properties": {"x": {"type": "string"}}},
                        {"properties": {"y": {"type": "integer"}}},
                    ]
                }
            },
        }
        result = merge_allof(schema)
        inner = result["properties"]["inner"]
        assert "allOf" not in inner
        assert "x" in inner["properties"]
        assert "y" in inner["properties"]

    def test_input_not_mutated(self):
        schema = {"allOf": [{"type": "string"}, {"minLength": 1}]}
        original = copy.deepcopy(schema)
        merge_allof(schema)
        assert schema == original

    def test_additional_properties_merge(self):
        schema = {
            "allOf": [
                {"additionalProperties": {"type": "string", "minLength": 1}},
                {"additionalProperties": {"type": "string", "maxLength": 100}},
            ]
        }
        result = merge_allof(schema)
        ap = result["additionalProperties"]
        assert ap["type"] == "string"
        assert ap["minLength"] == 1
        assert ap["maxLength"] == 100


# ---------------------------------------------------------------------------
# Phase 3 — simplify_unions
# ---------------------------------------------------------------------------


class TestSimplifyUnions:
    """anyOf/oneOf simplification tests."""

    def test_nullable_anyof(self):
        schema = {
            "anyOf": [
                {"type": "string"},
                {"type": "null"},
            ]
        }
        result = simplify_unions(schema)
        assert result["type"] == "string"
        assert result["nullable"] is True
        assert "anyOf" not in result

    def test_nullable_oneof(self):
        schema = {
            "oneOf": [
                {"type": "integer"},
                {"type": "null"},
            ]
        }
        result = simplify_unions(schema)
        assert result["type"] == "integer"
        assert result["nullable"] is True

    def test_single_variant_no_null(self):
        schema = {"anyOf": [{"type": "string", "minLength": 1}]}
        result = simplify_unions(schema)
        assert result["type"] == "string"
        assert result["minLength"] == 1
        assert "nullable" not in result
        assert "anyOf" not in result

    def test_multi_variant_keeps_first(self):
        schema = {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"},
            ]
        }
        result = simplify_unions(schema)
        assert result["type"] == "string"
        assert "anyOf" not in result

    def test_multi_variant_with_null(self):
        schema = {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"},
                {"type": "null"},
            ]
        }
        result = simplify_unions(schema)
        assert result["type"] == "string"
        assert result["nullable"] is True

    def test_all_null_variants(self):
        schema = {"anyOf": [{"type": "null"}, {"type": "null"}]}
        result = simplify_unions(schema)
        assert result.get("nullable") is True
        assert "anyOf" not in result

    def test_sibling_keys_preserved(self):
        schema = {
            "description": "a nullable string",
            "anyOf": [
                {"type": "string"},
                {"type": "null"},
            ],
        }
        result = simplify_unions(schema)
        assert result["description"] == "a nullable string"
        assert result["type"] == "string"
        assert result["nullable"] is True

    def test_sibling_deep_merged(self):
        """Sibling keys should be deep-merged, not shallow-overwritten."""
        schema = {
            "title": "MyField",
            "anyOf": [
                {
                    "type": "object",
                    "properties": {"a": {"type": "string"}},
                },
                {"type": "null"},
            ],
        }
        result = simplify_unions(schema)
        assert result["title"] == "MyField"
        assert result["properties"]["a"] == {"type": "string"}
        assert result["nullable"] is True

    def test_nested_anyof(self):
        schema = {
            "type": "object",
            "properties": {
                "field": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                }
            },
        }
        result = simplify_unions(schema)
        field = result["properties"]["field"]
        assert field["type"] == "string"
        assert field["nullable"] is True

    def test_input_not_mutated(self):
        schema = {"anyOf": [{"type": "string"}, {"type": "null"}]}
        original = copy.deepcopy(schema)
        simplify_unions(schema)
        assert schema == original

    def test_nullable_object_with_properties(self):
        """Complex nullable object: ensure properties are fully preserved."""
        schema = {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                    "required": ["name"],
                },
                {"type": "null"},
            ]
        }
        result = simplify_unions(schema)
        assert result["type"] == "object"
        assert result["nullable"] is True
        assert result["properties"]["name"] == {"type": "string"}
        assert result["properties"]["age"] == {"type": "integer"}
        assert result["required"] == ["name"]


# ---------------------------------------------------------------------------
# Phase 4 — sanitize
# ---------------------------------------------------------------------------


class TestSanitize:
    """Sanitization and required-pruning tests."""

    def test_strip_default_keys(self):
        schema = {
            "type": "object",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$comment": "test",
            "deprecated": True,
            "readOnly": True,
            "examples": [{}],
            "properties": {"a": {"type": "string"}},
        }
        result = sanitize(schema)
        for key in ("$schema", "$comment", "deprecated", "readOnly", "examples"):
            assert key not in result
        assert result["properties"]["a"] == {"type": "string"}

    def test_strip_nested(self):
        schema = {
            "type": "object",
            "properties": {
                "a": {
                    "type": "string",
                    "deprecated": True,
                    "examples": ["hello"],
                }
            },
        }
        result = sanitize(schema)
        assert "deprecated" not in result["properties"]["a"]
        assert "examples" not in result["properties"]["a"]

    def test_extra_strip_keys(self):
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"a": {"type": "string"}},
        }
        result = sanitize(schema, strip_keys={"additionalProperties"})
        assert "additionalProperties" not in result

    def test_required_pruned(self):
        schema = {
            "type": "object",
            "properties": {"a": {"type": "string"}},
            "required": ["a", "b", "c"],
        }
        result = sanitize(schema)
        assert result["required"] == ["a"]

    def test_required_all_orphaned(self):
        schema = {
            "type": "object",
            "properties": {"a": {"type": "string"}},
            "required": ["x", "y"],
        }
        result = sanitize(schema)
        assert "required" not in result

    def test_required_pruned_nested(self):
        schema = {
            "type": "object",
            "properties": {
                "inner": {
                    "type": "object",
                    "properties": {"x": {"type": "string"}},
                    "required": ["x", "y"],
                }
            },
        }
        result = sanitize(schema)
        assert result["properties"]["inner"]["required"] == ["x"]

    def test_required_without_properties_untouched(self):
        """If there's no 'properties', required should not be pruned."""
        schema = {"required": ["a", "b"]}
        result = sanitize(schema)
        assert result["required"] == ["a", "b"]

    def test_strip_in_array_items(self):
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "$comment": "should be stripped",
                "properties": {"x": {"type": "string"}},
            },
        }
        result = sanitize(schema)
        assert "$comment" not in result["items"]

    def test_input_not_mutated(self):
        schema = {"type": "string", "$comment": "test"}
        original = copy.deepcopy(schema)
        sanitize(schema)
        assert schema == original


# ---------------------------------------------------------------------------
# Phase 5 — flatten_schema (integration)
# ---------------------------------------------------------------------------


class TestFlattenSchema:
    """Full pipeline integration tests."""

    def test_simple_passthrough(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        result = flatten_schema(schema)
        assert result == schema

    def test_ref_plus_allof(self):
        schema = {
            "allOf": [
                {"$ref": "#/$defs/Base"},
                {"properties": {"extra": {"type": "boolean"}}, "required": ["extra"]},
            ],
            "$defs": {
                "Base": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                }
            },
        }
        result = flatten_schema(schema)
        assert "$defs" not in result
        assert "allOf" not in result
        assert result["type"] == "object"
        assert result["properties"]["name"] == {"type": "string"}
        assert result["properties"]["extra"] == {"type": "boolean"}
        assert set(result["required"]) == {"name", "extra"}

    def test_ref_plus_anyof_nullable(self):
        schema = {
            "type": "object",
            "properties": {
                "address": {
                    "anyOf": [
                        {"$ref": "#/$defs/Address"},
                        {"type": "null"},
                    ]
                }
            },
            "$defs": {
                "Address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                    },
                }
            },
        }
        result = flatten_schema(schema)
        addr = result["properties"]["address"]
        assert addr["type"] == "object"
        assert addr["nullable"] is True
        assert "street" in addr["properties"]

    def test_full_pipeline(self):
        """Complex schema with $ref + allOf + anyOf + unsupported keys."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "config": {
                    "allOf": [
                        {"$ref": "#/$defs/BaseConfig"},
                        {
                            "properties": {
                                "timeout": {"type": "integer", "minimum": 1},
                            },
                            "required": ["timeout"],
                        },
                    ]
                },
                "label": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "null"},
                    ],
                    "description": "Optional label",
                    "deprecated": True,
                },
            },
            "$defs": {
                "BaseConfig": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string", "$comment": "server host"},
                    },
                    "required": ["host"],
                }
            },
        }
        result = flatten_schema(schema)

        # $ref resolved, $defs removed
        assert "$defs" not in result
        assert "$schema" not in result

        # allOf merged
        config = result["properties"]["config"]
        assert "allOf" not in config
        assert config["type"] == "object"
        assert "host" in config["properties"]
        assert "timeout" in config["properties"]
        assert set(config["required"]) == {"host", "timeout"}
        assert "$comment" not in config["properties"]["host"]

        # anyOf simplified
        label = result["properties"]["label"]
        assert label["type"] == "string"
        assert label["nullable"] is True
        assert label["description"] == "Optional label"
        assert "deprecated" not in label

    def test_input_not_mutated(self):
        schema = {
            "allOf": [{"type": "string"}, {"minLength": 1}],
            "$defs": {"X": {"type": "integer"}},
        }
        original = copy.deepcopy(schema)
        flatten_schema(schema)
        assert schema == original

    def test_real_world_llm_tool_schema(self):
        """Schema resembling a real LLM tool definition."""
        schema = {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "filters": {
                    "allOf": [
                        {"$ref": "#/$defs/BaseFilter"},
                        {
                            "properties": {
                                "date_range": {
                                    "anyOf": [
                                        {
                                            "type": "object",
                                            "properties": {
                                                "start": {"type": "string"},
                                                "end": {"type": "string"},
                                            },
                                        },
                                        {"type": "null"},
                                    ],
                                }
                            }
                        },
                    ],
                },
            },
            "required": ["query", "filters"],
            "$defs": {
                "BaseFilter": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "$comment": "max results",
                        },
                    },
                    "required": ["limit"],
                }
            },
        }
        result = flatten_schema(schema)

        assert "$defs" not in result
        assert "allOf" not in result
        filters = result["properties"]["filters"]
        assert filters["type"] == "object"
        assert "limit" in filters["properties"]
        assert "$comment" not in filters["properties"]["limit"]

        date_range = filters["properties"]["date_range"]
        assert date_range["type"] == "object"
        assert date_range["nullable"] is True
        assert "start" in date_range["properties"]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_schema(self):
        assert flatten_schema({}) == {}

    def test_no_ops_needed(self):
        schema = {"type": "string", "minLength": 1}
        assert flatten_schema(schema) == schema

    def test_deeply_nested(self):
        schema = {
            "type": "object",
            "properties": {
                "level1": {
                    "type": "object",
                    "properties": {
                        "level2": {
                            "type": "array",
                            "items": {
                                "allOf": [
                                    {
                                        "type": "object",
                                        "properties": {"a": {"type": "string"}},
                                    },  # noqa: E501
                                    {"properties": {"b": {"type": "integer"}}},
                                ]
                            },
                        }
                    },
                }
            },
        }
        result = flatten_schema(schema)
        item = result["properties"]["level1"]["properties"]["level2"]["items"]
        assert "allOf" not in item
        assert "a" in item["properties"]
        assert "b" in item["properties"]

    def test_allof_empty_list(self):
        schema = {"allOf": [], "type": "object"}
        result = merge_allof(schema)
        assert result == {"type": "object"}

    def test_anyof_not_a_list(self):
        """Non-list anyOf should be left alone."""
        schema = {"anyOf": "invalid"}
        result = simplify_unions(schema)
        assert result == {"anyOf": "invalid"}

    def test_strip_keys_constant_completeness(self):
        """Verify UNSUPPORTED_SCHEMA_KEYS contains expected entries."""
        expected = {
            "$schema",
            "$id",
            "$comment",
            "$anchor",
            "$dynamicAnchor",
            "$dynamicRef",
            "contentEncoding",
            "contentMediaType",
            "contentSchema",
            "deprecated",
            "readOnly",
            "writeOnly",
            "examples",
            "propertyNames",
            "const",
        }
        assert UNSUPPORTED_SCHEMA_KEYS == expected
