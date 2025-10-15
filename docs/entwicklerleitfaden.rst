Entwicklerleitfaden
===================

Code-Stil
---------

* Python >= 3.11, Typhinweise sind obligatorisch.
* Formatierung mit ``black`` und Linting mit ``ruff``.
* Docstrings im Google-Stil, Benutzer:innen-Dokumentation auf Deutsch.

Tests
-----

* ``pytest`` für Unit- und Integrationstests.
* ``hypothesis`` für eigenschaftsbasierte Szenarien.
* ``mypy --strict`` zur Typprüfung.

Beitragsprozess
---------------

1. Fork erstellen und Feature-Branch anlegen.
2. Änderungen implementieren, inklusive Tests und Dokumentation.
3. ``pre-commit`` Hooks ausführen.
4. Merge-Request mit klarer Beschreibung einreichen.

