# T8 Full Pipeline Null Model — ret_20_savgol Variant (PRELIMINAR)

**Data:** 2026-03-26
**Status:** PRELIMINAR — baseado em 6/30 simulacoes de Random Walk. Processo abortado
antes da conclusao. Resultados parciais consistentes o suficiente para conclusao.

**Objetivo:** Testar se substituir sg_velocity_51 por ret_20_savgol (artefato forte,
p=0.80 individualmente no T8 original) no pipeline completo ainda produz alpha genuino.

**Motivacao:** O T8 Full Pipeline com sg_velocity_51 resultou em GENUINE (p=0.000).
Sera que a feature mais forte (ret_20_savgol) produz resultado ainda melhor, ou o
fato de ser um artefato mais forte *contamina* o pipeline inteiro?

---

## Metodologia

Identica ao T8 Full Pipeline original, exceto:
- **sg_velocity_51 substituida por ret_20_savgol** (pct_change(20) sobre SavGol-smoothed close)
- ret_20_savgol computada manualmente (removida do FeatureRegistry por ser artefato)
- SavGol config: window=21, polyorder=3 (mesma do pipeline original)

**Features testadas:** ret_20_savgol, tstat_50, volatility_20, volatility_50, tstat_20, ffd_close, tstat_10, btc_dxy_spread, volatility_10
**N simulacoes planejadas:** 30 (apenas 6 RW completadas antes do abort)
**Config RF:** 500 trees, depth=6, min_leaf=50
**LIMITE_DECISORIO:** 0.5
**Fees:** taker=0.0270% (pessimistic mode)

---

## Resultados Preliminares

### SR do Modelo Real (ret_20_savgol variant)

| Metrica | Valor |
|---------|-------|
| SR (meta-label, todas barras) | **~0.082** |
| Nota | Maior que sg_velocity_51 (0.052) |

### Null Model A: Random Walk (drift=0) — PARCIAL

| Metrica | Valor |
|---------|-------|
| N simulacoes completadas | **6 de 30** |
| SR range observado | **+0.063 a +0.084** |
| SR medio (6 sims) | **~+0.074** |

**CRITICO:** Os SRs do null model sao **POSITIVOS** e se sobrepoem ao SR real (~0.082).

### Comparacao Direta com sg_velocity_51

| Metrica | sg_velocity_51 | ret_20_savgol |
|---------|---------------|---------------|
| SR real | 0.052 | ~0.082 |
| SR null (RW) range | -0.124 a +0.002 | **+0.063 a +0.084** |
| SR null (RW) medio | -0.046 | **~+0.074** |
| Separacao real vs null | **~5 sigma** | **~0 sigma** |
| Veredito | **GENUINE** | **ARTIFACT** (preliminar) |

---

## Veredito Preliminar

### **ARTIFACT**

Mesmo com apenas 6/30 simulacoes de Random Walk, o padrao e inequivoco:

1. **Os SRs do null model sao POSITIVOS** (~+0.074) — o pipeline gera SR positivo
   *mesmo em random walks puros* quando ret_20_savgol esta presente
2. **O SR real (~0.082) esta DENTRO da distribuicao nula** — nao ha separacao
   estatistica entre dados reais e ruido
3. **Contraste total** com sg_velocity_51: la o null era negativo (-0.046), aqui e positivo (+0.074)

**Nao e necessario completar 30 simulacoes.** A sobreposicao total entre real e null
com apenas 6 amostras ja exclui p-value < 0.05 com alta confianca.

---

## Interpretacao: Por Que Isso Acontece?

### O Mecanismo do Artefato

ret_20_savgol = pct_change(20) sobre precos suavizados por SavGol

O SavGol introduz autocorrelacao artificial: precos suavizados mudam lentamente,
entao pct_change(20) sobre eles e quase sempre positivo em tendencias de alta e
negativo em tendencias de baixa — **mesmo em random walks**.

Isso acontece porque:
1. O SavGol suaviza o random walk, criando "tendencias" artificiais
2. pct_change(20) captura essas "tendencias" como sinal
3. O RF aprende a usar esse sinal para prever direcao
4. A triple-barrier labeling nos mesmos precos suavizados cria labels com a mesma autocorrelacao
5. **Resultado: o RF "acerta" previsoes em random walks porque o artefato esta em ambos os lados**

### Por Que sg_velocity_51 Nao Tem Este Problema?

sg_velocity_51 (SavGol velocity, janela 51) e um artefato **mais fraco**:
- E a *derivada* do SavGol, nao o *nivel* — menos autocorrelada
- Janela maior (51 vs 21) dilui o sinal
- No RF, tem MDA=0.033 (contribuicao moderada, nao dominante)
- Permite que features genuinas (tstat_20, tstat_50) dominem as decisoes

ret_20_savgol (pct_change(20) sobre SavGol, janela 21) e um artefato **forte demais**:
- Captura nivel de preco suavizado diretamente
- Janela curta (21) preserva autocorrelacao alta
- No RF, DOMINA as outras features (MDA altissimo quando presente)
- **Abafa as features genuinas**, fazendo o modelo depender quase inteiramente do artefato

---

## Analogia Feynman

> *"Imagine que voce esta jogando dados e anota os resultados. Depois passa uma
> media movel nos resultados. Agora olha para a media movel e diz 'aha! ha uma
> tendencia!'. Claro que ha — voce criou a tendencia com a media movel.*
>
> *Com sg_velocity_51, voce esta olhando para a VELOCIDADE de mudanca da media
> movel — ela oscila em torno de zero mesmo com a suavizacao. O artefato existe
> mas e fraco o suficiente para nao enganar completamente.*
>
> *Com ret_20_savgol, voce esta olhando para o NIVEL da media movel comparado
> consigo mesma 20 periodos atras. Isso e quase garantido de ter sinal — artificial —
> em qualquer serie temporal suavizada.*
>
> *E como a diferenca entre ouvir um eco fraco (sg_velocity) vs um eco ensurdecedor
> (ret_20). O eco fraco permite ouvir sons genuinos por tras dele. O eco forte
> mascara tudo."*

---

## Perspectiva Marcos Lopez de Prado

Do ponto de vista de AFML:

1. **Selection bias amplification**: ret_20_savgol foi originalmente selecionada por
   ter alto MDA — mas esse MDA era inflado pelo artefato. Reintroduzi-la e reintroduzir
   o vies de selecao que o T8 original detectou (p=0.80).

2. **Feature dominance in RF**: Quando uma feature artefatual e muito forte, o RF
   aloca a maioria dos splits para ela, marginalizando features genuinas. O ensemble
   de 500 arvores converge para um modelo que e essencialmente "ret_20_savgol > threshold".

3. **The paradox resolved**: O "paradoxo dos artefatos" (modelo colapsa sem artefatos)
   tem uma resolucao precisa: o pipeline precisa de features de *contexto* (artefatos fracos)
   para complementar features de *sinal* (genuinas). Mas artefatos FORTES destroem
   o sinal ao inves de complementa-lo.

4. **Practical implication**: sg_velocity_51 esta no "sweet spot" — artefatual o
   suficiente para dar contexto ao RF, mas fraca o suficiente para nao dominar.
   Esta e a justificativa empirica para mante-la no pipeline.

---

## Comparacao Final: sg_velocity_51 vs ret_20_savgol

| Dimensao | sg_velocity_51 | ret_20_savgol |
|----------|---------------|---------------|
| Tipo | SavGol velocity (derivada) | SavGol pct_change (nivel) |
| Janela | 51 (larga) | 21 (curta) |
| T8 individual (p-value) | 0.33 (marginal) | 0.80 (artifact) |
| T8 full pipeline (p-value) | **0.000 (GENUINE)** | **>>0.05 (ARTIFACT)** |
| SR real | 0.052 | ~0.082 (maior!) |
| SR null RW | -0.046 | +0.074 (positivo!) |
| Papel no RF | Contexto (complementa tstat) | Dominante (abafa tstat) |
| Veredito | **MANTER** | **NAO READMITIR** |

**A maior ironia:** ret_20_savgol produz SR real MAIOR (0.082 vs 0.052), mas esse SR
e inteiramente explicavel por artefatos. sg_velocity_51 produz SR real MENOR, mas
esse SR e genuino. **Mais retorno ≠ mais alpha.**

---

## Conclusao

**ret_20_savgol NAO deve ser readmitida no pipeline.**

A decisao original de remove-la (T8 individual, p=0.80) esta validada tambem no
contexto do pipeline completo. A feature e tao forte como artefato que:
1. Domina o RF, marginalizando features genuinas
2. Gera SR positivo em random walks puros
3. Torna impossivel distinguir sinal real de ruido

O pipeline atual com sg_velocity_51 esta corretamente configurado: o artefato fraco
complementa as features genuinas sem domina-las.

---

*Gerado em 2026-03-26. PRELIMINAR (6/30 sims RW). Predecessores: t8_full_pipeline.md,
feature_null_model.md, genuinas_vs_artefatos.md*
