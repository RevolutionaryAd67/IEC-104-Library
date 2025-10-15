"""Protocol constants and enumerations."""

from __future__ import annotations

from enum import IntEnum
from typing import Final

MAX_APDU_LENGTH: Final[int] = 253
APCI_HEADER_LENGTH: Final[int] = 6
CONTROL_FIELD_LENGTH: Final[int] = 4
IOA_LENGTH: Final[int] = 3
DEFAULT_K_VALUE: Final[int] = 12
DEFAULT_W_VALUE: Final[int] = 8
DEFAULT_T0: Final[float] = 30.0
DEFAULT_T1: Final[float] = 15.0
DEFAULT_T2: Final[float] = 10.0
DEFAULT_T3: Final[float] = 20.0


class TypeID(IntEnum):
    """Supported Type Identifiers."""

    M_SP_NA_1 = 1
    M_ME_NC_1 = 13
    M_SP_TB_1 = 30
    C_SC_NA_1 = 45


class CauseOfTransmission(IntEnum):
    """Cause of transmission codes used within the library."""

    PERIODIC = 1
    BACKGROUND = 2
    SPONTANEOUS = 3
    INITIALIZED = 4
    REQUEST = 5
    ACTIVATION = 6
    ACTIVATION_CONFIRMATION = 7
    DEACTIVATION = 8
    DEACTIVATION_CONFIRMATION = 9
    COMMAND_TERMINATION = 10
    TELECOMMAND = 11
    REMOTE_INDICATION = 20


SUPPORTED_TYPE_IDS: Final[tuple[TypeID, ...]] = (
    TypeID.M_SP_NA_1,
    TypeID.M_ME_NC_1,
    TypeID.M_SP_TB_1,
    TypeID.C_SC_NA_1,
)

