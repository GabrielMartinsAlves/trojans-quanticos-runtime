"""Gráfico de floresta da regressão logística (GEE), a partir de results/hipoteses_regressao.csv.

Não reajusta o modelo: apenas lê a tabela de razões de chances (OR, IC 95%) salva por
testes_hipoteses.py e desenha o gráfico, com a mesma estilização de figuras_ruido.py.

A porta H tem razão de chances várias ordens de grandeza acima dos demais fatores e distorceria a
escala. Por isso há dois arquivos:

- results/fig_regressao_porta.svg: só as portas, com eixo quebrado (H num painel à direita);
- results/fig_regressao_outros.svg: posição, papel, entrada, base e família, um quadro por fator,
  empilhados e com o mesmo eixo x.

Uso: python experiments/figura_regressao.py
"""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import NullFormatter, NullLocator  # noqa: E402
from matplotlib.transforms import blended_transform_factory  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
ALFA = 0.05

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

# Paleta e tinta (mesmas de figuras_ruido.py).
SERIE_1 = "#0d56af"   # efeito significativo
SUPERFICIE = "#fcfcfb"
TINTA = "#000000"
TINTA_2 = "#000000"
TINTA_3 = "#898781"   # efeito não significativo / linha de referência
GRADE = "#e1e0d9"

# Categorias de referência da regressão (iguais às de testes_hipoteses.py).
REFERENCIA = {"porta": "x", "posicao": "meio", "papel": "ativo", "entrada": "zeros", "base": "z", "familia": "reversivel"}

ROTULOS = {
    "porta": ("Porta", {"h": "H", "t": "T", "x": "X", "z": "Z", "rz_pi16": "RZ(π/16)"}),
    "posicao": ("Posição", {"inicio": "início", "meio": "meio", "fim": "fim"}),
    "papel": ("Papel", {"ativo": "ativo", "ocioso": "ocioso"}),
    "entrada": ("Entrada", {"zeros": "|0…0⟩", "mais": "|+⟩ⁿ", "base_z": "estados da base Z", "base_x": "estados da base X"}),
    "base": ("Base", {"z": "Z", "x": "X"}),
    "familia": ("Família", {"reversivel": "reversíveis", "oraculo": "oráculos", "emaranhamento": "emaranhamento"}),
}

# Termos que ficam no painel da direita (escala própria).
PAINEL_DIREITO = {("Porta", "H")}


def estilo(ax) -> None:
    ax.set_facecolor(SUPERFICIE)
    for spine in ax.spines.values():
        spine.set_color(TINTA)
        spine.set_visible(True)
    ax.set_axisbelow(True)


def ler_tabela(caminho: Path) -> list[tuple[str, str, pd.Series]]:
    """Lê o CSV e devolve (fator, nível, linha) para cada termo com erro-padrão definido."""
    tab = pd.read_csv(caminho, index_col=0)
    linhas = []
    for termo, r in tab.drop(index="Intercept", errors="ignore").iterrows():
        if pd.isna(r.erro_padrao):
            continue  # nível sem variação própria (ex.: estados da base Z se comportam como |0...0>)
        m = re.match(r"C\((\w+).*\)\[T\.(.+)\]", str(termo))
        if m is None:
            continue
        nome, niveis = ROTULOS[m.group(1)]
        linhas.append((nome, niveis.get(m.group(2), m.group(2)), r))
    return linhas


def marcas_eixo(vmin: float, vmax: float, so_potencias: bool = False) -> list[float]:
    """Marcas 1-2-5 x 10^k (ou só 10^k) dentro de [vmin, vmax], para eixo logarítmico."""
    base = (1,) if so_potencias else (1, 2, 5)
    candidatas = [m * 10.0**k for k in range(-4, 6) for m in base]
    marcas = [t for t in candidatas if vmin <= t <= vmax]
    return marcas if len(marcas) >= 2 else [vmin, vmax]


def ajustar_as_marcas(vmin: float, vmax: float) -> tuple[float, float]:
    """Estende [vmin, vmax] até as marcas 1-2-5 mais próximas, para o eixo ter pelo menos 3 marcas."""
    cand = sorted(m * 10.0**k for k in range(-4, 6) for m in (1, 2, 5))
    return max(t for t in cand if t <= vmin), min(t for t in cand if t >= vmax)


def limites(valores: list[float], folga: float = 1.25) -> tuple[float, float]:
    v = [x for x in valores if np.isfinite(x) and x > 0]
    return min(v) / folga, max(v) * folga


def fig_quadros(linhas: list[tuple[str, str, pd.Series]], fatores: list[str], destino: Path) -> None:
    """Um quadro por fator, empilhados e com o mesmo eixo x; o nome do fator e a categoria de
    referência ficam num cabeçalho logo acima de cada quadro.

    Se algum termo estiver em PAINEL_DIREITO, o eixo é quebrado: esse termo vai para um painel à
    direita, em escala própria, e o resto fica no painel principal.
    """
    nomes = {f: ROTULOS[f][0] for f in fatores}
    grupos = {nomes[f]: [(n, r) for nome, n, r in linhas if nome == nomes[f]] for f in fatores}
    referencia = {nomes[f]: ROTULOS[f][1][REFERENCIA[f]] for f in fatores}
    todas = [r for g in grupos.values() for _, r in g]
    no_direito = lambda nome, nivel: (nome, nivel) in PAINEL_DIREITO  # noqa: E731
    quebrar = any(no_direito(nome, n) for nome, g in grupos.items() for n, _ in g)

    esq = [r for nome, g in grupos.items() for n, r in g if not no_direito(nome, n)]
    dir_ = [r for nome, g in grupos.items() for n, r in g if no_direito(nome, n)]
    # Painel principal em escala log, com limites e marcas em potências de 2 (0,25; 0,5; 1; 2; 4...),
    # colados aos dados para não sobrar espaço vazio.
    valores = [x for r in esq for x in (r.OR_ic_inf, r.OR_ic_sup)] + [1.0]
    lim1 = (2.0 ** np.floor(np.log2(min(valores))), 2.0 ** np.ceil(np.log2(max(valores))))
    lim2 = limites([x for r in dir_ for x in (r.OR_ic_inf, r.OR_ic_sup, r.OR)], folga=1.8) if quebrar else None

    ha_sig = any(r.p < ALFA for r in todas)
    ha_nsig = any(r.p >= ALFA for r in todas)
    linhas_leg = 2 if (int(ha_sig) + int(ha_nsig) + 1) == 3 else 1

    # Folga no topo do quadro com painel direito, para o valor da OR caber acima do ponto.
    topo_y = {nome: len(g) - 0.4 + (0.6 if any(no_direito(nome, n) for n, _ in g) else 0) for nome, g in grupos.items()}
    alturas = [topo_y[nome] + 0.6 for nome in grupos]
    LINHA, CABECALHO, FOLGA = 0.2, 0.17, 0.10  # polegadas
    topo_in = 0.10 + 0.15 * linhas_leg + CABECALHO
    base_in, largura = 0.38, 5.2
    entre = CABECALHO + FOLGA
    medio = LINHA * np.mean(alturas)
    altura = topo_in + LINHA * sum(alturas) + entre * (len(grupos) - 1) + base_in

    fig = plt.figure(figsize=(largura, altura), facecolor=SUPERFICIE)
    gs = fig.add_gridspec(len(grupos), 2 if quebrar else 1, height_ratios=alturas,
                          width_ratios=[3, 1] if quebrar else None, hspace=entre / medio, wspace=0.12,
                          left=0.22, right=0.975, bottom=base_in / altura, top=1 - topo_in / altura)
    eixos, direitos = [], {}
    for k, nome in enumerate(grupos):
        ax = fig.add_subplot(gs[k, 0], sharex=eixos[0] if eixos else None)
        eixos.append(ax)
        if quebrar and any(no_direito(nome, n) for n, _ in grupos[nome]):
            direitos[nome] = fig.add_subplot(gs[k, 1], sharey=ax)
    ultimo = eixos[-1]

    for ax, (nome, g) in zip(eixos, grupos.items()):
        n = len(g)
        par = [ax] + ([direitos[nome]] if nome in direitos else [])
        for a in par:
            estilo(a)
            a.set_xscale("log")
            a.xaxis.set_minor_locator(NullLocator())
            a.xaxis.set_minor_formatter(NullFormatter())
            a.set_ylim(-0.6, topo_y[nome])
        ax.set_xlim(*lim1)
        ax.set_yticks(range(n))
        ax.set_yticklabels([nivel for nivel, _ in g][::-1], fontsize=7, color=TINTA_2)
        ax.axvline(1, color=TINTA_3, linestyle=(0, (3, 2)), linewidth=1, zorder=1.5)
        for yi, (nivel, r) in zip(range(n)[::-1], g):
            cor = SERIE_1 if r.p < ALFA else TINTA_3
            na_direita = no_direito(nome, nivel)
            for a in par:
                a.plot([r.OR_ic_inf, r.OR_ic_sup], [yi, yi], color=cor, linewidth=1.2, zorder=2)
                a.scatter(r.OR, yi, s=20, color=cor, edgecolor=SUPERFICIE, linewidth=0.5, zorder=3)
            if na_direita:
                direitos[nome].text(r.OR, yi + 0.4, f"{r.OR:.0f}", ha="center", va="bottom", fontsize=6.5, color=TINTA_2)
        ax.tick_params(labelbottom=(ax is ultimo), bottom=(ax is ultimo))

    ticks1 = [2.0 ** k for k in range(int(np.log2(lim1[0])), int(np.log2(lim1[1])) + 1)]
    ultimo.set_xticks(ticks1)
    ultimo.set_xticklabels([f"{t:g}".replace(".", ",") for t in ticks1], fontsize=7)

    # Eixo quebrado: painel direito em potências de 10, sem moldura do lado esquerdo.
    for nome, ax2 in direitos.items():
        ax1 = eixos[list(grupos).index(nome)]
        ax2.set_xlim(*lim2)
        ticks2 = marcas_eixo(*lim2, so_potencias=True)
        ax2.set_xticks(ticks2)
        ax2.set_xticklabels([f"{t:g}".replace(".", ",") for t in ticks2], fontsize=7)
        ax2.tick_params(left=False, labelleft=False)
        ax1.spines["right"].set_visible(False)
        ax2.spines["left"].set_visible(False)
        # Marcas da quebra: 45° de verdade (tamanho fixo em polegadas, não em fração do eixo).
        kw = dict(color=TINTA, clip_on=False, linewidth=1.0)
        for a_, x0 in ((ax1, 1.0), (ax2, 0.0)):
            pos = a_.get_position()
            dx, dy = 0.06 / (pos.width * largura), 0.06 / (pos.height * altura)
            for y0 in (0.0, 1.0):
                a_.plot((x0 - dx, x0 + dx), (y0 - dy, y0 + dy), transform=a_.transAxes, **kw)

    # Cabeçalho de cada quadro: nome do fator (negrito) e, ao lado, a categoria de referência.
    renderer = fig.canvas.get_renderer()
    for ax, nome in zip(eixos, grupos):
        t = ax.annotate(nome, xy=(0, 1), xycoords="axes fraction", xytext=(0, 3), textcoords="offset points",
                        ha="left", va="bottom", fontsize=7, fontweight="bold", color=TINTA)
        largura_pt = t.get_window_extent(renderer).width * 72 / fig.dpi
        ax.annotate(f"ref.: {referencia[nome]}", xy=(0, 1), xycoords="axes fraction",
                    xytext=(largura_pt + 5, 3), textcoords="offset points",
                    ha="left", va="bottom", fontsize=6, color=TINTA_3)

    alcas = []
    if ha_sig:
        alcas.append(Line2D([0], [0], color=SERIE_1, marker="o", markersize=4, linewidth=1.2,
                            label=f"Significativo (valor-p < {ALFA:.2f})".replace(".", ",")))
    if ha_nsig:
        alcas.append(Line2D([0], [0], color=TINTA_3, marker="o", markersize=4, linewidth=1.2,
                            label=f"Não significativo (valor-p ≥ {ALFA:.2f})".replace(".", ",")))
    alcas.append(Line2D([0], [0], color=TINTA_3, linestyle=(0, (3, 2)), linewidth=1, label="OR = 1 (sem efeito)"))
    fig.legend(handles=alcas, loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False,
               fontsize=6.5, labelcolor=TINTA, columnspacing=1.0, handletextpad=0.4, handlelength=1.6)

    x1 = (direitos[next(iter(direitos))] if direitos else ultimo).get_position().x1
    rotulo = "Razão de chances de ser visível (IC 95%, escala log" + ("; eixo quebrado)" if quebrar else ")")
    fig.text((ultimo.get_position().x0 + x1) / 2, 0.0, rotulo, ha="center", va="bottom", fontsize=7, color=TINTA_2)
    fig.savefig(destino, dpi=300, facecolor=SUPERFICIE, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def main() -> None:
    linhas = ler_tabela(RAIZ / "results" / "hipoteses_regressao.csv")
    # A porta H (OR na casa das centenas) fica num gráfico próprio, com eixo quebrado;
    # os demais fatores ficam juntos, em quadros empilhados com o mesmo eixo x.
    fig_quadros(linhas, ["porta"], RAIZ / "results" / "fig_regressao_porta.svg")
    fig_quadros(linhas, ["posicao", "papel", "entrada", "base", "familia"], RAIZ / "results" / "fig_regressao_outros.svg")


if __name__ == "__main__":
    main()