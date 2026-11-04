# Rascunho: ambiente com ruído (J2 e J3)

Texto para colar no Docs. A parte de metodologia complementa a seção 6.4 (aba G3); a parte de
resultados entra na seção de resultados. O experimento foi rodado com **1.000 shots** (principal,
o mesmo valor do simulador ideal) e com **4.000 shots** (análise de sensibilidade, o valor que
estava no PDF do checkpoint). As tabelas trazem os dois.

Arquivos (`<s>` = 1000 ou 4000): `results/piso_ruido_<s>.csv`, `results/ruido_<s>.csv`,
`results/resumo_*ruido*_<s>.csv`, `results/fig_ruido_revela_<s>.png` e
`results/fig_ruido_piso_<s>.png`. Para reproduzir:

```
python experiments/rodar_ruido.py --shots 1000      # ~3 min
python experiments/consolidar_ruido.py --shots 1000
python experiments/figuras_ruido.py --shots 1000
```

(e o mesmo com `--shots 4000`). As sementes são fixas, então os números se repetem.

---

## Metodologia: simulador com ruído (complemento da seção 6.4)

No simulador com ruído, usa-se o modelo do processador IBM Torino (*fake backend* `FakeTorino`
do Qiskit, 133 qubits, portas nativas CZ, √X, X e RZ), que reúne erros de porta, relaxação
térmica e erros de leitura medidos em uma calibração do processador. Os 13 circuitos golden e as
360 variantes infectadas rodam com duas entradas, |0···0⟩ e |+⟩ⁿ, medidas nas bases Z e X, em um
total de 1.492 execuções. Cada execução usa 1.000 *shots*, o mesmo número do simulador ideal; o
experimento foi repetido com 4.000 *shots* para avaliar a sensibilidade a esse parâmetro. Golden e
infectado passam pela mesma transpilação mínima (nível de otimização 0), com os qubits lógicos
fixos nos qubits físicos 0 a n−1, que formam uma cadeia linear no processador. Em nenhuma
variante a porta inserida alterou o roteamento: golden e infectado têm o mesmo número de
portas CZ.

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
porém, fica em 0,07 a 0,11 em média com 1.000 *shots* (0,04 a 0,06 com 4.000), porque o ruído é
o mesmo nos dois lotes comparados. Se a referência fosse a saída ideal, o piso teria de absorver
o próprio ruído e subiria para 0,20 a 0,31 em média.

| Família | CZ (média) | Golden com ruído × ideal¹ | Piso ideal (1.000) | Piso com ruído (1.000) | Piso ideal (4.000) | Piso com ruído (4.000) |
|---|---|---|---|---|---|---|
| Reversíveis | 104 | 0,259 | 0,037 | 0,093 | 0,019 | 0,047 |
| Oráculos | 25 | 0,181 | 0,061 | 0,113 | 0,031 | 0,058 |
| Emaranhamento | 9 | 0,177 | 0,041 | 0,073 | 0,021 | 0,037 |

*Tabela Z: piso e distorção médios por família (FakeTorino, média das 4 condições de entrada e
base). ¹ Estimada com 4.000 shots; com 1.000, a amostragem acrescenta de 0,00 a 0,02.*

**Quase tudo que aparece no ideal continua aparecendo com ruído.** Com 1.000 *shots*, das 591
combinações de variante, entrada e base em que a inserção é visível no ideal, 90,5% continuam
visíveis com ruído. As 56 que deixam de aparecer têm, em geral, impacto ideal muito pequeno
(TVD mediana de 0,010). X, H e Z continuam visíveis em 100% das combinações, T em 91,7% e
RZ(π/16) em apenas 10,9%.

**A perda se concentra nas rotações sutis.** Considerando as quatro condições juntas (entrada
|0···0⟩ ou |+⟩ⁿ, base Z ou X), a fração de variantes reveladas cai de 94% no ideal para 84% com
ruído (Fig. X). A queda vem quase toda de RZ(π/16): de 100% para 17% nos reversíveis e de 81% para
33% nos oráculos. T também perde um pouco nos reversíveis (de 100% para 90%); X, H e Z são
reveladas na mesma proporção que no ideal. Nos circuitos de emaranhamento, RZ(π/16) já era pouco
visível no ideal (19%); o aumento aparente com ruído (38%) é compatível com falsos alarmes
acumulados nas quatro condições (ver abaixo). Na condição do trabalho-base (|0···0⟩ medido na
base Z), a fração é de 48% no ideal e de 47% com ruído. Ou seja, o ruído não muda a conclusão de
que a entrada e a base de medição são o que mais pesa para um trojan aparecer.

**Sensibilidade ao número de shots.** Com 4.000 *shots*, o piso cai pela metade e parte das
rotações sutis volta a aparecer: RZ(π/16) sobe para 28% nos reversíveis e 48% nos oráculos, T nos
reversíveis volta a 100%, e o total revelado com ruído vai a 86% (Tabela W). As demais portas e a
condição do trabalho-base não mudam. O custo de encontrar um trojan, portanto, depende do
orçamento de medições do usuário, sobretudo para inserções de ângulo pequeno.

| Resultado | 1.000 shots | 4.000 shots |
|---|---|---|
| Combinações visíveis no ideal que continuam visíveis com ruído | 90,5% (535/591) | 92,4% (551/596) |
| Continuam visíveis, por porta: X, H e Z / T / RZ(π/16) | 100% / 91,7% / 10,9% | 100% / 95,5% / 26,8% |
| Variantes reveladas em alguma das 4 condições: ideal → ruído | 94% → 84% | 94% → 86% |
| RZ(π/16), reversíveis: ideal → ruído | 100% → 17% | 100% → 28% |
| RZ(π/16), oráculos: ideal → ruído | 81% → 33% | 81% → 48% |
| RZ(π/16), emaranhamento: ideal → ruído | 19% → 38%² | 19% → 25%² |
| T, reversíveis: ideal → ruído | 100% → 90% | 100% → 100% |
| Trabalho-base (\|0···0⟩, base Z): ideal → ruído | 48% → 47% | 48% → 48% |
| Falsos alarmes (812 combinações sem efeito no ideal) | 6,3% | 4,8% |
| Piso com ruído (mínimo–máximo) | 0,044–0,291 | 0,023–0,153 |

*Tabela W: resultados com ruído para os dois números de shots (FakeTorino). ² Aumento aparente,
compatível com falsos alarmes.*

| Achado | 1.000 shots | 4.000 shots | Implicação |
|---|---|---|---|
| Distorção do golden pelo ruído (TVD com ruído × ideal) | 0,18–0,26 em média; até 0,83 (`alu-v2_31`) | igual | Comparar com a saída ideal exige um piso alto |
| Piso com ruído (golden × golden) | 0,07–0,11 | 0,04–0,06 | Rodar o golden no mesmo processador preserva a sensibilidade |
| Detecções do ideal que se mantêm: X, H e Z | 100% | 100% | O ruído não esconde as portas "grandes" |
| Detecções do ideal que se mantêm: T | 92% | 96% | Perda pequena, só nos reversíveis |
| Detecções do ideal que se mantêm: RZ(π/16) | 11% | 27% | Rotações sutis ficam praticamente invisíveis |
| Trabalho-base (\|0···0⟩, base Z): ideal → ruído | 48% → 47% | 48% → 48% | O ruído não muda o peso da entrada e da base |
| Falsos alarmes | 6,3% | 4,8% | Critério calibrado (esperado: 5%) |

*Quadro V: síntese dos resultados no simulador com ruído (FakeTorino).*

**Calibração do critério.** Nas 812 combinações em que a inserção não muda em nada a saída
ideal, o critério acusou diferença em 6,3% dos casos com 1.000 *shots* e em 4,8% com 4.000,
próximo dos 5% esperados para o percentil 95. O excesso com 1.000 *shots* provavelmente vem do
*bootstrap*: com menos medições, saídas raras do golden não aparecem na amostra e o piso fica
levemente subestimado. São falsos alarmes de amostragem, que também explicam os pequenos ganhos
aparentes com ruído (por exemplo, X em oráculos, de 93% para 96%). Ao combinar quatro condições,
a chance de falso alarme para uma variante silenciosa chega a cerca de 1 − 0,95⁴ ≈ 19%, o que
precisa ser considerado ao ler os números agregados.

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
condições, sobretudo com 1.000 *shots*, o que aponta para um k95 muito maior com ruído nesse caso.

*Legenda da Fig. X (`fig_ruido_revela_1000.png`): fração de variantes infectadas reveladas em
pelo menos uma das quatro condições (entrada |0···0⟩ ou |+⟩ⁿ, base Z ou X), no simulador ideal e
com o modelo de ruído do FakeTorino (1.000 shots). n = número de variantes por porta. A versão
com 4.000 shots está em `fig_ruido_revela_4000.png`.*

*Legenda da Fig. Y (`fig_ruido_piso_1000.png`): TVD média entre a saída do golden com ruído e a
ideal (azul) e piso de ruído entre dois lotes do golden (laranja), por circuito, em função do
número de portas CZ depois da transpilação (1.000 shots).*

---

## Quadro resumo das hipóteses (ideal + ruído)

Para a discussão. Os números do ideal vêm do `results/ideal.csv` e dos `results/resumo_*.csv` do
Gabriel (1.000 shots); os do ruído, deste experimento.

| Hipótese | Situação | Evidência principal |
|---|---|---|
| H1: o impacto de trojans de fase e controlados depende da entrada e da família | Confirmada para as portas de fase; a parte dos trojans controlados não foi testada (CZ ficou fora do escopo) | Z nos reversíveis: 0% com \|0···0⟩ na base Z e 100% com \|+⟩ⁿ na base X; nos oráculos, 48% com \|0···0⟩ na base Z |
| H2: em famílias com interferência, \|+⟩ⁿ revela mais que \|0···0⟩ | Não confirmada (efeito contrário) | Z em oráculos, base Z: 48% com \|0···0⟩ e 4% com \|+⟩ⁿ; T em emaranhamento, base X: 81% e 56%. Esses circuitos começam com H, que leva \|+⟩ⁿ a \|0···0⟩; o que importa é haver superposição no ponto da inserção e a base de medição certa |
| H3: nos reversíveis, a fase só aparece com entrada em superposição medida em X | Confirmada | Z, T e RZ: 0% com qualquer entrada da base computacional, em qualquer base; 100% com \|+⟩ⁿ medido em X. Com ruído, o padrão se mantém (fora os falsos alarmes) |
| H4: com a entrada variando, posição e papel do qubit passam a pesar | Pendente (SHAP/regressão) | Na tabela descritiva, a fração revelada quase não varia com posição e papel (reversíveis 100%; oráculos 96–100%; emaranhamento 80–87%), mas essa medida satura perto de 100% |
| H5: poucos testes bastam; entradas raras e ruído aumentam o número | Parcialmente confirmada | k95 mediano de 1 na maioria; RZ(π/16) nos reversíveis tem mediana 5 e máximo 23. Com ruído, RZ(π/16) nos reversíveis cai de 100% para 17% (1.000 shots) ou 28% (4.000); o k95 com ruído não foi medido |

*Quadro resumo: hipóteses e evidências.*

---

## Notas para o grupo (não colar)

- **1.000 shots são 1.000 mesmo.** Os scripts passam `SHOTS = 1000` explicitamente. O padrão
  do Qiskit (`AerSimulator.run` e Samplers locais) é 1.024, e o da IBM Runtime (SamplerV2) é
  4.096. Roy et al. e John et al. usaram 1.000, e o trabalho-base usou 512. A diferença entre
  1.000 e 1.024 muda o piso em cerca de 1%.

- **Shots: decidir o principal.** Este rascunho usa 1.000 como principal, para bater com a seção
  6.4 da aba G3 e com o `ideal.csv`, e 4.000 como sensibilidade. Se o grupo preferir 4.000 como
  principal, basta trocar os números do texto pela coluna de 4.000 das tabelas (o ideal também
  teria de rodar com 4.000, para ficar coerente).
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
