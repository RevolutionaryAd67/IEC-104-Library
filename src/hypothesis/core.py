"""Lightweight property-testing utilities compatible with Hypothesis API."""

from __future__ import annotations

import functools
import inspect
import random
from collections.abc import Callable
from typing import Any

from .strategies import SearchStrategy

DEFAULT_EXAMPLES = 25


def given(
    *strategy_args: SearchStrategy,
    **strategy_kwargs: SearchStrategy,
) -> Callable[[Callable[..., Any]], Callable[..., None]]:
    """Simplified implementation of :func:`hypothesis.given`.

    The decorated test is executed ``DEFAULT_EXAMPLES`` times with values
    sampled from the provided strategies.
    """

    def decorator(test_func: Callable[..., Any]) -> Callable[..., None]:
        @functools.wraps(test_func)
        def wrapper(*args: Any, **kwargs: Any) -> None:
            rnd = random.Random(0)
            for _ in range(DEFAULT_EXAMPLES):
                positional = [strategy.example(rnd) for strategy in strategy_args]
                keyword: dict[str, Any] = {
                    name: strategy.example(rnd)
                    for name, strategy in strategy_kwargs.items()
                }
                test_func(*positional, **keyword)

        wrapper.__signature__ = inspect.Signature()  # type: ignore[attr-defined]
        return wrapper

    return decorator

