"""Security policy hooks for IEC 104 deployments."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from ..errors import PolicyViolation


class ConnectionPolicy(Protocol):
    """Protocol for connection admission policies."""

    async def allow(self, peername: tuple[str, int]) -> bool:
        """Return ``True`` if the peer is allowed to connect."""


@dataclass(slots=True)
class NullPolicy(ConnectionPolicy):
    """Policy that allows all connections."""

    async def allow(self, peername: tuple[str, int]) -> bool:
        # pragma: no cover - trivial
        return True


@dataclass(slots=True)
class IPAllowlistPolicy(ConnectionPolicy):
    """Simple allowlist policy for source IP addresses."""

    allowed: frozenset[str]

    def __init__(self, allowed: Iterable[str]) -> None:
        self.allowed = frozenset(allowed)

    async def allow(self, peername: tuple[str, int]) -> bool:
        host, _port = peername
        return host in self.allowed


async def enforce(policy: ConnectionPolicy, peername: tuple[str, int]) -> None:
    """Raise :class:`PolicyViolation` if the connection is not allowed."""

    if not await policy.allow(peername):
        raise PolicyViolation(f"connection from {peername[0]} denied by policy")

