"""Autoteste em tempo de execução: quantos testes até encontrar o trojan."""
from __future__ import annotations

import math


def prob_deteccao(p: float, k: int) -> float:
    """Chance de pelo menos um entre k testes revelar o trojan, se cada um revela com prob. p."""
    return 1 - (1 - p) ** k


def k95(p: float, alvo: float = 0.95) -> float:
    """Menor k com prob_deteccao(p, k) >= alvo. Infinito se nenhuma entrada revela o trojan."""
    if p <= 0:
        return math.inf
    if p >= 1:
        return 1
    return math.ceil(math.log(1 - alvo) / math.log(1 - p))
