from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st
from iec104.spec.time import CP56Time2a


def cp_strategy() -> st.SearchStrategy[CP56Time2a]:
    return st.builds(
        CP56Time2a,
        milliseconds=st.integers(min_value=0, max_value=59999),
        minute=st.integers(min_value=0, max_value=59),
        invalid=st.booleans(),
        hour=st.integers(min_value=0, max_value=23),
        summer_time=st.booleans(),
        day_of_month=st.integers(min_value=1, max_value=28),
        day_of_week=st.integers(min_value=0, max_value=7),
        month=st.integers(min_value=1, max_value=12),
        year=st.integers(min_value=0, max_value=99),
    )


@given(cp_strategy())
def test_cp56time_roundtrip(value: CP56Time2a) -> None:
    encoded = value.encode()
    decoded = CP56Time2a.decode(memoryview(encoded))
    assert decoded.milliseconds == value.milliseconds
    assert decoded.minute == value.minute
    assert decoded.hour == value.hour
    assert decoded.day_of_month == value.day_of_month
    assert decoded.month == value.month
    assert decoded.year == value.year

