# Plano: Checkpoint 2 (30/10) e Sprint 2 (06/11)

## Entregas

Checkpoint 2, sexta 30/10 às 10h:
- fundamentação teórica e revisão bibliográfica;
- metodologia reprodutível (como os experimentos rodam e como os resultados são analisados).

Sprint 2, até sexta 06/11 (15 pontos):
- tudo do checkpoint, mais experimentos e parâmetros, métricas, resultados com tabelas e
  figuras, e o código e os dados organizados (este repositório).

Escopo: versão enxuta (ver README). Ficam de fora QFT/QPE, Grover, porta CZ, estados de produto
aleatórios, segundo backend de ruído e regressão com interações.

## Tarefas

### Gabriel: pipeline e metodologia
| # | Tarefa | Prazo |
|---|---|---|
| G1 | Rodar os testes e o notebook `00_conceitos` | ter 27 |
| G2 | Ligar `experiments/rodar_ideal.py` aos circuitos de `data/selecao.csv` e rodar tudo | qua 28 |
| G3 | Reescrever a seção 6 (Metodologia) no Docs com o escopo enxuto | qui 29 |
| G4 | Rodada completa, conferir os números com o Gustavo e escrever os resultados | qua 04/11 |

### João: dados e simulador com ruído
| # | Tarefa | Prazo |
|---|---|---|
| J1 | Clonar o dataset em `data/raw`, filtrar o `metadata.csv` e escolher 3 a 5 circuitos por família (até 8 qubits, sem medição ou reset no meio). Salvar em `data/selecao.csv` com arquivo, família, qubits e profundidade | **qua 28, 18h** |
| J2 | Rodar `src/trojans/ruido.py` com um fake backend e medir o piso de ruído dos goldens (`results/piso_ruido.csv`) | qui 29 |
| J3 | Rodar as entradas \|0...0> e \|+>^n com ruído, comparar com o ideal e escrever a subseção do ambiente com ruído | ter 03/11 |

### Gustavo: análise e autoteste
| # | Tarefa | Prazo |
|---|---|---|
| U1 | Notebook `notebooks/01_analise.ipynb` sobre `results/ideal.csv`: mapas de calor porta × entrada por família e base, e tabela de k95 | qua 28 |
| U2 | Adaptar a análise SHAP do trabalho-base às nossas colunas e comparar \|0...0> com as entradas variadas | qui 29 |
| U3 | Subseção de métricas (TVD, piso, p, k95, SHAP) e figuras finais em `results/` | qua 04/11 |

### Bruno: texto do checkpoint
| # | Tarefa | Prazo |
|---|---|---|
| B1 | Fundamentação teórica: medição, fase e interferência, bases Z e X, circuitos reversíveis, transpilação no Qiskit, trojans quânticos (1,5 a 2 páginas) | qua 28 |
| B2 | Trabalhos relacionados: quadro comparando Das e Ghosh (2024), Roy et al. (2024), John et al. (2025) e Souza Filho et al. (2026) por entrada usada, ruído e tipo de detecção | qui 29 |
| B3 | Ajustar resumo, abstract, objetivo 4.1 c), H2, Tabela 1 e seção 6.4 ao escopo enxuto (junto com o Gabriel) | qui 29 |
| B4 | Figura do modelo de ameaça e do fluxo do experimento | qui 29 |

### Todos
- Qui 29, 21h: revisão cruzada (cada um lê a parte de outra pessoa).
- Sex 30, 10h: checkpoint.

## Ordem

- J1 → G2 → U1/U2 → resultados
- B1, B2, G3 e B3 → checkpoint
