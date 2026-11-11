"""Carregamento dos circuitos golden do dataset e classificação por família."""
from __future__ import annotations

import re
from pathlib import Path

from qiskit import QuantumCircuit
from qiskit.circuit import Gate

# Palavras-chave no nome do arquivo de cada família.
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
    """True se o circuito cabe no estudo: até `max_qubits` e só portas unitárias.

    Ficam de fora medições ou resets no meio do circuito e controle clássico (if/while).
    """
    if circ.num_qubits > max_qubits:
        return False
    return all(isinstance(inst.operation, Gate) or inst.operation.name == "barrier" for inst in circ.data)


def reversivel(circ: QuantumCircuit) -> bool:
    """True se o circuito só usa X, CNOT, Toffoli e variações (permuta a base computacional)."""
    portas = {inst.operation.name for inst in circ.data} - {"barrier"}
    return portas <= {"x", "cx", "ccx", "mcx", "swap", "cswap", "c3x", "c4x"}
