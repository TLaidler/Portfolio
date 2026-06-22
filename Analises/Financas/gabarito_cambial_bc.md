# Gabarito — Exercícios sobre as operações cambiais do BC

> Confira **só depois** de tentar. Errar primeiro e entender depois fixa muito mais — é assim que Feynman aprendia.

---

## Exercício 1 — Traduzindo "contratos" para "dólares"

**Dado:** 1 contrato = US$ 50.000.

**a)** Multiplicação direta `contratos × 50.000`:

| Contratos | Valor em US$ |
|---|---|
| 20.000 | **US$ 1.000.000.000** (1 bi) |
| 50.000 | **US$ 2.500.000.000** (2,5 bi) |
| 550.000 | **US$ 27.500.000.000** (27,5 bi) |

**b)** Perna do swap: `20.000 × 50.000 = US$ 1.000.000.000`.

```
diferença = 1.000.000.000 − 1.000.000.000 = 0
```

**c)** **Neutra.** As duas pernas têm exatamente o mesmo tamanho (US$ 1 bi cada). O BC vende dólar à vista e, ao mesmo tempo, "recompra" o mesmo tanto via swap reverso. A exposição líquida em direção de dólar é zero → o objetivo é ajustar o **cupom cambial / liquidez de curtíssimo prazo**, não empurrar o preço do dólar.

> **Fórmula Excel sugerida:** com `$B$1 = 50000`, use `=20000*$B$1`, etc. Para a diferença: `=1000000000 - (20000*$B$1)`.

---

## Exercício 2 — O cupom cambial escondido no casado

**Dados:** `i = 0,025` ; `S = 5,40` ; `F = 5,4675`.

**a)** Casado:

```
F − S = 5,4675 − 5,40 = 0,0675
```

**b)** Cupom cambial:

```
c = (1 + 0,025) × (5,40 / 5,4675) − 1
  = 1,025 × 0,987654 − 1
  = 1,012346 − 1
  = 0,012346  =  1,2346%
```

> **Fórmula Excel:** `=(1+0,025)*(5,40/5,4675)-1`, formate a célula como porcentagem com 4 casas.

**c)** Sensibilidade (mesmos `S = 5,40` e `i = 0,025`):

| Cenário | F | Casado (F − S) | Cupom c |
|---|---|---|---|
| 1 | 5,4675 | 0,0675 | **1,2346%** |
| 2 | 5,4900 | 0,0900 | **0,8197%** |
| 3 | 5,5200 | 0,1200 | **0,2717%** |

**Conclusão:** quando o dólar futuro **sobe** (casado aumenta), o cupom cambial **desce**.

*Intuição:* na fórmula `c = (1 + i) × S/F − 1`, o **F está no denominador**. Aumentar F encolhe a fração, então c cai. Em termos econômicos: se o mercado já "embute" um dólar bem mais caro no futuro, sobra menos juro em dólar para compensar — o prêmio de carregar dólar diminui.

---

## Exercício 3 — O swap como dólar sintético financiado

**Dados:** `Notional = R$ 250.000` ; `S_ini = 5,00` ; `DI = 0,025`.

**a)** Resultado do swap = `250.000 × ((S_fim / 5,00) − 1 − 0,025)`:

| Cenário | S_fim | Variação do dólar | Variação − DI | **Resultado swap** |
|---|---|---|---|---|
| A (sobe 5%) | 5,25 | +5,0% | +2,5% | **+R$ 6.250** |
| B (cai 5%) | 4,75 | −5,0% | −7,5% | **−R$ 18.750** |

> **Fórmula Excel (cenário A):** `=250000*((5,25/5,00)-1-0,025)` → `6250`.

**b)** Resultado **físico** = `50.000 × (S_fim − 5,00)`:

| Cenário | S_fim | **Resultado físico** |
|---|---|---|
| A | 5,25 | `50.000 × 0,25` = **+R$ 12.500** |
| B | 4,75 | `50.000 × (−0,25)` = **−R$ 12.500** |

**c)** Diferença (físico − swap):

| Cenário | Físico | Swap | **Físico − Swap** |
|---|---|---|---|
| A | +12.500 | +6.250 | **+6.250** |
| B | −12.500 | −18.750 | **+6.250** |

A diferença é sempre **R$ 6.250** — e isso é exatamente o **custo do DI** sobre o notional:

```
250.000 × 0,025 = R$ 6.250
```

**O que isso significa:** o swap te entrega a **mesma variação do dólar** que comprar dólar de verdade, **menos o custo de financiamento (DI)**. É um dólar comprado "a prazo, financiado a juros".

> **A grande sacada:** quem compra dólar físico precisa desembolsar R$ 250.000 hoje. Quem usa o swap **não desembolsa nada** à vista — por isso "paga" o DI como custo de carregar a posição. E o BC adora isso porque consegue dar proteção cambial ao mercado **sem tirar um dólar sequer das reservas**. Volta tudo à frase da Seção 0: *mexer na pressão sem tirar moléculas da caixa.* 🎯

---

## Exercício 4 — Separando as quatro taxas

**Dados:** `i_BR = 0,1425` ; `i_US = 0,0365` ; `S = 5,00` ; `F = 5,50`.

**a)** Cupom cambial:

```
c = (1 + 0,1425) × (5,00 / 5,50) − 1
  = 1,1425 × 0,909091 − 1
  = 1,038636 − 1
  = 0,038636  =  3,8636%
```

**b)** Diferencial e forward premium:

```
diferencial bruto = i_BR − i_US = 14,25% − 3,65% = 10,60%
forward premium   = F/S − 1     = 5,50/5,00 − 1   = 10,00%
```

**c)** Classificação:

| Taxa | Valor | Tipo |
|---|---|---|
| Juro em real (i_BR) | 14,25% | NÍVEL (alto) |
| **Cupom cambial (c)** | **3,86%** | **NÍVEL (~4%) ← o único "cupom cambial" de verdade** |
| Juro do dólar lá fora (i_US) | 3,65% | NÍVEL (~4%) |
| Diferencial / carry | ~10% | DIFERENÇA |

O **cupom cambial** (3,86%) é o único que merece o nome — e repare que ele mora coladinho no juro externo (3,65%), com um prêmio de ~0,21% em cima.

**d)** Verificação da identidade:

```
(1 + c) × (F/S) = 1,038636 × (5,50/5,00) = 1,038636 × 1,10 = 1,1425 = 1 + i_BR  ✔
```

Fecha. O cupom e o forward premium são as duas peças que, multiplicadas, reconstroem o juro em real.

---

## Exercício 5 — O ganho (e o risco) do carry-trade

**Dados:** deve `US$ 103,65` ; tem `R$ 571,25` no fim.

**a)** Lucro = `571,25 / S_fim − 103,65`:

| Cenário | S_fim | 571,25 / S_fim | **Lucro (US$)** |
|---|---|---|---|
| A (real estável) | 5,00 | 114,25 | **+10,60** |
| B (cai 10% = forward) | 5,50 | 103,86 | **+0,21** |
| C (cai 20%, crise) | 6,00 | 95,21 | **−8,44** |

> **Fórmula Excel (cenário A):** `=571,25/5,00-103,65` → `10,60`.

**b)** Breakeven (lucro = 0):

```
571,25 / S_fim = 103,65   ->   S_fim = 571,25 / 103,65 = 5,5113
```

**c)** O breakeven (`5,5113`) está **quase colado** no forward (`5,50`). Por quê? Porque o forward é, por construção, o câmbio que faz a operação **travada** dar lucro zero — e a operação não-travada vira a mesma coisa quando o câmbio realizado cai exatamente no forward. A diferencinha (`5,5113` vs `5,50`) é justamente o **prêmio do cupom** (aqueles ~0,2% a mais do dólar onshore) que sobra a seu favor.

**Risco que você corre:** o câmbio futuro `S_fim`. Se o real se desvalorizar **mais** que ~10% (passar de 5,51), você perde — e numa crise cambial ele pode disparar bem além disso. O carry paga ~10,6% nos anos calmos e devolve tudo de uma vez no ano ruim: **prêmio de risco, não arbitragem.** 🎯
