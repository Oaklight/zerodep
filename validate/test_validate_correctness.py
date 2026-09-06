"""Correctness tests: zerodep validate module."""

import dataclasses
import os
import sys
from typing import Annotated, Any, Literal, Optional, Union

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from validate import (
    Doc,
    ErrorDetail,
    FieldValidator,
    Ge,
    Gt,
    Le,
    Lt,
    Match,
    MaxLen,
    MinLen,
    Predicate,
    ValidationError,
    create_struct,
    json_schema,
    model_validator,
    validate,
)

if sys.version_info >= (3, 11):
    from typing import NotRequired, Required, TypedDict
else:
    from typing_extensions import NotRequired, Required, TypedDict


# ── Test TypedDicts ──


class SimpleUser(TypedDict):
    name: str
    age: int


class Address(TypedDict):
    street: str
    city: str
    zip_code: str


class UserWithAddress(TypedDict):
    name: str
    address: Address


class PartialUser(TypedDict, total=False):
    name: str
    age: int
    email: str


class MixedUser(TypedDict):
    name: str
    age: Required[int]
    email: NotRequired[str]


class ConstrainedItem(TypedDict):
    name: Annotated[str, MinLen(1), MaxLen(100)]
    price: Annotated[float, Gt(0)]
    quantity: Annotated[int, Ge(0), Le(1000)]


class TaggedItem(TypedDict):
    name: str
    tags: Annotated[list[str], MaxLen(5)]


class PatternField(TypedDict):
    email: Annotated[str, Match(r"[^@]+@[^@]+\.[^@]+")]


class TypeA(TypedDict):
    kind: Literal["a"]
    value_a: str


class TypeB(TypedDict):
    kind: Literal["b"]
    value_b: int


class Container(TypedDict):
    items: list[SimpleUser]


# ── Test Dataclasses ──


@dataclasses.dataclass
class Point:
    x: float
    y: float


@dataclasses.dataclass
class PointWithDefault:
    x: float
    y: float
    z: float = 0.0


# ── Simple Types ──


class TestSimpleTypes:
    def test_str_valid(self):
        assert validate("hello", str) == "hello"

    def test_str_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            validate(123, str)
        assert len(exc_info.value.errors) == 1
        assert exc_info.value.errors[0].expected == "str"

    def test_int_valid(self):
        assert validate(42, int) == 42

    def test_int_invalid(self):
        with pytest.raises(ValidationError):
            validate("not_int", int)

    def test_float_valid(self):
        assert validate(3.14, float) == 3.14

    def test_float_accepts_int(self):
        assert validate(42, float) == 42

    def test_bool_valid(self):
        assert validate(True, bool) is True
        assert validate(False, bool) is False

    def test_bool_rejects_int(self):
        with pytest.raises(ValidationError):
            validate(1, bool)

    def test_int_rejects_bool(self):
        with pytest.raises(ValidationError):
            validate(True, int)

    def test_float_rejects_bool(self):
        with pytest.raises(ValidationError):
            validate(True, float)

    def test_bytes_valid(self):
        assert validate(b"data", bytes) == b"data"

    def test_none_valid(self):
        assert validate(None, None) is None

    def test_none_invalid(self):
        with pytest.raises(ValidationError):
            validate(42, None)

    def test_any_accepts_anything(self):
        assert validate("anything", Any) == "anything"
        assert validate(None, Any) is None
        assert validate([1, 2], Any) == [1, 2]


# ── Container Types ──


class TestContainerTypes:
    def test_list_of_str(self):
        assert validate(["a", "b"], list[str]) == ["a", "b"]

    def test_list_of_str_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            validate(["a", 1], list[str])
        assert any("[1]" in e.path for e in exc_info.value.errors)

    def test_list_not_a_list(self):
        with pytest.raises(ValidationError):
            validate("not_list", list[str])

    def test_dict_str_int(self):
        assert validate({"a": 1, "b": 2}, dict[str, int]) == {"a": 1, "b": 2}

    def test_dict_invalid_value(self):
        with pytest.raises(ValidationError):
            validate({"a": "not_int"}, dict[str, int])

    def test_tuple_positional(self):
        assert validate((1, "a"), tuple[int, str]) == (1, "a")

    def test_tuple_positional_wrong_length(self):
        with pytest.raises(ValidationError, match="elements"):
            validate((1, "a", 3.0), tuple[int, str])

    def test_tuple_homogeneous(self):
        assert validate((1, 2, 3), tuple[int, ...]) == (1, 2, 3)

    def test_set_of_int(self):
        validate({1, 2, 3}, set[int])

    def test_set_accepts_list(self):
        validate([1, 2, 3], set[int])


# ── TypedDict ──


class TestTypedDict:
    def test_simple_valid(self):
        data = {"name": "Alice", "age": 30}
        assert validate(data, SimpleUser) == data

    def test_missing_required_field(self):
        with pytest.raises(ValidationError) as exc_info:
            validate({"name": "Alice"}, SimpleUser)
        errors = exc_info.value.errors
        assert len(errors) == 1
        assert errors[0].actual == "MISSING"
        assert "age" in errors[0].path

    def test_wrong_field_type(self):
        with pytest.raises(ValidationError) as exc_info:
            validate({"name": "Alice", "age": "thirty"}, SimpleUser)
        assert any("age" in e.path for e in exc_info.value.errors)

    def test_nested_typeddict(self):
        data = {
            "name": "Alice",
            "address": {"street": "123 Main St", "city": "NYC", "zip_code": "10001"},
        }
        assert validate(data, UserWithAddress) == data

    def test_nested_typeddict_error(self):
        data = {
            "name": "Alice",
            "address": {"street": 123, "city": "NYC", "zip_code": "10001"},
        }
        with pytest.raises(ValidationError) as exc_info:
            validate(data, UserWithAddress)
        errors = exc_info.value.errors
        assert any("address.street" in e.path for e in errors)

    def test_not_a_dict(self):
        with pytest.raises(ValidationError):
            validate("not_a_dict", SimpleUser)

    def test_total_false(self):
        # All fields optional
        assert validate({}, PartialUser) == {}
        assert validate({"name": "Alice"}, PartialUser) == {"name": "Alice"}

    def test_required_not_required(self):
        # name and age required, email optional
        assert validate({"name": "Alice", "age": 30}, MixedUser) == {
            "name": "Alice",
            "age": 30,
        }
        with pytest.raises(ValidationError):
            validate({"name": "Alice"}, MixedUser)

    def test_extra_fields_ignored(self):
        data = {"name": "Alice", "age": 30, "extra": "ignored"}
        assert validate(data, SimpleUser) == data

    def test_list_of_typeddict(self):
        data = {"items": [{"name": "A", "age": 1}, {"name": "B", "age": 2}]}
        assert validate(data, Container) == data

    def test_list_of_typeddict_error(self):
        data = {"items": [{"name": "A", "age": 1}, {"name": "B", "age": "x"}]}
        with pytest.raises(ValidationError) as exc_info:
            validate(data, Container)
        assert any("items[1].age" in e.path for e in exc_info.value.errors)


# ── Dataclass ──


class TestDataclass:
    def test_valid(self):
        data = {"x": 1.0, "y": 2.0}
        assert validate(data, Point) == data

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            validate({"x": 1.0}, Point)

    def test_with_default(self):
        # z has a default, so it's optional
        assert validate({"x": 1.0, "y": 2.0}, PointWithDefault) == {"x": 1.0, "y": 2.0}

    def test_instance_flat(self):
        p = Point(x=1.0, y=2.0)
        result = validate(p, Point)
        assert result == {"x": 1.0, "y": 2.0}

    def test_instance_invalid_field(self):
        p = Point(x="bad", y=2.0)  # type: ignore[arg-type]
        with pytest.raises(ValidationError) as exc_info:
            validate(p, Point)
        assert any("x" in e.path for e in exc_info.value.errors)

    def test_instance_nested(self):
        @dataclasses.dataclass
        class Inner:
            value: int

        @dataclasses.dataclass
        class Outer:
            name: str
            inner: Inner

        obj = Outer(name="test", inner=Inner(value=42))
        result = validate(obj, Outer)
        assert result["name"] == "test"
        # Conversion is shallow: nested DC instances stay as-is in the returned dict
        assert isinstance(result["inner"], Inner)
        assert result["inner"].value == 42

    def test_instance_nested_invalid(self):
        @dataclasses.dataclass
        class Inner:
            value: int

        @dataclasses.dataclass
        class Outer:
            name: str
            inner: Inner

        obj = Outer(name="test", inner=Inner(value="bad"))  # type: ignore[arg-type]
        with pytest.raises(ValidationError) as exc_info:
            validate(obj, Outer)
        assert any("inner.value" in e.path for e in exc_info.value.errors)

    def test_instance_against_typeddict(self):
        """DC instance validated against a mismatched TypedDict fails."""
        p = Point(x=1.0, y=2.0)
        with pytest.raises(ValidationError):
            validate(p, SimpleUser)  # Point has x,y but SimpleUser requires name,age

    def test_instance_cross_schema(self):
        """DC instance validated against a TypedDict with matching fields."""

        class PointTD(TypedDict):
            x: float
            y: float

        p = Point(x=1.0, y=2.0)
        result = validate(p, PointTD)
        assert result == {"x": 1.0, "y": 2.0}

    def test_instance_with_default_fields(self):
        p = PointWithDefault(x=1.0, y=2.0)
        result = validate(p, PointWithDefault)
        assert result == {"x": 1.0, "y": 2.0, "z": 0.0}

    def test_instance_in_list(self):
        points = [Point(x=1.0, y=2.0), Point(x=3.0, y=4.0)]
        result = validate(points, list[Point])
        assert len(result) == 2
        # validate doesn't replace list items; originals stay as DC instances
        assert isinstance(result[0], Point)
        assert result[0].x == 1.0

    def test_instance_slots(self):
        """dataclass(slots=True) instances work (no __dict__)."""

        @dataclasses.dataclass(slots=True)
        class SlottedPoint:
            x: float
            y: float

        p = SlottedPoint(x=1.0, y=2.0)
        result = validate(p, SlottedPoint)
        assert result == {"x": 1.0, "y": 2.0}

    def test_instance_no_mutation(self):
        """Modifying the returned dict must not alter the original instance."""
        p = Point(x=1.0, y=2.0)
        result = validate(p, Point)
        result["x"] = 999.0
        assert p.x == 1.0


# ── Annotated Constraints ──


class TestConstraints:
    def test_gt(self):
        validate({"name": "a", "price": 1.0, "quantity": 0}, ConstrainedItem)
        with pytest.raises(ValidationError):
            validate({"name": "a", "price": 0.0, "quantity": 0}, ConstrainedItem)
        with pytest.raises(ValidationError):
            validate({"name": "a", "price": -1.0, "quantity": 0}, ConstrainedItem)

    def test_ge_le(self):
        validate({"name": "a", "price": 1.0, "quantity": 0}, ConstrainedItem)
        validate({"name": "a", "price": 1.0, "quantity": 1000}, ConstrainedItem)
        with pytest.raises(ValidationError):
            validate({"name": "a", "price": 1.0, "quantity": -1}, ConstrainedItem)
        with pytest.raises(ValidationError):
            validate({"name": "a", "price": 1.0, "quantity": 1001}, ConstrainedItem)

    def test_lt(self):
        c = Lt(10)
        assert c.check(9)
        assert not c.check(10)

    def test_minlen_maxlen(self):
        validate({"name": "a", "price": 1.0, "quantity": 0}, ConstrainedItem)
        with pytest.raises(ValidationError):
            validate({"name": "", "price": 1.0, "quantity": 0}, ConstrainedItem)
        with pytest.raises(ValidationError):
            validate({"name": "x" * 101, "price": 1.0, "quantity": 0}, ConstrainedItem)

    def test_maxlen_on_list(self):
        validate({"name": "a", "tags": ["t1", "t2"]}, TaggedItem)
        with pytest.raises(ValidationError):
            validate({"name": "a", "tags": ["t"] * 6}, TaggedItem)

    def test_match(self):
        validate({"email": "test@example.com"}, PatternField)
        with pytest.raises(ValidationError):
            validate({"email": "not-an-email"}, PatternField)

    def test_predicate(self):
        EvenInt = Annotated[int, Predicate(lambda x: x % 2 == 0, "must be even")]
        validate(4, EvenInt)
        with pytest.raises(ValidationError, match="even"):
            validate(3, EvenInt)

    def test_multiple_constraints(self):
        BoundedStr = Annotated[str, MinLen(2), MaxLen(5)]
        validate("ab", BoundedStr)
        validate("abcde", BoundedStr)
        with pytest.raises(ValidationError):
            validate("a", BoundedStr)
        with pytest.raises(ValidationError):
            validate("abcdef", BoundedStr)

    def test_constraint_not_checked_on_type_error(self):
        """Constraints should not be checked if the base type fails."""
        PosInt = Annotated[int, Gt(0)]
        with pytest.raises(ValidationError) as exc_info:
            validate("not_int", PosInt)
        # Should have type error but not constraint error
        assert len(exc_info.value.errors) == 1
        assert exc_info.value.errors[0].expected == "int"


# ── Union / Optional ──


class TestUnion:
    def test_optional_none(self):
        assert validate(None, Optional[str]) is None

    def test_optional_value(self):
        assert validate("hello", Optional[str]) == "hello"

    def test_optional_wrong_type(self):
        with pytest.raises(ValidationError):
            validate(42, Optional[str])

    def test_union_str_int(self):
        assert validate("hello", Union[str, int]) == "hello"
        assert validate(42, Union[str, int]) == 42

    def test_union_no_match(self):
        with pytest.raises(ValidationError):
            validate([], Union[str, int])

    def test_pep604_optional(self):
        """PEP 604 ``X | None`` works like ``Optional[X]``."""
        assert validate("hello", str | None) == "hello"
        assert validate(None, str | None) is None
        with pytest.raises(ValidationError):
            validate(42, str | None)

    def test_pep604_union(self):
        """PEP 604 ``X | Y`` works like ``Union[X, Y]``."""
        assert validate("hello", str | int) == "hello"
        assert validate(42, str | int) == 42
        with pytest.raises(ValidationError):
            validate([], str | int)

    def test_discriminated_union(self):
        DiscUnion = Union[TypeA, TypeB]
        data_a = {"kind": "a", "value_a": "hello"}
        data_b = {"kind": "b", "value_b": 42}
        assert validate(data_a, DiscUnion) == data_a
        assert validate(data_b, DiscUnion) == data_b

    def test_discriminated_union_invalid(self):
        DiscUnion = Union[TypeA, TypeB]
        data = {"kind": "a", "value_a": 123}  # value_a should be str
        with pytest.raises(ValidationError):
            validate(data, DiscUnion)

    def test_discriminated_union_unknown_discriminator_value(self):
        """Unknown discriminator value should fall back to linear probe and fail."""
        DiscUnion = Union[TypeA, TypeB]
        data = {"kind": "c", "value_a": "hello"}
        with pytest.raises(ValidationError):
            validate(data, DiscUnion)

    def test_discriminated_union_missing_discriminator_field(self):
        """Missing discriminator field should fall back to linear probe."""
        DiscUnion = Union[TypeA, TypeB]
        data = {"value_a": "hello"}  # no "kind" field
        with pytest.raises(ValidationError):
            validate(data, DiscUnion)

    def test_discriminated_union_unhashable_discriminator_value(self):
        """Unhashable discriminator value should not crash."""
        DiscUnion = Union[TypeA, TypeB]
        data = {"kind": ["not", "hashable"], "value_a": "hello"}
        with pytest.raises(ValidationError):
            validate(data, DiscUnion)

    def test_discriminated_union_many_variants(self):
        """10-variant union with Literal discriminator."""

        class V1(TypedDict):
            type: Literal["text"]
            text: str

        class V2(TypedDict):
            type: Literal["image"]
            url: str

        class V3(TypedDict):
            type: Literal["file"]
            path: str

        class V4(TypedDict):
            type: Literal["tool_call"]
            name: str

        class V5(TypedDict):
            type: Literal["tool_result"]
            output: str

        class V6(TypedDict):
            type: Literal["reasoning"]
            content: str

        class V7(TypedDict):
            type: Literal["refusal"]
            reason: str

        class V8(TypedDict):
            type: Literal["citation"]
            source: str

        class V9(TypedDict):
            type: Literal["audio"]
            data: str

        class V10(TypedDict):
            type: Literal["meta"]
            info: str

        BigUnion = Union[V1, V2, V3, V4, V5, V6, V7, V8, V9, V10]

        # Every variant should match correctly
        assert validate({"type": "text", "text": "hi"}, BigUnion)["type"] == "text"
        assert validate({"type": "meta", "info": "x"}, BigUnion)["type"] == "meta"
        assert (
            validate({"type": "tool_call", "name": "f"}, BigUnion)["type"]
            == "tool_call"
        )

        # Wrong inner fields should fail
        with pytest.raises(ValidationError):
            validate({"type": "text", "text": 123}, BigUnion)

        # Unknown type should fail
        with pytest.raises(ValidationError):
            validate({"type": "unknown", "data": "x"}, BigUnion)

    def test_discriminated_union_list_large_payload(self):
        """Validate a large list of discriminated union items (stress test)."""

        class TextPart(TypedDict):
            type: Literal["text"]
            text: str

        class ToolCallPart(TypedDict):
            type: Literal["tool_call"]
            name: str
            args: str

        class ToolResultPart(TypedDict):
            type: Literal["tool_result"]
            output: str

        ContentPart = Union[TextPart, ToolCallPart, ToolResultPart]

        # Build a large payload: 200 items cycling through types
        templates = [
            {"type": "text", "text": "hello"},
            {"type": "tool_call", "name": "read", "args": "{}"},
            {"type": "tool_result", "output": "data"},
        ]
        payload = [templates[i % 3] for i in range(200)]

        result = validate(payload, list[ContentPart])
        assert len(result) == 200
        assert result[0]["type"] == "text"
        assert result[1]["type"] == "tool_call"
        assert result[2]["type"] == "tool_result"

    def test_discriminated_union_nested_messages(self):
        """Nested structure: list of messages, each with list of union content parts."""

        class TextPart(TypedDict):
            type: Literal["text"]
            text: str

        class ImagePart(TypedDict):
            type: Literal["image"]
            url: str

        class ToolCallPart(TypedDict):
            type: Literal["tool_call"]
            name: str

        ContentPart = Union[TextPart, ImagePart, ToolCallPart]

        class Message(TypedDict):
            role: Literal["user", "assistant"]
            content: list[ContentPart]

        # 50 messages, each with 5 content parts = 250 union validations
        messages = [
            {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": [
                    {"type": "text", "text": f"msg {i}"},
                    {"type": "tool_call", "name": "fn"},
                    {"type": "text", "text": "response"},
                    {"type": "image", "url": "http://img"},
                    {"type": "text", "text": "end"},
                ],
            }
            for i in range(50)
        ]

        result = validate(messages, list[Message])
        assert len(result) == 50
        assert len(result[0]["content"]) == 5

    def test_discriminated_union_multi_literal(self):
        """Variant with multiple Literal values."""

        class Draft(TypedDict):
            status: Literal["draft", "pending"]
            title: str

        class Published(TypedDict):
            status: Literal["published"]
            title: str
            url: str

        Article = Union[Draft, Published]

        assert (
            validate({"status": "draft", "title": "WIP"}, Article)["status"] == "draft"
        )
        assert (
            validate({"status": "pending", "title": "Rev"}, Article)["status"]
            == "pending"
        )
        assert (
            validate({"status": "published", "title": "Done", "url": "/a"}, Article)[
                "status"
            ]
            == "published"
        )


# ── Literal ──


class TestLiteral:
    def test_valid(self):
        assert validate("a", Literal["a", "b", "c"]) == "a"

    def test_invalid(self):
        with pytest.raises(ValidationError):
            validate("x", Literal["a", "b"])

    def test_int_literal(self):
        assert validate(1, Literal[1, 2, 3]) == 1


# ── Coercion ──


class TestCoercion:
    def test_str_to_int(self):
        assert validate("42", int, coerce=True) == 42

    def test_str_to_float(self):
        assert validate("3.14", float, coerce=True) == 3.14

    def test_int_to_float(self):
        assert validate(42, float, coerce=True) == 42.0

    def test_list_to_tuple(self):
        result = validate([1, 2], tuple[int, ...], coerce=True)
        assert isinstance(result, (tuple, list))

    def test_no_coerce_by_default(self):
        with pytest.raises(ValidationError):
            validate("42", int)

    def test_invalid_coerce(self):
        with pytest.raises(ValidationError):
            validate("not_a_number", int, coerce=True)


# ── Error Collection ──


class TestErrorCollection:
    def test_multiple_errors(self):
        data = {"name": 123, "age": "thirty"}
        with pytest.raises(ValidationError) as exc_info:
            validate(data, SimpleUser)
        assert len(exc_info.value.errors) == 2

    def test_error_paths(self):
        data = {
            "name": "Alice",
            "address": {"street": 123, "city": 456, "zip_code": "ok"},
        }
        with pytest.raises(ValidationError) as exc_info:
            validate(data, UserWithAddress)
        paths = {e.path for e in exc_info.value.errors}
        assert "address.street" in paths
        assert "address.city" in paths

    def test_list_index_in_path(self):
        data = {"items": [{"name": "A", "age": 1}, {"name": 123, "age": "x"}]}
        with pytest.raises(ValidationError) as exc_info:
            validate(data, Container)
        paths = {e.path for e in exc_info.value.errors}
        assert "items[1].name" in paths
        assert "items[1].age" in paths

    def test_error_detail_fields(self):
        with pytest.raises(ValidationError) as exc_info:
            validate(42, str)
        err = exc_info.value.errors[0]
        assert isinstance(err, ErrorDetail)
        assert err.expected == "str"
        assert err.actual == "int"
        assert err.message

    def test_error_str_truncation(self):
        """ValidationError message truncates after 5 errors."""

        class ManyFields(TypedDict):
            a: str
            b: str
            c: str
            d: str
            e: str
            f: str

        with pytest.raises(ValidationError) as exc_info:
            validate({"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6}, ManyFields)
        assert "more" in str(exc_info.value)


# ── JSON Schema ──


class TestJsonSchema:
    def test_simple_typeddict(self):
        schema = json_schema(SimpleUser)
        assert schema["type"] == "object"
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]
        assert schema["properties"]["name"] == {"type": "string"}
        assert schema["properties"]["age"] == {"type": "integer"}
        assert set(schema["required"]) == {"name", "age"}

    def test_title(self):
        schema = json_schema(SimpleUser)
        assert schema["title"] == "SimpleUser"
        schema = json_schema(SimpleUser, title="Custom")
        assert schema["title"] == "Custom"

    def test_nested(self):
        schema = json_schema(UserWithAddress)
        addr_schema = schema["properties"]["address"]
        assert addr_schema["type"] == "object"
        assert "street" in addr_schema["properties"]

    def test_optional_fields(self):
        schema = json_schema(MixedUser)
        assert "name" in schema["required"]
        assert "age" in schema["required"]
        assert "email" not in schema.get("required", [])

    def test_annotated_constraints(self):
        schema = json_schema(ConstrainedItem)
        price = schema["properties"]["price"]
        assert price["exclusiveMinimum"] == 0
        qty = schema["properties"]["quantity"]
        assert qty["minimum"] == 0
        assert qty["maximum"] == 1000
        name = schema["properties"]["name"]
        assert name["minLength"] == 1
        assert name["maxLength"] == 100

    def test_list_schema(self):
        schema = json_schema(Container)
        items_schema = schema["properties"]["items"]
        assert items_schema["type"] == "array"
        assert items_schema["items"]["type"] == "object"

    def test_maxlen_on_array(self):
        schema = json_schema(TaggedItem)
        tags = schema["properties"]["tags"]
        assert tags["type"] == "array"
        assert tags["maxItems"] == 5

    def test_literal_schema(self):
        class HasLiteral(TypedDict):
            kind: Literal["a", "b"]

        schema = json_schema(HasLiteral)
        assert schema["properties"]["kind"] == {"enum": ["a", "b"]}

    def test_union_schema(self):
        class HasUnion(TypedDict):
            value: Union[str, int]

        schema = json_schema(HasUnion)
        assert "oneOf" in schema["properties"]["value"]

    def test_optional_schema(self):
        class HasOptional(TypedDict):
            value: Optional[str]

        schema = json_schema(HasOptional)
        val = schema["properties"]["value"]
        assert val["type"] == ["string", "null"]

    def test_pep604_optional_schema(self):
        """PEP 604 ``X | None`` produces same schema as ``Optional[X]``."""
        schema = _type_to_schema_import(str | None)
        assert schema == {"type": ["string", "null"]}

    def test_pep604_union_schema(self):
        """PEP 604 ``X | Y`` produces same schema as ``Union[X, Y]``."""
        schema = _type_to_schema_import(str | int)
        assert "oneOf" in schema

    def test_pep604_double_optional_no_duplicate_null(self):
        """``Optional[X | None]`` does not produce double null in schema."""
        schema = _type_to_schema_import(Optional[str | None])
        assert schema == {"type": ["string", "null"]}

    def test_dict_schema(self):
        schema = _type_to_schema_import(dict[str, int])
        assert schema["type"] == "object"
        assert schema["additionalProperties"] == {"type": "integer"}

    def test_tuple_positional_schema(self):
        schema = _type_to_schema_import(tuple[int, str])
        assert schema["type"] == "array"
        assert len(schema["prefixItems"]) == 2
        assert schema["minItems"] == 2

    def test_tuple_homogeneous_schema(self):
        schema = _type_to_schema_import(tuple[int, ...])
        assert schema["type"] == "array"
        assert schema["items"] == {"type": "integer"}

    def test_set_schema(self):
        schema = _type_to_schema_import(set[int])
        assert schema["type"] == "array"
        assert schema["uniqueItems"] is True

    def test_dataclass_schema(self):
        schema = json_schema(Point)
        assert schema["type"] == "object"
        assert set(schema["required"]) == {"x", "y"}

    def test_dataclass_optional_field(self):
        schema = json_schema(PointWithDefault)
        assert "z" not in schema.get("required", [])

    def test_none_schema(self):
        schema = _type_to_schema_import(None)
        assert schema == {"type": "null"}

    def test_any_schema(self):
        schema = _type_to_schema_import(Any)
        assert schema == {}

    def test_match_pattern(self):
        schema = json_schema(PatternField)
        assert schema["properties"]["email"]["pattern"] == r"[^@]+@[^@]+\.[^@]+"


def _type_to_schema_import(tp: Any) -> dict[str, Any]:
    """Helper to access the internal _type_to_schema for direct type tests."""
    from validate import _type_to_schema

    return _type_to_schema(tp)


# ── Doc ──


class TestDoc:
    def test_schema_description(self):
        """Doc adds description to JSON Schema."""
        schema = json_schema(Annotated[str, Doc("A name")])
        assert schema == {"type": "string", "description": "A name"}

    def test_with_constraints(self):
        """Doc and constraints can be combined."""
        tp = Annotated[int, Doc("User age"), Ge(0)]
        schema = json_schema(tp)
        assert schema["type"] == "integer"
        assert schema["description"] == "User age"
        assert schema["minimum"] == 0

    def test_no_validation_effect(self):
        """Doc does not affect validation."""
        tp = Annotated[str, Doc("just a label")]
        assert validate("hello", tp) == "hello"
        with pytest.raises(ValidationError):
            validate(123, tp)

    def test_in_typeddict_schema(self):
        """Doc descriptions appear in struct property schemas."""

        class Params(TypedDict):
            name: Annotated[str, Doc("The user's name")]
            age: Annotated[int, Doc("Years old")]

        schema = json_schema(Params)
        assert schema["properties"]["name"]["description"] == "The user's name"
        assert schema["properties"]["age"]["description"] == "Years old"

    def test_str(self):
        assert str(Doc("hello")) == "hello"


# ── create_struct ──


class TestCreateStruct:
    def test_required_fields(self):
        """Fields with Ellipsis default are required."""
        T = create_struct("T", {"x": (int, ...), "y": (str, ...)})
        assert validate({"x": 1, "y": "a"}, T) == {"x": 1, "y": "a"}
        with pytest.raises(ValidationError):
            validate({"x": 1}, T)

    def test_optional_with_default(self):
        """Fields with non-Ellipsis default are optional."""
        T = create_struct("T", {"x": (int, ...), "y": (str, "hello")})
        assert validate({"x": 1}, T) == {"x": 1}
        assert validate({"x": 1, "y": "world"}, T) == {"x": 1, "y": "world"}

    def test_is_typeddict(self):
        """Returned type behaves as a TypedDict."""
        T = create_struct("T", {"x": (int, ...)})
        assert hasattr(T, "__required_keys__")
        assert hasattr(T, "__optional_keys__")

    def test_field_defaults_stored(self):
        """Default values are stored in __field_defaults__."""
        T = create_struct("T", {"x": (int, ...), "y": (str, "hi"), "z": (int, 0)})
        assert T.__field_defaults__ == {"y": "hi", "z": 0}

    def test_all_required_empty_defaults(self):
        """All-required struct has empty __field_defaults__."""
        T = create_struct("T", {"x": (int, ...), "y": (str, ...)})
        assert T.__field_defaults__ == {}

    def test_with_doc(self):
        """Doc annotations work inside create_struct fields."""
        T = create_struct(
            "T",
            {
                "name": (Annotated[str, Doc("The name")], ...),
            },
        )
        schema = json_schema(T)
        assert schema["properties"]["name"]["description"] == "The name"

    def test_with_constraints(self):
        """Constraint annotations work inside create_struct fields."""
        T = create_struct("T", {"age": (Annotated[int, Ge(0)], ...)})
        validate({"age": 5}, T)
        with pytest.raises(ValidationError):
            validate({"age": -1}, T)
        schema = json_schema(T)
        assert schema["properties"]["age"]["minimum"] == 0

    def test_schema_includes_defaults(self):
        """json_schema emits default values for optional fields."""
        T = create_struct(
            "T",
            {
                "x": (int, ...),
                "y": (str, "hello"),
                "z": (int, 42),
            },
        )
        schema = json_schema(T)
        assert "default" not in schema["properties"]["x"]
        assert schema["properties"]["y"]["default"] == "hello"
        assert schema["properties"]["z"]["default"] == 42

    def test_nested_struct(self):
        """create_struct types can be nested."""
        Inner = create_struct("Inner", {"v": (int, ...)})
        Outer = create_struct("Outer", {"inner": (Inner, ...), "tag": (str, "x")})
        data = {"inner": {"v": 1}}
        assert validate(data, Outer) == data
        schema = json_schema(Outer)
        assert schema["properties"]["inner"]["type"] == "object"
        assert schema["properties"]["tag"]["default"] == "x"

    def test_schema_title(self):
        """create_struct type name becomes schema title."""
        T = create_struct("MyParams", {"x": (int, ...)})
        schema = json_schema(T)
        assert schema["title"] == "MyParams"

    def test_none_default(self):
        """None as default value is emitted in schema."""
        T = create_struct("T", {"tag": (str | None, None)})
        schema = json_schema(T)
        assert schema["properties"]["tag"]["default"] is None

    def test_dataclass_defaults_in_schema(self):
        """Dataclass static defaults appear in json_schema output."""
        schema = json_schema(PointWithDefault)
        assert schema["properties"]["z"]["default"] == 0.0
        assert "default" not in schema["properties"]["x"]
        assert "default" not in schema["properties"]["y"]

    def test_doc_and_default_combined(self):
        """Doc description and default coexist in schema."""
        T = create_struct(
            "T",
            {
                "limit": (Annotated[int, Doc("Max results")], 10),
            },
        )
        schema = json_schema(T)
        prop = schema["properties"]["limit"]
        assert prop["description"] == "Max results"
        assert prop["default"] == 10


# ── FieldValidator ──


class TestFieldValidator:
    def test_passthrough(self):
        """FieldValidator that returns value unchanged."""
        Identity = Annotated[str, FieldValidator(lambda v: v, "identity")]
        assert validate("hello", Identity) == "hello"

    def test_transform(self):
        """FieldValidator transforms the value."""

        def strip_lower(v: str) -> str:
            return v.strip().lower()

        Cleaned = Annotated[str, FieldValidator(strip_lower, "strip_lower")]
        assert validate("  HELLO  ", Cleaned) == "hello"

    def test_validation_failure(self):
        """FieldValidator raises ValueError on failure."""

        def must_be_positive(v: int) -> int:
            if v <= 0:
                raise ValueError("must be positive")
            return v

        PosInt = Annotated[int, FieldValidator(must_be_positive, "positive")]
        assert validate(5, PosInt) == 5
        with pytest.raises(ValidationError, match="positive"):
            validate(-1, PosInt)

    def test_assertion_error(self):
        """FieldValidator can also raise AssertionError."""

        def check(v: str) -> str:
            assert len(v) > 0, "must not be empty"
            return v

        NonEmpty = Annotated[str, FieldValidator(check, "non_empty")]
        with pytest.raises(ValidationError, match="non_empty"):
            validate("", NonEmpty)

    def test_not_checked_on_type_error(self):
        """FieldValidator should not run if base type fails."""
        call_count = 0

        def counter(v: str) -> str:
            nonlocal call_count
            call_count += 1
            return v

        Tracked = Annotated[str, FieldValidator(counter)]
        with pytest.raises(ValidationError):
            validate(123, Tracked)
        assert call_count == 0

    def test_chain_with_predicate(self):
        """FieldValidator composes with Predicate constraints."""

        def strip(v: str) -> str:
            return v.strip()

        # strip first, then check length >= 1
        Cleaned = Annotated[str, FieldValidator(strip, "strip"), MinLen(1)]
        assert validate("  hi  ", Cleaned) == "hi"
        with pytest.raises(ValidationError):
            validate("   ", Cleaned)  # strip → "" → MinLen(1) fails

    def test_multiple_field_validators(self):
        """Multiple FieldValidators compose left-to-right."""

        def strip(v: str) -> str:
            return v.strip()

        def lower(v: str) -> str:
            return v.lower()

        Cleaned = Annotated[
            str,
            FieldValidator(strip, "strip"),
            FieldValidator(lower, "lower"),
        ]
        assert validate("  HELLO  ", Cleaned) == "hello"

    def test_in_typeddict(self):
        """FieldValidator works inside TypedDict fields."""

        def normalize(v: str) -> str:
            return v.strip().lower()

        class Profile(TypedDict):
            username: Annotated[str, FieldValidator(normalize, "normalize")]
            age: int

        data = {"username": "  Alice  ", "age": 30}
        result = validate(data, Profile)
        # Note: validate doesn't mutate the original dict for field values,
        # but the returned value from _validate_annotated is the transformed one.
        # The top-level dict values are not replaced in-place (current behavior).
        assert result == data  # dict itself is returned as-is


# ── Model Validator ──


class _ModelValidatorFixture(TypedDict):
    password: str
    confirm: str


class _MVTransform(TypedDict):
    x: int
    y: int


class _MVMulti(TypedDict):
    a: int
    b: int


@model_validator(_ModelValidatorFixture)
def _check_passwords(data: dict) -> dict:
    if data.get("password") != data.get("confirm"):
        raise ValueError("passwords do not match")
    return data


@model_validator(_MVTransform)
def _add_sum(data: dict) -> dict:
    data["sum"] = data["x"] + data["y"]
    return data


@model_validator(_MVMulti)
def _check_a_positive(data: dict) -> dict:
    if data["a"] <= 0:
        raise ValueError("a must be positive")
    return data


@model_validator(_MVMulti)
def _check_a_less_than_b(data: dict) -> dict:
    if data["a"] >= data["b"]:
        raise ValueError("a must be less than b")
    return data


class TestModelValidator:
    def test_cross_field_valid(self):
        data = {"password": "secret", "confirm": "secret"}
        assert validate(data, _ModelValidatorFixture) == data

    def test_cross_field_invalid(self):
        data = {"password": "secret", "confirm": "wrong"}
        with pytest.raises(ValidationError, match="passwords do not match"):
            validate(data, _ModelValidatorFixture)

    def test_not_called_on_field_error(self):
        """Model validator should not run if field validation fails."""
        data = {"password": 123, "confirm": "secret"}  # password should be str
        with pytest.raises(ValidationError) as exc_info:
            validate(data, _ModelValidatorFixture)
        # Should have type error only, not model validator error
        assert all(
            "model validation" not in e.message.lower() for e in exc_info.value.errors
        )

    def test_not_called_on_missing_field(self):
        """Model validator should not run if required fields are missing."""
        data = {"password": "secret"}  # confirm is missing
        with pytest.raises(ValidationError) as exc_info:
            validate(data, _ModelValidatorFixture)
        assert any("MISSING" in e.actual for e in exc_info.value.errors)
        assert all(
            "model validation" not in e.message.lower() for e in exc_info.value.errors
        )

    def test_transform(self):
        """Model validator can modify the data dict."""
        data = {"x": 3, "y": 4}
        result = validate(data, _MVTransform)
        assert result["sum"] == 7

    def test_multiple_validators(self):
        """Multiple model validators run in registration order."""
        assert validate({"a": 1, "b": 2}, _MVMulti) == {"a": 1, "b": 2}

    def test_multiple_validators_first_fails(self):
        data = {"a": -1, "b": 2}
        with pytest.raises(ValidationError, match="a must be positive"):
            validate(data, _MVMulti)

    def test_multiple_validators_second_fails(self):
        data = {"a": 5, "b": 3}
        with pytest.raises(ValidationError, match="a must be less than b"):
            validate(data, _MVMulti)

    def test_on_dataclass(self):
        @dataclasses.dataclass
        class Range:
            lo: int
            hi: int

        @model_validator(Range)
        def _check_range(data: dict) -> dict:
            if data["lo"] >= data["hi"]:
                raise ValueError("lo must be less than hi")
            return data

        assert validate({"lo": 1, "hi": 10}, Range) == {"lo": 1, "hi": 10}
        with pytest.raises(ValidationError, match="lo must be less than hi"):
            validate({"lo": 10, "hi": 1}, Range)

    def test_error_path(self):
        """Model validator error should reference the struct path."""
        data = {"password": "a", "confirm": "b"}
        with pytest.raises(ValidationError) as exc_info:
            validate(data, _ModelValidatorFixture)
        err = exc_info.value.errors[0]
        assert err.path == "$"


# ── Cross-validation with pydantic ──

try:
    import pydantic

    _HAS_PYDANTIC = True
except ImportError:
    _HAS_PYDANTIC = False


@pytest.mark.skipif(not _HAS_PYDANTIC, reason="pydantic not installed")
class TestCrossValidation:
    def test_simple_valid(self):
        """Both accept valid data."""

        class PydanticUser(pydantic.BaseModel):
            name: str
            age: int

        data = {"name": "Alice", "age": 30}
        validate(data, SimpleUser)
        PydanticUser.model_validate(data)

    def test_simple_invalid(self):
        """Both reject invalid data."""

        class PydanticUser(pydantic.BaseModel):
            model_config = pydantic.ConfigDict(strict=True)
            name: str
            age: int

        data = {"name": "Alice", "age": "thirty"}
        with pytest.raises(ValidationError):
            validate(data, SimpleUser)
        with pytest.raises(pydantic.ValidationError):
            PydanticUser.model_validate(data)

    def test_missing_field(self):
        """Both reject missing required fields."""

        class PydanticUser(pydantic.BaseModel):
            name: str
            age: int

        data = {"name": "Alice"}
        with pytest.raises(ValidationError):
            validate(data, SimpleUser)
        with pytest.raises(pydantic.ValidationError):
            PydanticUser.model_validate(data)

    def test_bool_int_separation(self):
        """Both reject bool where int is expected (strict mode)."""

        class PydanticUser(pydantic.BaseModel):
            model_config = pydantic.ConfigDict(strict=True)
            name: str
            age: int

        data = {"name": "Alice", "age": True}
        with pytest.raises(ValidationError):
            validate(data, SimpleUser)
        with pytest.raises(pydantic.ValidationError):
            PydanticUser.model_validate(data)

    def test_nested_validation(self):
        """Both validate nested structures."""

        class PydanticAddress(pydantic.BaseModel):
            street: str
            city: str
            zip_code: str

        class PydanticUserAddr(pydantic.BaseModel):
            name: str
            address: PydanticAddress

        data = {
            "name": "Alice",
            "address": {"street": "123 Main St", "city": "NYC", "zip_code": "10001"},
        }
        validate(data, UserWithAddress)
        PydanticUserAddr.model_validate(data)

    def test_constraint_gt(self):
        """Both enforce Gt constraint."""

        class PydanticItem(pydantic.BaseModel):
            price: Annotated[float, pydantic.Field(gt=0)]

        class OurItem(TypedDict):
            price: Annotated[float, Gt(0)]

        validate({"price": 1.0}, OurItem)
        PydanticItem.model_validate({"price": 1.0})

        with pytest.raises(ValidationError):
            validate({"price": 0.0}, OurItem)
        with pytest.raises(pydantic.ValidationError):
            PydanticItem.model_validate({"price": 0.0})

    def test_json_schema_structure(self):
        """JSON Schema has same structure as pydantic."""

        class PydanticUser(pydantic.BaseModel):
            name: str
            age: int

        our_schema = json_schema(SimpleUser)
        pydantic_schema = PydanticUser.model_json_schema()

        assert our_schema["type"] == pydantic_schema["type"]
        assert set(our_schema["properties"]) == set(pydantic_schema["properties"])
        assert set(our_schema["required"]) == set(pydantic_schema["required"])
