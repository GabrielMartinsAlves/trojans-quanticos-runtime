"""Figuras do ambiente com ruído, a partir de results/ruido_<shots>.csv e results/piso_ruido_<shots>.csv.

- results/fig_ruido_revela_<shots> (SVG e PDF): fração de variantes reveladas em alguma das 4 condições
  (entrada |0...0> ou |+>^n, base Z ou X), no simulador ideal e com ruído, por família e porta,
  com as contagens (k/n) e o nível de falso alarme com ruído, 1 - (1 - f)^4, com f medido nas
  réplicas (results/falso_alarme_replicas_<shots>.csv) ou, se não houver réplicas, f = 5%;
- results/fig_ruido_piso_<shots> (SVG e PDF): quanto o ruído afasta o golden da saída ideal, comparado com o
  piso de ruído (golden x golden), em função do número de CZ depois da transpilação.

Uso: python experiments/figuras_ruido.py [--shots 1024]
"""
from __future__ import annotations

import argparse

import matplotlib
import matplotlib.ticker
from matplotlib.lines import Line2D

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from comum import CHAVE, RESULTADOS, salvar_figura  # noqa: E402


plt.rcParams.update({
    "text.usetex": False,
    "font.family": "serif",
    "font.serif": ["STIXGeneral"],
    "font.size": 10,
    "axes.labelsize": 10,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
})

# Paleta e tinta do gráfico.
SERIE_1 = "#0d56af"  # ideal / distorção
SERIE_2 = "#cc7400"  # com ruído / piso
SUPERFICIE = "#ffffff"
TINTA = "#000000"
TINTA_2 = "#000000"
GRADE = "#e1e0d9"
RUIDO = "#0d56af"
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
    arquivo = RESULTADOS / f"falso_alarme_replicas_{shots}.csv"
    if arquivo.exists():
        fa = pd.read_csv(arquivo)
        f = float(fa[fa.entrada == "todas"].taxa.iloc[0])
        return 1 - (1 - f) ** 4, "medido nas réplicas"
    return FALSO_ALARME_TEORICO, "teórico"

FAMILIAS = {"reversivel": "Reversíveis", "oraculo": "Oráculos", "emaranhamento": "Emaranhamento"}
PORTAS = {"x": "X", "h": "H", "z": "Z", "t": "T", "rz_pi16": "RZ(π/16)"}


def estilo(ax) -> None:
    ax.set_facecolor(SUPERFICIE)
    #ax.tick_params(colors=TINTA_2, labelsize=8, length=0)
    for spine in ax.spines.values():
        spine.set_color(TINTA)
        #spine.set_linewidth(0.2)
        spine.set_visible(True)
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
    salvar_figura(fig, f"fig_ruido_revela_{shots}", dpi=300, facecolor=SUPERFICIE)
    plt.close(fig)


def fig_piso(pisos: pd.DataFrame, shots: int) -> None:
    c = pisos.groupby(["familia", "circuito"]).agg(
        cz=("cz", "first"), distorcao=("tvd_ruido_vs_ideal", "mean"), piso=("piso_ruido", "mean")
    ).reset_index()

    fig, ax = plt.subplots(figsize=(4, 3.0), facecolor=SUPERFICIE)
    estilo(ax)
    
    ax.set_xscale("log")
    #ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    for i, r in c.iterrows():
        ax.plot([r.cz, r.cz], [r.piso, r.distorcao], color=RUIDO, linewidth=0.8, zorder=1, linestyle='dotted')
    ax.scatter(c.cz, c.piso, marker='D', s=12, color=SERIE_2, edgecolor=SUPERFICIE, linewidth=0.5, zorder=3,
               label=f"Piso: golden × golden (p95, {shots} shots)")
    ax.scatter(c.cz, c.distorcao, s=20, color=SERIE_1, edgecolor=SUPERFICIE, linewidth=0.5, zorder=3,
               label="Golden com ruído × ideal")
    
    for nome in ("alu-v2_31", "bv_8", "deutsch_n2"):
        r = c[c.circuito == nome].iloc[0]

        direita = r.cz > np.sqrt(ax.get_xlim()[0] * ax.get_xlim()[1])
        acima = r.distorcao > 0.85 * ax.get_ylim()[1]

        ax.annotate(
            nome,
            (r.cz, r.distorcao),
            xytext=(
                -2 if direita else 2,
                -4 if acima else 4
            ),
            textcoords="offset points",
            ha="right" if direita else "left",
            va="top" if acima else "bottom",
            fontsize=7,
            color=TINTA_2,
        )
        
    ax.set_xlabel("Portas CZ depois da transpilação", fontsize=8, color=TINTA_2)
    ax.set_ylabel("TVD (média das 4 condições)", fontsize=8, color=TINTA_2)
    ax.set_ylim(0, None)
    ax.set_yticks([t for t in ax.get_yticks() if not np.isclose(t, 0) and t <= ax.get_ylim()[1]])
        
    ax.legend(
        frameon=False,
        fontsize=7,
        labelcolor=TINTA,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.15),
        ncol=2,
        columnspacing=2.0,
        handletextpad=0.1,
    )
    

    fig.subplots_adjust(
        left=0.16,
        right=0.97,
        bottom=0.17,
        top=0.78,
    )

    salvar_figura(
        fig,
        f"fig_ruido_piso_{shots}",
        dpi=300,
        facecolor=SUPERFICIE,
        bbox_inches="tight",
        pad_inches=0.03,
    )
    plt.close(fig)


def fig_piso_dispersao(pisos: pd.DataFrame, shots: int) -> None:
    c = pisos.groupby(["familia", "circuito"]).agg(
        cz=("cz", "first"),
        distorcao=("tvd_ruido_vs_ideal", "mean"),
        piso=("piso_ruido", "mean")
    ).reset_index()

    fig, ax = plt.subplots(figsize=(5, 4.0), facecolor=SUPERFICIE)
    estilo(ax)

    # Limites iguais nos dois eixos para preservar a diagonal y = x
    limite = max(c["piso"].max(), c["distorcao"].max()) * 1.08
    limite = max(limite, 0.01)

    ax.set_xlim(0, limite)
    ax.set_ylim(0, limite)

    # Linha de referência: distorção = piso de ruído
    ax.plot(
        [0, limite], [0, limite],
        color=RUIDO,
        linewidth=0.9,
        linestyle="dotted",
        zorder=1,
        label="Distorção = piso"
    )

    # Dispersão
    ax.scatter(
        c.piso,
        c.distorcao,
        s=20,
        color=SERIE_1,
        edgecolor=SUPERFICIE,
        linewidth=0.5,
        zorder=3,
        label="Circuitos"
    )

    # Identificação de circuitos selecionados
    for nome in ("alu-v2_31", "bv_8", "deutsch_n2"):
        selecionado = c[c.circuito == nome]

        if selecionado.empty:
            continue

        r = selecionado.iloc[0]

        ax.annotate(
            nome,
            (r.piso, r.distorcao),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=7,
            color=TINTA_2,
        )

    # Rótulos dos eixos
    ax.set_xlabel("Piso de ruído (TVD)", fontsize=8, color=TINTA_2)
    ax.set_ylabel("Distorção em relação ao ideal (TVD)", fontsize=8, color=TINTA_2)

    # Remove o zero dos ticks, mantendo a origem
    ax.set_xticks([t for t in ax.get_xticks() if not np.isclose(t, 0)])
    ax.set_yticks([t for t in ax.get_yticks() if not np.isclose(t, 0)])
    
    ax.legend(
        frameon=False,
        fontsize=7,
        labelcolor=TINTA,
        loc="upper left",
        bbox_to_anchor=(0, 1.15),
    )

    fig.subplots_adjust(
        left=0.16,
        right=0.97,
        bottom=0.17,
        top=0.78,
    )

    salvar_figura(
        fig,
        f"fig_ruido_dispersao_{shots}",
        dpi=300,
        facecolor=SUPERFICIE,
        bbox_inches="tight",
        pad_inches=0.03,
    )
    plt.close(fig)


def main(shots: int = 1024) -> None:
    tab = pd.read_csv(RESULTADOS / f"ruido_{shots}.csv")
    pisos = pd.read_csv(RESULTADOS / f"piso_ruido_{shots}.csv")
    fig_revela(tab, shots)
    fig_piso(pisos, shots)
    fig_piso_dispersao(pisos, shots)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=int, default=1024)
    main(parser.parse_args().shots)
