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


def piso_bootstrap(
    freq,
    shots: int,
    n_rep: int = 500,
    percentil: float = 95,
    seed: int = 0,
    referencia=None,
) -> float:
    """Piso de ruído no simulador com ruído, por reamostragem (bootstrap).

    `freq` são as frequências do golden medidas no simulador com ruído. Sorteia lotes de
    `shots` medições dessa distribuição e devolve o percentil da TVD:
    - sem `referencia`: entre dois lotes independentes do golden (piso da seção VI.D do artigo);
    - com `referencia`: entre um lote e a distribuição dada (por exemplo, a saída ideal do golden,
      quando o usuário compara o que mediu com a saída calculada classicamente).
    """
    rng = np.random.default_rng(seed)
    valores = []
    for _ in range(n_rep):
        lote = amostrar(freq, shots, rng)
        outro = amostrar(freq, shots, rng) if referencia is None else referencia
        valores.append(tvd(lote, outro))
    return float(np.percentile(valores, percentil))


def revela(p_golden, p_infectado, limiar: float) -> bool:
    """True se o trojan muda a saída mais do que o piso de ruído."""
    return tvd(p_golden, p_infectado) > limiar


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de confiança de Wilson (95% por padrão) para uma proporção k/n.

    Funciona bem com n pequeno e com proporções perto de 0 ou de 1, onde o intervalo
    "p ± 1,96·erro padrão" sai do intervalo [0, 1] ou fica estreito demais.
    """
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    meia = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, float(centro - meia)), min(1.0, float(centro + meia)))
