"""Figuras do ambiente com ruído, a partir de results/ruido_<shots>.csv e results/piso_ruido_<shots>.csv.

- results/fig_ruido_revela_<shots>.png: fração de variantes reveladas em alguma das 4 condições
  (entrada |0...0> ou |+>^n, base Z ou X), no simulador ideal e com ruído, por família e porta,
  com as contagens (k/n) e o nível de falso alarme com ruído, 1 - (1 - f)^4, com f medido nas
  réplicas (results/falso_alarme_replicas_<shots>.csv) ou, se não houver réplicas, f = 5%;
- results/fig_ruido_piso_<shots>.png: quanto o ruído afasta o golden da saída ideal, comparado com o
  piso de ruído (golden x golden), em função do número de CZ depois da transpilação.

Uso: python experiments/figuras_ruido.py [--shots 1024]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
CHAVE = ["familia", "circuito", "porta", "posicao", "papel"]

# Paleta (validada para daltonismo) e tinta do gráfico.
SERIE_1 = "#2a78d6"  # ideal / distorção
SERIE_2 = "#eb6834"  # com ruído / piso
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"
TINTA_3 = "#898781"  # linha de referência (falso alarme)

# Chance de uma variante silenciosa "aparecer" em alguma das 4 condições: 1 - (1 - f)^4, em que f é
# a taxa de falso alarme por condição. Valor teórico: f = 5% (percentil 95 do piso).
FALSO_ALARME_TEORICO = 1 - 0.95**4


def nivel_falso_alarme(shots: int) -> tuple[float, str]:
    """Nível de falso alarme por variante e a origem do número.

    Usa a taxa por condição medida nas réplicas (results/falso_alarme_replicas_<shots>.csv,
    gerado por replicas_ruido.py) quando existe; senão, o valor teórico.
    """
    arquivo = RAIZ / "results" / f"falso_alarme_replicas_{shots}.csv"
    if arquivo.exists():
        fa = pd.read_csv(arquivo)
        f = float(fa[fa.entrada == "todas"].taxa.iloc[0])
        return 1 - (1 - f) ** 4, "medido nas réplicas"
    return FALSO_ALARME_TEORICO, "teórico"

FAMILIAS = {"reversivel": "Reversíveis", "oraculo": "Oráculos", "emaranhamento": "Emaranhamento"}
PORTAS = {"x": "X", "h": "H", "z": "Z", "t": "T", "rz_pi16": "RZ(π/16)"}


def estilo(ax) -> None:
    ax.set_facecolor(SUPERFICIE)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(EIXO)
    ax.tick_params(colors=TINTA_2, labelsize=8, length=0)
    ax.set_axisbelow(True)


def fig_revela(tab: pd.DataFrame, shots: int) -> None:
    nivel, origem = nivel_falso_alarme(shots)
    print(f"nível de falso alarme ({shots} shots): {nivel:.1%} ({origem})")
    v = tab.groupby(CHAVE)[["revela_ideal", "revela_ruido"]].any().reset_index()
    soma = v.groupby(["familia", "porta"])[["revela_ideal", "revela_ruido"]].sum()
    n = v.groupby(["familia", "porta"]).size()

    fig, eixos = plt.subplots(1, 3, figsize=(7.2, 2.7), sharey=True, facecolor=SUPERFICIE)
    y = np.arange(len(PORTAS))
    altura = 0.36
    for ax, (fam, nome) in zip(eixos, FAMILIAS.items()):
        estilo(ax)
        total = [int(n.loc[(fam, p)]) for p in PORTAS]
        k_ideal = [int(soma.loc[(fam, p), "revela_ideal"]) for p in PORTAS]
        k_ruido = [int(soma.loc[(fam, p), "revela_ruido"]) for p in PORTAS]
        ideal = [k / m for k, m in zip(k_ideal, total)]
        ruido = [k / m for k, m in zip(k_ruido, total)]
        # 2px de folga entre as barras do par.
        ax.barh(y - altura / 2, ideal, height=altura, color=SERIE_1, edgecolor=SUPERFICIE, linewidth=1,
                label="Ideal (mesmas 4 condições)")
        ax.barh(y + altura / 2, ruido, height=altura, color=SERIE_2, edgecolor=SUPERFICIE, linewidth=1,
                label=f"Com ruído ({shots} shots)")
        # Uma variante silenciosa testada em 4 condições, cada uma com 5% de falso alarme (percentil 95),
        # "aparece" por acaso em 1 - 0,95^4 das vezes. Barras com ruído perto desta linha são acaso.
        ax.axvline(nivel, color=TINTA_3, linestyle=(0, (3, 2)), linewidth=1, zorder=2.5,
                   label=f"Nível de falso alarme com ruído (≈{nivel:.0%})".replace("%", " %"))
        # Contagens em todas as barras: com n pequeno, uma variante muda vários pontos percentuais.
        for i in range(len(PORTAS)):
            for dy, val, k in ((-altura / 2, ideal[i], k_ideal[i]), (altura / 2, ruido[i], k_ruido[i])):
                ax.text(val + 0.02, y[i] + dy, f"{k}/{total[i]}", va="center", fontsize=6.5, color=TINTA_2, zorder=3,
                        bbox=dict(facecolor=SUPERFICIE, edgecolor="none", pad=0.4))
        ax.set_xlim(0, 1.25)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
        ax.set_xticklabels(["0", "25", "50", "75", "100 %"])
        ax.grid(axis="x", color=GRADE, linewidth=0.6)
        ax.set_title(f"{nome} (n = {int(n.loc[fam].iloc[0])})", fontsize=9, color=TINTA, loc="left")
    eixos[0].set_yticks(y)
    eixos[0].set_yticklabels(list(PORTAS.values()))
    eixos[0].invert_yaxis()
    fig.text(0.5, 0.01, "Variantes reveladas em alguma das 4 condições (entrada |0…0⟩ ou |+⟩ⁿ, base Z ou X); n = variantes por porta",
             ha="center", fontsize=8, color=TINTA_2)
    alcas, rotulos = eixos[0].get_legend_handles_labels()
    ordem = [1, 2, 0]  # barras primeiro, linha de falso alarme por último
    alcas, rotulos = [alcas[i] for i in ordem], [rotulos[i] for i in ordem]
    fig.legend(alcas, rotulos, loc="upper left", bbox_to_anchor=(0.07, 1.0), ncol=3, frameon=False, fontsize=8,
               labelcolor=TINTA)
    fig.tight_layout(rect=(0, 0.05, 1, 0.9))
    fig.savefig(RAIZ / "results" / f"fig_ruido_revela_{shots}.png", dpi=300, facecolor=SUPERFICIE)
    plt.close(fig)


def fig_piso(pisos: pd.DataFrame, shots: int) -> None:
    c = pisos.groupby(["familia", "circuito"]).agg(
        cz=("cz", "first"), distorcao=("tvd_ruido_vs_ideal", "mean"), piso=("piso_ruido", "mean")
    ).reset_index()

    fig, ax = plt.subplots(figsize=(3.5, 2.6), facecolor=SUPERFICIE)
    estilo(ax)
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    for i, r in c.iterrows():
        ax.plot([r.cz, r.cz], [r.piso, r.distorcao], color=GRADE, linewidth=1, zorder=1)
    ax.scatter(c.cz, c.distorcao, s=36, color=SERIE_1, edgecolor=SUPERFICIE, linewidth=1.5, zorder=3,
               label="Golden com ruído × ideal")
    ax.scatter(c.cz, c.piso, s=36, color=SERIE_2, edgecolor=SUPERFICIE, linewidth=1.5, zorder=3,
               label=f"Piso: golden × golden (p95, {shots} shots)")
    for nome in ("alu-v2_31", "bv_8", "deutsch_n2"):
        r = c[c.circuito == nome].iloc[0]
        ax.annotate(nome, (r.cz, r.distorcao), xytext=(4, 4), textcoords="offset points", fontsize=7, color=TINTA_2)
    ax.set_xlabel("Portas CZ depois da transpilação", fontsize=8, color=TINTA_2)
    ax.set_ylabel("TVD (média das 4 condições)", fontsize=8, color=TINTA_2)
    ax.set_ylim(0, None)
    ax.grid(axis="y", color=GRADE, linewidth=0.6)
    ax.legend(frameon=False, fontsize=7, labelcolor=TINTA, loc="upper left")
    fig.tight_layout()
    fig.savefig(RAIZ / "results" / f"fig_ruido_piso_{shots}.png", dpi=300, facecolor=SUPERFICIE)
    plt.close(fig)


def main(shots: int = 1024) -> None:
    tab = pd.read_csv(RAIZ / "results" / f"ruido_{shots}.csv")
    pisos = pd.read_csv(RAIZ / "results" / f"piso_ruido_{shots}.csv")
    fig_revela(tab, shots)
    fig_piso(pisos, shots)
    print(f"results/fig_ruido_revela_{shots}.png e results/fig_ruido_piso_{shots}.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=int, default=1024)
    main(parser.parse_args().shots)
