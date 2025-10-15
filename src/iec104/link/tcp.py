"""Async TCP helpers for IEC 60870-5-104."""

from __future__ import annotations

import asyncio

from ..errors import SessionClosedError
from ..logging import get_logger
from ..typing import ASDUHandler, ASDUType
from .session import (
    IEC104Session,
    SessionParameters,
    create_client_session,
    create_server_session,
)


class IEC104Client:
    """High-level client API for IEC 104."""

    def __init__(self, session: IEC104Session) -> None:
        self._session = session

    @classmethod
    async def connect(
        cls, host: str, port: int, params: SessionParameters | None = None
    ) -> IEC104Client:
        session = await create_client_session(host, port, params)
        return cls(session)

    async def send_asdu(self, asdu: ASDUType) -> None:
        await self._session.send_asdu(asdu)

    async def recv(self) -> ASDUType:
        return await self._session.recv()

    async def close(self) -> None:
        await self._session.close()

    @property
    def session(self) -> IEC104Session:
        return self._session


class IEC104Server:
    """Async server handling multiple IEC 104 sessions."""

    def __init__(
        self,
        host: str,
        port: int,
        handler: ASDUHandler,
        params: SessionParameters | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._handler = handler
        self._params = params or SessionParameters()
        self._server: asyncio.AbstractServer | None = None
        self._logger = get_logger("iec104.server")

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._on_client, self._host, self._port
        )

    async def _on_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        session = await create_server_session(reader, writer, self._params)
        await session.start()
        self._logger.info("client connected", peer=writer.get_extra_info("peername"))
        try:
            while True:
                asdu = await session.recv()
                await self._handler(session, asdu)
        except SessionClosedError:
            self._logger.info("session closed", peer=writer.get_extra_info("peername"))
        finally:
            await session.close()

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

