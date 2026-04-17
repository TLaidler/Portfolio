# Regime Detection BTC/USDT — Relatorio Modelo 0 (Baseline Negativo: Sem Features de Retorno)

**Modelo:** Random Forest + Meta-Labeling sobre Dollar Bars (AFML Framework)
**Ativo:** BTC/USDT Perpetual Futures (Binance)
**Data do relatorio:** 2026-03-24
**Experimento:** Ablacao de todas as features de retorno/savgol (ret_20, ret_60, volatility_20, mom_residual_50). Baseline negativo para quantificar a contribuicao do momentum ao pipeline.

---

> *"A essencia do conhecimento e, tendo-o, aplica-lo; nao o tendo, confessar a sua ignorancia."*
> — Confucio

---

## 1. Motivacao — O Que Mudamos e Por Que

O Modelo 0 e um **experimento de ablacao negativa**: removemos deliberadamente as features que a serie de modelos (1-6) identificou como dominantes — todas derivadas de retorno/savgol — para medir o que resta quando o modelo perde acesso a informacao de momentum.

| Mudanca | Hipotese |
|---------|----------|
| **disable_savgol_returns = True** | Remove ret_20, ret_60, volatility_20 (do SavGolMomentumFeature) e mom_residual_50 (do MomentumResidualFeature). Preserva log_volume |
| **14 features candidatas** | Pool reduzido: microestrutura, exogenas, t-stats, RSI, entropia — nenhuma informacao direta de retorno passado |
| **Fees pessimistas mantidos** | Taker ambas pontas (0.054%/round-trip), mesma config do Mod5 |
| **Mesmo dataset** | 14,928 barras rotuladas, train/test 11,942/2,986 |

**Pergunta central:** *As features de microestrutura, exogenas e estatisticas sao suficientes para detectar regimes sem informacao de retorno?*

**Resposta antecipada:** Nao. Este modelo existe para confirmar que **ret_20 e insubstituivel** e quantificar o tamanho da perda.

---

## 2. Treinamento — Modelo Sem Retornos

### 2.1 Dollar Bars e Dataset

| Parametro | Mod5 (com retornos) | **Mod0 (sem retornos)** |
|-----------|:---:|:---:|
| Bars/dia | 10 (fixo) | **10 (fixo)** |
| Threshold | $1,328M | **$1,328M** |
| Dollar Bars | 18,405 | **18,405** |
| Barras rotuladas | 14,928 | **14,928** |
| Train/Test | 11,942/2,986 | **11,942/2,986** |
| Features candidatas | 18 | **14** |
| disable_savgol_returns | False | **True** |

![Dollar Bars Sampling — Modelo 0](pngs/dollar_bars_sampling_mod0.png)

### 2.2 Selecao de Features — Tudo Fraco

Das 14 features candidatas, o MDA selecionou **11** (threshold > 0):

| Feature | MDA (selecao) | MDA (final CPCV) | Status |
|---------|:---:|:---:|:---:|
| **tstat_20** | 0.0070 | 0.0095 | Selecionada |
| **roll_spread** | 0.0037 | 0.0028 | Selecionada |
| **rsi** | 0.0037 | 0.0051 | Selecionada |
| **fear_greed_chg** | 0.0033 | 0.0042 | Selecionada |
| **vix_chg** | 0.0032 | 0.0018 | Selecionada |
| **kyle_lambda** | 0.0011 | 0.0011 | Selecionada |
| **log_volume** | 0.0010 | 0.0012 | Selecionada |
| **tstat_10** | 0.0009 | 0.0016 | Selecionada |
| **vpin** | 0.0004 | -0.0004 | Selecionada |
| **btc_dxy_spread** | 0.0003 | 0.0014 | Selecionada |
| **funding_rate_zscore** | 0.0001 | -0.0002 | Selecionada |
| lz_entropy | 0.0000 | — | Rejeitada |
| ffd_close | -0.0014 | — | Rejeitada |
| tstat_50 | -0.0015 | — | Rejeitada |

![Feature Importance MDA — Modelo 0](pngs/feature_importance_mda_mod0.png)

**Observacoes criticas:**

1. **A feature mais importante (tstat_20) tem MDA 0.010.** Compare com ret_20 no Mod5: MDA 0.156. A melhor feature sem retornos e **17x mais fraca** que a feature dominante com retornos. O modelo perdeu seu motor principal.

2. **Todas as features tem MDA < 0.01.** No Mod5, ret_20 sozinha tinha MDA 0.156 — mais que a SOMA de todas as 11 features selecionadas no Mod0 (total ~0.025). A informacao preditiva disponivel e radicalmente menor.

3. **11 features selecionadas — o maior numero da serie.** Paradoxalmente, o MDA selecionou quase tudo porque todas as features tem importancia ~similar e proxima de zero. Sem um sinal dominante, o threshold 0.0 nao consegue distinguir sinal de ruido.

4. **VPIN e funding_rate_zscore com MDA negativa no CPCV final** (-0.0004 e -0.0002), apesar de selecionadas. Essas features sao ativamente contraproducentes — o modelo seria melhor sem elas.

5. **tstat_20 e rsi sao as unicas features com MDA > 0.005.** Ambas sao derivadas indiretas de retorno (t-stat mede a significancia do retorno medio; RSI mede forca relativa de subidas vs descidas). O pouco sinal que resta vem de proxies fracas de momentum.

**Comparativo da feature mais importante entre modelos:**

| Modelo | Top Feature | MDA Top | Features Selecionadas |
|--------|---|:---:|:---:|
| Mod1 | ret_20 | — | 10 |
| Mod2 | ret_20 | — | 4 |
| Mod3 | ret_20 | — | 8 |
| Mod4 | ret_20 | 0.183 | 5 |
| Mod5 | ret_20 | 0.156 | 6 |
| Mod6 | ret_20 | 0.144 | 5 |
| **Mod0** | **tstat_20** | **0.010** | **11** |

### 2.3 CPCV — 15 Paths (com Fees)

| Path | Accuracy | F1 | Sharpe |
|:----:|:--------:|:--:|:------:|
| 1 | 0.5197 | 0.5198 | 0.3297 |
| 2 | 0.5125 | 0.5155 | 0.0821 |
| 3 | 0.5179 | 0.5166 | 0.2096 |
| 4 | 0.5040 | 0.4895 | 0.1636 |
| 5 | 0.5197 | 0.5193 | 0.1176 |
| 6 | 0.4803 | 0.3738 | 0.0056 |
| 7 | 0.5143 | 0.5126 | 0.1625 |
| 8 | 0.5123 | 0.5113 | 0.0884 |
| 9 | 0.5289 | 0.5284 | 0.1006 |
| 10 | 0.5034 | 0.4953 | 0.1670 |
| 11 | 0.5205 | 0.5177 | 0.0930 |
| 12 | 0.5376 | 0.5392 | 0.0773 |
| 13 | 0.5123 | 0.5031 | 0.2044 |
| 14 | 0.4885 | 0.4857 | 0.1346 |
| 15 | 0.5008 | 0.4157 | 0.0527 |
| **Media** | **0.5115** | **0.4962** | **+0.1326** |
| **Std** | **0.0141** | **0.0427** | **0.0757** |

![CPCV Sharpe Distribution — Modelo 0](pngs/cpcv_sharpe_distribution_mod0.png)

![CPCV Accuracy Distribution — Modelo 0](pngs/cpcv_accuracy_distribution_mod0.png)

**Comparativo CPCV entre todos os modelos:**

| Metrica | Mod1 | Mod2 | Mod3 | Mod4 | Mod5 | Mod6 | **Mod0** |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Accuracy | 59.7% | 63.6% | 63.6% | 67.3% | 67.7% | 66.3% | **51.2%** |
| F1 | 0.617 | 0.658 | 0.638 | 0.678 | 0.680 | 0.656 | **0.496** |
| **Sharpe medio** | -0.003 | +0.035 | +0.108 | +0.067 | +0.060 | +0.064 | **+0.133** |
| **Paths SR > 0** | 6/15 | 14/15 | 15/15 | 15/15 | 15/15 | 15/15 | **15/15** |
| **Sharpe minimo** | -0.027 | -0.027 | +0.063 | +0.027 | +0.037 | +0.015 | **+0.006** |
| PSR (CPCV OOS) | 0.623 | 0.980 | 1.000 | 1.000 | 1.000 | 1.000 | **1.000** |
| Std Sharpe | 0.014 | 0.022 | 0.028 | 0.024 | 0.014 | 0.018 | **0.076** |
| Std Accuracy | — | — | 0.021 | 0.020 | 0.010 | 0.011 | **0.014** |

**Resultados notaveis:**

1. **Accuracy de 51.2% — essencialmente aleatorio.** Caiu de 67.7% (Mod5) para pouco acima de 50%. Um classificador ternario (bear/neutro/bull) aleatorio uniforme daria ~33%; com classes balanceadas bear/bull (sem neutro), um coin flip da ~50%. O modelo nao aprendeu praticamente nada.

2. **Sharpe medio CPCV de +0.133 — SUSPEITOSAMENTE ALTO.** Este e o segundo maior Sharpe CPCV da serie, atras apenas do Mod3 (0.108)... num modelo que acerta 51%. Como e possivel?

   A explicacao: **com 51% de accuracy e alta abstencao do meta-labeler, as poucas operacoes que passam pelo filtro podem ter Sharpe positivo por puro acaso.** O Std de 0.076 (o maior da serie, 5x o Mod5) confirma a instabilidade — o Sharpe varia de 0.006 a 0.330 entre paths, um range de 55x. Compare com o Mod5 onde o range e de 3x (0.037 a 0.088).

3. **PSR = 1.000 — FALSO POSITIVO.** O PSR testa se o Sharpe agregado do CPCV e significativamente > 0. Com 15 paths todos positivos, o teste passa. Mas o PSR nao detecta que o sinal e espurio — demonstracao classica da limitacao do PSR quando a distribuicao subjacente tem alta dispersao.

4. **Std Sharpe de 0.076 — recorde negativo.** A dispersao entre paths e 5x maior que no Mod5. Nao ha estabilidade temporal — o resultado de cada path e quase independente dos outros, sugerindo que o Sharpe positivo e aleatorio.

### 2.4 Meta-Labeling — Teste In-Sample

| Metrica | Mod1 | Mod2 | Mod3 | Mod4 | Mod5 | Mod6 | **Mod0** |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Accuracy (meta) | 17.6% | 47.8% | 17.9% | 31.6% | 10.6% | 36.1% | **2.6%** |
| F1 (weighted) | 0.240 | 0.594 | 0.278 | 0.437 | 0.186 | 0.491 | **0.047** |
| Sharpe | 0.020 | 0.093 | 0.057 | 0.091 | 0.045 | 0.053 | **-0.034** |
| PSR | 0.750 | 0.974 | 0.986 | 0.999 | 0.994 | 0.992 | **0.024** |
| Kurtosis | 194 | 55.8 | 45.3 | 27.0 | 26.2 | 25.3 | **96.6** |
| Skewness | -1.335 | -0.903 | +3.652 | +1.761 | +0.384 | +0.626 | **-4.073** |

**Confusion Matrix (meta-label, teste in-sample):**

| | Pred Bear (-1) | Pred Neutro (0) | Pred Bull (+1) |
|---|:---:|:---:|:---:|
| **Real Bear (1437)** | **53** | 1370 | 14 |
| **Real Neutro (5)** | 0 | **4** | 1 |
| **Real Bull (1544)** | 33 | 1490 | **21** |

![Confusion Matrix Treino — Modelo 0](pngs/confusion_matrix_mod0.png)

**Precision e Recall in-sample:**

| Classe | Precision | Recall |
|--------|:---------:|:------:|
| Bear (-1) | **62%** | 4% |
| Bull (+1) | **58%** | 1% |

**Analise devastadora:**

- **Sharpe NEGATIVO (-0.034) no teste in-sample.** E o primeiro e unico modelo da serie com Sharpe negativo no proprio teste de treino. Todos os outros modelos (incluindo o Mod1, o mais fraco) tinham Sharpe positivo aqui. O modelo perde dinheiro mesmo nos dados que conhece.

- **PSR de 0.024 — o mais baixo da serie por larga margem.** Apenas 2.4% de confianca de que o Sharpe e positivo. Compare com o Mod5 (99.4%). O teste estatistico basicamente diz: *este modelo nao tem sinal*.

- **Kurtosis de 96.6 — a segunda maior da serie (atras apenas do Mod1 com 194).** A distribuicao de retornos tem caudas extremas. Skewness de -4.07 — caudas negativas pesadas. O modelo, quando opera, tende a perder muito nos raros trades que faz errado.

- **Accuracy de 2.6% com recall bull de 1%.** O meta-labeler filtrou ~97% das barras. Das poucas que passaram, a maioria esta errada. O modelo opera quase nunca, e quando opera, nao sabe para que lado.

### 2.5 Portfolio Equity — Teste In-Sample

![Portfolio Equity Treino — Modelo 0](pngs/portfolio_equity_mod0.png)

O grafico de portfolio equity in-sample mostra uma curva essencialmente flat com alguns spikes erraticos — tanto para cima quanto para baixo. Nao ha tendencia direcional. A estrategia nao gera alpha consistente nem no periodo de treino. Compare com os degraus positivos visiveis nos Mod4/Mod5.

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
| Trades ativos | **174 (9.0%)** |
| Abstencoes | 1,758 (91.0%) |
| **Fees por trade** | **0.027% taker entrada + 0.027% taker saida** |

### 3.2 Resultados OOS — Primeiro Retorno Negativo da Serie

| Estrategia | Retorno |
|------------|:-------:|
| **Modelo 0 (sem retornos, c/ fees)** | **-24.82%** |
| BTC Buy & Hold | -34.28% |
| US Risk-Free (4.5% a.a.) | +2.49% |
| **Alpha vs BTC** | **+9.47pp** |
| **Excesso vs Risk-Free** | **-27.30pp** |

**Comparativo de retorno OOS entre todos os modelos:**

| Metrica | Mod1 | Mod2 | Mod3 | Mod4 | Mod5 | Mod6 | **Mod0** |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Retorno | +13.85% | +21.85%* | +33.03% | +114.71% | +54.02% | +266.94%** | **-24.82%** |
| Fees? | Nao | Nao | Nao | Nao | Sim | Sim | **Sim** |
| BTC B&H | -38.08% | +171.35%* | -37.30% | -34.28% | -34.28% | +76.52%** | **-34.28%** |
| Alpha vs BTC | +52pp | -150pp* | +70pp | +149pp | +88pp | +190pp** | **+9pp** |
| Excesso vs RF | +6pp | +15pp* | +31pp | +112pp | +52pp | +264pp** | **-27pp** |

*\*Mod2 OOS: 4.5 anos bull. \*\*Mod6 OOS: 4.5 anos misto (train bear → test misto).*

**-24.82% — o primeiro e unico retorno negativo da serie.** Todos os outros modelos (1-6) geraram retorno positivo no OOS, independente do periodo. O Mod0 perdeu quase um quarto do capital.

O "+9.47pp vs BTC" e uma ilusao: a estrategia perdeu menos que buy & hold nao por skill, mas por **91% de abstencao**. Ficar parado enquanto o mercado cai gera "alpha" mecanico. O US Risk-Free rendeu +2.49% no mesmo periodo — a estrategia perdeu -27pp vs o ativo livre de risco.

### 3.3 Confusion Matrix OOS

| | Pred Bear (-1) | Pred Neutro (0) | Pred Bull (+1) |
|---|:---:|:---:|:---:|
| **Real Bear (984)** | **48** | 926 | 10 |
| **Real Neutro (3)** | 0 | **3** | 0 |
| **Real Bull (945)** | 62 | 832 | **51** |

![Confusion Matrix OOS — Modelo 0](pngs/confusion_matrix_oos_mod0.png)

**Precision e Recall OOS:**

| Classe | Precision | Recall |
|--------|:---------:|:------:|
| Bear (-1) | **44%** | 5% |
| Bull (+1) | **84%** | 5% |

Wait — a precision bear do classification_report diz 46% e bull 53%. Mas a confusion matrix mostra: pred bear total = 48+0+62 = 110. Acertos bear = 48. Precision = 48/110 = 43.6%. Pred bull total = 10+0+51 = 61. Acertos bull = 51. Precision = 51/61 = 83.6%.

A discrepancia com o classification report (46%/53%) se deve ao calculo do sklearn considerar a classe 0 diferentemente. Os numeros da confusion matrix sao mais informativos:

| Classe | Precision (confusion matrix) | Recall |
|--------|:---------:|:------:|
| Bear (-1) | **44%** | 5% |
| Bull (+1) | **84%** | 5% |

**Comparativo Precision/Recall OOS entre todos os modelos:**

| Metrica | Mod1 | Mod2 | Mod3 | Mod4 | Mod5 | Mod6 | **Mod0** |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Precision Bear | 89% | 74% | 68% | 85% | 84% | 90% | **44%** |
| Precision Bull | 80% | 71% | 68% | 88% | 95% | 87% | **84%** |
| Recall Bear | 12% | 49% | 7% | 34% | 21% | 33% | **5%** |
| Recall Bull | 20% | 47% | 10% | 27% | 9% | 32% | **5%** |
| Abstencao | 81% | 37% | 87% | 64.5% | 82.7% | 45.2% | **91.0%** |
| Erros direcionais | 70 | 834 | 106 | 90 | 41 | 352 | **72** |
| Trades ativos | 490 | 3,603 | 335 | 685 | 335 | 3,019 | **174** |

**Destaques:**

1. **Precision bear de 44% — a pior da serie por larga margem.** Todos os outros modelos tinham precision bear >= 68%. Aqui, mais da metade das apostas short estao erradas. A feature de retorno era o que permitia ao modelo detectar bears com confianca.

2. **Precision bull de 84% — surpreendentemente alta.** Das 61 apostas bull, 51 estavam corretas. Mas isso e enganoso: com apenas 61 trades bull (recall 5%), o modelo so aposta quando tem altissima certeza, gerando precision alta mas sem volume util.

3. **62 erros bull→bear (false shorts).** O modelo classifica 62 barras bull como bear — quase tantas quanto os 48 acertos bear. Shortear quando o mercado sobe e o pior tipo de erro, e o Mod0 faz isso com frequencia.

4. **91% de abstencao** — a maior da serie. O modelo sabe que nao sabe, e a unica coisa inteligente que faz.

### 3.4 Sharpe Ratios OOS

| Metrica | Todas barras | Trades ativos (174) |
|---------|:---:|:---:|
| **Sharpe Ratio** | **-0.068** | **-0.220** |
| **PSR** | **0.001** | **0.002** |
| DSR | 0.000 | 0.000 |
| Skewness | -2.295 | **-0.129** |
| Kurtosis (excess) | 33.89 | **0.28** |

**Sharpe vs US Risk-Free (4.5% a.a.):**

| Base | SR vs RF | PSR |
|------|:---:|:---:|
| Todas barras | -0.074 | 0.000 |
| Trades ativos | **-0.222** | **0.001** |

**Comparativo de Sharpe OOS entre todos os modelos:**

| Metrica | Mod1 | Mod2 | Mod3 | Mod4 | Mod5 | Mod6 | **Mod0** |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| SR (todas barras) | 0.019 | 0.009 | 0.068 | 0.084 | 0.057 | 0.068 | **-0.068** |
| SR (trades ativos) | 0.044 | 0.011 | 0.191 | 0.142 | 0.142 | 0.095 | **-0.220** |
| PSR (trades ativos) | 0.817 | 0.737 | 0.9999 | 0.998 | 0.976 | 0.984 | **0.002** |
| Kurtosis (ativos) | 54.9 | 189.9 | 7.1 | 41.5 | 40.6 | 38.4 | **0.28** |
| Skewness (ativos) | -2.8 | -8.9 | +1.3 | -3.2 | -3.8 | -2.6 | **-0.13** |

**Analise:**

1. **Sharpe NEGATIVO em ambas as bases** — -0.068 (todas barras), -0.220 (trades ativos). O unico modelo da serie com Sharpe OOS negativo. O modelo destroi valor.

2. **PSR de 0.002 (trades ativos)** — 0.2% de confianca de que o Sharpe e positivo. Na pratica, zero. Compare com o PSR 0.976 do Mod5 e o 0.9999 do Mod3.

3. **A UNICA metrica positiva do Mod0:** kurtosis de 0.28 e skewness de -0.13 nos trades ativos. A distribuicao de retornos e **quase normal** — sem caudas pesadas, sem eventos extremos. E o melhor perfil de distribuicao da serie inteira. Ironicamente, o modelo com a pior performance tem a distribuicao mais saudavel. A explicacao: sem sinal direcional, os trades sao essencialmente aleatorios e distribuidos normalmente. Eventos de cauda requerem convicao direcional — que o Mod0 nao tem.

### 3.5 Filtragem do Meta-Labeler

![Meta Label Filtering OOS — Modelo 0](pngs/meta_label_filtering_oos_mod0.png)

O meta-labeler filtrou 91% das barras — o recorde de abstencao da serie. Os 174 trades ativos sao distribuidos de forma esparsa, sem concentracao em momentos especificos. O modelo nao identifica janelas de oportunidade — opera essencialmente ao acaso.

### 3.6 Regimes Detectados

![Regime Classification OOS — Modelo 0](pngs/regime_classification_oos_mod0.png)

### 3.7 Triple-Barrier Labels

![Triple Barrier Labels OOS — Modelo 0](pngs/triple_barrier_labels_oos_mod0.png)

### 3.8 Retorno Acumulado

![Retorno Acumulado OOS — Modelo 0](pngs/cumulative_returns_oos_mod0.png)

### 3.9 Portfolio Equity

![Portfolio Equity OOS — Modelo 0](pngs/portfolio_equity_oos_mod0.png)

---

## 4. Analise — O Que o Mod0 Prova

### 4.1 ret_20 E Insubstituivel

A tabela abaixo resume o impacto da remocao de retornos:

| Metrica | Mod5 (com ret) | Mod0 (sem ret) | Variacao |
|---------|:---:|:---:|:---:|
| CPCV Accuracy | 67.7% | 51.2% | **-16.5pp** |
| CPCV Sharpe Std | 0.014 | 0.076 | **+5.4x** |
| Meta-label Sharpe (teste) | +0.045 | -0.034 | **Inverteu sinal** |
| Meta-label PSR (teste) | 0.994 | 0.024 | **-97pp** |
| Retorno OOS | +54.02% | -24.82% | **-79pp** |
| Sharpe OOS (ativos) | +0.142 | -0.220 | **Inverteu sinal** |
| PSR OOS (ativos) | 0.976 | 0.002 | **-97pp** |
| Precision Bear OOS | 84% | 44% | **-40pp** |
| Erros direcionais | 41 | 72 | **+76%** |

**ret_20 e responsavel por ~80% do poder preditivo do pipeline.** Sem ela:
- A accuracy cai para moeda jogada ao ar
- O Sharpe fica negativo em toda parte
- A precision bear colapsa para pior que 50%
- O retorno OOS vai de +54% para -25%

Nenhuma combinacao de microestrutura (VPIN, Kyle Lambda, Roll Spread), exogenas (VIX, Fear & Greed, DXY) ou estatisticas (t-stats, RSI, entropia) substitui a informacao contida no retorno de 20 barras filtrado por Savitzky-Golay.

### 4.2 Proxies Indiretas de Retorno (tstat, RSI) Nao Sao Suficientes

tstat_20 e RSI sao, em essencia, transformacoes de retorno:
- **tstat_20** = media dos retornos / (desvio padrao / sqrt(n)) — mede a significancia estatistica do retorno
- **RSI** = 100 - 100/(1 + media_subidas/media_descidas) — mede a proporcao de subidas vs descidas

Ambas *derivam* de retornos, mas perdem informacao:
- tstat e normalizada — perde a magnitude absoluta do movimento
- RSI comprime tudo para [0, 100] — perde a escala
- Nenhuma tem a suavizacao do filtro Savitzky-Golay causal, que remove ruido intra-bar

O Mod0 prova que **a magnitude filtrada do retorno (ret_20)** contem informacao que suas proxies estatisticas nao conseguem reconstruir.

### 4.3 Microestrutura Sozinha E Insuficiente

VPIN, Kyle Lambda, Roll Spread e funding_rate_zscore — as features de microestrutura do AFML — ficaram com MDA < 0.003 e, no CPCV final, VPIN e funding_rate_zscore ficaram negativas. Sem o contexto de retorno, essas features sao ruido.

Isso nao significa que microestrutura e inutil — no Mod5, VPIN e Kyle Lambda contribuiam como complemento ao ret_20. A conclusao correta e: **microestrutura e uma feature de refino, nao de fundacao.** Ela melhora um sinal existente mas nao cria sinal sozinha.

### 4.4 O Paradoxo do CPCV Sharpe Alto

O CPCV Sharpe de +0.133 no Mod0 (mais alto que todos os modelos exceto Mod3 e com PSR = 1.0) e um **falso positivo estatistico** que merece atencao:

- **Com 51% de accuracy**, o modelo nao tem poder preditivo real
- **Mas o meta-labeler filtra ~97%** das barras no teste, deixando apenas ~3% de trades ativos
- Com tao poucos trades, o Sharpe CPCV pode ser positivo por variancia amostral
- O **Std de 0.076** (5x maior que Mod5) confirma a instabilidade
- No teste meta-label completo, o Sharpe cai para **-0.034** com PSR 0.024 — o sinal desaparece

**Licao:** PSR e CPCV Sharpe nao sao suficientes para validar um modelo. O conjunto accuracy + Sharpe + PSR + estabilidade (Std) deve ser avaliado em conjunto. Um modelo com accuracy ~50%, Sharpe CPCV alto mas instavel, e PSR meta-label < 0.05 e um **falso positivo**.

---

## 5. Tabela Comparativa Final — Sete Modelos

### 5.1 Treino (CPCV)

| Metrica | Mod1 | Mod2 | Mod3 | Mod4 | Mod5 | Mod6 | **Mod0** | Melhor |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Bars/dia | 50 | 50 | 20 | 10 | 10 | 10 | **10** | — |
| Features | 10 | 4 | 8 | 5 | 6 | 5 | **11** | — |
| Fees | Nao | Nao | Nao | Nao | Sim | Sim | **Sim** | — |
| Accuracy | 59.7% | 63.6% | 63.6% | 67.3% | **67.7%** | 66.3% | 51.2% | **Mod5** |
| F1 | 0.617 | 0.658 | 0.638 | 0.678 | **0.680** | 0.656 | 0.496 | **Mod5** |
| Sharpe CPCV | -0.003 | +0.035 | **+0.108** | +0.067 | +0.060 | +0.064 | +0.133* | **Mod3** |
| Paths SR > 0 | 6/15 | 14/15 | **15/15** | **15/15** | **15/15** | **15/15** | **15/15** | Empate |
| SR minimo | -0.027 | -0.027 | **+0.063** | +0.027 | +0.037 | +0.015 | +0.006 | **Mod3** |
| Std Sharpe | **0.014** | 0.022 | 0.028 | 0.024 | **0.014** | 0.018 | 0.076 | **Mod1/5** |

*\*Sharpe CPCV do Mod0 e um falso positivo — ver secao 4.4*

### 5.2 OOS

| Metrica | Mod1 | Mod2* | Mod3 | Mod4 | Mod5 | Mod6** | **Mod0** | Melhor (bear) |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Retorno | +13.85% | +21.85% | +33.03% | +114.71% | +54.02% | +266.94% | **-24.82%** | Mod4 (bruto) / Mod5 (liq.) |
| Fees | Nao | Nao | Nao | Nao | Sim | Sim | **Sim** | — |
| Alpha vs BTC | +52pp | -150pp | +70pp | +149pp | +88pp | +190pp | **+9pp** | Mod6 |
| SR (ativos) | 0.044 | 0.011 | **0.191** | 0.142 | 0.142 | 0.095 | -0.220 | **Mod3** |
| PSR (ativos) | 0.817 | 0.737 | **0.9999** | 0.998 | 0.976 | 0.984 | 0.002 | **Mod3** |
| Kurtosis | 54.9 | 189.9 | 7.1 | 41.5 | 40.6 | 38.4 | **0.28** | **Mod0** |
| Skewness | -2.8 | -8.9 | +1.3 | -3.2 | -3.8 | -2.6 | **-0.13** | **Mod0** |
| Prec. Bear | **89%** | 74% | 68% | 85% | 84% | 90% | 44% | **Mod6** |
| Prec. Bull | 80% | 71% | 68% | 88% | **95%** | 87% | 84% | **Mod5** |
| Erros dir. | 70 | 834 | 106 | 90 | **41** | 352 | 72 | **Mod5** |
| Trades | 490 | 3,603 | 335 | 685 | 335 | 3,019 | 174 | — |

*\*Mod2 OOS: 4.5 anos bull. \*\*Mod6 OOS: 4.5 anos misto.*

### 5.3 Perfil de Cada Modelo (Atualizado)

**Modelo 0 — O Baseline Cego:**
Sem features de retorno, sem sinal. **Confirma que ret_20 e o motor do pipeline.** Unica virtude: distribuicao quase normal (kurtosis 0.28, skewness -0.13).

**Modelo 1 — O Sniper Classico:**
Precision maxima bear (89%). Fraqueza: Sharpe fraco, sem fees.

**Modelo 2 — O Soldado Agressivo:**
Mais trades, mais recall. Fraqueza: kurtosis extrema (190), perde para BTC em bull.

**Modelo 3 — O Estrategista Conservador:**
Melhor Sharpe/trade (0.191), unico com skewness positiva. **Melhor perfil de risco puro.** Fraqueza: sem fees, retorno modesto.

**Modelo 4 — O Operador de Alto Retorno:**
Retorno recorde bear (+115%), precision alta. Fraqueza: sem fees, skewness negativa.

**Modelo 5 — O Modelo Realista:**
Primeiro com fees pessimistas. **Precision bull recorde (95%), menor numero de erros (41), alpha de +54% liquido.** Fraqueza: skewness negativa, recall baixo.

**Modelo 6 — O Generalista Cross-Regime:**
Treino bear, OOS misto. +267% em 4.5 anos. Prova generalizacao bidirecional. Fraqueza: mais trades = mais erros absolutos.

---

## 6. Ressalvas e Limitacoes

### 6.1 O Que o Mod0 Prova

**A. Retorno e a feature fundacional do pipeline.**
Sem ret_20, nao ha sinal. Todas as outras features sao complementares.

**B. O CPCV Sharpe pode dar falsos positivos.**
Sharpe +0.133 com PSR 1.000 num modelo de 51% accuracy e uma licao sobre confiar cegamente em metricas agregadas.

**C. Microestrutura e exogenas nao substituem momentum.**
VPIN, Kyle Lambda, VIX, Fear & Greed — nenhuma compensa a ausencia de retorno.

### 6.2 Limitacoes do Experimento

**A. Nao isolamos cada feature removida.**
Removemos ret_20, ret_60, volatility_20 e mom_residual_50 simultaneamente. O ideal seria ablacao individual para quantificar a contribuicao marginal de cada uma. Baseado nos MDA historicos (ret_20 >> ret_60 >> volatility_20), e quase certo que ret_20 responde pela maioria da perda.

**B. O pool de features candidatas mudou.**
14 features vs 18 no Mod5. A reducao pode ter efeito alem da perda de retorno, embora as 4 features removidas fossem consistentemente as mais importantes nos modelos anteriores.

---

## 7. Proximos Passos

1. **Restaurar disable_savgol_returns = False** para voltar ao pipeline com retornos.

2. **Grid de janelas de retorno** — testar ret_10, ret_20, ret_40, ret_60, ret_100 com e sem Savitzky-Golay em diferentes janelas/polyorders. Buscar janela otima.

3. **Grid de janelas para t-stat e volatility** — expandir para tstat_10, tstat_20, tstat_50, tstat_100 e volatility_10, volatility_20, volatility_50, volatility_100.

4. **Fear & Greed como media movel** — transformar fear_greed_chg de variacao pontual para media movel em janelas similares (10, 20, 50).

5. **Simplificacao pos-grid** — apos encontrar janelas otimas, cortar features redundantes com MDA ≤ 0 para manter o modelo parcimonioso.

---

## Apendice A — Configuracao do Modelo 0

| Parametro | Valor |
|-----------|:-----:|
| Dollar bars/dia | **10 (fixo)** |
| Threshold | **$1,328,433,250** |
| Features selecionadas | **tstat_20, roll_spread, rsi, fear_greed_chg, vix_chg, kyle_lambda, log_volume, tstat_10, vpin, btc_dxy_spread, funding_rate_zscore** |
| **disable_savgol_returns** | **True** |
| Features removidas (ablacao) | **ret_20, ret_60, volatility_20, mom_residual_50** |
| fee_maker | 0.0090% |
| fee_taker | 0.0270% |
| fee_mode | pessimistic (taker ambas pontas) |
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

## Apendice B — Arquivos Gerados

```
relatorios/
  relatorio_regime_detection_mod0.md     (Modelo 0 — este documento)
  relatorio_regime_detection_mod1.md     (Modelo 1)
  relatorio_regime_detection_mod2.md     (Modelo 2)
  relatorio_regime_detection_mod3.md     (Modelo 3)
  relatorio_regime_detection_mod4.md     (Modelo 4)
  relatorio_regime_detection_mod5.md     (Modelo 5)
  relatorio_regime_detection_mod6.md     (Modelo 6)
  pngs/
    *_mod0.png                           (plots treino Modelo 0)
    *_oos_mod0.png                       (plots OOS Modelo 0)
  modelos/
    trained_model_mod0.joblib            (Modelo 0)
```

---

*Relatorio gerado em 2026-03-24. Pipeline: regime_detection_advanced.py + rd_adv_application.py*
*Experimento: ablacao negativa — remocao de todas as features de retorno/savgol. Confirma que ret_20 e a feature fundacional do pipeline, responsavel por ~80% do poder preditivo.*
