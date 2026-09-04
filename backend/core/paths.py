"""Caminhos centrais do monorepo MARIA."""

from pathlib import Path

# Raiz do monorepo (3 níveis acima de backend/core/).
RAIZ_MONOREPO = str(Path(__file__).resolve().parent.parent.parent)
