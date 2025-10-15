"""Async timer utilities for IEC 60870-5-104 sessions."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

Callback = Callable[[], Awaitable[None] | None]


class Timer:
    """Simple async timer that triggers a callback after a timeout."""

    def __init__(self, name: str, timeout: float, callback: Callback) -> None:
        self._name = name
        self._timeout = timeout
        self._callback = callback
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        self.cancel()
        if self._timeout <= 0:
            return
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._run())

    def cancel(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def _run(self) -> None:
        try:
            await asyncio.sleep(self._timeout)
            await _maybe_await(self._callback)
        except asyncio.CancelledError:
            return

    @property
    def timeout(self) -> float:
        return self._timeout

    def reschedule(self, timeout: float) -> None:
        self._timeout = timeout
        if self._task is not None:
            self.start()


async def _maybe_await(callback: Callback) -> None:
    result = callback()
    if inspect.isawaitable(result):
        await result


@dataclass(slots=True)
class TimerConfig:
    t0: float
    t1: float
    t2: float
    t3: float

