from __future__ import annotations

import pytest

from iec104.apci.control_field import (
    IControlField,
    SControlField,
    UControlField,
    UFrameType,
    build_i_control,
    build_s_control,
    build_u_control,
    decode_control_field,
)
from iec104.errors import DecodeError, FrameError


def test_i_control_roundtrip() -> None:
    field = IControlField(send_seq=5, recv_seq=7)
    encoded = field.encode()
    assert encoded == build_i_control(5, 7)
    decoded = decode_control_field(encoded)
    assert isinstance(decoded, IControlField)
    assert decoded.send_seq == 5
    assert decoded.recv_seq == 7


def test_s_control_roundtrip() -> None:
    field = SControlField(recv_seq=123)
    encoded = field.encode()
    assert encoded == build_s_control(123)
    decoded = decode_control_field(encoded)
    assert isinstance(decoded, SControlField)
    assert decoded.recv_seq == 123


def test_u_control_patterns() -> None:
    for u_type in UFrameType:
        encoded = build_u_control(u_type)
        decoded = decode_control_field(encoded)
        assert isinstance(decoded, UControlField)
        assert decoded.u_type is u_type


def test_control_field_invalid_length() -> None:
    with pytest.raises(FrameError):
        decode_control_field(b"\x00\x00\x00")


def test_u_frame_reserved_bits() -> None:
    with pytest.raises(DecodeError):
        decode_control_field(b"\x07\x01\x00\x00")

