"""Impacto (TVD) e piso de ruído de amostragem."""
from __future__ import annotations

import numpy as np

from .simulacao import amostrar


def tvd(p, q) -> float:
    """Distância de variação total: 0 = distribuições iguais, 1 = nada em comum."""
    return 0.5 * float(np.abs(np.asarray(p, dtype=float) - np.asarray(q, dtype=float)).sum())


def piso(p_esperado, shots: int, n_rep: int = 500, percentil: float = 95, seed: int = 0) -> float:
    """Percentil da TVD entre uma amostra de `shots` medições e a distribuição esperada.

    É quanto a medição "erra por acaso" mesmo sem trojan. No autoteste, o usuário
    compara o que mediu com a saída esperada (calculada classicamente), então
    o piso é medido contra a distribuição exata.
    """
    rng = np.random.default_rng(seed)
    valores = [tvd(amostrar(p_esperado, shots, rng), p_esperado) for _ in range(n_rep)]
    return float(np.percentile(valores, percentil))


def revela(p_golden, p_infectado, limiar: float) -> bool:
    """True se o trojan muda a saída mais do que o piso de ruído."""
    return tvd(p_golden, p_infectado) > limiar
