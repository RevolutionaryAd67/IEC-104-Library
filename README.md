# IEC 60870-5-104 (iec104)

## Überblick

`iec104` ist eine industrietaugliche, asynchrone Python-Bibliothek zur Umsetzung des IEC 60870-5-104 Protokolls. Sie bietet vollständige Unterstützung für APCI-Rahmen, die Codierung und Decodierung zentraler ASDUs sowie eine robuste TCP-Sitzungsverwaltung mit Timern und Flusskontrolle.

## Eigenschaften

- Vollständig typannotierte, asynchrone API für Client- und Serverbetrieb.
- Zero-Copy-Dekodierung auf Basis von `memoryview`.
- Erweiterbares Registry-System für zusätzliche ASDUs.
- Umfassende Sicherheitsprüfungen, konfigurierbare Grenzen und Vorbereitungen für TLS-Integration.
- Deutsche Dokumentation (Sphinx) und ausführliche Testsuite inkl. Property-basierten Tests.

## Schnellstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest -q
mypy --strict
```

Weitere Beispiele sind unter `src/iec104/examples/` verfügbar.

## Sicherheitshinweise

- Eingabeströme werden strikt validiert und abgebrochene Sitzungen werden sauber beendet.
- Implementieren Sie eigene Sicherheitsrichtlinien über `iec104.security.policy` (z. B. IP-Allowlist, Rate-Limiting, TLS).
- Nutzen Sie isolierte Netzwerke und folgen Sie bewährten Verfahren für SCADA-Systeme.

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.

