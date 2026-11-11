# Trojans quânticos em tempo de execução

Código e dados do artigo **"Detectabilidade de trojans quânticos em tempo de execução: efeito da
entrada, da base de medição e do ponto de inserção em diferentes famílias de circuitos"**, da eletiva
de Computação Quântica do Inteli (2026-2B).

**Pergunta:** quando um trojan (porta extra inserida na compilação) aparece na saída de um
circuito, e quantos testes um usuário precisa para encontrá-lo?

O trabalho estende o dataset de Souza Filho, Hayashi e Ferreira (SBSeg 2026), que mediu o impacto
dos trojans só com a entrada |0...0> e só na base Z.

## Escopo

| Fator | Valores |
|---|---|
| Famílias | reversíveis/aritméticos, oráculos (Deutsch, Bernstein-Vazirani, Simon), emaranhamento (GHZ, Bell, W) |
| Porta inserida | X, H, Z, T, RZ(π/16) |
| Posição | início (10%), meio (50%), fim (90%) da profundidade |
| Papel do qubit | ativo ou ocioso na camada de inserção |
| Entradas | \|0...0>, \|+>^n, todos os estados da base Z (\|j>) e da base X (H^n\|j>) |
| Bases de medição | Z e X |
| Ambientes | simulador ideal (exato) e simulador com ruído do IBM Torino (FakeTorino) |
| Métricas | TVD, piso de ruído (percentil 95), fração p de entradas que revelam, k95 |

## Estrutura

```
src/trojans/      biblioteca do projeto
  exemplos.py       circuitos pequenos de cada família (estudo e testes)
  circuitos.py      leitura dos QASM do dataset e classificação por família
  insercao.py       inserção do trojan (porta, posição, papel do qubit)
  entradas.py       preparação das entradas
  simulacao.py      distribuições exatas (vetor de estado e unitário)
  metricas.py       TVD e piso de ruído de amostragem
  autoteste.py      probabilidade de detecção e k95
  ruido.py          simulador com modelo de ruído (fake backend IBM)
experiments/      scripts que geram os resultados (comum.py: caminhos compartilhados)
notebooks/        notebooks de estudo e de análise
tests/            testes (também servem de exemplo dos conceitos)
data/raw/         dataset do trabalho-base (não versionado; ver README da pasta)
results/          tabelas e figuras geradas
```

## Como rodar (Windows / PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest
python experiments\selecionar.py   # gera data/selecao.csv (precisa do dataset em data/raw)
python experiments\rodar_ideal.py   # gera results/ideal.csv
python experiments\consolidar.py    # gera results/resumo_*.csv
python experiments\rodar_ruido.py       # gera results/piso_ruido_1024.csv e results/ruido_1024.csv (FakeTorino, ~3 min)
python experiments\consolidar_ruido.py  # gera results/resumo_*ruido*_1024.csv
python experiments\figuras_ruido.py     # gera results/fig_ruido_*_1024.png
# os três aceitam --shots 4096 (análise de sensibilidade; arquivos com sufixo _4096)
python experiments\replicas_ruido.py    # 10 réplicas com sementes diferentes (~20 min; aceita --shots 4096)
python experiments\testes_hipoteses.py  # testes das hipóteses H1 a H5c (McNemar, GEE e SHAP)
```

`notebooks/00_conceitos.py` tem exemplos dos conceitos básicos (abre como notebook no VS Code).

Os resultados gerados ficam em `results/` e são versionados, para que os números do artigo possam
ser conferidos sem rodar os experimentos.

## Referência do trabalho-base

W. J. de Souza Filho, V. T. Hayashi e B. K. Ferreira, "Dataset e análise de sensibilidade de trojans
em circuitos quânticos", Anais Estendidos do SBSeg 2026, pp. 489–499.
DOI: 10.5753/sbseg_estendido.2026.29446.

## Licença e citação

O código e os resultados estão sob a [licença MIT](LICENSE). O dataset do trabalho-base não faz
parte deste repositório (ver `data/raw/README.md`).

Para citar, use os metadados de [CITATION.cff](CITATION.cff). O DOI do arquivamento no Zenodo é
gerado a cada release.
