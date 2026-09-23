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
    SchemaValidationError,
    flatten_schema,
    iter_errors,
    merge_allof,
    resolve_refs,
    sanitize,
    schema_validate,
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

    def test_multi_variant_preserved(self):
        schema = {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"},
            ]
        }
        result = simplify_unions(schema)
        assert result["anyOf"] == [{"type": "string"}, {"type": "integer"}]
        assert "nullable" not in result

    def test_multi_variant_with_null(self):
        schema = {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"},
                {"type": "null"},
            ]
        }
        result = simplify_unions(schema)
        assert result["anyOf"] == [{"type": "string"}, {"type": "integer"}]
        assert result["nullable"] is True

    def test_multi_variant_number_and_array(self):
        schema = {
            "anyOf": [
                {"type": "number"},
                {"type": "array", "items": {"type": "number"}},
                {"type": "null"},
            ]
        }
        result = simplify_unions(schema)
        assert result["anyOf"] == [
            {"type": "number"},
            {"type": "array", "items": {"type": "number"}},
        ]
        assert result["nullable"] is True

    def test_multi_variant_no_null(self):
        schema = {
            "oneOf": [
                {"type": "string"},
                {"type": "number"},
                {"type": "boolean"},
            ]
        }
        result = simplify_unions(schema)
        assert result["anyOf"] == [
            {"type": "string"},
            {"type": "number"},
            {"type": "boolean"},
        ]
        assert "nullable" not in result

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


# ---------------------------------------------------------------------------
# Regression: position-aware walkers (issue #153)
# ---------------------------------------------------------------------------


class TestPropertyNameCollisions:
    """Parameter names that collide with schema keywords must survive."""

    def _tool_schema(self, **props):
        """Build a minimal tool-parameter schema."""
        return {
            "type": "object",
            "properties": props,
            "required": list(props),
        }

    # -- sanitize ----------------------------------------------------------

    def test_param_named_title_survives_sanitize(self):
        schema = self._tool_schema(
            title={"type": "string"},
            name={"type": "string"},
        )
        result = sanitize(schema, strip_keys={"title"})
        assert "title" in result["properties"]
        assert "title" in result["required"]

    def test_param_named_deprecated_survives_sanitize(self):
        schema = self._tool_schema(
            deprecated={"type": "boolean"},
            name={"type": "string"},
        )
        result = sanitize(schema)
        assert "deprecated" in result["properties"]

    def test_param_named_examples_survives_sanitize(self):
        schema = self._tool_schema(
            examples={"type": "array", "items": {"type": "string"}},
            query={"type": "string"},
        )
        result = sanitize(schema)
        assert "examples" in result["properties"]

    def test_param_named_nullable_survives_sanitize(self):
        schema = self._tool_schema(
            nullable={"type": "boolean"},
            value={"type": "integer"},
        )
        result = sanitize(schema, strip_keys={"nullable"})
        assert "nullable" in result["properties"]

    def test_param_named_const_survives_sanitize(self):
        schema = self._tool_schema(
            const={"type": "string"},
        )
        result = sanitize(schema)
        assert "const" in result["properties"]

    def test_pattern_property_key_survives_sanitize(self):
        schema = {
            "type": "object",
            "patternProperties": {
                "title": {"type": "string"},
                "^x-": {"type": "string"},
            },
        }
        result = sanitize(schema, strip_keys={"title"})
        assert "title" in result["patternProperties"]

    def test_dependent_schemas_key_survives_sanitize(self):
        schema = {
            "type": "object",
            "properties": {"mode": {"type": "string"}},
            "dependentSchemas": {
                "title": {
                    "properties": {"subtitle": {"type": "string"}},
                },
            },
        }
        result = sanitize(schema, strip_keys={"title"})
        assert "title" in result["dependentSchemas"]

    def test_schema_keyword_title_still_stripped(self):
        """title as a schema keyword (not a param name) should still be stripped."""
        schema = {
            "type": "object",
            "title": "MyModel",
            "properties": {
                "name": {"type": "string", "title": "Name Field"},
            },
        }
        result = sanitize(schema, strip_keys={"title"})
        assert "title" not in result
        assert "title" not in result["properties"]["name"]
        assert "name" in result["properties"]

    def test_nested_object_param_named_title_survives(self):
        schema = {
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "size": {"type": "integer"},
                    },
                    "required": ["title"],
                },
            },
        }
        result = sanitize(schema, strip_keys={"title"})
        inner = result["properties"]["config"]["properties"]
        assert "title" in inner
        assert "title" in result["properties"]["config"]["required"]

    def test_required_preserved_when_param_name_collides(self):
        schema = self._tool_schema(
            data_path={"type": "string"},
            title={"type": "string"},
            width={"type": "integer"},
        )
        result = sanitize(schema, strip_keys={"title"})
        assert sorted(result["required"]) == ["data_path", "title", "width"]
        assert sorted(result["properties"]) == ["data_path", "title", "width"]

    # -- simplify_unions ---------------------------------------------------

    def test_param_named_anyOf_survives_simplify(self):
        """A parameter literally named 'anyOf' should not trigger simplification."""
        schema = {
            "type": "object",
            "properties": {
                "anyOf": {"type": "string", "description": "filter expression"},
                "name": {"type": "string"},
            },
        }
        result = simplify_unions(schema)
        assert "anyOf" in result["properties"]
        assert result["properties"]["anyOf"]["type"] == "string"

    # -- merge_allof -------------------------------------------------------

    def test_param_named_allOf_survives_merge(self):
        """A parameter literally named 'allOf' should not trigger merging."""
        schema = {
            "type": "object",
            "properties": {
                "allOf": {"type": "string", "description": "merge strategy"},
                "name": {"type": "string"},
            },
        }
        result = merge_allof(schema)
        assert "allOf" in result["properties"]
        assert result["properties"]["allOf"]["type"] == "string"

    # -- flatten_schema (full pipeline) ------------------------------------

    def test_flatten_preserves_title_param(self):
        """The exact scenario from toolregistry#265."""
        schema = {
            "type": "object",
            "properties": {
                "data_path": {"type": "string", "description": "input file"},
                "title": {"type": "string", "description": "figure title"},
                "width": {"type": "integer", "default": 800},
            },
            "required": ["data_path", "title"],
        }
        result = flatten_schema(schema, strip_keys={"title", "nullable"})
        assert sorted(result["properties"]) == ["data_path", "title", "width"]
        assert sorted(result["required"]) == ["data_path", "title"]

    def test_flatten_preserves_multiple_colliding_params(self):
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "deprecated": {"type": "boolean", "default": False},
                "examples": {"type": "array", "items": {"type": "string"}},
                "name": {"type": "string"},
            },
            "required": ["title", "name"],
        }
        result = flatten_schema(schema, strip_keys={"title", "nullable"})
        props = result["properties"]
        assert "title" in props
        assert "deprecated" in props
        assert "examples" in props
        assert "name" in props

    def test_flatten_strips_schema_keywords_but_keeps_param_names(self):
        """Schema-level title stripped, param-level title kept."""
        schema = {
            "type": "object",
            "title": "PlotParams",
            "deprecated": True,
            "properties": {
                "title": {"type": "string", "title": "Title", "deprecated": True},
                "size": {"type": "integer", "examples": [100, 200]},
            },
            "required": ["title"],
        }
        result = flatten_schema(schema, strip_keys={"title", "nullable"})
        # Schema-level keywords stripped
        assert "title" not in result
        assert "deprecated" not in result
        # Param "title" survives
        assert "title" in result["properties"]
        assert result["required"] == ["title"]
        # Schema keywords inside param sub-schemas are stripped
        assert "title" not in result["properties"]["title"]
        assert "deprecated" not in result["properties"]["title"]
        assert "examples" not in result["properties"]["size"]

    def test_flatten_with_ref_and_colliding_param(self):
        """$ref resolution + sanitization should not eat param named 'title'."""
        schema = {
            "type": "object",
            "properties": {
                "title": {"$ref": "#/$defs/Title"},
                "count": {"type": "integer"},
            },
            "required": ["title"],
            "$defs": {
                "Title": {"type": "string", "minLength": 1},
            },
        }
        result = flatten_schema(schema, strip_keys={"title", "nullable"})
        assert "title" in result["properties"]
        assert result["properties"]["title"] == {"type": "string", "minLength": 1}
        assert "title" in result["required"]


# ---------------------------------------------------------------------------
# Phase 6 — Data validation
# ---------------------------------------------------------------------------


class TestSchemaValidateType:
    """Type keyword validation."""

    def test_string_valid(self):
        assert iter_errors("hello", {"type": "string"}) == []

    def test_string_invalid(self):
        errs = iter_errors(42, {"type": "string"})
        assert len(errs) == 1
        assert errs[0].validator == "type"

    def test_integer_valid(self):
        assert iter_errors(42, {"type": "integer"}) == []

    def test_integer_invalid(self):
        errs = iter_errors(3.14, {"type": "integer"})
        assert len(errs) == 1

    def test_integer_rejects_bool(self):
        errs = iter_errors(True, {"type": "integer"})
        assert len(errs) == 1

    def test_number_valid(self):
        assert iter_errors(3.14, {"type": "number"}) == []

    def test_number_accepts_int(self):
        assert iter_errors(42, {"type": "number"}) == []

    def test_number_rejects_bool(self):
        errs = iter_errors(False, {"type": "number"})
        assert len(errs) == 1

    def test_boolean_valid(self):
        assert iter_errors(True, {"type": "boolean"}) == []

    def test_boolean_invalid(self):
        errs = iter_errors(1, {"type": "boolean"})
        assert len(errs) == 1

    def test_null_valid(self):
        assert iter_errors(None, {"type": "null"}) == []

    def test_null_invalid(self):
        errs = iter_errors("", {"type": "null"})
        assert len(errs) == 1

    def test_array_valid(self):
        assert iter_errors([1, 2], {"type": "array"}) == []

    def test_array_invalid(self):
        errs = iter_errors("not array", {"type": "array"})
        assert len(errs) == 1

    def test_object_valid(self):
        assert iter_errors({"a": 1}, {"type": "object"}) == []

    def test_object_invalid(self):
        errs = iter_errors([1, 2], {"type": "object"})
        assert len(errs) == 1

    def test_type_array_accepts_any_listed(self):
        schema = {"type": ["string", "integer"]}
        assert iter_errors("hello", schema) == []
        assert iter_errors(42, schema) == []

    def test_type_array_rejects_unlisted(self):
        schema = {"type": ["string", "integer"]}
        errs = iter_errors(3.14, schema)
        assert len(errs) == 1

    def test_nullable_type_array(self):
        schema = {"type": ["string", "null"]}
        assert iter_errors(None, schema) == []
        assert iter_errors("hello", schema) == []
        errs = iter_errors(42, schema)
        assert len(errs) == 1

    def test_empty_schema_accepts_anything(self):
        assert iter_errors("anything", {}) == []
        assert iter_errors(42, {}) == []
        assert iter_errors(None, {}) == []
        assert iter_errors({"nested": [1, 2]}, {}) == []


class TestSchemaValidateEnum:
    """Enum keyword validation."""

    def test_enum_valid(self):
        assert iter_errors("red", {"enum": ["red", "green", "blue"]}) == []

    def test_enum_invalid(self):
        errs = iter_errors("yellow", {"enum": ["red", "green", "blue"]})
        assert len(errs) == 1
        assert errs[0].validator == "enum"

    def test_enum_with_null(self):
        schema = {"enum": ["a", "b", None]}
        assert iter_errors(None, schema) == []
        assert iter_errors("a", schema) == []

    def test_enum_with_types(self):
        schema = {"enum": [1, "one", True]}
        assert iter_errors(1, schema) == []
        assert iter_errors("one", schema) == []
        assert iter_errors(True, schema) == []


class TestSchemaValidateConst:
    """Const keyword validation."""

    def test_const_valid(self):
        assert iter_errors(42, {"const": 42}) == []

    def test_const_invalid(self):
        errs = iter_errors(43, {"const": 42})
        assert len(errs) == 1
        assert errs[0].validator == "const"

    def test_const_null(self):
        assert iter_errors(None, {"const": None}) == []
        errs = iter_errors("", {"const": None})
        assert len(errs) == 1


class TestSchemaValidateString:
    """String constraint keywords."""

    def test_minlength_valid(self):
        assert iter_errors("abc", {"type": "string", "minLength": 2}) == []

    def test_minlength_invalid(self):
        errs = iter_errors("a", {"type": "string", "minLength": 2})
        assert len(errs) == 1
        assert errs[0].validator == "minLength"

    def test_maxlength_valid(self):
        assert iter_errors("ab", {"type": "string", "maxLength": 5}) == []

    def test_maxlength_invalid(self):
        errs = iter_errors("toolong", {"type": "string", "maxLength": 3})
        assert len(errs) == 1
        assert errs[0].validator == "maxLength"

    def test_pattern_valid(self):
        assert (
            iter_errors("abc123", {"type": "string", "pattern": "^[a-z]+\\d+$"}) == []
        )

    def test_pattern_invalid(self):
        errs = iter_errors("ABC", {"type": "string", "pattern": "^[a-z]+$"})
        assert len(errs) == 1
        assert errs[0].validator == "pattern"

    def test_string_constraints_skip_non_string(self):
        assert iter_errors(42, {"minLength": 1, "maxLength": 10, "pattern": ".*"}) == []


class TestSchemaValidateNumber:
    """Numeric constraint keywords."""

    def test_minimum_valid(self):
        assert iter_errors(10, {"type": "number", "minimum": 5}) == []

    def test_minimum_invalid(self):
        errs = iter_errors(3, {"type": "number", "minimum": 5})
        assert len(errs) == 1
        assert errs[0].validator == "minimum"

    def test_maximum_valid(self):
        assert iter_errors(5, {"type": "number", "maximum": 10}) == []

    def test_maximum_invalid(self):
        errs = iter_errors(15, {"type": "number", "maximum": 10})
        assert len(errs) == 1
        assert errs[0].validator == "maximum"

    def test_exclusive_minimum_valid(self):
        assert iter_errors(6, {"type": "integer", "exclusiveMinimum": 5}) == []

    def test_exclusive_minimum_invalid(self):
        errs = iter_errors(5, {"type": "integer", "exclusiveMinimum": 5})
        assert len(errs) == 1
        assert errs[0].validator == "exclusiveMinimum"

    def test_exclusive_maximum_valid(self):
        assert iter_errors(4, {"type": "integer", "exclusiveMaximum": 5}) == []

    def test_exclusive_maximum_invalid(self):
        errs = iter_errors(5, {"type": "integer", "exclusiveMaximum": 5})
        assert len(errs) == 1
        assert errs[0].validator == "exclusiveMaximum"

    def test_multiple_of_valid(self):
        assert iter_errors(10, {"type": "integer", "multipleOf": 5}) == []

    def test_multiple_of_invalid(self):
        errs = iter_errors(7, {"type": "integer", "multipleOf": 3})
        assert len(errs) == 1
        assert errs[0].validator == "multipleOf"

    def test_multiple_of_float(self):
        assert iter_errors(0.5, {"type": "number", "multipleOf": 0.25}) == []
        errs = iter_errors(0.3, {"type": "number", "multipleOf": 0.25})
        assert len(errs) == 1

    def test_number_constraints_skip_non_number(self):
        assert iter_errors("hello", {"minimum": 0, "maximum": 100}) == []


class TestSchemaValidateObject:
    """Object keyword validation."""

    def test_required_present(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        assert iter_errors({"name": "Alice"}, schema) == []

    def test_required_missing(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        errs = iter_errors({}, schema)
        assert len(errs) == 1
        assert errs[0].validator == "required"

    def test_required_multiple_missing(self):
        schema = {"type": "object", "required": ["a", "b", "c"]}
        errs = iter_errors({"a": 1}, schema)
        assert len(errs) == 2  # b and c missing

    def test_properties_valid(self):
        schema = {"type": "object", "properties": {"age": {"type": "integer"}}}
        assert iter_errors({"age": 25}, schema) == []

    def test_properties_invalid_child(self):
        schema = {"type": "object", "properties": {"age": {"type": "integer"}}}
        errs = iter_errors({"age": "old"}, schema)
        assert len(errs) == 1
        assert errs[0].path == "age"

    def test_additional_properties_false(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": False,
        }
        assert iter_errors({"name": "Alice"}, schema) == []
        errs = iter_errors({"name": "Alice", "extra": 1}, schema)
        assert len(errs) == 1
        assert errs[0].validator == "additionalProperties"

    def test_additional_properties_schema(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": {"type": "integer"},
        }
        assert iter_errors({"name": "Alice", "age": 25}, schema) == []
        errs = iter_errors({"name": "Alice", "age": "old"}, schema)
        assert len(errs) == 1

    def test_pattern_properties(self):
        schema = {
            "type": "object",
            "patternProperties": {"^x-": {"type": "string"}},
        }
        assert iter_errors({"x-custom": "hello"}, schema) == []
        errs = iter_errors({"x-custom": 42}, schema)
        assert len(errs) == 1

    def test_pattern_properties_with_additional(self):
        schema = {
            "type": "object",
            "patternProperties": {"^x-": {"type": "string"}},
            "additionalProperties": False,
        }
        assert iter_errors({"x-ext": "val"}, schema) == []
        errs = iter_errors({"x-ext": "val", "other": 1}, schema)
        assert len(errs) == 1
        assert errs[0].validator == "additionalProperties"

    def test_min_max_properties(self):
        schema = {"type": "object", "minProperties": 1, "maxProperties": 2}
        assert iter_errors({"a": 1}, schema) == []
        errs_min = iter_errors({}, schema)
        assert len(errs_min) == 1
        assert errs_min[0].validator == "minProperties"
        errs_max = iter_errors({"a": 1, "b": 2, "c": 3}, schema)
        assert len(errs_max) == 1
        assert errs_max[0].validator == "maxProperties"


class TestSchemaValidateArray:
    """Array keyword validation."""

    def test_items_valid(self):
        schema = {"type": "array", "items": {"type": "integer"}}
        assert iter_errors([1, 2, 3], schema) == []

    def test_items_invalid_child(self):
        schema = {"type": "array", "items": {"type": "integer"}}
        errs = iter_errors([1, "two", 3], schema)
        assert len(errs) == 1
        assert errs[0].path == "[1]"

    def test_min_items(self):
        schema = {"type": "array", "minItems": 2}
        assert iter_errors([1, 2], schema) == []
        errs = iter_errors([1], schema)
        assert len(errs) == 1
        assert errs[0].validator == "minItems"

    def test_max_items(self):
        schema = {"type": "array", "maxItems": 2}
        assert iter_errors([1, 2], schema) == []
        errs = iter_errors([1, 2, 3], schema)
        assert len(errs) == 1
        assert errs[0].validator == "maxItems"

    def test_unique_items_valid(self):
        schema = {"type": "array", "uniqueItems": True}
        assert iter_errors([1, 2, 3], schema) == []

    def test_unique_items_invalid(self):
        schema = {"type": "array", "uniqueItems": True}
        errs = iter_errors([1, 2, 2, 3], schema)
        assert len(errs) == 1
        assert errs[0].validator == "uniqueItems"

    def test_unique_items_unhashable(self):
        schema = {"type": "array", "uniqueItems": True}
        assert iter_errors([{"a": 1}, {"b": 2}], schema) == []
        errs = iter_errors([{"a": 1}, {"a": 1}], schema)
        assert len(errs) == 1

    def test_prefix_items(self):
        schema = {
            "type": "array",
            "prefixItems": [
                {"type": "string"},
                {"type": "integer"},
            ],
        }
        assert iter_errors(["hello", 42], schema) == []
        errs = iter_errors([42, "hello"], schema)
        assert len(errs) == 2  # both wrong type

    def test_prefix_items_with_items_false(self):
        schema = {
            "type": "array",
            "prefixItems": [{"type": "string"}],
            "items": False,
        }
        assert iter_errors(["hello"], schema) == []
        errs = iter_errors(["hello", "extra"], schema)
        assert len(errs) == 1
        assert errs[0].validator == "items"

    def test_contains(self):
        schema = {"type": "array", "contains": {"type": "integer"}}
        assert iter_errors(["a", 1, "b"], schema) == []
        errs = iter_errors(["a", "b", "c"], schema)
        assert len(errs) == 1
        assert errs[0].validator == "contains"


class TestSchemaValidateComposition:
    """Composition keyword validation (allOf, anyOf, oneOf, not)."""

    def test_allof_both_pass(self):
        schema = {
            "allOf": [
                {"type": "object", "properties": {"name": {"type": "string"}}},
                {"required": ["name"]},
            ]
        }
        assert iter_errors({"name": "Alice"}, schema) == []

    def test_allof_one_fails(self):
        schema = {
            "allOf": [
                {"type": "object"},
                {"required": ["name"]},
            ]
        }
        errs = iter_errors({}, schema)
        assert len(errs) == 1
        assert errs[0].validator == "required"

    def test_anyof_one_matches(self):
        schema = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
        assert iter_errors("hello", schema) == []
        assert iter_errors(42, schema) == []

    def test_anyof_none_matches(self):
        schema = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
        errs = iter_errors(3.14, schema)
        assert len(errs) == 1
        assert errs[0].validator == "anyOf"

    def test_oneof_exactly_one(self):
        schema = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
        assert iter_errors("hello", schema) == []

    def test_oneof_none_match(self):
        schema = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
        errs = iter_errors(3.14, schema)
        assert len(errs) == 1
        assert errs[0].validator == "oneOf"
        assert "does not match" in errs[0].message

    def test_oneof_two_match(self):
        schema = {"oneOf": [{"type": "number"}, {"type": "integer"}]}
        errs = iter_errors(42, schema)
        assert len(errs) == 1
        assert errs[0].validator == "oneOf"
        assert "more than one" in errs[0].message

    def test_not_passes(self):
        schema = {"not": {"type": "string"}}
        assert iter_errors(42, schema) == []

    def test_not_fails(self):
        schema = {"not": {"type": "string"}}
        errs = iter_errors("hello", schema)
        assert len(errs) == 1
        assert errs[0].validator == "not"

    def test_nested_composition(self):
        schema = {
            "allOf": [
                {"anyOf": [{"type": "object"}, {"type": "null"}]},
                {
                    "type": "object",
                    "properties": {
                        "status": {
                            "oneOf": [{"const": "active"}, {"const": "inactive"}]
                        }
                    },
                },
            ]
        }
        assert iter_errors({"status": "active"}, schema) == []
        errs = iter_errors({"status": "unknown"}, schema)
        assert len(errs) == 1
        assert errs[0].validator == "oneOf"

    def test_if_then_else(self):
        schema = {
            "type": "object",
            "properties": {"kind": {"type": "string"}, "value": {}},
            "if": {"properties": {"kind": {"const": "number"}}},
            "then": {"properties": {"value": {"type": "number"}}},
            "else": {"properties": {"value": {"type": "string"}}},
        }
        assert iter_errors({"kind": "number", "value": 42}, schema) == []
        assert iter_errors({"kind": "text", "value": "hello"}, schema) == []
        errs = iter_errors({"kind": "number", "value": "not a number"}, schema)
        assert len(errs) == 1
        assert errs[0].validator == "type"


class TestSchemaValidateRef:
    """$ref resolution before validation."""

    def test_ref_resolved_before_validation(self):
        schema = {
            "type": "object",
            "properties": {"user": {"$ref": "#/$defs/User"}},
            "$defs": {
                "User": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                }
            },
        }
        assert iter_errors({"user": {"name": "Alice"}}, schema) == []
        errs = iter_errors({"user": {}}, schema)
        assert len(errs) == 1
        assert errs[0].validator == "required"

    def test_ref_with_allof_composition(self):
        schema = {
            "allOf": [
                {"$ref": "#/$defs/Base"},
                {"properties": {"extra": {"type": "boolean"}}},
            ],
            "$defs": {
                "Base": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                }
            },
        }
        assert iter_errors({"name": "Alice", "extra": True}, schema) == []

    def test_circular_ref_does_not_hang(self):
        schema = {
            "type": "object",
            "properties": {
                "child": {"$ref": "#"},
            },
        }
        # Should not hang — circular $ref is broken by resolve_refs
        errs = iter_errors({"child": {"child": {}}}, schema)
        assert isinstance(errs, list)


class TestSchemaValidateBooleanSchema:
    """Boolean schema (true/false) validation."""

    def test_true_accepts_anything(self):
        assert iter_errors("anything", True) == []
        assert iter_errors(42, True) == []
        assert iter_errors(None, True) == []
        assert iter_errors({"a": [1]}, True) == []

    def test_false_rejects_everything(self):
        for value in ("anything", 42, None, {}, [], True, False):
            errs = iter_errors(value, False)
            assert len(errs) == 1, f"Expected 1 error for {value!r}"
            assert errs[0].validator == "false_schema"


class TestSchemaValidateErrorModel:
    """Error detail and exception model."""

    def test_error_path_nested_object(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            },
        }
        errs = iter_errors({"user": {"name": 42}}, schema)
        assert len(errs) == 1
        assert errs[0].path == "user.name"

    def test_error_path_array_item(self):
        schema = {"type": "array", "items": {"type": "integer"}}
        errs = iter_errors([1, "two", 3], schema)
        assert len(errs) == 1
        assert errs[0].path == "[1]"

    def test_error_path_deeply_nested(self):
        schema = {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"value": {"type": "number"}},
                    },
                }
            },
        }
        errs = iter_errors({"data": [{"value": 1}, {"value": "bad"}]}, schema)
        assert len(errs) == 1
        assert errs[0].path == "data[1].value"

    def test_error_schema_path_present(self):
        schema = {
            "type": "object",
            "properties": {"age": {"type": "integer", "minimum": 0}},
        }
        errs = iter_errors({"age": -1}, schema)
        assert len(errs) == 1
        assert "minimum" in errs[0].schema_path

    def test_multiple_errors_collected(self):
        schema = {
            "type": "object",
            "properties": {"a": {"type": "string"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        }
        errs = iter_errors({}, schema)
        assert len(errs) == 2  # two required fields missing

    def test_schema_validation_error_message_format(self):
        schema = {"type": "string"}
        try:
            schema_validate(42, schema)
            assert False, "Should have raised"
        except SchemaValidationError as exc:
            assert "1 schema validation error(s)" in str(exc)
            assert len(exc.errors) == 1

    def test_schema_validation_error_truncates_many(self):
        schema = {"type": "object", "required": list("abcdefgh")}
        try:
            schema_validate({}, schema)
        except SchemaValidationError as exc:
            assert len(exc.errors) == 8
            assert "... and 3 more" in str(exc)

    def test_error_detail_is_frozen(self):
        errs = iter_errors(42, {"type": "string"})
        with pytest.raises(AttributeError):
            errs[0].path = "mutated"

    def test_schema_validate_passes_silently(self):
        schema_validate("hello", {"type": "string"})  # no exception


class TestSchemaValidateEdgeCases:
    """Edge cases and special scenarios."""

    def test_empty_schema(self):
        assert iter_errors("anything", {}) == []
        assert iter_errors(None, {}) == []

    def test_schema_with_no_type(self):
        schema = {"minLength": 3}
        assert iter_errors("abcd", schema) == []
        errs = iter_errors("ab", schema)
        assert len(errs) == 1
        # Non-string values should pass (minLength doesn't apply)
        assert iter_errors(42, schema) == []

    def test_none_instance_against_object_schema(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        errs = iter_errors(None, schema)
        assert len(errs) == 1
        assert errs[0].validator == "type"

    def test_deeply_nested_objects(self):
        schema: dict = {"type": "object", "properties": {"child": {}}}
        # Build a 10-level nested schema
        inner = schema
        for _ in range(10):
            inner["properties"]["child"] = {
                "type": "object",
                "properties": {"child": {}},
            }
            inner = inner["properties"]["child"]
        inner["properties"]["child"] = {"type": "string"}

        # Build matching data
        data: dict = {"child": {}}
        inner_data = data
        for _ in range(10):
            inner_data["child"] = {"child": {}}
            inner_data = inner_data["child"]
        inner_data["child"] = "leaf"

        assert iter_errors(data, schema) == []

    def test_nullable_in_anyof_pattern(self):
        schema = {"anyOf": [{"type": "string"}, {"type": "null"}]}
        assert iter_errors(None, schema) == []
        assert iter_errors("hello", schema) == []
        errs = iter_errors(42, schema)
        assert len(errs) == 1

    def test_additional_properties_with_no_properties(self):
        schema = {"type": "object", "additionalProperties": {"type": "string"}}
        assert iter_errors({"any": "value"}, schema) == []
        errs = iter_errors({"any": 42}, schema)
        assert len(errs) == 1

    def test_empty_required_array(self):
        schema = {"type": "object", "required": []}
        assert iter_errors({}, schema) == []

    def test_empty_allof(self):
        schema = {"allOf": []}
        assert iter_errors("anything", schema) == []

    def test_items_with_empty_array(self):
        schema = {"type": "array", "items": {"type": "integer"}}
        assert iter_errors([], schema) == []

    def test_combined_constraints(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 50},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "uniqueItems": True,
                },
            },
            "required": ["name", "age"],
        }
        valid = {"name": "Alice", "age": 30, "tags": ["admin"]}
        assert iter_errors(valid, schema) == []

        invalid = {"name": "", "age": -1, "tags": ["a", "a"]}
        errs = iter_errors(invalid, schema)
        assert len(errs) == 3  # minLength, minimum, uniqueItems


class TestSchemaValidateTypeAwareEquality:
    """Type-aware equality for enum, const, and uniqueItems."""

    def test_enum_bool_not_equal_to_int(self):
        errs = iter_errors(True, {"enum": [1, 2, 3]})
        assert len(errs) == 1

    def test_enum_int_not_equal_to_bool(self):
        errs = iter_errors(1, {"enum": [True, False]})
        assert len(errs) == 1

    def test_enum_bool_matches_bool(self):
        assert iter_errors(True, {"enum": [True, False]}) == []

    def test_const_bool_not_equal_to_int(self):
        errs = iter_errors(1, {"const": True})
        assert len(errs) == 1

    def test_const_int_not_equal_to_bool(self):
        errs = iter_errors(True, {"const": 1})
        assert len(errs) == 1

    def test_const_bool_matches_bool(self):
        assert iter_errors(True, {"const": True}) == []

    def test_unique_items_bool_vs_int(self):
        schema = {"type": "array", "uniqueItems": True}
        # Top-level bool vs int: distinct via (type, value) tuple
        assert iter_errors([True, 1], schema) == []


class TestSchemaValidateBooleanSubSchemas:
    """Boolean sub-schemas in properties and patternProperties."""

    def test_property_false_rejects(self):
        schema = {"type": "object", "properties": {"x": False}}
        errs = iter_errors({"x": 1}, schema)
        assert len(errs) == 1
        assert errs[0].validator == "false_schema"

    def test_property_true_accepts(self):
        schema = {"type": "object", "properties": {"x": True}}
        assert iter_errors({"x": "anything"}, schema) == []

    def test_pattern_property_false_rejects(self):
        schema = {"type": "object", "patternProperties": {"^x-": False}}
        errs = iter_errors({"x-custom": "val"}, schema)
        assert len(errs) == 1
        assert errs[0].validator == "false_schema"


class TestSchemaValidateResolved:
    """The resolved=True flag skips redundant $ref resolution."""

    def test_resolved_matches_default(self):
        schema = {
            "type": "object",
            "properties": {"user": {"$ref": "#/$defs/User"}},
            "$defs": {
                "User": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                }
            },
        }
        resolved = resolve_refs(schema)
        instance = {"user": {"name": "Alice"}}
        assert iter_errors(instance, schema) == []
        assert iter_errors(instance, resolved, resolved=True) == []

    def test_resolved_catches_errors(self):
        schema = {
            "type": "object",
            "properties": {"user": {"$ref": "#/$defs/User"}},
            "$defs": {
                "User": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                }
            },
        }
        resolved = resolve_refs(schema)
        errs_default = iter_errors({"user": {}}, schema)
        errs_resolved = iter_errors({"user": {}}, resolved, resolved=True)
        assert len(errs_default) == len(errs_resolved) == 1
        assert errs_default[0].validator == errs_resolved[0].validator

    def test_schema_validate_resolved(self):
        resolved = resolve_refs({"type": "string"})
        schema_validate("hello", resolved, resolved=True)
        try:
            schema_validate(42, resolved, resolved=True)
            assert False, "Should have raised"
        except SchemaValidationError:
            pass

    def test_resolve_once_validate_many(self):
        schema = resolve_refs(
            {
                "type": "object",
                "properties": {"n": {"type": "integer", "minimum": 0}},
                "required": ["n"],
            }
        )
        items = [{"n": i} for i in range(10)]
        for item in items:
            assert iter_errors(item, schema, resolved=True) == []
        errs = iter_errors({"n": -1}, schema, resolved=True)
        assert len(errs) == 1
        assert errs[0].validator == "minimum"


class TestSchemaValidateVsReference:
    """Compare our validation against the jsonschema PyPI package."""

    @pytest.fixture(autouse=True)
    def _import_reference(self):
        # Import real jsonschema PyPI by temporarily filtering our dir from path
        saved_path = sys.path[:]
        sys.path = [
            p for p in sys.path if os.path.abspath(p) != os.path.abspath(_this_dir)
        ]
        # Evict our local module
        sys.modules.pop("jsonschema", None)
        for k in list(sys.modules):
            if k.startswith("jsonschema."):
                sys.modules.pop(k, None)
        try:
            import jsonschema as ref

            if not hasattr(ref, "validate"):
                raise ImportError("Not the real jsonschema")
            self.ref_validate = ref.validate
            self.ref_ValidationError = ref.ValidationError
        except ImportError:
            pytest.skip("jsonschema PyPI not installed")
        finally:
            sys.path = saved_path
            # Clean up real jsonschema from modules
            sys.modules.pop("jsonschema", None)
            for k in list(sys.modules):
                if k.startswith("jsonschema."):
                    sys.modules.pop(k, None)

    def _both_agree(self, instance, schema):
        """Assert both implementations agree on validity."""
        ours = iter_errors(instance, schema)
        try:
            self.ref_validate(instance, schema)
            ref_valid = True
        except self.ref_ValidationError:
            ref_valid = False

        our_valid = len(ours) == 0
        ours_s = "valid" if our_valid else "invalid"
        ref_s = "valid" if ref_valid else "invalid"
        assert our_valid == ref_valid, (
            f"Disagreement on {instance!r}: ours={ours_s}, ref={ref_s}"
        )

    def test_type_string(self):
        self._both_agree("hello", {"type": "string"})
        self._both_agree(42, {"type": "string"})

    def test_type_integer(self):
        self._both_agree(42, {"type": "integer"})
        self._both_agree(3.14, {"type": "integer"})
        self._both_agree(True, {"type": "integer"})

    def test_type_number(self):
        self._both_agree(3.14, {"type": "number"})
        self._both_agree(42, {"type": "number"})
        self._both_agree(True, {"type": "number"})

    def test_required(self):
        schema = {"type": "object", "required": ["a"]}
        self._both_agree({"a": 1}, schema)
        self._both_agree({}, schema)

    def test_enum(self):
        schema = {"enum": [1, 2, 3]}
        self._both_agree(1, schema)
        self._both_agree(4, schema)

    def test_minimum_maximum(self):
        schema = {"type": "integer", "minimum": 0, "maximum": 10}
        self._both_agree(5, schema)
        self._both_agree(-1, schema)
        self._both_agree(11, schema)

    def test_string_constraints(self):
        schema = {"type": "string", "minLength": 2, "maxLength": 5}
        self._both_agree("abc", schema)
        self._both_agree("a", schema)
        self._both_agree("toolong", schema)

    def test_additional_properties_false(self):
        schema = {
            "type": "object",
            "properties": {"a": {}},
            "additionalProperties": False,
        }
        self._both_agree({"a": 1}, schema)
        self._both_agree({"a": 1, "b": 2}, schema)

    def test_anyof(self):
        schema = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
        self._both_agree("hello", schema)
        self._both_agree(42, schema)
        self._both_agree(3.14, schema)

    def test_nested_object(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                }
            },
        }
        self._both_agree({"user": {"name": "Alice"}}, schema)
        self._both_agree({"user": {}}, schema)

    def test_array_items(self):
        schema = {"type": "array", "items": {"type": "integer"}, "minItems": 1}
        self._both_agree([1, 2, 3], schema)
        self._both_agree([], schema)
        self._both_agree([1, "two"], schema)

    def test_oneof(self):
        schema = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
        self._both_agree("hello", schema)
        self._both_agree(3.14, schema)

    def test_not(self):
        schema = {"not": {"type": "string"}}
        self._both_agree(42, schema)
        self._both_agree("hello", schema)

    def test_pattern(self):
        schema = {"type": "string", "pattern": "^[a-z]+$"}
        self._both_agree("abc", schema)
        self._both_agree("ABC", schema)

    def test_openapi_style_schema(self):
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string", "minLength": 1},
                "email": {"type": "string", "pattern": "^.+@.+$"},
                "role": {"enum": ["admin", "user", "guest"]},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "uniqueItems": True,
                },
            },
            "required": ["id", "name", "email", "role"],
        }
        valid = {
            "id": 1,
            "name": "Alice",
            "email": "a@b.com",
            "role": "admin",
            "tags": ["dev"],
        }
        self._both_agree(valid, schema)
        invalid = {"id": "one", "name": "", "email": "bad", "role": "superuser"}
        self._both_agree(invalid, schema)
