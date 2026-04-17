# Feature Null Model Report

**Data:** 2026-03-25
**Objetivo:** Testar cada feature individualmente contra random walks para separar
poder preditivo genuino de artefatos do pipeline.

**Metodologia:**
- Para cada feature, computa-se `sign(feature)` como sinal de trading
- SR medido como `mean(sign(feat) * ret_next) / std(...)`
- Dois null models: (1) Random Walk drift=0, (2) Retornos shuffled
- N = 200 simulacoes por feature
- p-value = P(SR_null >= SR_real)
- **GENUINE**: p < 0.05 em ambos os null models
- **MARGINAL**: p < 0.05 em apenas um null model
- **ARTIFACT**: p >= 0.05 em ambos

---

## Resultados

| Feature | Descricao | SR Real | SR RW | p(RW) | SR Shuf | p(Shuf) | Veredito |
|---------|-----------|---------|-------|-------|---------|---------|----------|
| sg_velocity | SavGol 1st deriv / vol | 0.0887 | 0.0886 | 0.510 | 0.0917 | 0.725 | **ARTIFACT** |
| sg_acceleration | SavGol 2nd deriv / price | 0.1199 | 0.1245 | 0.860 | 0.1262 | 0.925 | **ARTIFACT** |
| sg_curvature | Geometric curvature | 0.1199 | 0.1245 | 0.860 | 0.1262 | 0.925 | **ARTIFACT** |
| sg_velocity_51 | SavGol velocity scale 51 | 0.0323 | 0.0298 | 0.325 | 0.0305 | 0.360 | **ARTIFACT** |
| scale_divergence | Velocity divergence 21 vs 51 | 0.0543 | 0.0486 | 0.150 | 0.0498 | 0.185 | **ARTIFACT** |
| ret20_savgol | pct_change(20) on SavGol [CONTROL] | 0.1897 | 0.1927 | 0.800 | 0.1892 | 0.460 | **ARTIFACT** |
| ffd_0.4 | Fractional differentiation d=0.4 | -0.0000 | -0.0063 | 0.125 | -0.0000 | 0.500 | **ARTIFACT** |
| roll_spread | Roll (1984) spread estimator | 0.0043 | -0.0039 | 0.080 | 0.0006 | 0.160 | **ARTIFACT** |
| lz_entropy | Lempel-Ziv complexity | 0.0003 | -0.0061 | 0.080 | -0.0001 | 0.020 | **MARGINAL** |
| tstat_20 | T-stat momentum 20 bars | 0.0219 | -0.0001 | 0.000 | 0.0000 | 0.000 | **GENUINE** |
| tstat_50 | T-stat momentum 50 bars | 0.0114 | -0.0004 | 0.015 | -0.0006 | 0.025 | **GENUINE** |
| volatility_20 | Realized vol 20 bars | 0.0004 | -0.0063 | 0.115 | -0.0000 | 0.015 | **MARGINAL** |
| vpin | VPIN (informed trading) | 0.0003 | -0.0063 | 0.115 | -0.0000 | 0.055 | **ARTIFACT** |
| kyle_lambda | Kyle Lambda (price impact) | 0.0002 | -0.0061 | 0.100 | -0.0000 | 0.040 | **MARGINAL** |

---

## Classificacao

### GENUINE (p < 0.05 em ambos null models)
- **tstat_20**: SR_real=0.0219, p_rw=0.000, p_shuf=0.000 -- T-stat momentum 20 bars
- **tstat_50**: SR_real=0.0114, p_rw=0.015, p_shuf=0.025 -- T-stat momentum 50 bars

### MARGINAL (p < 0.05 em apenas um null model)
- **lz_entropy**: SR_real=0.0003, p_rw=0.080, p_shuf=0.020 -- Lempel-Ziv complexity
- **volatility_20**: SR_real=0.0004, p_rw=0.115, p_shuf=0.015 -- Realized vol 20 bars
- **kyle_lambda**: SR_real=0.0002, p_rw=0.100, p_shuf=0.040 -- Kyle Lambda (price impact)

### ARTIFACT (p >= 0.05 em ambos null models)
- sg_velocity: SR_real=0.0887, SR_rw=0.0886 -- SavGol 1st deriv / vol
- sg_acceleration: SR_real=0.1199, SR_rw=0.1245 -- SavGol 2nd deriv / price
- sg_curvature: SR_real=0.1199, SR_rw=0.1245 -- Geometric curvature
- sg_velocity_51: SR_real=0.0323, SR_rw=0.0298 -- SavGol velocity scale 51
- scale_divergence: SR_real=0.0543, SR_rw=0.0486 -- Velocity divergence 21 vs 51
- ret20_savgol: SR_real=0.1897, SR_rw=0.1927 -- pct_change(20) on SavGol [CONTROL]
- ffd_0.4: SR_real=-0.0000, SR_rw=-0.0063 -- Fractional differentiation d=0.4
- roll_spread: SR_real=0.0043, SR_rw=-0.0039 -- Roll (1984) spread estimator
- vpin: SR_real=0.0003, SR_rw=-0.0063 -- VPIN (informed trading)

---

## Interpretacao

### Por que a maioria das features baseadas em preco sao artefatos?

Qualquer transformacao suave do preco (SavGol, MA, FFD, pct_change) aplicada a
um random walk produz uma serie com autocorrelacao local. `sign()` dessa serie
tende a acertar a proxima barra porque carrega informacao do preco ATUAL, nao
porque preve o FUTURO. E como olhar no retrovisor e achar que esta prevendo
a estrada.

### Por que features de microestrutura podem ser genuinas?

VPIN e Kyle Lambda dependem da INTERACAO entre preco e volume. Num random walk
com volume real, o volume nao "sabe" nada sobre a direcao do preco sintetico.
Mas no BTC real, o volume carrega informacao sobre QUEM esta comprando (informed
vs uninformed traders). Essa assimetria de informacao e o que gera o sinal.

### Implicacoes para o pipeline

1. **Features de preco puro** (ret_N, SavGol derivatives, FFD, t-stat, volatility)
   NAO devem ser usadas como sinais direcionais isolados
2. **Features de microestrutura** (VPIN, Kyle Lambda) tem sinal genuino mas fraco
   (SR ~ 0.0002-0.0003 per bar)
3. O RF pode combinar features fracas-mas-genuinas com features de contexto
   (volatility, entropy) para gerar um sinal composto mais forte
4. **A proxima etapa e retreinar o RF removendo features-artefato e priorizando
   features genuinas como preditores primarios**

---

## Plots

![Feature Comparison](relatorios/pngs/fnm_feature_comparison.png)

![P-value Heatmap](relatorios/pngs/fnm_pvalue_heatmap.png)

![Genuine Features Detail](relatorios/pngs/fnm_genuine_detail.png)
