"""Minimal strategy implementations used in tests."""

from __future__ import annotations

import random
from collections.abc import Sequence
from typing import Any


class SearchStrategy:
    """Base class for simple value generators."""

    def example(self, rnd: random.Random) -> Any:  # pragma: no cover - interface
        raise NotImplementedError


class IntegerStrategy(SearchStrategy):
    def __init__(self, min_value: int, max_value: int) -> None:
        self._min = min_value
        self._max = max_value

    def example(self, rnd: random.Random) -> int:
        return rnd.randint(self._min, self._max)


class BooleanStrategy(SearchStrategy):
    def example(self, rnd: random.Random) -> bool:
        return bool(rnd.getrandbits(1))


class JustStrategy(SearchStrategy):
    def __init__(self, value: Any) -> None:
        self._value = value

    def example(self, rnd: random.Random) -> Any:  # pragma: no cover - deterministic
        return self._value


class FloatStrategy(SearchStrategy):
    def __init__(self, min_value: float, max_value: float) -> None:
        self._min = min_value
        self._max = max_value

    def example(self, rnd: random.Random) -> float:
        return rnd.uniform(self._min, self._max)


class ListStrategy(SearchStrategy):
    def __init__(
        self, element_strategy: SearchStrategy, min_size: int, max_size: int
    ) -> None:
        self._element = element_strategy
        self._min = min_size
        self._max = max_size

    def example(self, rnd: random.Random) -> list[Any]:
        size = rnd.randint(self._min, self._max)
        return [self._element.example(rnd) for _ in range(size)]


class TupleStrategy(SearchStrategy):
    def __init__(self, strategies: Sequence[SearchStrategy]) -> None:
        self._strategies = strategies

    def example(self, rnd: random.Random) -> tuple[Any, ...]:
        return tuple(strategy.example(rnd) for strategy in self._strategies)


class BuildsStrategy(SearchStrategy):
    def __init__(self, constructor: Any, kwargs: dict[str, SearchStrategy]) -> None:
        self._constructor = constructor
        self._kwargs = kwargs

    def example(self, rnd: random.Random) -> Any:
        values = {
            name: strategy.example(rnd) for name, strategy in self._kwargs.items()
        }
        return self._constructor(**values)


class OneOfStrategy(SearchStrategy):
    def __init__(self, strategies: Sequence[SearchStrategy]) -> None:
        self._strategies = strategies

    def example(self, rnd: random.Random) -> Any:
        strategy = rnd.choice(self._strategies)
        return strategy.example(rnd)


def ensure_strategy(value: Any) -> SearchStrategy:
    if isinstance(value, SearchStrategy):
        return value
    return JustStrategy(value)


def integers(*, min_value: int, max_value: int) -> SearchStrategy:
    return IntegerStrategy(min_value, max_value)


def booleans() -> SearchStrategy:
    return BooleanStrategy()


def just(value: Any) -> SearchStrategy:
    return JustStrategy(value)


def floats(
    *, min_value: float = -1_000.0, max_value: float = 1_000.0, **_: Any
) -> SearchStrategy:
    return FloatStrategy(min_value, max_value)


def lists(
    element_strategy: SearchStrategy, *, min_size: int, max_size: int
) -> SearchStrategy:
    return ListStrategy(element_strategy, min_size, max_size)


def tuples(*strategies: SearchStrategy) -> SearchStrategy:
    return TupleStrategy(list(strategies))


def builds(constructor: Any, **kwargs: Any) -> SearchStrategy:
    strategy_kwargs = {name: ensure_strategy(value) for name, value in kwargs.items()}
    return BuildsStrategy(constructor, strategy_kwargs)


def one_of(*strategies: SearchStrategy) -> SearchStrategy:
    return OneOfStrategy(list(strategies))

