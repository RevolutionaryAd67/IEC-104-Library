"""Public typing helpers for IEC 104."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .asdu.header import ASDUHeader
from .asdu.types.common import ASDU, InformationObject

if TYPE_CHECKING:
    from .link.session import IEC104Session


ASDUType = ASDU[InformationObject]


class ASDUFactory(Protocol):
    """Protocol for callables producing ASDUs."""

    def __call__(
        self, header: ASDUHeader, objects: tuple[InformationObject, ...]
    ) -> ASDUType:
        ...


class ASDUHandler(Protocol):
    """Protocol for handler functions used by the server API."""

    async def __call__(self, session: IEC104Session, asdu: ASDUType) -> None:
        ...

