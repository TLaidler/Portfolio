# T8 Full Pipeline Null Model — sg_acceleration_51 Variant

**Data:** 2026-03-26
**Objetivo:** Testar se o pipeline completo com **sg_acceleration_51** (2a derivada
SavGol, escala 51) substituindo sg_velocity_51 gera alpha genuino.

**Hipotese:** A aceleracao (2a derivada) e um artefato ainda mais fraco que a
velocidade (1a derivada). Se sg_velocity_51 foi fraca o suficiente para permitir
alpha genuino (T8 GENUINE, p=0.000), a aceleracao deve ser pelo menos tao boa.

---

## Metodologia

Para cada simulacao:
1. Substituir close/high/low dos dollar bars por precos sinteticos (random walk)
2. Preservar volume real e estrutura intra-bar (ratios high/low relativos ao close)
3. Computar as **mesmas 9 features** (sg_acceleration_51 no lugar de sg_velocity_51)
4. Aplicar triple-barrier labeling nos precos sinteticos
5. Treinar meta-label (80/20 split temporal) com **mesma config** do RF
6. Computar SR no test set

**Features testadas:** sg_acceleration_51, tstat_50, volatility_20, volatility_50, tstat_20, ffd_close, tstat_10, btc_dxy_spread, volatility_10
**N simulacoes:** 30
**Config RF:** 500 trees, depth=6, min_leaf=50
**LIMITE_DECISORIO:** 0.5
**Fees:** taker=0.0270% (pessimistic mode)

---

## Resultados

### SR do Modelo Real

| Metrica | Valor |
|---------|-------|
| SR (meta-label, todas barras) | **0.057242** |
| SR (apenas trades ativos) | **0.088272** |
| N trades ativos (teste) | 3725 |
| PSR | 1.0000 |
| Skewness | -0.0368 |

### Null Model A: Random Walk (drift=0)

| Metrica | Valor |
|---------|-------|
| N simulacoes validas | 30 |
| SR medio | -0.039791 +/- 0.027888 |
| P5 / P50 / P95 | -0.092321 / -0.036489 / 0.000146 |
| **p-value (todas barras)** | **0.0000** |
| **p-value (active trades)** | **0.0000** |
| N_active medio | 3648 +/- 1088 |

### Null Model B: Shuffled Returns

| Metrica | Valor |
|---------|-------|
| N simulacoes validas | 30 |
| SR medio | -0.033710 +/- 0.024010 |
| P5 / P50 / P95 | -0.075016 / -0.033478 / -0.004666 |
| **p-value (todas barras)** | **0.0000** |
| **p-value (active trades)** | **0.0000** |
| N_active medio | 3298 +/- 1068 |

---

## Veredito

### **GENUINE**

O SR do modelo completo (0.0572) supera P95 de **ambos** os null models.
A aceleracao SavGol na escala 51 e um artefato fraco o suficiente para complementar
features genuinas (tstat, volatility) sem dominar o RF.

**Implicacao:** sg_acceleration_51 e uma alternativa viavel a sg_velocity_51 como
feature de contexto. Ambas sao artefatos fracos que permitem alpha genuino emergir
da combinacao com features genuinas.

---

## Comparacao: Tres Variantes do T8 Full Pipeline

| Variante | SR real | SR null (RW) | p-value RW | p-value Shuf | Veredito |
|----------|---------|-------------|-----------|-------------|---------|
| sg_velocity_51 | 0.0518 | -0.046 +/- 0.037 | 0.0000 | 0.0000 | **GENUINE** |
| ret_20_savgol | ~0.082 | ~+0.074 (prelim) | >>0.05 | - | **ARTIFACT** |
| sg_acceleration_51 | 0.0572 | -0.0398 +/- 0.0279 | 0.0000 | 0.0000 | **GENUINE** |

---

## Analise Complementar

### Trades Ativos: O Pipeline Filtra Igual em Ruido?

| Cenario | N_active medio | SR_active medio |
|---------|---------------|-----------------|
| Dados reais | 3725 | 0.0883 |
| Random Walk | 3648 +/- 1088 | -0.0503 +/- 0.0382 |
| Shuffled | 3298 +/- 1068 | -0.0442 +/- 0.0334 |

### Skewness: O Pipeline Distorce a Distribuicao?

| Cenario | Skewness media |
|---------|---------------|
| Dados reais | -0.0368 |
| Random Walk | -0.1236 +/- 0.1081 |
| Shuffled | -1.5605 +/- 1.7991 |

---

## Tempo de Execucao

- Total: 45.4 minutos
- Por simulacao (media): 45.4 segundos

---

## Plots

![SR Distributions](pngs/t8fp_accel51_sr_distributions.png)

![Active Trades Analysis](pngs/t8fp_accel51_active_analysis.png)

![Box Plot Comparison](pngs/t8fp_accel51_boxplot.png)

---

*Gerado em 2026-03-26. Predecessores: t8_full_pipeline.md, t8_full_pipeline_ret20.md,
genuinas_vs_artefatos.md*
