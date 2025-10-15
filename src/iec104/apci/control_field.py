"""APCI control field handling for IEC 60870-5-104."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..errors import DecodeError, FrameError
from ..utils.bitops import ensure_15bit, pack_seq, unpack_seq


class FrameFormat(str, Enum):
    """Enumeration of APCI frame formats."""

    I_FORMAT = "I"
    S_FORMAT = "S"
    U_FORMAT = "U"


class UFrameType(Enum):
    """Types of U-frames."""

    STARTDT_ACT = 0x07
    STARTDT_CON = 0x0B
    STOPDT_ACT = 0x13
    STOPDT_CON = 0x23
    TESTFR_ACT = 0x43
    TESTFR_CON = 0x83

    @classmethod
    def from_byte(cls, value: int) -> UFrameType:
        try:
            return cls(value)
        except ValueError as exc:
            raise DecodeError(f"unknown U-frame control value: 0x{value:02x}") from exc


@dataclass(slots=True)
class IControlField:
    """Control field for I-frames."""

    send_seq: int
    recv_seq: int

    def encode(self) -> bytes:
        ensure_15bit(self.send_seq)
        ensure_15bit(self.recv_seq)
        s0, s1 = pack_seq(self.send_seq)
        r0, r1 = pack_seq(self.recv_seq)
        return bytes((s0, s1, r0, r1))


@dataclass(slots=True)
class SControlField:
    """Control field for S-frames."""

    recv_seq: int

    def encode(self) -> bytes:
        ensure_15bit(self.recv_seq)
        r0, r1 = pack_seq(self.recv_seq)
        return bytes((0x01, 0x00, r0, r1))


@dataclass(slots=True)
class UControlField:
    """Control field for U-frames."""

    u_type: UFrameType

    def encode(self) -> bytes:
        value = self.u_type.value
        return bytes((value, 0x00, 0x00, 0x00))


ControlField = IControlField | SControlField | UControlField


def decode_control_field(data: bytes | bytearray | memoryview) -> ControlField:
    """Decode a 4-byte control field into a control field object."""

    if len(data) != 4:
        raise FrameError("control field must be 4 bytes")
    b0, b1, b2, b3 = (int(x) for x in bytes(data))
    if b0 & 0x01 == 0 and b1 & 0x01 == 0:
        send = unpack_seq(b0, b1)
        recv = unpack_seq(b2, b3)
        return IControlField(send_seq=send, recv_seq=recv)
    if b0 & 0x03 == 0x01:
        recv = unpack_seq(b2, b3)
        return SControlField(recv_seq=recv)
    if b0 & 0x03 == 0x03:
        u_type = UFrameType.from_byte(b0)
        if b1 or b2 or b3:
            raise DecodeError("U-frame reserved bytes must be zero")
        return UControlField(u_type=u_type)
    raise DecodeError("unknown control field format")


def build_i_control(ns: int, nr: int) -> bytes:
    """Encode an I-format control field."""

    return IControlField(send_seq=ns, recv_seq=nr).encode()


def build_s_control(nr: int) -> bytes:
    """Encode an S-format control field."""

    return SControlField(recv_seq=nr).encode()


def build_u_control(u_type: UFrameType) -> bytes:
    """Encode a U-format control field."""

    return UControlField(u_type=u_type).encode()

