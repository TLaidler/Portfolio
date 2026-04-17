# T8 Full Pipeline Null Model — The Definitive Test

**Data:** 2026-03-26
**Objetivo:** Testar se o pipeline COMPLETO (features + RF + meta-label) gera
SR estatisticamente significativo em dados reais vs random walks.

**Diferenca do T8 original:** O T8 anterior testou features *individualmente*
(e.g., ret_20_savgol → p=0.80, artifact). Este teste avalia o *modelo completo*:
a combinacao de 9 features dentro do RF + meta-label pode gerar alpha genuino
mesmo que features individuais sejam artefatos?

---

## Metodologia

Para cada simulacao:
1. Substituir close/high/low dos dollar bars por precos sinteticos (random walk)
2. Preservar volume real e estrutura intra-bar (ratios high/low relativos ao close)
3. Computar as **mesmas 9 features** selecionadas pelo MDA no modelo real
4. Aplicar triple-barrier labeling nos precos sinteticos
5. Treinar meta-label (80/20 split temporal) com **mesma config** do RF
6. Computar SR no test set

**Features testadas:** sg_velocity_51, tstat_50, volatility_20, volatility_50, tstat_20, ffd_close, tstat_10, btc_dxy_spread, volatility_10
**N simulacoes:** 30
**Config RF:** 500 trees, depth=6, min_leaf=50
**LIMITE_DECISORIO:** 0.5
**Fees:** taker=0.0270% (pessimistic mode)

---

## Resultados

### SR do Modelo Real

| Metrica | Valor |
|---------|-------|
| SR (meta-label, todas barras) | **0.051801** |
| SR (apenas trades ativos) | **0.089928** |
| SR CPCV (media 15 paths) | 0.121100 |
| N trades ativos (teste) | 3094 |
| PSR | 1.0000 |
| Skewness | 0.0560 |

### Null Model A: Random Walk (drift=0)

| Metrica | Valor |
|---------|-------|
| N simulacoes validas | 30 |
| SR medio | -0.045990 +/- 0.037207 |
| P5 / P50 / P95 | -0.123718 / -0.044331 / 0.002218 |
| **p-value (todas barras)** | **0.0000** |
| **p-value (active trades)** | **0.0000** |
| N_active medio | 3781 +/- 1289 |

### Null Model B: Shuffled Returns

| Metrica | Valor |
|---------|-------|
| N simulacoes validas | 28 |
| SR medio | -0.032888 +/- 0.031067 |
| P5 / P50 / P95 | -0.073326 / -0.029583 / -0.000875 |
| **p-value (todas barras)** | **0.0000** |
| **p-value (active trades)** | **0.0000** |
| N_active medio | 3055 +/- 1153 |

---

## Veredito

### **GENUINE**

O SR do modelo completo (0.0518) supera P95 de **ambos** os null models.
O pipeline extrai sinal genuino que nao e explicavel por artefatos do filtro SavGol
nem pela distribuicao empirica dos retornos.

**Implicacao:** A combinacao de features (sg_velocity_51 como contexto + tstat como
sinal direcional) dentro do RF gera alpha que nao existe em nenhuma feature individual.
O todo e maior que a soma das partes.

---

## Analise Complementar

### Trades Ativos: O Pipeline Filtra Igual em Ruido?

| Cenario | N_active medio | SR_active medio |
|---------|---------------|-----------------|
| Dados reais | 3094 | 0.0899 |
| Random Walk | 3781 +/- 1289 | -0.0598 +/- 0.0501 |
| Shuffled | 3055 +/- 1153 | -0.0423 +/- 0.0430 |

Se o modelo gera numero similar de trades em dados reais e sinteticos, o meta-label
nao esta usando informacao genuina para decidir *quando* operar — esta operando
com a mesma frequencia em ruido.

Se o modelo gera MAIS trades em dados reais, ha evidencia de que detecta regime.
Se gera MENOS, pode estar sendo mais cauteloso com dados reais (possivel sinal
de que reconhece incerteza genuina).

### Skewness: O Pipeline Distorce a Distribuicao?

| Cenario | Skewness media |
|---------|---------------|
| Dados reais | 0.0560 |
| Random Walk | -0.1490 +/- 0.1131 |
| Shuffled | -1.4762 +/- 1.8791 |

---

## Tempo de Execucao

- Total: 66.5 minutos
- Por simulacao (media): 66.5 segundos

---

## Plots

![SR Distributions](pngs/t8fp_sr_distributions.png)

![Active Trades Analysis](pngs/t8fp_active_analysis.png)

![Box Plot Comparison](pngs/t8fp_boxplot.png)

---

*Gerado em 2026-03-26. Predecessores: feature_null_model.md, genuinas_vs_artefatos.md,
revisao_feynman_marcos_mod7.md*
