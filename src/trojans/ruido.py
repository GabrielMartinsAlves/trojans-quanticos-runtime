"""Simulação com o modelo de ruído de um processador IBM (fake backend).

Depende de qiskit-aer e qiskit-ibm-runtime (para os fake backends).
Golden e infectado passam pela mesma transpilação mínima, só para aplicar o ruído.
"""
from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit, transpile

from .simulacao import _na_base


def simulador(nome: str = "FakeTorino"):
    """AerSimulator com o modelo de ruído do fake backend `nome`."""
    from qiskit_aer import AerSimulator
    from qiskit_ibm_runtime import fake_provider

    backend = getattr(fake_provider, nome)()
    return AerSimulator.from_backend(backend)


def distribuicao_ruidosa(
    circ: QuantumCircuit, sim, shots: int, base: str = "z", seed: int = 0
) -> np.ndarray:
    """Frequências medidas no simulador com ruído (vetor de tamanho 2^n)."""
    c = _na_base(circ, base)
    c.measure_all()
    n = circ.num_qubits
    transpilado = transpile(
        c,
        sim,
        optimization_level=0,
        initial_layout=list(range(n)),
        seed_transpiler=seed,
    )
    contagens = sim.run(transpilado, shots=shots, seed_simulator=seed).result().get_counts()
    freq = np.zeros(2**n)
    for bits, valor in contagens.items():
        freq[int(bits.replace(" ", ""), 2)] = valor / shots
    return freq
