"""Single point information without timestamp (M_SP_NA_1)."""

from __future__ import annotations

from dataclasses import dataclass

from ...errors import LengthError
from ...spec.constants import TypeID
from ..header import ASDUHeader, calculate_information_object_length
from ..ioa import decode_ioa, encode_ioa
from .common import ASDU, InformationObject


@dataclass(slots=True)
class SinglePointInformation(InformationObject):
    """Single point value with quality flags."""

    value: bool
    quality: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.quality <= 0x1E:
            raise ValueError("quality must be between 0 and 0x1E")


@dataclass(slots=True)
class SinglePointASDU(ASDU[SinglePointInformation]):
    """ASDU carrying :class:`SinglePointInformation`."""

    TYPE_ID = TypeID.M_SP_NA_1


def encode(asdu: SinglePointASDU) -> bytes:
    header = asdu.header
    objects = asdu.information_objects
    header.validate_object_count(len(objects))
    payload = bytearray()
    if header.sequence:
        base = objects[0].ioa
        for index, obj in enumerate(objects):
            if obj.ioa != base + index:
                raise LengthError("sequential ASDUs must have consecutive IOAs")
            payload.append(_encode_value(obj.value, obj.quality))
        payload = bytearray(encode_ioa(base)) + payload
    else:
        for obj in objects:
            payload.extend(encode_ioa(obj.ioa))
            payload.append(_encode_value(obj.value, obj.quality))
    return bytes(payload)


def decode(header: ASDUHeader, payload: memoryview) -> tuple[SinglePointASDU, int]:
    expected = calculate_information_object_length(
        header.sequence, header.vsq_number, 1
    )
    if len(payload) < expected:
        raise LengthError("payload truncated for M_SP_NA_1")
    objects: list[SinglePointInformation] = []
    offset = 0
    if header.sequence:
        base_ioa = decode_ioa(payload[offset : offset + 3])
        offset += 3
        for i in range(header.vsq_number):
            value_byte = int(payload[offset])
            offset += 1
            objects.append(
                SinglePointInformation(
                    ioa=base_ioa + i,
                    value=bool(value_byte & 0x01),
                    quality=value_byte & 0x1E,
                )
            )
    else:
        for _ in range(header.vsq_number):
            ioa = decode_ioa(payload[offset : offset + 3])
            value_byte = int(payload[offset + 3])
            offset += 4
            objects.append(
                SinglePointInformation(
                    ioa=ioa,
                    value=bool(value_byte & 0x01),
                    quality=value_byte & 0x1E,
                )
            )
    return (
        SinglePointASDU(header=header, information_objects=tuple(objects)),
        expected,
    )


def _encode_value(value: bool, quality: int) -> int:
    if not 0 <= quality <= 0x1E:
        raise ValueError("quality out of range")
    return (1 if value else 0) | (quality & 0x1E)

