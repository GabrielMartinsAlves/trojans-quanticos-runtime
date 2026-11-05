# Rascunho: ambiente com ruído (J2 e J3)

Texto para colar no Docs. A parte de metodologia complementa a seção 6.4 (aba G3); a parte de
resultados entra na seção de resultados. O experimento foi rodado com **1.024 shots** (principal,
o padrão do Qiskit e o mesmo valor do simulador ideal) e com **4.096 shots** (análise de
sensibilidade, o padrão da IBM Runtime), e repetido **10 vezes** com sementes diferentes para
cada número de shots, para medir a margem de erro.

**Figuras sugeridas:** no corpo do texto, só as de 1.024 shots (`results/fig_ruido_revela_1024.png`
e `results/fig_ruido_piso_1024.png`). A sensibilidade a 4.096 shots entra nas Tabelas W e R; a
figura de 4.096 (`results/fig_ruido_revela_4096.png`) fica como material complementar.

Arquivos (`<s>` = 1024 ou 4096):

- rodada única (réplica 0): `results/piso_ruido_<s>.csv`, `results/ruido_<s>.csv`,
  `results/resumo_*ruido*_<s>.csv` (com contagens e intervalos de confiança),
  `results/fig_ruido_revela_<s>.png` e `results/fig_ruido_piso_<s>.png`;
- 10 réplicas: `results/ruido_replicas_<s>.csv`, `results/resumo_replicas_<s>.csv` e
  `results/falso_alarme_replicas_<s>.csv`.

Para reproduzir:

```
python experiments/rodar_ruido.py --shots 1024        # ~3 min
python experiments/consolidar_ruido.py --shots 1024
python experiments/replicas_ruido.py --shots 1024     # 10 réplicas, ~20–40 min
python experiments/figuras_ruido.py --shots 1024      # depois das réplicas (usa a taxa de falso alarme medida)
```

(e o mesmo com `--shots 4096`). As sementes são fixas, então os números se repetem. A réplica 0
de `replicas_ruido.py` é idêntica a `ruido_<s>.csv`.

---

## Metodologia: simulador com ruído (complemento da seção 6.4)

No simulador com ruído, usa-se o modelo do processador IBM Torino (*fake backend* `FakeTorino`
do Qiskit, 133 qubits, portas nativas CZ, √X, X e RZ), que reúne erros de porta, relaxação
térmica e erros de leitura medidos em uma calibração do processador. Os 13 circuitos golden e as
360 variantes infectadas rodam com duas entradas, |0···0⟩ e |+⟩ⁿ, medidas nas bases Z e X, em um
total de 1.492 execuções por rodada. Cada execução usa 1.024 *shots*, o mesmo número do simulador
ideal; o experimento foi repetido com 4.096 *shots*, o padrão da IBM Runtime, para avaliar a
sensibilidade a esse parâmetro. Golden e infectado passam pela mesma transpilação mínima (nível
de otimização 0), com os qubits lógicos fixos nos qubits físicos 0 a n−1, que formam uma cadeia
linear no processador. Em nenhuma variante a porta inserida alterou o roteamento: golden e
infectado têm o mesmo número de portas CZ.

O piso de ruído é estimado por circuito, entrada e base, a partir de execuções independentes do
golden. Das frequências medidas do golden, sorteiam-se 500 pares de lotes com o mesmo número de
*shots* (*bootstrap*), e o piso é o percentil 95 da TVD entre os lotes de cada par. Uma inserção
conta como visível quando a TVD entre golden e infectado, ambos executados com ruído, passa desse
piso. Para comparação, calcula-se também o resultado ideal **nas mesmas quatro condições** (|0···0⟩
e |+⟩ⁿ, bases Z e X) e com o mesmo número de *shots*. Esse "ideal" não é o da seção de resultados
do simulador ideal, que usa todos os estados das bases Z e X; nesta amostra, as duas medidas
coincidem por família e porta (94% das variantes no total), mas os conjuntos de condições são
diferentes. Registra-se ainda uma variante em que a referência é a saída ideal do golden,
calculada classicamente.

**Réplicas e margens de erro.** Em uma rodada, cada variante é executada uma vez por condição, e a
decisão de revelar ou não depende do acaso da amostragem. Por isso, o experimento foi repetido 10
vezes para cada número de *shots*, mudando só as sementes do simulador e do *bootstrap*; a
transpilação e o modelo de ruído são os mesmos. A primeira réplica é a rodada usada nas figuras.
Para cada variante, a probabilidade de detecção é a fração das réplicas em que ela foi revelada
em alguma das quatro condições, e a detecção é considerada **robusta** quando essa fração passa de
metade. As proporções são apresentadas com intervalos de confiança de Wilson de 95%, adequados a
amostras pequenas e a proporções perto de 0% ou de 100%.

**Volume de dados.** Cada rodada tem 1.492 execuções (52 do golden e 1.440 das variantes). Com
1.024 *shots*, são cerca de 1,5 milhão de medições por rodada e 15,3 milhões nas 10 réplicas
(61,1 milhões com 4.096 *shots*). O piso de cada golden, entrada e base é estimado com 500
reamostragens em cada réplica.

## Resultados no simulador com ruído

**O ruído afasta a saída da ideal, mas o piso continua baixo.** Executado com ruído, o golden
se afasta da sua saída ideal por uma TVD média de 0,17 (emaranhamento), 0,20 (oráculos) e
0,27 (reversíveis), na média das quatro condições. O afastamento depende da condição: é grande
quando a saída ideal é um único resultado, porque o ruído espalha a probabilidade para outros
resultados, e pequeno quando a saída ideal já é espalhada. No `alu-v2_31`, o maior circuito (311
portas CZ depois da transpilação), a TVD chega a 0,83 com |+⟩ⁿ medido na base X e a 0,78 com
|0···0⟩ na base Z, as duas condições de saída determinística; nas outras duas, fica abaixo de
0,09. A Fig. Y mostra a média das quatro condições (0,44 no `alu-v2_31`), que cresce com o número
de portas de dois qubits. O piso, porém, fica em 0,07 a 0,11 em média com 1.024 *shots* (0,04 a
0,06 com 4.096), porque o ruído é o mesmo nos dois lotes comparados. Se a referência fosse a
saída ideal, o piso teria de absorver o próprio ruído e subiria para 0,20 a 0,30 em média.

| Família | CZ (média) | Golden com ruído × ideal¹ | Piso ideal (1.024) | Piso com ruído (1.024) | Piso ideal (4.096) | Piso com ruído (4.096) |
|---|---|---|---|---|---|---|
| Reversíveis | 104 | 0,270 | 0,037 | 0,091 | 0,019 | 0,046 |
| Oráculos | 25 | 0,204 | 0,060 | 0,112 | 0,030 | 0,058 |
| Emaranhamento | 9 | 0,174 | 0,041 | 0,073 | 0,021 | 0,036 |

*Tabela Z: piso e distorção médios por família (FakeTorino, média das 4 condições de entrada e
base). ¹ Com 1.024 shots; com 4.096, de 0,00 a 0,02 menor (com menos shots, a amostragem infla um
pouco a TVD). O pior caso por condição está no texto.*

**Quase tudo que aparece no ideal continua aparecendo com ruído.** Com 1.024 *shots*, das 592
combinações de variante, entrada e base em que a inserção é visível no ideal, 90,0% continuam
visíveis com ruído. As 59 que deixam de aparecer têm, em geral, impacto ideal muito pequeno
(TVD mediana de 0,010). X, H e Z continuam visíveis em 100% das combinações, T em 90,5% e
RZ(π/16) em apenas 8,9%.

**A perda se concentra nas rotações sutis.** Considerando as quatro condições juntas, a fração
de variantes reveladas cai de 94% (338/360) no ideal para 82% (295/360; IC 95%: 78%–86%) com
ruído (Fig. X); nas 10 réplicas, a média é de 83% e a detecção robusta, de 79% (Tabela R). A queda
vem principalmente de RZ(π/16), cuja maior parte muda a saída ideal em uma TVD de apenas 0,01,
bem abaixo do piso com ruído. Nos reversíveis, a rodada da Fig. X mostra 4/29, mas nenhuma dessas
detecções é real: na única condição em que a rotação aparece no ideal (|+⟩ⁿ medido na base X),
nenhuma foi detectada com ruído, e nas 10 réplicas nenhuma das 29 variantes é revelada em mais da
metade das rodadas. Os 4/29 ficam abaixo da linha tracejada da Fig. X, que marca o nível de falso
alarme por variante (≈25% com 1.024 *shots*). Nos oráculos, a rodada mostra 11/27 (contra 22/27 no
ideal), mas só 3/27 têm detecção robusta. Nos circuitos de emaranhamento, em que essa rotação já
era pouco visível no ideal (3/16), as três variantes visíveis no ideal continuam sendo detectadas
na maioria das réplicas. T também perde um pouco nos reversíveis (de 29/29 para 24/29 na rodada;
23/29 de detecção robusta), sempre no `alu-v2_31`, o circuito mais ruidoso, em que o efeito do T
fica logo abaixo do piso. X, H e Z são reveladas na mesma proporção que no ideal. Na condição do
trabalho-base (|0···0⟩ medido na base Z), a fração é de 48% no ideal e de 47% a 48% com ruído. Ou
seja, o ruído não muda a conclusão de que a entrada e a base de medição são o que mais pesa para
um trojan aparecer.

**Sensibilidade ao número de shots.** Com 4.096 *shots*, o piso cai pela metade, mas as réplicas
mostram que o ganho de detecção é pequeno: a média entre as 10 réplicas vai de 83,2% para 83,5%, e
a detecção robusta, de 284 para 286 das 360 variantes (Tabela R). O ganho aparece onde o efeito
do trojan está perto do piso: os T do `alu-v2_31` (detecção robusta nos reversíveis de 23/29 para
26/29) e os três RZ(π/16) do emaranhamento visíveis no ideal, que mudam a saída em uma TVD de 0,05
a 0,08 e passam de 80%–100% para 100% das réplicas. A maior parte dos RZ(π/16), com efeito de
0,01, continua invisível com os dois números de *shots*: nos reversíveis, nenhum é detectado de
forma robusta. Como o piso diminui com a raiz do número de *shots*, enxergá-los exigiria um piso
cerca de quatro vezes menor, isto é, da ordem de 16 vezes mais *shots* (cerca de 65 mil). Mais
*shots* também reduz os falsos alarmes (de 6,8% para 4,8% por condição; ver abaixo). O custo de
encontrar um trojan, portanto, depende do orçamento de medições do usuário, e as inserções de
ângulo muito pequeno ficam fora do alcance de um autoteste com orçamento usual.

| Resultado (rodada única) | 1.024 shots | 4.096 shots |
|---|---|---|
| Combinações visíveis no ideal que continuam visíveis com ruído | 90,0% (533/592) | 91,8% (547/596) |
| Continuam visíveis, por porta: X, H e Z / T / RZ(π/16) | 100% / 90,5% / 8,9% | 100% / 94,3% / 21,4% |
| Variantes reveladas em alguma das 4 condições: ideal → ruído | 338 → 295 de 360 (94% → 82%; IC do ruído 78–86%) | 338 → 303 de 360 (94% → 84%; IC 80–88%) |
| RZ(π/16), reversíveis: ideal → ruído | 29/29 → 4/29² (IC 5–31%) | 29/29 → 4/29² (IC 5–31%) |
| RZ(π/16), oráculos: ideal → ruído | 22/27 → 11/27 (IC 25–59%) | 22/27 → 10/27 (IC 22–56%) |
| RZ(π/16), emaranhamento: ideal → ruído | 3/16 → 2/16 (IC 3–36%) | 3/16 → 5/16³ (IC 14–56%) |
| T, reversíveis: ideal → ruído | 29/29 → 24/29 (IC 65–92%) | 29/29 → 28/29 (IC 83–99%) |
| T, emaranhamento: ideal → ruído | 16/16 → 15/16 (IC 72–99%) | 16/16 → 16/16 (IC 81–100%) |
| Trabalho-base (\|0···0⟩, base Z): ideal → ruído | 48,1% → 46,9% | 48,1% → 47,5% |
| Falsos alarmes por condição⁴ | 6,8% (IC 6,3–7,4%) | 4,8% (IC 4,3–5,2%) |
| Piso com ruído (mínimo–máximo) | 0,044–0,289 | 0,022–0,151 |

*Tabela W: resultados da rodada única (réplica 0) para os dois números de shots (FakeTorino);
"ideal" = mesmas 4 condições; IC = intervalo de confiança de Wilson de 95%. ² Abaixo do nível de
falso alarme por variante (≈25% com 1.024 e ≈18% com 4.096); detecção robusta de 0/29 nas
réplicas. ³ Os 3 visíveis no ideal mais 2 compatíveis com falso alarme. ⁴ Juntando as 10 réplicas
(8.120 combinações sem efeito no ideal); na rodada única, 5,0% e 4,4%.*

**Robustez: margens de erro e 10 réplicas.** Os números acima vêm de uma rodada só. Para medir
quanto eles mudam de uma rodada para outra, o experimento foi repetido 10 vezes, mudando só as
sementes (14.920 execuções por número de *shots*). A Tabela R mostra, para cada grupo, a média e a
faixa da fração revelada entre as réplicas e a detecção robusta, isto é, as variantes reveladas
em mais da metade das réplicas. Esse critério praticamente elimina o falso alarme: uma variante
silenciosa passa nele por acaso em cerca de 2% dos casos com 1.024 *shots* e 0,3% com 4.096. O
total varia pouco entre as réplicas (de 81% a 87% com 1.024 *shots*), e a detecção robusta fica em
79% (IC 95%: 74%–83%), contra 94% no ideal. X, H e Z têm detecção robusta igual à do ideal em
todas as famílias (213/216). As células pequenas, porém, variam muito: a fração de RZ(π/16)
revelada nos oráculos, por exemplo, foi de 19% a 63% entre as réplicas com 1.024 *shots*, enquanto
só 3 das 27 variantes são detectadas de forma robusta. Nos reversíveis, a média de 15% de RZ(π/16)
revelados é toda falso alarme: nenhuma variante é detectada de forma robusta (0/29; IC 95%:
0%–12%).

| Grupo | Ideal | 1.024: média nas réplicas (mín–máx) | 1.024: detecção robusta | 4.096: média nas réplicas (mín–máx) | 4.096: detecção robusta |
|---|---|---|---|---|---|
| Todas as variantes | 338/360 = 94% (IC 91–96%) | 83,2% (81,4–86,9%) | 284/360 = 79% (IC 74–83%) | 83,5% (81,7–85,8%) | 286/360 = 79% (IC 75–83%) |
| X, H e Z (3 famílias) | 213/216 | 99% | 213/216 | 99% | 213/216 |
| T, reversíveis | 29/29 (IC 88–100%) | 85,5% (79,3–96,6%) | 23/29 (IC 62–90%) | 91,4% (79,3–100%) | 26/29 (IC 74–96%) |
| T, emaranhamento | 16/16 (IC 81–100%) | 95,0% (87,5–100%) | 16/16 (IC 81–100%) | 100% | 16/16 (IC 81–100%) |
| RZ(π/16), reversíveis | 29/29 (IC 88–100%) | 14,8% (6,9–27,6%) | 0/29 (IC 0–12%) | 14,1% (0–31,0%) | 0/29 (IC 0–12%) |
| RZ(π/16), oráculos | 22/27 (IC 63–92%) | 35,2% (18,5–63,0%) | 3/27 (IC 4–28%) | 29,6% (22,2–37,0%) | 2/27 (IC 2–23%) |
| RZ(π/16), emaranhamento | 3/16 (IC 7–43%) | 33,8% (12,5–56,2%) | 3/16 (IC 7–43%) | 38,1% (31,2–50,0%) | 3/16 (IC 7–43%) |
| Trabalho-base (\|0···0⟩, base Z) | 48,1% | 47,7% (46,1–51,9%) | — | 47,9% (45,6–50,3%) | — |
| Falso alarme por condição | — | 6,8% (IC 6,3–7,4%) | — | 4,8% (IC 4,3–5,2%) | — |

*Tabela R: 10 réplicas do experimento com ruído (FakeTorino). Média nas réplicas: fração de
variantes reveladas em alguma das 4 condições, em média entre as réplicas (mínimo e máximo entre
parênteses). Detecção robusta: variantes reveladas em mais da metade das réplicas. IC = intervalo
de confiança de Wilson de 95%. Arquivos: `results/resumo_replicas_<s>.csv` e
`results/falso_alarme_replicas_<s>.csv`.*

| Achado | 1.024 shots | 4.096 shots | Implicação |
|---|---|---|---|
| Distorção do golden pelo ruído (TVD com ruído × ideal) | 0,17–0,27 em média; pior caso 0,83 (`alu-v2_31`, \|+⟩ⁿ na base X) | 0,18–0,26 em média; pior caso 0,83 | Comparar com a saída ideal exige um piso alto |
| Piso com ruído (golden × golden) | 0,07–0,11 | 0,04–0,06 | Rodar o golden no mesmo processador preserva a sensibilidade |
| Detecção robusta, 10 réplicas (ideal: 94%) | 79% (284/360) | 79% (286/360) | O resultado não depende da rodada; o ruído custa ~15 p.p. |
| X, H e Z (detecção robusta) | 213/216, igual ao ideal | 213/216 | O ruído não esconde as portas "grandes" |
| T (detecção robusta) | Perde 6 de 29 nos reversíveis, todos no `alu-v2_31` | Perde 3 de 29 | Perda pequena, só no circuito mais ruidoso, e diminui com mais shots |
| RZ(π/16) (detecção robusta) | 0/29 nos reversíveis; 3/27 nos oráculos | 0/29; 2/27 | Efeito típico (TVD ≈ 0,01) abaixo do piso nos dois casos |
| Trabalho-base (\|0···0⟩, base Z): ideal → ruído | 48% → 48% (média nas réplicas) | 48% → 48% | O ruído não muda o peso da entrada e da base |
| Falsos alarmes por condição (10 réplicas) | 6,8% | 4,8% | Um pouco acima de 5% com 1.024 shots; o critério robusto resolve |

*Quadro V: síntese dos resultados no simulador com ruído (FakeTorino).*

**Calibração do critério.** Juntando as 10 réplicas, nas combinações em que a inserção não muda
em nada a saída ideal, o critério acusou diferença em 4,8% dos casos com 4.096 *shots* (IC 95%:
4,3%–5,2%), como esperado para o percentil 95, e em 6,8% com 1.024 (6,3%–7,4%), um pouco acima,
sobretudo na base X (até 8%). A causa provável é o *bootstrap*: o piso é estimado reamostrando a
distribuição medida do golden, e com 1.024 medições os resultados raros não aparecem nela, o que
deixa o piso levemente subestimado. Com quatro condições, o nível de falso alarme por variante
fica em cerca de 25% com 1.024 *shots* e 18% com 4.096 (linha tracejada na Fig. X). Por isso, numa
rodada única, barras com ruído abaixo ou perto dessa linha não devem ser lidas como detecção; a
detecção robusta (Tabela R) resolve o problema.

**Observação sobre as portas de fase.** Nos processadores IBM, Z, T e RZ(θ) são implementadas
como mudança de referencial (portas virtuais, sem duração nem erro). Um trojan de fase,
portanto, não acrescenta ruído ao circuito, e só se esconde quando o seu efeito fica abaixo
do piso. X e H, ao contrário, viram pulsos físicos.

**Limitações.** Usou-se um único modelo de ruído, de uma calibração do Torino; ele inclui
erros de porta, relaxação e leitura, mas não *crosstalk* nem erros coerentes, e não substitui
o processador real. O layout fixo em cadeia linear, sem otimização, pode superestimar o ruído
em relação a uma compilação comum. Com 1.024 *shots*, o piso por *bootstrap* fica levemente
subestimado (falso alarme de 6,8% por condição em vez de 5%); uma correção possível é estimar o
piso com execuções adicionais do golden. As réplicas medem a variação devida à amostragem, mas não
a devida à escolha dos circuitos, que continua limitada a 13. Como só duas entradas foram
executadas com ruído, ainda não é possível estimar a fração p de entradas reveladoras nem o k95
com ruído. Os resultados indicam, porém, que rotações de ângulo pequeno ficam praticamente
invisíveis nessas condições, mesmo com 4.096 *shots*, o que aponta para um k95 muito maior com
ruído nesse caso.

*Legenda da Fig. X (`fig_ruido_revela_1024.png`): variantes infectadas reveladas em pelo menos uma
das quatro condições (entrada |0···0⟩ ou |+⟩ⁿ, base Z ou X), no simulador ideal (mesmas quatro
condições) e com o modelo de ruído do FakeTorino, ambos com 1.024 shots, numa rodada. Os rótulos
k/n dão o número de variantes reveladas; n = variantes por porta. A linha tracejada marca o nível
de falso alarme por variante, calculado com a taxa por condição medida nas 10 réplicas (≈25% com
1.024 shots; ≈18% na versão com 4.096). A detecção robusta, nas 10 réplicas, está na Tabela R.*

*Legenda da Fig. Y (`fig_ruido_piso_1024.png`): por circuito, TVD entre a saída do golden com ruído
e a ideal (azul) e piso de ruído entre dois lotes do golden (laranja), na média das quatro
condições, em função do número de portas CZ depois da transpilação (1.024 shots). O pior caso por
condição chega a 0,83 (`alu-v2_31`, |+⟩ⁿ na base X).*

---

## Hipóteses: o que o experimento com ruído acrescenta

Os testes das hipóteses estão em `experiments/testes_hipoteses.py` (Gabriel), que lê o
`results/ideal.csv` e o `results/ruido_1024.csv` e grava `results/hipoteses_resumo.csv`. O quadro
abaixo resume esse arquivo e acrescenta o que vem do ambiente com ruído.

| Hipótese | Resultado (`hipoteses_resumo.csv`) | O que o ruído acrescenta |
|---|---|---|
| H1 | Atende nas 3 famílias: alguma condição revela de 36 a 60 p.p. a mais que o trabalho-base (McNemar, Holm) | Com ruído, o trabalho-base fica em 48% e as 4 condições em 83% (média de 10 réplicas) |
| H2 | Reversíveis: \|+⟩ⁿ revela mais (100% contra 0%). Oráculos e emaranhamento: \|+⟩ⁿ não revela mais (38% contra 53%; 50% contra 62%; p de Holm = 0,40) | — |
| H3 | Atende: nenhuma detecção de fase fora de "superposição + base X" | Com ruído, o padrão se mantém para Z e T; os RZ(π/16) ficam abaixo do piso |
| H4 | Não atende: posição + papel = 3,6% da importância SHAP | — |
| H5a | Atende: 96,4% das variantes visíveis com k95 ≤ 10 | — |
| H5b | Atende no total (mediana de k95 do RZ(π/16) = 5 contra 1); nos oráculos, não | Com ruído, nenhum RZ(π/16) dos reversíveis é detectado de forma robusta (0/29), com 1.024 ou 4.096 shots |
| H5c | Atende: 94% no ideal contra 82% com ruído (McNemar, p = 2,6 × 10⁻¹²) | Nas 10 réplicas: média de 83% e detecção robusta de 79% (IC 74–83%), com 1.024 ou 4.096 shots |

---

## Notas para o grupo (não colar)

- **Shots.** Principal: 1.024, o padrão do Qiskit (`AerSimulator.run` e Samplers locais), igual
  ao ideal desde o commit d8b3b79 do Gabriel. Sensibilidade: 4.096, o padrão da IBM Runtime
  (SamplerV2). Para comparação: o PDF do checkpoint falava em 4.000, Roy et al. e John et al.
  usaram 1.000, e o trabalho-base usou 512.
- **Não renomear `results/ruido_1024.csv`.** O `testes_hipoteses.py` lê esse arquivo para a H5c.
  Ele é a réplica 0 de `results/ruido_replicas_1024.csv`.
- **Variabilidade entre rodadas.** As 10 réplicas quantificam o que as rodadas anteriores (1.000 e
  4.000 shots) já sugeriam: o total varia pouco (desvio-padrão de 1 a 2 p.p.), mas células com
  poucas variantes variam muito (RZ nos oráculos: de 19% a 63% com 1.024 shots). Para afirmações
  sobre células pequenas, usar a detecção robusta da Tabela R, não a rodada única.
- **Figura com as réplicas.** Se o grupo preferir, a Fig. X pode mostrar a detecção robusta (10
  réplicas) em vez da rodada única; aí a linha de falso alarme deixa de ser necessária.
- **Escopo x PDF.** A seção VI.D do PDF ainda fala em dois *fake backends* e em 16 estados da
  base e 16 de produto com ruído. O que rodou foi um backend e só |0···0⟩ e |+⟩ⁿ, como está na
  aba G3. Se quiserem p e k95 com ruído, dá para estender `ENTRADAS` em `rodar_ruido.py` para 16
  estados da base.
- **Tabela I.** O PDF lista Deutsch-Jozsa e Grover entre os oráculos. A seleção (Tabela 1 da
  aba G3) tem Deutsch, BV e Simon: o dataset não tem DJ além do `deutsch_n2`, e Grover saiu do
  escopo.
