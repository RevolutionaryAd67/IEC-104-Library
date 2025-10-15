"""Information Object Address encoding/decoding."""

from __future__ import annotations

from ..errors import LengthError


def encode_ioa(address: int) -> bytes:
    """Encode an information object address."""

    if not 0 <= address < 1 << 24:
        raise LengthError("IOA out of range")
    return bytes((address & 0xFF, (address >> 8) & 0xFF, (address >> 16) & 0xFF))


def decode_ioa(data: memoryview) -> int:
    """Decode an information object address from 3 bytes."""

    if len(data) < 3:
        raise LengthError("insufficient bytes for IOA")
    return int(data[0]) | (int(data[1]) << 8) | (int(data[2]) << 16)

