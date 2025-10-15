from __future__ import annotations

import pytest

from iec104.asdu.header import ASDUHeader
from iec104.asdu.types.c_sc_na_1 import SingleCommand, SingleCommandASDU
from iec104.asdu.types.m_me_nc_1 import MeasuredValueASDU, MeasuredValueFloat
from iec104.asdu.types.m_sp_na_1 import SinglePointASDU, SinglePointInformation
from iec104.asdu.types.m_sp_tb_1 import (
    SinglePointTimeASDU,
    SinglePointWithCP56Time,
)
from iec104.codec.decode import decode_asdu
from iec104.codec.encode import encode_asdu
from iec104.spec.constants import CauseOfTransmission, TypeID
from iec104.spec.time import CP56Time2a


def _header(type_id: TypeID, *, sequence: bool, count: int) -> ASDUHeader:
    return ASDUHeader(
        type_id=type_id,
        sequence=sequence,
        vsq_number=count,
        cause=CauseOfTransmission.SPONTANEOUS,
        negative_confirm=False,
        test=False,
        originator_address=0,
        common_address=1,
        oa=None,
    )


def test_single_point_roundtrip() -> None:
    header = _header(TypeID.M_SP_NA_1, sequence=False, count=1)
    asdu = SinglePointASDU(
        header=header,
        information_objects=(
            SinglePointInformation(ioa=1, value=True, quality=0),
        ),
    )
    encoded = encode_asdu(asdu)
    decoded = decode_asdu(memoryview(encoded))
    assert isinstance(decoded, SinglePointASDU)
    assert decoded.information_objects[0].value is True


def test_single_point_sequence_roundtrip() -> None:
    header = _header(TypeID.M_SP_NA_1, sequence=True, count=3)
    infos = tuple(
        SinglePointInformation(ioa=10 + i, value=bool(i % 2)) for i in range(3)
    )
    asdu = SinglePointASDU(header=header, information_objects=infos)
    encoded = encode_asdu(asdu)
    decoded = decode_asdu(memoryview(encoded))
    assert isinstance(decoded, SinglePointASDU)
    assert [obj.ioa for obj in decoded.information_objects] == [10, 11, 12]


def test_measured_value_roundtrip() -> None:
    header = _header(TypeID.M_ME_NC_1, sequence=False, count=1)
    asdu = MeasuredValueASDU(
        header=header,
        information_objects=(
            MeasuredValueFloat(ioa=5, value=1.5, quality=1),
        ),
    )
    encoded = encode_asdu(asdu)
    decoded = decode_asdu(memoryview(encoded))
    assert isinstance(decoded, MeasuredValueASDU)
    assert decoded.information_objects[0].value == pytest.approx(1.5)


def test_single_point_time_roundtrip() -> None:
    header = _header(TypeID.M_SP_TB_1, sequence=False, count=1)
    ts = CP56Time2a(
        milliseconds=1000,
        minute=1,
        invalid=False,
        hour=2,
        summer_time=False,
        day_of_month=1,
        day_of_week=1,
        month=1,
        year=0,
    )
    asdu = SinglePointTimeASDU(
        header=header,
        information_objects=(
            SinglePointWithCP56Time(ioa=1, value=False, quality=0, timestamp=ts),
        ),
    )
    encoded = encode_asdu(asdu)
    decoded = decode_asdu(memoryview(encoded))
    assert isinstance(decoded, SinglePointTimeASDU)
    assert decoded.information_objects[0].timestamp.milliseconds == 1000


def test_single_command_roundtrip() -> None:
    header = _header(TypeID.C_SC_NA_1, sequence=False, count=1)
    asdu = SingleCommandASDU(
        header=header,
        information_objects=(
            SingleCommand(ioa=1, state=True, qualifier=1, select=True),
        ),
    )
    encoded = encode_asdu(asdu)
    decoded = decode_asdu(memoryview(encoded))
    assert isinstance(decoded, SingleCommandASDU)
    obj = decoded.information_objects[0]
    assert obj.state is True
    assert obj.select is True

