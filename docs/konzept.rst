Architektur und Konzepte
========================

Die Bibliothek ``iec104`` implementiert die IEC 60870-5-104 Stapelung in klar
gelayouteten Schichten:

* **Link-Layer**: Verwaltung von TCP-Verbindungen, U/S/I-Rahmen und Timern.
* **Codec-Schicht**: Serialisierung und Deserialisierung von APCI- sowie ASDU-Strukturen.
* **Anwendungsobjekte**: Dataklassen für einzelne Type-IDs.

Zustandsautomat
----------------

Der Sitzungszustand wird über einen deterministischen Automaten gesteuert:

::

    [CLOSED] --connect--> [CONNECTING] --STARTDT con--> [RUNNING]
       ^                             |                     |
       |--Stop/Fehler-- [STOPPED] <--+-- STOPDT act/con <--+

Tritt ein Fehler oder eine Zeitüberschreitung auf, wird die Sitzung sauber
geschlossen. Die Sequenznummern werden modulo 32768 geführt.

Timer
-----

Die IEC 104 Timerschiene wird konfigurierbar über ``SessionParameters``
abgebildet. Die Standardwerte (in Sekunden) sind: ``T0=30``, ``T1=15``,
``T2=10`` und ``T3=20``. T1 überwacht ausgehende I-Rahmen, T2 könnte für
verzögerte Bestätigungen genutzt werden (in dieser Implementierung erfolgt
sofortige Bestätigung), und T3 initiiert periodische ``TESTFR``-Rahmen.

Flusskontrolle
--------------

Die Parameter ``k`` (Sende-Fenster) und ``w`` (Empfangsfenster) begrenzen die
Anzahl unbestätigter I-Rahmen. Bei ausgeschöpftem Fenster blockiert die API
so lange, bis Bestätigungen eingehen oder ein Timeout ausgelöst wird.

