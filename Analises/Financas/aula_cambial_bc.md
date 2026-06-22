# Como o Banco Central age no câmbio — uma aula no estilo Feynman

> *"Você não entende nada até conseguir explicar para a sua avó."*
> Então vamos do zero, devagar, sem pular nenhum degrau.

---

## 0. A grande ideia (leia isto primeiro)

Imagine que o dólar é um **gás dentro de uma caixa**.

- A **quantidade de moléculas** (quantos dólares existem disponíveis no mercado) é uma coisa.
- A **pressão** (quão caro está o dólar, e quão caro está ter dólar *hoje* versus *amanhã*) é outra coisa.

O Banco Central (BC) quase nunca quer **tirar moléculas da caixa** — ou seja, gastar suas reservas de verdade. Isso é caro e arriscado. Ele prefere **mexer na pressão** usando instrumentos espertos que dão proteção ao mercado **sem entregar dólar de verdade**.

Essa é a frase para tatuar no braço:

> **O BC prefere mexer no preço e na "pressão" do dólar do que gastar suas reservas físicas.**

Tudo que vem a seguir são apenas *ferramentas diferentes* para fazer isso.

---

## 1. Três preços do dólar que você precisa separar na cabeça

### 1.1 Dólar à vista (*spot*, símbolo $S$)
É o dólar que você compra **hoje** e recebe **hoje** (ou em 2 dias). É o preço do "agora".

### 1.2 Dólar futuro (símbolo $F$)
É um contrato para comprar dólar **numa data lá na frente** (ex.: 1º de outubro), mas com o **preço combinado hoje**. Ninguém entrega dólar agora — só na data marcada.

### 1.3 O "casado"
É simplesmente a **diferença** entre os dois:

$$
\text{casado} = F - S
$$

Pergunta natural de físico: *por que o futuro seria diferente do à vista?* Porque guardar dinheiro custa (ou rende) juros. Esse é o próximo conceito.

---

## 2. O "cupom cambial": a taxa de juros do dólar dentro do Brasil

Pense em dois caminhos para sair de **1 real hoje** e chegar em **reais no futuro**:

**Caminho A — ficar em real:**
Você aplica 1 real à taxa de juros brasileira $i$ (a Selic/CDI). No fim você tem:
$$
1 + i
$$

**Caminho B — passar pelo dólar:**
1. Troca o real por dólar hoje: vira $\tfrac{1}{S}$ dólares.
2. Aplica esses dólares à taxa de juros **em dólar dentro do Brasil**, chamada **cupom cambial** $c$. Vira $\tfrac{1+c}{S}$ dólares.
3. No futuro, troca de volta para real ao preço futuro $F$. Vira $\tfrac{(1+c)\,F}{S}$ reais.

Se os dois caminhos não derem o **mesmo** resultado, existe **dinheiro de graça** (arbitragem) — e o mercado fecha esse buraco em segundos. Logo, no equilíbrio:

$$
\boxed{\,1 + i \;=\; (1+c)\cdot\dfrac{F}{S}\,}
$$

Isolando o cupom cambial:

$$
c \;=\; (1+i)\cdot\dfrac{S}{F} \;-\; 1
$$

**O que isso te diz, na prática:**
- O **casado** ($F-S$) e o **cupom cambial** ($c$) são dois lados da mesma moeda. Mexeu em um, mexeu no outro.
- Quando o BC opera **ao mesmo tempo** no à vista e no futuro, ele não está apostando se o dólar vai subir ou cair. Ele está **ajustando o cupom cambial** — o "juro do dólar" aqui dentro.

---

## 3. O swap cambial: o "dólar de mentira" (sintético)

Aqui está a ferramenta favorita do BC. Um **swap cambial** é um contrato com **duas pernas**:

| Perna | Quem segura essa perna ganha... |
|---|---|
| **Perna do dólar** | a variação do dólar + o cupom cambial |
| **Perna dos juros** | a taxa de juros DI (parente da Selic) |

No **swap tradicional**, o BC fica na ponta que **paga a variação do dólar** e recebe juros. O mercado fica do outro lado: **recebe a variação do dólar**.

Repare na mágica: **ninguém entrega um dólar sequer.** Tudo é acertado em **reais** no fim. Mas quem está do lado "dólar" sente *exatamente* o que sentiria se tivesse comprado dólar de verdade.

> É um **dólar sintético**. Dá a mesma proteção que comprar dólar, **sem o BC precisar tirar dólar das reservas.**

Dois sabores:

- **Swap tradicional** → o BC age como quem **vende dólar** (dá proteção contra a *alta* do dólar). Usado quando o dólar está subindo demais.
- **Swap reverso** → o BC age como quem **compra dólar**. Usado quando o dólar está fraco demais (real forte demais) ou para o BC recompor posição.

### Número de ouro para decorar
$$
\textbf{1 contrato de swap} \;\approx\; \textbf{US\$ 50.000}
$$
Esse é o "fator de conversão" que transforma *contratos* (linguagem da notícia) em *dólares* (linguagem que você entende).

---

## 4. "Rolar" um contrato — a parte que mais confunde

Os swaps têm **data de vencimento**. Quando chega o vencimento, o BC tem duas escolhas:

- **Rolar** = abrir contratos novos para substituir os que estão vencendo.
  → O **estoque** de proteção no mercado **fica igual**. É uma jogada **neutra**: "está tudo sob controle, mantenho o hedge".
- **Não rolar** = deixar vencer e não repor.
  → O estoque **diminui**. Isso é uma **decisão de política**: equivale a "retirar proteção" do mercado.

> A regra de ouro: **o que importa é o ESTOQUE, não o leilão de um dia.** Rolar mantém; não rolar é uma escolha com recado.

E cuidado com o vocabulário: além dos swaps, o BC também tem as **"linhas"** — que são empréstimos de dólar **de verdade** aos bancos (com compromisso de devolução). Quando o BC "não rola uma linha", ele está recolhendo um pouco de dólar físico que havia emprestado. Se ele faz isso sem estresse, é sinal de que **sobra dólar** no mercado.

---

## 5. Agora releia a notícia com olhos de especialista

> *"BC oferta casadão com até US\$ 1 bilhão em leilão à vista e, simultaneamente, swap cambial reverso de até 20.000 contratos."*

Faça a conta: $20.000 \times US\$50.000 = US\$\,1$ bilhão. **As duas pernas têm o mesmo tamanho!** Vende US$ 1 bi à vista, "recompra" US$ 1 bi no futuro via swap. Direção líquida no dólar ≈ **zero** → é uma operação para **ajustar o cupom/liquidez de curtíssimo prazo**, não para empurrar o dólar para cima ou para baixo.

> *"BC não deve rolar US\$ 2,05 bi de linha; estoque cai para US\$ 2 bi."*

Recolhe um pouco de dólar emprestado, sem drama → **liquidez confortável**.

> *"Voltou a 50.000 contratos para rolagem."*

$50.000 \times US\$50.000 = US\$\,2{,}5$ bi por leilão. Ritmo cheio → **intenção de manter o estoque de hedge**.

> *"Já rolou 550.000 contratos com vencimento em 1/jul."*

$550.000 \times US\$50.000 = US\$\,27{,}5$ bi. É o tamanho do lote sendo rolado → **manutenção, sem susto.**

**Conclusão geral:** é um BC em **modo manutenção**, não em modo crise. Nada de "queimar munição".

---

## 6. Os 3 conceitos para levar para casa

1. **Sintético × físico:** swap = dólar de mentira (não gasta reserva); leilão à vista e linhas = dólar de verdade.
2. **Nível × preço-no-tempo:** quando o BC casa as pernas (notionais iguais, US\$1bi = US\$1bi), o alvo é o **cupom cambial/casado**, não a direção do dólar.
3. **Rolar = neutro; não rolar = decisão:** olhe o **estoque**, não o leilão isolado.

---
---

# 🧮 Exercícios para resolver no Excel

> Monte cada exercício numa aba do Excel. Crie células separadas para os **dados** e para as **fórmulas**, do jeito que um físico monta uma planilha de laboratório: entrada, conta, resultado. Confira tudo depois no arquivo `gabarito_cambial_bc.md`.

---

## Exercício 1 — Traduzindo "contratos" para "dólares" (e a mágica do casadão)

**Contexto:** a notícia fala em *contratos*, mas você pensa em *dólares*. Vamos construir o tradutor.

**Dado:** 1 contrato = US$ 50.000.

**a)** Numa coluna, calcule o valor em dólares de:
- 20.000 contratos
- 50.000 contratos
- 550.000 contratos

**b)** O "casadão" da notícia tem duas pernas:
- Perna à vista: US$ 1.000.000.000 (1 bilhão)
- Perna do swap reverso: 20.000 contratos

Converta a perna do swap para dólares e calcule a **diferença** entre as duas pernas:
$$\text{diferença} = \text{perna à vista} - \text{perna do swap}$$

**c)** Com base no resultado de (b), responda numa célula de texto: **a operação é "comprada", "vendida" ou "neutra" em direção de dólar?** Por quê?

> 💡 *Dica de montagem:* coloque "tamanho do contrato" numa única célula (ex.: `B1 = 50000`) e refira-se a ela com `$B$1` nas fórmulas. Assim você muda um número só e a planilha inteira se atualiza.

---

## Exercício 2 — O cupom cambial escondido no "casado"

**Contexto:** vamos usar a fórmula de não-arbitragem da Seção 2 para descobrir o "juro do dólar" dentro do Brasil.

**Dados (período até o vencimento):**
- Taxa de juros em real no período: $i = 2{,}5\%$ (ou seja, 0,025)
- Dólar à vista: $S = 5{,}40$
- Dólar futuro: $F = 5{,}4675$

**a)** Calcule o **casado**: $\;F - S$.

**b)** Calcule o **cupom cambial** $c$ usando:
$$c = (1+i)\cdot\frac{S}{F} - 1$$
Mostre o resultado em **% com 4 casas decimais**.

**c)** **Análise de sensibilidade.** Refaça o item (b) para três valores de futuro, mantendo $S$ e $i$ fixos:

| Cenário | $F$ |
|---|---|
| 1 | 5,4675 |
| 2 | 5,4900 |
| 3 | 5,5200 |

Numa frase: **quando o dólar futuro sobe (casado aumenta), o cupom cambial sobe ou desce?**

> 💡 *Dica:* monte uma coluna de $F$ e arraste a fórmula do cupom para baixo. Olhar três pontos é como olhar a inclinação de uma reta — você "sente" a derivada.

---

## Exercício 3 — A "verdade" do swap: dólar sintético financiado a juros

**Contexto:** vamos provar, com números, que um swap cambial entrega a exposição ao dólar **menos** o custo de juros — ou seja, é um dólar comprado "a prazo, financiado".

**Dados de 1 contrato de swap (ponta comprada em dólar):**
- Tamanho: US$ 50.000
- Dólar no início: $S_{\text{ini}} = 5{,}00$  →  notional em reais $= 50.000 \times 5{,}00 = R\$\,250.000$
- Juros DI acumulados no período: $\text{DI} = 2{,}5\%$ (0,025)

A liquidação (em reais) para quem está comprado em dólar via swap é, de forma simplificada:
$$
\text{Resultado} = \text{Notional}_{R\$} \times \big(\text{variação do dólar} - \text{DI}\big)
$$
onde $\text{variação do dólar} = \dfrac{S_{\text{fim}}}{S_{\text{ini}}} - 1$.

**a)** Calcule o **Resultado** em dois cenários:
- Cenário A (dólar sobe 5%): $S_{\text{fim}} = 5{,}25$
- Cenário B (dólar cai 5%): $S_{\text{fim}} = 4{,}75$

**b)** Agora compare com **comprar dólar de verdade**: alguém que pegou R$ 250.000, comprou US$ 50.000 a 5,00 e vendeu no fim. Calcule o resultado físico:
$$
\text{Resultado físico} = 50.000 \times (S_{\text{fim}} - S_{\text{ini}})
$$
para os mesmos cenários A e B.

**c)** Calcule a **diferença** (físico − swap) em cada cenário. Você vai notar que ela é sempre a mesma. **O que essa diferença representa?** (Pista: é o preço de algo que aparece na fórmula do swap.)

> 💡 *Reflexão final:* o swap te dá a "emoção" de ter dólar sem precisar desembolsar os R$ 250.000 à vista — mas em troca você "paga" o DI. É exatamente por isso que o BC adora: ele oferece proteção cambial **sem tirar dólar das reservas**.
