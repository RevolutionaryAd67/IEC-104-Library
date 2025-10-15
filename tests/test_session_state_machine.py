from __future__ import annotations

import asyncio

from iec104.asdu.header import ASDUHeader
from iec104.asdu.types.m_sp_na_1 import SinglePointASDU, SinglePointInformation
from iec104.link.session import SessionParameters, create_server_session
from iec104.link.tcp import IEC104Client
from iec104.spec.constants import CauseOfTransmission, TypeID


def test_client_server_roundtrip() -> None:
    asyncio.run(_client_server_roundtrip())


async def _client_server_roundtrip() -> None:
    received: asyncio.Queue[SinglePointASDU] = asyncio.Queue()

    async def handle(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        session = await create_server_session(reader, writer, SessionParameters())
        await session.start()
        asdu = await session.recv()
        await received.put(asdu)
        await session.send_asdu(asdu)
        await session.close()

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    host, port = server.sockets[0].getsockname()[:2]

    client = await IEC104Client.connect(host, port)
    header = ASDUHeader(
        type_id=TypeID.M_SP_NA_1,
        sequence=False,
        vsq_number=1,
        cause=CauseOfTransmission.SPONTANEOUS,
        negative_confirm=False,
        test=False,
        originator_address=0,
        common_address=1,
        oa=None,
    )
    asdu = SinglePointASDU(
        header=header,
        information_objects=(SinglePointInformation(ioa=100, value=True),),
    )
    await client.send_asdu(asdu)
    echoed = await asyncio.wait_for(client.recv(), timeout=5.0)
    assert echoed.information_objects[0].ioa == 100
    server_asdu = await asyncio.wait_for(received.get(), timeout=5.0)
    assert server_asdu.information_objects[0].ioa == 100
    await client.close()
    server.close()
    await server.wait_closed()

