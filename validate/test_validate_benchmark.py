"""Benchmark: zerodep validate vs pydantic."""

import os
import sys
from typing import Annotated

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from validate import Ge, Gt, Le, MaxLen, MinLen, json_schema, validate

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

pydantic = pytest.importorskip("pydantic", reason="pydantic not installed")


# ── Shared test data ──


class SimpleUserTD(TypedDict):
    name: str
    age: int
    email: str


class SimpleUserPydantic(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(strict=True)
    name: str
    age: int
    email: str


SIMPLE_DATA = {"name": "Alice", "age": 30, "email": "alice@example.com"}


class AddressTD(TypedDict):
    street: str
    city: str
    zip_code: str


class UserWithAddrTD(TypedDict):
    name: str
    age: int
    address: AddressTD


class AddressPydantic(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(strict=True)
    street: str
    city: str
    zip_code: str


class UserWithAddrPydantic(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(strict=True)
    name: str
    age: int
    address: AddressPydantic


NESTED_DATA = {
    "name": "Alice",
    "age": 30,
    "address": {"street": "123 Main St", "city": "NYC", "zip_code": "10001"},
}


class ConstrainedTD(TypedDict):
    name: Annotated[str, MinLen(1), MaxLen(100)]
    price: Annotated[float, Gt(0)]
    quantity: Annotated[int, Ge(0), Le(1000)]


class ConstrainedPydantic(pydantic.BaseModel):
    name: Annotated[str, pydantic.Field(min_length=1, max_length=100)]
    price: Annotated[float, pydantic.Field(gt=0)]
    quantity: Annotated[int, pydantic.Field(ge=0, le=1000)]


CONSTRAINED_DATA = {"name": "Widget", "price": 9.99, "quantity": 100}


class ItemTD(TypedDict):
    name: str
    price: float


ITEMS_DATA = [{"name": f"item_{i}", "price": float(i)} for i in range(50)]


# ── Benchmarks ──


class TestBenchmarkSimple:
    def test_ours(self, benchmark):
        benchmark(validate, SIMPLE_DATA, SimpleUserTD)

    def test_pydantic(self, benchmark):
        benchmark(SimpleUserPydantic.model_validate, SIMPLE_DATA)


class TestBenchmarkNested:
    def test_ours(self, benchmark):
        benchmark(validate, NESTED_DATA, UserWithAddrTD)

    def test_pydantic(self, benchmark):
        benchmark(UserWithAddrPydantic.model_validate, NESTED_DATA)


class TestBenchmarkConstrained:
    def test_ours(self, benchmark):
        benchmark(validate, CONSTRAINED_DATA, ConstrainedTD)

    def test_pydantic(self, benchmark):
        benchmark(ConstrainedPydantic.model_validate, CONSTRAINED_DATA)


class TestBenchmarkListOfDicts:
    def test_ours(self, benchmark):
        benchmark(validate, ITEMS_DATA, list[ItemTD])

    def test_pydantic(self, benchmark):
        class ItemPydantic(pydantic.BaseModel):
            model_config = pydantic.ConfigDict(strict=True)
            name: str
            price: float

        ta = pydantic.TypeAdapter(list[ItemPydantic])
        benchmark(ta.validate_python, ITEMS_DATA)


class TestBenchmarkJsonSchema:
    def test_ours(self, benchmark):
        benchmark(json_schema, ConstrainedTD)

    def test_pydantic(self, benchmark):
        benchmark(ConstrainedPydantic.model_json_schema)
