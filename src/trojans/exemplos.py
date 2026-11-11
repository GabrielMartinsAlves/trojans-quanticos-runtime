"""Circuitos pequenos de cada família, para estudo e testes.

Todos terminam com os qubits auxiliares de volta em |0>, para que a saída
medida seja só a resposta do algoritmo.
"""
from __future__ import annotations

from qiskit import QuantumCircuit


def ghz(n: int) -> QuantumCircuit:
    """Estado GHZ: (|0...0> + |1...1>)/sqrt(2)."""
    qc = QuantumCircuit(n, name=f"ghz_{n}")
    qc.h(0)
    for i in range(n - 1):
        qc.cx(i, i + 1)
    return qc


def bernstein_vazirani(segredo: str) -> QuantumCircuit:
    """Bernstein-Vazirani: a saída nos qubits de dados é o segredo s.

    O qubit n é o auxiliar; ele começa e termina em |0>.
    O bit mais à direita de `segredo` corresponde ao qubit 0 (convenção do Qiskit).
    """
    n = len(segredo)
    qc = QuantumCircuit(n + 1, name=f"bv_{segredo}")
    qc.x(n)
    qc.h(range(n + 1))
    for i, bit in enumerate(reversed(segredo)):
        if bit == "1":
            qc.cx(i, n)
    qc.h(range(n + 1))
    qc.x(n)
    return qc


def deutsch_jozsa(n: int, tipo: str = "balanceado") -> QuantumCircuit:
    """Deutsch-Jozsa com oráculo f(x) = x_0 (balanceado) ou f(x) = 0 (constante).

    Constante: os qubits de dados terminam em |0...0>. Balanceado: não terminam.
    """
    if tipo not in ("balanceado", "constante"):
        raise ValueError("tipo deve ser 'balanceado' ou 'constante'")
    qc = QuantumCircuit(n + 1, name=f"dj_{tipo}_{n}")
    qc.x(n)
    qc.h(range(n + 1))
    if tipo == "balanceado":
        qc.cx(0, n)
    qc.h(range(n + 1))
    qc.x(n)
    return qc


def somador_completo() -> QuantumCircuit:
    """Somador completo reversível (só X, CNOT e Toffoli).

    Qubits: 0 = a, 1 = b, 2 = carry de entrada (vira a soma), 3 = carry de saída (começa em 0).
    Saída: qubit 2 = a XOR b XOR cin; qubit 3 = maioria(a, b, cin); qubit 1 = a XOR b.
    """
    qc = QuantumCircuit(4, name="somador_completo")
    qc.ccx(0, 1, 3)
    qc.cx(0, 1)
    qc.ccx(1, 2, 3)
    qc.cx(1, 2)
    return qc
