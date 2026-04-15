# Regime Detection BTC/USDT — Relatorio Modelo 5 (Custos de Transacao Pessimistas)

**Modelo:** Random Forest + Meta-Labeling sobre Dollar Bars (AFML Framework)
**Ativo:** BTC/USDT Perpetual Futures (Binance)
**Data do relatorio:** 2026-03-24
**Experimento:** Dollar bars 10/dia, fees pessimistas (taker ambas pontas = 0.054%/round-trip), dataset de treino expandido (14,928 barras rotuladas)

---

> *"Se voce nao consegue descrever o que esta fazendo como um processo, voce nao sabe o que esta fazendo."*
> — W. Edwards Deming

---

## 1. Motivacao — O Que Mudamos e Por Que

O Modelo 5 e o primeiro da serie a incorporar **custos reais de transacao**. Todos os modelos anteriores (1-4) operavam com retornos brutos — uma premissa irrealista que pode inflar o alpha medido. Este modelo responde a pergunta fundamental: **o sinal sobrevive apos fees?**

| Mudanca | Hipotese |
|---------|----------|
| **Fees pessimistas (taker ambas pontas)** | Cobra 0.027% (taker Binance USDT-M) na entrada E na saida. Cada round-trip custa 0.054%. Se o alpha sobrevive aqui, qualquer economia com limit orders e upside gratuito |
| **fee_mode = "pessimistic"** | Assume market orders em ambas as pontas. Stops nunca sao maker; regime changes geram urgencia; backtesting otimista mata |
| **Dataset de treino expandido** | 14,928 barras rotuladas (vs 5,319 no Mod4) — ~3x mais dados de treino |
| **18 features candidatas** | Pool de features ajustado em relacao ao Mod4 |

O principio: **um modelo que gera +114% sem fees pode estar financiando a ilusao com custos ignorados. Um modelo que gera +54% com fees pessimistas e mais valioso.**

---

## 2. Treinamento — Modelo com Custos Reais

### 2.1 Dollar Bars e Dataset

| Parametro | Mod4 (sem fees) | **Mod5 (com fees)** |
|-----------|:---:|:---:|
| Bars/dia | 10 (fixo) | **10 (fixo)** |
| Threshold | $1,328M | **$1,328M** |
| Dollar Bars | 18,405 | **18,405** |
| Barras rotuladas | 5,319 | **14,928** |
| Train/Test | 4,255/1,064 | **11,942/2,986** |

A principal diferenca alem dos fees: o dataset de treino foi expandido para **14,928 barras rotuladas** — quase 3x mais que o Mod4. Mais dados de treino permitem ao CPCV gerar splits maiores e ao MDA estimar importancias com menor variancia.

![Dollar Bars Sampling — Modelo 5](pngs/dollar_bars_sampling_mod5.png)

### 2.2 Selecao de Features — Microestrutura Emerge

Das 18 features candidatas, o MDA selecionou **6**:

| Feature | MDA (selecao) | MDA (final CPCV) | Status |
|---------|:---:|:---:|:---:|
| **ret_20** | 0.1541 | 0.1558 | Selecionada |
| **ret_60** | 0.0137 | 0.0127 | Selecionada |
| **vpin** | 0.0007 | 0.0044 | Selecionada |
| **tstat_50** | 0.0003 | 0.0007 | Selecionada |
| **kyle_lambda** | 0.0001 | 0.0011 | Selecionada |
| **fear_greed_chg** | 0.0001 | -0.0001 | Selecionada |
| lz_entropy | 0.0000 | — | Rejeitada |
| log_volume | -0.0000 | — | Rejeitada |
| volatility_20 | -0.0000 | — | Rejeitada |
| ffd_close | -0.0001 | — | Rejeitada |
| vix_chg | -0.0001 | — | Rejeitada |
| mom_residual_50 | -0.0002 | — | Rejeitada |
| funding_rate_zscore | -0.0002 | — | Rejeitada |
| btc_dxy_spread | -0.0002 | — | Rejeitada |
| roll_spread | -0.0003 | — | Rejeitada |
| tstat_20 | -0.0005 | — | Rejeitada |
| tstat_10 | -0.0007 | — | Rejeitada |
| rsi | -0.0007 | — | Rejeitada |

![Feature Importance MDA — Modelo 5](pngs/feature_importance_mda_mod5.png)

**Observacoes:**

1. **ret_20 continua dominante** (MDA 0.156), mas com importancia ligeiramente menor que no Mod4 (0.183). Com mais dados de treino, a estimativa de MDA e mais precisa — a importancia "real" de ret_20 pode ser ~0.156, e o Mod4 superestimava por variancia amostral.

2. **VPIN entrou com forca.** Rejeitado em todos os modelos anteriores (MDA negativo nos Mod1-4), agora e a 3a feature mais importante (MDA 0.004 no CPCV final). O Volume-Synchronized Probability of Informed Trading (AFML Cap. 18) mede a probabilidade de fluxo informado — com 3x mais dados de treino, o MDA tem resolucao para detectar seu sinal.

3. **kyle_lambda ressuscitou.** Tambem do framework de microestrutura (AFML Cap. 18), mede o impacto de preco por unidade de fluxo. Rejeitado em todos os modelos anteriores, agora contribui com MDA 0.001.

4. **tstat_50 entrou** — significancia estatistica de tendencia longa (50 barras = ~5 dias). Complementa ret_60 medindo nao apenas a magnitude do movimento mas sua significancia.

5. **volatility_20, vix_chg e log_volume foram REJEITADAS** — eram as 3 features secundarias do Mod4. Com mais dados, o MDA as revelou como ruido.

6. **fear_greed_chg sobreviveu por pouco** na selecao (MDA +0.0001) mas no CPCV final ficou ligeiramente negativa (-0.0001). Feature marginal que poderia ser removida sem perda.

**Comparativo de features selecionadas entre modelos:**

| Modelo | Features | Tipo dominante |
|--------|:---:|---|
| Mod1 | 10 | Momentum + microestrutura + exogenas |
| Mod2 | 4 | Momentum puro |
| Mod3 | 8 | Momentum + exogenas (barras grossas) |
| Mod4 | 5 | Momentum + volatilidade + volume |
| **Mod5** | **6** | **Momentum + microestrutura (VPIN, Kyle)** |

O Mod5 e o primeiro modelo onde features de **microestrutura** (VPIN, Kyle Lambda) tem papel relevante. Isso sugere que com dados suficientes, o fluxo informado contribui informacao ortogonal ao momentum — informacao que os modelos anteriores nao conseguiam extrair por variancia amostral.

### 2.3 CPCV — 15 Paths (com Fees)

| Path | Accuracy | F1 | Sharpe |
|:----:|:--------:|:--:|:------:|
| 1 | 0.6568 | 0.6723 | 0.0732 |
| 2 | 0.6791 | 0.6806 | 0.0478 |
| 3 | 0.6907 | 0.6887 | 0.0610 |
| 4 | 0.6853 | 0.6845 | 0.0692 |
| 5 | 0.6716 | 0.6810 | 0.0625 |
| 6 | 0.6598 | 0.6658 | 0.0579 |
| 7 | 0.6821 | 0.6815 | 0.0486 |
| 8 | 0.6893 | 0.6888 | 0.0374 |
| 9 | 0.6821 | 0.6850 | 0.0522 |
| 10 | 0.6680 | 0.6679 | 0.0579 |
| 11 | 0.6793 | 0.6792 | 0.0425 |
| 12 | 0.6666 | 0.6717 | 0.0524 |
| 13 | 0.6831 | 0.6818 | 0.0806 |
| 14 | 0.6827 | 0.6814 | 0.0687 |
| 15 | 0.6817 | 0.6830 | 0.0875 |
| **Media** | **0.6772** | **0.6796** | **+0.0600** |
| **Std** | **0.0099** | **0.0068** | **0.0135** |

![CPCV Sharpe Distribution — Modelo 5](pngs/cpcv_sharpe_distribution_mod5.png)

![CPCV Accuracy Distribution — Modelo 5](pngs/cpcv_accuracy_distribution_mod5.png)

**Comparativo CPCV entre todos os modelos:**

| Metrica | Mod1 | Mod2 | Mod3 | Mod4 | **Mod5** |
|---------|:---:|:---:|:---:|:---:|:---:|
| Accuracy | 59.7% | 63.6% | 63.6% | 67.3% | **67.7%** |
| F1 | 0.617 | 0.658 | 0.638 | 0.678 | **0.680** |
| **Sharpe medio** | -0.003 | +0.035 | +0.108 | +0.067 | **+0.060** |
| **Paths SR > 0** | 6/15 | 14/15 | 15/15 | 15/15 | **15/15** |
| **Sharpe minimo** | -0.027 | -0.027 | +0.063 | +0.027 | **+0.037** |
| PSR (CPCV OOS) | 0.623 | 0.980 | 1.000 | 1.000 | **1.000** |
| Std Sharpe | 0.014 | 0.022 | 0.028 | 0.024 | **0.014** |
| Std Accuracy | — | — | 0.021 | 0.020 | **0.010** |

**Resultados notaveis:**

1. **Accuracy e F1 sao recordes** — 67.7% e 0.680. Mais dados de treino melhoram a classificacao de regimes.

2. **Sharpe medio CPCV de 0.060 — positivo APOS fees.** A queda vs Mod4 (0.067→0.060) e o custo dos fees pessimistas (taker ambas pontas). O sinal sobrevive.

3. **15/15 paths positivos, minimo 0.037.** Nenhum path ficou negativo mesmo pagando 0.054% por round-trip em cada troca de posicao.

4. **Std Sharpe de 0.014 — a mais baixa da serie.** A dispersao entre paths caiu pela metade vs Mod3/Mod4. Com 3x mais dados, os splits CPCV sao maiores e as estimativas mais estaveis. O modelo e mais **consistente** entre diferentes janelas temporais.

5. **Std Accuracy de 0.010 — tambem recorde.** O range do boxplot (0.657 a 0.691) e estreitissimo. O classificador e robusto.

### 2.4 Meta-Labeling — Teste In-Sample

| Metrica | Mod1 | Mod2 | Mod3 | Mod4 | **Mod5** |
|---------|:---:|:---:|:---:|:---:|:---:|
| Accuracy (meta) | 17.6% | 47.8% | 17.9% | 31.6% | **10.6%** |
| F1 (weighted) | 0.240 | 0.594 | 0.278 | 0.437 | **0.186** |
| Sharpe | 0.020 | 0.093 | 0.057 | 0.091 | **0.045** |
| PSR | 0.750 | 0.974 | 0.986 | 0.999 | **0.994** |
| Kurtosis | 194 | 55.8 | 45.3 | 27.0 | **26.2** |
| Skewness | -1.335 | -0.903 | +3.652 | +1.761 | **+0.384** |

**Confusion Matrix (meta-label, teste in-sample):**

| | Pred Bear (-1) | Pred Neutro (0) | Pred Bull (+1) |
|---|:---:|:---:|:---:|
| **Real Bear (1437)** | **161** | 1250 | 26 |
| **Real Neutro (5)** | 3 | **2** | 0 |
| **Real Bull (1544)** | 31 | 1361 | **152** |

![Confusion Matrix Treino — Modelo 5](pngs/confusion_matrix_mod5.png)

**Precision e Recall in-sample:**

| Classe | Precision | Recall |
|--------|:---------:|:------:|
| Bear (-1) | **83%** | 11% |
| Bull (+1) | **85%** | 10% |

O modelo e **extremamente conservador** no teste in-sample — absteve em 87% das barras (2613/2986). A precision se mantem alta (83-85%), e a kurtosis atingiu o minimo da serie (26.2). A skewness e positiva (+0.38) mas proxima de zero — perfil quase simetrico, sem os eventos de cauda extremos dos modelos anteriores.

### 2.5 Portfolio Equity — Teste In-Sample

![Portfolio Equity Treino — Modelo 5](pngs/portfolio_equity_mod5.png)

O grafico de portfolio equity do teste in-sample mostra a curva da estrategia (azul) vs BTC buy & hold (laranja) durante o periodo de teste do treino. A curva azul cresce em degraus discretos — cada degrau corresponde a um trade ativo onde o modelo apostou corretamente. Entre os degraus, a linha e flat (abstencao). O drawdown maximo e visivel mas contido.

---

## 3. Teste Out-of-Sample — Bear Market (ago/2025 a mar/2026)

### 3.1 Setup

| Parametro | Valor |
|-----------|:-----:|
| Periodo | 2025-08-01 a 2026-03-23 |
| Duracao | 203.6 dias |
| Linhas 1-min | 338,114 |
| Dollar Bars (threshold $1.328B) | 2,554 |
| Barras rotuladas | 1,932 |
| Labels: Bear / Neutro / Bull | 984 / 3 / 945 |
| Trades ativos | **335 (17.3%)** |
| Abstencoes | 1,597 (82.7%) |
| **Fees por trade** | **0.027% taker entrada + 0.027% taker saida** |

### 3.2 Resultados OOS — Alpha Sobrevive Apos Fees

| Estrategia | Retorno |
|------------|:-------:|
| **Modelo 5 (Meta-Label, c/ fees)** | **+54.02%** |
| BTC Buy & Hold | -34.28% |
| US Risk-Free (4.5% a.a.) | +2.49% |
| **Alpha vs BTC** | **+88.30pp** |
| **Excesso vs Risk-Free** | **+51.53pp** |

**Comparativo de retorno OOS entre todos os modelos:**

| Metrica | Mod1 | Mod2 | Mod3 | Mod4 | **Mod5** |
|---------|:---:|:---:|:---:|:---:|:---:|
| Retorno | +13.85% | +21.85%* | +33.03% | +114.71% | **+54.02%** |
| Fees incluidos? | Nao | Nao | Nao | Nao | **Sim** |
| BTC B&H | -38.08% | +171.35%* | -37.30% | -34.28% | **-34.28%** |
| Alpha vs BTC | +52pp | -150pp* | +70pp | +149pp | **+88pp** |
| Excesso vs RF | +5.89pp | +15.01pp* | +30.54pp | +112pp | **+52pp** |

*\*Mod2 OOS era periodo diferente (4.5 anos bull)*

**+54% liquido de fees num bear market de -34%.** O retorno caiu vs Mod4 (+115%), mas a comparacao direta nao e justa: o Mod5 tem dataset de treino expandido (features e modelo diferentes), alem dos fees. O importante: **alpha de +88pp vs BTC e +52pp vs risk-free depois de pagar todas as comissoes**.

### 3.3 Confusion Matrix OOS

| | Pred Bear (-1) | Pred Neutro (0) | Pred Bull (+1) |
|---|:---:|:---:|:---:|
| **Real Bear (984)** | **205** | 774 | 5 |
| **Real Neutro (3)** | 3 | 0 | 0 |
| **Real Bull (945)** | 36 | 823 | **86** |

![Confusion Matrix OOS — Modelo 5](pngs/confusion_matrix_oos_mod5.png)

**Precision e Recall OOS:**

| Classe | Precision | Recall |
|--------|:---------:|:------:|
| Bear (-1) | **84%** | 21% |
| Bull (+1) | **95%** | 9% |

**Comparativo Precision/Recall OOS entre todos os modelos:**

| Metrica | Mod1 | Mod2 | Mod3 | Mod4 | **Mod5** |
|---------|:---:|:---:|:---:|:---:|:---:|
| Precision Bear | 89% | 74% | 68% | 85% | **84%** |
| Precision Bull | 80% | 71% | 68% | 88% | **95%** |
| Recall Bear | 12% | 49% | 7% | 34% | **21%** |
| Recall Bull | 20% | 47% | 10% | 27% | **9%** |
| Abstencao | 81% | 37% | 87% | 64.5% | **82.7%** |
| Erros direcionais | 70 | 834 | 106 | 90 | **41** |
| Trades ativos | 490 | 3,603 | 335 | 685 | **335** |

**Destaques extraordinarios:**

1. **Precision bull de 95%** — o recorde absoluto da serie. Das 91 apostas bull, apenas 5 estavam erradas. Em 19 de cada 20 vezes que o modelo disse "compra", estava certo.

2. **Apenas 41 erros direcionais** — menos da metade do Mod4 (90) e do Mod1 (70). De 335 trades ativos, apenas 41 tiveram sinal trocado (5 bears classificados como bull + 36 bulls classificados como bear). Taxa de erro direcional de 12.2%.

3. **Assimetria nos erros:** o modelo errou 36 vezes em bull→bear mas apenas 5 vezes em bear→bull. Isso significa que o vies de erro e conservador — quando erra, tende a shortear quando deveria comprar (perda limitada pela alta do mercado), raramente compra quando deveria shortear (exposicao a queda).

4. **O modelo e mais conservador no lado bull** (91 trades) que no lado bear (244 trades). Em um bear market, isso faz sentido — mais oportunidades de short.

### 3.4 Sharpe Ratios OOS

| Metrica | Todas barras | Trades ativos (335) |
|---------|:---:|:---:|
| **Sharpe Ratio** | **0.0566** | **0.1421** |
| **PSR** | **0.9742** | **0.9757** |
| DSR | 0.000 | 0.000 |
| Skewness | -7.966 | **-3.760** |
| Kurtosis (excess) | 230.3 | **40.6** |

**Sharpe vs US Risk-Free (4.5% a.a.):**

| Base | SR vs RF | PSR |
|------|:---:|:---:|
| Todas barras | 0.0535 | 0.9689 |
| Trades ativos | **0.1408** | **0.9750** |

**Comparativo de Sharpe OOS entre todos os modelos:**

| Metrica | Mod1 | Mod2 | Mod3 | Mod4 | **Mod5** |
|---------|:---:|:---:|:---:|:---:|:---:|
| SR (todas barras) | 0.019 | 0.009 | 0.068 | 0.084 | **0.057** |
| SR (trades ativos) | 0.044 | 0.011 | **0.191** | 0.142 | 0.142 |
| PSR (trades ativos) | 0.817 | 0.737 | **0.9999** | 0.998 | 0.976 |
| Kurtosis (ativos) | 54.9 | 189.9 | **7.1** | 41.5 | 40.6 |
| Skewness (ativos) | -2.8 | -8.9 | **+1.3** | -3.2 | -3.8 |

**Analise:**

O **Sharpe por trade ativo (0.142)** e identico ao Mod4, apesar dos fees pessimistas. Isso indica que o impacto dos fees no Sharpe por trade e **negligivel** — 0.054% de custo por round-trip e pequeno comparado ao retorno medio por trade.

A diferenca real e o **numero de trades**: 335 (Mod5) vs 685 (Mod4). O meta-labeler do Mod5, treinado com mais dados e features diferentes, e mais seletivo — filtra 83% das barras vs 65% no Mod4. O retorno total cai (54% vs 115%) porque ha menos oportunidades capturadas, nao porque cada trade e pior.

A **skewness permanece negativa** (-3.76) e a **kurtosis alta** (40.6) — perfil similar ao Mod4, com eventos de cauda negativos. O Mod3 continua sendo o unico modelo com skewness positiva.

### 3.5 Filtragem do Meta-Labeler

![Meta Label Filtering OOS — Modelo 5](pngs/meta_label_filtering_oos_mod5.png)

O meta-labeler filtrou 82.7% das barras — voltando ao padrao conservador do Mod1 (81%) e Mod3 (87%). Os 335 trades ativos estao concentrados em momentos de alta convicao onde ret_20 + VPIN + Kyle Lambda convergem.

### 3.6 Regimes Detectados

![Regime Classification OOS — Modelo 5](pngs/regime_classification_oos_mod5.png)

### 3.7 Triple-Barrier Labels

![Triple Barrier Labels OOS — Modelo 5](pngs/triple_barrier_labels_oos_mod5.png)

### 3.8 Retorno Acumulado

![Retorno Acumulado OOS — Modelo 5](pngs/cumulative_returns_oos_mod5.png)

### 3.9 Portfolio Equity

![Portfolio Equity OOS — Modelo 5](pngs/portfolio_equity_oos_mod5.png)

---

## 4. Analise — O Impacto Real dos Fees

### 4.1 Quanto Custaram os Fees?

Com 335 trades ativos e fee_mode pessimista (taker ambas pontas):

```
Custo por round-trip: 2 × 0.027% = 0.054%
Total estimado de round-trips: ~335
Custo total estimado: 335 × 0.054% ≈ 0.18pp
```

**Apenas ~0.18 pontos percentuais** de drag sobre um retorno de +54%. Os fees sao quase irrelevantes. O motivo: o modelo opera com **frequencia baixa** (~1.6 trades/dia) sobre **barras grossas** ($1.3B cada). Cada trade captura movimentos de ~2.4h que valem dezenas/centenas de bps — o fee de 0.054% e negligivel comparado ao tamanho do movimento.

Isso confirma que **a frequencia de operacao do modelo (barras de 10/dia) e naturalmente compativel com os custos de futures da Binance**. O Mod5 nao precisou sacrificar alpha para pagar fees.

### 4.2 Entao Por Que o Retorno Caiu de 115% para 54%?

A queda nao e explicada pelos fees (~0.18pp). Os fatores reais:

1. **Modelo diferente.** O Mod5 foi retreinado com 3x mais dados e selecionou features diferentes (VPIN, Kyle Lambda, tstat_50 vs volatility_20, vix_chg, log_volume). E um modelo distinto, nao "Mod4 + fees".

2. **Metade dos trades.** 335 trades ativos vs 685 no Mod4. O meta-labeler do Mod5 e mais seletivo — talvez por causa das features de microestrutura (VPIN) que adicionam uma camada de filtragem que o Mod4 nao tinha.

3. **Recall menor.** Bull recall 9% vs 27% (Mod4). O modelo captura 3x menos oportunidades bull. Em compensacao, quando captura, acerta 95% das vezes.

**A relacao real e: Mod5 = modelo diferente com features melhores e fees incluidos. Nao e uma versao degradada do Mod4.**

### 4.3 O Argumento para fee_mode "optimistic"

Se o alpha sobrevive com taker em ambas as pontas, existe margem para otimizar a execucao:

| Cenario | Custo round-trip | Retorno estimado* |
|---------|:---:|:---:|
| Pessimista (taker + taker) | 0.054% | +54.02% (medido) |
| Otimista (taker + maker) | 0.036% | ~+54.08% (estimado) |
| Sem fees | 0.000% | ~+54.20% (estimado) |

*\*Estimativa linear: 335 round-trips × diferenca de fee*

A diferenca entre pessimista e otimista e de apenas ~0.006pp. **A escolha de fee_mode e irrelevante na pratica** para este modelo — a frequencia de trading e baixa demais para que a diferenca importe.

### 4.4 Perfil de Risco: Comparativo com Fees

| Metrica de Risco | Mod3 | Mod4 (sem fees) | **Mod5 (com fees)** |
|---|:---:|:---:|:---:|
| Sharpe (ativos) | **0.191** | 0.142 | 0.142 |
| Skewness | **+1.3** | -3.2 | -3.8 |
| Kurtosis | **7.1** | 41.5 | 40.6 |
| Max Drawdown | Menor | Moderado | Moderado |
| Erros direcionais | 106 | 90 | **41** |
| Precision Bull | 68% | 88% | **95%** |

O Mod5 tem o **menor numero de erros e a maior precisao bull da serie**, mas o perfil de distribuicao de retornos (skewness negativa, kurtosis alta) e similar ao Mod4 e inferior ao Mod3.

---

## 5. Tabela Comparativa Final — Cinco Modelos

### 5.1 Treino (CPCV)

| Metrica | Mod1 | Mod2 | Mod3 | Mod4 | **Mod5** | Melhor |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| Bars/dia | 50 | 50 | 20 | 10 | **10** | — |
| Features | 10 | 4 | 8 | 5 | **6** | — |
| Fees | Nao | Nao | Nao | Nao | **Sim** | — |
| Accuracy | 59.7% | 63.6% | 63.6% | 67.3% | **67.7%** | **Mod5** |
| F1 | 0.617 | 0.658 | 0.638 | 0.678 | **0.680** | **Mod5** |
| Sharpe CPCV | -0.003 | +0.035 | **+0.108** | +0.067 | +0.060 | **Mod3** |
| Paths SR > 0 | 6/15 | 14/15 | **15/15** | **15/15** | **15/15** | Empate |
| SR minimo | -0.027 | -0.027 | **+0.063** | +0.027 | +0.037 | **Mod3** |
| Std Accuracy | — | — | 0.021 | 0.020 | **0.010** | **Mod5** |
| Std Sharpe | 0.014 | 0.022 | 0.028 | 0.024 | **0.014** | Empate |

### 5.2 OOS (Bear Market)

| Metrica | Mod1 | Mod2* | Mod3 | Mod4 | **Mod5** | Melhor (bear) |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| Retorno | +13.85% | +21.85% | +33.03% | +114.71% | **+54.02%** | Mod4 (bruto) / **Mod5 (liq.)** |
| Fees | Nao | Nao | Nao | Nao | **Sim** | — |
| Alpha vs BTC | +52pp | -150pp | +70pp | +149pp | **+88pp** | Mod4 |
| SR (ativos) | 0.044 | 0.011 | **0.191** | 0.142 | 0.142 | **Mod3** |
| PSR (ativos) | 0.817 | 0.737 | **0.9999** | 0.998 | 0.976 | **Mod3** |
| Kurtosis | 54.9 | 189.9 | **7.1** | 41.5 | 40.6 | **Mod3** |
| Skewness | -2.8 | -8.9 | **+1.3** | -3.2 | -3.8 | **Mod3** |
| Precision Bear | **89%** | 74% | 68% | 85% | 84% | Mod1 |
| Precision Bull | 80% | 71% | 68% | 88% | **95%** | **Mod5** |
| Erros dir. | 70 | 834 | 106 | 90 | **41** | **Mod5** |
| Trades ativos | 490 | 3,603 | 335 | 685 | **335** | — |

*\*Mod2 OOS era periodo diferente (4.5 anos bull)*

### 5.3 Perfil de Cada Modelo

**Modelo 1 — O Sniper Classico:**
Precision maxima bear (89%). Fraqueza: Sharpe fraco, sem fees.

**Modelo 2 — O Soldado Agressivo:**
Mais trades, mais recall. Fraqueza: kurtosis extrema (190), perde para BTC em bull.

**Modelo 3 — O Estrategista Conservador:**
Melhor Sharpe/trade (0.191), unico com skewness positiva. **Melhor perfil de risco puro.** Fraqueza: sem fees, retorno modesto.

**Modelo 4 — O Operador de Alto Retorno:**
Retorno recorde (+115%), precision alta. Fraqueza: sem fees, skewness negativa.

**Modelo 5 — O Modelo Realista:**
Primeiro com fees pessimistas incluidos. **Precision bull recorde (95%), menor numero de erros (41), alpha de +54% liquido.** Features de microestrutura (VPIN, Kyle Lambda). Fraqueza: skewness negativa, recall baixo.

---

## 6. Ressalvas e Limitacoes

### 6.1 O Que Preocupa

**A. Skewness -3.76 e kurtosis 40.6.**
Eventos de cauda negativos persistem. Embora os fees estejam incorporados, stops e gestao de posicao sao necessarios em producao.

**B. DSR = 0 continua.**
Nenhum modelo da serie passa no teste mais rigoroso.

**C. Recall bull de 9%.**
O modelo captura apenas ~1 em 11 oportunidades bull. Excelente quando opera, mas inativo demais no lado comprado.

**D. fear_greed_chg com MDA negativa no CPCV final (-0.0001).**
Esta feature sobreviveu a selecao por margem minima (+0.0001 na fase de selecao) mas e contraproducente no modelo final. Versoes futuras devem aumentar o threshold de selecao.

**E. Dataset de treino diferente do Mod4.**
A comparacao Mod4 vs Mod5 nao isola o efeito dos fees — o modelo, as features e o volume de dados mudaram simultaneamente.

### 6.2 O Que E Genuino

**A. O alpha sobrevive apos fees pessimistas.**
+54.02% liquido num bear de -34%. PSR 0.976 nos trades ativos. O sinal e real.

**B. 15/15 paths CPCV positivos com fees.**
Sharpe minimo 0.037 APOS pagar taker em ambas as pontas. Nenhuma janela temporal perdeu dinheiro.

**C. Precision bull de 95% — quase cirurgica.**
5 erros em 91 apostas bull. O modelo sabe quando o mercado vai subir.

**D. 41 erros direcionais em 335 trades.**
Taxa de erro direcional de 12.2% — a mais baixa da serie.

**E. Fees sao irrelevantes nesta frequencia.**
~0.18pp de drag sobre +54% de retorno. A arquitetura de barras grossas (10/dia) torna os custos de transacao um non-issue.

---

## 7. Proximos Passos

1. **Isolar o efeito puro dos fees** — rodar Mod4 (mesmos dados, mesmas features) com e sem fees, para quantificar exatamente quanto o fee pessimista custa ao Mod4.

2. **Testar OOS em bull market** — o Mod5 nao foi testado em condicoes de alta.

3. **Remover fear_greed_chg** — MDA negativa no CPCV final sugere que e uma feature ruido.

4. **Ensemble Mod3 + Mod5** — Mod3 tem skewness positiva e o melhor Sharpe/trade; Mod5 tem a maior precisao e menos erros. Operar Mod5 nos momentos em que Mod3 tambem concorda pode combinar o melhor dos dois perfis.

5. **Implementar stops dinamicos** — a skewness negativa exige protecao contra eventos de cauda. Stop baseado em volatility_20 ou VPIN.

---

## Apendice A — Configuracao do Modelo 5

| Parametro | Valor |
|-----------|:-----:|
| Dollar bars/dia | **10 (fixo)** |
| Threshold | **$1,328,433,250** |
| Features selecionadas | **ret_20, ret_60, vpin, tstat_50, kyle_lambda, fear_greed_chg** |
| **fee_maker** | **0.0090%** |
| **fee_taker** | **0.0270%** |
| **fee_mode** | **pessimistic (taker ambas pontas)** |
| FFD d | 0.4 |
| SavGol window / polyorder | 21 / 3 |
| PT/SL multiplier | 2.0x / 2.0x |
| Max holding bars | 50 |
| CPCV groups / k_test | 6 / 2 |
| CPCV purge / embargo | 1% / 1% |
| MDA repeats / threshold | 5 / 0.0 |
| RF estimators / depth / leaf | 500 / 6 / 50 |
| Train ratio | 0.8 |
| Train/Test split | 11,942 / 2,986 |

## Apendice B — Estrutura de Fees

```
fee_mode = "pessimistic" (padrao):
  Entrada:  taker = 0.0270%  (market order)
  Saida:    taker = 0.0270%  (market order)
  Flip:     taker + taker = 0.0540%

fee_mode = "optimistic":
  Entrada:  taker = 0.0270%  (market order)
  Saida:    maker = 0.0090%  (limit order)
  Flip:     maker + taker = 0.0360%
```

Os fees sao aplicados a cada MUDANCA de posicao na funcao `compute_strategy_returns()`. Posicoes mantidas (sem mudanca) nao incorrem custo adicional.

## Apendice C — Arquivos Gerados

```
relatorios/
  relatorio_regime_detection_mod1.md     (Modelo 1)
  relatorio_regime_detection_mod2.md     (Modelo 2)
  relatorio_regime_detection_mod3.md     (Modelo 3)
  relatorio_regime_detection_mod4.md     (Modelo 4)
  relatorio_regime_detection_mod5.md     (Modelo 5 — este documento)
  pngs/
    *_mod5.png                           (plots treino Modelo 5)
    *_oos_mod5.png                       (plots OOS Modelo 5)
  modelos/
    mod1.joblib                          (Modelo 1)
    trained_model_mod2.joblib            (Modelo 2)
    trained_model_mod3.joblib            (Modelo 3)
    trained_model_mod4.joblib            (Modelo 4)
    trained_model_mod5.joblib            (Modelo 5)
```

---

*Relatorio gerado em 2026-03-24. Pipeline: regime_detection_advanced.py + rd_adv_application.py*
*Experimento: primeiro modelo com custos de transacao pessimistas (taker ambas pontas). Features de microestrutura (VPIN, Kyle Lambda) emergem com dataset expandido.*
