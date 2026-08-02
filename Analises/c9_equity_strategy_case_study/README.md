# Estratégia sistemática em ações brasileiras — um case study de processo

> **TL;DR (English).** Research case study of a systematic equity strategy on Brazilian stocks (quality + value + momentum). What this document sells is the **process**, not the pick: ~43 pre-registered trials with a numeric acceptance bar declared before running; every failed attempt kept on the record with a post-mortem; data biases hunted down and **published against my own result** (the base strategy's return fell from 20.0% to 14.8% p.a. as corrections were applied); multiple-testing correction via Probabilistic and Deflated Sharpe Ratio — with the final strategy's DSR (87.5%) honestly reported **below** our own 95% bar. Verdict kept deliberately modest: *"smart beta harvesting known premia — strong evidence, not proof."* The rule is frozen for 12 months with a falsification gate. Exact parameters and the live portfolio are intentionally omitted (real capital runs on this).

---

## 1. A pergunta de pesquisa

O ponto de partida não foi "que estratégia rende mais?", e sim duas hipóteses econômicas testáveis sobre a B3:

- **"Boa-e-barata" é um estado efêmero.** Empresas com alta qualidade e valuation baixo permanecem nesse estado por cerca de **2 anos** em mediana — e a porta de saída usual é a valorização. Se isso é verdade, uma carteira anual consegue colher a transição.
- **Lucro excepcional derrete.** O lucro acima do normal decai com meia-vida de aproximadamente **3,2 anos**. Consequência metodológica: qualidade deve ser medida pela **mediana de 3 anos** dos fundamentos, nunca pelo pico do último balanço.

O momentum entrou na tese pela assimetria da distribuição de retornos forward: quedas fortes têm mediana e média próximas, mas altas fortes carregam uma cauda direita gorda (a média supera bastante a mediana). Carteiras "comem médias" — então momentum entra **positivo**, como componente de convicção, não como veto.

## 2. O protocolo veio antes dos resultados

Regras do laboratório, declaradas em docstrings datados **antes** de cada rodada:

| Item | Regra |
|---|---|
| Barra de aceitação | PSR ≥ 95%, retorno > IBOV e > CDI, ambas as metades da amostra positivas, diversificação mínima na carteira |
| Registro | Toda tentativa entra na contagem — inclusive as fracassadas, com autópsia escrita |
| Correção de múltiplos testes | Probabilistic Sharpe Ratio (ajustado por skew/curtose) e Deflated Sharpe Ratio (López de Prado, 2014) sobre a família inteira de trials |
| Benchmark honesto | Além de IBOV e CDI, um **nulo pareado**: 500 carteiras aleatórias com o mesmo número de ativos por ano, mesmo universo, mesmos custos e impostos, mesma regra de regime |
| Anti-drift | Regra vencedora **congelada por 12 meses** (gate de revisão: jul/2027), com aviso automático no código caso o ranking do ano dispute a regra impressa |

## 3. As rodadas — o cemitério faz parte do resultado

Aproximadamente **43 tentativas** na família, em rodadas datadas. Resumo:

| Família | O que testou | Veredito |
|---|---|---|
| V1–V3 | Filtros de elegibilidade qualidade+valor (base do universo) | V3 adotada como base: 14,8% a.a. após todas as correções de viés |
| L1–L8 | 8 ideias isoladas: momentum, corte de volatilidade, distress, meta-labeling (RF walk-forward com embargo), rebalanceamento semestral, regime de juros, concentração top-10, histerese | Maioria reprovada — o rebalanceamento semestral, p.ex., destruía 3,3 p.p./ano |
| C1–C6 | Combinações da rodada 2 | C6 venceu por margem mínima de PSR |
| C7a/C7b | Interseção concentração ∩ momentum | Reprovadas no gate de diversificação (chegou a carteira de 1 ativo num ano) |
| C8 | Meio-termo com piso de nomes | Reprovada: não dominava as estratégias-mãe |
| **C9** | Score composto qualidade+valor+momentum, guarda de risco e regime de juros | **Adotada** (07/2026) e congelada |
| Contrarian, short, cripto, EUA | Momentum invertido; "C9 ao contrário" vendida; carry cripto; espelho da C9 nos EUA (SEC EDGAR) | **Todas reprovadas ou não adotadas** — incluindo a versão americana, que perdeu do S&P 500 |

Duas notas que dizem mais que os números: uma empresa ficou fora da carteira por **um milésimo** no score de elegibilidade e foi mantida fora por princípio ("a regra é a regra"); e a versão americana da estratégia, mesmo com resultado re-testado acima do benchmark numa variante, **não foi adotada** por falta de dominância — o mesmo critério que reprovou candidatas internas.

## 4. Os vieses que encontramos — e quanto custaram (contra nós)

A parte de que mais me orgulho: cada viés descoberto **piorou o número publicado**, e ficou registrado.

| Correção | Efeito no retorno da estratégia-base |
|---|---|
| Número inicial (ingênuo) | 20,0% a.a. |
| Viés de sobrevivência: 210 empresas deslistadas reintegradas à seleção e aos retornos (as "mortas" ocupam 19% das vagas históricas) | −1,6 p.p./ano |
| Look-ahead nos preços: retro-ajuste de splits da fonte de dados vazava informação futura para o valuation → migração para preços as-traded da B3 (522 splits tratados manualmente) | −2,4 p.p./ano |
| Bug de escala em dados cadastrais (ações em milhares, 273 empresas afetadas) | correção estrutural |
| **Número final publicado** | **14,8% a.a.** |

Universo final: painel CVM/DFP 2010–2025, ~1.200 companhias incluindo deslistadas; preços B3 COTAHIST; taxa de juros BCB/SGS; fatores de risco NEFIN/USP.

## 5. O resultado — com as ressalvas na frente

Estratégia final (C9), líquida de custos e imposto, sobre 13 decisões anuais de compra (2012–2024, janelas de 12 meses):

| Métrica | C9 | Referências |
|---|---|---|
| Retorno anualizado | 21,5% | IBOV 10,4% · CDI 10,0% · mediana do nulo pareado 13,0% |
| Sharpe | 0,57 | — |
| Max drawdown | −40% | o preço do equity concentrado |
| Metades da amostra | +26,1% / +16,9% | ambas positivas (exigência da barra) |
| PSR | 97,3% | acima da barra de 95% |
| **Deflated Sharpe (família de ~43 trials)** | **87,5%** | **abaixo da nossa barra de 95%** |
| vs. nulo pareado | percentil 100 de 500 | nulo com mesmas regras, custos e regime |

**A leitura registrada em ata é deliberadamente modesta:** a regressão contra os 5 fatores de risco brasileiros (NEFIN, erros Newey-West) mostrou alpha estatisticamente **não significativo** — as cargas são de mercado, value, momentum e iliquidez. Ou seja: **"é beta inteligente, não alpha"** — colheita disciplinada de prêmios de risco conhecidos, com uma implementação que sobreviveu a testes que derrubaram 40+ irmãs. Vantagem forte; prova, só com a carteira viva.

## 6. Limitações conhecidas (autodeclaradas)

1. **Não existe out-of-sample verdadeiro ainda.** São 13 decisões anuais; a regra foi escolhida vendo a amostra inteira (as "duas metades positivas" são exigência de robustez, não OOS). O primeiro ano genuinamente fora da amostra fecha em meados de 2027 — até lá, a classificação honesta é "não provada".
2. **Liquidez e slippage.** Custos de 0,2% por ponta sem modelo de impacto de mercado, num universo que inclui microcaps — parte do retorno é prêmio de iliquidez (a carga no fator IML confirma), e a execução real numa carteira maior seria pior.
3. **Point-in-time por convenção, não por data efetiva.** A regra opera com folga de meses após o prazo legal de publicação dos balanços, mas a data de recebimento efetivo de cada demonstração (coletada) ainda não é usada como filtro individual — republicações tardias são um canal residual de look-ahead.
4. **Governança da contagem de trials.** A lista de tentativas para o Deflated Sharpe é mantida manualmente e mistura campanhas de universos diferentes — direção conservadora, mas estatisticamente imperfeita.

## 7. O que não está aqui — e por quê

Os parâmetros exatos dos filtros, a composição da carteira viva e o código executável ficam num repositório privado: a estratégia roda com capital real. Este documento existe para mostrar **como** o resultado foi construído e auditado — não para distribuir a receita. Os métodos citados (PSR/DSR, purged validation, nulos pareados, point-in-time) estão todos na literatura aberta (López de Prado, *Advances in Financial Machine Learning*; Bailey & López de Prado, 2014).

---

*Stack: Python (pandas/NumPy), dados abertos CVM (DFP), B3 COTAHIST, BCB/SGS, NEFIN-USP. Projeto irmão: [replicação da metodologia AFML em cripto](../regime_detection_study) — onde o pipeline rejeitou a própria estratégia out-of-sample e o resultado nulo foi documentado.*
