"""Réplicas do experimento com ruído: repete rodar_ruido.py com sementes diferentes.

Em rodar_ruido.py, cada variante é executada uma vez por condição, e a decisão "revelou ou não"
depende do acaso da amostragem. Aqui a mesma execução é repetida R vezes, mudando só as sementes
do simulador (amostras medidas) e do bootstrap do piso. A transpilação e o modelo de ruído são
os mesmos. A réplica 0 reproduz results/ruido_<shots>.csv.

Com isso, cada variante passa a ter uma probabilidade de detecção (fração das réplicas em que
foi revelada em alguma das 4 condições) em vez de um "sim ou não".

Saídas:
- results/ruido_replicas_<shots>.csv: uma linha por variante, base, entrada e réplica;
- results/resumo_replicas_<shots>.csv: por família e porta (e no total), a fração revelada no
  ideal, a média, o desvio-padrão e a faixa (mínimo–máximo) da fração revelada com ruído entre
  as réplicas, e as variantes com detecção robusta (reveladas em mais da metade das réplicas),
  com intervalo de Wilson;
- results/falso_alarme_replicas_<shots>.csv: taxa de falso alarme por condição, juntando as réplicas.

Uso:
  python experiments/replicas_ruido.py [--shots 1024] [--replicas 10]   # ~2 min por réplica
  python experiments/replicas_ruido.py --shots 1024 --resumir           # só refaz os resumos
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "experiments"))

from rodar_ideal import goldens  # noqa: E402
from rodar_ruido import BACKEND, SHOTS, avaliar, preparar_golden, semente_simulador  # noqa: E402
from trojans import metricas, ruido  # noqa: E402

REPLICAS = 10
CHAVE = ["familia", "circuito", "porta", "posicao", "papel"]
COLUNAS = CHAVE + ["base", "entrada", "replica", "tvd_ideal", "revela_ideal", "tvd_ruido", "piso_ruido", "revela_ruido"]
ROBUSTA = 0.5  # detecção robusta: revelada em mais da metade das réplicas


def rodar(shots: int, replicas: int) -> pd.DataFrame:
    inicio = time.time()
    sim = ruido.simulador(BACKEND)
    linhas = []
    for i_circ, (familia, golden) in enumerate(goldens()):
        t0 = time.time()
        variantes, grupos, transpilados = preparar_golden(golden, sim)
        for r in range(replicas):
            freqs = ruido.rodar(transpilados, sim, shots, seed=semente_simulador(i_circ, r))
            _, li = avaliar(familia, golden, i_circ, variantes, grupos, transpilados, freqs, shots, replica=r)
            linhas += [{**linha, "replica": r} for linha in li]
        print(f"{familia}/{golden.name}: {replicas} réplicas em {time.time() - t0:.0f}s", flush=True)
    tabela = pd.DataFrame(linhas)[COLUNAS]
    tabela.to_csv(RAIZ / "results" / f"ruido_replicas_{shots}.csv", index=False)
    print(f"\n{len(tabela)} linhas em results/ruido_replicas_{shots}.csv ({(time.time() - inicio) / 60:.1f} min)")
    return tabela


def resumir(tab: pd.DataFrame, shots: int) -> None:
    # Por variante e réplica: revelada em alguma das 4 condições?
    vr = tab.groupby(CHAVE + ["replica"])[["revela_ideal", "revela_ruido"]].any().reset_index()
    # Por variante: fração das réplicas em que foi revelada com ruído.
    v = vr.groupby(CHAVE).agg(revela_ideal=("revela_ideal", "first"), p_deteccao=("revela_ruido", "mean")).reset_index()
    v["robusta"] = v.p_deteccao > ROBUSTA

    def linha(grupo_vr: pd.DataFrame, grupo_v: pd.DataFrame) -> dict:
        por_replica = grupo_vr.groupby("replica").revela_ruido.mean()
        n = len(grupo_v)
        k_ideal, k_rob = int(grupo_v.revela_ideal.sum()), int(grupo_v.robusta.sum())
        ic_ideal, ic_rob = metricas.wilson(k_ideal, n), metricas.wilson(k_rob, n)
        return {
            "n": n,
            "ideal_k": k_ideal,
            "ideal": k_ideal / n,
            "ideal_ic_inf": ic_ideal[0],
            "ideal_ic_sup": ic_ideal[1],
            "ruido_media": por_replica.mean(),
            "ruido_dp": por_replica.std(ddof=1),
            "ruido_min": por_replica.min(),
            "ruido_max": por_replica.max(),
            "robusta_k": k_rob,
            "robusta": k_rob / n,
            "robusta_ic_inf": ic_rob[0],
            "robusta_ic_sup": ic_rob[1],
            "p_deteccao_media": grupo_v.p_deteccao.mean(),
        }

    linhas = []
    for (fam, porta), g in v.groupby(["familia", "porta"]):
        linhas.append({"familia": fam, "porta": porta, **linha(vr[(vr.familia == fam) & (vr.porta == porta)], g)})
    linhas.append({"familia": "todas", "porta": "", **linha(vr, v)})
    resumo = pd.DataFrame(linhas)
    resumo.to_csv(RAIZ / "results" / f"resumo_replicas_{shots}.csv", index=False)

    # Falso alarme: combinações (variante, entrada, base) sem efeito nenhum no ideal.
    sil = tab[tab.tvd_ideal < 1e-9]
    fa = []
    for (entrada, base), g in sil.groupby(["entrada", "base"]):
        k, n = int(g.revela_ruido.sum()), len(g)
        ic = metricas.wilson(k, n)
        fa.append({"entrada": entrada, "base": base, "n": n, "k": k, "taxa": k / n, "ic_inf": ic[0], "ic_sup": ic[1]})
    k, n = int(sil.revela_ruido.sum()), len(sil)
    ic = metricas.wilson(k, n)
    fa.append({"entrada": "todas", "base": "", "n": n, "k": k, "taxa": k / n, "ic_inf": ic[0], "ic_sup": ic[1]})
    falso = pd.DataFrame(fa)
    falso.to_csv(RAIZ / "results" / f"falso_alarme_replicas_{shots}.csv", index=False)

    r = tab.replica.nunique()
    print(f"\n{shots} shots, {r} réplicas, {len(v)} variantes")
    print("Fração revelada: ideal | com ruído (média, dp, mín–máx entre réplicas) | detecção robusta (> metade)")
    print(resumo.round(3).to_string(index=False))
    print("\nFalso alarme por condição (todas as réplicas)")
    print(falso.round(4).to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--shots", type=int, default=SHOTS)
    parser.add_argument("--replicas", type=int, default=REPLICAS)
    parser.add_argument("--resumir", action="store_true", help="só refaz os resumos a partir do CSV")
    args = parser.parse_args()
    if args.resumir:
        tab = pd.read_csv(RAIZ / "results" / f"ruido_replicas_{args.shots}.csv")
    else:
        tab = rodar(args.shots, args.replicas)
    resumir(tab, args.shots)


if __name__ == "__main__":
    main()
