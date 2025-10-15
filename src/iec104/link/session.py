"""Session management and state machine for IEC 60870-5-104."""

from __future__ import annotations

import asyncio
import builtins
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum, auto

from ..apci.control_field import IControlField, SControlField, UControlField, UFrameType
from ..apci.frame import APCIFrame, build_apci
from ..codec.decode import StreamingAPDUDecoder
from ..codec.encode import build_i_frame, encode_asdu
from ..errors import HandshakeError, SequenceError, SessionClosedError, TimeoutError
from ..logging import get_logger
from ..spec.constants import (
    DEFAULT_K_VALUE,
    DEFAULT_T0,
    DEFAULT_T1,
    DEFAULT_T2,
    DEFAULT_T3,
    DEFAULT_W_VALUE,
)
from ..typing import ASDUType
from .timers import Timer

SEQUENCE_MODULO = 32768


class SessionState(Enum):
    CLOSED = auto()
    CONNECTING = auto()
    IDLE = auto()
    RUNNING = auto()
    STOPPED = auto()


@dataclass(slots=True)
class SessionParameters:
    """Configurable protocol parameters."""

    k: int = DEFAULT_K_VALUE
    w: int = DEFAULT_W_VALUE
    t0: float = DEFAULT_T0
    t1: float = DEFAULT_T1
    t2: float = DEFAULT_T2
    t3: float = DEFAULT_T3
    with_oa: bool = False


def seq_increment(value: int) -> int:
    return (value + 1) % SEQUENCE_MODULO


def seq_distance(a: int, b: int) -> int:
    return (a - b) % SEQUENCE_MODULO


def seq_acknowledged(seq: int, nr: int) -> bool:
    diff = (nr - seq) % SEQUENCE_MODULO
    return 0 < diff <= SEQUENCE_MODULO // 2


class IEC104Session:
    """Manage an IEC 60870-5-104 connection."""

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        params: SessionParameters,
        *,
        role: str,
    ) -> None:
        self._reader = reader
        self._writer = writer
        self._params = params
        self._role = role
        self._state = SessionState.CONNECTING if role == "client" else SessionState.IDLE
        self._incoming: asyncio.Queue[ASDUType] = asyncio.Queue()
        self._decoder = StreamingAPDUDecoder(with_oa=params.with_oa)
        self._send_seq = 0
        self._recv_seq = 0
        self._peer_ack = 0
        self._unacked: OrderedDict[int, bytes] = OrderedDict()
        self._window_event = asyncio.Event()
        self._window_event.set()
        self._running = asyncio.Event()
        self._start_confirm = asyncio.Event()
        self._logger = get_logger("iec104.session", role=role)
        self._loop = asyncio.get_running_loop()
        self._reader_task = self._loop.create_task(self._read_loop())
        self._closing = False
        self._fatal_error: BaseException | None = None
        self._t1 = Timer("T1", params.t1, self._on_t1_timeout)
        self._t3 = Timer("T3", params.t3, self._on_t3_timeout)
        self._t0_value = params.t0

    async def start(self) -> None:
        """Perform the session handshake depending on the role."""

        if self._role == "client":
            await self._client_handshake()
        else:
            await self._running.wait()

    async def send_asdu(self, asdu: ASDUType) -> None:
        """Encode and transmit an ASDU."""

        await self._running.wait()
        if self._state != SessionState.RUNNING:
            raise SessionClosedError("session not running")
        await self._wait_for_window()
        payload = encode_asdu(asdu)
        frame = build_i_frame(payload, self._send_seq, self._recv_seq)
        await self._safe_write(frame)
        self._unacked[self._send_seq] = frame
        self._send_seq = seq_increment(self._send_seq)
        self._t1.start()

    async def recv(self) -> ASDUType:
        """Receive the next ASDU from the peer."""

        await self._running.wait()
        if self._state in {SessionState.CLOSED, SessionState.STOPPED}:
            raise SessionClosedError("session closed")
        if self._fatal_error is not None:
            raise SessionClosedError("session failed") from self._fatal_error
        return await self._incoming.get()

    async def close(self) -> None:
        """Terminate the session gracefully."""

        if self._closing:
            return
        self._closing = True
        try:
            await self._send_u_frame(UFrameType.STOPDT_ACT)
        except Exception:  # pragma: no cover - best effort
            pass
        self._set_state(SessionState.STOPPED)
        self._writer.close()
        try:
            await self._writer.wait_closed()
        except BrokenPipeError:  # pragma: no cover - platform specific
            pass
        self._reader_task.cancel()
        self._running.clear()
        self._t1.cancel()
        self._t3.cancel()

    async def _client_handshake(self) -> None:
        self._set_state(SessionState.CONNECTING)
        await self._send_u_frame(UFrameType.STARTDT_ACT)
        try:
            await asyncio.wait_for(self._start_confirm.wait(), timeout=self._t0_value)
        except builtins.TimeoutError as exc:
            raise HandshakeError("STARTDT confirmation timeout") from exc
        self._set_state(SessionState.RUNNING)
        self._running.set()
        self._t3.start()

    async def _read_loop(self) -> None:
        try:
            while True:
                data = await self._reader.read(1024)
                if not data:
                    break
                for frame, asdu in self._decoder.feed(data):
                    try:
                        await self._handle_frame(frame, asdu)
                    except Exception as exc:
                        self._fatal_error = exc
                        return
        except asyncio.CancelledError:
            return
        except Exception as exc:  # pragma: no cover - defensive
            self._fatal_error = exc
        finally:
            self._set_state(SessionState.CLOSED)
            self._running.clear()

    async def _handle_frame(self, frame: APCIFrame, asdu: ASDUType | None) -> None:
        control = frame.control
        if isinstance(control, IControlField):
            await self._handle_i_frame(control, asdu)
        elif isinstance(control, SControlField):
            self._handle_s_frame(control)
        elif isinstance(control, UControlField):
            await self._handle_u_frame(control)

    async def _handle_i_frame(
        self, control: IControlField, asdu: ASDUType | None
    ) -> None:
        if control.send_seq != self._recv_seq:
            raise SequenceError(
                f"unexpected send sequence {control.send_seq}, "
                f"expected {self._recv_seq}"
            )
        self._recv_seq = seq_increment(self._recv_seq)
        self._acknowledge(control.recv_seq)
        if asdu is not None:
            await self._incoming.put(asdu)
        await self._send_s_frame()

    def _handle_s_frame(self, control: SControlField) -> None:
        self._acknowledge(control.recv_seq)

    async def _handle_u_frame(self, control: UControlField) -> None:
        if control.u_type == UFrameType.STARTDT_ACT:
            await self._send_u_frame(UFrameType.STARTDT_CON)
            self._set_state(SessionState.RUNNING)
            self._running.set()
            self._t3.start()
        elif control.u_type == UFrameType.STARTDT_CON:
            self._start_confirm.set()
        elif control.u_type == UFrameType.TESTFR_ACT:
            await self._send_u_frame(UFrameType.TESTFR_CON)
        elif control.u_type == UFrameType.TESTFR_CON:
            self._t3.start()
        elif control.u_type == UFrameType.STOPDT_ACT:
            await self._send_u_frame(UFrameType.STOPDT_CON)
            self._set_state(SessionState.STOPPED)
        elif control.u_type == UFrameType.STOPDT_CON:
            self._set_state(SessionState.STOPPED)

    async def _wait_for_window(self) -> None:
        while seq_distance(self._send_seq, self._peer_ack) >= self._params.k:
            self._window_event.clear()
            await self._window_event.wait()

    def _acknowledge(self, nr: int) -> None:
        to_remove = [seq for seq in self._unacked if seq_acknowledged(seq, nr)]
        for seq in to_remove:
            self._unacked.pop(seq, None)
        if to_remove:
            self._peer_ack = nr
            self._window_event.set()
            if not self._unacked:
                self._t1.cancel()

    async def _send_s_frame(self) -> None:
        frame = build_apci(SControlField(recv_seq=self._recv_seq), b"")
        await self._safe_write(frame)

    async def _send_u_frame(self, u_type: UFrameType) -> None:
        frame = build_apci(UControlField(u_type), b"")
        await self._safe_write(frame)

    def _set_state(self, state: SessionState) -> None:
        if self._state != state:
            self._logger.debug(
                "state change", old_state=self._state.name, new_state=state.name
            )
        self._state = state

    async def _on_t1_timeout(self) -> None:
        if self._unacked:
            self._fatal_error = TimeoutError(
                "T1 timer expired waiting for acknowledgement"
            )
            await self.close()

    async def _on_t3_timeout(self) -> None:
        await self._send_u_frame(UFrameType.TESTFR_ACT)

    async def _safe_write(self, data: bytes) -> None:
        try:
            self._writer.write(data)
            await self._writer.drain()
        except (BrokenPipeError, ConnectionResetError):
            self._fatal_error = SessionClosedError("connection lost")
            self._set_state(SessionState.CLOSED)
            self._running.clear()


async def create_client_session(
    host: str,
    port: int,
    params: SessionParameters | None = None,
) -> IEC104Session:
    params = params or SessionParameters()
    reader, writer = await asyncio.open_connection(host, port)
    session = IEC104Session(reader, writer, params, role="client")
    await session.start()
    return session


async def create_server_session(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    params: SessionParameters | None = None,
) -> IEC104Session:
    session = IEC104Session(
        reader, writer, params or SessionParameters(), role="server"
    )
    return session

