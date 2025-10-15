"""Common abstractions for ASDU types."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar, Generic, TypeVar

from ...spec.constants import TypeID
from ..header import ASDUHeader


@dataclass(slots=True)
class InformationObject:
    """Base class for information objects."""

    ioa: int


IO = TypeVar("IO", bound=InformationObject, covariant=True)


@dataclass(slots=True)
class ASDU(Generic[IO]):
    """Generic ASDU carrying information objects."""

    header: ASDUHeader
    information_objects: tuple[IO, ...]
    TYPE_ID: ClassVar[TypeID]

    def __post_init__(self) -> None:
        self.header.validate_object_count(len(self.information_objects))


def ensure_sequence_length(sequence: Sequence[object], expected: int) -> None:
    """Ensure the sequence length matches ``expected``."""

    if len(sequence) != expected:
        raise ValueError("sequence length mismatch")

