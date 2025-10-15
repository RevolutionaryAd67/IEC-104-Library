"""Buffer utilities for streaming decoders."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from ..errors import LengthError


class BoundedBuffer:
    """A byte buffer with an upper capacity to avoid unbounded growth."""

    __slots__ = ("_buffer", "_capacity", "_size")

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._capacity = capacity
        self._buffer: deque[bytes] = deque()
        self._size = 0

    def append(self, data: bytes | bytearray | memoryview) -> None:
        chunk = bytes(data)
        new_size = self._size + len(chunk)
        if new_size > self._capacity:
            raise LengthError(f"buffer capacity exceeded: {new_size}>{self._capacity}")
        if chunk:
            self._buffer.append(chunk)
            self._size = new_size

    def extend(self, chunks: Iterable[bytes | bytearray | memoryview]) -> None:
        for chunk in chunks:
            self.append(chunk)

    def peek(self, size: int) -> bytes:
        if size < 0:
            raise ValueError("size must be non-negative")
        if size > self._size:
            raise LengthError("not enough data available")
        if size == 0:
            return b""
        view = bytearray()
        remaining = size
        for chunk in self._buffer:
            if remaining <= 0:
                break
            to_take = min(len(chunk), remaining)
            view.extend(chunk[:to_take])
            remaining -= to_take
        return bytes(view)

    def consume(self, size: int) -> bytes:
        data = self.peek(size)
        remaining = size
        while remaining and self._buffer:
            chunk = self._buffer.popleft()
            if len(chunk) <= remaining:
                remaining -= len(chunk)
                continue
            tail = chunk[remaining:]
            self._buffer.appendleft(tail)
            remaining = 0
        self._size -= size
        return data

    def __len__(self) -> int:
        return self._size

    @property
    def capacity(self) -> int:
        return self._capacity

