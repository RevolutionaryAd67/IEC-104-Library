from __future__ import annotations

from iec104.asdu.header import ASDUHeader
from iec104.asdu.types.m_sp_na_1 import SinglePointASDU, SinglePointInformation
from iec104.codec.decode import StreamingAPDUDecoder
from iec104.codec.encode import build_i_frame, encode_asdu
from iec104.spec.constants import CauseOfTransmission, TypeID


def _make_asdu(ioa: int) -> SinglePointASDU:
    header = ASDUHeader(
        type_id=TypeID.M_SP_NA_1,
        sequence=False,
        vsq_number=1,
        cause=CauseOfTransmission.SPONTANEOUS,
        negative_confirm=False,
        test=False,
        originator_address=0,
        common_address=1,
        oa=None,
    )
    return SinglePointASDU(
        header=header,
        information_objects=(SinglePointInformation(ioa=ioa, value=True),),
    )


def test_streaming_decoder_handles_chunks() -> None:
    decoder = StreamingAPDUDecoder()
    frame1 = build_i_frame(encode_asdu(_make_asdu(1)), 0, 0)
    frame2 = build_i_frame(encode_asdu(_make_asdu(2)), 1, 0)
    data = frame1 + frame2
    outputs = []
    for size in range(1, len(data)):
        decoder.clear()
        outputs.clear()
        for offset in range(0, len(data), size):
            chunk = data[offset : offset + size]
            outputs.extend(decoder.feed(chunk))
        assert len(outputs) == 2
        assert outputs[0][1].information_objects[0].ioa == 1
        assert outputs[1][1].information_objects[0].ioa == 2

