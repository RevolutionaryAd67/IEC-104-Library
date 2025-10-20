"""Async TCP helpers for IEC 60870-5-104."""

from __future__ import annotations

import asyncio

from ..asdu.header import ASDUHeader
from ..asdu.types.c_ic_na_1 import (
    GeneralInterrogation,
    GeneralInterrogationASDU,
)
from ..errors import IEC104Error, SessionClosedError, TimeoutError as IECTimeoutError
from ..logging import get_logger
from ..spec.constants import CauseOfTransmission, TypeID
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

    async def general_interrogation(
        self,
        *,
        common_address: int,
        qualifier: int = 20,
        originator_address: int = 0,
        oa: int | None = None,
        timeout: float | None = None,
    ) -> list[ASDUType]:
        """Execute a complete general interrogation sequence.

        Args:
            common_address: Target common ASDU address.
            qualifier: Qualifier of interrogation (default 20 = general).
            originator_address: Originator address for the command.
            oa: Optional originator byte if ``SessionParameters.with_oa`` is set.
            timeout: Optional timeout in seconds per receive step.

        Returns:
            List of ASDUs received as interrogation data.

        Raises:
            IEC104Error: If the remote station responds with unexpected data.
            IECTimeoutError: If waiting for responses times out.
        """

        header = ASDUHeader(
            type_id=TypeID.C_IC_NA_1,
            sequence=False,
            vsq_number=1,
            cause=CauseOfTransmission.ACTIVATION,
            negative_confirm=False,
            test=False,
            originator_address=originator_address,
            common_address=common_address,
            oa=oa,
        )
        command = GeneralInterrogationASDU(
            header=header,
            information_objects=(
                GeneralInterrogation(ioa=0, qualifier=qualifier),
            ),
        )
        await self.send_asdu(command)
        await self._await_interrogation_response(
            expected_cause=CauseOfTransmission.ACTIVATION_CONFIRMATION,
            qualifier=qualifier,
            timeout=timeout,
            phase="general interrogation activation confirmation",
        )
        responses: list[ASDUType] = []
        while True:
            asdu = await self._recv_with_timeout(
                timeout, phase="general interrogation data"
            )
            if isinstance(asdu, GeneralInterrogationASDU):
                if asdu.header.cause != CauseOfTransmission.COMMAND_TERMINATION:
                    raise IEC104Error(
                        "unexpected general interrogation ASDU with cause "
                        f"{asdu.header.cause.name}"
                    )
                self._validate_interrogation_asdu(asdu, qualifier)
                break
            responses.append(asdu)
        return responses

    async def _recv_with_timeout(
        self, timeout: float | None, *, phase: str
    ) -> ASDUType:
        try:
            if timeout is None:
                return await self._session.recv()
            return await asyncio.wait_for(self._session.recv(), timeout)
        except asyncio.TimeoutError as exc:  # pragma: no cover - defensive
            raise IECTimeoutError(f"timeout while waiting for {phase}") from exc

    async def _await_interrogation_response(
        self,
        *,
        expected_cause: CauseOfTransmission,
        qualifier: int,
        timeout: float | None,
        phase: str,
    ) -> GeneralInterrogationASDU:
        asdu = await self._recv_with_timeout(timeout, phase=phase)
        if not isinstance(asdu, GeneralInterrogationASDU):
            raise IEC104Error(
                "unexpected ASDU while waiting for general interrogation response"
            )
        if asdu.header.cause != expected_cause:
            raise IEC104Error(
                "unexpected cause of transmission "
                f"{asdu.header.cause.name} during general interrogation"
            )
        self._validate_interrogation_asdu(asdu, qualifier)
        return asdu

    @staticmethod
    def _validate_interrogation_asdu(
        asdu: GeneralInterrogationASDU, qualifier: int
    ) -> None:
        if asdu.header.negative_confirm:
            raise IEC104Error("general interrogation rejected by remote station")
        if not asdu.information_objects:
            raise IEC104Error("general interrogation response missing information")
        obj = asdu.information_objects[0]
        if obj.qualifier != qualifier:
            raise IEC104Error("general interrogation qualifier mismatch")

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

