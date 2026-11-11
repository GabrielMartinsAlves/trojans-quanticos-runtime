"""Caminhos e constantes compartilhados pelos scripts de experimento.

Importar este módulo também coloca `src/` no caminho de importação e deixa a saída do console em
UTF-8 (o console do Windows não mostra o desenho dos circuitos sem isso).
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RESULTADOS = RAIZ / "results"
CHAVE = ["familia", "circuito", "porta", "posicao", "papel"]

sys.path.insert(0, str(RAIZ / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
