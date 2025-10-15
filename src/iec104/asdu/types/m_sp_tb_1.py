"""Single point with CP56Time2a timestamp (M_SP_TB_1)."""

from __future__ import annotations

from dataclasses import dataclass

from ...errors import LengthError
from ...spec.constants import TypeID
from ...spec.time import CP56Time2a
from ..header import ASDUHeader
from ..ioa import decode_ioa, encode_ioa
from .common import ASDU, InformationObject


@dataclass(slots=True)
class SinglePointWithCP56Time(InformationObject):
    """Single point value with timestamp."""

    value: bool
    quality: int
    timestamp: CP56Time2a

    def __post_init__(self) -> None:
        if not 0 <= self.quality <= 0x1E:
            raise ValueError("quality must be between 0 and 0x1E")


@dataclass(slots=True)
class SinglePointTimeASDU(ASDU[SinglePointWithCP56Time]):
    TYPE_ID = TypeID.M_SP_TB_1


def encode(asdu: SinglePointTimeASDU) -> bytes:
    header = asdu.header
    if header.sequence:
        raise LengthError("M_SP_TB_1 does not support sequential addressing")
    payload = bytearray()
    for obj in asdu.information_objects:
        payload.extend(encode_ioa(obj.ioa))
        payload.append((1 if obj.value else 0) | (obj.quality & 0x1E))
        payload.extend(obj.timestamp.encode())
    return bytes(payload)


def decode(header: ASDUHeader, payload: memoryview) -> tuple[SinglePointTimeASDU, int]:
    if header.sequence:
        raise LengthError("M_SP_TB_1 does not support sequential addressing")
    object_size = 1 + CP56Time2a.SIZE
    expected = header.vsq_number * (3 + object_size)
    if len(payload) < expected:
        raise LengthError("payload truncated for M_SP_TB_1")
    objects: list[SinglePointWithCP56Time] = []
    offset = 0
    for _ in range(header.vsq_number):
        ioa = decode_ioa(payload[offset : offset + 3])
        value_byte = int(payload[offset + 3])
        timestamp = CP56Time2a.decode(
            payload[offset + 4 : offset + 4 + CP56Time2a.SIZE]
        )
        offset += 3 + object_size
        objects.append(
            SinglePointWithCP56Time(
                ioa=ioa,
                value=bool(value_byte & 0x01),
                quality=value_byte & 0x1E,
                timestamp=timestamp,
            )
        )
    return (
        SinglePointTimeASDU(header=header, information_objects=tuple(objects)),
        expected,
    )

