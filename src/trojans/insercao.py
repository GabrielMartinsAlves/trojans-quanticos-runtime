"""Inserção de uma porta (trojan) em um circuito golden.

O circuito é dividido em camadas (portas que podem rodar ao mesmo tempo).
A porta extra entra logo depois da camada escolhida pela posição
(início, meio ou fim da profundidade), em um qubit que naquela camada
está ativo (alguma porta age nele) ou ocioso.
"""
from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import HGate, RZGate, TGate, XGate, ZGate
from qiskit.converters import circuit_to_dag, dag_to_circuit

PORTAS = {
    "x": XGate,
    "h": HGate,
    "z": ZGate,
    "t": TGate,
    "rz_pi16": lambda: RZGate(np.pi / 16),
}
POSICOES = {"inicio": 0.1, "meio": 0.5, "fim": 0.9}
PAPEIS = ("ativo", "ocioso")


def camadas(circ: QuantumCircuit) -> list[QuantumCircuit]:
    """Camadas do circuito, na ordem de execução."""
    dag = circuit_to_dag(circ)
    return [dag_to_circuit(camada["graph"]) for camada in dag.layers()]


def qubits_ativos(camada: QuantumCircuit) -> set[int]:
    """Índices dos qubits usados por alguma porta da camada."""
    return {camada.find_bit(q).index for inst in camada.data for q in inst.qubits}


def inserir(
    circ: QuantumCircuit,
    porta: str,
    posicao: str,
    papel: str,
    seed: int = 0,
) -> tuple[QuantumCircuit, dict] | None:
    """Devolve (circuito infectado, metadados) ou None se a combinação não existe.

    Exemplo de combinação inexistente: pedir um qubit ocioso numa camada
    em que todos os qubits estão ativos.
    """
    if porta not in PORTAS or posicao not in POSICOES or papel not in PAPEIS:
        raise ValueError(f"porta/posição/papel inválido: {porta}, {posicao}, {papel}")

    cams = camadas(circ)
    if not cams:
        return None
    indice = min(len(cams) - 1, int(round(POSICOES[posicao] * (len(cams) - 1))))
    ativos = qubits_ativos(cams[indice])
    candidatos = sorted(ativos if papel == "ativo" else set(range(circ.num_qubits)) - ativos)
    if not candidatos:
        return None
    qubit = int(np.random.default_rng(seed).choice(candidatos))

    infectado = circ.copy_empty_like()
    for i, cam in enumerate(cams):
        infectado.compose(cam, inplace=True)
        if i == indice:
            infectado.append(PORTAS[porta](), [qubit])

    meta = {
        "porta": porta,
        "posicao": posicao,
        "papel": papel,
        "qubit": qubit,
        "camada": indice,
        "n_camadas": len(cams),
    }
    return infectado, meta
