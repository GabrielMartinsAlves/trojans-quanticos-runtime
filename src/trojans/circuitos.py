"""Carregamento dos circuitos golden do dataset e classificação por família."""
from __future__ import annotations

import re
from pathlib import Path

from qiskit import QuantumCircuit

# Palavras-chave no nome do arquivo para cada família do escopo.
# Prefira a coluna de família do metadata.csv do trabalho-base quando ela existir;
# isto é só um plano B para nomes de arquivo.
FAMILIAS = {
    "reversivel": ("adder", "alu", "4gt", "hwb", "rd", "mod", "toffoli", "fredkin", "peres", "decod", "ham"),
    "oraculo": ("bv", "bernstein", "deutsch", "dj"),
    "emaranhamento": ("ghz", "wstate", "cat"),
}


def familia(nome: str) -> str | None:
    """Família do circuito a partir do nome do arquivo, ou None se não reconhecer."""
    nome = nome.lower()
    for fam, chaves in FAMILIAS.items():
        if any(re.search(rf"(^|[^a-z]){re.escape(c)}", nome) for c in chaves):
            return fam
    return None


def carregar(caminho: str | Path) -> QuantumCircuit:
    """Lê um arquivo OpenQASM 2 e remove as medições finais.

    A simulação calcula as distribuições direto do vetor de estado,
    então as medições do arquivo não são necessárias.
    """
    circ = QuantumCircuit.from_qasm_file(str(caminho))
    circ = circ.remove_final_measurements(inplace=False)
    circ.name = Path(caminho).stem
    return circ


def elegivel(circ: QuantumCircuit, max_qubits: int = 10) -> bool:
    """True se o circuito cabe no estudo: até `max_qubits` e sem medição ou reset no meio."""
    operacoes = {inst.operation.name for inst in circ.data}
    return circ.num_qubits <= max_qubits and not operacoes & {"measure", "reset"}
