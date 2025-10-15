"""Single command (C_SC_NA_1)."""

from __future__ import annotations

from dataclasses import dataclass

from ...errors import LengthError
from ...spec.constants import TypeID
from ..header import ASDUHeader
from ..ioa import decode_ioa, encode_ioa
from .common import ASDU, InformationObject


@dataclass(slots=True)
class SingleCommand(InformationObject):
    """Single command with select/execute semantics."""

    state: bool
    qualifier: int
    select: bool = False

    def __post_init__(self) -> None:
        if not 0 <= self.qualifier <= 0x3F:
            raise ValueError("qualifier must be between 0 and 0x3F")


@dataclass(slots=True)
class SingleCommandASDU(ASDU[SingleCommand]):
    TYPE_ID = TypeID.C_SC_NA_1


def encode(asdu: SingleCommandASDU) -> bytes:
    header = asdu.header
    if header.sequence:
        raise LengthError("C_SC_NA_1 does not support sequential addressing")
    payload = bytearray()
    for obj in asdu.information_objects:
        payload.extend(encode_ioa(obj.ioa))
        payload.append(_encode_command(obj))
    return bytes(payload)


def decode(header: ASDUHeader, payload: memoryview) -> tuple[SingleCommandASDU, int]:
    if header.sequence:
        raise LengthError("C_SC_NA_1 does not support sequential addressing")
    expected = header.vsq_number * 4
    if len(payload) < expected:
        raise LengthError("payload truncated for C_SC_NA_1")
    objects: list[SingleCommand] = []
    offset = 0
    for _ in range(header.vsq_number):
        ioa = decode_ioa(payload[offset : offset + 3])
        command_byte = int(payload[offset + 3])
        qualifier = (command_byte >> 1) & 0x3F
        select = bool(command_byte & 0x80)
        state = bool(command_byte & 0x01)
        objects.append(
            SingleCommand(ioa=ioa, state=state, qualifier=qualifier, select=select)
        )
        offset += 4
    return (
        SingleCommandASDU(header=header, information_objects=tuple(objects)),
        expected,
    )


def _encode_command(command: SingleCommand) -> int:
    value = (1 if command.state else 0) | ((command.qualifier & 0x3F) << 1)
    if command.select:
        value |= 0x80
    return value

