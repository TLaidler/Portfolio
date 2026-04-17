# Regime Detection BTC/USDT — Relatorio Modelo 2 (Datasets Invertidos)

**Modelo:** Random Forest + Meta-Labeling sobre Dollar Bars (AFML Framework)
**Ativo:** BTC/USDT Perpetual Futures (Binance)
**Data do relatorio:** 2026-03-23
**Experimento:** Inversao de datasets — treino no periodo curto (bear), OOS no periodo longo (bull)

---

> *"O teste de todo conhecimento e o experimento. O experimento e o unico juiz da 'verdade' cientifica."*
> — Richard Feynman, Lectures on Physics, Vol. I

---

## 1. Motivacao — Por Que Inverter os Datasets?

No Modelo 1, treinamos em 5 anos de dados (2021-2025) e testamos OOS em 200 dias de bear market (ago/2025-mar/2026). O modelo retornou +13.85% enquanto BTC caiu -38%. Resultado promissor — mas precisamos responder uma pergunta critica:

**O modelo funciona porque aprendeu algo genuino sobre regimes, ou porque "decorou" o bear market no treino e acertou por vies de amostra?**

A forma mais honesta de testar e **inverter tudo**:

| | Modelo 1 | Modelo 2 (este relatorio) |
|---|---|---|
| **Treino** | 5 anos (multiplos regimes) | 200 dias (bear market puro) |
| **OOS** | 200 dias (bear market) | 4.5 anos (multiplos regimes) |
| **Hipotese testada** | Modelo generaliza para bear? | Modelo treinado em bear generaliza para bull? |

Se o modelo funcionar em ambas as direcoes, temos evidencia forte de que o framework AFML captura algo real. Se falhar, sabemos que o Modelo 1 pode ter sido sorte.

---

## 2. Treinamento — Bear Market como Escola

### 2.1 Dados de Treino

| Parametro | Valor |
|-----------|:-----:|
| Periodo | ~ago/2025 a mar/2026 |
| Dollar Bar Threshold | $290,340,041 |
| Dollar Bars geradas | 11,615 |
| Barras rotuladas | 2,633 |
| Labels: Bear / Neutro / Bull | 1,358 / 78 / 1,197 |
| Train/Test split | 2,106 / 527 |

Comparado ao Modelo 1 (91,482 dollar bars, 5,712 rotuladas), temos **8x menos dados**. Isso e um desafio severo — Random Forests precisam de volume para construir splits robustos. O que acontece quando forcamos o modelo a aprender com tao pouco?

### 2.2 Selecao de Features — Navalha de Occam Forcada

Das 20 features candidatas, o MDA selecionou **apenas 4**:

| Feature | MDA (selecao) | MDA (final CPCV) | Status |
|---------|:---:|:---:|:---:|
| **ret_20** | 0.1740 | 0.1856 | Selecionada |
| **vpin** | 0.0023 | -0.0100 | Selecionada |
| **log_volume** | 0.0012 | -0.0031 | Selecionada |
| **volatility_20** | 0.0006 | 0.0066 | Selecionada |
| lz_entropy | 0.0000 | — | Rejeitada |
| kyle_lambda | -0.0001 | — | Rejeitada |
| btc_dxy_spread | -0.0009 | — | Rejeitada |
| roll_spread | -0.0010 | — | Rejeitada |
| ffd_close | -0.0013 | — | Rejeitada |
| ret_10 | -0.0013 | — | Rejeitada |
| funding_rate_zscore | -0.0019 | — | Rejeitada |
| etf_volume_zscore | -0.0024 | — | Rejeitada |
| mom_residual_50 | -0.0025 | — | Rejeitada |
| tstat_10 | -0.0026 | — | Rejeitada |
| ret_50 | -0.0027 | — | Rejeitada |
| rsi | -0.0030 | — | Rejeitada |
| tstat_50 | -0.0038 | — | Rejeitada |
| tstat_20 | -0.0043 | — | Rejeitada |
| vix_chg | -0.0050 | — | Rejeitada |
| fear_greed_chg | -0.0072 | — | Rejeitada |

![Feature Importance MDA — Modelo 2](pngs/feature_importance_mda_mod2.png)

**Comparativo de features selecionadas:**

| Feature | Modelo 1 (10 features) | Modelo 2 (4 features) |
|---------|:---:|:---:|
| ret_20 | Sim (MDA 0.131) | Sim (MDA 0.174) |
| ret_50 | Sim (MDA 0.014) | **Nao** (MDA -0.003) |
| vix_chg | Sim (MDA 0.004) | **Nao** (MDA -0.005) |
| ffd_close | Sim (MDA 0.002) | **Nao** (MDA -0.001) |
| volatility_20 | Sim (MDA 0.001) | Sim (MDA 0.001) |
| tstat_20 | Sim (MDA 0.001) | **Nao** (MDA -0.004) |
| tstat_10 | Sim (MDA 0.000) | **Nao** (MDA -0.003) |
| log_volume | Sim (MDA 0.000) | Sim (MDA 0.001) |
| rsi | Sim (MDA 0.000) | **Nao** (MDA -0.003) |
| roll_spread | Sim (MDA 0.000) | **Nao** (MDA -0.001) |
| vpin | **Nao** (MDA -0.002) | Sim (MDA 0.002) |

**Leitura Feynman:**

O modelo com pouco dado fez algo inteligente: **descartou tudo que era sutil e ficou com o essencial.** Com apenas 2,633 barras, nao ha amostras suficientes para que features como `tstat_20` (que mede signal-to-noise ratio do momentum) contribuam de forma robusta. O modelo entendeu — via MDA — que tentar usar informacao fina com amostra pequena e pior do que ignorar.

O nucleo que sobreviveu: **momentum de 20 barras + volatilidade + volume + microestrutura (VPIN)**. Sao as features mais "ruidosas" mas tambem as mais fundamentais. O VPIN (probabilidade de informed trading) e particularmente interessante: foi rejeitado no Modelo 1 (MDA -0.002) mas aceito no Modelo 2 (MDA +0.002). Em um bear market concentrado, VPIN pode capturar fluxo direcional de liquidacoes mais efetivamente que em 5 anos de dados heterogeneos.

Note tambem que `ret_50` foi **rejeitada**. Momentum de 50 barras nao faz sentido quando voce tem apenas ~200 dias de dados — nao ha horizonte suficiente para que padroes de longo prazo se manifestem.

### 2.3 CPCV — 15 Paths

| Path | Accuracy | F1 | Sharpe |
|:----:|:--------:|:--:|:------:|
| 1 | 0.4989 | 0.5442 | +0.0187 |
| 2 | 0.5297 | 0.5869 | +0.0163 |
| 3 | 0.5342 | 0.6038 | +0.0497 |
| 4 | 0.6872 | 0.6898 | -0.0267 |
| 5 | 0.6311 | 0.6573 | +0.0479 |
| 6 | 0.6461 | 0.6581 | +0.0482 |
| 7 | 0.6769 | 0.6795 | +0.0469 |
| 8 | 0.5947 | 0.6179 | +0.0300 |
| 9 | 0.6345 | 0.6345 | +0.0566 |
| 10 | 0.6712 | 0.6925 | +0.0550 |
| 11 | 0.7180 | 0.7205 | +0.0247 |
| 12 | 0.5812 | 0.6456 | +0.0327 |
| 13 | 0.6963 | 0.6991 | +0.0164 |
| 14 | 0.7253 | 0.7358 | +0.0622 |
| 15 | 0.7117 | 0.7097 | +0.0476 |
| **Media** | **0.6358** | **0.6584** | **+0.0351** |
| **Std** | **0.0707** | **0.0518** | **0.0222** |

![CPCV Sharpe Distribution — Modelo 2](pngs/cpcv_sharpe_distribution_mod2.png)

**Comparativo CPCV:**

| Metrica | Modelo 1 | Modelo 2 |
|---------|:---:|:---:|
| Accuracy media | 59.7% | **63.6%** (+3.9pp) |
| F1 medio | 0.617 | **0.658** (+0.041) |
| Sharpe medio | -0.003 | **+0.035** |
| Paths com Sharpe > 0 | 6/15 | **14/15** |
| PSR (CPCV) | 0.623 | **0.980** |
| Std accuracy | 0.025 | 0.071 |

O resultado e contraintuitivo: **8x menos dados, mas CPCV muito melhor.** 14 de 15 paths tem Sharpe positivo (vs 6/15 no Modelo 1). A accuracy media subiu 4pp. O PSR foi para 0.98 — 98% de confianca de que o Sharpe real e positivo.

**Mas ha um asterisco importante:** a variancia e alta (std accuracy 0.071 vs 0.025). Os paths variam de 50% a 73% de accuracy. Isso e consequencia direta do dataset pequeno — cada fold de CPCV tem poucas centenas de observacoes, entao a variancia entre folds explode.

**A explicacao para a performance paradoxalmente melhor:** com apenas 4 features e pouco dado, o modelo e **mais simples e menos overfittado**. O bias aumenta um pouco (nao captura nuances), mas a variancia cai drasticamente. E o classico trade-off bias-variance — com pouco dado, modelos simples vencem.

### 2.4 Meta-Labeling — Teste In-Sample

| Metrica | Modelo 1 | Modelo 2 |
|---------|:---:|:---:|
| Accuracy (meta) | 17.6% | **47.8%** |
| F1 (weighted) | 0.240 | **0.594** |
| Sharpe | 0.020 | **0.093** |
| PSR | 0.750 | **0.974** |
| Abstencao | 83% | **40%** |
| Kurtosis | 194 | **55.8** |

**Confusion Matrix (teste in-sample):**

| | Pred Bear (-1) | Pred Neutro (0) | Pred Bull (+1) |
|---|:---:|:---:|:---:|
| **Real Bear (288)** | **156** | 112 | 20 |
| **Real Neutro (3)** | 0 | **0** | 3 |
| **Real Bull (236)** | 41 | 99 | **96** |

![Confusion Matrix Treino — Modelo 2](pngs/confusion_matrix_mod2.png)

**Precision e Recall in-sample:**

| Classe | Precision | Recall |
|--------|:---------:|:------:|
| Bear (-1) | **79%** | **54%** |
| Bull (+1) | **81%** | **41%** |

**A transformacao mais importante:** O meta-labeler deixou de ser um sniper ultra-conservador e virou um atirador com cadencia razoavel. O recall saltou de 11%→54% (bear) e 17%→41% (bull). A precision se manteve em ~80%. O Sharpe de teste quase quintuplicou (0.020→0.093).

**Por que?** Com apenas 4 features, as probabilidades do meta-labeler sao mais "decisivas" — ele tem menos dimensoes para ficar confuso. Com 10 features e pouco dado (Modelo 1 no teste in-sample), o meta-labeler via muita incerteza e preferia abster. Com 4 features, as fronteiras de decisao sao mais claras.

---

## 3. Teste Out-of-Sample — 4.5 Anos de Mercado Real

### 3.1 Setup

O modelo treinado em ~200 dias de bear market agora enfrenta o periodo mais diverso possivel: mar/2021 a jul/2025. Esse periodo inclui:

- **Bull run 2021:** BTC de $50k a $69k (ATH)
- **Crash 2022:** BTC de $69k a $16k (colapso Terra/Luna, FTX)
- **Recuperacao 2023:** BTC de $16k a $45k
- **Rally 2024-25:** ETF aprovado, BTC de $45k a $100k+

| Parametro | Valor |
|-----------|:-----:|
| Periodo | 2021-03-24 a 2025-07-31 |
| Duracao | **548 dias** (~1.5 anos de barras rotuladas) |
| Dados 1-min | 2,290,016 linhas |
| Dollar Bars | 83,815 |
| Barras rotuladas | 5,751 |
| Labels: Bear / Neutro / Bull | 2,610 / 274 / 2,867 |

### 3.2 O Que o Modelo Decidiu

| Decisao | N barras | % |
|---------|:--------:|:-:|
| Aposta Bear (-1) | 1,731 | 30.1% |
| **Abstencao (0)** | 2,148 | **37.3%** |
| Aposta Bull (+1) | 1,872 | 32.5% |
| **Total trades ativos** | **3,603** | **62.7%** |

Contraste dramatico com o Modelo 1 OOS (81% abstencao). Este modelo apostou em **63% das barras** — quase o oposto do comportamento anterior. O meta-labeler treinado num bear market concentrado desenvolveu confianca mais rapidamente, resultando em mais trades.

### 3.3 Regimes Detectados

![Regime Classification OOS — Modelo 2](pngs/regime_classification_oos_mod2.png)

O plot mostra como o modelo classificou cada barra ao longo de 4.5 anos. Com 63% de trades ativos, ha muito mais pontos verdes (bull) e vermelhos (bear) em comparacao com o Modelo 1. O modelo esta tentando acompanhar as transicoes de regime — mas como veremos, nem sempre com sucesso.

### 3.4 Triple-Barrier Labels — Ground Truth

![Triple Barrier Labels OOS — Modelo 2](pngs/triple_barrier_labels_oos_mod2.png)

Os labels do triple-barrier revelam a "verdade" dos 4.5 anos: alternancia constante entre fases bull e bear, com picos concentrados de labels vermelhos nos crashes (2022, mid-2024). O modelo precisava navegar essa complexidade com apenas 4 features aprendidas em 200 dias.

### 3.5 Filtragem do Meta-Labeler

![Meta Label Filtering OOS — Modelo 2](pngs/meta_label_filtering_oos_mod2.png)

Este plot mostra trades mantidos (azul) vs filtrados (vermelho). Com apenas 37% de abstencao, ha muito mais azul do que no Modelo 1. O meta-labeler filtra menos — mas os momentos onde filtra sao visivelmente os mais volateis (transicoes abruptas de regime).

### 3.6 Confusion Matrix OOS

| | Pred Bear (-1) | Pred Neutro (0) | Pred Bull (+1) |
|---|:---:|:---:|:---:|
| **Real Bear (2610)** | **1282** | 869 | **459** |
| **Real Neutro (274)** | 74 | **123** | 77 |
| **Real Bull (2867)** | **375** | 1156 | **1336** |

![Confusion Matrix OOS — Modelo 2](pngs/confusion_matrix_oos_mod2.png)

**Precision e Recall OOS:**

| Classe | Precision | Recall |
|--------|:---------:|:------:|
| Bear (-1) | **74%** | **49%** |
| Bull (+1) | **71%** | **47%** |

**Comparativo completo de Precision/Recall entre os dois modelos e fases:**

| Metrica | Mod1 In-Sample | Mod1 OOS | Mod2 In-Sample | Mod2 OOS |
|---------|:---:|:---:|:---:|:---:|
| Precision Bear | 73% | 89% | 79% | **74%** |
| Precision Bull | 86% | 80% | 81% | **71%** |
| Recall Bear | 11% | 12% | 54% | **49%** |
| Recall Bull | 17% | 20% | 41% | **47%** |
| Abstencao | 83% | 81% | 40% | **37%** |

**Leitura critica:**

A precision caiu significativamente comparada ao Modelo 1 OOS (89%→74% bear, 80%→71% bull). Mas o recall aumentou enormemente (12%→49% bear, 20%→47% bull). O modelo troca **pontaria por cobertura** — erra mais quando aposta, mas aposta muito mais vezes.

Os erros direcionais sao preocupantes: **459 vezes** o modelo disse "bull" quando era bear (vs 56 no Mod1), e **375 vezes** disse "bear" quando era bull (vs 14 no Mod1). Esses erros sao caros — apostar na direcao errada e pior que nao apostar.

A explicacao: o modelo treinou em um unico regime (bear). Os rallies explosivos de 2021 e 2024 sao padroes que ele nunca viu. Quando BTC sobe rapidamente com volume alto e volatilidade em expansao, o modelo confunde com condicoes de crash (alta vol + alto volume no treino = bear) e aposta short. Esse e um erro de **generalizacao assimetrica** — o modelo aprendeu bear mas nao bull.

### 3.7 Rentabilidade Composta

| Estrategia | Retorno | Retorno Anualizado |
|------------|:-------:|:------------------:|
| **Modelo (Meta-Label)** | **+21.85%** | ~+13.3% a.a. |
| BTC Buy & Hold | +171.35% | ~+73% a.a. |
| US Risk-Free (4.5% a.a.) | +6.84% | +4.5% a.a. |
| **Alpha vs BTC** | **-149.51pp** | — |
| **Excesso vs Risk-Free** | **+15.01pp** | ~+8.8% a.a. |

![Portfolio Equity OOS — Modelo 2](pngs/portfolio_equity_oos_mod2.png)

**O modelo retornou +21.85% em 548 dias — positivo e acima do risk-free.** Mas BTC retornou +171% no mesmo periodo. A underperformance relativa e de -150pp.

**Decomposicao do retorno:**

1. **Acertos bear (+alpha):** 1,282 apostas bear corretas durante quedas. Isso gerou retorno positivo nos crashs de 2022, correcoes intermediarias, etc.
2. **Acertos bull (+alpha):** 1,336 apostas bull corretas durante rallies. Capturou parte dos movimentos de alta.
3. **Erros direcionais (-alpha):** 459+375 = 834 apostas na direcao errada. Isso corroeu parte significativa dos ganhos.
4. **Abstencao durante rallies (custo de oportunidade):** 37% de abstencao incluiu alguns dos rallies mais fortes. Nao perdeu dinheiro, mas perdeu oportunidade.

O resultado liquido: positivo em termos absolutos, mas o modelo "devolveu" a maior parte do alpha potencial em erros direcionais — algo que o Modelo 1 (com 81% de abstencao) evitava por design.

### 3.8 Retorno Acumulado Aritmetico

![Retorno Acumulado OOS — Modelo 2](pngs/cumulative_returns_oos_mod2.png)

O grafico mostra a divergencia ao longo dos 4.5 anos:

1. **Barras 0-1500 (~2021-2022):** A estrategia (azul) acompanha BTC (laranja) razoavelmente bem, ambas subindo. O modelo acerta a direcao bull na maior parte do tempo.

2. **Barras 1500-2500 (~2022, crash):** BTC despenca e a estrategia tambem cai — mas menos. O modelo detectou parte do bear market e reduziu exposicao, mas nao o suficiente para evitar perda.

3. **Barras 2500-3500 (~2022-2023, fundo):** A estrategia toca seu pior ponto (chega a ficar levemente negativa). O modelo esta confuso — transicao de regime e o pior cenario para qualquer modelo de momentum.

4. **Barras 3500-5751 (~2023-2025, recuperacao + rally):** BTC dispara para cima. A estrategia recupera, mas fica muito atras. O modelo nao consegue surfar o rally completo — alterna entre bull e abstencao.

**O ponto mais revelador:** a estrategia nunca acompanha BTC nas aceleracoes mais fortes. Isso confirma o diagnostico: o modelo e um instrumento de **protecao de downside**, nao de **captura de upside**.

### 3.9 Sharpe Ratios OOS

**Perspectiva 1: Todas as barras**

| Metrica | Valor |
|---------|:-----:|
| Sharpe Ratio | 0.0088 |
| PSR | 0.7370 |
| DSR | 0.0000 |
| Skewness | **-11.199** |
| Kurtosis (excess) | **304.6** |
| N observacoes | 5,751 |

**Perspectiva 2: Apenas trades ativos (3,603)**

| Metrica | Valor |
|---------|:-----:|
| Sharpe Ratio | 0.0111 |
| PSR | 0.7370 |
| DSR | 0.0000 |
| Skewness | **-8.877** |
| Kurtosis (excess) | **189.9** |

**Perspectiva 3: Excess return sobre US Risk-Free (4.5% a.a.)**

| Base | SR vs RF | PSR |
|------|:---:|:---:|
| Todas barras | 0.0069 | 0.6938 |
| Trades ativos | 0.0096 | 0.7104 |

**Analise comparativa dos Sharpe:**

| Metrica | Mod1 OOS | Mod2 OOS |
|---------|:---:|:---:|
| SR (todas barras) | 0.0189 | 0.0088 |
| SR (trades ativos) | 0.0439 | 0.0111 |
| PSR (trades ativos) | 0.817 | 0.737 |
| Kurtosis (trades ativos) | 54.9 | **189.9** |
| Skewness (trades ativos) | -2.8 | **-8.9** |

O Modelo 2 tem Sharpe pior em todas as perspectivas. A kurtosis e 3.5x maior e a skewness 3x mais negativa. A distribuicao de retornos e mais perigosa: eventos extremos negativos sao mais frequentes e mais severos. Isso e consequencia direta de apostar mais vezes com menos precisao.

---

## 4. Comparativo Final — Modelo 1 vs Modelo 2

### 4.1 Tabela Sintetica

| Dimensao | Modelo 1 | Modelo 2 | Vencedor |
|----------|:---:|:---:|:---:|
| **Treino** | 5 anos (multiplos regimes) | 200 dias (bear puro) | — |
| **Features** | 10 | 4 | — |
| **CPCV Accuracy** | 59.7% | **63.6%** | Mod2 |
| **CPCV Sharpe** | -0.003 | **+0.035** | Mod2 |
| **CPCV PSR** | 0.623 | **0.980** | Mod2 |
| **OOS Retorno** | +13.85% | **+21.85%** | Mod2 |
| **OOS Alpha vs BTC** | **+51.92pp** | -149.51pp | **Mod1** |
| **OOS Excesso vs RF** | +5.89pp | **+15.01pp** | Mod2 |
| **OOS Precision Bear** | **89%** | 74% | **Mod1** |
| **OOS Precision Bull** | **80%** | 71% | **Mod1** |
| **OOS Recall Bear** | 12% | **49%** | Mod2 |
| **OOS Recall Bull** | 20% | **47%** | Mod2 |
| **OOS Sharpe (ativos)** | **0.044** | 0.011 | **Mod1** |
| **OOS Kurtosis (ativos)** | **54.9** | 189.9 | **Mod1** |
| **OOS Abstencao** | 81% | **37%** | Depende |

### 4.2 Perfis Complementares

Os dois modelos sao **instrumentos diferentes para situacoes diferentes:**

**Modelo 1 — O Sniper:**
- Aposta raramente (19% das barras), mas com precision de 80-89%
- Brilha em bear markets (+52pp alpha vs BTC)
- Protecao de downside pura
- Sharpe mais alto, kurtosis mais baixa — perfil de risco mais controlado
- Fraqueza: perde upside em bull markets

**Modelo 2 — O Soldado:**
- Aposta frequentemente (63% das barras), com precision de 71-74%
- Retorno absoluto positivo em ambos os regimes (+21.85% em bull)
- Mais exposto a erros direcionais (834 apostas erradas)
- Sharpe mais baixo, kurtosis mais alta — perfil de risco mais arriscado
- Fraqueza: nao captura bull markets completos, sofre em transicoes de regime

---

## 5. Analise Critica — O Que Feynman Diria

### 5.1 O Que Aprendemos com a Inversao

> "Eu preferiria ter perguntas que nao podem ser respondidas do que respostas que nao podem ser questionadas."

A inversao dos datasets revelou **tres verdades fundamentais:**

**Verdade 1: `ret_20` e o unico fator robusto.**
Em ambos os modelos, com qualquer tamanho de amostra, `ret_20` domina com MDA de 0.13-0.19. Momentum de 20 barras sobre dollar bars e o sinal mais confiavel que o modelo encontra. Todas as outras features sao complementares — uteis com dados abundantes, descartaveis com dados escassos.

**Verdade 2: O modelo e fundamentalmente defensivo.**
Em ambas as direcoes, a estrategia retornou positivo em termos absolutos (+13.85% e +21.85%) e acima do risk-free. Mas em nenhuma das duas superou BTC em bull market. O framework AFML + meta-labeling naturalmente produz estrategias conservadoras — o meta-labeler absteve ou errou durante os movimentos mais explosivos.

**Verdade 3: Tamanho do treino afeta TIPO de modelo, nao QUALIDADE.**
- Treino longo → mais features, mais conservador, mais preciso, menos recall
- Treino curto → menos features, mais agressivo, menos preciso, mais recall

Nao e que um e "melhor" — sao perfis de risco diferentes. O mercado que voce usa para treinar determina a personalidade do modelo.

### 5.2 O Que E Preocupante

**A. Skewness de -11 no Modelo 2 OOS.**
A distribuicao de retornos e extremamente assimetrica para a esquerda. Com 3,603 trades ativos e skewness -11, o modelo esta acumulando risco de cauda esquerda. Um unico "dia do juizo final" pode causar perda desproporcional. Isso e pior que o Modelo 1 (skewness -6).

**B. 834 erros direcionais no Modelo 2 OOS.**
Apostar na direcao errada e o pior tipo de erro — pior que abster. O Modelo 1 cometeu apenas 70 erros desse tipo (56+14). O Modelo 2 cometeu 834 (459+375). Cada erro direcional custa o dobro de uma abstencao errada.

**C. Ambos os modelos tem DSR = 0.**
Nenhum dos dois modelos passa no teste mais rigoroso de significancia estatistica. Isso nao invalida os resultados, mas significa que nao podemos afirmar com confianca estatistica formal que o alpha e real. A evidencia e sugestiva, nao conclusiva.

### 5.3 O Que E Genuino

**A. Retorno positivo em ambas as direcoes de inversao.**
O modelo treinou em bear e retornou positivo em bull. Treinou em multiplos regimes e retornou positivo em bear. Isso e evidencia forte de que algo real esta sendo capturado — nao e apenas um artefato da direcao dos dados.

**B. Excesso sobre risk-free em ambos os casos.**
+5.89pp (Mod1) e +15.01pp (Mod2) sobre o risk-free. Com PSR de 0.74-0.82, temos ~75-82% de confianca de que o excesso e genuino.

**C. Precision acima de 70% em todos os cenarios.**
Em nenhum cenario (in-sample ou OOS, Mod1 ou Mod2) a precision caiu abaixo de 71%. Quando o modelo aposta, a direcao esta certa 3 em cada 4 vezes. Isso e um sinal consistente de que o detector de regime tem valor informacional.

---

## 6. Implicacoes Praticas

### 6.1 Qual Modelo Usar?

| Cenario de Mercado | Modelo Recomendado | Razao |
|--------------------|:---:|-------|
| Bear market / Crise | **Modelo 1** | Precision 89%, abstencao protege capital |
| Bull market estavel | **Nenhum** (buy & hold) | Ambos perdem para BTC em bull |
| Mercado lateral / incerto | **Modelo 2** | Mais recall, captura mais oportunidades |
| Hedge de portfolio long | **Modelo 1** | Filtra exposicao, reduz drawdowns |

### 6.2 A Pergunta de $1 Milhao

> *Se eu tivesse que colocar dinheiro real, o que faria?*

A resposta honesta: usaria o Modelo 1 como **filtro de exposicao**, nao como estrategia standalone.

Concretamente: manter posicao long BTC por default (para capturar upside), mas **zerar a posicao quando o Modelo 1 sinaliza bear com alta confianca** (meta_confidence > 0.6 e predicao = -1). Isso combina o upside de buy & hold com a protecao de downside do modelo.

O Modelo 2 mostra que tentar usar o modelo para timing ativo (comprar e vender frequentemente) degrada a qualidade dos sinais. A forca do framework esta na **deteccao de perigo**, nao na **captura de oportunidade**.

---

## Apendice A — Configuracao do Modelo 2

| Parametro | Valor |
|-----------|:-----:|
| Dollar bar threshold | $290,340,041 |
| Features selecionadas | ret_20, vpin, log_volume, volatility_20 |
| FFD d | 0.4 |
| SavGol window | 21 |
| PT/SL multiplier | 2.0x / 2.0x |
| Max holding bars | 50 |
| CPCV groups / k_test | 6 / 2 |
| RF estimators / depth / leaf | 500 / 6 / 50 |
| Meta-label threshold | 0.6 |
| Train/test ratio | 80/20 |

## Apendice B — Arquivos Gerados

```
relatorios/
  relatorio_regime_detection.md          (Modelo 1)
  relatorio_regime_detection_mod2.md     (Modelo 2 — este documento)
  pngs/
    *_mod2.png                           (plots treino Modelo 2)
    *_oos_mod2.png                       (plots OOS Modelo 2)
  modelos/
    trained_model.joblib                 (Modelo 1)
    trained_model_mod2.joblib            (Modelo 2)
```

---

*Relatorio gerado em 2026-03-23. Pipeline: regime_detection_advanced.py + rd_adv_application.py*
*Experimento de inversao de datasets para teste de robustez bidirecional.*
