from __future__ import annotations

from datetime import UTC, datetime

import pytest

from iec104.spec.time import CP56Time2a


def test_encode_decode_roundtrip() -> None:
    dt = datetime(2024, 1, 2, 3, 4, 5, 123000, tzinfo=UTC)
    cp = CP56Time2a.from_datetime(dt)
    encoded = cp.encode()
    decoded = CP56Time2a.decode(memoryview(encoded))
    assert decoded.to_datetime() == dt


def test_invalid_range() -> None:
    with pytest.raises(ValueError):
        CP56Time2a(
            milliseconds=70000,
            minute=0,
            invalid=False,
            hour=0,
            summer_time=False,
            day_of_month=1,
            day_of_week=1,
            month=1,
            year=0,
        )

