"""Minimaler IEC 104 Server, der Testrahmen beantwortet."""

from __future__ import annotations

import asyncio

from .. import IEC104Server
from ..link.session import IEC104Session
from ..typing import ASDUType


async def handler(session: IEC104Session, asdu: ASDUType) -> None:
    print("ASDU empfangen:", asdu)
    # Echo zurück
    await session.send_asdu(asdu)


async def main() -> None:
    server = IEC104Server("127.0.0.1", 2404, handler)
    await server.start()
    print("Server gestartet auf 127.0.0.1:2404")
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())

