"""Decoding helpers for APCI and ASDUs."""

from __future__ import annotations

from collections.abc import Callable

from ..apci.control_field import FrameFormat
from ..apci.frame import APCIFrame, expected_frame_length, parse_apci
from ..asdu.header import ASDUHeader, parse_asdu_header
from ..asdu.types import c_sc_na_1, m_me_nc_1, m_sp_na_1, m_sp_tb_1
from ..asdu.types.common import ASDU, InformationObject
from ..errors import UnsupportedTypeError
from ..spec.constants import MAX_APDU_LENGTH, TypeID
from ..utils.buffers import BoundedBuffer

ASDUDecodeResult = tuple[ASDU[InformationObject], int]
TypeDecoder = Callable[[ASDUHeader, memoryview], ASDUDecodeResult]


def _decode_single_point(
    header: ASDUHeader, payload: memoryview
) -> ASDUDecodeResult:
    asdu, consumed = m_sp_na_1.decode(header, payload)
    return asdu, consumed


def _decode_single_point_time(
    header: ASDUHeader, payload: memoryview
) -> ASDUDecodeResult:
    asdu, consumed = m_sp_tb_1.decode(header, payload)
    return asdu, consumed


def _decode_measured_value(
    header: ASDUHeader, payload: memoryview
) -> ASDUDecodeResult:
    asdu, consumed = m_me_nc_1.decode(header, payload)
    return asdu, consumed


def _decode_single_command(
    header: ASDUHeader, payload: memoryview
) -> ASDUDecodeResult:
    asdu, consumed = c_sc_na_1.decode(header, payload)
    return asdu, consumed


_TYPE_DECODERS: dict[TypeID, TypeDecoder] = {
    m_sp_na_1.SinglePointASDU.TYPE_ID: _decode_single_point,
    m_sp_tb_1.SinglePointTimeASDU.TYPE_ID: _decode_single_point_time,
    m_me_nc_1.MeasuredValueASDU.TYPE_ID: _decode_measured_value,
    c_sc_na_1.SingleCommandASDU.TYPE_ID: _decode_single_command,
}


def register_type(type_id: TypeID, decoder: TypeDecoder) -> None:
    """Register a decoder for an additional type identifier."""

    _TYPE_DECODERS[type_id] = decoder


def decode_asdu_with_length(
    view: memoryview, *, with_oa: bool = False
) -> tuple[ASDU[InformationObject], int]:
    """Decode an ASDU from the provided bytes returning consumed length."""

    header, header_size = parse_asdu_header(view, with_oa=with_oa)
    decoder = _TYPE_DECODERS.get(header.type_id)
    if decoder is None:
        raise UnsupportedTypeError(f"no decoder for type {header.type_id}")
    asdu, consumed = decoder(header, view[header_size:])
    return asdu, header_size + consumed


def decode_asdu(view: memoryview, *, with_oa: bool = False) -> ASDU[InformationObject]:
    """Decode an ASDU from bytes."""

    asdu, _ = decode_asdu_with_length(view, with_oa=with_oa)
    return asdu


def decode_apdu(
    data: bytes, *, with_oa: bool = False
) -> tuple[APCIFrame, ASDU[InformationObject] | None, int]:
    """Decode a single APDU and optionally the contained ASDU."""

    frame, consumed = parse_apci(memoryview(data))
    asdu: ASDU[InformationObject] | None = None
    if frame.format == FrameFormat.I_FORMAT:
        asdu = decode_asdu(frame.payload, with_oa=with_oa)
    return frame, asdu, consumed


class StreamingAPDUDecoder:
    """Streaming decoder accumulating bytes until complete frames are available."""

    def __init__(
        self, *, capacity: int = MAX_APDU_LENGTH * 2, with_oa: bool = False
    ) -> None:
        self._buffer = BoundedBuffer(capacity)
        self._with_oa = with_oa

    def feed(
        self, data: bytes | bytearray | memoryview
    ) -> list[tuple[APCIFrame, ASDU[InformationObject] | None]]:
        """Feed bytes into the decoder and return all complete frames."""

        self._buffer.append(data)
        frames: list[tuple[APCIFrame, ASDU[InformationObject] | None]] = []
        while True:
            if len(self._buffer) < 2:
                break
            header_bytes = self._buffer.peek(2)
            total_length = expected_frame_length(header_bytes)
            if total_length is None or len(self._buffer) < total_length:
                break
            frame_bytes = self._buffer.consume(total_length)
            frame, _ = parse_apci(memoryview(frame_bytes))
            asdu: ASDU[InformationObject] | None = None
            if frame.format == FrameFormat.I_FORMAT:
                asdu = decode_asdu(frame.payload, with_oa=self._with_oa)
            frames.append((frame, asdu))
        return frames

    def clear(self) -> None:
        """Remove all buffered bytes."""

        self._buffer = BoundedBuffer(self._buffer.capacity)

