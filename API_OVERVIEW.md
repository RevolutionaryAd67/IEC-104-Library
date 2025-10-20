**Kurzfassung für Eilige**
- Asynchrone IEC 60870-5-104 Stack mit I/S/U-Rahmen, Sequenzierung und Timersteuerung auf Basis von ``asyncio``.
- Öffentliche API bündelt Client, Server, Sessions, Codec-Utilities und Protokollkonstanten.
- Unterstützte ASDUs: M_SP_NA_1, M_SP_TB_1, M_ME_NC_1, C_SC_NA_1, C_IC_NA_1 (erweiterbar über Registry).
- Sequenzfenster ``k`` standardmäßig 12; Empfangsbestätigungen aktualisieren ``peer_ack`` und stoppen ``T1``.
- Handshake: STARTDT_ACT/CON, STOPDT_ACT/CON, TESTFR_ACT/CON mit automatischer Bestätigung.
- Timeout-Handling über T0 (Handshake), T1 (I-Ack), T3 (Idle Keepalive); T2 vorgesehen aber derzeit ungenutzt.
- Session trennt bei Sequenzfehlern oder Buffer-Überlauf; Fehler propagieren als ``IEC104Error``-Ableitungen.
- Roh-Codec akzeptiert ``memoryview`` und liefert zero-copy Strukturen; StreamingDecoder kapselt BoundedBuffer.
- Konfigurierbare Originator Address (OA) via ``SessionParameters.with_oa``.
- Logging liefert strukturierte Schlüssel (z. B. ``role``) und lässt sich direkt in ``logging`` integrieren.
- Minimalbeispiele weiter unten zeigen Client, Server und Raw-APDU-Workflow.

## 1. Paketübersicht
Kurzbeschreibung: Das Paket ``iec104`` stellt eine vollständig typisierte, asynchrone Implementierung des IEC 60870-5-104 Protokolls bereit. Es umfasst APCI-/ASDU-Codierung, eine Streaming-Dekodierpipeline, Zustandsautomat mit Sequenzfenster und Timer sowie Komfort-APIs für TCP-Client und -Server.

Dateibaum (relevante Module):
```
iec104/
├── __init__.py
├── apci/
│   ├── control_field.py
│   └── frame.py
├── asdu/
│   ├── header.py
│   ├── ioa.py
│   └── types/
│       ├── common.py
│       ├── m_sp_na_1.py
│       ├── m_sp_tb_1.py
│       ├── m_me_nc_1.py
│       └── c_sc_na_1.py
├── codec/
│   ├── decode.py
│   └── encode.py
├── errors.py
├── link/
│   ├── session.py
│   ├── tcp.py
│   └── timers.py
├── logging.py
├── spec/
│   ├── constants.py
│   └── time.py
├── typing.py
└── utils/
    ├── bitops.py
    └── buffers.py
```

## 2. Öffentliche API (klare Imports)
| Symbol | Import-Pfad | Sichtbarkeit | Sync/Async | Thread-Safety | Stabilität |
| --- | --- | --- | --- | --- | --- |
| ``ASDUType`` | ``from iec104 import ASDUType`` | public Typalias | N/A | abhängig von zugrundeliegenden Objekten, unveränderlich | Alpha |
| ``CauseOfTransmission`` | ``from iec104 import CauseOfTransmission`` | public Enum | Sync | thread-safe (konstant) | Stabilisiert für Nutzung |
| ``CP56Time2a`` | ``from iec104 import CP56Time2a`` | public Dataclass | Sync | thread-safe solange immutable Nutzung | Stabil |
| ``IEC104Client`` | ``from iec104 import IEC104Client`` | public Klasse | Async Methoden | nicht thread-safe, asyncio-loop-gebunden | Alpha |
| ``IEC104Server`` | ``from iec104 import IEC104Server`` | public Klasse | Async Methoden | nicht thread-safe, asyncio-loop-gebunden | Alpha |
| ``IEC104Session`` | ``from iec104 import IEC104Session`` | public Klasse | Async Methoden | nicht thread-safe, asyncio-loop-gebunden | Alpha |
| ``SessionParameters`` | ``from iec104 import SessionParameters`` | public Dataclass | Sync | threadsafe solange immutable genutzt | Alpha |
| ``StreamingAPDUDecoder`` | ``from iec104 import StreamingAPDUDecoder`` | public Klasse | Sync Methoden | threadsafe? nein, zustandsbehaftet ohne Lock | Alpha |
| ``TypeID`` | ``from iec104 import TypeID`` | public Enum | Sync | thread-safe | Stabil |
| ``build_i_frame`` | ``from iec104 import build_i_frame`` | public Funktion | Sync | reentrant/thread-safe | Stabil |
| ``decode_apdu`` | ``from iec104 import decode_apdu`` | public Funktion | Sync | reentrant/thread-safe | Stabil |
| ``decode_asdu`` | ``from iec104 import decode_asdu`` | public Funktion | Sync | reentrant/thread-safe | Stabil |
| ``encode_asdu`` | ``from iec104 import encode_asdu`` | public Funktion | Sync | reentrant/thread-safe | Stabil |

## 3. Klassen & Funktionen (Signaturen + Docstrings verdichtet)
### ASDUType
- **Signatur:** ``ASDUType = ASDU[InformationObject]`` (Typalias). 【F:src/iec104/typing.py†L13-L14】
- **Zweck:** Stellt die generische ASDU-Instanz mit bereits auf ``InformationObject`` konkretisiertem Typargument bereit.
- **Nebenwirkungen:** keine.

### CauseOfTransmission
- **Signatur:** ``class CauseOfTransmission(IntEnum)`` mit Werten 1–20. 【F:src/iec104/spec/constants.py†L19-L40】
- **Zweck:** Enum der unterstützten Übertragungsursachen.
- **Rückgabe:** IntEnum-Wert.
- **Nebenwirkungen:** keine.

### CP56Time2a
- **Signatur:** ``@dataclass(slots=True) class CP56Time2a`` mit Feldern ``milliseconds:int``, ``minute:int``, ``invalid:bool``, ``hour:int``, ``summer_time:bool``, ``day_of_month:int``, ``day_of_week:int``, ``month:int``, ``year:int``. 【F:src/iec104/spec/time.py†L10-L88】
- **Methoden:**
  - ``to_datetime(self) -> datetime``: wirft ``ValueError`` bei ``invalid=True``. 【F:src/iec104/spec/time.py†L22-L44】
  - ``from_datetime(cls, dt: datetime, *, summer_time: bool = False) -> CP56Time2a``: erwartet TZ-aware Datum, sonst ``ValueError``. 【F:src/iec104/spec/time.py†L46-L65】
  - ``encode(self) -> bytes``: validiert und serialisiert in 7 Bytes. 【F:src/iec104/spec/time.py†L67-L82】
  - ``decode(cls, view: memoryview) -> CP56Time2a``: erwartet mindestens 7 Bytes. 【F:src/iec104/spec/time.py†L84-L117】
- **Nebenwirkungen:** keine.
- **Minimalbeispiel:**
```python
from datetime import datetime, UTC
from iec104 import CP56Time2a
stamp = CP56Time2a.from_datetime(datetime(2024, 1, 1, 12, tzinfo=UTC))
assert stamp.to_datetime().year == 2024
```

### IEC104Client
- **Signatur:** ``class IEC104Client`` mit ``__init__(session: IEC104Session)``, ``@classmethod async connect(cls, host: str, port: int, params: SessionParameters | None = None) -> IEC104Client``, ``async send_asdu(self, asdu: ASDUType) -> None``, ``async recv(self) -> ASDUType``, ``async close(self) -> None``, ``async general_interrogation(...) -> list[ASDUType]``, ``session``-Property. 【F:src/iec104/link/tcp.py†L24-L158】
- **Zweck:** Komfort-Fassade für ``IEC104Session`` auf TCP-Clientseite.
- **Parameter:** ``host``/``port`` Zieladresse, ``params`` optional ``SessionParameters``.
- **Rückgaben:** ``connect`` liefert neuen Client.
- **Exceptions:** weitergereichte ``SessionClosedError``, ``IEC104Error`` aus Session.
- **Nebenwirkungen:** Netzwerkzugriff via asyncio Streams; startet Session-Handshakes.
- **Lebenszyklus:** ``connect`` → ``send_asdu``/``recv`` → ``close``.
- **Generalabfrage:** ``general_interrogation`` erstellt automatisch einen ``C_IC_NA_1``-Befehl (QOI=20 default), wartet auf Aktivierungsbestätigung sowie Abschluss (COT 6/7/10) und liefert alle dazwischen empfangenen ASDUs zurück; Timeout pro Phase optional. 【F:src/iec104/link/tcp.py†L46-L153】

### IEC104Server
- **Signatur:** ``class IEC104Server`` mit ``__init__(host: str, port: int, handler: ASDUHandler, params: SessionParameters | None = None)``, ``async start(self) -> None``, ``async stop(self) -> None``. 【F:src/iec104/link/tcp.py†L47-L78】
- **Zweck:** Lauscht auf TCP, akzeptiert Clients, erstellt für jede Verbindung eine ``IEC104Session`` und ruft ``handler``.
- **Parameter:** ``handler`` async Callable ``(session, asdu)``.
- **Exceptions:** Leitet ``SessionClosedError`` intern ab; Logging bei Verbindungsende.
- **Nebenwirkungen:** Netzwerk-Listener, spawnt Tasks pro Client.

### IEC104Session
- **Signatur:** ``class IEC104Session`` mit wichtigsten Methoden ``async start(self) -> None``, ``async send_asdu(self, asdu: ASDUType) -> None``, ``async recv(self) -> ASDUType``, ``async close(self) -> None``. Konstruktor erwartet ``asyncio.StreamReader/Writer``, ``SessionParameters`` sowie ``role``. 【F:src/iec104/link/session.py†L40-L204】
- **Zweck:** Kernzustandsautomat für IEC 104 Sessions.
- **Wichtige Parameter:** ``params`` bestimmt Fenster ``k``/``w`` und Timer; ``role`` string "client"/"server".
- **Rückgaben:** ``recv`` liefert nächste ASDU.
- **Exceptions:** ``SessionClosedError`` bei geschlossener Sitzung, ``SequenceError`` bei Sequenzfehlern, ``TimeoutError`` bei T1 Ablauf, ``HandshakeError`` bei T0, ``UnsupportedTypeError`` aus Codec.
- **Nebenwirkungen:** Netzwerk I/O, Timer-Tasks, interne Queues.
- **Lebenszyklus:** ``create_*_session`` → ``start`` (führt STARTDT) → Datentransfer → ``close`` sendet STOPDT.

### SessionParameters
- **Signatur:** ``@dataclass(slots=True) class SessionParameters(k:int=12, w:int=8, t0:float=30.0, t1:float=15.0, t2:float=10.0, t3:float=20.0, with_oa: bool=False)``. 【F:src/iec104/link/session.py†L33-L46】
- **Zweck:** Konfiguration für Fenster, Timer, OA.
- **Besonderheiten:** ``t2`` und ``w`` derzeit nicht ausgewertet (siehe Anmerkungen).

### StreamingAPDUDecoder
- **Signatur:** ``class StreamingAPDUDecoder(capacity: int = MAX_APDU_LENGTH * 2, with_oa: bool = False)`` mit ``feed(self, data: bytes|bytearray|memoryview) -> list[tuple[APCIFrame, ASDUType|None]]`` und ``clear(self) -> None``. 【F:src/iec104/codec/decode.py†L59-L112】
- **Zweck:** Akkumuliert TCP-Streambytes und liefert komplette APCI/ASDU-Paare.
- **Nebenwirkungen:** verwaltet internen ``BoundedBuffer``.
- **Exceptions:** ``LengthError`` bei Überlauf (aus Buffer), ``UnsupportedTypeError`` bei unbekanntem ASDU.

### TypeID
- **Signatur:** ``class TypeID(IntEnum)`` mit Einträgen ``M_SP_NA_1=1``, ``M_ME_NC_1=13``, ``M_SP_TB_1=30``, ``C_SC_NA_1=45``, ``C_IC_NA_1=100``. 【F:src/iec104/spec/constants.py†L12-L31】
- **Zweck:** Liste der eingebauten ASDUs.

### build_i_frame
- **Signatur:** ``build_i_frame(asdu_bytes: bytes, send_seq: int, recv_seq: int) -> bytes``. 【F:src/iec104/codec/encode.py†L53-L59】
- **Zweck:** Hüllt ASDU in I-Frame mit Sequenznummern; nutzt ``IControlField``.
- **Exceptions:** ``ValueError`` bei ungültigen Sequenzen (via ``ensure_15bit``).

### decode_apdu / decode_asdu / encode_asdu
- **Signaturen:**
  - ``decode_apdu(data: bytes, *, with_oa: bool = False) -> tuple[APCIFrame, ASDUType | None, int]``. 【F:src/iec104/codec/decode.py†L90-L106】
  - ``decode_asdu(view: memoryview, *, with_oa: bool = False) -> ASDUType``. 【F:src/iec104/codec/decode.py†L82-L88】
  - ``encode_asdu(asdu: ASDUType) -> bytes``. 【F:src/iec104/codec/encode.py†L37-L52】
- **Zweck:** Serialisierung und Deserialisierung von ASDUs/APDUs.
- **Exceptions:** ``UnsupportedTypeError`` für unbekannte Typen oder Länge >253 Bytes; ``LengthError``/``DecodeError`` aus Unterfunktionen.
- **Nebenwirkungen:** keine.

## 4. Datenmodelle & Protokoll-Mapping
- **ASDUHeader**: Felder ``type_id``, ``sequence`` (bool für kontinuierliche IOAs), ``vsq_number`` (1–127), ``cause`` (COT), ``negative_confirm``, ``test``, ``originator_address`` (16 Bit), ``common_address`` (16 Bit), ``oa`` (optional Byte). Encoding prüft OA-Konfiguration. 【F:src/iec104/asdu/header.py†L7-L60】
- **Information Objects:**
  - ``SinglePointInformation`` mit ``value: bool``, ``quality: int`` (0–0x1E). 【F:src/iec104/asdu/types/m_sp_na_1.py†L7-L30】
  - ``SinglePointWithCP56Time`` plus ``timestamp: CP56Time2a``. 【F:src/iec104/asdu/types/m_sp_tb_1.py†L1-L39】
  - ``MeasuredValueFloat`` mit ``value: float``, ``quality: int`` (0–0x1F). 【F:src/iec104/asdu/types/m_me_nc_1.py†L1-L34】
  - ``SingleCommand`` mit ``state: bool``, ``qualifier: int``, ``select: bool``. 【F:src/iec104/asdu/types/c_sc_na_1.py†L1-L33】
- ``GeneralInterrogation`` mit ``qualifier: int`` (0–0xFF). 【F:src/iec104/asdu/types/c_ic_na_1.py†L10-L41】
- **ASDU Klassen:** ``SinglePointASDU``, ``SinglePointTimeASDU``, ``MeasuredValueASDU``, ``SingleCommandASDU``, ``GeneralInterrogationASDU``; alle erzwingen Objektanzahl und IOA-Sequenzen.
- **APCI Mapping:**
  - I-Frame: ``IControlField(send_seq, recv_seq)`` mit LSB=0 Codierung. Acknowledgement bei Empfang via ``seq_acknowledged``. 【F:src/iec104/apci/control_field.py†L22-L45】
  - S-Frame: ``SControlField(recv_seq)`` sendet reine Bestätigung. 【F:src/iec104/apci/control_field.py†L47-L57】
  - U-Frame: ``UControlField(u_type)`` für STARTDT/STOPDT/TESTFR. 【F:src/iec104/apci/control_field.py†L59-L76】
- **Sequenznummern:** 15 Bit modulo 32768. ``seq_increment`` und ``seq_acknowledged`` verwalten Wrap-Around. 【F:src/iec104/link/session.py†L48-L64】
- **Fenster k/w:** ``k`` begrenzt unbestätigte I-Frames; ``w`` vorgesehen für Empfangsbestätigungstrigger, aber aktuell nicht genutzt (siehe Anmerkung). 【F:src/iec104/link/session.py†L33-L46】【F:src/iec104/link/session.py†L140-L163】
- **ASDU Typen & COT:** Unterstützt TypeIDs in ``SUPPORTED_TYPE_IDS``; COT-Werte siehe Enum.
- **Zeitstempel:** CP56Time2a encode/decode 7 Byte, 16ms Auflösung, Sommerzeit-Bit. 【F:src/iec104/spec/time.py†L67-L115】
- **Beispiel Rohbytes → Felder:**
```python
from iec104 import decode_apdu
frame, asdu, consumed = decode_apdu(b"\x68\x0E\x00\x00\x00\x00\x01\x01\x03\x00\x01\x00\x00\x00\x01\x00")
assert frame.format.value == "I"
print(asdu.information_objects[0].ioa)  # 1
```

## 5. Zustandsautomat & Timer (IEC-104)
- **Zustände:** ``CLOSED`` → ``CONNECTING`` (Client) → ``RUNNING`` nach STARTDT-Handshake oder ``IDLE``→``RUNNING`` (Server). STOPDT führt zu ``STOPPED``, Ende von Reader-Loop zu ``CLOSED``. 【F:src/iec104/link/session.py†L20-L38】【F:src/iec104/link/session.py†L66-L108】
- **Übergänge:**
  - Client sendet ``STARTDT_ACT`` und wartet ``STARTDT_CON`` bis ``T0`` (``params.t0``). Ausfall → ``HandshakeError``.
  - Server bei ``STARTDT_ACT`` sendet ``STARTDT_CON`` und aktiviert ``RUNNING``.
  - ``STOPDT_ACT``/``STOPDT_CON`` setzen ``STOPPED`` und schließen Writer.
  - ``TESTFR_ACT`` initiiert Keepalive, Antwort ``TESTFR_CON`` reaktiviert ``T3``.
  - I-Frame Empfang erhöht ``recv_seq`` und sendet ``S``-Frame als Bestätigung.
- **Timer:**
  - ``T0`` (Handshakes) – genutzt via ``asyncio.wait_for`` im Client-Handshake. 【F:src/iec104/link/session.py†L109-L130】
  - ``T1`` startet nach I-Frame-Send; Ablauf erzeugt ``TimeoutError`` und schließt Session. 【F:src/iec104/link/session.py†L164-L205】
  - ``T2`` Parameter vorhanden, aber keine Implementierung (siehe Anmerkungen).
  - ``T3`` startet nach RUNNING; Ablauf sendet ``TESTFR_ACT``. 【F:src/iec104/link/session.py†L130-L205】
- **Sequenz-/Bestätigungslogik:**
  - ``_wait_for_window`` blockiert Sender sobald unbestätigte I-Frames ≥ ``k``. 【F:src/iec104/link/session.py†L150-L163】
  - ``_acknowledge`` entfernt bestätigte Frames, setzt ``peer_ack``/Fenster-Event und stoppt ``T1`` bei leerem Puffer. 【F:src/iec104/link/session.py†L165-L190】
  - Empfang eines I-Frames mit unerwarteter Sequenz löst ``SequenceError`` aus. 【F:src/iec104/link/session.py†L117-L144】

## 6. Nebenläufigkeit & Performance
- Asyncio-basierte Architektur; alle öffentlichen Methoden (außer reinen Codec-Funktionen) müssen im selben Event Loop wie erzeugt ausgeführt werden. Keine Locks, daher nicht thread-safe.
- ``IEC104Session`` nutzt ``asyncio.Queue`` für eingehende ASDUs; Backpressure via Fenster ``k`` und ``_window_event``.
- ``StreamingAPDUDecoder`` hält BoundedBuffer (Standardkapazität 506 Bytes); Überläufe werfen ``LengthError``.
- Liveness: ``T3`` Keepalive sendet ``TESTFR_ACT`` bei Inaktivität; ``_reader_task`` beendet Session bei Verbindungsabbruch.
- Performance: Zero-Copy-Dekodierung via ``memoryview``; ``BoundedBuffer`` vermeidet Kopien außer beim Konsum.

## 7. Konfiguration & Umgebungsvariablen
- ``SessionParameters`` Felder:
  - ``k``: max. unbestätigte I-Frames (Default 12).
  - ``w``: Schwelle für explizite Bestätigungen (noch ungenutzt).
  - ``t0``: Handshake-Timeout STARTDT (Default 30 s).
  - ``t1``: Acknowledgement-Timeout (Default 15 s).
  - ``t2``: (reserviert, 10 s) – noch ohne Wirkung.
  - ``t3``: Idle-Timeout für TESTFR (Default 20 s).
  - ``with_oa``: Erwartet OA-Byte im ASDU-Header.
- Weitere globale Defaults: ``MAX_APDU_LENGTH=253``, ``DEFAULT_K_VALUE=12`` usw. 【F:src/iec104/spec/constants.py†L6-L18】
- Keine Umgebungsvariablen vorgesehen.

## 8. Fehlermodell & Logging
- **Exceptions:**
  - ``IEC104Error`` Basis; Unterklassen ``FrameError``, ``LengthError``, ``SequenceError``, ``TimeoutError``, ``UnsupportedTypeError``, ``DecodeError``, ``PolicyViolation``, ``SessionClosedError``, ``HandshakeError``. 【F:src/iec104/errors.py†L1-L34】
  - ``Session.send_asdu``/``recv`` werfen ``SessionClosedError`` wenn nicht RUNNING. 【F:src/iec104/link/session.py†L98-L129】
  - ``_on_t1_timeout`` setzt ``TimeoutError`` und schließt Session. 【F:src/iec104/link/session.py†L191-L205】
- **Retry-Strategien:** Beim ``TimeoutError`` erfolgt ``close()`` und Verbindung muss extern neu aufgebaut werden. Bei ``SessionClosedError`` Handler neu verbinden.
- **Logging:** ``get_logger(name, **context)`` liefert ``StructuredAdapter``; Kontext (z. B. ``role``) wird mit LogRecord-``extra`` zusammengeführt. 【F:src/iec104/logging.py†L1-L36】
- Logeinträge in ``IEC104Session`` (Debug ``state change``) und ``IEC104Server`` (Info ``client connected``/``session closed``) nutzen strukturierte Felder.

## 9. Best-Practice-Rezepte (bewährte Aufrufmuster)
### Client: connect → STARTDT → Command → close
```python
import asyncio
from datetime import datetime, UTC
from iec104 import (
    IEC104Client, SessionParameters, TypeID,
    CauseOfTransmission, CP56Time2a
)
from iec104.asdu.header import ASDUHeader
from iec104.asdu.types.c_sc_na_1 import SingleCommand, SingleCommandASDU

async def main() -> None:
    client = await IEC104Client.connect("127.0.0.1", 2404, SessionParameters())
    header = ASDUHeader(
        type_id=TypeID.C_SC_NA_1,
        sequence=False,
        vsq_number=1,
        cause=CauseOfTransmission.ACTIVATION,
        negative_confirm=False,
        test=False,
        originator_address=0,
        common_address=1,
        oa=None,
    )
    command = SingleCommandASDU(
        header=header,
        information_objects=(SingleCommand(ioa=100, state=True, qualifier=0),),
    )
    await client.send_asdu(command)
    await client.close()

asyncio.run(main())
```

### Server-Skeleton: bind → start → respond measurement
```python
import asyncio
from iec104 import IEC104Server, SessionParameters, TypeID, CauseOfTransmission
from iec104.asdu.header import ASDUHeader
from iec104.asdu.types.m_me_nc_1 import MeasuredValueASDU, MeasuredValueFloat

async def handler(session, asdu):
    if asdu.header.type_id is TypeID.C_SC_NA_1:
        reply_header = ASDUHeader(
            type_id=TypeID.M_ME_NC_1,
            sequence=False,
            vsq_number=1,
            cause=CauseOfTransmission.SPONTANEOUS,
            negative_confirm=False,
            test=False,
            originator_address=0,
            common_address=asdu.header.common_address,
            oa=asdu.header.oa,
        )
        measurement = MeasuredValueASDU(
            header=reply_header,
            information_objects=(MeasuredValueFloat(ioa=200, value=42.0, quality=0),),
        )
        await session.send_asdu(measurement)

async def main() -> None:
    server = IEC104Server("0.0.0.0", 2404, handler, SessionParameters())
    await server.start()
    try:
        await asyncio.Future()
    finally:
        await server.stop()

asyncio.run(main())
```

### Raw-APDU: eigene Pipeline
```python
from iec104 import build_i_frame, encode_asdu, decode_apdu
from iec104.asdu.header import ASDUHeader
from iec104.asdu.types.m_sp_na_1 import SinglePointASDU, SinglePointInformation
from iec104.spec.constants import TypeID, CauseOfTransmission

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
    information_objects=(SinglePointInformation(ioa=5, value=True, quality=0),),
)
asdu_bytes = encode_asdu(asdu)
apdu = build_i_frame(asdu_bytes, send_seq=0, recv_seq=0)
frame, decoded_asdu, consumed = decode_apdu(apdu)
assert consumed == len(apdu)
assert decoded_asdu.information_objects[0].ioa == 5
```

- **Timeout/Fehlerbehandlung:** Prüfen Sie ``SessionClosedError`` und ``TimeoutError`` in send/recv Loops; bei ``TimeoutError`` Verbindung neu aufbauen, ggf. Backoff.

## 10. Integrationsleitfaden (Adapter-Sicht)
- **Minimale Adapter-Schnittstelle:** Implementieren Sie einen ``ASDUHandler`` (async ``callable(session, asdu)``). Für rückseitige Systeme definieren Sie Mappings zwischen ``asdu.header`` Feldern (COT, CA, OA) und Domänenobjekten.
- **Domain-Mapping:**
  - Nutzen Sie ``TypeID`` zur Auswahl des DTO (z. B. ``SinglePointInformation`` → Binärsignal, ``MeasuredValueFloat`` → Messwert).
  - ``common_address`` gruppiert Stationen; ``information_objects`` enthalten IOA als 24-Bit Adresse.
  - Zeitstempel ``CP56Time2a`` konvertieren via ``to_datetime``.
- **WebSocket / Eventbus:** Serialisieren Sie eingehende ASDUs in JSON mit Feldern ``typeId``, ``cause``, ``ca``, ``ioa``, ``value``, ``quality``, ``timestamp`` (UTC ISO-Format) – Logging-Adapter liefert bereits strukturierte Felder zur Weiterleitung.
- **Sicherheitsadapter:** Bei Bedarf ``PolicyViolation`` werfen, um Sitzungen frühzeitig abzubrechen (Policy-Logik extern implementieren).

## 11. Versions-/Lizenzinfo
- Paketversion ``0.1.0`` laut ``pyproject.toml`` und ``iec104.__version__``. 【F:pyproject.toml†L6-L32】【F:src/iec104/__init__.py†L23-L27】
- Lizenz: MIT. 【F:pyproject.toml†L6-L32】
- Unterstützte Python-Versionen: ``>=3.11``. 【F:pyproject.toml†L6-L32】
- Entwicklungsstatus: "Alpha" laut Klassifizierer.

### Anmerkungen / Unschärfen
- ``SessionParameters.w`` sowie ``t2`` sind definiert, werden jedoch derzeit nicht innerhalb von ``IEC104Session`` ausgewertet – Implementierung ggf. zukünftige Erweiterung. 【F:src/iec104/link/session.py†L33-L46】
- Die Liste der unterstützten ASDUs ist begrenzt; zusätzliche Typen müssen via ``codec.encode.register_type``/``codec.decode.register_type`` ergänzt werden (Registrierungsfunktionen sind intern verfügbar, aber nicht im ``__all__`` exportiert).
