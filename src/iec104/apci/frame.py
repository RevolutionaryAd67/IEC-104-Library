"""APCI frame encoding and decoding."""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import DecodeError, FrameError, LengthError
from ..spec.constants import CONTROL_FIELD_LENGTH, MAX_APDU_LENGTH
from .control_field import ControlField, FrameFormat, decode_control_field

START_BYTE = 0x68


@dataclass(slots=True)
class APCIFrame:
    """Representation of a parsed APCI frame."""

    format: FrameFormat
    control: ControlField
    payload: memoryview

    def encode(self) -> bytes:
        control_bytes = self.control.encode()
        if isinstance(self.payload, memoryview):
            payload = self.payload.tobytes()
        else:
            payload = bytes(self.payload)
        length = len(control_bytes) + len(payload)
        if length > MAX_APDU_LENGTH:
            raise LengthError("APDU length exceeds protocol maximum")
        return bytes((START_BYTE, length)) + control_bytes + payload


def parse_apci(data: memoryview) -> tuple[APCIFrame, int]:
    """Parse an APCI frame from the beginning of ``data``.

    Args:
        data: Buffer containing at least one APCI frame.

    Returns:
        Tuple of parsed :class:`APCIFrame` and number of bytes consumed.
    """

    if len(data) < 2:
        raise LengthError("insufficient data for APCI header")
    if data[0] != START_BYTE:
        raise FrameError("invalid start byte")
    apdu_length = int(data[1])
    if apdu_length < CONTROL_FIELD_LENGTH:
        raise LengthError("APDU length too small for control field")
    total_length = 2 + apdu_length
    if total_length > len(data):
        raise LengthError("incomplete frame in buffer")
    control_slice = data[2 : 2 + CONTROL_FIELD_LENGTH]
    payload_slice = data[2 + CONTROL_FIELD_LENGTH : total_length]
    control = decode_control_field(bytes(control_slice))
    frame_format = _determine_format(control)
    return APCIFrame(frame_format, control, payload_slice), total_length


def _determine_format(control: ControlField) -> FrameFormat:
    if control.__class__.__name__.startswith("I"):
        return FrameFormat.I_FORMAT
    if control.__class__.__name__.startswith("S"):
        return FrameFormat.S_FORMAT
    return FrameFormat.U_FORMAT


def build_apci(control: ControlField, payload: bytes | memoryview = b"") -> bytes:
    """Build a serialized APCI frame from control and payload."""

    payload_view = memoryview(payload)
    frame = APCIFrame(_determine_format(control), control, payload_view)
    return frame.encode()


def expected_frame_length(header: bytes | memoryview) -> int | None:
    """Return the total frame length if determinable from a partial header."""

    view = memoryview(header)
    if len(view) < 2:
        return None
    if view[0] != START_BYTE:
        raise DecodeError("invalid start byte in stream")
    length = int(view[1])
    if length < CONTROL_FIELD_LENGTH:
        raise LengthError("invalid APDU length in header")
    return 2 + length

