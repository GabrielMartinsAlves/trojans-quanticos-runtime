"""Resume results/ruido_<shots>.csv e results/piso_ruido_<shots>.csv: o que muda do ideal para o com ruído.

Gera:
- results/resumo_piso_ruido_<shots>.csv: piso médio por família, base e entrada;
- results/resumo_ruido_<shots>.csv: fração de variantes reveladas por família, porta, entrada e base,
  no ideal (mesmo número de shots), com ruído (referência: golden com ruído) e com ruído
  comparando com a saída ideal;
- results/resumo_ruido_variantes_<shots>.csv: por família e porta, fração de variantes reveladas por
  alguma das 4 condições (entrada |0...0> ou |+>^n, base Z ou X), no ideal e com ruído, com as
  contagens (k de n) e o intervalo de confiança de Wilson (95%) de cada fração.

Esta é uma rodada só (réplica 0). Para a variação entre rodadas, ver experiments/replicas_ruido.py.

Uso: python experiments/consolidar_ruido.py [--shots 1024]
"""
from __future__ import annotations

import argparse

import pandas as pd
from comum import CHAVE, RESULTADOS

from trojans import metricas

REVELA = ["revela_ideal", "revela_ruido", "revela_vs_ideal"]


def main(shots: int = 1024) -> None:
    pisos = pd.read_csv(RESULTADOS / f"piso_ruido_{shots}.csv")
    tab = pd.read_csv(RESULTADOS / f"ruido_{shots}.csv")
    print(f"{len(tab)} linhas, {tab.groupby(CHAVE).ngroups} variantes em {tab.circuito.nunique()} circuitos\n")

    piso = (
        pisos.groupby(["familia", "base", "entrada"])[
            ["piso_ideal", "piso_ruido", "piso_vs_ideal", "tvd_ruido_vs_ideal", "cz"]
        ]
        .mean()
        .round(3)
    )
    print("Piso médio (ideal | ruído: golden x golden | ruído: golden x ideal) e distorção do golden")
    print(piso.to_string(), "\n")

    tab["perdida_pelo_ruido"] = tab.revela_ideal & ~tab.revela_ruido
    tab["so_com_ruido"] = ~tab.revela_ideal & tab.revela_ruido
    cols = REVELA + ["perdida_pelo_ruido", "so_com_ruido"]
    cond = tab.groupby(["familia", "porta", "entrada", "base"])[cols].mean().round(2)
    print("Fração revelada por condição")
    print(cond.to_string(), "\n")

    # Por variante: revelada em alguma das 4 condições (entrada x base)?
    v = tab.groupby(CHAVE)[REVELA].any()
    zeros_z = tab[(tab.entrada == "zeros") & (tab.base == "z")].set_index(CHAVE)
    v["base_trabalho_ideal"] = zeros_z.revela_ideal  # o que o trabalho-base mediu
    v["base_trabalho_ruido"] = zeros_z.revela_ruido
    v = v.reset_index()
    var_cols = ["base_trabalho_ideal", "base_trabalho_ruido"] + REVELA
    var = v.groupby(["familia", "porta"])[var_cols].mean().round(2)
    var.loc[("todas", ""), :] = v[var_cols].mean().round(2)
    # Contagens e intervalo de Wilson (95%) para o ideal e para o ruído (alguma das 4 condições).
    grupos = [((f, p), g) for (f, p), g in v.groupby(["familia", "porta"])] + [(("todas", ""), v)]
    for (f, p), g in grupos:
        var.loc[(f, p), "n"] = len(g)
        for col in ("revela_ideal", "revela_ruido"):
            k = int(g[col].sum())
            inf, sup = metricas.wilson(k, len(g))
            var.loc[(f, p), f"{col}_k"] = k
            var.loc[(f, p), f"{col}_ic_inf"] = round(inf, 2)
            var.loc[(f, p), f"{col}_ic_sup"] = round(sup, 2)
    contagens = ["n", "revela_ideal_k", "revela_ruido_k"]
    var[contagens] = var[contagens].astype(int)
    print("Fração de variantes reveladas: só |0...0> na base Z | alguma das 4 condições (com k, n e IC 95%)")
    print(var.to_string())

    piso.to_csv(RESULTADOS / f"resumo_piso_ruido_{shots}.csv")
    cond.to_csv(RESULTADOS / f"resumo_ruido_{shots}.csv")
    var.to_csv(RESULTADOS / f"resumo_ruido_variantes_{shots}.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=int, default=1024)
    main(parser.parse_args().shots)
