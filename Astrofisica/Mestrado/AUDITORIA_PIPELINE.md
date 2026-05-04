# Auditoria Crítica da Pipeline de Detecção de Ocultações Estelares

**Auditor:** Cientista de Dados Sênior + Pesquisador em Astroestatística (com Richard Feynman, Carl Sagan e Josiah Willard Gibbs)
**Data:** 2026-04-04
**Escopo:** `pipeline/` (Python) + `writing_latex/Tese/` (dissertação)
**Status deste documento:** registro técnico de referência. Não dispara ações imediatas.

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
