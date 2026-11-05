# Rascunho: ambiente com ruído (J2 e J3)

Texto para colar no Docs. A parte de metodologia complementa a seção 6.4 (aba G3); a parte de
resultados entra na seção de resultados. O experimento foi rodado com **1.024 shots** (principal,
o padrão do Qiskit e o mesmo valor do simulador ideal) e com **4.096 shots** (análise de
sensibilidade, o padrão da IBM Runtime).

**Figuras sugeridas:** no corpo do texto, só as de 1.024 shots (`results/fig_ruido_revela_1024.png`
e `results/fig_ruido_piso_1024.png`). A sensibilidade a 4.096 shots entra só na Tabela W; a figura
de 4.096 (`results/fig_ruido_revela_4096.png`) fica como material complementar.

Arquivos (`<s>` = 1024 ou 4096): `results/piso_ruido_<s>.csv`, `results/ruido_<s>.csv`,
`results/resumo_*ruido*_<s>.csv`, `results/fig_ruido_revela_<s>.png` e
`results/fig_ruido_piso_<s>.png`. Para reproduzir:

```
python experiments/rodar_ruido.py --shots 1024      # ~3 min
python experiments/consolidar_ruido.py --shots 1024
python experiments/figuras_ruido.py --shots 1024
```

(e o mesmo com `--shots 4096`). As sementes são fixas, então os números se repetem.

---

## Metodologia: simulador com ruído (complemento da seção 6.4)

No simulador com ruído, usa-se o modelo do processador IBM Torino (*fake backend* `FakeTorino`
do Qiskit, 133 qubits, portas nativas CZ, √X, X e RZ), que reúne erros de porta, relaxação
térmica e erros de leitura medidos em uma calibração do processador. Os 13 circuitos golden e as
360 variantes infectadas rodam com duas entradas, |0···0⟩ e |+⟩ⁿ, medidas nas bases Z e X, em um
total de 1.492 execuções. Cada execução usa 1.024 *shots*, o mesmo número do simulador ideal; o
experimento foi repetido com 4.096 *shots*, o padrão da IBM Runtime, para avaliar a
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
de variantes reveladas cai de 94% (338/360) no ideal para 82% (295/360) com ruído (Fig. X). A
queda vem principalmente de RZ(π/16): de 29/29 para 4/29 nos reversíveis e de 22/27 para 11/27
nos oráculos. A maior parte dessas inserções muda a saída ideal em uma TVD de apenas 0,01, bem
abaixo do piso com ruído. Os 4/29 dos reversíveis não são detecções: na única condição em que a
rotação aparece no ideal (|+⟩ⁿ medido na base X), nenhuma foi detectada com ruído, e uma variante
silenciosa testada em quatro condições, cada uma com 5% de falso alarme, "aparece" por acaso em
cerca de 1 − 0,95⁴ ≈ 19% das vezes (linha tracejada na Fig. X). Nos circuitos de emaranhamento,
em que essa rotação já era pouco visível no ideal (3/16), ficam 2/16. T também perde um pouco
nos reversíveis (de 29/29 para 24/29) e no emaranhamento (de 16/16 para 15/16); X, H e Z são
reveladas na mesma proporção que no ideal. Na condição do trabalho-base (|0···0⟩ medido na base
Z), a fração é de 48% no ideal e de 47% com ruído. Ou seja, o ruído não muda a conclusão de que a
entrada e a base de medição são o que mais pesa para um trojan aparecer.

**Sensibilidade ao número de shots.** Com 4.096 *shots*, o piso cai pela metade, e inserções de
efeito intermediário passam a aparecer. É o caso dos RZ(π/16) do emaranhamento que mudam a saída
ideal em uma TVD de 0,05 a 0,08: os três visíveis no ideal são todos detectados com 4.096 *shots*
(com 1.024, dois deles). Com isso, essa célula vai a 5/16, acima do ideal (3/16); as duas
variantes a mais não aparecem no ideal e são compatíveis com falso alarme. Com n = 16, cada
variante vale cerca de 6 pontos percentuais. T também se recupera (de 90,5% para 94,3% das
combinações visíveis no ideal). A maior parte dos RZ(π/16), porém, com efeito de 0,01, continua
abaixo do piso: nos reversíveis, a célula segue em 4/29, abaixo do nível de falso alarme. Como o
piso diminui com a raiz do número de *shots*, enxergar essas inserções exigiria um piso cerca de
quatro vezes menor, isto é, da ordem de 16 vezes mais *shots* (cerca de 65 mil). No total, a
fração de variantes reveladas com ruído vai de 82% para 84% (303/360; Tabela W). O custo de
encontrar um trojan, portanto, depende do orçamento de medições do usuário, e as inserções de
ângulo muito pequeno ficam fora do alcance de um autoteste com orçamento usual.

| Resultado | 1.024 shots | 4.096 shots |
|---|---|---|
| Combinações visíveis no ideal que continuam visíveis com ruído | 90,0% (533/592) | 91,8% (547/596) |
| Continuam visíveis, por porta: X, H e Z / T / RZ(π/16) | 100% / 90,5% / 8,9% | 100% / 94,3% / 21,4% |
| Variantes reveladas em alguma das 4 condições: ideal → ruído | 338 → 295 de 360 (94% → 82%) | 338 → 303 de 360 (94% → 84%) |
| RZ(π/16), reversíveis: ideal → ruído | 29/29 → 4/29² | 29/29 → 4/29² |
| RZ(π/16), oráculos: ideal → ruído | 22/27 → 11/27 | 22/27 → 10/27 |
| RZ(π/16), emaranhamento: ideal → ruído | 3/16 → 2/16 | 3/16 → 5/16³ |
| T, reversíveis: ideal → ruído | 29/29 → 24/29 | 29/29 → 28/29 |
| T, emaranhamento: ideal → ruído | 16/16 → 15/16 | 16/16 → 16/16 |
| Trabalho-base (\|0···0⟩, base Z): ideal → ruído | 48,1% → 46,9% | 48,1% → 47,5% |
| Falsos alarmes por condição (812 combinações sem efeito no ideal) | 5,0% | 4,4% |
| Piso com ruído (mínimo–máximo) | 0,044–0,289 | 0,022–0,151 |

*Tabela W: resultados com ruído para os dois números de shots (FakeTorino); "ideal" = mesmas
4 condições. ² Abaixo do nível de falso alarme (≈ 19% por variante): na condição em que a rotação
aparece no ideal, a detecção com ruído foi de 0% (1.024) e 7% (4.096). ³ Os 3 visíveis no ideal
mais 2 compatíveis com falso alarme.*

| Achado | 1.024 shots | 4.096 shots | Implicação |
|---|---|---|---|
| Distorção do golden pelo ruído (TVD com ruído × ideal) | 0,17–0,27 em média; pior caso 0,83 (`alu-v2_31`, \|+⟩ⁿ na base X) | 0,18–0,26 em média; pior caso 0,83 | Comparar com a saída ideal exige um piso alto |
| Piso com ruído (golden × golden) | 0,07–0,11 | 0,04–0,06 | Rodar o golden no mesmo processador preserva a sensibilidade |
| Detecções do ideal que se mantêm: X, H e Z | 100% | 100% | O ruído não esconde as portas "grandes" |
| Detecções do ideal que se mantêm: T | 90,5% | 94,3% | Perda pequena, que diminui com mais shots |
| Detecções do ideal que se mantêm: RZ(π/16) | 8,9% | 21,4% | Efeito típico (TVD ≈ 0,01) abaixo do piso nos dois casos |
| Trabalho-base (\|0···0⟩, base Z): ideal → ruído | 48,1% → 46,9% | 48,1% → 47,5% | O ruído não muda o peso da entrada e da base |
| Falsos alarmes por condição | 5,0% | 4,4% | Critério calibrado (esperado: 5%) |

*Quadro V: síntese dos resultados no simulador com ruído (FakeTorino).*

**Calibração do critério.** Nas 812 combinações em que a inserção não muda em nada a saída
ideal, o critério acusou diferença em 5,0% dos casos com 1.024 *shots* e em 4,4% com 4.096, como
esperado para o percentil 95. São falsos alarmes de amostragem, que também explicam pequenos
ganhos aparentes com ruído (por exemplo, Z em oráculos com 4.096 *shots*, de 26/27 para 27/27).
Ao combinar quatro condições, a chance de falso alarme para uma variante silenciosa chega a cerca
de 1 − 0,95⁴ ≈ 19%. Por isso, na Fig. X, barras com ruído abaixo ou perto da linha tracejada não
devem ser lidas como detecção.

**Observação sobre as portas de fase.** Nos processadores IBM, Z, T e RZ(θ) são implementadas
como mudança de referencial (portas virtuais, sem duração nem erro). Um trojan de fase,
portanto, não acrescenta ruído ao circuito, e só se esconde quando o seu efeito fica abaixo
do piso. X e H, ao contrário, viram pulsos físicos.

**Limitações.** Usou-se um único modelo de ruído, de uma calibração do Torino; ele inclui
erros de porta, relaxação e leitura, mas não *crosstalk* nem erros coerentes, e não substitui
o processador real. O layout fixo em cadeia linear, sem otimização, pode superestimar o ruído
em relação a uma compilação comum. Como só duas entradas foram executadas com ruído, ainda não
é possível estimar a fração p de entradas reveladoras nem o k95 com ruído. Os resultados
indicam, porém, que rotações de ângulo pequeno ficam praticamente invisíveis nessas condições,
mesmo com 4.096 *shots*, o que aponta para um k95 muito maior com ruído nesse caso.

*Legenda da Fig. X (`fig_ruido_revela_1024.png`): variantes infectadas reveladas em pelo menos uma
das quatro condições (entrada |0···0⟩ ou |+⟩ⁿ, base Z ou X), no simulador ideal (mesmas quatro
condições) e com o modelo de ruído do FakeTorino, ambos com 1.024 shots. Os rótulos k/n dão o
número de variantes reveladas; n = variantes por porta. A linha tracejada marca o nível de falso
alarme esperado com ruído para uma variante silenciosa (1 − 0,95⁴ ≈ 19%).*

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
| H1 | Atende nas 3 famílias: alguma condição revela de 36 a 60 p.p. a mais que o trabalho-base (McNemar, Holm) | Com ruído, o trabalho-base fica em 47% e as 4 condições em 82% |
| H2 | Reversíveis: \|+⟩ⁿ revela mais (100% contra 0%). Oráculos e emaranhamento: \|+⟩ⁿ não revela mais (38% contra 53%; 50% contra 62%; p de Holm = 0,40) | — |
| H3 | Atende: nenhuma detecção de fase fora de "superposição + base X" | Com ruído, o padrão se mantém para Z e T; os RZ(π/16) ficam abaixo do piso |
| H4 | Não atende: posição + papel = 3,6% da importância SHAP | — |
| H5a | Atende: 96,4% das variantes visíveis com k95 ≤ 10 | — |
| H5b | Atende no total (mediana de k95 do RZ(π/16) = 5 contra 1); nos oráculos, não | Com ruído, a maior parte dos RZ(π/16) fica abaixo do piso com 1.024 e com 4.096 shots |
| H5c | Atende: 94% no ideal contra 82% com ruído (McNemar, p = 2,6 × 10⁻¹²) | Com 4.096 shots, 84%; a perda continua concentrada nos RZ(π/16) |

---

## Notas para o grupo (não colar)

- **Shots.** Principal: 1.024, o padrão do Qiskit (`AerSimulator.run` e Samplers locais), igual
  ao ideal desde o commit d8b3b79 do Gabriel. Sensibilidade: 4.096, o padrão da IBM Runtime
  (SamplerV2). Para comparação: o PDF do checkpoint falava em 4.000, Roy et al. e John et al.
  usaram 1.000, e o trabalho-base usou 512.
- **Não renomear `results/ruido_1024.csv`.** O `testes_hipoteses.py` lê esse arquivo para a H5c.
- **Variabilidade entre rodadas.** Rodadas anteriores com 1.000 e 4.000 shots funcionam quase
  como réplicas independentes, porque as amostras sorteadas mudam. O total ficou estável (84%
  com 1.000, 82% com 1.024, 86% com 4.000 e 84% com 4.096), mas células com poucas variantes
  oscilaram bastante: RZ(π/16) em emaranhamento deu 38% (1.000), 12% (1.024), 25% (4.000) e 31%
  (4.096); RZ(π/16) nos reversíveis deu 28% com 4.000 e 14% com 4.096. Por isso as figuras
  trazem as contagens e a linha de falso alarme.
- **Escopo x PDF.** A seção VI.D do PDF ainda fala em dois *fake backends* e em 16 estados da
  base e 16 de produto com ruído. O que rodou foi um backend e só |0···0⟩ e |+⟩ⁿ, como está na
  aba G3. Se quiserem p e k95 com ruído, dá para estender `ENTRADAS` em `rodar_ruido.py` para 16
  estados da base.
- **Tabela I.** O PDF lista Deutsch-Jozsa e Grover entre os oráculos. A seleção (Tabela 1 da
  aba G3) tem Deutsch, BV e Simon: o dataset não tem DJ além do `deutsch_n2`, e Grover saiu do
  escopo.
