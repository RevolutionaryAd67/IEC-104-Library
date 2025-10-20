"""General interrogation command (C_IC_NA_1)."""

from __future__ import annotations

from dataclasses import dataclass

from ...errors import LengthError
from ...spec.constants import TypeID
from ..header import ASDUHeader
from ..ioa import decode_ioa, encode_ioa
from .common import ASDU, InformationObject


@dataclass(slots=True)
class GeneralInterrogation(InformationObject):
    """Information object carrying the qualifier of interrogation."""

    qualifier: int

    def __post_init__(self) -> None:
        if not 0 <= self.qualifier <= 0xFF:
            raise ValueError("qualifier must be between 0 and 0xFF")


@dataclass(slots=True)
class GeneralInterrogationASDU(ASDU[GeneralInterrogation]):
    TYPE_ID = TypeID.C_IC_NA_1


def encode(asdu: GeneralInterrogationASDU) -> bytes:
    header = asdu.header
    if header.sequence:
        raise LengthError("C_IC_NA_1 does not support sequential addressing")
    payload = bytearray()
    for obj in asdu.information_objects:
        payload.extend(encode_ioa(obj.ioa))
        payload.append(obj.qualifier & 0xFF)
    return bytes(payload)


def decode(
    header: ASDUHeader, payload: memoryview
) -> tuple[GeneralInterrogationASDU, int]:
    if header.sequence:
        raise LengthError("C_IC_NA_1 does not support sequential addressing")
    expected = header.vsq_number * 4
    if len(payload) < expected:
        raise LengthError("payload truncated for C_IC_NA_1")
    objects: list[GeneralInterrogation] = []
    offset = 0
    for _ in range(header.vsq_number):
        ioa = decode_ioa(payload[offset : offset + 3])
        qualifier = int(payload[offset + 3])
        objects.append(GeneralInterrogation(ioa=ioa, qualifier=qualifier))
        offset += 4
    return (
        GeneralInterrogationASDU(header=header, information_objects=tuple(objects)),
        expected,
    )
