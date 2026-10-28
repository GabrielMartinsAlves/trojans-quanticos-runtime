"""Distribuições de saída exatas (simulador ideal).

As distribuições são vetores de tamanho 2^n indexados pelo inteiro da saída,
na convenção do Qiskit (qubit 0 é o bit menos significativo).
"""
from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector

BASES = ("z", "x")


def _na_base(circ: QuantumCircuit, base: str) -> QuantumCircuit:
    """Medir na base X é aplicar H em todos os qubits e medir na base Z."""
    if base not in BASES:
        raise ValueError(f"base desconhecida: {base}")
    c = circ.copy()
    if base == "x":
        c.h(range(c.num_qubits))
    return c


def distribuicao(circ: QuantumCircuit, base: str = "z") -> np.ndarray:
    """Distribuição exata da saída do circuito, começando em |0...0>."""
    return Statevector(_na_base(circ, base)).probabilities()


def distribuicoes_base(circ: QuantumCircuit, base: str = "z", entrada: str = "z") -> np.ndarray:
    """Matriz P com P[y, j] = probabilidade de medir y quando a entrada é o j-ésimo estado da base.

    - `entrada="z"`: entradas |j> (estados da base computacional);
    - `entrada="x"`: entradas H^n|j> (produtos de |+> e |->; a coluna 0 é |+>^n).

    Calcula o unitário uma vez só e devolve as distribuições de todas as entradas
    de uma vez (coluna j = entrada j).
    """
    if entrada not in BASES:
        raise ValueError(f"base de entrada desconhecida: {entrada}")
    c = circ.copy_empty_like()
    if entrada == "x":
        c.h(range(c.num_qubits))
    c.compose(circ, inplace=True)
    unitario = Operator(_na_base(c, base)).data
    return np.abs(unitario) ** 2


def amostrar(p: np.ndarray, shots: int, rng: np.random.Generator) -> np.ndarray:
    """Frequências observadas ao medir `shots` vezes uma distribuição p."""
    p = np.clip(np.asarray(p, dtype=float), 0, None)
    return rng.multinomial(shots, p / p.sum()) / shots
