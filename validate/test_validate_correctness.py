"""Correctness tests: zerodep validate module."""

import dataclasses
import os
import sys
from typing import Annotated, Any, Literal, Optional, Union

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from validate import (
    ErrorDetail,
    Ge,
    Gt,
    Le,
    Lt,
    Match,
    MaxLen,
    MinLen,
    Predicate,
    ValidationError,
    json_schema,
    validate,
)

try:
    from typing import NotRequired, Required, TypedDict
except ImportError:
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
