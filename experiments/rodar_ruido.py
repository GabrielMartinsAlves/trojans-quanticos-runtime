"""Experimento no simulador com ruído: gera results/piso_ruido_<shots>.csv e results/ruido_<shots>.csv.

Segue a seção VI.D do artigo, no escopo enxuto (docs/PLANO_SEMANA.md):
- modelo de ruído de um processador IBM (fake backend do Qiskit);
- 1.024 shots por execução (o padrão do Qiskit); com --shots 4096 (o padrão da IBM Runtime),
  para a análise de sensibilidade;
- golden e infectado passam pela mesma transpilação mínima (nível 0, qubits fixos em 0..n-1);
- entradas |0...0> e |+>^n, bases de medição Z e X;
- piso de ruído: percentil 95 da TVD entre dois lotes independentes do golden com ruído,
  estimado por reamostragem (bootstrap);
- a inserção é visível numa entrada quando a TVD entre golden e infectado (ambos com ruído)
  passa do piso.

Para comparar, também registra:
- o resultado ideal com o mesmo número de shots (TVD exata contra o piso de amostragem,
  como em rodar_ideal.py);
- uma variante em que a referência é a saída ideal do golden: o usuário compara o que mediu
  no processador com a saída calculada classicamente, sem rodar o golden no hardware.

Saídas:
- results/piso_ruido_<shots>.csv: uma linha por golden, base e entrada (piso de ruído);
- results/ruido_<shots>.csv: uma linha por variante infectada, base e entrada.

Uso: python experiments/rodar_ruido.py [--shots 1024]
"""
from __future__ import annotations

import argparse
import itertools
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
from trojans import entradas, insercao, metricas, ruido, simulacao  # noqa: E402

BACKEND = "FakeTorino"
SHOTS = 1024  # padrão do Qiskit (AerSimulator.run e Samplers locais)
N_REP = 500  # reamostragens do bootstrap
SEED = 0
ENTRADAS = ("zeros", "mais")
# Quando a saída ideal é determinística, o piso de amostragem é 0 e diferenças de
# arredondamento (~1e-16) passariam dele. Abaixo desta TVD, a inserção conta como invisível.
TOL = 1e-9


def n_cz(transpilado) -> int:
    """Portas de dois qubits depois da transpilação (no Torino, a porta nativa é a CZ)."""
    return int(transpilado.count_ops().get("cz", 0))


def main(shots: int = SHOTS) -> None:
    inicio = time.time()
    sim = ruido.simulador(BACKEND)
    linhas_piso, linhas = [], []

    for i_circ, (familia, golden) in enumerate(goldens()):
        t0 = time.time()
        variantes = []
        for porta, posicao, papel in itertools.product(insercao.PORTAS, insercao.POSICOES, insercao.PAPEIS):
            resultado = insercao.inserir(golden, porta, posicao, papel)
            if resultado is not None:
                variantes.append(resultado)

        # Um lote por golden: para cada base e entrada, o golden e todas as variantes.
        # Índice 0 de cada grupo é o golden.
        grupos = {}
        circs = []
        for base, entrada in itertools.product(simulacao.BASES, ENTRADAS):
            grupo = [entradas.com_entrada(golden, entrada)]
            grupo += [entradas.com_entrada(infectado, entrada) for infectado, _ in variantes]
            grupos[(base, entrada)] = (len(circs), grupo)
            circs += [(base, c) for c in grupo]

        transpilados = [ruido.preparar(c, sim, base, SEED) for base, c in circs]
        freqs = ruido.rodar(transpilados, sim, shots, seed=SEED + 10_000 * (i_circ + 1))

        for (base, entrada), (ini, grupo) in grupos.items():
            seed_piso = SEED + 1000 * i_circ + 10 * simulacao.BASES.index(base) + ENTRADAS.index(entrada)
            ideal_g = simulacao.distribuicao(grupo[0], base)
            ruido_g = freqs[ini]
            tr_g = transpilados[ini]

            piso_ideal = metricas.piso(ideal_g, shots, n_rep=N_REP, seed=seed_piso)
            piso_ruido = metricas.piso_bootstrap(ruido_g, shots, n_rep=N_REP, seed=seed_piso)
            piso_vs_ideal = metricas.piso_bootstrap(
                ruido_g, shots, n_rep=N_REP, seed=seed_piso, referencia=ideal_g
            )
            comum = {
                "familia": familia,
                "circuito": golden.name,
                "n_qubits": golden.num_qubits,
                "base": base,
                "entrada": entrada,
            }
            linhas_piso.append(
                {
                    **comum,
                    "backend": BACKEND,
                    "shots": shots,
                    "profundidade": golden.depth(),
                    "profundidade_transpilada": tr_g.depth(),
                    "cz": n_cz(tr_g),
                    "tvd_ruido_vs_ideal": metricas.tvd(ruido_g, ideal_g),
                    "piso_ideal": piso_ideal,
                    "piso_ruido": piso_ruido,
                    "piso_vs_ideal": piso_vs_ideal,
                }
            )

            for k, (_, meta) in enumerate(variantes, start=1):
                ideal_i = simulacao.distribuicao(grupo[k], base)
                ruido_i = freqs[ini + k]
                tvd_ideal = metricas.tvd(ideal_g, ideal_i)
                tvd_ruido = metricas.tvd(ruido_g, ruido_i)
                tvd_vs_ideal = metricas.tvd(ruido_i, ideal_g)
                linhas.append(
                    {
                        **comum,
                        **meta,
                        "tvd_ideal": tvd_ideal,
                        "piso_ideal": piso_ideal,
                        "revela_ideal": bool(tvd_ideal > max(piso_ideal, TOL)),
                        "tvd_ruido": tvd_ruido,
                        "piso_ruido": piso_ruido,
                        "revela_ruido": bool(tvd_ruido > max(piso_ruido, TOL)),
                        "tvd_vs_ideal": tvd_vs_ideal,
                        "piso_vs_ideal": piso_vs_ideal,
                        "revela_vs_ideal": bool(tvd_vs_ideal > max(piso_vs_ideal, TOL)),
                        "cz_golden": n_cz(tr_g),
                        "cz_infectado": n_cz(transpilados[ini + k]),
                    }
                )

        print(
            f"{familia}/{golden.name}: {golden.num_qubits} qubits, {len(variantes)} variantes, "
            f"{len(circs)} execuções em {time.time() - t0:.0f}s",
            flush=True,
        )

    pasta = RAIZ / "results"
    pasta.mkdir(exist_ok=True)
    pisos = pd.DataFrame(linhas_piso)
    tabela = pd.DataFrame(linhas)
    pisos.to_csv(pasta / f"piso_ruido_{shots}.csv", index=False)
    tabela.to_csv(pasta / f"ruido_{shots}.csv", index=False)
    print(f"\n{len(pisos)} linhas em results/piso_ruido_{shots}.csv, {len(tabela)} em results/ruido_{shots}.csv")
    print(f"tempo total: {(time.time() - inicio) / 60:.1f} min")

    roteamento_diferente = (tabela.cz_golden != tabela.cz_infectado).sum()
    print(f"variantes com roteamento diferente do golden: {roteamento_diferente}")

    print(f"\nPiso médio por família, {shots} shots (ideal | com ruído | ruído contra o ideal)")
    print(
        pisos.groupby("familia")[["piso_ideal", "piso_ruido", "piso_vs_ideal", "tvd_ruido_vs_ideal"]]
        .mean()
        .round(3)
        .to_string()
    )


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--shots", type=int, default=SHOTS, help=f"medições por execução (padrão {SHOTS})")
    return parser.parse_args()


if __name__ == "__main__":
    main(argumentos().shots)
