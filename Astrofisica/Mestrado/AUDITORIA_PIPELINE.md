# Auditoria Crítica da Pipeline de Detecção de Ocultações Estelares

**Auditor:** Cientista de Dados Sênior + Pesquisador em Astroestatística (com Richard Feynman, Carl Sagan e Josiah Willard Gibbs)
**Data:** 2026-04-04
**Escopo:** `pipeline/` (Python) + `writing_latex/Tese/` (dissertação)
**Status deste documento:** registro técnico de referência. Não dispara ações imediatas.

> **Nota (2026-08-20):** este documento tem duas rodadas. A **primeira rodada** (abaixo) foi
> obtida por leitura de código e enumera 10 achados críticos de natureza estatística.
> A **segunda rodada** ([ir para a seção](#segunda-rodada--verificação-empírica-2026-08-20))
> mediu empiricamente cada hipótese da primeira contra o dataset e o banco, **refutou uma
> delas com números** (C3), **resolveu outra** (C9) e acrescentou 9 achados novos — entre eles
> dois que a primeira rodada não podia enxergar por serem de *construção do benchmark*,
> não de estatística (V1 e V2).

---

## Sumário executivo

A pipeline está **funcional e tecnicamente correta nos pontos centrais** (split por curva, imputação fit-on-train, padronização condicional para Logistic Regression, McNemar test, persistência de artefatos). Apresenta, no entanto, **10 achados CRÍTICOS** que afetam ou poderiam afetar a interpretação dos resultados. A maioria não invalida as conclusões da dissertação, mas exige **reconhecimento explícito como limitação** ou **correção antes de submissão a periódico**.

| Categoria | CRÍTICO | IMPORTANTE | MENOR | OK |
|-----------|:-------:|:----------:|:-----:|:--:|
| Pré-processamento + Features | 3 | 2 | 1 | 2 |
| Modelo + Treino | 3 | 1 | 1 | 5 |
| Validação + Métricas | 4 | 4 | 1 | 6 |
| **Total** | **10** | **7** | **3** | **13** |

---

## Achados CRÍTICOS

### C1. Normalização do baseline contaminada pelo dip

**Arquivo:** `pipeline/model_training/astro_data_access.py:222-281` (função `normalize_flux`)

A baseline é estimada como média das duas médias mais altas entre quatro segmentos quartílicos. Se o dip ocupa o segundo ou terceiro quartil temporal, esse segmento ainda pode estar entre os "top-2" para dips rasos, **contaminando a baseline e achatando artificialmente a profundidade do dip**.

**Mitigação:** mediana acima do percentil 75 da curva inteira:
```python
baseline = np.median(flux[flux >= np.percentile(flux, 75)])
```

---

### C2. Remoção de outliers pode descartar o próprio dip em baixo SNR

**Arquivo:** `pipeline/model_training/astro_data_access.py:593-605` (função `remove_outliers`)

Z-score de 3σ sobre a média global. Em curvas de baixo SNR, o piso do dip pode exceder 3σ da média (puxada para baixo pelo próprio dip) e ser removido como outlier — exatamente o sinal que se quer detectar.

**Mitigação:** usar MAD (mediana de desvios absolutos) em vez de média/desvio padrão, ou aplicar z-score apenas em pontos *acima* da mediana.

---

### C3. Vazamento potencial de positiva original após criação de negativos artificiais ⚠️ DETALHADO

**Arquivo:** `pipeline/model_training/build_dataset.py:69-214` (função `recortar_negativos_interativo`)

#### O problema

Quando um segmento negativo é recortado de uma curva positiva, o código corretamente exclui a positiva original do conjunto de positivas. Porém, **o identificador da curva é construído como string e o filtro de exclusão opera apenas sobre o nome completo da curva**, não sobre o triplet `(objeto, data, observador)`:

```python
# build_dataset.py — linha ~195
new_curve = {
    'time': seg_time.tolist(),
    'flux': seg_flux.tolist(),
    'flux_normalized': seg_flux.tolist()
}
curve_id = f"{obj}_{date}_{observer}_{seg_name}"   # Identificador composto
artificial_negatives.append((new_curve, obj, date, observer, seg_name))
```

Se o mesmo `(objeto, data, observador)` aparecer como **positiva nativa** em outra entrada do banco (por exemplo, mesma campanha de Umbriel registrada por dois caminhos diferentes — Grupo do Rio e VizieR), o filtro atual **não detecta o conflito**. Mesma observação física pode aparecer como positiva em uma fold e como negativa (recortada de outra entrada) em outra fold.

#### Exemplo numérico

Suponha duas entradas no banco:
- Entrada A: `Umbriel_2020-09-21_Bardecker.dat` (positiva, do Grupo do Rio)
- Entrada B: `(UII)_20200921_Bardecker_J.dat` (mesma observação, registrada no VizieR com naming distinto)

Da Entrada A, recorta-se um segmento "antes do ingresso" como negativo artificial. Na hora do split:
- Treino: Entrada A (positiva) + segmento de A (negativo artificial) → **conflito interno corretamente bloqueado**
- Treino: Entrada A (positiva)
- Teste: segmento de B (negativo artificial recortado) → **vazamento**: o modelo já viu o ruído desta noite, deste telescópio, desta estrela, na classe positiva.

#### Mitigação proposta

Rastrear o triplet durante o split:
```python
# Pseudocódigo
def split_by_curve_safe(df, test_size=0.2, random_state=42):
    df['triplet_key'] = df['object'] + '_' + df['date'] + '_' + df['observer']
    triplets = df['triplet_key'].unique()
    train_triplets, test_triplets = train_test_split(
        triplets, test_size=test_size, random_state=random_state
    )
    df_train = df[df['triplet_key'].isin(train_triplets)]
    df_test  = df[df['triplet_key'].isin(test_triplets)]
    # Garante que mesmo triplet nunca aparece em ambos os conjuntos
    return df_train, df_test
```

O ganho prático esperado: queda marginal de F1 (provavelmente <0,5 pp), mas **eliminação completa** desse vetor de vazamento.

---

### C4. Ausência de detecção/mitigação de ruído correlacionado (1/f, atmosférico)

**Arquivo:** pipeline inteira — não foi encontrada referência

A pipeline assume implicitamente ruído branco gaussiano. Curvas de luz reais exibem **ruído vermelho** (cintilação atmosférica, deriva térmica), que pode mimetizar dips e enviesar tanto treino quanto avaliação. Knieling et al. (2024) e Cazeneuve et al. (2023) tratam isso explicitamente via Processos Gaussianos ou redes que processam séries de referência.

**Mitigação mínima:** adicionar feature de autocorrelação de lag-1 ao vetor:
```python
def acf_lag1(flux):
    f = flux - np.mean(flux)
    return float(np.dot(f[:-1], f[1:]) / np.dot(f, f))
```

---

### C5. XGBoost sem regularização explícita L1/L2

**Arquivo:** `pipeline/model_training/train_model.py:123-132` (`XGB_PARAMS`)

`reg_alpha` (L1) e `reg_lambda` (L2) ausentes — usa apenas defaults. Para `max_depth=6` e `n_estimators=100`, isso é regularização frouxa.

**Mitigação:** adicionar `'reg_alpha': 0.1, 'reg_lambda': 1.0` (ou tunar via Optuna).

---

### C6. Regressão Logística sem `penalty` e `C` explícitos

**Arquivo:** `pipeline/model_training/train_model.py:143-148` (`LR_PARAMS`)

Faltam `'penalty': 'l2'` e `'C': 1.0`. Default funciona, mas **não está explícito no código** — qualquer arguente em banca perguntaria "qual regularização você usou?".

---

### C7. Hiperparâmetros fixos sem busca sistemática

**Arquivo:** `pipeline/model_training/train_model.py:113-148`

Todos os valores hardcoded. Não há GridSearchCV, RandomizedSearchCV nem Optuna. Já reconhecido como limitação no cap. 6 da dissertação.

---

### C8. Métricas reportadas apenas como estimativas pontuais (sem CI)

**Arquivo:** `pipeline/model_training/train_model.py:529-559` (`evaluate_model`)

F1 = 0,9906 (sem ±0,XX). McNemar implementado, mas **não há bootstrap confidence intervals nem paired t-test entre folds**. Banca de doutorado e revisores de periódico exigem incerteza nas métricas.

**Mitigação:**
```python
from scipy.stats import bootstrap
ci = bootstrap((y_test, y_pred),
               lambda yt, yp: f1_score(yt, yp),
               n_resamples=1000, paired=True)
```

---

### C9. Apenas uma semente aleatória (42) ⚠️ DETALHADO

**Arquivo:** `pipeline/model_training/train_model.py:62`

#### O problema

Toda a análise depende de um único `RANDOM_STATE`:

```python
# train_model.py — linha 62
RANDOM_STATE = 42

# Aplicada em:
np.random.seed(RANDOM_STATE)         # linha 63
random.seed(RANDOM_STATE)            # linha 64
RF_PARAMS  = {..., 'random_state': RANDOM_STATE}    # linha 118
XGB_PARAMS = {..., 'random_state': RANDOM_STATE}    # linha 129
CAT_PARAMS = {..., 'random_state': RANDOM_STATE}    # linha 138
LR_PARAMS  = {..., 'random_state': RANDOM_STATE}    # linha 145

# Nas funções de split:
train_test_split(..., random_state=RANDOM_STATE)    # passado em split_by_curve, etc.

# StratifiedKFold (CV):
skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=random_state)  # linha 736
```

Reprodutibilidade é excelente (qualquer um roda e obtém o mesmo F1=0,9906). Porém, **toda a tese depende de uma única partição aleatória**. Se a semente 42 produziu uma divisão "fácil", o resultado é otimista; se produziu uma "difícil", é pessimista. **Não há como saber sem rodar com outras sementes.**

#### Implicação para a defesa

Pergunta esperada da banca: *"O F1 = 0,9906 do Experimento 5 é robusto a perturbações no split? Se você rodasse com `random_state=123`, daria o mesmo resultado?"*

Resposta atual: "não foi testado". Resposta ideal: "Sim — a média sobre 10 sementes é 0,990 ± 0,003, então 0,9906 está dentro do desvio padrão."

#### Mitigação proposta

```python
# Pseudocódigo: substituir o run único por loop multi-seed
SEEDS = [42, 123, 456, 789, 999, 1024, 2025, 3141, 7777, 9999]
results_by_seed = []

for seed in SEEDS:
    random.seed(seed); np.random.seed(seed)
    # rodar pipeline completa com essa semente
    metrics = run_pipeline(random_state=seed, ...)
    results_by_seed.append(metrics)

# Reportar média ± std e CI 95%
df = pd.DataFrame(results_by_seed)
print(df.describe())  # mean, std, 25%, 50%, 75%
# Bootstrap CI em cima dos 10 pontos
```

Custo computacional: 10× o atual. Para um treino que leva ~30 min, isso é 5 horas — viável de rodar em uma noite.

---

### C10. Apenas split treino/teste (sem conjunto de validação) ⚠️ DETALHADO

**Arquivo:** `pipeline/model_training/train_model.py:279-320` (`split_by_curve`)

#### O problema

A pipeline implementa apenas `train_test_split`. Não há split treino/validação/teste:

```python
# train_model.py — split_by_curve, simplificado
def split_by_curve(df, test_size=0.35, random_state=42):
    curves = df[ID_COL].drop_duplicates().values
    y_curves = df.groupby(ID_COL)[TARGET_COL].first().values
    curves_train, curves_test, _, _ = train_test_split(
        curves, y_curves,
        test_size=test_size,
        random_state=random_state,
        stratify=y_curves
    )
    df_train = df[df[ID_COL].isin(curves_train)]
    df_test  = df[df[ID_COL].isin(curves_test)]
    return df_train, df_test
```

Onde está o problema:

1. **Threshold tuning** (Seção 5.x da dissertação) é feito sobre o conjunto de teste — analisando precision-recall e F2 ao variar τ no mesmo conjunto cujas métricas finais são reportadas. **Isso contamina o teste**: o τ ótimo foi escolhido olhando para as etiquetas verdadeiras desse conjunto.

2. **Seleção entre RF, XGBoost, CatBoost e Logistic** é feita comparando F1 no mesmo conjunto de teste. Não é "selecionar o melhor modelo no conjunto de validação e reportar no conjunto de teste" — é "olhar todos no teste e escolher o melhor".

3. Se eventualmente for adicionado hyperparameter tuning (C7), ele necessariamente precisaria de um conjunto de validação separado.

#### Magnitude do efeito

Em cenário de alta separabilidade entre classes (como aqui, AUC-ROC > 0,99), o viés introduzido é provavelmente pequeno (talvez 0,5–1 pp em F1). Mas o argumento metodológico é o que importa: **um conjunto de teste tocado mais de uma vez deixa de ser conjunto de teste**.

#### Mitigação proposta

```python
# Pseudocódigo: split em três partes
def split_train_val_test(df, val_size=0.2, test_size=0.2, random_state=42):
    # 1. Reserva test (20% do total)
    df_remaining, df_test = split_by_curve(df, test_size=test_size, random_state=random_state)

    # 2. Do restante (80%), reserva val (25% disto = 20% do total)
    val_relative = val_size / (1 - test_size)  # 0.20 / 0.80 = 0.25
    df_train, df_val = split_by_curve(df_remaining, test_size=val_relative,
                                       random_state=random_state)

    return df_train, df_val, df_test  # 60% / 20% / 20%

# Uso:
df_train, df_val, df_test = split_train_val_test(df)

# Hyperparameter tuning + threshold tuning + model selection: tudo em (X_val, y_val)
# Reportagem final: única passagem em (X_test, y_test)
```

#### Mitigação aceitável para o mestrado

Como o tamanho do dataset é modesto (1693 amostras), reservar 20% para validação reduziria o treino para ~1015 amostras. Alternativa pragmática: **usar apenas validação cruzada** (já implementada via `StratifiedKFold`) **dentro do treino** para todas as escolhas (threshold, modelo, hiperparâmetros), e tocar o teste somente no final. Isso já é o caminho profissional padrão e não exige reduzir o conjunto de treino.

---

## Achados IMPORTANTES

### I1. Janela do Savitzky-Golay pode mascarar dips rápidos
**Arquivo:** `pipeline/model_training/build_dataset.py:319-340`. Para curvas curtas (<120 pontos), janela é `len(flux)/3`. Em dips com 3-4 pontos, suaviza o sinal antes da extração de features.

### I2. Validação cruzada com apenas uma semente
Coberto em C9. Reforço: a CV multi-seed é o caminho mais barato e mais informativo para fortalecer a tese.

### I3. Sem análise de calibração das probabilidades
Não há Platt scaling, isotonic regression, calibration plot, Brier score nem Expected Calibration Error. Como o ajuste de τ depende de probabilidades calibradas, esta lacuna é não-trivial.

### I4. Importância de features apenas via MDI (Gini)
MDI é viesado para variáveis contínuas de alta cardinalidade. **Permutation importance** ou **SHAP values** seriam mais robustos.

### I5. Fraser et al. (2024) não tratado: artefatos de campos densos
Pipeline ingere todas as curvas do VizieR sem verificar densidade de campo, blending PSF ou contaminação fotométrica.

### I6. Independência das amostras nos testes KS entre quartis
**Arquivo:** `pipeline/model_training/build_dataset.py:386-423`. KS pressupõe amostras independentes; quartis temporais da mesma curva têm dependência. P-valor reportado é sub-estimado. Não invalida o uso como feature, mas é uma aproximação.

### I7. F2-score apenas em `threshold_analysis`, não em `evaluate_model`
F2 é mais relevante que F1 no contexto (custo de FN > custo de FP). Deveria estar no relatório padrão de métricas.

---

## Achados MENORES

- **M1.** Janela do Savgol fixa em polyorder=2 sem fallback para curvas muito curtas (<10 pontos).
- **M2.** Curva de aprendizado (`plot_learning_curve_from_results`) não é gerada automaticamente — depende de execução manual de múltiplos splits.
- **M3.** Path quebrado `Tese/pngs/LimbFitCircle.png` em `capitulo2.tex` (já discutido em sessão anterior).

---

## Itens OK — implementado corretamente

- Split treino/teste **no nível de curva** (não no nível de ponto) — `split_by_curve`
- `SimpleImputer` fit apenas no treino — sem vazamento aqui
- `StandardScaler` aplicado apenas à Regressão Logística — correto para árvores
- K-means com `random_state=42` e `n_init=10` — reprodutível
- Threshold tuning de τ entre 0,01 e 1,0 com F2 e curva PR — excelente
- McNemar test implementado para comparação entre modelos
- Persistência completa de artefatos (modelos, imputer, scaler, feature_names)
- `split_real_holdout` para Experimento 7 (treino com sintéticas, teste só com reais)
- Padronização da semente em todos os componentes (numpy, random, modelos, splits)
- p-valores em escala log com epsilon (`-log10(p + 1e-300)`) — correto numericamente
- Estratificação por classe nas dobras de CV — `StratifiedKFold`
- Confusion matrix gerada e salva em formato gráfico
- Class balancing aplicado consistentemente (`class_weight='balanced'` ou `auto_class_weights='Balanced'` em todos os modelos)

---

## O que foi pulado/esquecido

Resposta direta à pergunta do usuário ("E mais importante, houve algum passo importante que foi 'pulado'/esquecido?"):

1. **Bootstrap confidence intervals** nas métricas finais
2. **Multi-seed robustness study** (rodar com 5–10 sementes)
3. **Train/Validation/Test** (atualmente apenas train/test)
4. **Calibração de probabilidades** (Platt / isotonic regression)
5. **Permutation importance** ou SHAP além do MDI
6. **Feature de autocorrelação** para detectar ruído correlacionado
7. **Auditoria de campo denso** (Fraser 2024)
8. **Hyperparameter tuning sistemático** (Optuna / GridSearch)
9. **Validação em catálogo externo** (Unistellar, OASES) — já reconhecida em cap. 6
10. **Triplete `(obj, date, observer)` como chave de leakage** — não como nome da curva apenas

---

## Recomendação de prioridades

**(a) Reconhecer no texto da dissertação (custo: baixo, alto valor):**
Adicionar à seção "Limitações" do cap. 6:
- Ausência de bootstrap CI nas métricas
- Ausência de multi-seed robustness
- Suposição implícita de ruído branco
- Ausência de calibração de probabilidades

Estes itens **fortalecem a defesa** ao demonstrar consciência metodológica.

**(b) Implementar antes da defesa (custo: médio):**
- Bootstrap CI nas métricas finais (1-2 dias)
- Multi-seed CV (1 dia + reprocessamento)
- Permutation importance (algumas horas)

**(c) Implementar antes de submeter artigo (custo: alto):**
- Hyperparameter tuning com Optuna
- Calibração de probabilidades
- Validação em catálogo externo
- Triplete-aware leakage check
- Feature de autocorrelação para ruído correlacionado

---

## Comentários do painel

**Cientista de Dados Sênior:** A pipeline está em estado defensável. Os achados críticos são reais, mas vários deles (sementes, CI, calibração) afetam a *qualidade da reportagem* mais do que a validade da metodologia. A defesa está blindada se você reconhecer a maioria como limitações no cap. 6.

**Richard Feynman:** *"Você fez bem em testar a ablação do K-means. Agora faça o teste honesto: rode com 10 sementes diferentes. Se a média ± 2σ ainda dá F1 > 0,98, você sabe que não foi sorte."*

**Carl Sagan:** *"O ponto sobre ruído correlacionado é o que mais me intriga. Curvas de luz reais não têm ruído branco. Vale ao menos um parágrafo de discussão no cap. 5."*

**Josiah Willard Gibbs:** *"Bootstrap. Sempre bootstrap. Métricas sem intervalo de confiança são números sem incerteza — e em ciência, número sem incerteza é metade do trabalho."*

---

## Anexo: arquivos críticos lidos durante a auditoria

| Arquivo | Achados principais |
|---------|--------------------|
| `pipeline/model_training/astro_data_access.py` | C1 (normalização), C2 (outlier removal) |
| `pipeline/model_training/build_dataset.py` | **C3 (leakage triplet)**, I1 (Savgol), I6 (KS independência) |
| `pipeline/model_training/occ_features.py` | C4 (sem ruído correlacionado) |
| `pipeline/model_training/train_model.py` | C5/C6/C7 (regularização/tuning), C8 (CI), **C9 (sementes)**, **C10 (validação)** |
| `pipeline/model_in_practice/test_low_snr.py` | OK (já validado em sessão anterior) |

---
---

# Segunda rodada — verificação empírica (2026-08-20)

**Método.** A primeira rodada foi leitura de código; esta rodada **mediu** cada hipótese contra
`pipeline/model_training/outputs/dataset_final.csv` (1693 amostras, 28 features),
`pipeline/data_warehouse/stellar_occultations.db` (931 observações, 462.738 pontos) e os
artefatos salvos em `outputs/resultado*/`. Onde uma hipótese admitia teste destrutivo, o teste
foi feito: o conjunto negativo foi **reconstruído** por um critério independente e o resultado
comparado. Todo número abaixo é reprodutível a partir dos dados versionados.

**Resultado em uma frase.** O pipeline é mais robusto do que a primeira rodada sugeria em
estatística (C9 resolvido, C3 refutado), e menos robusto do que a tese sugere em
**construção do benchmark** — mas o desvio é pequeno em magnitude e, quando corrigido,
**favorece** a tese em vez de enfraquecê-la (ver V1 e o reenquadramento na Parte III).

| | CRÍTICO | IMPORTANTE | MENOR |
|---|:---:|:---:|:---:|
| Achados novos (segunda rodada) | 4 | 3 | 2 |

---

## Parte I — Status dos achados da primeira rodada

| Achado | Status após medição | Evidência |
|---|---|---|
| **C3** — vazamento de positiva original | ❌ **REFUTADO** | 186 recortes, 125 curvas-mãe distintas, **0 mães permanecem na classe positiva**; 0 `curve_name` duplicados. O filtro de exclusão funciona. Substituído por **V7**, que é o problema real e mais fino. |
| **C9** — semente única | ✅ **RESOLVIDO** | 10 sementes, 11 features, dataset completo: **F1 = 0,985 ± 0,005** (RF) e **0,986 ± 0,005** (boosting). O F1 de 0,9906 está dentro de 1σ. Pode ir para a defesa hoje. |
| **C1** — baseline contaminado pelo dip | ✅ Corroborado | Ver **V2**: além da contaminação, `normalize_flux` produz fluxo normalizado negativo em 25% das positivas. |
| **C2** — outlier removal descarta o dip | ✅ Corroborado e **agravado** | Ver **V4**: `remove_outliers` é chamado em **um único ponto do pipeline**, e só na classe negativa. |
| **C4** — ruído correlacionado | ✅ Corroborado (não medido) | Permanece válido como limitação. |
| **C5/C6/C7** — regularização e tuning | ✅ Corroborado | Ver **V9** para a contradição adicional texto↔código na ponderação de classes do XGBoost. |
| **C8** — métricas sem CI | ✅ Corroborado | Parcialmente endereçado pelos ±σ multi-semente acima; bootstrap ainda pendente. |
| **C10** — sem conjunto de validação | ✅ Corroborado | O ajuste de τ e a escolha entre modelos ocorrem no teste. Válido. |
| **I1/I6** — Savgol e independência do KS | ✅ Corroborado | Sem alteração. |

---

## Parte II — Achados novos

### V1. Circularidade da fronteira do recorte (limiar 0,78) — CRÍTICO ⚠️ DETALHADO

**Arquivo:** `pipeline/model_training/build_dataset.py:117-139`

#### O mecanismo

Os negativos por recorte têm as **bordas** definidas pelo limiar, não pelo revisor humano:

```python
ocultando  = flux_clean < threshold        # threshold = 0.78
inicio_occ = np.where(ocultando)[0][0]     # 1º ponto abaixo de 0,78
fim_occ    = np.where(ocultando)[0][-1]    # último ponto abaixo de 0,78
segments.append(('antes',  flux_clean[:inicio_occ]))
segments.append(('depois', flux_clean[fim_occ+1:]))
```

O segmento `antes` é, por definição, tudo que precede o **primeiro** ponto abaixo de 0,78 —
logo nenhum ponto dele pode estar abaixo de 0,78. Idem para `depois`. O revisor responde
`s`/`n`/`skip`: aceita ou rejeita, **mas não move as bordas**. Aprovação manual é operação de
**subconjunto**, e qualquer invariante válida para todos os candidatos vale para os aprovados.

**Importante:** isto **não** é um problema de rotulagem. Os rótulos estão corretos — um trecho
fora da ocultação é, de fato, sem ocultação. O problema é que as duas classes ficam
analiticamente disjuntas ao longo de um eixo do espaço de features.

Medido:

| fonte | n | fração com `flux_min` < 0,78 | fração com `Savgol_Min` < 0,78 |
|---|---|---|---|
| `db_positive` | 802 | 0,9813 | 0,9613 |
| `artificial_negative` | 186 | **0,0000** | **0,0000** |
| `synthetic` | 702 | 0,1895 | 0,0427 |
| `db_negative` | 3 | 0,6667 | 0,0000 |

O `0,0000` é invariante do fatiamento, não coincidência amostral.

#### Efeito colateral de seleção

Em `build_dataset.py:119-121`:

```python
if not np.any(ocultando):
    print("  -> Nenhuma ocultação detectada nesta curva, pulando...")
    continue
```

As **31 positivas de dip raso** (3,9% de 802; nenhum ponto abaixo de 0,78) foram puladas
*antes* da revisão — nunca foram oferecidas ao revisor. A classe negativa portanto não contém
nenhum recorte proveniente de noites de dip raso. Efeito de seleção que a revisão manual não
tinha como corrigir, pois não viu essas curvas.

#### Consequência mensurável

Separabilidade univariada no dataset (AUC de uma única feature):

| feature | AUC |
|---|---|
| `Feature_Savgol_Min` | **0,9892** |
| `kmeans_centroid_dist` | 0,9817 |
| `Occ_flux_min` | 0,9813 |
| `Feature_Savgol_std` | 0,9755 |
| `Occ_depth` | 0,9690 |
| `Occ_SNR_dip` | 0,8115 |
| `Occ_chi2_constant` | 0,7658 |
| `Occ_chi2_square_well` | 0,5404 |

Uma árvore de decisão de **profundidade 1** treinada em `Feature_Savgol_Min` aprende o corte em
**0,78137** — redescobre a constante do `build_dataset.py` — e atinge F1 = 0,953.

#### Teste de falsificação

O conjunto negativo foi **reconstruído** com bordas definidas sem qualquer referência a nível de
fluxo: janela = fração fixa do comprimento (primeiros ou últimos 40% dos pontos), dip localizado
por critério **estatístico** (maior run abaixo de mediana − 5·σ_MAD, que se adapta ao ruído de
cada curva e não impõe fronteira em valor constante), curva descartada se o dip invadir a janela
com guarda de 5%. Mesmo pré-processamento nas duas classes, para isolar o efeito de fronteira do
efeito de **V4**. Executado também sem os dois χ² somados sobre N, para não trocar um artefato
por outro (**V5**). 10 sementes, split 80/20.

| | (A) original, borda = 0,78 | (B) sem limiar, borda = fração do comprimento |
|---|---|---|
| n (positivas / negativas) | 988 (802 / 186) | 1136 (898 / 238) |
| negativos com `flux_min` < 0,78 | **0 / 186 (0,0%)** | **174 / 238 (73,1%)** |
| Boosting, 11 features | 0,9888 ± 0,0056 | **0,9727 ± 0,0064** |
| Boosting, 9 features (sem χ² somados) | 0,9839 ± 0,0041 | 0,9694 ± 0,0051 |
| Random Forest, 11 features | 0,9901 ± 0,0057 | 0,9703 ± 0,0094 |
| regra trivial `min < 0,78` | 0,9794 ± 0,0053 | **0,9161 ± 0,0106** |
| **vantagem do ML sobre a regra** | **+0,94 pp** | **+5,66 pp** |

#### Interpretação — e registro de uma correção do próprio auditor

A hipótese inicial desta rodada foi que a circularidade explicava a maior parte do F1 = 0,99.
**A hipótese está errada, e o teste é que mostra isso.** Removida a circularidade, o F1 dos
modelos cai apenas **1,6 pp** (0,989 → 0,973): os modelos não estavam redescobrindo o limiar,
estavam lendo estrutura de dip. O que a circularidade inflava era a **regra trivial**
(0,979 → 0,916) — isto é, a muleta fazia a contribuição do ML parecer *menor* do que é. A
vantagem real sobre a heurística é ~6× maior que a comparação ingênua sugere.

Os 1,6 pp são um **limite superior**: os negativos de (B) não passaram por revisão humana e
carregam nuvem e sistemáticos que teriam sido rejeitados, então parte da queda é sujeira e não
fronteira. Critério de leitura declarado *antes* de rodar o teste: "se o F1 se mantiver em
0,98–0,99, a circularidade é irrelevante na prática". Ficou em 0,973 — logo o efeito existe,
é real e é pequeno.

**Ressalvas do teste (B):** 660 de 898 curvas descartadas (dip invadindo a janela ou não
detectado pelo critério de 5σ), o que introduz seleção própria; janelas de 40% são mais longas
que os recortes originais. É teste de sanidade, não substituto do conjunto revisado à mão.

#### Regime difícil — o número que realmente importa

Restringindo às positivas em que a heurística falha por construção (sem nenhum ponto abaixo de
0,78):

| regime difícil | n positivas | n negativas | Boosting | regra trivial |
|---|---|---|---|---|
| com negativos originais | 31 | 891 (inclui as 702 sintéticas) | 0,833 ± 0,071 | **0,000** |
| com negativos sem limiar | 30 | 238 (janela por fração) | 0,641 ± 0,111 | **0,000** |

Os dois conjuntos negativos diferem em tamanho e composição, portanto as duas linhas **não são
diretamente comparáveis entre si** — cada uma deve ser lida contra a sua própria regra trivial
(0,000 em ambos os casos). A comparação limpa entre construções é a da tabela anterior.

A barra de erro é grande e o corte em 0,78 é arbitrário, mas o contraste qualitativo é
inequívoco: onde a heurística vale exatamente zero, o modelo recupera a maioria dos eventos.
Este é o mesmo regime do anel fino Q2R no estudo de caso de Quaoar (Cap. 5, Seção 5.7.2) — e
hoje os dois resultados estão desconectados no texto.

#### Mitigação

1. Reportar a regra trivial na tabela principal do Cap. 5, ao lado do F1 dos modelos.
2. Criar seção "regime difícil" com os números acima.
3. Para o artigo: refazer o recorte com bordas independentes de nível de fluxo (critério em σ_MAD,
   ou tempos de imersão/emersão publicados quando disponíveis) e reportar o F1 resultante.

---

### V2. Fluxo normalizado não-físico entrando nas features — CRÍTICO

**Arquivos:** `pipeline/model_training/astro_data_access.py:221-281` (`normalize_flux`) e
`pipeline/model_training/build_dataset.py:456-475`

O pipeline de treino não aplica nenhum clip físico ao fluxo. Distribuição de `Occ_flux_min` nas
802 positivas do dataset da tese:

```
count = 802     mean = -89,87     std = 2547,39
min = -72141    p01 = -1,385   p05 = -0,498   p25 = -0,103
med = 0,032     p95 =  0,696   p99 =  0,835   max =  0,917
```

- **204 de 802 positivas (25%)** têm fluxo normalizado mínimo abaixo de −0,1, o que não é físico.
- Pior caso: `Hera_2005-04-01_BAllen` entra no treino com `flux_min = −72141`,
  `Feature_Amp = 81664` e `Occ_depth = 55344`. É *flag* de qualidade do PRAIA ou quadro
  corrompido passando direto para as features.
- Outros: `Desiderata_2016-02-01_ARPratt` (−3,61), `Jiangxi_2020-12-01_Unknown` (−2,54),
  `2002KX14_2018-09-01_WHanna` (−1,96), `Oceana_2012-03-01_MForbes` (−1,82),
  `Pretoria_2005-10-01_Unknown` (−1,69).

**Inconsistência de projeto:** `pipeline/model_in_practice/test_quaoar.py` **faz** o clip físico
em `[-2, 5]` (descrito no Cap. 5, linha 465), justamente para remover valores extremos do PRAIA.
O script de **inferência** é mais cuidadoso que o de **treinamento**.

Isso corta nos dois sentidos: valores extremos tornam algumas positivas trivialmente separáveis
por motivo errado, e `Feature_Amp` / `Max_Drawdown` / `Occ_depth` dessas curvas são lixo.

**Mitigação:** aplicar em `build_dataset.py` o mesmo clip já usado em `test_quaoar.py`, e registrar
quantas curvas foram afetadas. É uma linha e é a correção de maior retorno por esforço de toda
esta auditoria — vale rodar antes da defesa e reportar o F1 resultante.

---

### V3. `Occ_SNR_dip` tem distribuição nula centrada em ~4–5, não em 0 — CRÍTICO

**Arquivo:** `pipeline/model_training/occ_features.py:157` e `occ_features.py:98`

Duas causas que se somam na mesma direção:

1. `depth = baseline − min(flux)` usa o **mínimo**, uma estatística de valor extremo: para ruído
   gaussiano puro, cresce como σ·√(2 ln N). Nunca é ≈ 0.
2. `baseline_std = std(flux[flux >= mediana])` usa apenas a **metade superior** da distribuição,
   subestimando σ em ~40%.

Logo `SNR_dip = depth / baseline_std` não é significância de detecção. Medido:

| fonte | mediana `SNR_dip` | p90 | fração > 3 |
|---|---|---|---|
| `synthetic` (ruído puro por construção) | 4,68 | 5,81 | **0,996** |
| `db_negative` | 4,28 | 4,34 | 1,000 |
| `artificial_negative` | 3,31 | 5,05 | 0,586 |
| `db_positive` | 7,35 | 14,81 | 0,928 |

Uma curva de ruído puro tira "SNR > 3" em 99,6% dos casos.

**Consequência para a tese.** O parágrafo do Cap. 6 (linha 18) e o script
`pipeline/model_in_practice/test_low_snr.py` selecionam curvas com `Occ_SNR_dip < 3` e as tratam
como "curvas difíceis / de baixo SNR". Não são: `SNR_dip < 3` está **abaixo da mediana do ruído
puro**, então as 67 curvas selecionadas são uma cauda atípica, não os casos fisicamente difíceis.
O teste não mede o que o texto afirma que mede (e, como se reconhece no próprio parágrafo, é
in-sample).

**Mitigação:** cortar a afirmação do Cap. 6 ou trocar o estimador por um com nulo em ≈ 0, por
exemplo `Occ_depth / (σ_MAD · √n_frames_no_dip)`, e verificar a distribuição nula nas sintéticas
antes de usar.

---

### V4. Pré-processamento assimétrico entre as classes — CRÍTICO

**Arquivo:** `pipeline/model_training/build_dataset.py:110`

`remove_outliers` é chamado em **exatamente um lugar** de todo o pipeline: dentro de
`recortar_negativos_interativo`. As positivas que entram no dataset (`build_dataset.py:464`) usam
a curva crua do banco.

Ou seja: **a classe negativa levou clipping de 3σ e a positiva não.** Medianas por fonte:

| fonte | `Feature_Flux_std` | `Feature_Amp` | `Feature_Savgol_Max` |
|---|---|---|---|
| `db_positive` | 0,2891 | 1,3667 | 1,2499 |
| `artificial_negative` | 0,0939 | 0,4212 | 1,1985 |
| `synthetic` | 0,0357 | 0,2001 | 1,0550 |

Parte dessa diferença é física (o dip infla a dispersão), mas parte é o degrau de tratamento.
`Feature_Flux_std`, `Feature_Amp`, `Max_Drawdown` e `Occ_baseline_std` — todas no conjunto final —
são afetadas.

**Mitigação:** mesmo pré-processamento nas duas classes, e trocar média/σ por MAD no
`remove_outliers` (já apontado em C2).

---

### V5. `Occ_chi2_constant` e `Occ_chi2_square_well` são proxies de comprimento — IMPORTANTE

**Arquivo:** `pipeline/model_training/occ_features.py:233-291`

Ambos são somas de resíduos quadráticos sobre N pontos, **sem redução por graus de liberdade**.
Logo escalam com o comprimento da curva. Medianas:

| fonte | `Occ_chi2_constant` |
|---|---|
| `db_positive` | 1220,1 |
| `db_negative` | 976,9 |
| `synthetic` | 593,7 |
| `artificial_negative` | **140,0** |

Fator ~9 entre positivas e recortes, porque o recorte é por construção mais curto que a curva-mãe.
As duas features estão no conjunto final de 11 e codificam **proveniência**, não física.
Confirmação independente: no teste de falsificação (**V1**), remover essas duas features muda o
resultado em menos de 0,5 pp — elas contribuem pouco além do comprimento.

**Mitigação:** dividir por N (χ² reduzido). `Occ_chi2_ratio` já é adimensional e pode ficar.

---

### V6. Distribution shift entre sintéticas e reais, dentro da mesma classe — IMPORTANTE

Treinando um discriminador `synthetic` vs. `artificial_negative` — **ambas rótulo 0**:

| feature | AUC |
|---|---|
| `Feature_Savgol_std` | **0,9425** |
| `kmeans_centroid_dist` | 0,9411 |
| `Occ_chi2_square_well` | 0,9336 |
| `Occ_chi2_constant` | 0,9304 |
| `Deriv_Std` | 0,9186 |

As 702 sintéticas são uma subpopulação reconhecível e são **78% da classe negativa**. Parte do que
o modelo aprende é "isto é sintético → negativo", que não transfere para dado observacional.

Confirmação pelo caminho oposto: removendo as sintéticas e treinando só em dado real
(802 positivas vs. 189 negativas), o F1 **sobe** — RF 0,9886 ± 0,0063, boosting 0,9882 ± 0,0057,
contra 0,985/0,986 no dataset completo. As sintéticas não estão ajudando a generalização medida.

O Experimento 3 é a mitigação correta, mas seu teste tem 38 negativas reais.

**Mitigação:** reportar esse AUC de 0,94 como *adversarial validation* explícita no Cap. 5. É um
número honesto, barato de calcular e demonstra domínio metodológico.

---

### V7. Split por curva, não por evento — IMPORTANTE (substitui C3)

**Arquivo:** `pipeline/model_training/train_model.py:279-320` (`split_by_curve`)

O split é feito por `curve_name` = `objeto_data_observador`. Mas uma mesma ocultação física é
frequentemente registrada por vários observadores:

- 765 eventos (objeto + data) distintos entre as 988 curvas reais;
- **164 eventos têm mais de uma curva**, envolvendo **387 das 988 curvas (39%)**;
- simulando 20 sementes, em média **59,8 eventos ficam partidos entre treino e teste**.

Nesses casos o modelo vê uma corda da mesma ocultação — mesma estrela, mesma noite, mesma escala
de profundidade e duração — no treino, e é testado em outra corda do mesmo evento. Viés otimista
leve, mas sistemático. É a versão real e mensurada da preocupação levantada em C3 (que, no nível
de curva-mãe, foi refutada).

**Mitigação:** `StratifiedGroupKFold` / `GroupShuffleSplit` agrupando por `(objeto, data)`.

---

### V8. O `dataset_final.csv` versionado é incompatível com o código — CRÍTICO (reprodutibilidade)

**Arquivos:** `outputs/dataset_final.csv` vs. `occ_features.py` e `train_model.py:88`

O CSV versionado tem colunas com prefixo **`IOTA_`**; `occ_features.py` e a lista
`EXCLUDED_FEATURES` usam **`Occ_`**. A exclusão é *match* por string, **sem validação**. Portanto,
quem clonar o repositório e rodar `train_model.py` obtém **19 features em vez de 11** e números que
não reproduzem a tese. Os `feature_names.pkl` dos diretórios `resultado*/` confirmam que as
rodadas reais usaram `Occ_`.

Problema relacionado, em `train_model.py:175`:

```python
df = pd.read_csv(from_csv).dropna()
```

O `dropna()` roda **antes** do split e sobre **todas** as colunas, inclusive as excluídas. Um NaN
em `Deriv_Kurtosis` (que só ocorre em curvas com poucos pontos) elimina a curva inteira, mesmo a
feature não sendo usada — descartando preferencialmente curvas curtas, que são as difíceis. E
torna o `SimpleImputer` um no-op, contradizendo o Cap. 4 ("valores faltantes preenchidos pela
mediana calculada no conjunto de treino").

**Mitigação:**
```python
faltando = set(EXCLUDED_FEATURES) - set(df.columns)
assert not faltando, f"EXCLUDED_FEATURES não encontradas no dataset: {faltando}"
```
mais: regerar o CSV versionado, e restringir o `dropna()` às colunas efetivamente usadas (ou
removê-lo, deixando o imputer trabalhar como o Cap. 4 descreve).

---

### V9. Inconsistências texto↔código — MENOR (mas a banca cutuca)

| # | Item | Onde | Situação |
|---|---|---|---|
| a | **Ponderação de classes no XGBoost** | `train_model.py:123`; Cap. 5 linha 228; Seção 5.11.1; `apendice_hiperparametros.tex:36` | `XGB_PARAMS` não tem `scale_pos_weight`. O Cap. 5 afirma "ponderação das classes nos quatro algoritmos" e o apêndice diz que "o desbalanceamento é tratado indiretamente pelo algoritmo" — **isso não é verdade**, o default é `scale_pos_weight=1`, sem tratamento algum. Numericamente irrelevante (802/891 é quase balanceado); corrigir só o texto. |
| b | **McNemar: definição de b e c** | `train_model.py:923`; Cap. 5 linha 682 vs. legenda da Tabela 5.11 | O corpo do texto define "b = A erra e B acerta"; código e legenda usam o inverso. Os seis p-valores foram recalculados e **estão corretos** (a estatística é simétrica em \|b−c\|), mas texto e legenda se contradizem. |
| c | **McNemar: teste errado para o regime** | `train_model.py:930` | Com b+c ≤ 6 a aproximação χ² não vale (regra de bolso: b+c ≥ 25). Usar binomial exato — `statsmodels.stats.contingency_tables.mcnemar(exact=True)`, uma linha. A tese já reconhece que o teste é "pouco potente"; trocar blinda a afirmação. |
| d | **Curva de aprendizado** | `train_model.py:968-1005` | `n_train` hardcoded por nome de diretório, com convenções inconsistentes entre eles (`0.4-0.6` = 40% treino; `0.35-0.65` = 65% treino), e `set_ylim([0.96, 1.0])`. A conclusão de "saturação" (contribuição 4 do Cap. 6) repousa em 3 pontos com o eixo y comprimido em 0,04. Ampliar para 5–6 pontos ou suavizar a afirmação. |
| e | **Escala de Fresnel** | `capitulo2.tex:90` | "Essa escala define a resolução espacial efetiva na direção **perpendicular à corda**" — a difração de Fresnel borra o perfil **ao longo** da corda (direção do movimento da sombra); a resolução perpendicular é dada pelo espaçamento entre cordas. O cálculo numérico (1,2 km a 40 UA) está correto. |
| f | **Rastreabilidade dos experimentos** | `outputs/resultado*/feature_names.pkl` | Contagens salvas: 28, 13, 12, 12, 11, 11, 11. A tese cita "Experimento 4 (14 features)" — **não existe rodada com 14 features salva**. Cada experimento foi produzido editando constantes globais à mão, então o repositório guarda só um estado. Para a defesa basta uma tabela mapeando experimento da tese → diretório de resultado; para o artigo, um `experiments.yaml` + loop. |
| g | **Path de figura quebrado** | `capitulo2.tex:104` | `Tese/pngs/LimbFitCircle.png`, inconsistente com o `pngs/...` do resto do capítulo (já registrado como M3). |

---

## Parte III — Reenquadramento recomendado do Capítulo 5

O achado V1 exige uma mudança de narrativa, mas ela é **a favor** da tese. Hoje o Cap. 5 reporta
F1 ≈ 0,99 sem baseline trivial na tabela principal, o que deixa aberta a pergunta óbvia da banca:
*"por que ML e não um `if`?"*

Narrativa recomendada, sustentada pelos números desta rodada:

1. Uma heurística de limiar fixo atinge **F1 = 0,92** em condições honestas (construção sem
   circularidade).
2. Os modelos atingem **F1 = 0,97** nas mesmas condições — vantagem de **+5,7 pp**, ~6× maior do
   que a comparação ingênua sugeria.
3. No regime em que a heurística vale **exatamente zero** (dip raso, sem ponto abaixo de 0,78), os
   modelos ainda recuperam **F1 ≈ 0,64**.
4. Esse regime é precisamente o do anel fino Q2R de Quaoar (Seção 5.7.2), fechando o laço entre
   experimento formal e estudo de caso — que hoje aparecem desconectados.

Resposta de 30 segundos a ter pronta para a banca:
> *"Seu conjunto negativo foi construído com um corte em 0,78; o modelo não está só reaprendendo
> esse corte?"*
> — "Em 96% das curvas, sim, e é por isso que reporto separadamente os 4% em que ele não está.
> Testei removendo a circularidade: o F1 dos modelos cai 1,6 pp, o da heurística cai 6,3 pp."

---

## Parte IV — Prioridades revisadas

**(a) Antes da defesa — baixo custo, alto retorno**

| Ação | Custo | Fecha |
|---|---|---|
| Aplicar o clip físico do `test_quaoar.py` no `build_dataset.py` e reportar o F1 | 1 h | **V2** |
| Reportar a regra trivial na tabela principal + seção "regime difícil" | 4 h | **V1** |
| Levar os números multi-semente (F1 = 0,985 ± 0,005, 10 sementes) | pronto | **C9** |
| Bootstrap CI nas métricas finais | 4 h | **C8** |
| Corrigir os itens (a), (b), (e) de **V9** e a afirmação de baixo SNR do Cap. 6 | 1 tarde | **V3**, **V9** |
| Tabela mapeando experimento da tese → diretório de resultado | 30 min | **V9-f** |
| `assert` da lista `EXCLUDED_FEATURES` + regerar o CSV versionado | 1 h | **V8** |

**(b) Antes de submeter artigo**

- Recorte de negativos com bordas independentes de nível de fluxo (**V1**)
- Mesmo pré-processamento nas duas classes, com MAD (**V4**, C2)
- χ² reduzidos por N (**V5**)
- `Occ_SNR_dip` com distribuição nula em ≈ 0 (**V3**)
- Split agrupado por `(objeto, data)` (**V7**)
- *Adversarial validation* sintética vs. real reportada (**V6**)
- Calibração de probabilidades, Optuna, permutation importance / SHAP (I3, I4, C7)
- Conjunto de validação separado do teste (**C10**)

---

## Anexo: como reproduzir os números desta rodada

Todos os resultados vêm de `outputs/dataset_final.csv` e de
`pipeline/data_warehouse/stellar_occultations.db`, ambos versionados. Os dois scripts do teste de
falsificação (**V1**) foram executados fora do repositório:

- `recorte_sem_limiar.py` — reconstrói o conjunto negativo com bordas por fração de comprimento e
  dip localizado por 5·σ_MAD; grava `dataset_sem_limiar.csv`.
- `compara.py` — compara construções (A) e (B) com as mesmas 11 features, mesmos modelos e 10
  sementes.

Parâmetros usados na construção (B): `FRAC_JANELA = 0.40`, `MARGEM = 0.05`, `K_SIGMA = 5.0`,
`MIN_PTS = 20`; positivas lidas do banco com ≥ 50 pontos (898 curvas); 660 descartadas por dip
invadindo a janela ou não detectado; 238 negativos gerados.

**Nota de método.** Os modelos usados na comparação foram `RandomForestClassifier` com os
hiperparâmetros de `RF_PARAMS` e `HistGradientBoostingClassifier` como substituto do XGBoost
(`xgboost` não estava instalado no ambiente do auditor). Como toda a comparação é **relativa**
entre as construções (A) e (B), com o mesmo modelo nas duas pontas, a substituição não afeta a
conclusão — mas os valores absolutos de F1 não são diretamente comparáveis aos da tese, que usa
XGBoost. Recomenda-se reexecutar `compara.py` no ambiente do `requirements_frozen.txt` antes de
citar qualquer número desta rodada na dissertação.

---

## Comentários do painel — segunda rodada

**Cientista de Dados Sênior:** O achado V2 é o que eu corrigiria primeiro: uma curva com
amplitude de 8×10⁴ no conjunto de treino é indefensável em qualquer revisão, e o conserto é uma
linha. V1 é o achado intelectualmente mais interessante, mas o teste mostrou que o impacto é
pequeno — reporte-o como força, não como fraqueza.

**Richard Feynman:** *"Você formulou uma hipótese — 'o limiar explica o 0,99' — desenhou o teste
que poderia matá-la, declarou o critério antes de rodar, e a hipótese morreu. Isso é o único jeito
de saber alguma coisa. Escreva a hipótese refutada na tese, não só a que sobreviveu."*

**Carl Sagan:** *"O SNR que dá 5 para ruído puro é o tipo de coisa que passa por três revisores
sem ninguém olhar a distribuição nula. Sempre plote o nulo."*

**Josiah Willard Gibbs:** *"F1 = 0,985 ± 0,005 sobre dez sementes é uma afirmação. F1 = 0,9906
não era. A segunda rodada transformou uma em outra — falta agora o bootstrap."*
