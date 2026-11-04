"""Experimento no simulador ideal: gera results/ideal.csv.

Para cada circuito golden, porta, posição e papel do qubit:
- mede o impacto (TVD) com a entrada |0...0>, com |+>^n e com cada estado da base;
- nas bases de medição Z e X;
- calcula a fração p de estados que revelam o trojan e o k95 do autoteste,
  tanto para entradas da base Z (|j>) quanto da base X (H^n|j>, superposições).

Usa os circuitos de data/selecao.csv (gerado por experiments/selecionar.py).
Com a opção --exemplos, usa os circuitos pequenos de src/trojans/exemplos.py.
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # console do Windows não mostra o desenho dos circuitos sem isso

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from trojans import autoteste, circuitos, exemplos, insercao, metricas, simulacao  # noqa: E402

SHOTS = 1000  # medições por execução no autoteste
SELECAO = RAIZ / "data" / "selecao.csv"
DATASET = RAIZ / "data" / "raw" / "IC-QT-2026"


def goldens(usar_exemplos: bool = False):
    """Lista de (família, golden)."""
    if usar_exemplos:
        return [
            ("reversivel", exemplos.somador_completo()),
            ("oraculo", exemplos.bernstein_vazirani("101")),
            ("oraculo", exemplos.deutsch_jozsa(3, "balanceado")),
            ("emaranhamento", exemplos.ghz(4)),
        ]
    selecao = pd.read_csv(SELECAO)
    lista = []
    for r in selecao.itertuples():
        circ = circuitos.carregar(DATASET / r.caminho)
        circ.name = Path(r.arquivo).stem
        lista.append((r.familia, circ))
    return lista


def main() -> None:
    usar_exemplos = "--exemplos" in sys.argv
    saida = RAIZ / "results" / ("ideal_exemplos.csv" if usar_exemplos else "ideal.csv")
    linhas = []
    for familia, golden in goldens(usar_exemplos):
        print(f"rodando {familia}/{golden.name} ({golden.num_qubits} qubits)", flush=True)
        for base in simulacao.BASES:
            # Saídas esperadas do golden e piso de ruído de cada entrada.
            P_g = simulacao.distribuicoes_base(golden, base)
            pisos = np.array([metricas.piso(P_g[:, j], SHOTS) for j in range(P_g.shape[1])])
            Q_g = simulacao.distribuicoes_base(golden, base, entrada="x")
            pisos_x = np.array([metricas.piso(Q_g[:, j], SHOTS) for j in range(Q_g.shape[1])])
            piso_mais = pisos_x[0]  # coluna 0 da base X é |+>^n

            for porta, posicao, papel in itertools.product(insercao.PORTAS, insercao.POSICOES, insercao.PAPEIS):
                resultado = insercao.inserir(golden, porta, posicao, papel)
                if resultado is None:
                    continue
                infectado, meta = resultado

                P_i = simulacao.distribuicoes_base(infectado, base)
                tvd_base = np.array([metricas.tvd(P_g[:, j], P_i[:, j]) for j in range(P_g.shape[1])])
                p_revela = float(np.mean(tvd_base > pisos))
                Q_i = simulacao.distribuicoes_base(infectado, base, entrada="x")
                tvd_x = np.array([metricas.tvd(Q_g[:, j], Q_i[:, j]) for j in range(Q_g.shape[1])])
                p_revela_x = float(np.mean(tvd_x > pisos_x))
                tvd_mais = tvd_x[0]

                linhas.append(
                    {
                        "familia": familia,
                        "circuito": golden.name,
                        "n_qubits": golden.num_qubits,
                        "base": base,
                        **meta,
                        "tvd_zeros": tvd_base[0],
                        "revela_zeros": bool(tvd_base[0] > pisos[0]),
                        "tvd_mais": tvd_mais,
                        "revela_mais": bool(tvd_mais > piso_mais),
                        "tvd_base_media": float(tvd_base.mean()),
                        "p_revela_base": p_revela,
                        "k95_base": autoteste.k95(p_revela),
                        "tvd_base_x_media": float(tvd_x.mean()),
                        "p_revela_base_x": p_revela_x,
                        "k95_base_x": autoteste.k95(p_revela_x),
                    }
                )

    saida.parent.mkdir(exist_ok=True)
    tabela = pd.DataFrame(linhas)
    tabela.to_csv(saida, index=False)
    print(f"{len(tabela)} linhas em {saida.relative_to(RAIZ)}")
    resumo = tabela.groupby(["familia", "base", "porta"])[["revela_zeros", "p_revela_base", "p_revela_base_x"]].mean()
    print("\nFração revelada: só |0...0> | entradas da base Z | entradas da base X")
    print(resumo.round(2).to_string())


if __name__ == "__main__":
    main()
