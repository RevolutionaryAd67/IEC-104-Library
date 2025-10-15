"""Minimaler IEC 104 Client zum Einlesen von Indikationen."""

from __future__ import annotations

import asyncio

from .. import IEC104Client
from ..asdu.header import ASDUHeader
from ..asdu.types.m_sp_na_1 import SinglePointASDU, SinglePointInformation
from ..spec.constants import CauseOfTransmission, TypeID


async def main() -> None:
    client = await IEC104Client.connect("127.0.0.1", 2404)
    header = ASDUHeader(
        type_id=TypeID.M_SP_NA_1,
        sequence=False,
        vsq_number=1,
        cause=CauseOfTransmission.ACTIVATION,
        negative_confirm=False,
        test=False,
        originator_address=0,
        common_address=1,
        oa=None,
    )
    asdu = SinglePointASDU(
        header=header,
        information_objects=(SinglePointInformation(ioa=1, value=True),),
    )
    await client.send_asdu(asdu)
    try:
        indication = await asyncio.wait_for(client.recv(), timeout=5.0)
        print("Empfangen:", indication)
    except TimeoutError:
        print("Keine Antwort empfangen")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

