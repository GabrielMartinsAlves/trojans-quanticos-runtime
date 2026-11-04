"""Resume results/ideal.csv em tabelas por família, porta, posição e papel do qubit.

Para cada variante infectada (circuito, porta, posição, papel), compara quatro estratégias de teste:
- base_trabalho: entrada |0...0> medida na base Z (o que o trabalho-base fez);
- zeros_x: entrada |0...0> medida na base X;
- entradas_z: algum estado da base computacional revela, medindo em Z ou em X;
- entradas_x: algum estado da base X (superposição) revela, medindo em Z ou em X.

Gera results/resumo_estrategias.csv, results/resumo_posicao_papel.csv e results/resumo_k95.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[1]
CHAVE = ["familia", "circuito", "porta", "posicao", "papel"]


def por_variante(tab: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por variante infectada, juntando as medições nas bases Z e X."""
    z = tab[tab.base == "z"].set_index(CHAVE)
    x = tab[tab.base == "x"].set_index(CHAVE)
    v = pd.DataFrame(index=z.index)
    v["base_trabalho"] = z.revela_zeros
    v["zeros_x"] = x.revela_zeros
    v["entradas_z"] = (z.p_revela_base > 0) | (x.p_revela_base > 0)
    v["entradas_x"] = (z.p_revela_base_x > 0) | (x.p_revela_base_x > 0)
    v["alguma"] = v[["base_trabalho", "zeros_x", "entradas_z", "entradas_x"]].any(axis=1)
    v["perdida_pelo_trabalho"] = v.alguma & ~v.base_trabalho
    # Melhor fração p de entradas que revelam, entre as 4 combinações (entrada Z/X x medição Z/X).
    v["p_melhor"] = np.maximum.reduce(
        [z.p_revela_base, x.p_revela_base, z.p_revela_base_x, x.p_revela_base_x]
    )
    v["k95_melhor"] = v.p_melhor.map(lambda p: np.inf if p <= 0 else int(np.ceil(np.log(0.05) / np.log(1 - p))) if p < 1 else 1)
    return v.reset_index()


def main() -> None:
    tab = pd.read_csv(RAIZ / "results" / "ideal.csv")
    v = por_variante(tab)
    print(f"{len(v)} variantes infectadas em {v.circuito.nunique()} circuitos\n")

    cols = ["base_trabalho", "zeros_x", "entradas_z", "entradas_x", "alguma", "perdida_pelo_trabalho"]
    estr = v.groupby(["familia", "porta"])[cols].mean().round(2)
    estr.loc[("todas", ""), :] = v[cols].mean().round(2)
    print("Fração de variantes reveladas por estratégia")
    print(estr.to_string(), "\n")

    pos = v.groupby(["familia", "posicao", "papel"])[["base_trabalho", "alguma"]].mean().round(2)
    print("Fração revelada por posição e papel do qubit")
    print(pos.to_string(), "\n")

    reveladas = v[v.alguma]
    k95 = reveladas.groupby(["familia", "porta"]).k95_melhor.agg(["count", "median", "max"])
    print("k95 com a melhor estratégia (só variantes que alguma estratégia revela)")
    print(k95.to_string())

    estr.to_csv(RAIZ / "results" / "resumo_estrategias.csv")
    pos.to_csv(RAIZ / "results" / "resumo_posicao_papel.csv")
    k95.to_csv(RAIZ / "results" / "resumo_k95.csv")


if __name__ == "__main__":
    main()
