# /// zerodep
# version = "0.4.3"
# deps = []
# tier = "subsystem"
# category = "data"
# note = "Install/update via: https://zerodep.readthedocs.io/en/latest/guide/cli/"
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
    # Fast-paths for common small values (tags, lengths, small ints)
    if value < 0x80:
        return bytes((value,))
    if value < 0x4000:
        return bytes(((value & 0x7F) | 0x80, value >> 7))
    buf = bytearray()
    while value > 0x7F:
        buf.append((value & 0x7F) | 0x80)
        value >>= 7
    buf.append(value & 0x7F)
    return bytes(buf)


def _write_varint(buf: bytearray, value: int) -> None:
    """Append a varint directly to *buf* (avoids intermediate bytes object)."""
    if value < 0:
        value = value & 0xFFFFFFFFFFFFFFFF
    if value < 0x80:
        buf.append(value)
        return
    if value < 0x4000:
        buf.append((value & 0x7F) | 0x80)
        buf.append(value >> 7)
        return
    while value > 0x7F:
        buf.append((value & 0x7F) | 0x80)
        value >>= 7
    buf.append(value & 0x7F)


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


_TAG_CACHE: dict[tuple[int, int], bytes] = {}


def make_tag(field_number: int, wire_type: int) -> bytes:
    """Pack a field number and wire type into a tag varint.

    Args:
        field_number: Proto field number (1–536870911).
        wire_type: Wire type (0–5).

    Returns:
        Varint-encoded tag bytes.
    """
    key = (field_number, wire_type)
    cached = _TAG_CACHE.get(key)
    if cached is not None:
        return cached
    tag = encode_varint((field_number << 3) | wire_type)
    _TAG_CACHE[key] = tag
    return tag


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

# Buffer-writing scalar encoders: write directly to bytearray (no intermediate bytes)
_SCALAR_BUF_WRITERS: dict[ScalarType, Any] = {
    ScalarType.INT32: lambda buf, v: _write_varint(
        buf, v & 0xFFFFFFFF if v >= 0 else v & 0xFFFFFFFFFFFFFFFF
    ),
    ScalarType.INT64: lambda buf, v: _write_varint(buf, v & 0xFFFFFFFFFFFFFFFF),
    ScalarType.UINT32: lambda buf, v: _write_varint(buf, v & 0xFFFFFFFF),
    ScalarType.UINT64: lambda buf, v: _write_varint(buf, v & 0xFFFFFFFFFFFFFFFF),
    ScalarType.SINT32: lambda buf, v: _write_varint(buf, zigzag_encode(v)),
    ScalarType.SINT64: lambda buf, v: _write_varint(buf, zigzag_encode(v)),
    ScalarType.BOOL: lambda buf, v: buf.append(1 if v else 0),
    ScalarType.FIXED32: lambda buf, v: buf.extend(struct.pack("<I", v & 0xFFFFFFFF)),
    ScalarType.FIXED64: lambda buf, v: buf.extend(struct.pack("<Q", v & 0xFFFFFFFFFFFFFFFF)),
    ScalarType.SFIXED32: lambda buf, v: buf.extend(struct.pack("<i", v)),
    ScalarType.SFIXED64: lambda buf, v: buf.extend(struct.pack("<q", v)),
    ScalarType.FLOAT: lambda buf, v: buf.extend(struct.pack("<f", v)),
    ScalarType.DOUBLE: lambda buf, v: buf.extend(struct.pack("<d", v)),
}


def _decode_int32(d: bytes | bytearray | memoryview, p: int) -> tuple[int, int]:
    v, p = decode_varint(d, p)
    v &= 0xFFFFFFFF
    return (v - 0x100000000 if v >= 0x80000000 else v), p


def _decode_int64(d: bytes | bytearray | memoryview, p: int) -> tuple[int, int]:
    v, p = decode_varint(d, p)
    return (v - 0x10000000000000000 if v >= 0x8000000000000000 else v), p


def _decode_uint32(d: bytes | bytearray | memoryview, p: int) -> tuple[int, int]:
    v, p = decode_varint(d, p)
    return v & 0xFFFFFFFF, p


def _decode_sint32(d: bytes | bytearray | memoryview, p: int) -> tuple[int, int]:
    v, p = decode_varint(d, p)
    return zigzag_decode(v), p


def _decode_bool(d: bytes | bytearray | memoryview, p: int) -> tuple[bool, int]:
    v, p = decode_varint(d, p)
    return bool(v), p


_SCALAR_DECODERS: dict[ScalarType, Any] = {
    ScalarType.INT32: _decode_int32,
    ScalarType.INT64: _decode_int64,
    ScalarType.UINT32: _decode_uint32,
    ScalarType.UINT64: decode_varint,
    ScalarType.SINT32: _decode_sint32,
    ScalarType.SINT64: _decode_sint32,  # same zigzag logic
    ScalarType.BOOL: _decode_bool,
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
    _decoder: Any = None  # cached dispatch handler, set after _FIELD_DECODERS is built
    _encoder: Any = None  # cached encode handler, set after _FIELD_ENCODERS is built
    _is_default: Any = None  # cached default-value check, bound at build time
    _tag: bytes = b""  # cached tag bytes for this field's native wire type
    _len_tag: bytes = b""  # cached tag bytes for LEN wire type (repeated/map)
    _map_meta: Any = None  # cached _MapMeta for MAP fields


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
        self._sorted_fields: list[FieldInfo] = []
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

        # Pre-sort fields by number for deterministic encoding
        self._sorted_fields = sorted(self.fields.values(), key=lambda f: f.number)

    def _bind_handlers(self) -> None:
        """Bind per-field encoder/decoder handlers and cache tags."""
        for info in self.fields.values():
            # Decoder
            handler = _FIELD_DECODERS.get(info.kind)
            if handler is not None:
                object.__setattr__(info, "_decoder", handler)
            # Encoder
            enc = _FIELD_ENCODERS.get(info.kind)
            if enc is not None:
                object.__setattr__(info, "_encoder", enc)
            # Default-value checker
            object.__setattr__(info, "_is_default", _make_is_default(info))
            # Cache tag bytes
            object.__setattr__(
                info, "_tag", make_tag(info.number, info.wire_type)
            )
            object.__setattr__(
                info, "_len_tag", make_tag(info.number, WireType.LEN)
            )
            # Cache map metadata
            if info.kind == FieldKind.MAP and info.map_marker is not None:
                object.__setattr__(info, "_map_meta", _MapMeta(info.map_marker))

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


def _make_is_default(info: FieldInfo) -> Any:
    """Create a specialized default-value checker for *info*."""
    kind = info.kind
    if kind == FieldKind.MAP or kind in (
        FieldKind.REPEATED_SCALAR,
        FieldKind.REPEATED_MESSAGE,
        FieldKind.REPEATED_ENUM,
        FieldKind.REPEATED_STRING,
        FieldKind.REPEATED_BYTES,
    ):
        return lambda v: not v
    if kind == FieldKind.MESSAGE:
        return lambda v: v is None
    if kind == FieldKind.ENUM:
        return lambda v: int(v) == 0
    if kind == FieldKind.STRING:
        return lambda v: not v
    if kind == FieldKind.BYTES:
        return lambda v: not v
    if info.scalar is not None:
        default = _SCALAR_DEFAULTS[info.scalar.scalar_type]
        if isinstance(default, float):
            return lambda v, _d=default: v == _d
        return lambda v, _d=default: v == _d
    return lambda v: False


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
    return _SCALAR_ENCODERS[scalar.scalar_type](value)


def _encode_length_delimited(data: bytes) -> bytes:
    """Wrap bytes with a varint length prefix."""
    return encode_varint(len(data)) + data


def _extend_length_delimited(buf: bytearray, data: bytes | bytearray) -> None:
    """Extend *buf* with a varint length prefix followed by *data*."""
    _write_varint(buf, len(data))
    buf.extend(data)


def _encode_field(buf: bytearray, info: FieldInfo, value: Any) -> None:
    """Encode a single field into *buf* (tag + value)."""
    tag = make_tag(info.number, info.wire_type)

    if info.kind == FieldKind.SCALAR:
        assert info.scalar is not None
        buf.extend(tag)
        buf.extend(_SCALAR_ENCODERS[info.scalar.scalar_type](value))
        return

    if info.kind == FieldKind.ENUM:
        buf.extend(tag)
        buf.extend(encode_varint(int(value) & 0xFFFFFFFFFFFFFFFF))
        return

    if info.kind == FieldKind.STRING:
        buf.extend(tag)
        _extend_length_delimited(buf, value.encode("utf-8"))
        return

    if info.kind == FieldKind.BYTES:
        buf.extend(tag)
        _extend_length_delimited(buf, value)
        return

    if info.kind == FieldKind.MESSAGE:
        buf.extend(tag)
        _extend_length_delimited(buf, _encode_message(value))
        return

    if info.kind == FieldKind.REPEATED_SCALAR:
        _encode_packed_repeated(buf, info, value)
        return

    if info.kind == FieldKind.REPEATED_ENUM:
        _encode_packed_enum(buf, info, value)
        return

    if info.kind == FieldKind.REPEATED_MESSAGE:
        _encode_repeated_messages(buf, info, value)
        return

    if info.kind == FieldKind.REPEATED_STRING:
        _encode_repeated_strings(buf, info, value)
        return

    if info.kind == FieldKind.REPEATED_BYTES:
        _encode_repeated_bytes(buf, info, value)
        return

    if info.kind == FieldKind.MAP:
        _encode_map(buf, info, value)
        return

    raise TypeError(f"Unknown field kind: {info.kind}")  # pragma: no cover


# Batch struct format strings for packed fixed-size scalars
_PACKED_STRUCT_FMT: dict[ScalarType, str] = {
    ScalarType.DOUBLE: "<d",
    ScalarType.FLOAT: "<f",
    ScalarType.FIXED32: "<I",
    ScalarType.FIXED64: "<Q",
    ScalarType.SFIXED32: "<i",
    ScalarType.SFIXED64: "<q",
}


def _encode_packed_repeated(buf: bytearray, info: FieldInfo, values: list[Any]) -> None:
    """Encode a packed repeated scalar field into *buf*."""
    if not values:
        return
    assert info.scalar is not None
    st = info.scalar.scalar_type
    tag = make_tag(info.number, WireType.LEN)
    # Batch encode for fixed-size types
    fmt = _PACKED_STRUCT_FMT.get(st)
    if fmt is not None:
        body = struct.pack(f"<{len(values)}{fmt[1]}", *values)
    else:
        body_buf = bytearray()
        writer = _SCALAR_BUF_WRITERS.get(st)
        if writer is not None:
            for v in values:
                writer(body_buf, v)
        else:
            encoder = _SCALAR_ENCODERS[st]
            for v in values:
                body_buf.extend(encoder(v))
        body = bytes(body_buf)
    buf.extend(tag)
    _extend_length_delimited(buf, body)


def _encode_packed_enum(buf: bytearray, info: FieldInfo, values: list[Any]) -> None:
    """Encode a packed repeated enum field into *buf*."""
    if not values:
        return
    body = bytearray()
    for v in values:
        _write_varint(body, int(v) & 0xFFFFFFFFFFFFFFFF)
    tag = make_tag(info.number, WireType.LEN)
    buf.extend(tag)
    _extend_length_delimited(buf, body)


def _encode_repeated_messages(
    buf: bytearray, info: FieldInfo, values: list[Any]
) -> None:
    """Encode repeated message fields (each length-delimited) into *buf*."""
    tag = make_tag(info.number, WireType.LEN)
    for v in values:
        buf.extend(tag)
        _extend_length_delimited(buf, _encode_message(v))


def _encode_repeated_strings(
    buf: bytearray, info: FieldInfo, values: list[str]
) -> None:
    """Encode repeated string fields (each length-delimited) into *buf*."""
    tag = make_tag(info.number, WireType.LEN)
    for v in values:
        buf.extend(tag)
        _extend_length_delimited(buf, v.encode("utf-8"))


def _encode_repeated_bytes(
    buf: bytearray, info: FieldInfo, values: list[bytes]
) -> None:
    """Encode repeated bytes fields (each length-delimited) into *buf*."""
    tag = make_tag(info.number, WireType.LEN)
    for v in values:
        buf.extend(tag)
        _extend_length_delimited(buf, v)


class _MapMeta:
    """Pre-computed type metadata for a map field (avoids per-entry introspection)."""

    __slots__ = (
        "key_scalar",
        "key_is_string",
        "key_tag",
        "key_buf_writer",
        "value_scalar",
        "value_base",
        "value_is_message",
        "value_is_enum",
        "val_tag",
        "val_buf_writer",
        "default_key",
        "default_value",
    )

    def __init__(self, map_marker: MapField) -> None:
        self.key_scalar = _extract_proto_scalar(
            map_marker.key_type
        ) or _infer_scalar(_get_base_type(map_marker.key_type))
        self.key_is_string = self.key_scalar.scalar_type == ScalarType.STRING
        self.key_tag = make_tag(1, self.key_scalar.wire_type)
        self.key_buf_writer = _SCALAR_BUF_WRITERS.get(self.key_scalar.scalar_type)

        self.value_scalar = _extract_proto_scalar(map_marker.value_type)
        self.value_base = _get_base_type(map_marker.value_type)
        self.value_is_message = _is_message_type(self.value_base)
        self.value_is_enum = _is_enum_type(self.value_base)

        if self.value_is_message:
            self.val_tag = make_tag(2, WireType.LEN)
        elif self.value_is_enum:
            self.val_tag = make_tag(2, WireType.VARINT)
        elif self.value_base is str or self.value_base is bytes:
            self.val_tag = make_tag(2, WireType.LEN)
        elif self.value_scalar is not None:
            self.val_tag = make_tag(2, self.value_scalar.wire_type)
        else:
            self.value_scalar = _infer_scalar(self.value_base)
            self.val_tag = make_tag(2, self.value_scalar.wire_type)

        self.val_buf_writer = (
            _SCALAR_BUF_WRITERS.get(self.value_scalar.scalar_type)
            if self.value_scalar
            else None
        )

        self.default_key = _SCALAR_DEFAULTS.get(self.key_scalar.scalar_type, 0)
        self.default_value = _default_map_value(
            self.value_scalar,
            self.value_base,
            self.value_is_message,
            self.value_is_enum,
        )


def _encode_map(buf: bytearray, info: FieldInfo, mapping: dict[Any, Any]) -> None:
    """Encode a map field as repeated key-value entry messages.

    Each entry is a message with field 1 = key, field 2 = value.
    """
    mm = info._map_meta
    tag = info._len_tag
    key_tag = mm.key_tag
    key_is_string = mm.key_is_string
    key_buf_writer = mm.key_buf_writer
    val_tag = mm.val_tag
    value_is_message = mm.value_is_message
    value_is_enum = mm.value_is_enum
    value_base = mm.value_base
    val_buf_writer = mm.val_buf_writer

    for k, v in mapping.items():
        entry = bytearray()
        # Key: field 1
        entry.extend(key_tag)
        if key_is_string:
            _extend_length_delimited(entry, k.encode("utf-8"))
        else:
            key_buf_writer(entry, k)

        # Value: field 2
        entry.extend(val_tag)
        if value_is_message:
            _extend_length_delimited(entry, _encode_message(v))
        elif value_is_enum:
            _write_varint(entry, int(v) & 0xFFFFFFFFFFFFFFFF)
        elif value_base is str:
            _extend_length_delimited(entry, v.encode("utf-8"))
        elif value_base is bytes:
            _extend_length_delimited(entry, v)
        else:
            val_buf_writer(entry, v)

        buf.extend(tag)
        _extend_length_delimited(buf, entry)


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
    for info in desc._sorted_fields:
        value = getattr(obj, info.name)
        if info._is_default(value):
            continue
        info._encoder(buf, info, value)

    # Append unknown fields
    unknown = getattr(obj, "_unknown_fields", None)
    if unknown:
        for _fn, _wt, raw in unknown:
            buf.extend(make_tag(_fn, _wt))
            if _wt == WireType.LEN:
                _extend_length_delimited(buf, raw)
            else:
                buf.extend(raw)

    return bytes(buf)


# Encoder dispatch table — mirrors _FIELD_DECODERS pattern for encode side.
# Each handler: (buf, info, value) -> None


def _dispatch_encode_scalar(buf: bytearray, info: FieldInfo, value: Any) -> None:
    buf.extend(info._tag)
    _SCALAR_BUF_WRITERS[info.scalar.scalar_type](buf, value)


def _dispatch_encode_enum(buf: bytearray, info: FieldInfo, value: Any) -> None:
    buf.extend(info._tag)
    _write_varint(buf, int(value) & 0xFFFFFFFFFFFFFFFF)


def _dispatch_encode_string(buf: bytearray, info: FieldInfo, value: Any) -> None:
    buf.extend(info._tag)
    _extend_length_delimited(buf, value.encode("utf-8"))


def _dispatch_encode_bytes(buf: bytearray, info: FieldInfo, value: Any) -> None:
    buf.extend(info._tag)
    _extend_length_delimited(buf, value)


def _dispatch_encode_message(buf: bytearray, info: FieldInfo, value: Any) -> None:
    buf.extend(info._tag)
    _extend_length_delimited(buf, _encode_message(value))


def _dispatch_encode_repeated_scalar(
    buf: bytearray, info: FieldInfo, value: Any
) -> None:
    _encode_packed_repeated(buf, info, value)


def _dispatch_encode_repeated_enum(
    buf: bytearray, info: FieldInfo, value: Any
) -> None:
    _encode_packed_enum(buf, info, value)


def _dispatch_encode_repeated_message(
    buf: bytearray, info: FieldInfo, value: Any
) -> None:
    _encode_repeated_messages(buf, info, value)


def _dispatch_encode_repeated_string(
    buf: bytearray, info: FieldInfo, value: Any
) -> None:
    _encode_repeated_strings(buf, info, value)


def _dispatch_encode_repeated_bytes(
    buf: bytearray, info: FieldInfo, value: Any
) -> None:
    _encode_repeated_bytes(buf, info, value)


def _dispatch_encode_map(buf: bytearray, info: FieldInfo, value: Any) -> None:
    _encode_map(buf, info, value)


_FIELD_ENCODERS: dict[FieldKind, Any] = {
    FieldKind.SCALAR: _dispatch_encode_scalar,
    FieldKind.ENUM: _dispatch_encode_enum,
    FieldKind.STRING: _dispatch_encode_string,
    FieldKind.BYTES: _dispatch_encode_bytes,
    FieldKind.MESSAGE: _dispatch_encode_message,
    FieldKind.REPEATED_SCALAR: _dispatch_encode_repeated_scalar,
    FieldKind.REPEATED_ENUM: _dispatch_encode_repeated_enum,
    FieldKind.REPEATED_MESSAGE: _dispatch_encode_repeated_message,
    FieldKind.REPEATED_STRING: _dispatch_encode_repeated_string,
    FieldKind.REPEATED_BYTES: _dispatch_encode_repeated_bytes,
    FieldKind.MAP: _dispatch_encode_map,
}


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


def _decode_string_value(
    data: bytes | bytearray | memoryview, pos: int
) -> tuple[str, int]:
    """Decode a length-prefixed UTF-8 string value."""
    length, pos = decode_varint(data, pos)
    raw_bytes = data[pos : pos + length]
    if isinstance(raw_bytes, memoryview):
        raw_bytes = bytes(raw_bytes)
    return raw_bytes.decode("utf-8"), pos + length


def _decode_bytes_value(
    data: bytes | bytearray | memoryview, pos: int
) -> tuple[bytes, int]:
    """Decode a length-prefixed bytes value."""
    length, pos = decode_varint(data, pos)
    raw_bytes = data[pos : pos + length]
    if isinstance(raw_bytes, memoryview):
        raw_bytes = bytes(raw_bytes)
    return raw_bytes, pos + length


def _decode_enum_value(
    enum_type: type, data: bytes | bytearray | memoryview, pos: int
) -> tuple[Any, int]:
    """Decode a varint and coerce to an enum type."""
    raw, pos = decode_varint(data, pos)
    try:
        return enum_type(raw), pos
    except ValueError:
        return raw, pos


def _decode_map_key(
    key_scalar: ProtoScalar,
    wt: int,
    data: bytes | bytearray | memoryview,
    pos: int,
) -> tuple[Any, int]:
    """Decode a map entry key field."""
    if key_scalar.scalar_type == ScalarType.STRING:
        return _decode_string_value(data, pos)
    return _decode_scalar_from_wire(key_scalar, wt, data, pos)


def _decode_map_value(
    value_scalar: ProtoScalar | None,
    value_base: type,
    value_is_message: bool,
    value_is_enum: bool,
    wt: int,
    data: bytes | bytearray | memoryview,
    pos: int,
) -> tuple[Any, int]:
    """Decode a map entry value field."""
    if value_is_message:
        length, pos = decode_varint(data, pos)
        value = _decode_message_bytes(value_base, data, pos, pos + length)
        return value, pos + length
    if value_is_enum:
        return _decode_enum_value(value_base, data, pos)
    if value_base is str:
        return _decode_string_value(data, pos)
    if value_base is bytes:
        return _decode_bytes_value(data, pos)
    if value_scalar is not None:
        return _decode_scalar_from_wire(value_scalar, wt, data, pos)
    vs = _infer_scalar(value_base)
    return _decode_scalar_from_wire(vs, wt, data, pos)


def _default_map_value(
    value_scalar: ProtoScalar | None,
    value_base: type,
    value_is_message: bool,
    value_is_enum: bool,
) -> Any:
    """Return the proto3 zero-value default for a map value type."""
    if value_is_message:
        return value_base()
    if value_is_enum:
        return 0
    if value_base is str:
        return ""
    if value_base is bytes:
        return b""
    if value_scalar is not None:
        return _SCALAR_DEFAULTS[value_scalar.scalar_type]
    return _SCALAR_DEFAULTS.get(_infer_scalar(value_base).scalar_type, 0)


def _decode_map_entry(
    mm: _MapMeta,
    data: bytes | bytearray | memoryview,
    pos: int,
    end: int,
) -> tuple[Any, Any]:
    """Decode a single map entry message (fields 1=key, 2=value)."""
    key: Any = mm.default_key
    value: Any = None

    while pos < end:
        fn, wt, pos = decode_tag(data, pos)
        if fn == 1:
            key, pos = _decode_map_key(mm.key_scalar, wt, data, pos)
        elif fn == 2:
            value, pos = _decode_map_value(
                mm.value_scalar,
                mm.value_base,
                mm.value_is_message,
                mm.value_is_enum,
                wt,
                data,
                pos,
            )
        else:
            _, pos = _skip_field(wt, data, pos)

    if value is None:
        value = mm.default_value

    return key, value


def _get_repeated_enum_base(info: FieldInfo) -> type | None:
    """Return the inner enum base type for a repeated enum field, or None."""
    if info.repeated_marker is None:
        return None
    inner_base = _get_base_type(info.repeated_marker.item_type)
    if _is_enum_type(inner_base):
        return inner_base
    return None


def _decode_field_scalar(
    info: FieldInfo,
    wire_type: int,
    data: bytes | bytearray | memoryview,
    pos: int,
    values: dict[str, Any],
) -> int:
    """Decode a singular scalar field and store it in *values*."""
    assert info.scalar is not None
    value, pos = _decode_scalar_from_wire(info.scalar, wire_type, data, pos)
    values[info.name] = value
    return pos


def _decode_field_enum(
    info: FieldInfo,
    data: bytes | bytearray | memoryview,
    pos: int,
    values: dict[str, Any],
) -> int:
    """Decode a singular enum field and store it in *values*."""
    enum_type = info.python_type
    if _is_enum_type(enum_type):
        values[info.name], pos = _decode_enum_value(enum_type, data, pos)
    else:
        values[info.name], pos = decode_varint(data, pos)
    return pos


def _decode_field_message(
    info: FieldInfo,
    data: bytes | bytearray | memoryview,
    pos: int,
    values: dict[str, Any],
) -> int:
    """Decode a singular nested message field and store it in *values*."""
    assert info.message_type is not None
    length, pos = decode_varint(data, pos)
    msg = _decode_message_bytes(info.message_type, data, pos, pos + length)
    values[info.name] = msg
    return pos + length


# struct format char and element size for batch-unpackable packed types
_PACKED_UNPACK: dict[ScalarType, tuple[str, int]] = {
    ScalarType.DOUBLE: ("d", 8),
    ScalarType.FLOAT: ("f", 4),
    ScalarType.FIXED32: ("I", 4),
    ScalarType.FIXED64: ("Q", 8),
    ScalarType.SFIXED32: ("i", 4),
    ScalarType.SFIXED64: ("q", 8),
}


def _decode_field_repeated_scalar(
    info: FieldInfo,
    wire_type: int,
    data: bytes | bytearray | memoryview,
    pos: int,
    values: dict[str, Any],
) -> int:
    """Decode a packed (or non-packed) repeated scalar field."""
    assert info.scalar is not None
    if wire_type == WireType.LEN:
        length, pos = decode_varint(data, pos)
        pack_end = pos + length
        st = info.scalar.scalar_type
        batch = _PACKED_UNPACK.get(st)
        if batch is not None:
            # Batch unpack for fixed-size types (doubles, floats, fixed32/64)
            fmt_char, elem_size = batch
            count = length // elem_size
            vals = struct.unpack_from(f"<{count}{fmt_char}", data, pos)
            values[info.name].extend(vals)
            pos = pack_end
        else:
            # Varint-based types: inline the decoder lookup
            decoder = _SCALAR_DECODERS[st]
            lst = values[info.name]
            while pos < pack_end:
                val, pos = decoder(data, pos)
                lst.append(val)
    else:
        val, pos = _decode_scalar_from_wire(info.scalar, wire_type, data, pos)
        values[info.name].append(val)
    return pos


def _decode_field_repeated_enum(
    info: FieldInfo,
    wire_type: int,
    data: bytes | bytearray | memoryview,
    pos: int,
    values: dict[str, Any],
) -> int:
    """Decode a packed (or non-packed) repeated enum field."""
    inner_base = _get_repeated_enum_base(info)
    if wire_type == WireType.LEN:
        length, pos = decode_varint(data, pos)
        pack_end = pos + length
        while pos < pack_end:
            raw_val, pos = decode_varint(data, pos)
            if inner_base is not None:
                try:
                    raw_val = inner_base(raw_val)
                except ValueError:
                    pass
            values[info.name].append(raw_val)
    else:
        raw_val, pos = decode_varint(data, pos)
        if inner_base is not None:
            try:
                raw_val = inner_base(raw_val)
            except ValueError:
                pass
        values[info.name].append(raw_val)
    return pos


def _decode_field_repeated_message(
    info: FieldInfo,
    data: bytes | bytearray | memoryview,
    pos: int,
    values: dict[str, Any],
) -> int:
    """Decode a single element of a repeated message field."""
    assert info.message_type is not None
    length, pos = decode_varint(data, pos)
    msg = _decode_message_bytes(info.message_type, data, pos, pos + length)
    values[info.name].append(msg)
    return pos + length


def _decode_field_string(
    info: FieldInfo,
    data: bytes | bytearray | memoryview,
    pos: int,
    values: dict[str, Any],
) -> int:
    """Decode a singular string field and store it in *values*."""
    val, pos = _decode_string_value(data, pos)
    values[info.name] = val
    return pos


def _decode_field_bytes(
    info: FieldInfo,
    data: bytes | bytearray | memoryview,
    pos: int,
    values: dict[str, Any],
) -> int:
    """Decode a singular bytes field and store it in *values*."""
    val, pos = _decode_bytes_value(data, pos)
    values[info.name] = val
    return pos


def _decode_field_repeated_string(
    info: FieldInfo,
    data: bytes | bytearray | memoryview,
    pos: int,
    values: dict[str, Any],
) -> int:
    """Decode a single element of a repeated string field."""
    val, pos = _decode_string_value(data, pos)
    values[info.name].append(val)
    return pos


def _decode_field_repeated_bytes(
    info: FieldInfo,
    data: bytes | bytearray | memoryview,
    pos: int,
    values: dict[str, Any],
) -> int:
    """Decode a single element of a repeated bytes field."""
    val, pos = _decode_bytes_value(data, pos)
    values[info.name].append(val)
    return pos


def _decode_field_map(
    info: FieldInfo,
    data: bytes | bytearray | memoryview,
    pos: int,
    values: dict[str, Any],
) -> int:
    """Decode a single map entry and store it in *values*."""
    length, pos = decode_varint(data, pos)
    k, v = _decode_map_entry(info._map_meta, data, pos, pos + length)
    values[info.name][k] = v
    return pos + length


def _init_collection_fields(desc: _MessageDescriptor) -> dict[str, Any]:
    """Initialize empty lists/dicts for repeated and map fields."""
    values: dict[str, Any] = {}
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
    return values


def _build_message_instance(
    cls: type,
    desc: _MessageDescriptor,
    values: dict[str, Any],
    unknown_fields: list[tuple[int, int, bytes]],
) -> Any:
    """Construct a message instance from decoded field values."""
    obj = cls.__new__(cls)
    for finfo in desc.fields.values():
        val = values.get(finfo.name, finfo.default_value)
        if val is finfo.default_value and isinstance(val, (list, dict)):
            val = type(val)(val)
        object.__setattr__(obj, finfo.name, val)
    object.__setattr__(obj, "_unknown_fields", unknown_fields)
    return obj


# Dispatch table for _decode_message_bytes field-kind handlers.
# Each handler signature: (info, wire_type, data, pos, values) -> new_pos
# Populated after all handler functions are defined.
def _dispatch_scalar(info: FieldInfo, wt: int, d: Any, p: int, v: dict) -> int:
    return _decode_field_scalar(info, wt, d, p, v)


def _dispatch_enum(info: FieldInfo, wt: int, d: Any, p: int, v: dict) -> int:
    return _decode_field_enum(info, d, p, v)


def _dispatch_string(info: FieldInfo, wt: int, d: Any, p: int, v: dict) -> int:
    return _decode_field_string(info, d, p, v)


def _dispatch_bytes(info: FieldInfo, wt: int, d: Any, p: int, v: dict) -> int:
    return _decode_field_bytes(info, d, p, v)


def _dispatch_message(info: FieldInfo, wt: int, d: Any, p: int, v: dict) -> int:
    return _decode_field_message(info, d, p, v)


def _dispatch_repeated_scalar(info: FieldInfo, wt: int, d: Any, p: int, v: dict) -> int:
    return _decode_field_repeated_scalar(info, wt, d, p, v)


def _dispatch_repeated_enum(info: FieldInfo, wt: int, d: Any, p: int, v: dict) -> int:
    return _decode_field_repeated_enum(info, wt, d, p, v)


def _dispatch_repeated_message(
    info: FieldInfo, wt: int, d: Any, p: int, v: dict
) -> int:
    return _decode_field_repeated_message(info, d, p, v)


def _dispatch_repeated_string(info: FieldInfo, wt: int, d: Any, p: int, v: dict) -> int:
    return _decode_field_repeated_string(info, d, p, v)


def _dispatch_repeated_bytes(info: FieldInfo, wt: int, d: Any, p: int, v: dict) -> int:
    return _decode_field_repeated_bytes(info, d, p, v)


def _dispatch_map(info: FieldInfo, wt: int, d: Any, p: int, v: dict) -> int:
    return _decode_field_map(info, d, p, v)


_FIELD_DECODERS: dict[FieldKind, Any] = {
    FieldKind.SCALAR: _dispatch_scalar,
    FieldKind.ENUM: _dispatch_enum,
    FieldKind.STRING: _dispatch_string,
    FieldKind.BYTES: _dispatch_bytes,
    FieldKind.MESSAGE: _dispatch_message,
    FieldKind.REPEATED_SCALAR: _dispatch_repeated_scalar,
    FieldKind.REPEATED_ENUM: _dispatch_repeated_enum,
    FieldKind.REPEATED_MESSAGE: _dispatch_repeated_message,
    FieldKind.REPEATED_STRING: _dispatch_repeated_string,
    FieldKind.REPEATED_BYTES: _dispatch_repeated_bytes,
    FieldKind.MAP: _dispatch_map,
}


def _decode_message_bytes(
    cls: type,
    data: bytes | bytearray | memoryview,
    pos: int,
    end: int,
) -> Any:
    """Decode a message from a byte range [pos, end)."""
    desc: _MessageDescriptor = cls._proto_descriptor
    values = _init_collection_fields(desc)
    unknown_fields: list[tuple[int, int, bytes]] = []
    fields_by_number = desc.fields_by_number

    while pos < end:
        # Inline 1-byte tag fast-path: field numbers 1-15 fit in 1 byte
        byte = data[pos]
        if byte < 0x80:
            field_number = byte >> 3
            wire_type = byte & 0x07
            pos += 1
        else:
            field_number, wire_type, pos = decode_tag(data, pos)
        info = fields_by_number.get(field_number)

        if info is None:
            raw, pos = _skip_field(wire_type, data, pos)
            unknown_fields.append((field_number, wire_type, raw))
            continue

        pos = info._decoder(info, wire_type, data, pos, values)

    return _build_message_instance(cls, desc, values, unknown_fields)


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
        if info._is_default(value):
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


def _value_from_dict_enum(info: FieldInfo, raw: Any) -> Any:
    """Convert a dict value to an enum field value."""
    enum_type = info.python_type
    if _is_enum_type(enum_type):
        try:
            return enum_type(raw)
        except ValueError:
            return raw
    return raw


def _value_from_dict_repeated_enum(info: FieldInfo, raw: Any) -> list[Any]:
    """Convert a dict list to a repeated enum field value."""
    inner_base = _get_repeated_enum_base(info)
    if inner_base is not None:
        result = []
        for item in raw:
            try:
                result.append(inner_base(item))
            except ValueError:
                result.append(item)
        return result
    return list(raw)


def _convert_map_key(key_base: type, k: Any) -> Any:
    """Convert a JSON string map key back to its Python type."""
    if key_base is int:
        return int(k)
    if key_base is bool:
        return k in ("true", "True", "1", True)
    return k


def _convert_map_value(value_base: type, v: Any) -> Any:
    """Convert a JSON map value back to its Python type."""
    import base64

    if _is_message_type(value_base):
        return _msg_from_dict(value_base, v)
    if _is_enum_type(value_base):
        try:
            return value_base(v)
        except ValueError:
            return v
    if value_base is bytes:
        return base64.b64decode(v) if isinstance(v, str) else v
    return v


def _value_from_dict_map(info: FieldInfo, raw: Any) -> dict[Any, Any]:
    """Convert a dict value to a map field value."""
    assert info.map_marker is not None
    key_base = _get_base_type(info.map_marker.key_type)
    value_base = _get_base_type(info.map_marker.value_type)
    return {
        _convert_map_key(key_base, k): _convert_map_value(value_base, v)
        for k, v in raw.items()
    }


def _value_from_dict(info: FieldInfo, raw: Any) -> Any:
    """Convert a dict value back to the field's Python type."""
    import base64

    if info.kind == FieldKind.MESSAGE:
        assert info.message_type is not None
        return _msg_from_dict(info.message_type, raw) if raw is not None else None

    if info.kind == FieldKind.ENUM:
        return _value_from_dict_enum(info, raw)

    if info.kind == FieldKind.BYTES:
        return base64.b64decode(raw) if isinstance(raw, str) else raw

    if info.kind == FieldKind.REPEATED_MESSAGE:
        assert info.message_type is not None
        return [_msg_from_dict(info.message_type, item) for item in raw]

    if info.kind == FieldKind.REPEATED_ENUM:
        return _value_from_dict_repeated_enum(info, raw)

    if info.kind == FieldKind.REPEATED_BYTES:
        return [
            base64.b64decode(item) if isinstance(item, str) else item for item in raw
        ]

    if info.kind == FieldKind.MAP:
        return _value_from_dict_map(info, raw)

    return raw


def _make_default_field(default: Any, metadata: Any) -> dataclasses.Field:
    """Create a dataclass field with a proto3 zero-value default."""
    if isinstance(default, (list, dict)):
        return dataclasses.field(
            default_factory=lambda d=default: type(d)(d),
            metadata=metadata,
        )
    return dataclasses.field(default=default, metadata=metadata)


def _apply_proto3_defaults(cls: type) -> None:
    """Set proto3 zero-value defaults on class fields that lack them."""
    annotations = get_type_hints(cls, include_extras=True)
    for attr_name, annotation in annotations.items():
        if attr_name.startswith("_"):
            continue
        current = getattr(cls, attr_name, dataclasses.MISSING)
        if not isinstance(current, dataclasses.Field):
            continue
        if (
            current.default is not dataclasses.MISSING
            or current.default_factory is not dataclasses.MISSING
        ):
            continue
        default = _proto3_default(annotation)
        setattr(cls, attr_name, _make_default_field(default, current.metadata))


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
    if not dataclasses.is_dataclass(cls):
        _apply_proto3_defaults(cls)
        cls = dataclasses.dataclass(cls)

    # Build descriptor
    descriptor = _MessageDescriptor(cls)
    descriptor._bind_handlers()
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
