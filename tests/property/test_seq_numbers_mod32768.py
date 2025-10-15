from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st
from iec104.link.session import seq_increment

MODULO = 32768


@given(st.integers(min_value=0, max_value=MODULO - 1))
def test_sequence_increment_wraps(value: int) -> None:
    nxt = seq_increment(value)
    assert 0 <= nxt < MODULO
    if value == MODULO - 1:
        assert nxt == 0
    else:
        assert nxt == value + 1


@given(
    st.integers(min_value=0, max_value=MODULO - 1),
    st.integers(min_value=0, max_value=MODULO * 2),
)
def test_sequence_multiple_steps(start: int, steps: int) -> None:
    value = start
    for _ in range(steps):
        value = seq_increment(value)
    expected = (start + steps) % MODULO
    assert value == expected

