# /// zerodep
# version = "0.4.0"
# deps = []
# tier = "subsystem"
# category = "data"
# ///

"""Zero-dependency proto3 encoder/decoder using Python dataclass schemas.

Part of zerodep: https://github.com/Oaklight/zerodep
Copyright (c) 2026 Peng Ding. MIT License.

Encode and decode Protocol Buffers (proto3) wire format using plain Python
dataclasses as message schemas.  No ``protoc`` compiler, no ``.proto`` files,
no C extensions — just stdlib + type annotations.

Basic usage::

    from protobuf import message, field, int32, repeated

    @message
    class Person:
        name: str = field(1)
        id: int32 = field(2)
        emails: repeated[str] = field(3)

    data = Person(name="Alice", id=123, emails=["a@b.com"]).serialize()
    person = Person.parse(data)
    print(person.to_dict())

Scalar type aliases::

    int32, int64, uint32, uint64        # varint
    sint32, sint64                      # varint + ZigZag
    fixed32, sfixed32, float32          # 32-bit fixed
    fixed64, sfixed64, double           # 64-bit fixed
    bool_                               # varint (0/1)

Composite fields::

    repeated[int32]         # packed repeated scalars
    map_field[str, int32]   # map<string, int32>

Proto3 semantics:
- All fields are optional with zero-value defaults.
- Fields at their default value are NOT serialized.
- Unknown fields are preserved across parse → serialize round-trips.
"""

from __future__ import annotations

import dataclasses
import struct
import sys
from enum import IntEnum
from typing import (
    Annotated,
    Any,
    get_type_hints,
)

if sys.version_info >= (3, 10):
    from typing import get_args, get_origin
else:
    from typing import get_args, get_origin

# ============================================================================
# Section 1: Wire-format primitives
# ============================================================================


class WireType(IntEnum):
    """Proto3 wire types."""

    VARINT = 0
    FIXED64 = 1
    LEN = 2
    # SGROUP = 3  (deprecated, not supported)
    # EGROUP = 4  (deprecated, not supported)
    FIXED32 = 5


def encode_varint(value: int) -> bytes:
    """Encode an unsigned integer as a varint.

    Args:
        value: Non-negative integer to encode.

    Returns:
        Varint-encoded bytes.
    """
    if value < 0:
        # Proto3 treats negative int32/int64 as 10-byte two's complement
        value = value & 0xFFFFFFFFFFFFFFFF
    buf = bytearray()
    while value > 0x7F:
        buf.append((value & 0x7F) | 0x80)
        value >>= 7
    buf.append(value & 0x7F)
    return bytes(buf)


def decode_varint(data: bytes | bytearray | memoryview, pos: int) -> tuple[int, int]:
    """Decode a varint from *data* starting at *pos*.

    Args:
        data: Buffer to read from.
        pos: Start offset.

    Returns:
        Tuple of (decoded value, new position after varint).

    Raises:
        ValueError: If the varint is malformed or exceeds 10 bytes.
    """
    result = 0
    shift = 0
    while True:
        if pos >= len(data):
            raise ValueError("Unexpected end of data while reading varint")
        byte = data[pos]
        result |= (byte & 0x7F) << shift
        pos += 1
        if not (byte & 0x80):
            break
        shift += 7
        if shift >= 70:
            raise ValueError("Varint too long (> 10 bytes)")
    return result, pos


def zigzag_encode(value: int) -> int:
    """ZigZag-encode a signed integer.

    Maps signed integers to unsigned: 0→0, -1→1, 1→2, -2→3, …

    Args:
        value: Signed integer.

    Returns:
        ZigZag-encoded unsigned integer.
    """
    return (value << 1) ^ (value >> 63)


def zigzag_decode(value: int) -> int:
    """ZigZag-decode an unsigned integer back to signed.

    Args:
        value: ZigZag-encoded unsigned integer.

    Returns:
        Original signed integer.
    """
    return (value >> 1) ^ -(value & 1)


def make_tag(field_number: int, wire_type: int) -> bytes:
    """Pack a field number and wire type into a tag varint.

    Args:
        field_number: Proto field number (1–536870911).
        wire_type: Wire type (0–5).

    Returns:
        Varint-encoded tag bytes.
    """
    return encode_varint((field_number << 3) | wire_type)


def decode_tag(data: bytes | bytearray | memoryview, pos: int) -> tuple[int, int, int]:
    """Decode a tag varint into field number and wire type.

    Args:
        data: Buffer.
        pos: Start offset.

    Returns:
        Tuple of (field_number, wire_type, new position).
    """
    tag, pos = decode_varint(data, pos)
    return tag >> 3, tag & 0x07, pos


def encode_fixed32(value: int) -> bytes:
    """Encode a 32-bit value in little-endian."""
    return struct.pack("<I", value & 0xFFFFFFFF)


def decode_fixed32(data: bytes | bytearray | memoryview, pos: int) -> tuple[int, int]:
    """Decode a 32-bit little-endian unsigned integer."""
    if pos + 4 > len(data):
        raise ValueError("Unexpected end of data reading fixed32")
    return struct.unpack_from("<I", data, pos)[0], pos + 4


def encode_sfixed32(value: int) -> bytes:
    """Encode a signed 32-bit value in little-endian."""
    return struct.pack("<i", value)


def decode_sfixed32(data: bytes | bytearray | memoryview, pos: int) -> tuple[int, int]:
    """Decode a signed 32-bit little-endian integer."""
    if pos + 4 > len(data):
        raise ValueError("Unexpected end of data reading sfixed32")
    return struct.unpack_from("<i", data, pos)[0], pos + 4


def encode_fixed64(value: int) -> bytes:
    """Encode a 64-bit value in little-endian."""
    return struct.pack("<Q", value & 0xFFFFFFFFFFFFFFFF)


def decode_fixed64(data: bytes | bytearray | memoryview, pos: int) -> tuple[int, int]:
    """Decode a 64-bit little-endian unsigned integer."""
    if pos + 8 > len(data):
        raise ValueError("Unexpected end of data reading fixed64")
    return struct.unpack_from("<Q", data, pos)[0], pos + 8


def encode_sfixed64(value: int) -> bytes:
    """Encode a signed 64-bit value in little-endian."""
    return struct.pack("<q", value)


def decode_sfixed64(data: bytes | bytearray | memoryview, pos: int) -> tuple[int, int]:
    """Decode a signed 64-bit little-endian integer."""
    if pos + 8 > len(data):
        raise ValueError("Unexpected end of data reading sfixed64")
    return struct.unpack_from("<q", data, pos)[0], pos + 8


def encode_float(value: float) -> bytes:
    """Encode a 32-bit float."""
    return struct.pack("<f", value)


def decode_float(data: bytes | bytearray | memoryview, pos: int) -> tuple[float, int]:
    """Decode a 32-bit float."""
    if pos + 4 > len(data):
        raise ValueError("Unexpected end of data reading float")
    return struct.unpack_from("<f", data, pos)[0], pos + 4


def encode_double(value: float) -> bytes:
    """Encode a 64-bit double."""
    return struct.pack("<d", value)


def decode_double(data: bytes | bytearray | memoryview, pos: int) -> tuple[float, int]:
    """Decode a 64-bit double."""
    if pos + 8 > len(data):
        raise ValueError("Unexpected end of data reading double")
    return struct.unpack_from("<d", data, pos)[0], pos + 8


# ============================================================================
# Section 2: Scalar type system
# ============================================================================


class ScalarType(IntEnum):
    """Identifies the proto3 scalar encoding strategy."""

    INT32 = 0
    INT64 = 1
    UINT32 = 2
    UINT64 = 3
    SINT32 = 4
    SINT64 = 5
    BOOL = 6
    FIXED32 = 7
    FIXED64 = 8
    SFIXED32 = 9
    SFIXED64 = 10
    FLOAT = 11
    DOUBLE = 12
    STRING = 13
    BYTES = 14
    ENUM = 15


@dataclasses.dataclass(frozen=True)
class ProtoScalar:
    """Annotated marker carrying proto wire-type metadata for a scalar field.

    Placed inside ``Annotated[base_type, ProtoScalar(...)]`` to tell the
    encoder/decoder how to serialize the value on the wire.
    """

    scalar_type: ScalarType
    wire_type: WireType

    @property
    def is_numeric(self) -> bool:
        return self.scalar_type not in (ScalarType.STRING, ScalarType.BYTES)

    @property
    def is_packable(self) -> bool:
        return self.wire_type != WireType.LEN


# Scalar type aliases — each is ``Annotated[python_type, ProtoScalar(...)]``
int32 = Annotated[int, ProtoScalar(ScalarType.INT32, WireType.VARINT)]
int64 = Annotated[int, ProtoScalar(ScalarType.INT64, WireType.VARINT)]
uint32 = Annotated[int, ProtoScalar(ScalarType.UINT32, WireType.VARINT)]
uint64 = Annotated[int, ProtoScalar(ScalarType.UINT64, WireType.VARINT)]
sint32 = Annotated[int, ProtoScalar(ScalarType.SINT32, WireType.VARINT)]
sint64 = Annotated[int, ProtoScalar(ScalarType.SINT64, WireType.VARINT)]
bool_ = Annotated[bool, ProtoScalar(ScalarType.BOOL, WireType.VARINT)]
fixed32 = Annotated[int, ProtoScalar(ScalarType.FIXED32, WireType.FIXED32)]
fixed64 = Annotated[int, ProtoScalar(ScalarType.FIXED64, WireType.FIXED64)]
sfixed32 = Annotated[int, ProtoScalar(ScalarType.SFIXED32, WireType.FIXED32)]
sfixed64 = Annotated[int, ProtoScalar(ScalarType.SFIXED64, WireType.FIXED64)]
float32 = Annotated[float, ProtoScalar(ScalarType.FLOAT, WireType.FIXED32)]
double = Annotated[float, ProtoScalar(ScalarType.DOUBLE, WireType.FIXED64)]

# Wire encoder/decoder lookup tables (indexed by ScalarType)
_SCALAR_ENCODERS: dict[ScalarType, Any] = {
    ScalarType.INT32: lambda v: encode_varint(
        v & 0xFFFFFFFF if v >= 0 else v & 0xFFFFFFFFFFFFFFFF
    ),
    ScalarType.INT64: lambda v: encode_varint(v & 0xFFFFFFFFFFFFFFFF),
    ScalarType.UINT32: lambda v: encode_varint(v & 0xFFFFFFFF),
    ScalarType.UINT64: lambda v: encode_varint(v & 0xFFFFFFFFFFFFFFFF),
    ScalarType.SINT32: lambda v: encode_varint(zigzag_encode(v)),
    ScalarType.SINT64: lambda v: encode_varint(zigzag_encode(v)),
    ScalarType.BOOL: lambda v: encode_varint(1 if v else 0),
    ScalarType.FIXED32: encode_fixed32,
    ScalarType.FIXED64: encode_fixed64,
    ScalarType.SFIXED32: encode_sfixed32,
    ScalarType.SFIXED64: encode_sfixed64,
    ScalarType.FLOAT: encode_float,
    ScalarType.DOUBLE: encode_double,
}

_SCALAR_DECODERS: dict[ScalarType, Any] = {
    ScalarType.INT32: lambda d, p: (
        lambda v, pp: (
            (v & 0xFFFFFFFF)
            if (v & 0xFFFFFFFF) < 0x80000000
            else (v & 0xFFFFFFFF) - 0x100000000,
            pp,
        )
    )(*decode_varint(d, p)),
    ScalarType.INT64: lambda d, p: (
        lambda v, pp: (v if v < 0x8000000000000000 else v - 0x10000000000000000, pp)
    )(*decode_varint(d, p)),
    ScalarType.UINT32: lambda d, p: (lambda v, pp: (v & 0xFFFFFFFF, pp))(
        *decode_varint(d, p)
    ),
    ScalarType.UINT64: decode_varint,
    ScalarType.SINT32: lambda d, p: (lambda v, pp: (zigzag_decode(v), pp))(
        *decode_varint(d, p)
    ),
    ScalarType.SINT64: lambda d, p: (lambda v, pp: (zigzag_decode(v), pp))(
        *decode_varint(d, p)
    ),
    ScalarType.BOOL: lambda d, p: (lambda v, pp: (bool(v), pp))(*decode_varint(d, p)),
    ScalarType.FIXED32: decode_fixed32,
    ScalarType.FIXED64: decode_fixed64,
    ScalarType.SFIXED32: decode_sfixed32,
    ScalarType.SFIXED64: decode_sfixed64,
    ScalarType.FLOAT: decode_float,
    ScalarType.DOUBLE: decode_double,
}

# Default zero-values per scalar type
_SCALAR_DEFAULTS: dict[ScalarType, Any] = {
    ScalarType.INT32: 0,
    ScalarType.INT64: 0,
    ScalarType.UINT32: 0,
    ScalarType.UINT64: 0,
    ScalarType.SINT32: 0,
    ScalarType.SINT64: 0,
    ScalarType.BOOL: False,
    ScalarType.FIXED32: 0,
    ScalarType.FIXED64: 0,
    ScalarType.SFIXED32: 0,
    ScalarType.SFIXED64: 0,
    ScalarType.FLOAT: 0.0,
    ScalarType.DOUBLE: 0.0,
    ScalarType.STRING: "",
    ScalarType.BYTES: b"",
    ScalarType.ENUM: 0,
}


# ============================================================================
# Section 3: Field descriptors
# ============================================================================


@dataclasses.dataclass(frozen=True)
class Repeated:
    """Annotated marker for ``repeated`` fields.

    ``repeated[int32]`` expands to
    ``Annotated[list[int], Repeated(...), ProtoScalar(...)]``.
    """

    item_type: type | Any  # The inner type (e.g., int32, str, a message class)


@dataclasses.dataclass(frozen=True)
class MapField:
    """Annotated marker for ``map<K, V>`` fields.

    ``map_field[str, int32]`` expands to ``Annotated[dict[str, int], MapField(...)]``.
    """

    key_type: type | Any
    value_type: type | Any


@dataclasses.dataclass(frozen=True)
class OneofGroup:
    """Annotated marker for ``oneof`` field grouping."""

    group_name: str


class _RepeatedMeta(type):
    """Metaclass for ``repeated`` that supports ``repeated[T]`` syntax."""

    def __getitem__(cls, item: Any) -> Any:
        # Extract the scalar marker if present
        scalar = _extract_proto_scalar(item)
        base = _get_base_type(item)
        annotations: list[Any] = [Repeated(item)]
        if scalar is not None:
            annotations.append(scalar)
        return Annotated[tuple((list[base], *annotations))]


class repeated(metaclass=_RepeatedMeta):  # noqa: N801
    """Subscriptable type alias for repeated proto fields.

    Usage: ``emails: repeated[str] = field(3)``
    """


class _MapFieldMeta(type):
    """Metaclass for ``map_field`` that supports ``map_field[K, V]`` syntax."""

    def __getitem__(cls, items: tuple[Any, Any]) -> Any:
        if not isinstance(items, tuple) or len(items) != 2:
            raise TypeError(
                "map_field requires exactly 2 type arguments: map_field[K, V]"
            )
        key_type, value_type = items
        key_base = _get_base_type(key_type)
        value_base = _get_base_type(value_type)
        return Annotated[dict[key_base, value_base], MapField(key_type, value_type)]


class map_field(metaclass=_MapFieldMeta):  # noqa: N801
    """Subscriptable type alias for map proto fields.

    Usage: ``attrs: map_field[str, int32] = field(5)``
    """


def oneof(group_name: str) -> OneofGroup:
    """Create a oneof group marker for use in field metadata.

    Usage::

        @message
        class Msg:
            text: str = field(1, oneof="body")
            image: bytes = field(2, oneof="body")

    Args:
        group_name: Name of the oneof group.

    Returns:
        OneofGroup marker.
    """
    return OneofGroup(group_name)


def field(
    number: int,
    *,
    default: Any = dataclasses.MISSING,
    default_factory: Any = dataclasses.MISSING,
    oneof: str | None = None,
) -> Any:
    """Define a proto field with its field number.

    Args:
        number: Proto field number (must be >= 1).
        default: Default value for the field.
        default_factory: Factory for mutable default values.
        oneof: Optional oneof group name.

    Returns:
        A ``dataclasses.Field`` with proto metadata.
    """
    if number < 1:
        raise ValueError(f"Field number must be >= 1, got {number}")
    metadata: dict[str, Any] = {"proto_number": number}
    if oneof is not None:
        metadata["proto_oneof"] = oneof
    kwargs: dict[str, Any] = {"metadata": metadata}
    if default is not dataclasses.MISSING:
        kwargs["default"] = default
    elif default_factory is not dataclasses.MISSING:
        kwargs["default_factory"] = default_factory
    return dataclasses.field(**kwargs)


# ============================================================================
# Section 4: Type introspection helpers
# ============================================================================


def _extract_proto_scalar(tp: Any) -> ProtoScalar | None:
    """Extract ``ProtoScalar`` from an ``Annotated`` type, or None."""
    if get_origin(tp) is Annotated:
        for arg in get_args(tp)[1:]:
            if isinstance(arg, ProtoScalar):
                return arg
    return None


def _extract_repeated(tp: Any) -> Repeated | None:
    """Extract ``Repeated`` marker from an ``Annotated`` type, or None."""
    if get_origin(tp) is Annotated:
        for arg in get_args(tp)[1:]:
            if isinstance(arg, Repeated):
                return arg
    return None


def _extract_map_field(tp: Any) -> MapField | None:
    """Extract ``MapField`` marker from an ``Annotated`` type, or None."""
    if get_origin(tp) is Annotated:
        for arg in get_args(tp)[1:]:
            if isinstance(arg, MapField):
                return arg
    return None


def _get_base_type(tp: Any) -> type:
    """Strip ``Annotated`` wrappers to get the base Python type."""
    if get_origin(tp) is Annotated:
        return get_args(tp)[0]
    return tp


def _is_message_type(tp: Any) -> bool:
    """Check if *tp* is a ``@message``-decorated class."""
    return isinstance(tp, type) and hasattr(tp, "_proto_descriptor")


def _is_enum_type(tp: Any) -> bool:
    """Check if *tp* is an IntEnum subclass (proto enum)."""
    return isinstance(tp, type) and issubclass(tp, IntEnum)


# ============================================================================
# Section 5: Message descriptor
# ============================================================================


class FieldKind(IntEnum):
    """Categories for how a field is encoded on the wire."""

    SCALAR = 0
    STRING = 1
    BYTES = 2
    MESSAGE = 3
    ENUM = 4
    REPEATED_SCALAR = 5  # packed
    REPEATED_MESSAGE = 6  # length-delimited per element
    REPEATED_ENUM = 7  # packed
    REPEATED_STRING = 8  # length-delimited per element
    REPEATED_BYTES = 9  # length-delimited per element
    MAP = 10


@dataclasses.dataclass(frozen=True)
class FieldInfo:
    """Resolved metadata for a single proto field."""

    name: str
    number: int
    kind: FieldKind
    wire_type: WireType
    scalar: ProtoScalar | None  # non-None for scalar/enum kinds
    message_type: type | None  # non-None for MESSAGE/REPEATED_MESSAGE
    repeated_marker: Repeated | None
    map_marker: MapField | None
    oneof_group: str | None
    python_type: type  # base Python type (int, str, etc.)
    default_value: Any  # proto3 zero-value


class _MessageDescriptor:
    """Compiled schema for a ``@message``-decorated class.

    Built once at decoration time. Holds field metadata, encoding tables,
    and lookup structures needed by the encoder/decoder.
    """

    def __init__(self, cls: type) -> None:
        self.cls = cls
        self.fields: dict[str, FieldInfo] = {}
        self.fields_by_number: dict[int, FieldInfo] = {}
        self.oneof_groups: dict[str, list[FieldInfo]] = {}
        self._build(cls)

    def _build(self, cls: type) -> None:
        hints = get_type_hints(cls, include_extras=True)
        dc_fields = {f.name: f for f in dataclasses.fields(cls)}

        for name, annotation in hints.items():
            if name.startswith("_"):
                continue
            dc_field = dc_fields.get(name)
            if dc_field is None:
                continue
            metadata = dc_field.metadata
            if "proto_number" not in metadata:
                continue

            number = metadata["proto_number"]
            oneof_group = metadata.get("proto_oneof")

            info = self._resolve_field(name, number, annotation, oneof_group)
            self.fields[name] = info
            self.fields_by_number[number] = info

            if oneof_group:
                self.oneof_groups.setdefault(oneof_group, []).append(info)

    def _resolve_field(
        self,
        name: str,
        number: int,
        annotation: Any,
        oneof_group: str | None,
    ) -> FieldInfo:
        # Check for map first
        map_marker = _extract_map_field(annotation)
        if map_marker is not None:
            return FieldInfo(
                name=name,
                number=number,
                kind=FieldKind.MAP,
                wire_type=WireType.LEN,
                scalar=None,
                message_type=None,
                repeated_marker=None,
                map_marker=map_marker,
                oneof_group=oneof_group,
                python_type=dict,
                default_value={},
            )

        # Check for repeated
        rep_marker = _extract_repeated(annotation)
        if rep_marker is not None:
            return self._resolve_repeated(name, number, rep_marker, oneof_group)

        # Scalar or message
        return self._resolve_singular(name, number, annotation, oneof_group)

    def _resolve_repeated(
        self,
        name: str,
        number: int,
        rep: Repeated,
        oneof_group: str | None,
    ) -> FieldInfo:
        inner = rep.item_type
        inner_scalar = _extract_proto_scalar(inner)
        inner_base = _get_base_type(inner)

        if _is_message_type(inner_base):
            kind = FieldKind.REPEATED_MESSAGE
            return FieldInfo(
                name=name,
                number=number,
                kind=kind,
                wire_type=WireType.LEN,
                scalar=None,
                message_type=inner_base,
                repeated_marker=rep,
                map_marker=None,
                oneof_group=oneof_group,
                python_type=list,
                default_value=[],
            )

        if _is_enum_type(inner_base):
            kind = FieldKind.REPEATED_ENUM
            scalar = ProtoScalar(ScalarType.ENUM, WireType.VARINT)
            return FieldInfo(
                name=name,
                number=number,
                kind=kind,
                wire_type=WireType.LEN,
                scalar=scalar,
                message_type=None,
                repeated_marker=rep,
                map_marker=None,
                oneof_group=oneof_group,
                python_type=list,
                default_value=[],
            )

        if inner_base is str:
            return FieldInfo(
                name=name,
                number=number,
                kind=FieldKind.REPEATED_STRING,
                wire_type=WireType.LEN,
                scalar=ProtoScalar(ScalarType.STRING, WireType.LEN),
                message_type=None,
                repeated_marker=rep,
                map_marker=None,
                oneof_group=oneof_group,
                python_type=list,
                default_value=[],
            )

        if inner_base is bytes:
            return FieldInfo(
                name=name,
                number=number,
                kind=FieldKind.REPEATED_BYTES,
                wire_type=WireType.LEN,
                scalar=ProtoScalar(ScalarType.BYTES, WireType.LEN),
                message_type=None,
                repeated_marker=rep,
                map_marker=None,
                oneof_group=oneof_group,
                python_type=list,
                default_value=[],
            )

        # Repeated scalar (packed by default in proto3)
        if inner_scalar is None:
            # Bare int/float without annotation — default to int64/double
            if inner_base is int:
                inner_scalar = ProtoScalar(ScalarType.INT64, WireType.VARINT)
            elif inner_base is float:
                inner_scalar = ProtoScalar(ScalarType.DOUBLE, WireType.FIXED64)
            elif inner_base is bool:
                inner_scalar = ProtoScalar(ScalarType.BOOL, WireType.VARINT)
            else:
                raise TypeError(
                    f"Cannot determine proto scalar type for repeated field "
                    f"'{name}' with inner type {inner_base!r}"
                )

        return FieldInfo(
            name=name,
            number=number,
            kind=FieldKind.REPEATED_SCALAR,
            wire_type=WireType.LEN,
            scalar=inner_scalar,
            message_type=None,
            repeated_marker=rep,
            map_marker=None,
            oneof_group=oneof_group,
            python_type=list,
            default_value=[],
        )

    def _resolve_singular(
        self,
        name: str,
        number: int,
        annotation: Any,
        oneof_group: str | None,
    ) -> FieldInfo:
        scalar = _extract_proto_scalar(annotation)
        base = _get_base_type(annotation)

        # Message type
        if _is_message_type(base):
            return FieldInfo(
                name=name,
                number=number,
                kind=FieldKind.MESSAGE,
                wire_type=WireType.LEN,
                scalar=None,
                message_type=base,
                repeated_marker=None,
                map_marker=None,
                oneof_group=oneof_group,
                python_type=base,
                default_value=None,
            )

        # Enum type
        if _is_enum_type(base):
            return FieldInfo(
                name=name,
                number=number,
                kind=FieldKind.ENUM,
                wire_type=WireType.VARINT,
                scalar=ProtoScalar(ScalarType.ENUM, WireType.VARINT),
                message_type=None,
                repeated_marker=None,
                map_marker=None,
                oneof_group=oneof_group,
                python_type=base,
                default_value=(base(0) if 0 in [e.value for e in base] else 0),
            )

        # String
        if base is str:
            return FieldInfo(
                name=name,
                number=number,
                kind=FieldKind.STRING,
                wire_type=WireType.LEN,
                scalar=ProtoScalar(ScalarType.STRING, WireType.LEN),
                message_type=None,
                repeated_marker=None,
                map_marker=None,
                oneof_group=oneof_group,
                python_type=str,
                default_value="",
            )

        # Bytes
        if base is bytes:
            return FieldInfo(
                name=name,
                number=number,
                kind=FieldKind.BYTES,
                wire_type=WireType.LEN,
                scalar=ProtoScalar(ScalarType.BYTES, WireType.LEN),
                message_type=None,
                repeated_marker=None,
                map_marker=None,
                oneof_group=oneof_group,
                python_type=bytes,
                default_value=b"",
            )

        # Explicit scalar annotation
        if scalar is not None:
            return FieldInfo(
                name=name,
                number=number,
                kind=FieldKind.SCALAR,
                wire_type=scalar.wire_type,
                scalar=scalar,
                message_type=None,
                repeated_marker=None,
                map_marker=None,
                oneof_group=oneof_group,
                python_type=base,
                default_value=_SCALAR_DEFAULTS[scalar.scalar_type],
            )

        # Bare int/float/bool without annotation
        if base is int:
            s = ProtoScalar(ScalarType.INT64, WireType.VARINT)
        elif base is float:
            s = ProtoScalar(ScalarType.DOUBLE, WireType.FIXED64)
        elif base is bool:
            s = ProtoScalar(ScalarType.BOOL, WireType.VARINT)
        else:
            raise TypeError(
                f"Cannot determine proto type for field '{name}' "
                f"with annotation {annotation!r}"
            )
        return FieldInfo(
            name=name,
            number=number,
            kind=FieldKind.SCALAR,
            wire_type=s.wire_type,
            scalar=s,
            message_type=None,
            repeated_marker=None,
            map_marker=None,
            oneof_group=oneof_group,
            python_type=base,
            default_value=_SCALAR_DEFAULTS[s.scalar_type],
        )


# ============================================================================
# Section 6: Encoder
# ============================================================================


def _is_default_value(info: FieldInfo, value: Any) -> bool:
    """Check if a value is the proto3 zero-value for its field."""
    if info.kind == FieldKind.MAP:
        return not value
    if info.kind in (
        FieldKind.REPEATED_SCALAR,
        FieldKind.REPEATED_MESSAGE,
        FieldKind.REPEATED_ENUM,
        FieldKind.REPEATED_STRING,
        FieldKind.REPEATED_BYTES,
    ):
        return not value
    if info.kind == FieldKind.MESSAGE:
        return value is None
    if info.kind == FieldKind.ENUM:
        return int(value) == 0
    if info.scalar is not None:
        return value == _SCALAR_DEFAULTS[info.scalar.scalar_type]
    return False


def _encode_scalar_value(scalar: ProtoScalar, value: Any) -> bytes:
    """Encode a single scalar value (without tag)."""
    encoder = _SCALAR_ENCODERS[scalar.scalar_type]
    return encoder(value)


def _encode_length_delimited(data: bytes) -> bytes:
    """Wrap bytes with a varint length prefix."""
    return encode_varint(len(data)) + data


def _encode_field(info: FieldInfo, value: Any) -> bytes:
    """Encode a single field (tag + value)."""
    tag = make_tag(info.number, info.wire_type)

    if info.kind == FieldKind.SCALAR:
        assert info.scalar is not None
        return tag + _encode_scalar_value(info.scalar, value)

    if info.kind == FieldKind.ENUM:
        return tag + encode_varint(int(value) & 0xFFFFFFFFFFFFFFFF)

    if info.kind == FieldKind.STRING:
        encoded = value.encode("utf-8")
        return tag + _encode_length_delimited(encoded)

    if info.kind == FieldKind.BYTES:
        return tag + _encode_length_delimited(value)

    if info.kind == FieldKind.MESSAGE:
        msg_bytes = _encode_message(value)
        return tag + _encode_length_delimited(msg_bytes)

    if info.kind == FieldKind.REPEATED_SCALAR:
        return _encode_packed_repeated(info, value)

    if info.kind == FieldKind.REPEATED_ENUM:
        return _encode_packed_enum(info, value)

    if info.kind == FieldKind.REPEATED_MESSAGE:
        return _encode_repeated_messages(info, value)

    if info.kind == FieldKind.REPEATED_STRING:
        return _encode_repeated_strings(info, value)

    if info.kind == FieldKind.REPEATED_BYTES:
        return _encode_repeated_bytes(info, value)

    if info.kind == FieldKind.MAP:
        return _encode_map(info, value)

    raise TypeError(f"Unknown field kind: {info.kind}")  # pragma: no cover


def _encode_packed_repeated(info: FieldInfo, values: list[Any]) -> bytes:
    """Encode a packed repeated scalar field."""
    if not values:
        return b""
    assert info.scalar is not None
    body = b"".join(_encode_scalar_value(info.scalar, v) for v in values)
    tag = make_tag(info.number, WireType.LEN)
    return tag + _encode_length_delimited(body)


def _encode_packed_enum(info: FieldInfo, values: list[Any]) -> bytes:
    """Encode a packed repeated enum field."""
    if not values:
        return b""
    body = b"".join(encode_varint(int(v) & 0xFFFFFFFFFFFFFFFF) for v in values)
    tag = make_tag(info.number, WireType.LEN)
    return tag + _encode_length_delimited(body)


def _encode_repeated_messages(info: FieldInfo, values: list[Any]) -> bytes:
    """Encode repeated message fields (each length-delimited)."""
    buf = bytearray()
    tag = make_tag(info.number, WireType.LEN)
    for v in values:
        msg_bytes = _encode_message(v)
        buf.extend(tag)
        buf.extend(_encode_length_delimited(msg_bytes))
    return bytes(buf)


def _encode_repeated_strings(info: FieldInfo, values: list[str]) -> bytes:
    """Encode repeated string fields (each length-delimited)."""
    buf = bytearray()
    tag = make_tag(info.number, WireType.LEN)
    for v in values:
        encoded = v.encode("utf-8")
        buf.extend(tag)
        buf.extend(_encode_length_delimited(encoded))
    return bytes(buf)


def _encode_repeated_bytes(info: FieldInfo, values: list[bytes]) -> bytes:
    """Encode repeated bytes fields (each length-delimited)."""
    buf = bytearray()
    tag = make_tag(info.number, WireType.LEN)
    for v in values:
        buf.extend(tag)
        buf.extend(_encode_length_delimited(v))
    return bytes(buf)


def _encode_map(info: FieldInfo, mapping: dict[Any, Any]) -> bytes:
    """Encode a map field as repeated key-value entry messages.

    Each entry is a message with field 1 = key, field 2 = value.
    """
    assert info.map_marker is not None
    buf = bytearray()
    tag = make_tag(info.number, WireType.LEN)

    key_scalar = _extract_proto_scalar(info.map_marker.key_type) or _infer_scalar(
        _get_base_type(info.map_marker.key_type)
    )
    value_scalar = _extract_proto_scalar(info.map_marker.value_type)
    value_base = _get_base_type(info.map_marker.value_type)
    value_is_message = _is_message_type(value_base)
    value_is_enum = _is_enum_type(value_base)

    for k, v in mapping.items():
        entry = bytearray()
        # Key: field 1
        entry.extend(make_tag(1, key_scalar.wire_type))
        if key_scalar.scalar_type == ScalarType.STRING:
            entry.extend(_encode_length_delimited(k.encode("utf-8")))
        else:
            entry.extend(_encode_scalar_value(key_scalar, k))

        # Value: field 2
        if value_is_message:
            msg_bytes = _encode_message(v)
            entry.extend(make_tag(2, WireType.LEN))
            entry.extend(_encode_length_delimited(msg_bytes))
        elif value_is_enum:
            entry.extend(make_tag(2, WireType.VARINT))
            entry.extend(encode_varint(int(v) & 0xFFFFFFFFFFFFFFFF))
        elif value_base is str:
            entry.extend(make_tag(2, WireType.LEN))
            entry.extend(_encode_length_delimited(v.encode("utf-8")))
        elif value_base is bytes:
            entry.extend(make_tag(2, WireType.LEN))
            entry.extend(_encode_length_delimited(v))
        elif value_scalar is not None:
            entry.extend(make_tag(2, value_scalar.wire_type))
            entry.extend(_encode_scalar_value(value_scalar, v))
        else:
            vs = _infer_scalar(value_base)
            entry.extend(make_tag(2, vs.wire_type))
            entry.extend(_encode_scalar_value(vs, v))

        buf.extend(tag)
        buf.extend(_encode_length_delimited(bytes(entry)))

    return bytes(buf)


def _infer_scalar(base: type) -> ProtoScalar:
    """Infer a default ProtoScalar for a bare Python type."""
    if base is int:
        return ProtoScalar(ScalarType.INT64, WireType.VARINT)
    if base is float:
        return ProtoScalar(ScalarType.DOUBLE, WireType.FIXED64)
    if base is bool:
        return ProtoScalar(ScalarType.BOOL, WireType.VARINT)
    if base is str:
        return ProtoScalar(ScalarType.STRING, WireType.LEN)
    if base is bytes:
        return ProtoScalar(ScalarType.BYTES, WireType.LEN)
    raise TypeError(f"Cannot infer proto scalar for {base!r}")


def _encode_message(obj: Any) -> bytes:
    """Encode a ``@message`` instance to wire format.

    Args:
        obj: Instance of a ``@message``-decorated class.

    Returns:
        Wire-format bytes (without outer length prefix).
    """
    desc: _MessageDescriptor = obj._proto_descriptor
    buf = bytearray()

    # Encode known fields in field-number order for deterministic output
    for info in sorted(desc.fields.values(), key=lambda f: f.number):
        value = getattr(obj, info.name)
        if _is_default_value(info, value):
            continue
        buf.extend(_encode_field(info, value))

    # Append unknown fields
    unknown = getattr(obj, "_unknown_fields", None)
    if unknown:
        for _fn, _wt, raw in unknown:
            buf.extend(make_tag(_fn, _wt))
            if _wt == WireType.LEN:
                buf.extend(_encode_length_delimited(raw))
            elif _wt == WireType.VARINT:
                buf.extend(raw)
            else:
                buf.extend(raw)

    return bytes(buf)


# ============================================================================
# Section 7: Decoder
# ============================================================================


def _skip_field(
    wire_type: int, data: bytes | bytearray | memoryview, pos: int
) -> tuple[bytes, int]:
    """Skip an unknown field and return its raw bytes."""
    if wire_type == WireType.VARINT:
        start = pos
        while pos < len(data) and data[pos] & 0x80:
            pos += 1
        pos += 1  # last byte
        return bytes(data[start:pos]), pos
    if wire_type == WireType.FIXED64:
        return bytes(data[pos : pos + 8]), pos + 8
    if wire_type == WireType.LEN:
        length, pos = decode_varint(data, pos)
        return bytes(data[pos : pos + length]), pos + length
    if wire_type == WireType.FIXED32:
        return bytes(data[pos : pos + 4]), pos + 4
    raise ValueError(f"Unknown wire type {wire_type}")


def _decode_scalar_from_wire(
    scalar: ProtoScalar,
    wire_type: int,
    data: bytes | bytearray | memoryview,
    pos: int,
) -> tuple[Any, int]:
    """Decode a scalar value given actual wire type and position."""
    decoder = _SCALAR_DECODERS[scalar.scalar_type]
    return decoder(data, pos)


def _decode_map_entry(
    map_marker: MapField,
    data: bytes | bytearray | memoryview,
    pos: int,
    end: int,
) -> tuple[Any, Any]:
    """Decode a single map entry message (fields 1=key, 2=value)."""
    key_scalar = _extract_proto_scalar(map_marker.key_type) or _infer_scalar(
        _get_base_type(map_marker.key_type)
    )
    value_scalar = _extract_proto_scalar(map_marker.value_type)
    value_base = _get_base_type(map_marker.value_type)
    value_is_message = _is_message_type(value_base)
    value_is_enum = _is_enum_type(value_base)

    key: Any = _SCALAR_DEFAULTS.get(key_scalar.scalar_type, 0)
    value: Any = None

    while pos < end:
        fn, wt, pos = decode_tag(data, pos)
        if fn == 1:
            # Key field
            if key_scalar.scalar_type == ScalarType.STRING:
                length, pos = decode_varint(data, pos)
                key = data[pos : pos + length]
                if isinstance(key, memoryview):
                    key = bytes(key)
                key = key.decode("utf-8")
                pos += length
            else:
                key, pos = _decode_scalar_from_wire(key_scalar, wt, data, pos)
        elif fn == 2:
            # Value field
            if value_is_message:
                length, pos = decode_varint(data, pos)
                value = _decode_message_bytes(value_base, data, pos, pos + length)
                pos += length
            elif value_is_enum:
                raw, pos = decode_varint(data, pos)
                try:
                    value = value_base(raw)
                except ValueError:
                    value = raw
            elif value_base is str:
                length, pos = decode_varint(data, pos)
                raw_bytes = data[pos : pos + length]
                if isinstance(raw_bytes, memoryview):
                    raw_bytes = bytes(raw_bytes)
                value = raw_bytes.decode("utf-8")
                pos += length
            elif value_base is bytes:
                length, pos = decode_varint(data, pos)
                raw_bytes = data[pos : pos + length]
                if isinstance(raw_bytes, memoryview):
                    raw_bytes = bytes(raw_bytes)
                value = raw_bytes
                pos += length
            elif value_scalar is not None:
                value, pos = _decode_scalar_from_wire(value_scalar, wt, data, pos)
            else:
                vs = _infer_scalar(value_base)
                value, pos = _decode_scalar_from_wire(vs, wt, data, pos)
        else:
            _, pos = _skip_field(wt, data, pos)

    if value is None:
        # Set default value for the value type
        if value_is_message:
            value = value_base()
        elif value_is_enum:
            value = 0
        elif value_base is str:
            value = ""
        elif value_base is bytes:
            value = b""
        elif value_scalar is not None:
            value = _SCALAR_DEFAULTS[value_scalar.scalar_type]
        else:
            value = _SCALAR_DEFAULTS.get(_infer_scalar(value_base).scalar_type, 0)

    return key, value


def _decode_message_bytes(
    cls: type,
    data: bytes | bytearray | memoryview,
    pos: int,
    end: int,
) -> Any:
    """Decode a message from a byte range [pos, end)."""
    desc: _MessageDescriptor = cls._proto_descriptor
    values: dict[str, Any] = {}
    unknown_fields: list[tuple[int, int, bytes]] = []

    # Initialize repeated/map fields
    for info in desc.fields.values():
        if info.kind in (
            FieldKind.REPEATED_SCALAR,
            FieldKind.REPEATED_MESSAGE,
            FieldKind.REPEATED_ENUM,
            FieldKind.REPEATED_STRING,
            FieldKind.REPEATED_BYTES,
        ):
            values[info.name] = []
        elif info.kind == FieldKind.MAP:
            values[info.name] = {}

    while pos < end:
        field_number, wire_type, pos = decode_tag(data, pos)
        info = desc.fields_by_number.get(field_number)

        if info is None:
            raw, pos = _skip_field(wire_type, data, pos)
            unknown_fields.append((field_number, wire_type, raw))
            continue

        # Scalar
        if info.kind == FieldKind.SCALAR:
            assert info.scalar is not None
            value, pos = _decode_scalar_from_wire(info.scalar, wire_type, data, pos)
            values[info.name] = value

        # Enum
        elif info.kind == FieldKind.ENUM:
            raw, pos = decode_varint(data, pos)
            assert info.message_type is None
            enum_type = info.python_type
            try:
                values[info.name] = enum_type(raw) if _is_enum_type(enum_type) else raw
            except ValueError:
                values[info.name] = raw

        # String
        elif info.kind == FieldKind.STRING:
            length, pos = decode_varint(data, pos)
            raw_bytes = data[pos : pos + length]
            if isinstance(raw_bytes, memoryview):
                raw_bytes = bytes(raw_bytes)
            values[info.name] = raw_bytes.decode("utf-8")
            pos += length

        # Bytes
        elif info.kind == FieldKind.BYTES:
            length, pos = decode_varint(data, pos)
            raw_bytes = data[pos : pos + length]
            if isinstance(raw_bytes, memoryview):
                raw_bytes = bytes(raw_bytes)
            values[info.name] = raw_bytes
            pos += length

        # Message
        elif info.kind == FieldKind.MESSAGE:
            assert info.message_type is not None
            length, pos = decode_varint(data, pos)
            msg = _decode_message_bytes(info.message_type, data, pos, pos + length)
            values[info.name] = msg
            pos += length

        # Repeated scalar (packed)
        elif info.kind == FieldKind.REPEATED_SCALAR:
            assert info.scalar is not None
            if wire_type == WireType.LEN:
                # Packed encoding
                length, pos = decode_varint(data, pos)
                pack_end = pos + length
                while pos < pack_end:
                    val, pos = _decode_scalar_from_wire(
                        info.scalar, info.scalar.wire_type, data, pos
                    )
                    values[info.name].append(val)
            else:
                # Non-packed (single element)
                val, pos = _decode_scalar_from_wire(info.scalar, wire_type, data, pos)
                values[info.name].append(val)

        # Repeated enum (packed)
        elif info.kind == FieldKind.REPEATED_ENUM:
            if wire_type == WireType.LEN:
                length, pos = decode_varint(data, pos)
                pack_end = pos + length
                inner_base = (
                    _get_base_type(info.repeated_marker.item_type)
                    if info.repeated_marker
                    else None
                )
                while pos < pack_end:
                    raw_val, pos = decode_varint(data, pos)
                    if inner_base is not None and _is_enum_type(inner_base):
                        try:
                            raw_val = inner_base(raw_val)
                        except ValueError:
                            pass
                    values[info.name].append(raw_val)
            else:
                raw_val, pos = decode_varint(data, pos)
                inner_base = (
                    _get_base_type(info.repeated_marker.item_type)
                    if info.repeated_marker
                    else None
                )
                if inner_base is not None and _is_enum_type(inner_base):
                    try:
                        raw_val = inner_base(raw_val)
                    except ValueError:
                        pass
                values[info.name].append(raw_val)

        # Repeated message
        elif info.kind == FieldKind.REPEATED_MESSAGE:
            assert info.message_type is not None
            length, pos = decode_varint(data, pos)
            msg = _decode_message_bytes(info.message_type, data, pos, pos + length)
            values[info.name].append(msg)
            pos += length

        # Repeated string
        elif info.kind == FieldKind.REPEATED_STRING:
            length, pos = decode_varint(data, pos)
            raw_bytes = data[pos : pos + length]
            if isinstance(raw_bytes, memoryview):
                raw_bytes = bytes(raw_bytes)
            values[info.name].append(raw_bytes.decode("utf-8"))
            pos += length

        # Repeated bytes
        elif info.kind == FieldKind.REPEATED_BYTES:
            length, pos = decode_varint(data, pos)
            raw_bytes = data[pos : pos + length]
            if isinstance(raw_bytes, memoryview):
                raw_bytes = bytes(raw_bytes)
            values[info.name].append(raw_bytes)
            pos += length

        # Map
        elif info.kind == FieldKind.MAP:
            assert info.map_marker is not None
            length, pos = decode_varint(data, pos)
            k, v = _decode_map_entry(info.map_marker, data, pos, pos + length)
            values[info.name][k] = v
            pos += length

    # Build instance
    obj = cls.__new__(cls)
    for finfo in desc.fields.values():
        val = values.get(finfo.name, finfo.default_value)
        # Copy mutable defaults
        if val is finfo.default_value and isinstance(val, (list, dict)):
            val = type(val)(val)
        object.__setattr__(obj, finfo.name, val)
    object.__setattr__(obj, "_unknown_fields", unknown_fields)
    return obj


# ============================================================================
# Section 8: @message decorator and public API
# ============================================================================


def _msg_serialize(self: Any) -> bytes:
    """Serialize this message to proto3 wire format."""
    return _encode_message(self)


def _msg_parse(cls: type, data: bytes | bytearray | memoryview) -> Any:
    """Parse proto3 wire-format bytes into a message instance.

    Args:
        data: Wire-format bytes.

    Returns:
        Instance of the message class.
    """
    if isinstance(data, memoryview):
        data = bytes(data)
    return _decode_message_bytes(cls, data, 0, len(data))


def _msg_to_dict(self: Any) -> dict[str, Any]:
    """Convert message to a plain dict (recursive).

    - Enum values become their integer value.
    - bytes fields become base64-encoded strings.
    - Nested messages are recursively converted.
    - Unknown fields are excluded.
    """

    desc: _MessageDescriptor = self._proto_descriptor
    result: dict[str, Any] = {}

    for info in desc.fields.values():
        value = getattr(self, info.name)
        if _is_default_value(info, value):
            continue  # Omit proto3 zero-values
        result[info.name] = _value_to_dict(info, value)

    return result


def _value_to_dict(info: FieldInfo, value: Any) -> Any:
    """Convert a field value to dict-compatible form."""
    import base64

    if info.kind == FieldKind.MESSAGE:
        return _msg_to_dict(value) if value is not None else None

    if info.kind == FieldKind.ENUM:
        return int(value)

    if info.kind == FieldKind.BYTES:
        return base64.b64encode(value).decode("ascii")

    if info.kind == FieldKind.REPEATED_MESSAGE:
        return [_msg_to_dict(v) for v in value]

    if info.kind == FieldKind.REPEATED_ENUM:
        return [int(v) for v in value]

    if info.kind == FieldKind.REPEATED_BYTES:
        return [base64.b64encode(v).decode("ascii") for v in value]

    if info.kind == FieldKind.MAP:
        assert info.map_marker is not None
        result = {}
        value_base = _get_base_type(info.map_marker.value_type)
        for k, v in value.items():
            dict_key = str(k)  # JSON keys are always strings
            if _is_message_type(value_base):
                result[dict_key] = _msg_to_dict(v)
            elif _is_enum_type(value_base):
                result[dict_key] = int(v)
            elif value_base is bytes:
                result[dict_key] = base64.b64encode(v).decode("ascii")
            else:
                result[dict_key] = v
        return result

    return value


def _msg_from_dict(cls: type, data: dict[str, Any]) -> Any:
    """Create a message instance from a plain dict (recursive).

    Args:
        data: Dictionary with field names as keys.

    Returns:
        Instance of the message class.
    """

    desc: _MessageDescriptor = cls._proto_descriptor
    kwargs: dict[str, Any] = {}

    for info in desc.fields.values():
        if info.name not in data:
            continue
        raw = data[info.name]
        kwargs[info.name] = _value_from_dict(info, raw)

    return cls(**kwargs)


def _value_from_dict(info: FieldInfo, raw: Any) -> Any:
    """Convert a dict value back to the field's Python type."""
    import base64

    if info.kind == FieldKind.MESSAGE:
        assert info.message_type is not None
        if raw is None:
            return None
        return _msg_from_dict(info.message_type, raw)

    if info.kind == FieldKind.ENUM:
        enum_type = info.python_type
        if _is_enum_type(enum_type):
            try:
                return enum_type(raw)
            except ValueError:
                return raw
        return raw

    if info.kind == FieldKind.BYTES:
        if isinstance(raw, str):
            return base64.b64decode(raw)
        return raw

    if info.kind == FieldKind.REPEATED_MESSAGE:
        assert info.message_type is not None
        return [_msg_from_dict(info.message_type, item) for item in raw]

    if info.kind == FieldKind.REPEATED_ENUM:
        inner_base = (
            _get_base_type(info.repeated_marker.item_type)
            if info.repeated_marker
            else None
        )
        if inner_base is not None and _is_enum_type(inner_base):
            result = []
            for item in raw:
                try:
                    result.append(inner_base(item))
                except ValueError:
                    result.append(item)
            return result
        return list(raw)

    if info.kind == FieldKind.REPEATED_BYTES:
        return [
            base64.b64decode(item) if isinstance(item, str) else item for item in raw
        ]

    if info.kind == FieldKind.MAP:
        assert info.map_marker is not None
        key_base = _get_base_type(info.map_marker.key_type)
        value_base = _get_base_type(info.map_marker.value_type)
        result = {}
        for k, v in raw.items():
            # Convert key from string
            if key_base is int:
                dict_key = int(k)
            elif key_base is bool:
                dict_key = k in ("true", "True", "1", True)
            else:
                dict_key = k

            # Convert value
            if _is_message_type(value_base):
                result[dict_key] = _msg_from_dict(value_base, v)
            elif _is_enum_type(value_base):
                try:
                    result[dict_key] = value_base(v)
                except ValueError:
                    result[dict_key] = v
            elif value_base is bytes:
                result[dict_key] = base64.b64decode(v) if isinstance(v, str) else v
            else:
                result[dict_key] = v
        return result

    return raw


def message(cls: type) -> type:
    """Decorator that turns a class into a proto3 message.

    Applies ``@dataclass`` (if not already applied) and injects proto3
    ``serialize()``, ``parse()``, ``to_dict()``, ``from_dict()`` methods.

    Usage::

        @message
        class Person:
            name: str = field(1)
            id: int32 = field(2)

    Args:
        cls: The class to decorate.

    Returns:
        The decorated class with proto3 capabilities.
    """
    # Apply @dataclass if needed
    if not dataclasses.is_dataclass(cls):
        # Set defaults for fields without explicit defaults
        # We need to handle proto3 zero-value defaults
        annotations = get_type_hints(cls, include_extras=True)
        for attr_name, annotation in annotations.items():
            if attr_name.startswith("_"):
                continue
            current = getattr(cls, attr_name, dataclasses.MISSING)
            if isinstance(current, dataclasses.Field):
                # Already a field() — check if it needs a default
                if (
                    current.default is dataclasses.MISSING
                    and current.default_factory is dataclasses.MISSING
                ):
                    # Determine proto3 zero-value default
                    default = _proto3_default(annotation)
                    if isinstance(default, (list, dict)):
                        new_field = dataclasses.field(
                            default_factory=lambda d=default: type(d)(d),
                            metadata=current.metadata,
                        )
                    else:
                        new_field = dataclasses.field(
                            default=default,
                            metadata=current.metadata,
                        )
                    setattr(cls, attr_name, new_field)
            elif current is dataclasses.MISSING:
                # No field() annotation and no default — skip, will be handled
                # by dataclass itself
                pass

        cls = dataclasses.dataclass(cls)

    # Build descriptor
    descriptor = _MessageDescriptor(cls)
    cls._proto_descriptor = descriptor  # type: ignore[attr-defined]

    # Inject methods
    cls.serialize = _msg_serialize  # type: ignore[attr-defined]
    cls.parse = classmethod(_msg_parse)  # type: ignore[attr-defined]
    cls.to_dict = _msg_to_dict  # type: ignore[attr-defined]
    cls.from_dict = classmethod(_msg_from_dict)  # type: ignore[attr-defined]

    # Add _unknown_fields support
    original_init = cls.__init__

    def _new_init(self: Any, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        if not hasattr(self, "_unknown_fields"):
            object.__setattr__(self, "_unknown_fields", [])

    cls.__init__ = _new_init  # type: ignore[attr-defined]

    return cls


def _proto3_default(annotation: Any) -> Any:
    """Determine the proto3 zero-value default for a type annotation."""
    map_marker = _extract_map_field(annotation)
    if map_marker is not None:
        return {}

    rep_marker = _extract_repeated(annotation)
    if rep_marker is not None:
        return []

    base = _get_base_type(annotation)

    if base is str:
        return ""
    if base is bytes:
        return b""
    if base is bool:
        return False
    if base is int:
        return 0
    if base is float:
        return 0.0

    scalar = _extract_proto_scalar(annotation)
    if scalar is not None:
        return _SCALAR_DEFAULTS[scalar.scalar_type]

    if _is_enum_type(base):
        return 0

    # Message type — default to None
    return None


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Decorator
    "message",
    # Field definition
    "field",
    # Scalar type aliases
    "int32",
    "int64",
    "uint32",
    "uint64",
    "sint32",
    "sint64",
    "bool_",
    "fixed32",
    "fixed64",
    "sfixed32",
    "sfixed64",
    "float32",
    "double",
    # Composite type aliases
    "repeated",
    "map_field",
    # Oneof
    "oneof",
    # Wire primitives (exposed for advanced use)
    "WireType",
    "ScalarType",
    "ProtoScalar",
    # Descriptors (exposed for introspection)
    "FieldInfo",
    "FieldKind",
    # Error/marker types
    "Repeated",
    "MapField",
    "OneofGroup",
    # Low-level wire functions
    "encode_varint",
    "decode_varint",
    "zigzag_encode",
    "zigzag_decode",
    "make_tag",
    "decode_tag",
]
