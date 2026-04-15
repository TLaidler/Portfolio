# Revisao Feynman & Marcos -- Modelo Hibrido (Mod7)

**Data:** 2026-03-26
**Modelo:** Hibrido (sg_velocity_51 como contexto + 8 features genuinas)
**Predecessores:** genuinas_vs_artefatos.md, feature_null_model.md, revisao_marcos.md
**Novos diagnosticos:** threshold_grid, return_concentration, return_distribution

---

## 1. O Que Mudou Nesta Rodada

Tres novas ferramentas de diagnostico foram adicionadas ao pipeline:

1. **Threshold Grid** -- varre LIMITE_DECISORIO de 0.50 a 0.60 e mede DSR, SR, N trades,
   skewness, retorno acumulado e PSR em cada ponto
2. **Return Concentration** -- curva de Lorenz dos retornos + top-20 trades por magnitude
3. **Return Distribution** -- histograma de retornos (todos vs ativos) com overlay gaussiano

Esses diagnosticos respondem a perguntas que estavam abertas desde a revisao_marcos.md.

---

## 2. Numeros do Modelo Atual

### 2.1 Treino (CPCV, 15 paths)

| Metrica | Valor |
|---------|-------|
| Features selecionadas | 9 (sg_velocity_51 dominante, MDA=0.033) |
| Accuracy | 52.5% +/- 1.6% |
| F1 | 53.2% +/- 1.2% |
| Sharpe | 0.121 +/- 0.060 |
| PSR / DSR (CPCV OOS) | 1.000 / 1.000 |
| 15/15 paths positivas | Sim (min=0.051, max=0.293) |

### 2.2 Meta-Label (Teste 20%, 5117 barras)

| Metrica | Threshold 0.50 | Threshold 0.55 | Threshold 0.60 |
|---------|---------------|----------------|----------------|
| SR | 0.070 | 0.028 | 0.018 |
| DSR | **0.989** | 0.466 | 0.202 |
| PSR | 1.000 | 0.977 | 0.893 |
| N trades ativos | 1744 (34%) | 613 (12%) | 28 (0.5%) |
| Skewness | -2.69 | -0.56 | **+1.52** |
| Retorno acumulado | +111.7% | +22.9% | +1.8% |

### 2.3 Application OOS (Ago/2025 -- Mar/2026, 180 dias, bear market)

| Metrica | Valor |
|---------|-------|
| Dollar Bars | 5104 (rotuladas: 2325) |
| Trades ativos | 871 (37.5%) |
| Precisao sell / buy | 52% / 60% |
| Recall sell / buy | 25% / 17% |
| SR (todas barras) | 0.069 |
| SR (trades ativos) | 0.119 |
| PSR / DSR (all) | 1.000 / 0.987 |
| Skewness / Kurtosis (all) | +11.16 / 312.3 |
| Retorno estrategia | **+120.47%** |
| BTC Buy & Hold | -38.66% |
| US Risk-Free | +2.20% |

---

## 3. Analise dos Novos Diagnosticos

### 3.1 Threshold Grid -- A Curva de Decisao

![Threshold Grid](pngs/adv_threshold_grid.png)

**Feynman:**

> Este grafico e a ferramenta mais importante que voces construiram ate agora.
> Ele revela a *anatomia* do meta-label. Vamos ler os 6 paineis:
>
> **DSR (painel 1):** Cai monotonicamente de 0.989 (th=0.50) para 0.004 (th=0.57),
> depois sobe para 0.20 (th=0.60). A queda e esperada -- menos trades = menos
> evidencia estatistica = DSR menor. Mas a *recuperacao* em 0.60 e curiosa.
> Com apenas 28 trades, o DSR sobe de 0.004 para 0.20. Isso significa que os
> ultimos 28 trades que sobrevivem ao threshold mais alto sao
> *qualitativamente diferentes* dos 184 que sobrevivem a 0.57.
>
> **Skewness (painel 4):** Aqui esta a revelacao. A skewness inverte de negativa
> para **positiva** em th=0.60 (+1.52). Nos thresholds intermediarios (0.52-0.57),
> a skewness e negativa (-0.56 a -4.79). Isso significa:
>
> - th=0.50: muitos trades, caudas esquerdas (desastres ocasionais)
> - th=0.55: trades medianos, skewness quase neutra (-0.56)
> - th=0.60: poucos trades, **caudas direitas** (ganhos > perdas)
>
> A transicao de skewness negativa para positiva e a assinatura de um modelo
> que *finalmente separa sinal de ruido*. O problema: a 0.60, sobram 28 trades
> em 5117 barras (0.5%). E operacionalmente viavel? Depende do yield de staking.

**Marcos:**

> Tres observacoes tecnicas sobre o threshold grid:
>
> 1. **O "vale da morte" esta em 0.57.** SR=-0.008, DSR=0.004, retorno=-3.0%.
>    Com 184 trades, o modelo esta no pior ponto: trades demais para ter qualidade,
>    de menos para ter significancia. Este e o threshold que ninguem deve usar.
>
> 2. **A nao-monotonicidade em 0.60 e estatisticamente fragil.** 28 trades nao
>    sao suficientes para um teste robusto. O intervalo de confianca do SR com
>    N=28 e enorme: SR=0.018 +/- ~0.19 (1/sqrt(28)). Precisamos de pelo menos
>    100-200 trades para confiar nesse ponto.
>
> 3. **O threshold otimo aparente e 0.50.** DSR=0.989, SR=0.070, 1744 trades.
>    Mas a skewness de -2.69 e um alerta: os lucros sao frageis, dependentes
>    de nao ter "dias ruins." A precisao de 55-58% e incompativel com a meta
>    de 90% do operador.

### 3.2 Return Concentration -- Quem Gera o Retorno?

![Return Concentration](pngs/adv_return_concentration.png)

**Feynman:**

> A curva de concentracao responde a pergunta: "o retorno depende de poucos
> trades ou e distribuido?"
>
> - Top 5 trades: 3.7% do retorno absoluto
> - Top 10 trades: 5.2%
> - Top 50 trades: 12.7%
> - Top 402 trades: 50%
> - Top 884 trades: 80%
>
> Isso e **saudavel**. O retorno NAO depende de 5-10 trades sortudos. Precisamos
> de ~400 trades para atingir metade do retorno. Isso indica que o edge e
> *distribuido*, nao concentrado em eventos raros.
>
> O barplot dos top-20 mostra que o maior trade individual contribui ~1.1% e
> os maiores perdedores sao da mesma ordem (-5% a -7%). Os ganhos e perdas sao
> *simetricos em magnitude* mas os ganhos sao mais frequentes (1022 vs 722).
>
> Isso e uma boa noticia para a estrategia sniper: se filtrar para 90% de
> precisao, o retorno nao vai colapsar por perder 3 trades magicos. O edge
> esta na frequencia de acertos, nao na magnitude.

**Marcos:**

> A concentracao confirma que nao ha "fat finger dependency." O profit factor
> implicito e: 1022 gains / 722 losses = **1.42**. Win rate = 58.6%.
>
> Para uma estrategia de 90% de precisao, o exercicio e: se filtrarmos os
> 10% de trades mais confiaveis (~174 trades), qual seria o profit factor?
> A curva sugere que os primeiros ~400 trades ja carregam 50% do retorno,
> entao os melhores 174 provavelmente teriam PF > 2.0.
>
> O problema: nao sabemos se "meta_confidence alta" seleciona os trades com
> melhor retorno. Essa correlacao -- confianca do modelo vs qualidade do
> trade -- e o proximo teste necessario.

### 3.3 Return Distribution -- As Caudas Falam

![Return Distribution](pngs/adv_return_distribution.png)

**Feynman:**

> Dois histogramas, duas historias:
>
> **Esquerda (todos os retornos, incl. abstencoes=0):** Um pico gigante em
> zero (as ~3400 abstencoes) com caudas finas. Mean=0.000218, SR=0.070.
> A gaussiana (tracejada) nao se ajusta -- nao e normal. Skewness=-2.69
> vem das caudas esquerdas DENTRO dos trades ativos.
>
> **Direita (apenas trades ativos):** ISTO e o que importa. Mean=0.000687,
> Std=0.00531, Skew=-1.38, Kurt=31.18. A distribuicao e leptocurtica
> (caudas mais pesadas que a normal) com skewness negativa moderada.
>
> SR dos trades ativos: 0.1296. Anualizado (~20 bars/dia, 365 dias):
> SR_anual = 0.1296 * sqrt(20*365) = **11.1**
>
> Esse numero e absurdamente alto. Antes de celebrar, lembrem: a
> autocorrelacao do sinal (positions mudam raramente) infla o SR per-bar.
> O SR por *trade independente* (T9 do hypothesis_testing) e o numero real.

**Marcos:**

> A kurtosis de 31.18 nos trades ativos (115 considerando todas as barras)
> invalida qualquer teste parametrico baseado em normalidade. PSR e DSR
> assumem distribuicao t-student, que e mais generosa com caudas, mas
> kurtosis >30 excede ate esse modelo.
>
> Recomendacao: implementar **block bootstrap** do Sharpe ratio:
> - Blocos de 50 barras (respeitando autocorrelacao)
> - 10.000 reamostragens
> - IC 95% do SR
>
> Sem isso, o DSR de 0.987 nao e confiavel.

---

## 4. O Modelo Visto Pela Otica OOS

### 4.1 Equity Curve (Treino)

![Portfolio Equity - Treino](pngs/adv_portfolio_equity.png)

A curva de equity no teste (20% holdout, ~dez/2024 a ago/2025) mostra:
- Estrategia: +197% vs BTC B&H: -27%
- Max drawdown: 12.5%
- Crescimento concentrado em dois periodos de alta (jan-fev e jun-jul 2025)
- Periodos longos de flatness (abstinencia operando)

### 4.2 Cumulative Returns (Treino)

![Cumulative Returns - Treino](pngs/adv_cumulative_returns.png)

Retorno acumulado aritmetico mostra divergencia crescente entre estrategia e benchmark
a partir da barra ~2000. PSR=1.000, DSR=0.989.

### 4.3 Confusion Matrix (CPCV Agregado)

![Confusion Matrix - CPCV](pngs/adv_confusion_matrix.png)

O CPCV agregado (sem meta-label) mostra:
- Pred -1: 6712 corretos / 5570 errados (precision **55%**)
- Pred +1: 6834 corretos / 5545 errados (precision **55%**)
- Pred 0: 5 corretos / 915 errados

O modelo primario e essencialmente um classificador de 55% de precisao em ambas
direcoes. O meta-label filtra para ~58% de precisao com recall ~20%.

### 4.4 Application OOS -- Bear Market

![Portfolio Equity - Application](pngs/app_portfolio_equity.png)

O resultado headline: **+120.47% num bear market de -38.66%**. A curva mostra:
- Estrategia acumula ganhos graduais ate dez/2025
- Dois saltos significativos em jan/2026 e mar/2026
- BTC cai de ~$120k para ~$65k no periodo
- US Risk-Free (4% a.a.) e uma linha quase flat

### 4.5 Meta-Label Filtering (Application)

![Meta-Label Filtering](pngs/app_meta_label_filtering.png)

Dos 2325 trades primarios, o meta-label manteve 871 (37.5%) e filtrou 1454 (62.5%).
Os pontos azuis (mantidos) e vermelhos (filtrados) se distribuem ao longo de toda a
serie temporal, sem concentracao em periodos especificos.

### 4.6 Regime Classification (Application)

![Regime Classification](pngs/app_regime_classification.png)

**Painel superior (predicao final, com meta-label):** Predominancia amarela (neutro/abstencao)
com trechos curtos de verde (bull) e vermelho (bear). O modelo opera em rajadas curtas.

**Painel inferior (predicao primaria, sem filtro):** Alternancia rapida entre bull e bear
ao longo de toda a serie. O meta-label esta corretamente filtrando a maioria dessas
previsoes primarias ruidosas.

### 4.7 Confusion Matrix (Application OOS)

![Confusion Matrix - Application](pngs/app_confusion_matrix.png)

| | Pred -1 | Pred 0 | Pred +1 |
|---|---------|--------|---------|
| **Real -1** (1135) | **283** | 723 | 129 |
| **Real 0** (8) | 6 | 1 | 1 |
| **Real +1** (1182) | 256 | 730 | **196** |

- Precision sell: 283/(283+6+256) = **51.9%**
- Precision buy: 196/(129+1+196) = **60.1%**
- Win rate direcional: (283+196)/(283+196+129+256) = **55.4%**

---

## 5. Feynman: "De Onde Vem o Retorno de +120%?"

> Vamos fazer a conta de padeiro. O modelo opera 871 vezes em 2325 barras.
> Win rate direcional: 55.4%. Fee round-trip: ~0.054%.
>
> Se cada trade ganha em media +X% quando acerta e perde -X% quando erra
> (assumindo simetria), o retorno esperado por trade e:
>
> E[ret] = 0.554 * X - 0.446 * X - 0.054% = 0.108 * X - 0.054%
>
> Para E[ret] > 0, precisamos X > 0.5%. Com dollar bars a 20/dia, cada barra
> cobre ~1.2 horas. Volatilidade tipica de BTC em 1.2h: ~0.5-1.0%.
>
> Entao o edge e real mas apertado: ~0.054% * (0.108/0.054 - 1) = ~0.054% por
> trade em excesso. Em 871 trades: 871 * 0.054% = ~47% retorno esperado.
>
> Mas o retorno observado e +120%. A diferenca (~73pp) vem de dois efeitos:
>
> 1. **Assimetria de timing:** O modelo acerta mais em barras de alta volatilidade
>    (retornos maiores quando acerta, menores quando erra). Isso e consistente
>    com sg_velocity_51 como "termometro de regime."
>
> 2. **Composicao nao-linear:** Retornos compostos favorecem quem evita perdas
>    grandes. Ficar flat durante -38% de BTC e equivalente a "ganhar" 38%
>    relativo. Se o modelo evitou os piores 10 dias de BTC, isso sozinho
>    explicaria grande parte do excesso.
>
> **Conclusao:** O retorno de +120% e uma combinacao de edge direcional fraco
> (~55% win rate) + evitamento de drawdowns + composicao favoravel. Nao e
> alpha puro no sentido de "previ o futuro." E alpha de *disciplina*: o
> modelo sabe quando NAO operar.

---

## 6. Marcos: "O Veredito Tecnico"

> ### 6.1 O Que Funciona
>
> 1. **CPCV e robusto:** 15/15 paths positivas, DSR=1.000. O modelo primario
>    tem edge genuino (fraco, SR~0.12, mas consistente).
>
> 2. **Meta-label filtra corretamente:** A confusion matrix OOS mostra que
>    o meta-label mantem ~37% dos trades e descarta os mais ruidosos.
>    O SR sobe de ~0.05 (primario) para 0.12 (filtrado).
>
> 3. **Concentracao saudavel:** Retorno distribuido em ~400+ trades, nao
>    dependente de outliers. Profit factor implicito de 1.42.
>
> 4. **Feature importance estavel:** sg_velocity_51 domina com MDA=0.033
>    (3.8x a segunda). O modelo e interpretavel: "velocidade de preco
>    suavizada como termometro, t-stats como sinal direcional."
>
> ### 6.2 O Que Nao Funciona
>
> 1. **Precisao de 55% esta longe dos 90% desejados.** O threshold grid
>    mostra que a precisao nao sobe significativamente com thresholds
>    maiores -- as probabilidades do meta-label nao sao suficientemente
>    bimodais. Para atingir 90%, seria necessario um sinal 3-5x mais forte.
>
> 2. **Kurtosis invalida PSR/DSR.** Com kurtosis >100 (OOS), os testes
>    parametricos nao sao confiaveis. Block bootstrap e necessario.
>
> 3. **DSR degrada de 1.000 (CPCV) para 0.987 (OOS).** Ainda alto,
>    mas a direcao de degradacao indica possivel overfitting residual.
>
> 4. **Skewness negativa no threshold default (0.50).** Lucros frageis,
>    dependentes de nao ter eventos extremos negativos. So inverte para
>    positiva em th=0.60, com 28 trades (insuficiente estatisticamente).
>
> ### 6.3 O "Pecado Cardinal" que Persiste
>
> **O modelo nao distingue "confianca alta" de "confianca media."**
>
> Na confusion matrix do teste:
> - Pred -1: 843 trades, precisao 55%
> - Pred +1: 901 trades, precisao 58%
> - Pred 0: 3373 abstencoes
>
> Se o meta-label conseguisse *dentro dos trades ativos* separar um subconjunto
> com >80% de precisao, o problema estaria resolvido. Mas nao consegue, porque
> as probabilidades meta-label sao quase uniformes entre 0.50 e 0.55.
>
> **Raiz do problema:** sg_velocity_51 e a feature dominante, mas e um artefato
> univariado. Produz splits de arvore informativos para accuracy, mas nao
> gera *certeza diferenciada*. O RF diz "55% bear" ou "55% bull" -- nunca
> "90% bear."

---

## 7. Feynman: "O Que Falta Para o Modelo Sniper?"

> Thiago quer 90% de precisao com 20% de recall. O modelo atual entrega
> 55% de precisao com 20% de recall. Onde estao os 35pp faltantes?
>
> Tres caminhos possiveis:
>
> ### Caminho 1: Feature mais forte
>
> Com sg_velocity_51 (MDA=0.033), o RF mal diferencia bull de bear.
> Nos modelos anteriores (Mod1/Mod5), ret_20 (MDA=0.177) permitia 90%+
> de precisao. A diferenca e **5x em forca de sinal**.
>
> Para atingir 90% de precisao com features genuinas, seria necessario
> encontrar uma feature com MDA ~0.10+. Nenhuma feature individual
> testada no T8 chega perto disso.
>
> Opcao: **combinacoes nao-lineares**. tstat_50 * volatility_20
> (momentum ajustado por regime) poderia gerar splits mais informativos.
> Mas e uma hipotese nao testada.
>
> ### Caminho 2: Readmitir artefatos controlados
>
> Ret_20 sobre SavGol e um artefato (T8 provou). Mas e um artefato
> *util* porque produz probabilidades bimodais no RF. A autocorrelacao
> do filtro funciona como *amplificador de sinal* -- transforma o
> momentum fraco de tstat_50 em algo que o meta-label consegue calibrar.
>
> Implicacao: readmitir ret_20 como feature, documentar que e artefato
> do filtro, e usar o meta-label com threshold 0.60 para filtrar.
> Mod5 ja mostrou que isso entrega precision_bull=95%, recall=9%.
>
> O risco: se o BTC entrar num regime onde a autocorrelacao do filtro
> e *anticorrelacionada* com retornos futuros (flash crash sem build-up),
> o modelo pode errar com alta confianca.
>
> ### Caminho 3: Abordagem probabilistica
>
> Substituir o RF por um modelo que produza probabilidades calibradas
> (e.g., Logistic Regression com regularizacao, ou RF com calibracao
> isotonica/Platt). O problema do RF atual e que leaf nodes com 50+
> amostras tem distribuicao ~50/50 por construcao (depth=6 nao e
> profundo o suficiente para separar classes com features fracas).
>
> Com calibracao, as probabilidades poderiam refletir a incerteza real
> e permitir thresholds mais efetivos.

---

## 8. Marcos: "Recomendacoes Formais (Priorizadas)"

> ### Prioridade 1: Diagnostico imediato
>
> 1. **Implementar block bootstrap do SR** -- blocos de 50 barras, 10k
>    amostras, reportar IC 95%. Sem isso, DSR de 0.987 e numero sem
>    contexto.
>
> 2. **Calcular correlacao: meta_confidence vs retorno do trade.** Se
>    rho > 0.15, o meta-label tem informacao sobre qualidade. Se rho ~ 0,
>    a confianca e ruidosa e o threshold nao pode melhorar a precisao.
>
> ### Prioridade 2: Melhoria do meta-label
>
> 3. **Calibracao de probabilidade** (isotonica ou Platt scaling) sobre o
>    RF primario. Transformar probabilidades de "55% em tudo" para uma
>    distribuicao mais dispersa.
>
> 4. **Testar Logistic Regression como meta-model.** LR produz probabilidades
>    naturalmente calibradas e pode ser mais efetivo como filtro do que
>    um segundo RF.
>
> ### Prioridade 3: Teste de hipotese pendente
>
> 5. **T8 para o modelo completo** (nao feature individual). Rodar o
>    pipeline inteiro (dollar bars + features + RF + meta-label) em 500
>    random walks. Se o SR do modelo completo em BTC real superar P95 das
>    simulacoes, o alpha e genuino -- mesmo que features individuais
>    sejam artefatos.
>
> 6. **Comparar modelo vs sign(savgol_velocity) puro.** Se a regra simples
>    tem SR similar, o RF e o meta-label sao complexidade desnecessaria.
>
> ### Prioridade 4: Estrategia operacional
>
> 7. **Formular o "yield combinado":**
>    ```
>    Y = staking_yield * (1 - f_active) + SR_active * f_active - fees * f_active
>    ```
>    Onde f_active = fracao do tempo operando. Otimizar LIMITE_DECISORIO
>    para maximizar Y, nao SR isolado.
>
> 8. **Expandir threshold grid ate 0.70-0.80** com passos de 0.01.
>    A nao-monotonicidade em 0.60 sugere que pode haver um "sweet spot"
>    entre 0.60 e 0.70 com mais trades e skewness ainda positiva.

---

## 9. Resumo Executivo

| Aspecto | Status | Nota |
|---------|--------|------|
| CPCV robusto | OK | 15/15 paths positivas, DSR=1.000 |
| Meta-label funcional | PARCIAL | Filtra corretamente, mas precisao ~55% (alvo: 90%) |
| Concentracao de retorno | OK | Distribuido em 400+ trades, PF=1.42 |
| Distribuicao de retorno | ALERTA | Kurtosis >100 invalida testes parametricos |
| OOS bear market | BOM | +120% vs BTC -39%, mas alpha e de abstinencia |
| Threshold optimization | INCOMPLETO | Grid ate 0.60; precisao de 90% nao atingivel |
| Precisao sniper (90%) | NAO ATINGIDO | Gap de 35pp; requer features mais fortes ou artefato readmitido |

### A Frase Final

**Feynman:**
> O modelo sabe quando NAO operar -- isso vale dinheiro. Mas quando decide
> operar, acerta 55%. Para um sniper, 55% e uma arma descalibrada. O proximo
> passo e calibrar a arma (Platt scaling, features mais fortes) ou aceitar
> que este modelo e um *detector de risco*, nao um *gerador de alpha*.

**Marcos:**
> A ciencia esta correta. A engenharia precisa de trabalho. DSR=0.987 OOS
> e raro e valioso -- mas com kurtosis 312, precisa de validacao nao-parametrica
> antes de alocar capital real.

---

## Plots de Referencia

### Treino (save_point_advanced)

![Feature Importance MDA](pngs/adv_feature_importance_mda.png)

![CPCV Sharpe Distribution](pngs/adv_cpcv_sharpe_distribution.png)

![Confusion Matrix CPCV](pngs/adv_confusion_matrix.png)

![Cumulative Returns Treino](pngs/adv_cumulative_returns.png)

![Portfolio Equity Treino](pngs/adv_portfolio_equity.png)

### Application OOS (bear market)

![Portfolio Equity OOS](pngs/app_portfolio_equity.png)

![Cumulative Returns OOS](pngs/app_cumulative_returns.png)

![Confusion Matrix OOS](pngs/app_confusion_matrix.png)

![Meta-Label Filtering](pngs/app_meta_label_filtering.png)

![Regime Classification](pngs/app_regime_classification.png)

### Novos Diagnosticos

![Threshold Grid](pngs/adv_threshold_grid.png)

![Return Concentration](pngs/adv_return_concentration.png)

![Return Distribution](pngs/adv_return_distribution.png)

---

*Relatorio gerado em 2026-03-26. Predecessores: genuinas_vs_artefatos.md,
feature_null_model.md, revisao_marcos.md.*
