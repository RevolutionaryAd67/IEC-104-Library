"""Encoding helpers for ASDUs and APCI frames."""
from __future__ import annotations

from collections.abc import Callable

from ..apci.control_field import IControlField
from ..apci.frame import build_apci
from ..asdu.types import c_sc_na_1, m_me_nc_1, m_sp_na_1, m_sp_tb_1
from ..asdu.types.common import ASDU, InformationObject
from ..errors import UnsupportedTypeError
from ..spec.constants import CONTROL_FIELD_LENGTH, MAX_APDU_LENGTH, TypeID

TypeEncoder = Callable[[ASDU[InformationObject]], bytes]


def _encode_single_point(asdu: ASDU[InformationObject]) -> bytes:
    if not isinstance(asdu, m_sp_na_1.SinglePointASDU):
        # pragma: no cover - defensive
        raise UnsupportedTypeError("expected SinglePointASDU")
    return m_sp_na_1.encode(asdu)


def _encode_single_point_time(asdu: ASDU[InformationObject]) -> bytes:
    if not isinstance(asdu, m_sp_tb_1.SinglePointTimeASDU):
        # pragma: no cover - defensive
        raise UnsupportedTypeError("expected SinglePointTimeASDU")
    return m_sp_tb_1.encode(asdu)


def _encode_measured_value(asdu: ASDU[InformationObject]) -> bytes:
    if not isinstance(asdu, m_me_nc_1.MeasuredValueASDU):
        # pragma: no cover - defensive
        raise UnsupportedTypeError("expected MeasuredValueASDU")
    return m_me_nc_1.encode(asdu)


def _encode_single_command(asdu: ASDU[InformationObject]) -> bytes:
    if not isinstance(asdu, c_sc_na_1.SingleCommandASDU):
        # pragma: no cover - defensive
        raise UnsupportedTypeError("expected SingleCommandASDU")
    return c_sc_na_1.encode(asdu)


_TYPE_ENCODERS: dict[TypeID, TypeEncoder] = {
    m_sp_na_1.SinglePointASDU.TYPE_ID: _encode_single_point,
    m_sp_tb_1.SinglePointTimeASDU.TYPE_ID: _encode_single_point_time,
    m_me_nc_1.MeasuredValueASDU.TYPE_ID: _encode_measured_value,
    c_sc_na_1.SingleCommandASDU.TYPE_ID: _encode_single_command,
}


def register_type(type_id: TypeID, encoder: TypeEncoder) -> None:
    """Register an additional ASDU encoder."""

    _TYPE_ENCODERS[type_id] = encoder


def encode_asdu(asdu: ASDU[InformationObject]) -> bytes:
    """Encode an ASDU into bytes (header + payload)."""

    encoder = _TYPE_ENCODERS.get(asdu.TYPE_ID)
    if encoder is None:
        raise UnsupportedTypeError(f"no encoder for type {asdu.TYPE_ID}")
    header = asdu.header.encode(with_oa=asdu.header.oa is not None)
    payload = encoder(asdu)
    if len(header) + len(payload) + CONTROL_FIELD_LENGTH > MAX_APDU_LENGTH:
        raise UnsupportedTypeError("ASDU exceeds maximum APDU length")
    return header + payload


def build_i_frame(asdu_bytes: bytes, send_seq: int, recv_seq: int) -> bytes:
    """Wrap ASDU bytes into an I-format APCI frame."""

    control = IControlField(send_seq=send_seq, recv_seq=recv_seq)
    return build_apci(control, asdu_bytes)

