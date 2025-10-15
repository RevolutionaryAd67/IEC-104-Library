from __future__ import annotations

import pytest

from iec104.apci.control_field import IControlField, UControlField, UFrameType
from iec104.apci.frame import build_apci, parse_apci
from iec104.errors import LengthError


def test_parse_i_frame() -> None:
    control = IControlField(send_seq=1, recv_seq=2)
    apdu = build_apci(control, b"\x01\x02")
    frame, consumed = parse_apci(memoryview(apdu))
    assert isinstance(frame.control, IControlField)
    assert consumed == len(apdu)
    assert bytes(frame.payload) == b"\x01\x02"


def test_parse_u_frame() -> None:
    control = UControlField(UFrameType.STARTDT_ACT)
    apdu = build_apci(control, b"")
    frame, _ = parse_apci(memoryview(apdu))
    assert isinstance(frame.control, UControlField)


def test_invalid_length() -> None:
    with pytest.raises(LengthError):
        parse_apci(memoryview(b"\x68\x02\x00\x00"))

