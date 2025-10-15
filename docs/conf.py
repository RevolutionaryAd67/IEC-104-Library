"""Sphinx-Konfiguration für die IEC104-Dokumentation."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

project = "iec104"
author = "Industrial Control"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
]
autosectionlabel_prefix_document = True
html_theme = "alabaster"
exclude_patterns: list[str] = []
napoleon_google_docstring = True
napoleon_numpy_docstring = False
language = "de"

