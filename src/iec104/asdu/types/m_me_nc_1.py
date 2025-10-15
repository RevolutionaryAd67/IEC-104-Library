"""Measured value, short floating point (M_ME_NC_1)."""

from __future__ import annotations

from dataclasses import dataclass
from struct import pack, unpack_from

from ...errors import LengthError
from ...spec.constants import TypeID
from ..header import ASDUHeader, calculate_information_object_length
from ..ioa import decode_ioa, encode_ioa
from .common import ASDU, InformationObject


@dataclass(slots=True)
class MeasuredValueFloat(InformationObject):
    """Measured value with quality descriptor."""

    value: float
    quality: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.quality <= 0x1F:
            raise ValueError("quality must be between 0 and 0x1F")


@dataclass(slots=True)
class MeasuredValueASDU(ASDU[MeasuredValueFloat]):
    TYPE_ID = TypeID.M_ME_NC_1


def encode(asdu: MeasuredValueASDU) -> bytes:
    header = asdu.header
    objects = asdu.information_objects
    header.validate_object_count(len(objects))
    payload = bytearray()
    if header.sequence:
        base = objects[0].ioa
        for index, obj in enumerate(objects):
            if obj.ioa != base + index:
                raise LengthError("sequential ASDUs must have consecutive IOAs")
            payload.extend(pack("<f", obj.value))
            payload.append(obj.quality & 0x1F)
        payload = bytearray(encode_ioa(base)) + payload
    else:
        for obj in objects:
            payload.extend(encode_ioa(obj.ioa))
            payload.extend(pack("<f", obj.value))
            payload.append(obj.quality & 0x1F)
    return bytes(payload)


def decode(header: ASDUHeader, payload: memoryview) -> tuple[MeasuredValueASDU, int]:
    element_size = 5
    expected = calculate_information_object_length(
        header.sequence, header.vsq_number, element_size
    )
    if len(payload) < expected:
        raise LengthError("payload truncated for M_ME_NC_1")
    objects: list[MeasuredValueFloat] = []
    offset = 0
    if header.sequence:
        base = decode_ioa(payload[offset : offset + 3])
        offset += 3
        for i in range(header.vsq_number):
            value = float(unpack_from("<f", payload, offset)[0])
            quality = int(payload[offset + 4]) & 0x1F
            offset += element_size
            objects.append(
                MeasuredValueFloat(ioa=base + i, value=value, quality=quality)
            )
    else:
        for _ in range(header.vsq_number):
            ioa = decode_ioa(payload[offset : offset + 3])
            value = float(unpack_from("<f", payload, offset + 3)[0])
            quality = int(payload[offset + 7]) & 0x1F
            offset += 3 + element_size
            objects.append(
                MeasuredValueFloat(ioa=ioa, value=value, quality=quality)
            )
    return (
        MeasuredValueASDU(header=header, information_objects=tuple(objects)),
        expected,
    )

