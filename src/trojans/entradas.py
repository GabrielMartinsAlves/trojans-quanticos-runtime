"""Preparação das entradas: o mesmo prefixo vai no golden e no infectado."""
from __future__ import annotations

from qiskit import QuantumCircuit

TIPOS = ("zeros", "mais", "base", "base_x")


def prefixo(n: int, tipo: str, valor: int = 0) -> QuantumCircuit:
    """Circuito que prepara a entrada a partir de |0...0>.

    - "zeros": não faz nada (entrada |0...0>);
    - "mais": H em todos os qubits (entrada |+>^n);
    - "base": X nos qubits cujo bit de `valor` é 1 (bit i -> qubit i, convenção do Qiskit);
    - "base_x": como "base" e depois H em todos, dando um produto de |+> e |->.
      São os estados da base X; com eles uma fase relativa pode aparecer na saída.
    """
    qc = QuantumCircuit(n)
    if tipo == "zeros":
        return qc
    if tipo == "mais":
        qc.h(range(n))
        return qc
    if tipo in ("base", "base_x"):
        for i in range(n):
            if (valor >> i) & 1:
                qc.x(i)
        if tipo == "base_x":
            qc.h(range(n))
        return qc
    raise ValueError(f"tipo de entrada desconhecido: {tipo}")


def com_entrada(circ: QuantumCircuit, tipo: str, valor: int = 0) -> QuantumCircuit:
    """Circuito com o prefixo de entrada antes das portas originais."""
    novo = circ.copy_empty_like()
    novo.compose(prefixo(circ.num_qubits, tipo, valor), inplace=True)
    novo.compose(circ, inplace=True)
    return novo
