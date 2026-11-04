# Rascunho: ambiente com ruído (J2 e J3)

Texto para colar no Docs. A parte de metodologia complementa a seção 6.4 (aba G3); a parte de
resultados entra na seção de resultados. O experimento foi rodado com **1.024 shots** (principal,
o padrão do Qiskit) e com **4.096 shots** (análise de sensibilidade, o padrão da IBM Runtime).
As tabelas trazem os dois.

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
total de 1.492 execuções. Cada execução usa 1.024 *shots*, o padrão do Qiskit; o experimento foi
repetido com 4.096 *shots*, o padrão da IBM Runtime, para avaliar a sensibilidade a esse
parâmetro. Golden e infectado passam pela mesma transpilação mínima (nível de otimização 0), com
os qubits lógicos fixos nos qubits físicos 0 a n−1, que formam uma cadeia linear no processador.
Em nenhuma variante a porta inserida alterou o roteamento: golden e infectado têm o mesmo número
de portas CZ.

O piso de ruído é estimado por circuito, entrada e base, a partir de execuções independentes do
golden. Das frequências medidas do golden, sorteiam-se 500 pares de lotes com o mesmo número de
*shots* (*bootstrap*), e o piso é o percentil 95 da TVD entre os lotes de cada par. Uma inserção
conta como visível quando a TVD entre golden e infectado, ambos executados com ruído, passa desse
piso. Para comparação, registra-se também o resultado ideal com o mesmo número de *shots* e uma
variante em que a referência é a saída ideal do golden, calculada classicamente.

## Resultados no simulador com ruído

**O ruído afasta a saída da ideal, mas o piso continua baixo.** Executado com ruído, o golden
se afasta da sua saída ideal por uma TVD média de 0,18 (emaranhamento), 0,18 (oráculos) e
0,26 (reversíveis), chegando a 0,83 no `alu-v2_31`, que tem 311 portas CZ depois da
transpilação. Esse afastamento cresce com o número de portas de dois qubits (Fig. Y). O piso,
porém, fica em 0,07 a 0,11 em média com 1.024 *shots* (0,04 a 0,06 com 4.096), porque o ruído é
o mesmo nos dois lotes comparados. Se a referência fosse a saída ideal, o piso teria de absorver
o próprio ruído e subiria para 0,20 a 0,30 em média.

| Família | CZ (média) | Golden com ruído × ideal¹ | Piso ideal (1.024) | Piso com ruído (1.024) | Piso ideal (4.096) | Piso com ruído (4.096) |
|---|---|---|---|---|---|---|
| Reversíveis | 104 | 0,260 | 0,037 | 0,091 | 0,019 | 0,046 |
| Oráculos | 25 | 0,180 | 0,060 | 0,112 | 0,030 | 0,058 |
| Emaranhamento | 9 | 0,176 | 0,041 | 0,073 | 0,021 | 0,036 |

*Tabela Z: piso e distorção médios por família (FakeTorino, média das 4 condições de entrada e
base). ¹ Estimada com 4.096 shots; com 1.024, a amostragem acrescenta de 0,00 a 0,02.*

**Quase tudo que aparece no ideal continua aparecendo com ruído.** Com 1.024 *shots*, das 592
combinações de variante, entrada e base em que a inserção é visível no ideal, 90,0% continuam
visíveis com ruído. As 59 que deixam de aparecer têm, em geral, impacto ideal muito pequeno
(TVD mediana de 0,010). X, H e Z continuam visíveis em 100% das combinações, T em 90,5% e
RZ(π/16) em apenas 8,9%.

**A perda se concentra nas rotações sutis.** Considerando as quatro condições juntas (entrada
|0···0⟩ ou |+⟩ⁿ, base Z ou X), a fração de variantes reveladas cai de 94% no ideal para 82% com
ruído (Fig. X). A queda vem principalmente de RZ(π/16): de 100% para 14% nos reversíveis e de
81% para 41% nos oráculos. A maior parte dessas inserções muda a saída ideal em uma TVD de apenas
0,01, bem abaixo do piso com ruído. Nos reversíveis, na única condição em que a rotação aparece no
ideal (|+⟩ⁿ medido na base X), nenhuma foi detectada com ruído; os 14% restantes são compatíveis
com falsos alarmes nas outras condições. Nos circuitos de emaranhamento, em que essa rotação já
era pouco visível no ideal (19%), fica em 12%. T também perde um pouco nos reversíveis (de 100%
para 83%) e no emaranhamento (de 100% para 94%); X, H e Z são reveladas na mesma proporção que no
ideal. Na condição do trabalho-base (|0···0⟩ medido na base Z), a fração é de 48% no ideal e de
47% com ruído. Ou seja, o ruído não muda a conclusão de que a entrada e a base de medição são o
que mais pesa para um trojan aparecer.

**Sensibilidade ao número de shots.** Com 4.096 *shots*, o piso cai pela metade, e inserções de
efeito intermediário passam a aparecer. É o caso dos RZ(π/16) do emaranhamento, que mudam a saída
ideal em uma TVD de 0,05 a 0,08: com 1.024 *shots* ficam abaixo do piso e quase não são
detectados; com 4.096, todos são. T também se recupera (de 90,5% para 94,3% das combinações
visíveis no ideal). A maior parte dos RZ(π/16), porém, com efeito de 0,01, continua abaixo do
piso: nos reversíveis, a fração revelada segue em 14%, no nível de falso alarme. Como o piso
diminui com a raiz do número de *shots*, enxergar essas inserções exigiria um piso cerca de quatro
vezes menor, isto é, da ordem de 16 vezes mais *shots* (cerca de 65 mil). No total, a fração de
variantes reveladas com ruído vai de 82% para 84% (Tabela W). O custo de encontrar um trojan,
portanto, depende do orçamento de medições do usuário, e as inserções de ângulo muito pequeno
ficam fora do alcance de um autoteste com orçamento usual.

| Resultado | 1.024 shots | 4.096 shots |
|---|---|---|
| Combinações visíveis no ideal que continuam visíveis com ruído | 90,0% (533/592) | 91,8% (547/596) |
| Continuam visíveis, por porta: X, H e Z / T / RZ(π/16) | 100% / 90,5% / 8,9% | 100% / 94,3% / 21,4% |
| Variantes reveladas em alguma das 4 condições: ideal → ruído | 94% → 82% | 94% → 84% |
| RZ(π/16), reversíveis: ideal → ruído | 100% → 14%² | 100% → 14%² |
| RZ(π/16), oráculos: ideal → ruído | 81% → 41% | 81% → 37% |
| RZ(π/16), emaranhamento: ideal → ruído | 19% → 12% | 19% → 31%³ |
| T, reversíveis: ideal → ruído | 100% → 83% | 100% → 97% |
| T, emaranhamento: ideal → ruído | 100% → 94% | 100% → 100% |
| Trabalho-base (\|0···0⟩, base Z): ideal → ruído | 48,1% → 46,9% | 48,1% → 47,5% |
| Falsos alarmes (812 combinações sem efeito no ideal) | 5,0% | 4,4% |
| Piso com ruído (mínimo–máximo) | 0,044–0,289 | 0,022–0,151 |

*Tabela W: resultados com ruído para os dois números de shots (FakeTorino). ² No nível de falso
alarme: na condição em que a rotação aparece no ideal, a detecção com ruído foi de 0% (1.024) e
7% (4.096). ³ Inclui falsos alarmes.*

| Achado | 1.024 shots | 4.096 shots | Implicação |
|---|---|---|---|
| Distorção do golden pelo ruído (TVD com ruído × ideal) | 0,18–0,26 em média; até 0,83 (`alu-v2_31`) | igual | Comparar com a saída ideal exige um piso alto |
| Piso com ruído (golden × golden) | 0,07–0,11 | 0,04–0,06 | Rodar o golden no mesmo processador preserva a sensibilidade |
| Detecções do ideal que se mantêm: X, H e Z | 100% | 100% | O ruído não esconde as portas "grandes" |
| Detecções do ideal que se mantêm: T | 90,5% | 94,3% | Perda pequena, que diminui com mais shots |
| Detecções do ideal que se mantêm: RZ(π/16) | 8,9% | 21,4% | Efeito típico (TVD ≈ 0,01) abaixo do piso nos dois casos |
| Trabalho-base (\|0···0⟩, base Z): ideal → ruído | 48,1% → 46,9% | 48,1% → 47,5% | O ruído não muda o peso da entrada e da base |
| Falsos alarmes | 5,0% | 4,4% | Critério calibrado (esperado: 5%) |

*Quadro V: síntese dos resultados no simulador com ruído (FakeTorino).*

**Calibração do critério.** Nas 812 combinações em que a inserção não muda em nada a saída
ideal, o critério acusou diferença em 5,0% dos casos com 1.024 *shots* e em 4,4% com 4.096, como
esperado para o percentil 95. São falsos alarmes de amostragem, que também explicam pequenos
ganhos aparentes com ruído (por exemplo, Z em oráculos com 4.096 *shots*, de 96% para 100%). Ao
combinar quatro condições, a chance de falso alarme para uma variante silenciosa chega a cerca
de 1 − 0,95⁴ ≈ 19%, o que precisa ser considerado ao ler os números agregados.

**Observação sobre as portas de fase.** Nos processadores IBM, Z, T e RZ(θ) são implementadas
como mudança de referencial (portas virtuais, sem duração nem erro). Um trojan de fase,
portanto, não acrescenta ruído ao circuito, e só se esconde quando o seu efeito fica abaixo
do piso. X e H, ao contrário, viram pulsos físicos.

**Limitações.** Usou-se um único modelo de ruído, de uma calibração do Torino; ele inclui
erros de porta, relaxação e leitura, mas não *crosstalk* nem erros coerentes, e não substitui
o processador real. O layout fixo em cadeia linear, sem otimização, pode superestimar o ruído
em relação a uma compilação comum. Como só duas entradas foram executadas com ruído, ainda não
é possível estimar a fração p de entradas reveladoras nem o k95 com ruído (SQ3, H5). Os
resultados indicam, porém, que rotações de ângulo pequeno ficam praticamente invisíveis nessas
condições, mesmo com 4.096 *shots*, o que aponta para um k95 muito maior com ruído nesse caso.

*Legenda da Fig. X (`fig_ruido_revela_1024.png`): fração de variantes infectadas reveladas em
pelo menos uma das quatro condições (entrada |0···0⟩ ou |+⟩ⁿ, base Z ou X), no simulador ideal e
com o modelo de ruído do FakeTorino (1.024 shots). n = número de variantes por porta. A versão
com 4.096 shots está em `fig_ruido_revela_4096.png`.*

*Legenda da Fig. Y (`fig_ruido_piso_1024.png`): TVD média entre a saída do golden com ruído e a
ideal (azul) e piso de ruído entre dois lotes do golden (laranja), por circuito, em função do
número de portas CZ depois da transpilação (1.024 shots).*

---

## Quadro resumo das hipóteses (ideal + ruído)

Para a discussão. Os números do ideal vêm do `results/ideal.csv` e dos `results/resumo_*.csv` do
Gabriel (1.000 shots); os do ruído, deste experimento.

| Hipótese | Situação | Evidência principal |
|---|---|---|
| H1: o impacto de trojans de fase e controlados depende da entrada e da família | Confirmada para as portas de fase; a parte dos trojans controlados não foi testada (CZ ficou fora do escopo) | Z nos reversíveis: 0% com \|0···0⟩ na base Z e 100% com \|+⟩ⁿ na base X; nos oráculos, 48% com \|0···0⟩ na base Z |
| H2: em famílias com interferência, \|+⟩ⁿ revela mais que \|0···0⟩ | Não confirmada (efeito contrário) | Z em oráculos, base Z: 48% com \|0···0⟩ e 4% com \|+⟩ⁿ; T em emaranhamento, base X: 81% e 56%. Esses circuitos começam com H, que leva \|+⟩ⁿ a \|0···0⟩; o que importa é haver superposição no ponto da inserção e a base de medição certa |
| H3: nos reversíveis, a fase só aparece com entrada em superposição medida em X | Confirmada | Z, T e RZ: 0% com qualquer entrada da base computacional, em qualquer base; 100% com \|+⟩ⁿ medido em X. Com ruído, o padrão se mantém para Z e T (fora os falsos alarmes); RZ(π/16) fica abaixo do piso |
| H4: com a entrada variando, posição e papel do qubit passam a pesar | Pendente (SHAP/regressão) | Na tabela descritiva, a fração revelada quase não varia com posição e papel (reversíveis 100%; oráculos 96–100%; emaranhamento 80–87%), mas essa medida satura perto de 100% |
| H5: poucos testes bastam; entradas raras e ruído aumentam o número | Parcialmente confirmada | k95 mediano de 1 na maioria; RZ(π/16) nos reversíveis tem mediana 5 e máximo 23. Com ruído, a maior parte dos RZ(π/16) fica abaixo do piso com 1.024 e com 4.096 shots (nos reversíveis, detecção no nível de falso alarme); o k95 com ruído não foi medido |

*Quadro resumo: hipóteses e evidências.*

---

## Notas para o grupo (não colar)

- **Shots.** Principal: 1.024, o padrão do Qiskit (`AerSimulator.run` e Samplers locais).
  Sensibilidade: 4.096, o padrão da IBM Runtime (SamplerV2). Para comparação: o PDF do
  checkpoint falava em 4.000, Roy et al. e John et al. usaram 1.000, e o trabalho-base usou 512.
- **O ideal ainda está em 1.000 shots.** O `rodar_ideal.py` usa `SHOTS = 1000`. A comparação
  ideal × ruído deste rascunho já usa o ideal com 1.024 (calculado em `rodar_ruido.py`), mas, para
  o artigo inteiro ficar coerente, é preciso trocar para 1024 lá e rodar o ideal de novo (junto
  com a correção do arredondamento, abaixo).
- **Variabilidade entre rodadas.** Rodadas anteriores com 1.000 e 4.000 shots funcionam quase
  como réplicas independentes, porque as amostras sorteadas mudam. O total ficou estável (84%
  com 1.000, 82% com 1.024, 86% com 4.000 e 84% com 4.096), mas células com poucas variantes
  oscilaram bastante: RZ(π/16) em emaranhamento deu 38% (1.000), 12% (1.024), 25% (4.000) e 31%
  (4.096); RZ(π/16) nos reversíveis deu 28% com 4.000 e 14% com 4.096. Vale mostrar contagens ou
  intervalos de confiança nas células pequenas e não dar destaque a elas.
- **Escopo x PDF.** A seção VI.D do PDF ainda fala em dois *fake backends* e em 16 estados da
  base e 16 de produto com ruído. O que rodou foi um backend e só |0···0⟩ e |+⟩ⁿ, como está na
  aba G3. Se quiserem p e k95 com ruído, dá para estender `ENTRADAS` em `rodar_ruido.py` para 16
  estados da base.
- **Bug de arredondamento no ideal.** Quando a saída ideal é determinística, o piso é 0 e uma
  TVD de ~1e-16 conta como "revela". No `results/ideal.csv` isso acontece em uma linha
  (`bv_4`, base Z, T, início, ativo: `revela_zeros = True` com TVD 4,4e-16), o que muda o
  "trabalho-base" de oráculo/T de 0,52 para 0,48. Correção: comparar com `max(piso, 1e-9)` em
  `rodar_ideal.py` (como já está em `rodar_ruido.py`) e rodar de novo.
- **Tabela I.** O PDF lista Deutsch-Jozsa e Grover entre os oráculos. A seleção (Tabela 1 da
  aba G3) tem Deutsch, BV e Simon: o dataset não tem DJ além do `deutsch_n2`, e Grover saiu do
  escopo.
