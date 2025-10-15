Sicherheitsaspekte
==================

Die Bibliothek erzwingt strikte Längenprüfungen und limitiert interne Buffer,
um DoS-Angriffe zu erschweren. Für produktive Umgebungen werden folgende
Schritte empfohlen:

* Verwenden Sie IP-Filter (z. B. ``IPAllowlistPolicy``) in Verbindung mit
  Segmentierung des Netzes.
* Aktivieren Sie Transportverschlüsselung durch externe Komponenten und
  integrieren Sie TLS über die bereitgestellten Hook-Punkte.
* Überwachen Sie Timer-Auslösungen und Fehlermeldungen in der strukturierten
  Protokollierung, um Anomalien frühzeitig zu erkennen.
* Validieren Sie Applikationsdaten vor deren Weiterverarbeitung.

