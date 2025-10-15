"""CP56Time2a time encoding and decoding."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar


@dataclass(slots=True)
class CP56Time2a:
    """Representation of CP56Time2a timestamps."""

    milliseconds: int
    minute: int
    invalid: bool
    hour: int
    summer_time: bool
    day_of_month: int
    day_of_week: int
    month: int
    year: int

    SIZE: ClassVar[int] = 7

    def __post_init__(self) -> None:
        self._validate()

    def to_datetime(self) -> datetime:
        """Convert the representation into a timezone-aware datetime.

        Returns:
            ``datetime`` object in UTC with year offset of 2000.
        """

        year = 2000 + self.year
        seconds, millis = divmod(self.milliseconds, 1000)
        minute = self.minute
        if self.invalid:
            raise ValueError("minute marked invalid in CP56Time2a")
        return datetime(
            year,
            self.month,
            self.day_of_month,
            self.hour,
            minute,
            seconds,
            millis * 1000,
            tzinfo=UTC,
        )

    @classmethod
    def from_datetime(cls, dt: datetime, *, summer_time: bool = False) -> CP56Time2a:
        """Create a CP56Time2a value from a datetime."""

        if dt.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")
        dt_utc = dt.astimezone(UTC)
        milliseconds = dt_utc.second * 1000 + dt_utc.microsecond // 1000
        day_of_week = dt_utc.isoweekday()
        return cls(
            milliseconds=milliseconds,
            minute=dt_utc.minute,
            invalid=False,
            hour=dt_utc.hour,
            summer_time=summer_time,
            day_of_month=dt_utc.day,
            day_of_week=day_of_week,
            month=dt_utc.month,
            year=(dt_utc.year - 2000) % 100,
        )

    def encode(self) -> bytes:
        """Return the 7-byte encoded representation."""

        self._validate()
        buf = bytearray(self.SIZE)
        buf[0] = self.milliseconds & 0xFF
        buf[1] = (self.milliseconds >> 8) & 0xFF
        buf[2] = (self.minute & 0x3F) | (0x80 if self.invalid else 0)
        buf[3] = (self.hour & 0x1F) | (0x80 if self.summer_time else 0)
        buf[4] = ((self.day_of_week & 0x07) << 5) | (self.day_of_month & 0x1F)
        buf[5] = self.month & 0x0F
        buf[6] = self.year & 0x7F
        return bytes(buf)

    @classmethod
    def decode(cls, view: memoryview) -> CP56Time2a:
        """Decode from bytes into a :class:`CP56Time2a` instance."""

        if len(view) < cls.SIZE:
            raise ValueError("insufficient bytes for CP56Time2a")
        millis = int(view[0]) | (int(view[1]) << 8)
        minute_raw = int(view[2])
        hour_raw = int(view[3])
        day_raw = int(view[4])
        month = int(view[5]) & 0x0F
        year = int(view[6]) & 0x7F
        minute = minute_raw & 0x3F
        invalid = (minute_raw & 0x80) != 0
        hour = hour_raw & 0x1F
        summer_time = (hour_raw & 0x80) != 0
        day_of_week = (day_raw >> 5) & 0x07
        day_of_month = day_raw & 0x1F
        instance = cls(
            milliseconds=millis,
            minute=minute,
            invalid=invalid,
            hour=hour,
            summer_time=summer_time,
            day_of_month=day_of_month,
            day_of_week=day_of_week,
            month=month,
            year=year,
        )
        instance._validate()
        return instance

    def _validate(self) -> None:
        if not 0 <= self.milliseconds <= 59999:
            raise ValueError("milliseconds out of range")
        if not 0 <= self.minute <= 59:
            raise ValueError("minute out of range")
        if not 0 <= self.hour <= 23:
            raise ValueError("hour out of range")
        if not 1 <= self.day_of_month <= 31:
            raise ValueError("day of month out of range")
        if not 0 <= self.day_of_week <= 7:
            raise ValueError("day of week out of range")
        if not 1 <= self.month <= 12:
            raise ValueError("month out of range")
        if not 0 <= self.year <= 99:
            raise ValueError("year out of range")

