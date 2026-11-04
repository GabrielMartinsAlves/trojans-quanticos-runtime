"""Resume results/ruido_<shots>.csv e results/piso_ruido_<shots>.csv: o que muda do ideal para o com ruído.

Gera:
- results/resumo_piso_ruido_<shots>.csv: piso médio por família, base e entrada;
- results/resumo_ruido_<shots>.csv: fração de variantes reveladas por família, porta, entrada e base,
  no ideal (mesmo número de shots), com ruído (referência: golden com ruído) e com ruído
  comparando com a saída ideal;
- results/resumo_ruido_variantes_<shots>.csv: por família e porta, fração de variantes reveladas por
  alguma das 4 condições (entrada |0...0> ou |+>^n, base Z ou X), no ideal e com ruído.

Uso: python experiments/consolidar_ruido.py [--shots 1000]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[1]
CHAVE = ["familia", "circuito", "porta", "posicao", "papel"]
REVELA = ["revela_ideal", "revela_ruido", "revela_vs_ideal"]


def main(shots: int = 1000) -> None:
    pisos = pd.read_csv(RAIZ / "results" / f"piso_ruido_{shots}.csv")
    tab = pd.read_csv(RAIZ / "results" / f"ruido_{shots}.csv")
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
    print("Fração de variantes reveladas: só |0...0> na base Z | alguma das 4 condições")
    print(var.to_string())

    piso.to_csv(RAIZ / "results" / f"resumo_piso_ruido_{shots}.csv")
    cond.to_csv(RAIZ / "results" / f"resumo_ruido_{shots}.csv")
    var.to_csv(RAIZ / "results" / f"resumo_ruido_variantes_{shots}.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=int, default=1000)
    main(parser.parse_args().shots)
