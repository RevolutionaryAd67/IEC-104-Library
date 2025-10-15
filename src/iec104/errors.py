"""Exception hierarchy for the IEC 60870-5-104 stack."""

from __future__ import annotations

from dataclasses import dataclass


class IEC104Error(Exception):
    """Base class for all IEC 60870-5-104 related exceptions."""


class FrameError(IEC104Error):
    """Raised when a frame violates structural constraints."""


class LengthError(FrameError):
    """Raised when lengths encoded in APCI/ASDU are invalid."""


class SequenceError(FrameError):
    """Raised when sequence numbers are inconsistent or overflow windows."""


class TimeoutError(IEC104Error):
    """Raised when a protocol timer expires."""


class UnsupportedTypeError(IEC104Error):
    """Raised when an ASDU type is not registered or implemented."""


class DecodeError(IEC104Error):
    """Raised when decoding of APCI/ASDU data fails."""


@dataclass(slots=True)
class PolicyViolation(IEC104Error):
    """Raised when a security policy prohibits an action."""

    reason: str


class SessionClosedError(IEC104Error):
    """Raised when session operations are attempted on a closed connection."""


class HandshakeError(IEC104Error):
    """Raised when a session handshake fails."""

