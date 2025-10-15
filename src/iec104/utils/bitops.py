"""Bit-level helpers for APCI and ASDU processing."""

from __future__ import annotations

from typing import Final

LSB_MASK: Final[int] = 0x01


def ensure_15bit(value: int) -> int:
    """Validate that ``value`` fits into a 15-bit sequence number."""

    if not 0 <= value < 1 << 15:
        raise ValueError(f"sequence number out of range: {value}")
    return value


def pack_seq(value: int) -> tuple[int, int]:
    """Pack a 15-bit value into two bytes with the IEC104 LSB=0 pattern."""

    ensure_15bit(value)
    low = (value << 1) & 0xFE
    high = (value >> 7) & 0xFE
    return low, high


def unpack_seq(low: int, high: int) -> int:
    """Unpack a 15-bit sequence number from two APCI bytes."""

    if low & LSB_MASK or high & LSB_MASK:
        raise ValueError("sequence bytes must have LSB cleared")
    value = ((high & 0xFE) << 7) | ((low & 0xFE) >> 1)
    return value & 0x7FFF


def is_bit_set(value: int, bit: int) -> bool:
    """Return whether ``bit`` is set in ``value``."""

    return (value & (1 << bit)) != 0


def set_bit(value: int, bit: int, enabled: bool) -> int:
    """Set or clear a bit and return the new value."""

    mask = 1 << bit
    return (value | mask) if enabled else (value & ~mask)

