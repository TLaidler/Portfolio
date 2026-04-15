# Revisão de Pares: Pipeline de Detecção de Regimes BTC/USDT

**Revisor:** Marcos López de Prado
**Afiliação:** Cornell University, Abu Dhabi Investment Authority (former)
**Data:** 2026-03-25
**Manuscrito:** "Regime Detection via Meta-Labeled Momentum on Dollar Bars"
**Decisão:** Major Revision Required

---

## 1. Sumário Executivo

> *"Most backtests are wrong, and most discoveries are false. The question is whether this one has earned the right to be different."*

Este pipeline é **o melhor trabalho amador que já vi**, e uso "amador" sem intenção pejorativa — no sentido de que foi construído fora de um laboratório de pesquisa institucional. O autor claramente leu meus livros (*AFML*, *MLAM*) e implementou a maioria dos componentes corretamente: dollar bars, triple-barrier, CPCV com purging e embargo, MDA feature selection, meta-labeling, PSR e DSR.

No entanto, a implementação contém **falhas estruturais que comprometem a validade das conclusões**. O pipeline não é charlatanismo matemático — há rigor genuíno — mas tampouco é um avanço científico publicável no estado atual. É um **rascunho promissor com sete pecados que precisam ser corrigidos**.

**O resultado mais revelador de toda a série de 7 modelos é este:** de 22 features oferecidas ao modelo, incluindo microestrutura (VPIN, Kyle Lambda, Roll Spread, Lempel-Ziv), sentimento (Fear & Greed em 4 variantes), funding rate, VIX, DXY, tstat, RSI, FFD, e momentum residual — apenas **momentum SavGol (ret_20) carrega ~90% do poder preditivo**. O modelo reduziu-se, com honestidade brutal, a uma estratégia de momentum disfarçada de ML.

**Nota provisória: 6.5/10.** Acima da média de submissões que recebo, mas insuficiente para publicação sem correções.

---

## 2. Análise de Componentes

### 2.1 Dados — Dollar Bars ✅ (com ressalvas)

**O que foi feito corretamente:**
- Dollar bars em vez de barras de tempo. O autor demonstra compreensão do Teorema 2.1 (AFML): retornos de dollar bars se aproximam de IID, condição necessária para que estimadores estatísticos tenham distribuições conhecidas.
- Calibração do threshold nos primeiros 30 dias apenas (anti-leakage).
- Implementação vetorizada eficiente (cumsum + searchsorted).

**Ressalvas:**
- O threshold é a **mediana** do dollar volume diário dividida por bars_per_day. Mediana é robusta a outliers, mas o autor não testa se a escolha de `bars_per_day=20` é ótima. Os relatórios Mod1-Mod6 mostram que a espessura das barras (50, 20, 10 bars/dia) teve **impacto maior que a escolha de features**. Isso sugere que o sampling rate é um hiperparâmetro de primeira ordem sendo tratado como constante.
- **Não há teste de IID das barras resultantes.** O autor deveria rodar Runs test, Ljung-Box, ou BDS test nos retornos das dollar bars para confirmar que a promessa teórica se materializa na prática.

### 2.2 Features — Arquitetura extensível, resultado desolador ⚠️

**O que foi feito corretamente:**
- Arquitetura BaseFeature/MultiFeature permite extensão modular.
- SavGol CAUSAL (pos=window-1) em vez de filtros centrados — elimina look-ahead.
- Fear & Greed com lag 1 dia (anti-leakage).
- FFD implementado (d=0.4) para preservação de memória.
- Features exógenas diárias (VIX, DXY, Fear & Greed) corretamente computadas na escala diária antes do merge com dollar bars. Isso foi recentemente corrigido — os z-scores do Fear & Greed agora são calculados no DataFrame diário, não nas barras.

**Problemas:**
1. **A FFD feature (ffd_close) foi rejeitada pelo MDA.** Com MDA = -0.000102 no último modelo, a diferenciação fracionária não contribui. Isso é grave: ou o d=0.4 está mal calibrado (deveria usar o procedimento de busca do mínimo d que rejeita o teste ADF), ou a memória preservada pela FFD não é informativa para o modelo usado (Random Forest). A FFD é um componente teórico central do framework — sua rejeição empírica merece investigação, não silêncio.

2. **Das 22 features, apenas 14 passaram o filtro MDA > 0, e destas, 12 têm MDA < 0.001.** O relatório de feature selection é impiedoso:

| Feature | MDA Mean | MDA Std | Razão Sinal/Ruído |
|---------|----------|---------|-------------------|
| ret_20 | 0.1774 | 0.0071 | **24.97** |
| ret_10 | 0.0083 | 0.0034 | 2.46 |
| ret_50 | 0.0022 | 0.0023 | 0.95 |
| fear_greed_zscore_5 | 0.0011 | 0.0012 | 0.93 |
| vix_chg | 0.0004 | 0.0009 | 0.45 |
| Todas as outras | < 0.0003 | > MDA | < 0.50 |

Apenas `ret_20` tem razão sinal/ruído > 2 de forma inequívoca. `ret_10` é marginalmente significativo. **Todas as outras features são indistinguíveis de ruído pelo critério MDA.** O modelo que usa 14 features está, na prática, usando 1-2 features reais e 12 features de ruído.

3. **O filtro de correlação a 0.85 removeu volatilities redundantes, o que é correto. Mas ret_20 e ret_10 são altamente correlacionados** (retornos SavGol em janelas sobrepostas). O modelo está usando duas features que são quase colineares e mais 12 features de ruído. Isso é a definição de *curse of dimensionality*.

### 2.3 Labeling — Triple-Barrier ✅

**Correto:**
- Triple-Barrier com volatilidade EWM dinâmica.
- Spans (t0, t1) armazenados e usados para purging no CPCV.
- Barreiras simétricas (pt=sl=2.0σ) — conservador e defensável.
- Holding period de 50 barras (~2.5 dias com 20 bars/dia).

**Menor ressalva:**
- A barreira vertical produz label=0 (neutro). Com apenas 140 neutros em 25.581 barras (0.55%), o modelo opera essencialmente como classificação binária. Isso é aceitável, mas o autor deveria documentar explicitamente que a barreira vertical quase nunca é atingida, o que implica que a volatilidade é alta o suficiente para que quase toda posição toque PT ou SL antes do timeout.

### 2.4 Validação — CPCV ✅ (com bug corrigido e problema residual)

**O que foi feito corretamente:**
- CPCV com C(6,2)=15 paths, não K-fold ingênuo.
- Purging baseado em spans (t0,t1) — amostras com overlap temporal são removidas do treino.
- Embargo pós-teste (1%).
- DSR para ajuste de múltiplos testes.

**Bug corrigido (crítico):**
O DSR estava implementado incorretamente — o benchmark SR* não era escalado por √V[SR̂]. Isso produzia DSR=0.0000 em TODOS os testes, tornando a métrica inútil. O bug foi corrigido e agora o DSR é informativo:
- CPCV OOS: DSR = 1.0000 ✅
- Meta-label teste: DSR = 0.9930 ✅
- Application OOS: DSR = 0.1260 ⚠️

**Problema residual:**
O DSR na application (0.1260) é catastroficamente baixo. Com 15 trials, há apenas ~13% de probabilidade de que o Sharpe observado OOS supere o esperado por acaso. **Isso não é estatisticamente significativo por nenhum critério convencional.** A divergência CPCV (DSR=1.0) vs. Application (DSR=0.13) é o sinal de alarme mais importante de todo o pipeline.

### 2.5 Meta-Labeling — Implementação correta, resultados extremos ⚠️

**O que foi feito corretamente:**
- Dois estágios: primário (direção) + meta (confiança).
- Meta-model treinado apenas no split temporal de treino (anti-leakage).
- Threshold configurável (LIMITE_DECISORIO = 0.6).

**Problemas:**
1. **O meta-label filtra >90% dos trades.** Na application, de 2.325 barras, apenas 191 são trades ativos (8.2%). No teste advanced, 94% de abstenção. Isso não é meta-labeling — é **recusa generalizada de operar**. O modelo não aprendeu quando apostar; aprendeu a não apostar. Isso até pode ser valioso para um trader, mas é um defeito para um modelo classificador. No nosso caso, consideraremos uma qualidade, mas é uma característica que merece atenção.

2. **Precision 94% com recall 8% é uma ilusão.** Se eu construo um modelo que diz "0" (não operar) em 99% dos casos e acerta a direção nos 1% restantes, terei precision altíssima e Sharpe positivo trivialmente — estou selecionando os casos mais óbvios. O meta-label deveria estar calibrado para recall ~ 30% para ter utilidade operacional.

3. **O Confusion Matrix conta a história real:**
   ```
   [[ 101 2415   17]    ← Bear: previu corretamente apenas 101/2533 (4%)
    [   2   16    0]    ← Neutro: irrelevante (N=18)
    [   9 2382  175]]   ← Bull: previu corretamente apenas 175/2566 (7%)
   ```
   O modelo classifica como neutro (linha central) **4.797 de 5.117 amostras**. Não é um classificador de regimes — é uma máquina de abstinência com respingos de acerto.

---

## 3. Os Sete Pecados

### Pecado 1: False Strategy Theorem — A teoria econômica está ausente

> *"A backtest is not a strategy. A strategy requires a theory of WHY."*

O pipeline não apresenta uma justificativa econômica para o ganho. A feature dominante é `ret_20` (retorno SavGol de 20 barras ≈ 1 dia). Isso é **momentum puro**: o ativo que subiu continua subindo. Momentum é um fator bem documentado (Jegadeesh & Titman, 1993; Asness et al., 2013), mas:

- Por que momentum funciona em dollar bars de BTC? Qual é o mecanismo? Herding? Fluxo institucional? Latência de informação?
- Por que 20 barras e não 5 ou 50? O grid search do benchmarking mostrou que ret_3 a ret_8 dominam OOS. O modelo escolheu ret_20. Esses resultados são contraditórios e não foram reconciliados. A explicação é o alto grau de overfitt para estes retornos no teste benchmark, de forma que o filtro savgol em janelas médias suprimiu ruido suficiente para o modelo generalizar bem. No entanto, faltou um trabalho mais detalhado na definição de barras/dia.

### Pecado 2: Overfitting silencioso via complexidade do modelo

Random Forest com 500 árvores, profundidade 6, e `min_samples_leaf=50` aplicado a um espaço de 14 features onde apenas 1-2 são informativas. Isso é **massivamente overparameterized**. O RF está ajustando ruído nas 12 features irrelevantes.

Evidência: CPCV dá accuracy 68.4% e Sharpe 0.064. Application dá accuracy 8% e Sharpe 0.027. **Degradação de 60 pontos percentuais em accuracy e 58% em Sharpe entre validação e application.** Isso é textbook overfitting — o modelo memoriza padrões espúrios no treino que não se repetem.

### Pecado 3: Viés de seleção não ajustado corretamente

O pipeline rodou **7 modelos** (Mod0-Mod6) com variações de features, espessura de barras, e períodos. O DSR usa `n_trials=15` (paths CPCV), mas ignora que **os 7 modelos são eles próprios trials**. Se ajustarmos para K=7×15=105 trials, o benchmark SR* aumenta substancialmente, e o DSR da application despencaria abaixo de 0.05.

O False Strategy Theorem (Bailey, Borwein, López de Prado, Zhu, 2014) é claro: com 105 trials e SR observado de 0.027 (application, todas barras), a probabilidade de ser falso positivo é >95%.

### Pecado 4: Distribuição de retornos patológica

Na application:
- **Skewness = -27.79** (todas barras) / **-8.36** (trades ativos)
- **Kurtosis (excess) = 1144.39** (todas barras) / **96.15** (trades ativos)

Kurtosis >1000 significa que a distribuição é dominada por eventos extremos. O Sharpe ratio é **matematicamente indefinido** quando os momentos superiores são desta magnitude — a variância é um estimador enviesado do risco real. O PSR usa skewness e kurtosis na correção, mas com kurtosis 1144, o próprio PSR perde validade assintótica.

**O retorno de +23.82% na application pode ser explicado por 1-2 eventos extremos.** Sem análise de concentração (fração do retorno vinda dos top-N trades), o resultado é anedótico.

### Pecado 5: Train/Test split temporal contamina a application

O modelo é treinado nos dados completos (36.802 barras, ~5 anos), depois testado na application (2.325 barras, ago/2025 - mar/2026). Mas o CPCV usa split 80/20 **dentro** dos dados de treino, onde o "teste" (20%) é temporalmente adjacente ao "treino" (80%).

O regime de ago/2025-mar/2026 (BTC -38%) pode ser estruturalmente diferente do regime de treino. A degradação DSR 1.0 → 0.13 confirma: **o modelo não generaliza**. O CPCV garante validade interna, mas não garante validade em regime shift.

### Pecado 6: Feature Selection insuficiente — MDA > 0 é critério frouxo

O critério `mda_mean > 0` aceita features com MDA = 0.000033 (btc_dxy_spread) e std = 0.000506. Isso é **14x mais ruído que sinal**. O critério anterior (`mean - std > 0`) era correto e foi revertido prematuramente.

Das 14 features selecionadas, sugiro a seguinte classificação:

| Categoria | Features | Evidência |
|-----------|----------|-----------|
| **Sinal real** | ret_20 | MDA/std = 25. Inequívoco. |
| **Sinal marginal** | ret_50 | MDA/std ≈ 1. Borderline. |
| **Ruído** | As outras 12 | MDA/std < 1. Indistinguíveis de zero. |

O modelo ganhou complexidade sem ganhar informação. As features de microestrutura (VPIN MDA=0.0001, Kyle MDA=0.0002) não contribuem de forma significativa. Isso pode refletir (a) que o Random Forest não é o modelo adequado para sinais não-lineares fracos, ou (b) que essas features genuinamente não carregam informação preditiva na escala temporal usada.

### Pecado 7: Ausência de um benchmark formal

O pipeline gera o modelo e a application, mas **nunca compara formalmente contra o benchmark naive no mesmo período com as mesmas taxas**. Os benchmarks existentes (relatório de robustez com sign_ret_20) foram rodados em períodos diferentes.

Para qualquer periódico sério, a Tabela 1 do paper deveria ser:

| Estratégia | Retorno | Sharpe (all) | DSR | Trades |
|------------|---------|-------------|-----|--------|
| Buy & Hold | -38.66% | — | — | 1 |
| sign_ret_20 (naive) | ??? | ??? | — | ~100% |
| ML Meta-Label (14 feats) | +23.82% | 0.027 | 0.13 | 8.2% |
| ML Meta-Label (2 feats) | +45.63% | 0.039 | 0.24 | 24.9% |

Sem a linha 3, não sei se o ML adiciona valor sobre o naive. E suspeito que não.

---

## 4. O Que Funciona — Porque Não Sou Apenas Destrutivo

1. **Dollar bars são corretos.** A maioria dos praticantes usa barras de tempo por preguiça. Aqui não.

2. **CPCV é correto.** O purging por spans (t0,t1) é a implementação que descrevi. O embargo funciona. Os 15 paths produzem uma distribuição, não um ponto.

3. **DSR corrigido é correto.** Depois da correção do bug de escala, o DSR agora discrimina: 1.0 no CPCV vs 0.13 na application. Isso é **informação real** — o modelo é internamente válido mas não generaliza.

4. **A série Mod0-Mod6 é ciência.** Ablation test (Mod0), inversão de dataset (Mod2), grid de espessura de barras, teste de fees (Mod5), generalização cross-regime (Mod6). Isso é metodologia, não alquimia.

5. **A honestidade do MDA.** O filtro eliminou 20 de 22 features no modelo com critério lower_ci > 0, e 8 de 22 com critério mean > 0. A maioria dos praticantes teria forçado features "teoricamente importantes" no modelo. Aqui, os dados decidiram — e o resultado (momentum domina) é incômodo mas honesto.

6. **Anti-leakage checklist explícita.** SavGol causal, lag 1 dia em features diárias, threshold calibrado em window separada, CPCV purge+embargo. A maioria dos pipelines que reviso tem pelo menos uma fonte de leakage oculta. Aqui não encontrei nenhuma.

---

## 5. Veredito Final

### Nota: 6.5 / 10

| Componente | Nota | Comentário |
|------------|------|-----------|
| Dados (Dollar Bars) | 8/10 | Correto. Falta teste IID formal. |
| Features | 5/10 | Arquitetura boa, resultado desolador. FFD inútil. |
| Labeling (Triple-Barrier) | 9/10 | Quase impecável. |
| Validação (CPCV + DSR) | 8/10 | Bug do DSR corrigido. Falta ajuste K total. |
| Meta-Labeling | 4/10 | Recall <10% não é operacional. |
| Performance OOS | 4/10 | DSR=0.13. Kurtosis=1144. Não significativo. |
| Rigor Metodológico | 8/10 | Série Mod0-6 é exemplar. |
| **Média Ponderada** | **6.5** | **Promissor mas não publicável.** |

### Recomendações de Correção (Ordenadas por Impacto)

1. **Restaurar critério MDA `mean - std > 0`.** O modelo com 2 features (ret_20 + ret_10) teve DSR=0.94 no teste e DSR=0.24 na application. O modelo com 14 features tem DSR=0.13 na application. **Mais features pioraram o resultado.** Occam's Razor aplica-se com força total.

2. **Comparação formal ML vs. naive momentum.** Rodar `sign(ret_20_sg)` no mesmo período da application, com mesmas fees. Se naive ≥ ML, o paper não tem razão de existir.

3. **Ajustar n_trials para total de modelos testados.** DSR com K=15 é otimista. O verdadeiro K inclui os 7 modelos e as variações de hiperparâmetros (grids de SavGol, polyorder, espessura de barras). Estimo K > 100.

4. **Calibrar meta-label para recall mínimo operacional.** O LIMITE_DECISORIO de 0.6 produz <10% de trades. Testar threshold=0.5, 0.45, 0.4 e reportar a curva precision-recall completa. Um fundo não pode ter uma estratégia que opera 8% do tempo. (Torne essa alteração uma escolha do usuário. Devemos manter em mente a possibilidade de uma estratégia que se aproveite do momentum apenas 8% das vezes).

5. **Análise de concentração do retorno.** Reportar: "X% do retorno vem dos top-5 trades." Se >80%, o resultado é anedótico e não replicável.

6. **Investigar por que FFD falha.** Se d=0.4 não é o mínimo d que rejeita ADF, calibrar corretamente. Se é, e ainda assim MDA é negativo, documentar como resultado negativo — isso tem valor científico.

7. **Substituir Random Forest por modelo mais simples para 2 features.** Se o sinal é ret_20, um threshold rule ou logistic regression tem a mesma capacidade com interpretabilidade total e zero risco de overfitting.

---

### Nota Final Pessoal

> *"The author has read my books. That alone puts this work in the top 10% of what I review. But reading is not understanding, and understanding is not executing. The pipeline has the bones of a correct implementation, but the flesh — the features, the model complexity, the meta-label calibration — needs surgery.*

> *The most important discovery of this research program is not the +23% return or the +45% return. It is the discovery that ret_20 — Savitzky-Golay smoothed momentum over ~1 day — is the ONLY feature that matters. Everything else is decoration. The author should have the courage to accept this finding and ask the real question: Why does 1-day momentum predict BTC regimes, and for how long will it continue?*

> *That question requires a theory, not a Random Forest."*

— Marcos López de Prado, March 2026

---

*Revisão produzida como exercício acadêmico. As opiniões são simuladas na persona do autor citado para fins de análise crítica.*
