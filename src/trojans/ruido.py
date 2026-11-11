"""Simulação com o modelo de ruído de um processador IBM (fake backend).

Depende de qiskit-aer e qiskit-ibm-runtime (para os fake backends).
Golden e infectado passam pela mesma transpilação mínima (nível 0, qubits fixos em 0..n-1),
só para aplicar o ruído.

Cada chamada ao simulador tem um custo fixo alto (o modelo de ruído do backend inteiro é
enviado ao Aer), então vale rodar muitos circuitos de uma vez com `rodar`.
"""
from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit, transpile

from .simulacao import na_base


def simulador(nome: str = "FakeTorino"):
    """AerSimulator com o modelo de ruído do fake backend `nome`."""
    from qiskit_aer import AerSimulator
    from qiskit_ibm_runtime import fake_provider

    backend = getattr(fake_provider, nome)()
    return AerSimulator.from_backend(backend)


def preparar(circ: QuantumCircuit, sim, base: str = "z", seed: int = 0) -> QuantumCircuit:
    """Circuito pronto para o simulador: base de medição, medições no fim e transpilação mínima."""
    c = na_base(circ, base)
    c.measure_all()
    return transpile(
        c,
        sim,
        optimization_level=0,
        initial_layout=list(range(circ.num_qubits)),
        seed_transpiler=seed,
    )


def frequencias(contagens: dict, n: int, shots: int) -> np.ndarray:
    """Vetor de tamanho 2^n com as frequências do registrador de `measure_all`.

    O registrador criado por `measure_all` é o último, então aparece primeiro na string
    de contagens (os registradores são separados por espaço).
    """
    freq = np.zeros(2**n)
    for bits, valor in contagens.items():
        freq[int(bits.split()[0], 2)] += valor / shots
    return freq


def rodar(transpilados: list[QuantumCircuit], sim, shots: int, seed: int = 0) -> list[np.ndarray]:
    """Frequências medidas de vários circuitos, numa chamada só ao simulador.

    O Aer deriva de `seed` uma semente diferente para cada circuito do lote,
    então os lotes de medições são independentes entre si.
    """
    resultado = sim.run(list(transpilados), shots=shots, seed_simulator=seed).result()
    # O transpilado ocupa o chip inteiro; o número de qubits do circuito é o tamanho
    # do registrador de medição criado por `measure_all` (o último).
    return [
        frequencias(resultado.get_counts(i), c.cregs[-1].size, shots)
        for i, c in enumerate(transpilados)
    ]


def distribuicao_ruidosa(
    circ: QuantumCircuit, sim, shots: int, base: str = "z", seed: int = 0
) -> np.ndarray:
    """Frequências medidas no simulador com ruído (vetor de tamanho 2^n)."""
    return rodar([preparar(circ, sim, base, seed)], sim, shots, seed)[0]
