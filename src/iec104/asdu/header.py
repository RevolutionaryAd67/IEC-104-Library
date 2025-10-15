"""ASDU header parsing and encoding."""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import LengthError
from ..spec.constants import IOA_LENGTH, TypeID


@dataclass(slots=True)
class ASDUHeader:
    """Header information preceding the ASDU payload."""

    type_id: TypeID
    sequence: bool
    vsq_number: int
    cause: int
    negative_confirm: bool
    test: bool
    originator_address: int
    common_address: int
    oa: int | None

    def encode(self, *, with_oa: bool) -> bytes:
        if not 1 <= self.vsq_number <= 127:
            raise LengthError("VSQ count must be between 1 and 127")
        vsq = self.vsq_number & 0x7F
        if self.sequence:
            vsq |= 0x80
        cot_low = self.cause & 0x3F
        if self.negative_confirm:
            cot_low |= 0x40
        if self.test:
            cot_low |= 0x80
        cot_high = (self.originator_address >> 8) & 0xFF
        header = bytearray(
            (
                int(self.type_id),
                vsq,
                cot_low,
                cot_high,
            )
        )
        if with_oa:
            if self.oa is None:
                raise LengthError("OA expected but missing")
            header.append(self.oa & 0xFF)
        else:
            if self.oa is not None:
                raise LengthError("OA provided but disabled in configuration")
        header.extend((self.common_address & 0xFF, (self.common_address >> 8) & 0xFF))
        return bytes(header)

    def validate_object_count(self, count: int) -> None:
        if count <= 0:
            raise LengthError("ASDU must carry at least one information object")
        if self.sequence and count != self.vsq_number:
            raise LengthError("Sequential ASDUs must declare exact number of objects")
        if not self.sequence and count != self.vsq_number:
            raise LengthError("VSQ count mismatch")


HEADER_MIN_LEN = 6


def parse_asdu_header(
    data: memoryview, *, with_oa: bool = False
) -> tuple[ASDUHeader, int]:
    """Parse an ASDU header from ``data``.

    Args:
        data: Buffer containing the ASDU header.
        with_oa: Whether an originator address byte is present.

    Returns:
        Tuple of :class:`ASDUHeader` and bytes consumed.
    """

    minimum = 6 + (1 if with_oa else 0)
    if len(data) < minimum:
        raise LengthError("insufficient bytes for ASDU header")
    type_id = TypeID(int(data[0]))
    vsq_raw = int(data[1])
    sequence = bool(vsq_raw & 0x80)
    vsq_number = vsq_raw & 0x7F
    if vsq_number == 0:
        raise LengthError("VSQ number must be >0")
    cot_low = int(data[2])
    cot_high = int(data[3])
    negative = bool(cot_low & 0x40)
    test = bool(cot_low & 0x80)
    cause = cot_low & 0x3F
    originator_high = cot_high
    offset = 4
    oa: int | None
    if with_oa:
        oa = int(data[offset])
        originator = (originator_high << 8) | oa
        offset += 1
    else:
        oa = None
        originator = originator_high << 8
    ca_low = int(data[offset])
    ca_high = int(data[offset + 1])
    common_address = ca_low | (ca_high << 8)
    offset += 2
    header = ASDUHeader(
        type_id=type_id,
        sequence=sequence,
        vsq_number=vsq_number,
        cause=cause,
        negative_confirm=negative,
        test=test,
        originator_address=originator,
        common_address=common_address,
        oa=oa,
    )
    return header, offset


def calculate_information_object_length(
    sequence: bool, number: int, element_size: int
) -> int:
    """Return expected payload size for information objects."""

    if sequence:
        if number < 1:
            raise LengthError("sequential ASDUs require positive number")
        return IOA_LENGTH + number * element_size
    return number * (IOA_LENGTH + element_size)

