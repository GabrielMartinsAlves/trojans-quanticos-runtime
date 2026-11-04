"""Testes que também servem de exemplo dos conceitos usados no artigo."""
import math

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

from trojans import autoteste, circuitos, entradas, exemplos, insercao, metricas, simulacao


def test_tvd_valores_conhecidos():
    assert metricas.tvd([1, 0], [1, 0]) == 0
    assert metricas.tvd([1, 0], [0, 1]) == 1
    assert metricas.tvd([1, 0], [0.5, 0.5]) == 0.5


def test_z_em_zero_nao_muda_nada():
    golden = QuantumCircuit(1)
    infectado = QuantumCircuit(1)
    infectado.z(0)
    assert metricas.tvd(simulacao.distribuicao(golden), simulacao.distribuicao(infectado)) == 0


def test_fase_so_aparece_com_interferencia():
    # Z em |+> vira |->: na base Z os dois dão 50/50, na base X a diferença é total.
    golden = entradas.com_entrada(QuantumCircuit(1), "mais")
    infectado = golden.copy()
    infectado.z(0)
    assert np.isclose(metricas.tvd(simulacao.distribuicao(golden, "z"), simulacao.distribuicao(infectado, "z")), 0)
    assert np.isclose(metricas.tvd(simulacao.distribuicao(golden, "x"), simulacao.distribuicao(infectado, "x")), 1)


def test_hzh_igual_a_x():
    hzh = QuantumCircuit(1)
    hzh.h(0)
    hzh.z(0)
    hzh.h(0)
    x = QuantumCircuit(1)
    x.x(0)
    assert Operator(hzh).equiv(Operator(x))


def test_cnot_depende_da_entrada():
    golden = QuantumCircuit(2)
    infectado = QuantumCircuit(2)
    infectado.cx(0, 1)

    def tvd_com(prefixo: QuantumCircuit) -> float:
        g = prefixo.compose(golden)
        i = prefixo.compose(infectado)
        return metricas.tvd(simulacao.distribuicao(g), simulacao.distribuicao(i))

    # Controle em |0>: o CNOT não dispara.
    assert tvd_com(QuantumCircuit(2)) == 0
    # Controle em |+> e alvo em |0>: o CNOT emaranha e muda a saída.
    controle_mais = QuantumCircuit(2)
    controle_mais.h(0)
    assert np.isclose(tvd_com(controle_mais), 0.5)
    # Alvo em |+> também esconde o CNOT: X|+> = |+>. Entradas diferentes escondem trojans diferentes.
    tudo_mais = QuantumCircuit(2)
    tudo_mais.h([0, 1])
    assert np.isclose(tvd_com(tudo_mais), 0)


def test_somador_completo_tabela_verdade():
    P = simulacao.distribuicoes_base(exemplos.somador_completo())
    for a in (0, 1):
        for b in (0, 1):
            for cin in (0, 1):
                entrada = a | (b << 1) | (cin << 2)
                saida = int(np.argmax(P[:, entrada]))
                assert (saida >> 2) & 1 == a ^ b ^ cin  # soma no qubit 2
                assert (saida >> 3) & 1 == int(a + b + cin >= 2)  # carry no qubit 3


def test_trojan_de_fase_em_circuito_reversivel():
    # H3: num circuito reversível (só X, CNOT, Toffoli), uma porta de fase
    # - com entrada da base computacional vira fase GLOBAL: invisível em qualquer base de medição;
    # - com medição na base Z continua invisível mesmo com entrada em superposição;
    # - só aparece com entrada em superposição E medição na base X.
    golden = exemplos.somador_completo()
    testados = 0
    for porta in ("z", "t", "rz_pi16"):
        for papel in insercao.PAPEIS:
            res = insercao.inserir(golden, porta, "meio", papel)
            if res is None:
                continue
            infectado, _ = res
            testados += 1

            def iguais(base, entrada):
                P_g = simulacao.distribuicoes_base(golden, base, entrada)
                P_i = simulacao.distribuicoes_base(infectado, base, entrada)
                return np.allclose(P_g, P_i)

            assert iguais("z", "z")
            assert iguais("x", "z")
            assert iguais("z", "x")
            assert not iguais("x", "x")
    assert testados > 0


def test_bernstein_vazirani_devolve_o_segredo():
    p = simulacao.distribuicao(exemplos.bernstein_vazirani("101"))
    assert int(np.argmax(p)) == 0b101
    assert np.isclose(p.max(), 1)


def test_insercao_pode_nao_existir():
    # Num circuito de uma camada que usa todos os qubits, não há qubit ocioso.
    circ = QuantumCircuit(2)
    circ.cx(0, 1)
    assert insercao.inserir(circ, "x", "meio", "ocioso") is None
    infectado, meta = insercao.inserir(circ, "x", "meio", "ativo")
    assert meta["qubit"] in (0, 1)
    assert infectado.size() == circ.size() + 1


def test_k95():
    assert autoteste.k95(0.5) == 5
    assert autoteste.k95(0.1) == 29
    assert autoteste.k95(1 / 256) == 766
    assert autoteste.k95(1) == 1
    assert math.isinf(autoteste.k95(0))


def test_piso_maior_com_menos_shots():
    p = np.full(8, 1 / 8)
    assert metricas.piso(p, shots=100) > metricas.piso(p, shots=10_000)


def test_filtro_de_circuitos():
    assert circuitos.elegivel(exemplos.somador_completo())
    assert circuitos.reversivel(exemplos.somador_completo())
    assert not circuitos.reversivel(exemplos.ghz(3))
    com_medicao = QuantumCircuit(2, 1)
    com_medicao.measure(0, 0)
    com_medicao.x(1)
    assert not circuitos.elegivel(com_medicao)


def test_piso_bootstrap():
    # Dois lotes do mesmo golden diferem por acaso; o piso cai com mais shots.
    p = np.full(8, 1 / 8)
    assert metricas.piso_bootstrap(p, shots=100) > metricas.piso_bootstrap(p, shots=10_000)
    # Contra uma referência fixa, só um dos lados tem ruído de amostragem: o piso é menor.
    assert metricas.piso_bootstrap(p, 1000, referencia=p) < metricas.piso_bootstrap(p, 1000)


def test_frequencias_do_registrador_de_medicao():
    # measure_all cria o último registrador, que aparece primeiro na string de contagens.
    from trojans import ruido

    freq = ruido.frequencias({"10 0": 3, "01 0": 1}, n=2, shots=4)
    assert np.allclose(freq, [0, 0.25, 0.75, 0])
