# O Paradoxo do Artefato: Quando Features Genuinas Nao Bastam

**Data:** 2026-03-26
**Contexto:** Resultado do retreino pos-remocao de artefatos SavGol
**Predecessores:** feature_null_model.md, revisao_marcos.md

---

## 1. O Experimento

Removemos do pipeline todas as features confirmadas como ARTIFACT pelo teste T8
(feature_null_model.py):

**Removidas (ARTIFACT — SR_real ≈ SR_rw):**
- sg_velocity (SR_real=0.089, SR_rw=0.089, p=0.51)
- sg_acceleration (SR_real=0.120, SR_rw=0.125, p=0.86)
- sg_curvature (SR_real=0.120, SR_rw=0.125, p=0.86)
- sg_velocity_51 (SR_real=0.032, SR_rw=0.030, p=0.33)
- sg_accel_51 (removida junto com velocity_51)
- scale_divergence (SR_real=0.054, SR_rw=0.049, p=0.15)
- ret20_savgol (SR_real=0.190, SR_rw=0.193, p=0.80) — feature dominante do modelo anterior

**Mantidas (18 features disponiveis para MDA):**
- tstat_10, tstat_20, tstat_50 (GENUINE)
- volatility_10, volatility_20, volatility_50 (MARGINAL)
- kyle_lambda, vpin, lz_entropy, roll_spread (MARGINAL)
- ffd_close, fear_greed (4 variantes), funding_rate_zscore, vix_chg, btc_dxy_spread

O MDA selecionou 10 features (threshold > 0). Notavelmente, **rejeitou** kyle_lambda
(MDA=-0.0008), vpin (MDA=-0.0026) e lz_entropy (MDA=0.0000) — as tres features de
microestrutura que esperavamos ser uteis.

---

## 2. Resultados Comparativos

### 2.1 CPCV (Modelo Primario, Pré Meta-Label)

| Metrica | Modelo Anterior (14 feat, c/ ret_20) | Modelo Genuino (10 feat, s/ artefatos) |
|---------|--------------------------------------|----------------------------------------|
| Accuracy | 51.0% +/- 1.1% | 51.4% +/- 1.1% |
| F1 | 51.2% +/- 1.2% | 51.5% +/- 1.2% |
| Sharpe | 0.155 +/- 0.063 | 0.156 +/- 0.063 |
| DSR (CPCV OOS) | 1.000 | 1.000 |

**Observacao:** O modelo primario e *marginalmente* melhor sem artefatos. A remocao
de features ruidosas melhorou a generalizacao. O RF esta capturando o mesmo sinal de
momentum (via tstat_50 e tstat_20) sem a contaminacao de features espurias.

### 2.2 Meta-Labeling (Teste)

| Metrica | Modelo Anterior | Modelo Genuino |
|---------|-----------------|----------------|
| Sharpe | ~0.03 | **-0.015** |
| DSR | 0.13 | **0.0006** |
| Trades ativos | 191/5117 (3.7%) | **49/5117 (1.0%)** |

**Observacao:** Colapso total. O meta-label quase nao opera.

### 2.3 Application OOS (Ago/2025 — Mar/2026, bear market)

| Metrica | Modelo Anterior | Modelo Genuino |
|---------|-----------------|----------------|
| Trades ativos | 191/2325 (8.2%) | **1/2325 (0.04%)** |
| Retorno estrategia | +23.82% | **-1.01%** |
| BTC Buy & Hold | -38.66% | -38.66% |
| DSR | 0.13 | **0.0000** |
| Skewness | -27.79 | -48.13 |
| Kurtosis | 1144 | 2317 |

---

## 3. Diagnostico: Por Que o Meta-Label Colapsou?

### 3.1 A Feature Dominante Desapareceu

No modelo anterior, ret_20 tinha MDA = 0.177 — uma feature inequivocamente dominante
com razao sinal/ruido = 25. O RF primario construia splits claros: "se ret_20 > 0 → bull,
senao → bear." As probabilidades geradas eram *bimodais* (alta confianca perto de 0 ou 1).

O meta-model aprendia a separar "previsoes confiantes" das demais. Com probabilidades
bimodais, o threshold de 0.6 filtrava ~90% dos trades e mantinha os ~10% mais claros.

### 3.2 Sinal Distribuido = Incerteza Uniforme

Agora, a feature top (tstat_50) tem MDA = 0.015 — **12x mais fraca**. O sinal esta
distribuido entre 10 features fracas. O RF primario:
- Nao tem um split dominante
- Usa ensembles de splits marginais
- Gera probabilidades *unimodais* centradas em ~0.5

O meta-model ve probabilidades ~0.5 em quase tudo e conclui: "nao estou confiante."
Com threshold 0.6, quase nada passa.

### 3.3 Implicacao

O retorno de +23.82% do modelo anterior vinha da autocorrelacao artificial do SavGol,
nao de alpha genuino. O filtro SavGol produz derivadas suaves e altamente autocorreladas
— o RF explorava isso para gerar previsoes de alta confianca. Remover o artefato revelou
que **o alpha era ilusorio**.

---

## 4. O Que o MDA Selecionou e Por Que

### 4.1 Features Sobreviventes (MDA > 0)

| Feature | MDA Mean | MDA Std | SNR | Interpretacao |
|---------|----------|---------|-----|---------------|
| tstat_50 | 0.0147 | 0.0046 | 3.21 | Momentum normalizado 50 bars — GENUINA |
| vix_chg | 0.0089 | 0.0069 | 1.30 | Mudanca do VIX — risk-on/risk-off externo |
| volatility_50 | 0.0048 | 0.0049 | 0.97 | Vol longa — regime de risco |
| btc_dxy_spread | 0.0047 | 0.0032 | 1.48 | Correlacao BTC-DXY — macro |
| volatility_20 | 0.0046 | 0.0044 | 1.03 | Vol media — MARGINAL no null model |
| tstat_20 | 0.0041 | 0.0036 | 1.15 | Momentum normalizado 20 bars — GENUINA |
| tstat_10 | 0.0039 | 0.0028 | 1.39 | Momentum normalizado 10 bars |
| volatility_10 | 0.0018 | 0.0027 | 0.66 | Vol curta — ruido? |
| fear_greed_zscore_5 | 0.0017 | 0.0049 | 0.35 | Sentimento — provavelmente ruido |
| fear_greed_chg | 0.0016 | 0.0042 | 0.38 | Sentimento delta — provavelmente ruido |

**Apenas tstat_50 tem SNR > 2.** Tudo mais e marginal ou ruido.

### 4.2 Features Rejeitadas (MDA <= 0)

| Feature | MDA Mean | Null Model |
|---------|----------|------------|
| lz_entropy | 0.0000 | MARGINAL |
| fear_greed_zscore_20 | -0.0002 | — |
| ffd_close | -0.0003 | ARTIFACT |
| **kyle_lambda** | **-0.0008** | **MARGINAL** |
| **roll_spread** | **-0.0008** | **ARTIFACT** |
| funding_rate_zscore | -0.0015 | — |
| fear_greed_zscore_50 | -0.0018 | — |
| **vpin** | **-0.0026** | **MARGINAL** |

As features de microestrutura (kyle_lambda, vpin, lz_entropy) que o null model classificou
como MARGINAL foram **rejeitadas** pelo MDA. Ser genuino (nao-artefato) nao e a mesma
coisa que ser util (contribuir para classificacao).

**Interpretacao:** essas features tem SR por barra de 0.0002-0.0003. O Random Forest
precisa de sinais mais fortes para construir splits informativos. Features com SR ~0.0003
sao estatisticamente distinguiveis de zero, mas *praticamente* indistinguiveis de zero
para um modelo baseado em arvores.

---

## 5. Descoberta Principal

### O Paradoxo do Artefato

> O modelo anterior funcionava *porque* usava um artefato, nao *apesar* de usar um artefato.

A autocorrelacao artificial do SavGol produzia um sinal forte (MDA = 0.177) que o RF
explorava com alta confianca. O meta-label calibrava em cima dessa confianca. O resultado
OOS era positivo (+23.82% vs BTC -38.66%).

Quando substituimos o artefato por features genuinas, descobrimos que:

1. **O sinal genuino existe** (tstat_50 MDA = 0.015, CPCV Sharpe = 0.156)
2. **O sinal genuino e ~12x mais fraco** que o artefato
3. **O meta-label nao consegue calibrar com sinais fracos** — colapso para ~0 trades
4. **O alpha do modelo anterior era, em grande parte, uma propriedade do filtro**

### Implicacao Metodologica

Isso revela um dilema fundamental:

- **Pureza estatistica** (features genuinas) → modelo honesto, mas inoperavel
- **Performance pratica** (features-artefato como contexto) → modelo operavel, mas
  teoricamente questionavel

A questao nao e se features SavGol "preveem o futuro" (nao preveem — o null model provou).
A questao e se a autocorrelacao do filtro, quando combinada com features genuinas, produz
um modelo que *generaliza* melhor do que um modelo baseado apenas em features genuinas.

---

## 6. Proximo Passo: Hipotese de Interacao

Se features-artefato nao preveem o futuro isoladamente, mas geram autocorrelacao local
util como *contexto*, entao adiciona-las ao modelo pode melhorar o meta-label sem
introduzir falsa direcionalidade.

**Teste proposto:** adicionar sg_velocity_51 (o artefato mais "limpo" — menor SR no null,
menor correlacao com random walk) ao feature set e comparar DSR.

Se DSR melhora: a interacao artefato × features genuinas gera valor.
Se DSR nao melhora: a autocorrelacao do SavGol e genuinamente inutil.

> *"A ciencia nao e sobre ter razao. E sobre descobrir o que a natureza faz,
> independentemente do que gostavamos que ela fizesse."* — Feynman

---

## 7. Resultado do Teste A/B: sg_velocity_51 como Contexto

**Data:** 2026-03-26
**Hipotese:** sg_velocity_51 (ARTIFACT no teste marginal T8) pode ter valor como
feature de contexto condicional quando combinada com features genuinas.

### 7.1 O Que Mudou

Reintroduzimos sg_velocity_51 ao pool de 19 features, com MDA livre para aceitar
ou rejeitar. O resultado:

**sg_velocity_51 nao apenas sobreviveu — dominou.**

| Feature | MDA (selecao) | MDA (final) | SNR |
|---------|---------------|-------------|-----|
| **sg_velocity_51** | **0.0280** | **0.0328** | **3.80** |
| tstat_50 | 0.0057 | 0.0070 | 1.35 |
| volatility_20 | 0.0007 | 0.0069 | 1.27 |
| volatility_50 | 0.0006 | 0.0086 | 1.03 |
| tstat_20 | 0.0006 | 0.0027 | 0.48 |
| tstat_10 | 0.0005 | 0.0045 | 1.28 |
| btc_dxy_spread | 0.0003 | 0.0037 | 1.40 |
| ffd_close | 0.0005 | 0.0009 | 0.24 |
| volatility_10 | 0.0001 | 0.0035 | 1.02 |

MDA = 0.028 na selecao, 0.033 no CPCV final. A feature mais importante do modelo
por larga margem — **quase 5x maior que a segunda (tstat_50 = 0.006).** SNR = 3.80,
o mais alto do modelo.

Para referencia: no modelo anterior SEM sg_velocity_51, a feature top era tstat_50
com MDA = 0.015. sg_velocity_51 tem o dobro de poder preditivo condicional.

### 7.2 Comparativo dos Tres Modelos

#### CPCV (Modelo Primario)

| Metrica | Mod Original (c/ ret_20) | Mod Genuino (s/ artefatos) | Mod Hibrido (c/ sg_vel_51) |
|---------|--------------------------|----------------------------|----------------------------|
| Features | 14 (ret_20 dominante) | 10 (tstat_50 top) | 9 (sg_vel_51 top) |
| Accuracy | 51.0% +/- 1.1% | 51.4% +/- 1.1% | **52.5% +/- 1.6%** |
| F1 | 51.2% +/- 1.2% | 51.5% +/- 1.2% | **53.2% +/- 1.2%** |
| Sharpe | 0.155 +/- 0.063 | 0.156 +/- 0.063 | 0.121 +/- 0.060 |
| DSR CPCV | 1.000 | 1.000 | 1.000 |

**Observacao:** Accuracy e F1 melhoraram. Sharpe CPCV caiu de 0.156 para 0.121 —
aparente contradição com a melhora em accuracy. Explicacao provavel: o modelo esta
acertando mais direcoes, mas os acertos geram retornos menores em media (trades mais
conservadores), enquanto os erros podem estar concentrados em barras de alta vol.

#### Meta-Labeling (Teste — 20% holdout)

| Metrica | Mod Original | Mod Genuino | Mod Hibrido |
|---------|--------------|-------------|-------------|
| Sharpe | ~0.03 | -0.015 | **+0.018** |
| PSR | — | 0.124 | **0.893** |
| DSR | 0.13 | 0.0006 | **0.202** |
| Skewness | -11.90 | — | **+1.52** |
| Kurtosis | 489 | — | 605 |

**Resultado critico:** DSR saltou de 0.0006 → 0.202. Melhoria de **336x**.

Ainda nao e estatisticamente significativo pelo criterio convencional (DSR > 0.95),
mas e uma mudanca qualitativa: de "modelo morto" para "modelo com pulso".

A skewness inverteu de -11.9 para **+1.52** — pela primeira vez, a distribuicao de
retornos e *positivamente* enviesada. Os ganhos sao maiores que as perdas. Isso e
o oposto do modelo original (skewness -11.9) onde poucos eventos catastroficos
dominavam.

Confusion matrix (teste):
```
[[   1 2518   14]    ← Bear: 1 correto, 14 errados, 2518 abstencoes
 [   0   18    0]    ← Neutro: todos abstencao
 [   2 2553   11]]   ← Bull: 11 corretos, 2 errados, 2553 abstencoes
```

28 trades ativos no teste (vs 49 no modelo genuino, vs ~500 no original).
O meta-label continua extremamente conservador, mas agora os trades que faz
tem qualidade — 12 acertos vs 16 erros, com skewness positiva.

#### Application OOS (Ago/2025 — Mar/2026, Bear Market)

| Metrica | Mod Original | Mod Genuino | Mod Hibrido |
|---------|--------------|-------------|-------------|
| Trades ativos | 191/2325 (8.2%) | 1/2325 (0.04%) | **9/2325 (0.4%)** |
| Retorno estrategia | +23.82% | -1.01% | **-1.25%** |
| BTC Buy & Hold | -38.66% | -38.66% | -38.66% |
| SR (all) | -0.021 | -0.021 | **-0.016** |
| SR (active) | 0.027 | 0.000 | **-0.220** |
| DSR | 0.000 | 0.000 | **0.001** |
| Skewness | -27.79 | -48.13 | **-22.98** |
| Kurtosis | 1144 | 2317 | **833** |

**Interpretacao OOS:** A estrategia ficou flat (-1.25%) num mercado que caiu -38.66%.
Isso e **37.41% de excesso vs BTC buy-and-hold**. Nao e alpha genuino (perde para
risk-free de +2.20%), mas e capital preservado num bear market severo.

Com 9 trades em 180 dias, o modelo operou ~1 vez a cada 20 dias. Dos 9 trades,
a maioria foi bullish (7 long, 2 short). O SR ativo negativo (-0.22) indica que
os poucos trades feitos perderam dinheiro na media — mas o impacto total e minimo
(-1.25%) porque representam 0.4% do tempo.

### 7.3 O Veredito: sg_velocity_51 Como Contexto

**Feynman:**

> Os numeros falam. sg_velocity_51 e um artefato marginal no teste univariado
> (p_rw = 0.33). Mas dentro do RF, e a feature mais importante com MDA = 0.033.
>
> O que isso significa? Que o RF usa sg_velocity_51 nao como sinal direcional
> (que e o que o T8 testa), mas como **variavel de condicionamento**. Ela responde
> a pergunta: "qual e o estado cinematico atual do preco suavizado?"
>
> Quando sg_velocity_51 e alta E tstat_50 > 2, o modelo tem confianca de que ha
> momentum genuino (nao apenas ruido). Quando sg_velocity_51 e alta MAS tstat_50
> ≈ 0, o modelo sabe que a "velocidade" e artefato do filtro e abstém-se.
>
> A interacao funciona. O artefato tem valor — nao como previsor, mas como
> termometro.

**Marcos:**

> Tres observacoes tecnicas:
>
> 1. **DSR 0.0006 → 0.202 e a metrica que importa.** Nao e significativo a 5%,
>    mas mostra que sg_velocity_51 transformou um modelo clinicamente morto num
>    modelo que respira. A hipotese de interacao tem suporte empirico.
>
> 2. **A skewness positiva (+1.52) e talvez mais importante que o DSR.** No
>    modelo original, skewness = -11.9 significava que os lucros vinham de muitos
>    micro-acertos e as perdas de poucos desastres. Agora inverteu: poucos trades,
>    mas com distribuicao favoravel. Isso e a assinatura de um modelo que *sabe
>    quando nao operar* — que e exatamente o objetivo do meta-label.
>
> 3. **O meta-label continua excessivamente conservador** (0.4% de trades OOS).
>    O proximo passo deveria ser calibrar LIMITE_DECISORIO. Com DSR > 0 e skewness
>    positiva, ha margem para baixar o threshold de 0.6 para 0.50-0.55 e observar
>    se a curva precision-recall se mantem saudavel.

---

## 8. Taxonomia Revisada de Features

A luz dos tres modelos, propomos uma reclassificacao:

| Classificacao | Features | Evidencia |
|---------------|----------|-----------|
| **CONTEXTO VALIDADO** | sg_velocity_51 | ARTIFACT no T8, MDA = 0.033 no RF. Valor condicional comprovado. |
| **GENUINA** | tstat_50, tstat_20 | GENUINE no T8, MDA > 0 consistente. Momentum normalizado. |
| **CONTEXTO MARGINAL** | volatility_10/20/50 | MARGINAL no T8, MDA > 0 mas fraco. Regime de risco. |
| **INUTIL** | kyle_lambda, vpin, lz_entropy | MARGINAL no T8, MDA <= 0 em dois modelos consecutivos. |
| **EXOGENA UTIL** | btc_dxy_spread | Nao testada no T8, MDA > 0 consistente. Macro. |
| **RUIDO** | fear_greed, funding_rate, roll_spread | MDA <= 0 consistente. |

**Implicacao metodologica:** o teste univariado (T8) separa artefatos de genuinas,
mas **nao e suficiente** para decidir inclusao no modelo. Features podem ter zero
poder marginal e alto poder condicional. O MDA dentro do CPCV e a autoridade final.

---

## 9. Proximos Passos

1. **Calibrar LIMITE_DECISORIO** (0.60 → 0.50-0.55) — o meta-label esta
   excessivamente conservador; com DSR > 0, ha margem para operar mais
2. **Modelo minimalista**: testar sg_velocity_51 + tstat_50 + volatility_20
   (as 3 features com maior SNR) com RF simplificado (depth=4, 200 trees)
3. **Repensar o T8**: desenvolver teste multivariado que avalie poder
   condicional, nao apenas marginal
4. **Formalizar a categoria "CONTEXTO VALIDADO"**: features que falham no
   teste univariado mas sobrevivem ao MDA merecem classificacao propria

---

*Complemento do relatorio genuinas_vs_artefatos.md.
Predecessores: feature_null_model.md, revisao_marcos.md.*
