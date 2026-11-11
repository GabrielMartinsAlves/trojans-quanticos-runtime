# %% [markdown]
# # 00 - Conceitos usados no artigo
#
# Exemplos pequenos de cada ideia usada no trabalho.
#
# Abra no VS Code (extensão Jupyter) ou converta com `jupytext --to ipynb`.

# %%
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # console do Windows não mostra o desenho dos circuitos sem isso

RAIZ = Path.cwd() if (Path.cwd() / "src").exists() else Path.cwd().parent
sys.path.insert(0, str(RAIZ / "src"))

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector

from trojans import autoteste, entradas, exemplos, insercao, metricas, simulacao

np.set_printoptions(precision=3, suppress=True)

# %% [markdown]
# ## 1. Medição = |amplitude|²
# |0> sempre dá 0. H|0> = |+> dá 0 ou 1 com 50% cada.

# %%
qc = QuantumCircuit(1)
print("|0>  ->", simulacao.distribuicao(qc))
qc.h(0)
print("H|0> ->", simulacao.distribuicao(qc))
print("vetor de estado:", Statevector(qc).data)

# %% [markdown]
# ## 2. TVD: o "tamanho do estrago"
# TVD = ½ Σ |p − q|. Vai de 0 (iguais) a 1 (nada em comum).

# %%
print(metricas.tvd([1, 0], [1, 0]))      # 0: iguais
print(metricas.tvd([1, 0], [0.5, 0.5]))  # 0.5: virou cara ou coroa
print(metricas.tvd([1, 0], [0, 1]))      # 1: saída trocada

# %% [markdown]
# ## 3. Por que Z e T "não fazem nada" no trabalho-base
# Z|0> = |0>. Como tudo começava em |0>, a porta de fase não tinha o que mudar.

# %%
golden = QuantumCircuit(1)
infectado = QuantumCircuit(1)
infectado.z(0)
print("TVD com entrada |0>:", metricas.tvd(simulacao.distribuicao(golden), simulacao.distribuicao(infectado)))

# %% [markdown]
# ## 4. Superposição sozinha não basta: a fase precisa de interferência
# Z|+> = |->. Na base Z, |+> e |-> dão 50/50: o Z continua invisível.
# Na base X (H antes de medir), H|+> = |0> e H|-> = |1>: diferença total.

# %%
g = entradas.com_entrada(QuantumCircuit(1), "mais")
i = g.copy()
i.z(0)
for base in ("z", "x"):
    print(f"base {base}: TVD =", metricas.tvd(simulacao.distribuicao(g, base), simulacao.distribuicao(i, base)))

# %% [markdown]
# ## 5. H Z H = X
# Envolver uma fase com H transforma fase em inversão de bit. É a interferência em ação.

# %%
hzh = QuantumCircuit(1); hzh.h(0); hzh.z(0); hzh.h(0)
x = QuantumCircuit(1); x.x(0)
print("H Z H == X ?", Operator(hzh).equiv(Operator(x)))

# %% [markdown]
# ## 6. A entrada decide se o trojan aparece: o exemplo do CNOT
# - controle em |0>: o CNOT não dispara (TVD 0);
# - controle em |+>, alvo em |0>: o CNOT emaranha, a saída muda (TVD 0,5);
# - alvo em |+>: X|+> = |+>, então o CNOT de novo não muda nada (TVD 0).
# Nenhuma entrada sozinha revela todos os trojans.

# %%
g = QuantumCircuit(2)
i = QuantumCircuit(2); i.cx(0, 1)
casos = {"|00>": [], "controle |+>, alvo |0>": [0], "|++>": [0, 1]}
for nome, qubits_h in casos.items():
    prep = QuantumCircuit(2)
    if qubits_h:
        prep.h(qubits_h)
    tvd = metricas.tvd(simulacao.distribuicao(prep.compose(g)), simulacao.distribuicao(prep.compose(i)))
    print(f"entrada {nome:<24} TVD = {tvd:.2f}")

# %% [markdown]
# ## 7. Circuito reversível: tabela-verdade do somador completo
# Só X, CNOT e Toffoli: cada entrada da base vira exatamente uma saída (permutação).
# Coluna j de P = distribuição da saída para a entrada |j>.

# %%
somador = exemplos.somador_completo()
print(somador.draw())
P = simulacao.distribuicoes_base(somador)
for entrada in range(8):
    saida = int(np.argmax(P[:, entrada]))
    print(f"entrada {entrada:04b} -> saída {saida:04b}")

# %% [markdown]
# ## 8. Hipótese H3: trojan de fase em circuito reversível
# Um circuito reversível leva cada estado da base |j> em outro estado da base, vezes uma fase.
# Com entrada |j>, o Z inserido só muda essa fase, que é GLOBAL: nenhuma medição a enxerga,
# nem na base Z nem na base X.
# Com entrada em superposição (estados da base X, como |+>^n), as fases de cada termo
# ficam diferentes entre si (fase RELATIVA). Medindo na base X, ela aparece.
#
# Ou seja: só aparece com entrada em superposição e medição em X.

# %%
infectado, meta = insercao.inserir(somador, "z", "meio", "ativo")
print(meta)
print(infectado.draw())
for entrada in ("z", "x"):
    for base in ("z", "x"):
        P_g = simulacao.distribuicoes_base(somador, base, entrada)
        P_i = simulacao.distribuicoes_base(infectado, base, entrada)
        tvds = [metricas.tvd(P_g[:, j], P_i[:, j]) for j in range(P_g.shape[1])]
        print(f"entradas da base {entrada.upper()}, medição em {base.upper()}: TVD máx = {max(tvds):.2f}")

# %% [markdown]
# ## 9. Piso de ruído de amostragem
# Mesmo sem trojan, medir 1000 vezes não reproduz a distribuição exata.
# O piso é o percentil 95 dessa diferença "por acaso".

# %%
p = simulacao.distribuicao(exemplos.ghz(3))
for shots in (100, 1000, 10000):
    print(f"{shots:>6} shots -> piso = {metricas.piso(p, shots):.3f}")

# %% [markdown]
# ## 10. Autoteste: quantos testes até achar o trojan
# Se uma fração p das entradas revela o trojan, com k testes a chance é 1 − (1 − p)^k.

# %%
for p in (0.5, 0.25, 0.1, 1 / 32, 1 / 256):
    print(f"p = {p:.4f} -> k95 = {autoteste.k95(p)}")

# %% [markdown]
# ## 11. Trojan em BV com |0...0> e com |+>^n
# Compare o impacto com |0...0> (como no trabalho-base) e com |+>^n.

# %%
bv = exemplos.bernstein_vazirani("101")
for porta in insercao.PORTAS:
    res = insercao.inserir(bv, porta, "meio", "ativo")
    if res is None:
        continue
    inf, _ = res
    t0 = metricas.tvd(simulacao.distribuicao(bv), simulacao.distribuicao(inf))
    tm = metricas.tvd(
        simulacao.distribuicao(entradas.com_entrada(bv, "mais")),
        simulacao.distribuicao(entradas.com_entrada(inf, "mais")),
    )
    print(f"{porta:>8}: TVD |0> = {t0:.2f} | TVD |+> = {tm:.2f}")
