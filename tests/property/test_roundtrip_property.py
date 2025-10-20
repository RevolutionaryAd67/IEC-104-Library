from __future__ import annotations

from collections.abc import Iterable

from hypothesis import given
from hypothesis import strategies as st
from iec104.asdu.header import ASDUHeader
from iec104.asdu.types.c_ic_na_1 import GeneralInterrogation, GeneralInterrogationASDU
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


def _base_header(type_id: TypeID, sequence: bool, count: int) -> ASDUHeader:
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


def _sp_strategy() -> st.SearchStrategy[SinglePointASDU]:
    seq_flag = st.booleans()
    base_ioa = st.integers(min_value=1, max_value=100)
    pairs = st.lists(
        st.tuples(st.booleans(), st.integers(min_value=0, max_value=0x1E)),
        min_size=1,
        max_size=4,
    )

    def build(
        sequence: bool,
        base: int,
        values: Iterable[tuple[bool, int]],
    ) -> SinglePointASDU:
        items = list(values)
        header = _base_header(TypeID.M_SP_NA_1, sequence, len(items))
        objects = tuple(
            SinglePointInformation(
                ioa=base + i if sequence else base + i * 3,
                value=val,
                quality=qual,
            )
            for i, (val, qual) in enumerate(items)
        )
        if sequence:
            objects = tuple(
                SinglePointInformation(
                    ioa=base + i,
                    value=val,
                    quality=qual,
                )
                for i, (val, qual) in enumerate(items)
            )
        return SinglePointASDU(header=header, information_objects=objects)

    return st.builds(build, sequence=seq_flag, base=base_ioa, values=pairs)


def _mv_strategy() -> st.SearchStrategy[MeasuredValueASDU]:
    base_ioa = st.integers(min_value=1, max_value=100)
    values = st.lists(
        st.floats(width=32, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=3,
    )

    def build(base: int, samples: list[float]) -> MeasuredValueASDU:
        header = _base_header(TypeID.M_ME_NC_1, False, len(samples))
        objects = tuple(
            MeasuredValueFloat(
                ioa=base + i,
                value=value,
                quality=i % 5,
            )
            for i, value in enumerate(samples)
        )
        return MeasuredValueASDU(header=header, information_objects=objects)

    return st.builds(build, base=base_ioa, samples=values)


def _spt_strategy() -> st.SearchStrategy[SinglePointTimeASDU]:
    ts = st.builds(
        CP56Time2a,
        milliseconds=st.integers(min_value=0, max_value=59999),
        minute=st.integers(min_value=0, max_value=59),
        invalid=st.just(False),
        hour=st.integers(min_value=0, max_value=23),
        summer_time=st.booleans(),
        day_of_month=st.integers(min_value=1, max_value=28),
        day_of_week=st.integers(min_value=0, max_value=7),
        month=st.integers(min_value=1, max_value=12),
        year=st.integers(min_value=0, max_value=99),
    )
    info = st.builds(
        SinglePointWithCP56Time,
        ioa=st.integers(min_value=1, max_value=100),
        value=st.booleans(),
        quality=st.integers(min_value=0, max_value=0x1E),
        timestamp=ts,
    )
    return st.builds(
        lambda obj: SinglePointTimeASDU(
            header=_base_header(TypeID.M_SP_TB_1, False, 1),
            information_objects=(obj,),
        ),
        obj=info,
    )


def _cmd_strategy() -> st.SearchStrategy[SingleCommandASDU]:
    info = st.builds(
        SingleCommand,
        ioa=st.integers(min_value=1, max_value=100),
        state=st.booleans(),
        qualifier=st.integers(min_value=0, max_value=0x3F),
        select=st.booleans(),
    )
    return st.builds(
        lambda obj: SingleCommandASDU(
            header=_base_header(TypeID.C_SC_NA_1, False, 1),
            information_objects=(obj,),
        ),
        obj=info,
    )


def _gi_strategy() -> st.SearchStrategy[GeneralInterrogationASDU]:
    info = st.builds(
        GeneralInterrogation,
        ioa=st.integers(min_value=0, max_value=2),
        qualifier=st.integers(min_value=0, max_value=0xFF),
    )
    return st.builds(
        lambda obj: GeneralInterrogationASDU(
            header=_base_header(TypeID.C_IC_NA_1, False, 1),
            information_objects=(obj,),
        ),
        obj=info,
    )


ASDU_STRATEGY = st.one_of(
    _sp_strategy(),
    _mv_strategy(),
    _spt_strategy(),
    _cmd_strategy(),
    _gi_strategy(),
)


@given(ASDU_STRATEGY)
def test_asdu_roundtrip(asdu) -> None:
    encoded = encode_asdu(asdu)
    decoded = decode_asdu(memoryview(encoded))
    assert type(decoded) is type(asdu)
    assert len(decoded.information_objects) == len(asdu.information_objects)
    for left, right in zip(
        decoded.information_objects,
        asdu.information_objects,
        strict=True,
    ):
        assert left.ioa == right.ioa

