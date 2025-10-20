from __future__ import annotations

import asyncio

import pytest

from iec104.asdu.header import ASDUHeader
from iec104.asdu.types.c_ic_na_1 import GeneralInterrogation, GeneralInterrogationASDU
from iec104.asdu.types.m_sp_na_1 import SinglePointASDU, SinglePointInformation
from iec104.errors import IEC104Error
from iec104.link.tcp import IEC104Client
from iec104.spec.constants import CauseOfTransmission, TypeID


class DummySession:
    def __init__(self) -> None:
        self.sent: list[object] = []
        self._queue: asyncio.Queue[object] = asyncio.Queue()

    async def send_asdu(self, asdu: object) -> None:
        self.sent.append(asdu)

    async def recv(self) -> object:
        return await self._queue.get()

    async def close(self) -> None:  # pragma: no cover - dummy implementation
        return None

    def push(self, asdu: object) -> None:
        self._queue.put_nowait(asdu)


def _gi_asdu(cause: CauseOfTransmission, qualifier: int) -> GeneralInterrogationASDU:
    header = ASDUHeader(
        type_id=TypeID.C_IC_NA_1,
        sequence=False,
        vsq_number=1,
        cause=cause,
        negative_confirm=False,
        test=False,
        originator_address=0,
        common_address=1,
        oa=None,
    )
    return GeneralInterrogationASDU(
        header=header,
        information_objects=(GeneralInterrogation(ioa=0, qualifier=qualifier),),
    )


def _single_point_asdu() -> SinglePointASDU:
    header = ASDUHeader(
        type_id=TypeID.M_SP_NA_1,
        sequence=False,
        vsq_number=1,
        cause=CauseOfTransmission.REMOTE_INDICATION,
        negative_confirm=False,
        test=False,
        originator_address=0,
        common_address=1,
        oa=None,
    )
    info = SinglePointInformation(ioa=1, value=True, quality=0)
    return SinglePointASDU(header=header, information_objects=(info,))


def test_general_interrogation_collects_data() -> None:
    async def scenario() -> tuple[list[SinglePointASDU], list[object], SinglePointASDU]:
        session = DummySession()
        client = IEC104Client(session)
        qualifier = 20
        confirm = _gi_asdu(CauseOfTransmission.ACTIVATION_CONFIRMATION, qualifier)
        data = _single_point_asdu()
        termination = _gi_asdu(CauseOfTransmission.COMMAND_TERMINATION, qualifier)
        session.push(confirm)
        session.push(data)
        session.push(termination)

        responses = await client.general_interrogation(
            common_address=1, qualifier=qualifier
        )
        return responses, session.sent, data

    responses, sent, data = asyncio.run(scenario())

    assert responses == [data]
    first = sent[0]
    assert isinstance(first, GeneralInterrogationASDU)
    assert first.header.cause == CauseOfTransmission.ACTIVATION


def test_general_interrogation_raises_on_unexpected_asdu() -> None:
    async def scenario() -> None:
        session = DummySession()
        client = IEC104Client(session)
        session.push(_single_point_asdu())
        await client.general_interrogation(common_address=1)

    with pytest.raises(IEC104Error):
        asyncio.run(scenario())
