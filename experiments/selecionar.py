"""Gera data/selecao.csv a partir do dataset do trabalho-base (data/raw/IC-QT-2026).

Critérios:
- circuitos golden com até 8 qubits e só portas unitárias (sem medição, reset ou if no meio);
- reversíveis: arquivos do RevLib que usam só X, CNOT, Toffoli e variações,
  com profundidade de pelo menos 5 (para início, meio e fim caírem em camadas diferentes);
- oráculos: Bernstein-Vazirani, Deutsch e Simon;
- emaranhamento: GHZ (cat state), Bell e W, nas versões não transpiladas.

Seleção provisória, até a seleção final do grupo ficar pronta.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from trojans import circuitos  # noqa: E402

BASE = RAIZ / "data" / "raw" / "IC-QT-2026"
METADATA = BASE / "results" / "datasets" / "dataset_trojan_final" / "full" / "metadata.csv"

ESCOLHA = {
    "reversivel": ["ham3_102.real", "decod24-v0_38.real", "4mod5-v0_18.real", "rd32_270.real", "alu-v2_31.real"],
    "oraculo": ["deutsch_n2.qasm", "bv_4.qasm", "bv_6.qasm", "bv_8.qasm", "simon_n6.qasm"],
    "emaranhamento": ["bell_n4.qasm", "cat_state_n4.qasm", "wstate_n3.qasm"],
}


def main() -> None:
    meta = pd.read_csv(METADATA)
    goldens = meta[meta.variant_type == "golden"]
    linhas = []
    for fam, arquivos in ESCOLHA.items():
        for arq in arquivos:
            reg = goldens[goldens.source_filename == arq].iloc[0]
            circ = circuitos.carregar(BASE / reg.original_path)
            assert circuitos.elegivel(circ, max_qubits=8), arq
            if fam == "reversivel":
                assert circuitos.reversivel(circ), arq
            linhas.append(
                {
                    "familia": fam,
                    "arquivo": arq,
                    "caminho": reg.original_path,
                    "base_circuit_id": int(reg.base_circuit_id),
                    "origem": reg.source_dataset,
                    "n_qubits": circ.num_qubits,
                    "profundidade": circ.depth(),
                    "portas": int(circ.size()),
                }
            )
    tabela = pd.DataFrame(linhas)
    saida = RAIZ / "data" / "selecao.csv"
    tabela.to_csv(saida, index=False)
    print(tabela.to_string(index=False))


if __name__ == "__main__":
    main()
