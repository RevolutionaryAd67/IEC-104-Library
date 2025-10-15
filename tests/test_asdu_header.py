from __future__ import annotations

import pytest

from iec104.asdu.header import ASDUHeader, parse_asdu_header
from iec104.errors import LengthError
from iec104.spec.constants import CauseOfTransmission, TypeID


def test_header_encode_decode() -> None:
    header = ASDUHeader(
        type_id=TypeID.M_ME_NC_1,
        sequence=False,
        vsq_number=1,
        cause=CauseOfTransmission.SPONTANEOUS,
        negative_confirm=False,
        test=False,
        originator_address=0,
        common_address=5,
        oa=None,
    )
    encoded = header.encode(with_oa=False)
    decoded, consumed = parse_asdu_header(memoryview(encoded))
    assert consumed == len(encoded)
    assert decoded.type_id is TypeID.M_ME_NC_1
    assert decoded.vsq_number == 1
    assert decoded.common_address == 5


def test_header_with_oa() -> None:
    header = ASDUHeader(
        type_id=TypeID.M_SP_NA_1,
        sequence=True,
        vsq_number=3,
        cause=CauseOfTransmission.PERIODIC,
        negative_confirm=True,
        test=True,
        originator_address=0x123,
        common_address=10,
        oa=0x23,
    )
    encoded = header.encode(with_oa=True)
    decoded, consumed = parse_asdu_header(memoryview(encoded), with_oa=True)
    assert decoded.originator_address == 0x123
    assert decoded.oa == 0x23
    assert consumed == len(encoded)


def test_header_invalid_vsq() -> None:
    raw = bytes((int(TypeID.M_SP_NA_1), 0, 0, 0, 0, 0))
    with pytest.raises(LengthError):
        parse_asdu_header(memoryview(raw))

