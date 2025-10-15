# Beitragende Richtlinien

Vielen Dank für Ihr Interesse an `iec104`! Dieses Projekt legt großen Wert auf getestete, gut dokumentierte Beiträge. Bitte folgen Sie diesen Schritten:

1. **Umgebung vorbereiten**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   pre-commit install
   ```
2. **Kodierstil**
   - Halten Sie sich an Black/ruff (werden automatisch durch Pre-Commit angewendet).
   - Nutzen Sie Typannotationen; führen Sie `mypy --strict` aus.
   - Docstrings im Google-Format, Benutzer:innen-Dokumentation auf Deutsch.
3. **Tests**
   ```bash
   pytest -q
   mypy --strict
   ruff check .
   ```
4. **Pull Requests**
   - Beschreiben Sie die Motivation und die vorgenommenen Änderungen klar.
   - Fügen Sie neue Tests und Dokumentation für neue Features hinzu.
   - Stellen Sie sicher, dass die Beispiele weiterhin funktionieren.

Vielen Dank für Ihren Beitrag!

